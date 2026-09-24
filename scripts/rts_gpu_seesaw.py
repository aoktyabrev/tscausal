"""
RTS stage 1 — see-saw with the state step on GPU (rts_gpu.admm_step): the operation steps stay on CPU
(cvxpy, problems of size d×d), the steps over ω₁, ω₂, Δ are computed by ADMM on GPU. Only this path scales
up to (6,6,6,6) and (8,8,8,8): SCS at N = 1296 spends ~350 s on a single w-step.

Cleanup of a point — per-factor noise, as in RTS 0, but basis-free (projections from rts_gpu): ISO and
operational independence are exact, positivity is confirmed by a Cholesky factorisation.
"""
import os
import sys
import time

import numpy as np
import torch

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import qproc as Q  # noqa: E402
import rts as R  # noqa: E402
import rts_gpu as GP  # noqa: E402
import rts_seesaw as S  # noqa: E402


def cleanup_gpu(gs, w1, w2, D, A, F, C, rng, tol=1e-12):
    """ω(q) = w₁(q)⊗w₂(q) + (1−q)Δ, w_i(q) = (1−q)w_i + q I/n_i; minimal q by bisection of the segment until ω ⪰ 0.
    ISO marginals and operational independence are exact by construction of the projections."""
    dA, dB1, dB2, dC = gs.dims
    w1c, w2c = gs.fix_local(w1, dA, dB1), gs.fix_local(w2, dB2, dC)
    Dc = gs.proj_delta(D)
    I1 = torch.eye(gs.n1, device=GP.DEV, dtype=GP.DT) / gs.n1
    I2 = torch.eye(gs.n2, device=GP.DEV, dtype=GP.DT) / gs.n2

    def om_of(q):
        return torch.kron((1 - q) * w1c + q * I1, (1 - q) * w2c + q * I2) + (1 - q) * Dc

    def lam(q):
        M = om_of(q)
        try:
            return float(torch.linalg.eigvalsh(M).min())
        except torch._C._LinAlgError:
            return float(torch.linalg.eigvalsh(M.cpu()).min())

    lo, hi = 0.0, 1.0
    if lam(0.0) > tol:
        hi = 0.0
    else:
        for _ in range(60):
            mid = (lo + hi) / 2
            if lam(mid) > tol:
                hi = mid
            else:
                lo = mid
    om_t = om_of(hi)
    torch.linalg.cholesky(om_t.cpu())                       # certificate ω ≻ 0
    om = om_t.cpu().numpy()
    return om, {"q_noise": hi, "T": R.T_value(om, A, F, C), "min_eig": float(np.linalg.eigvalsh(om_t.cpu().numpy()).min()),
                "iso_marginals_dev": R.marginals_ok(om, gs.dims),
                "oi_violation": R.oi_violation(om, gs.dims, rng, 50),
                "delta_rel_norm": float(((1 - hi) * Dc).norm() / om_t.norm())}


def run_gpu(dims, rng, iters=10, admm_iters=1500, start=None, verbose=True, time_budget=None, polish=6):
    """Two-phase see-saw: phase 1 — products (Δ = 0), phase 2 — Δ and operations. Returns a point or None."""
    m = S.Model(dims, delta_basis=False)
    gs = GP.GState(dims)
    dA, dB1, dB2, dC = dims
    t0 = time.time()
    A, F, C, w1, w2 = S.random_start(m, rng) if start is None else start
    w1t, w2t = GP._t(w1), GP._t(w2)
    Dt = torch.zeros((gs.N, gs.N), device=GP.DEV, dtype=GP.DT)
    hist, stats = [], {"admm": []}

    def omega():
        return (torch.kron(w1t, w2t) + Dt).cpu().numpy()

    def ops_step(om):
        nonlocal A, C, F
        A = S.solve_ops_A(m, om, F, C, "A", 3, 1.5 * dA)
        S.A_cur = A
        C = S.solve_ops_A(m, om, F, C, "C", 6, 3.0 * dC)
        F = S.solve_F(m, om, A, C)

    try:
        for phase in (1, 2):
            last = -np.inf
            for it in range(iters):
                if time_budget and time.time() - t0 > time_budget:
                    break
                ops_step(omega())
                Gt = GP._t(m.G(A, F, C))
                if phase == 2:
                    Dn, _, res, _ = GP.admm_step(gs, Gt, "D", w1t, w2t, Dt, iters=admm_iters)
                    Dt = Dn
                    stats["admm"].append(res)
                for part in ("w1", "w2"):
                    V, _, res, _ = GP.admm_step(gs, Gt, part, w1t, w2t, Dt, iters=admm_iters)
                    if part == "w1":
                        w1t = V
                    else:
                        w2t = V
                    stats["admm"].append(res)
                val = float((torch.kron(w1t, w2t) + Dt).flatten() @ Gt.T.flatten())
                hist.append(val)
                if verbose:
                    print(f"    phase {phase} iteration {it}: 𝒯 = {val:.6f} ({time.time() - t0:.0f} s)", flush=True)
                if val - last < 1e-6:
                    break
                last = val
    except Q.SolverFailure:
        return None
    # polish: a long ADMM at the final operations — reduces the residual infeasibility, and hence the
    # loss of 𝒯 in the cleanup (at d = 6 without it up to 0.42 was lost)
    polish_res = None
    if polish:
        Gt = GP._t(m.G(A, F, C))
        Dt, _, polish_res, _ = GP.admm_step(gs, Gt, "D", w1t, w2t, Dt, iters=admm_iters * polish)
        for part in ("w1", "w2"):
            V, _, polish_res, _ = GP.admm_step(gs, Gt, part, w1t, w2t, Dt, iters=admm_iters * polish)
            if part == "w1":
                w1t = V
            else:
                w2t = V
        hist.append(float((torch.kron(w1t, w2t) + Dt).flatten() @ Gt.T.flatten()))
    om, cl = cleanup_gpu(gs, w1t, w2t, Dt, A, F, C, rng)
    return {"T_raw": hist[-1] if hist else None, "T_clean": cl["T"], "cleanup": cl, "history": hist,
            "seconds": round(time.time() - t0, 1), "admm_last": stats["admm"][-1] if stats["admm"] else None, "polish_res": polish_res,
            "point": {"w1": w1t.cpu().numpy(), "w2": w2t.cpu().numpy(), "D": Dt.cpu().numpy(),
                      "A": A, "F": F, "C": C, "d": dims[0]}}

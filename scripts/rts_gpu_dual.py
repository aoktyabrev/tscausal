"""
RTS stage 1, S.2 — dual certificate on GPU (ADMM), for dimensions where cvxpy/SCS cannot assemble the problem:
at N = 1296 a dense representation of the lift map in cvxpy is unrealistic memory-wise.

Primal: max ⟨G, ω⟩ over ω ⪰ 0 with ISO marginals (operational independence is not required).
Dual: min (Tr Y + Tr Z)/n with lift(Y, Z) := Y_{(A,C)}⊗I_{(B1,B2)} + I_{(A,C)}⊗Z_{(B1,B2)} ⪰ G.
ADMM: min ⟨c, x⟩ + I_PSD(S) subject to lift(x) − S = G, x = (Y, Z).
  x-step: lift*(lift(x)) = lift*(R) − c/ρ, R = S + G − u. Here lift*(M) = (Tr_B M, Tr_AC M), and the system
     n_B·Y + (Tr Z)·I = P,  n_AC·Z + (Tr Y)·I = Q
  is solvable up to the kernel (tI, −tI), along which the objective is constant when n_AC = n_B.
  S-step: Π_PSD(lift(x) − G + u);  u-step: u += lift(x) − G − S.
The result is checked independently: the shift Y → Y + |λ_min| I and a Cholesky factorisation — only after that
is the number declared an upper bound. Result: results/json/rts_gpu_dual.json.
"""
import json
import os
import sys
import time

import numpy as np
import torch

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import polytope as P  # noqa: E402
import rts as R  # noqa: E402
import rts_gpu as GP  # noqa: E402
import rts_gpu_seesaw as GS  # noqa: E402
import rts_seesaw as S  # noqa: E402


class Lift:
    """lift(Y, Z) in the subsystem order (A, B1, B2, C)."""

    def __init__(self, dims):
        dA, dB1, dB2, dC = dims
        self.dims = dims
        self.nAC, self.nB = dA * dC, dB1 * dB2
        self.N = self.nAC * self.nB
        self.eB = torch.eye(self.nB, device=GP.DEV, dtype=GP.DT).reshape(dB1, dB2, dB1, dB2)
        self.eAC = torch.eye(self.nAC, device=GP.DEV, dtype=GP.DT).reshape(dA, dC, dA, dC)

    def __call__(self, Y, Z):
        dA, dB1, dB2, dC = self.dims
        Y4 = Y.reshape(dA, dC, dA, dC)
        Z4 = Z.reshape(dB1, dB2, dB1, dB2)
        out = torch.einsum("adeh,bcfg->abcdefgh", Y4, self.eB) + torch.einsum("adeh,bcfg->abcdefgh", self.eAC, Z4)
        return out.reshape(self.N, self.N)

    def adjoint(self, M):
        dA, dB1, dB2, dC = self.dims
        T = M.reshape(dA, dB1, dB2, dC, dA, dB1, dB2, dC)
        mAC = torch.einsum("abcdebcf->adef", T).reshape(self.nAC, self.nAC)
        mB = torch.einsum("abcdafgd->bcfg", T).reshape(self.nB, self.nB)
        return mAC, mB

    def solve_normal(self, Pm, Qm):
        """n_B·Y + (Tr Z)·I = P, n_AC·Z + (Tr Y)·I = Q; solution up to the kernel (tI, −tI)."""
        z = 0.0                                             # gauge along the kernel (objective constant along it)
        Y = (Pm - z * torch.eye(self.nAC, device=GP.DEV, dtype=GP.DT)) / self.nB
        y = float(torch.trace(Y))
        Z = (Qm - y * torch.eye(self.nB, device=GP.DEV, dtype=GP.DT)) / self.nAC
        return Y, Z


def dual_admm(dims, G, iters=3000, rho=None, tol=1e-10):
    lf = Lift(dims)
    Gt = 0.5 * (G + G.T)
    rho = rho or 1.0
    S_ = torch.zeros_like(Gt)
    u = torch.zeros_like(Gt)
    Y = torch.eye(lf.nAC, device=GP.DEV, dtype=GP.DT) * float(torch.linalg.eigvalsh(Gt).max())
    Z = torch.zeros((lf.nB, lf.nB), device=GP.DEV, dtype=GP.DT)
    cY = torch.eye(lf.nAC, device=GP.DEV, dtype=GP.DT) / lf.nAC       # ∇ of the objective: (Tr Y + Tr Z)/n_AC
    cZ = torch.eye(lf.nB, device=GP.DEV, dtype=GP.DT) / lf.nAC
    pr = dr = float("nan")
    for k in range(iters):
        Rm = S_ + Gt - u
        pA, pB = lf.adjoint(Rm)
        Y, Z = lf.solve_normal(pA - cY / rho, pB - cZ / rho)
        LX = lf(Y, Z)
        ev, evec = GP._eigh(LX - Gt + u)
        Sn = (evec * ev.clamp(min=0)) @ evec.T
        u = u + LX - Gt - Sn
        pr = float((LX - Gt - Sn).norm())
        dr = float(rho * (Sn - S_).norm())
        S_ = Sn
        if pr < tol and dr < tol:
            break
        if (k + 1) % 25 == 0:
            if pr > 10 * dr:
                rho, u = rho * 2, u / 2
            elif dr > 10 * pr:
                rho, u = rho / 2, u * 2
    return Y, Z, {"primal_res": pr, "dual_res": dr, "iters": k + 1, "rho": rho}


def certify(dims, A, F, C, iters=3000):
    m = S.Model(dims, delta_basis=False)
    G = m.G(A, F, C)
    G = (G + G.T) / 2
    Gt = GP._t(G)
    lf = Lift(dims)
    t0 = time.time()
    Y, Z, res = dual_admm(dims, Gt, iters=iters)
    # independent check on CPU: shift to feasibility and Cholesky
    Yn, Zn = Y.cpu().numpy(), Z.cpu().numpy()
    Yn, Zn = (Yn + Yn.T) / 2, (Zn + Zn.T) / 2
    M = lf(GP._t(Yn), GP._t(Zn)).cpu().numpy() - G
    lam = float(np.linalg.eigvalsh(M).min())
    shift = max(0.0, -lam) + 1e-9
    Yc = Yn + shift * np.eye(lf.nAC)
    Mc = lf(GP._t(Yc), GP._t(Zn)).cpu().numpy() - G
    np.linalg.cholesky(Mc)
    return {"certified_upper_bound": float((np.trace(Yc) + np.trace(Zn)) / lf.nAC), "lambda_min_raw": lam,
            "shift": shift, "min_eig_certificate": float(np.linalg.eigvalsh(Mc).min()),
            "admm": {k: v for k, v in res.items()}, "seconds": round(time.time() - t0, 1)}


def main():
    out_p = os.path.join(P.ROOT, "results", "json", "rts_gpu_dual.json")
    out = json.load(open(out_p)) if os.path.exists(out_p) else {}
    out["stage"] = "RTS1 S.2 двойственные сертификаты (ADMM на GPU) при найденных операциях"
    for d in json.loads(os.environ.get("RTS_DUAL_DIMS", "[2,4,6]")):
        f = os.path.join(P.ROOT, "results", f"rts_gpu_{d}.npz")
        if not os.path.exists(f):
            continue
        z = np.load(f, allow_pickle=True)
        A, F, C = z["A"].item(), list(z["F"]), z["C"].item()
        om = np.kron(z["w1"], z["w2"]) + z["D"]
        # comparison is against the CLEANED point: the raw one slightly violates ISO and its 𝒯 can exceed the max
        _, cl = GS.cleanup_gpu(GP.GState((d,) * 4), GP._t(z["w1"]), GP._t(z["w2"]), GP._t(z["D"]), A, F, C,
                               np.random.default_rng(0))
        rec = {"T_at_point_raw": R.T_value(om, A, F, C), "T_at_point": cl["T"], "q_noise": cl["q_noise"]}
        rec.update(certify((d,) * 4, A, F, C, iters=int(os.environ.get("RTS_DUAL_ITERS", "4000"))))
        rec["gap"] = rec["certified_upper_bound"] - rec["T_at_point"]
        out[f"d{d}"] = rec
        print(f"d={d}: value {rec['T_at_point']:.6f}, certificate {rec['certified_upper_bound']:.6f}, "
              f"gap {rec['gap']:.1e} ({rec['seconds']} s)", flush=True)
        with open(out_p, "w") as fh:
            json.dump(out, fh, ensure_ascii=False, indent=1, default=float)


if __name__ == "__main__":
    main()

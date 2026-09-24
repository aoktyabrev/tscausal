"""
RTS stage 1, S.2 — dual certificates at the operations that were FOUND (for every dimension of the scan).
Primal: max ⟨G, ω⟩ over ω ⪰ 0 with ISO marginals (OI is not required — the set is larger, so the bound is stronger).
Dual: min (Tr Y + Tr Z)/n subject to Y_{(A,C)}⊗I_{(B1,B2)} + I_{(A,C)}⊗Z_{(B1,B2)} − G ⪰ 0, n = dA·dC = dB1·dB2.
Any feasible (Y, Z) gives an upper bound; after the shift Y → Y + |λ_min| I, feasibility is checked by Cholesky.

This is NOT an upper bound for free operations: it refers to the specific operations. If the certificate
matches the value that was found, then the point is optimal for its own operations and the see-saw has squeezed
the state dry; whatever gap to the thresholds remains is down to the operations.
Result: results/json/rts_scan_dual.json.
"""
import json
import os
import sys
import time

import cvxpy as cp
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import polytope as P  # noqa: E402
import rts as R  # noqa: E402
import rts_seesaw as S  # noqa: E402


def perm_matrix(dims):
    """Pm: the order (A, C, B1, B2) → (A, B1, B2, C); Pm[new, old] = 1."""
    dA, dB1, dB2, dC = dims
    N = dA * dB1 * dB2 * dC
    Pm = np.zeros((N, N))
    for a, b1, b2, c in np.ndindex(dA, dB1, dB2, dC):
        new = ((a * dB1 + b1) * dB2 + b2) * dC + c
        old = ((a * dC + c) * dB1 + b1) * dB2 + b2
        Pm[new, old] = 1
    return Pm


def certify(dims, A, F, C, solver="SCS", max_iters=100000):
    dA, dB1, dB2, dC = dims
    nAC, nB = dA * dC, dB1 * dB2
    m = S.Model(dims, delta_basis=False)
    G = m.G(A, F, C)
    G = (G + G.T) / 2
    Pm = perm_matrix(dims)

    def lift(Y, Z):
        return Pm @ (np.kron(Y, np.eye(nB)) + np.kron(np.eye(nAC), Z)) @ Pm.T

    # a check on the lift: Tr[ω lift(Y,Z)] = Tr[m_AC(ω) Y] + Tr[m_B(ω) Z]
    rng = np.random.default_rng(0)
    Wt = rng.normal(size=(m.N, m.N)); Wt = Wt + Wt.T
    Yt = rng.normal(size=(nAC, nAC)); Yt = Yt + Yt.T
    Zt = rng.normal(size=(nB, nB)); Zt = Zt + Zt.T
    T8 = Wt.reshape(dA, dB1, dB2, dC, dA, dB1, dB2, dC)
    mAC = np.einsum("abcdebcf->adef", T8).reshape(nAC, nAC)
    mB = np.einsum("abcdafgd->bcfg", T8).reshape(nB, nB)
    lift_err = float(abs(np.trace(Wt @ lift(Yt, Zt)) - np.trace(mAC @ Yt) - np.trace(mB @ Zt)))

    Y = cp.Variable((nAC, nAC), symmetric=True)
    Z = cp.Variable((nB, nB), symmetric=True)
    L = Pm @ (cp.kron(Y, np.eye(nB)) + cp.kron(np.eye(nAC), Z)) @ Pm.T
    prob = cp.Problem(cp.Minimize((cp.trace(Y) + cp.trace(Z)) / nAC), [L - G >> 0])
    t0 = time.time()
    kw = {"eps": 1e-9, "max_iters": max_iters} if solver == "SCS" else {}
    prob.solve(solver=solver, **kw)
    sec = round(time.time() - t0, 1)
    Yv, Zv = (Y.value + Y.value.T) / 2, (Z.value + Z.value.T) / 2
    lam = float(np.linalg.eigvalsh(lift(Yv, Zv) - G).min())
    shift = max(0.0, -lam) + 1e-9
    Yc = Yv + shift * np.eye(nAC)
    M = lift(Yc, Zv) - G
    np.linalg.cholesky(M)                               # the feasibility certificate
    return {"solver": solver, "status": prob.status, "dual_value_raw": prob.value, "lift_check": lift_err,
            "lambda_min_raw": lam, "shift": shift,
            "certified_upper_bound": float((np.trace(Yc) + np.trace(Zv)) / nAC),
            "min_eig_certificate": float(np.linalg.eigvalsh(M).min()), "seconds": sec}


def main():
    S.limit_memory(float(os.environ.get("RTS_MEM_GB", "10")))
    fp = os.path.join(P.ROOT, "results", "json", "rts_scan_dual.json")
    out = json.load(open(fp)) if os.path.exists(fp) else {}      # merge: the solvers are run separately
    out["stage"] = "RTS1 S.2 сертификаты при найденных операциях"
    for d in json.loads(os.environ.get("RTS_DUAL_DIMS", "[2,4]")):
        f = os.path.join(P.ROOT, "results", f"rts_gpu_{d}.npz")
        if not os.path.exists(f):
            continue
        z = np.load(f, allow_pickle=True)
        A, F, C = z["A"].item(), list(z["F"]), z["C"].item()
        dims = (d,) * 4
        w1, w2, D = z["w1"], z["w2"], z["D"]
        om = np.kron(w1, w2) + D
        rec = {"T_at_point": R.T_value(om, A, F, C)}
        for solver in json.loads(os.environ.get("RTS_DUAL_SOLVERS", '["SCS"]')):
            try:
                rec[solver] = certify(dims, A, F, C, solver=solver)
            except (MemoryError, cp.error.SolverError, np.linalg.LinAlgError) as e:
                rec[solver] = {"failed": f"{type(e).__name__}: {str(e)[:200]}"}
        out.setdefault(f"d{d}", {}).update(rec)
        print(f"d={d}: {json.dumps(rec, ensure_ascii=False, default=float)}", flush=True)
    with open(fp, "w") as fh:
        json.dump(out, fh, ensure_ascii=False, indent=1, default=float)


if __name__ == "__main__":
    main()

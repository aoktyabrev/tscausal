"""
RTS stage 0, R.2.2 — строгая верхняя оценка max 𝒯 по всем вещественным ISO-процессам (без ОН) при операциях HW26.
Прямая: max Tr[W G], W ≥ 0, Tr_{B1B2} W = I/16 (на A,C), Tr_{AC} W = I/16 (на B1,B2).
Двойственная: min (Tr Y + Tr Z)/16 при  Y_{AC} ⊗ I_{B} + Z_{B} ⊗ I_{AC} − G ≥ 0 (в порядке A,B1,B2,C).
Любые (Y, Z) после сдвига Y → Y − λ_min I дают допустимую двойственную точку ⇒ строгая оценка (пересчёт eigvalsh
и Cholesky с запасом). Результат: results/json/rts_hw_iso_dual.json.
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
import rts_4444 as H  # noqa: E402
import rts_seesaw as S  # noqa: E402


def perm_matrix():
    """Pm: (a, c, b1, b2) → (a, b1, b2, c); Pm[new, old] = 1."""
    Pm = np.zeros((256, 256))
    for a, b1, b2, c in np.ndindex(4, 4, 4, 4):
        Pm[((a * 4 + b1) * 4 + b2) * 4 + c, ((a * 4 + c) * 4 + b1) * 4 + b2] = 1
    return Pm


PM = perm_matrix()


def lift(Y, Z):
    """Y на (A,C), Z на (B1,B2) → Y⊗I_B + I_AC⊗Z в порядке A,B1,B2,C."""
    return PM @ (np.kron(Y, np.eye(16)) + np.kron(np.eye(16), Z)) @ PM.T


def main():
    S.limit_memory(float(os.environ.get("RTS_MEM_GB", "5")))
    t0 = time.time()
    _, (omr, Ar, Fr, Cr) = R.main_cal()
    Fc = H.complete_bob(Fr)
    G = S.Model((4, 4, 4, 4)).G(Ar, Fc, Cr)
    G = (G + G.T) / 2
    # проверка lift: Tr[W lift(Y,Z)] = Tr[mAC(W) Y] + Tr[mB(W) Z]
    rng = np.random.default_rng(0)
    Wt = rng.normal(size=(256, 256)); Wt = Wt + Wt.T
    Yt = rng.normal(size=(16, 16)); Yt = Yt + Yt.T
    Zt = rng.normal(size=(16, 16)); Zt = Zt + Zt.T
    T8 = Wt.reshape([4] * 8)
    mAC = np.einsum("abcdebcf->adef", T8).reshape(16, 16)
    mB = np.einsum("abcdafgd->bcfg", T8).reshape(16, 16)
    lift_err = abs(np.trace(Wt @ lift(Yt, Zt)) - np.trace(mAC @ Yt) - np.trace(mB @ Zt))
    # двойственная SDP: переменные 16×16, PSD 256 — SCS
    Y = cp.Variable((16, 16), symmetric=True)
    Z = cp.Variable((16, 16), symmetric=True)
    Lexpr = PM @ (cp.kron(Y, np.eye(16)) + cp.kron(np.eye(16), Z)) @ PM.T
    prob = cp.Problem(cp.Minimize((cp.trace(Y) + cp.trace(Z)) / 16), [Lexpr - G >> 0])
    prob.solve(solver="SCS", eps=1e-9, max_iters=100000)
    Yv, Zv = (Y.value + Y.value.T) / 2, (Z.value + Z.value.T) / 2
    M = lift(Yv, Zv) - G
    lam = float(np.linalg.eigvalsh(M).min())
    shift = max(0.0, -lam) + 1e-9
    Yc = Yv + shift * np.eye(16)
    Mc = lift(Yc, Zv) - G
    np.linalg.cholesky(Mc)                                        # сертификат допустимости двойственной точки
    bound = float((np.trace(Yc) + np.trace(Zv)) / 16)
    out = {"stage": "RTS0 R.2.2 dual bound", "lift_check": float(lift_err), "status": prob.status,
           "dual_value_raw": prob.value, "lambda_min_raw": lam, "shift": shift,
           "certified_upper_bound": bound, "three_sqrt2": 3 * np.sqrt(2), "six_sqrt2": 6 * np.sqrt(2),
           "min_eig_certificate": float(np.linalg.eigvalsh(Mc).min()), "seconds": round(time.time() - t0, 1)}
    with open(os.path.join(P.ROOT, "results", "json", "rts_hw_iso_dual.json"), "w") as fh:
        json.dump(out, fh, ensure_ascii=False, indent=1, default=float)
    print(json.dumps(out, ensure_ascii=False, indent=1, default=float))


if __name__ == "__main__":
    main()

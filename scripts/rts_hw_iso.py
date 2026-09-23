"""
RTS stage 0, R.2.2: почему модель HW26 не лежит в вещественном ISO и можно ли заменить запрещённые члены.
1) разложение ω_HW по ребитовым шаблонам {I,J}^4 на (A',B1',B2',C'): вес, вклад в 𝒯, вклад в маргиналы ISO;
2) удаление только (A,C)-отклонения / только (B1,B2)-отклонения / обоих: min eig и 𝒯;
3) SDP: max 𝒯 по ВСЕМ вещественным ISO-ω (без ОН) при операциях HW (POVM Боба дополнен) — существует ли замена;
4) то же с ОН: ω = ω₁⊗ω₂ + Δ, чередование ω₁ / ω₂ / Δ при фиксированных операциях HW.
SDP 256×256 — SCS (Clarabel требует плотный KKT ≈ 8.7 ГБ). Результат: results/json/rts_hw_iso.json.
"""
import itertools
import json
import os
import sys
import time

import cvxpy as cp
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import polytope as P  # noqa: E402
import qproc as Q  # noqa: E402
import rts as R  # noqa: E402
import rts_4444 as H  # noqa: E402
import rts_4444_ext as E  # noqa: E402
import rts_seesaw as S  # noqa: E402

I2, J = np.eye(2), R.J
NAMES = ("A'", "B1'", "B2'", "C'")


def rebit_component(om, pat):
    """Компонента ω с шаблоном pat ∈ {I,J}^4 на ребитах (остальное — любые операторы на кубитах):
    ω_pat = Σ_q P_pat ⊗ X_q, выделяется сверткой: для ребита r с шаблоном I — (ρ + ZρZ + XρX + JρJᵀ)/4-проекция
    на span{I}; реализуем через частичные следы по ребитам с весом M/2 (M ∈ {I, J} ортогональны, Tr M Mᵀ = 2)."""
    T = om.reshape([2] * 16)          # (A',A,B1',B1,B2',B2,C',C) × то же
    Ms = [I2 if p == "I" else J for p in pat]
    # коэффициентный оператор на кубитах: X = Tr_rebits[(⊗ Mᵀ) ω] / 2^4
    X = np.einsum("aibjckdlAIBJCKDL,Aa,Bb,Cc,Dd->ijklIJKL", T, Ms[0].T, Ms[1].T, Ms[2].T, Ms[3].T) / 16
    comp = np.einsum("Aa,Bb,Cc,Dd,ijklIJKL->AiBjCkDlaIbJcKdL", *Ms, X)
    return comp.reshape(256, 256)


def main():
    S.limit_memory(float(os.environ.get("RTS_MEM_GB", "5")))
    t0 = time.time()
    rng = np.random.default_rng(22)
    out = {"stage": "RTS0 R.2.2 HW→ISO"}
    _, (omr, Ar, Fr, Cr) = R.main_cal()
    Fc = H.complete_bob(Fr)
    dims = (4, 4, 4, 4)
    T0 = R.T_value(omr, Ar, Fc, Cr)
    # 1) разложение
    comps, total = {}, np.zeros((256, 256))
    for pat in itertools.product("IJ", repeat=4):
        c = rebit_component(omr, pat)
        total += c
        name = "".join(f"J_{n}" for n, p in zip(NAMES, pat) if p == "J") or "I (без J)"
        md = R.marginals_ok(c + (np.eye(256) / 256 if pat != ("I",) * 4 else 0), dims) if np.abs(c).max() > 0 else (0, 0)
        comps[name] = {"norm": float(np.linalg.norm(c)), "T_contribution": R.T_value(c, Ar, Fc, Cr),
                       "AC_marginal_dev": md[0], "B_marginal_dev": md[1]}
    out["decomposition_check"] = float(np.abs(total - omr).max())
    out["components"] = {k: v for k, v in comps.items() if v["norm"] > 1e-12}
    # 2) удаление запрещённых частей по отдельности
    T8 = omr.reshape([4] * 8)
    mAC = np.einsum("abcdebcf->adef", T8).reshape(16, 16)
    mB = np.einsum("abcdafgd->bcfg", T8).reshape(16, 16)
    dAC, dB = mAC - np.eye(16) / 16, mB - np.eye(16) / 16
    tAC = np.einsum("acdf,be,gh->abgcdehf", dAC.reshape(4, 4, 4, 4), np.eye(4), np.eye(4)).reshape(256, 256) / 16
    tB = np.einsum("bcef,ad,gh->abcgdefh", dB.reshape(4, 4, 4, 4), np.eye(4), np.eye(4)).reshape(256, 256) / 16
    rem = {}
    for nm, w in (("без (A,C)-отклонения [J_A'J_C'…]", omr - tAC), ("без (B1,B2)-отклонения [J_B1'J_B2'…]", omr - tB),
                  ("без обоих", omr - tAC - tB)):
        lam = float(np.linalg.eigvalsh(w).min())
        p = max(0.0, -lam / (-lam + 1 / 256))
        rem[nm] = {"min_eig": lam, "T": R.T_value(w, Ar, Fc, Cr), "marginals_dev": R.marginals_ok(w, dims),
                   "OI_violation": R.oi_violation(w, dims, rng, 50), "noise_needed": p,
                   "T_after_noise": R.T_value((1 - p) * w + p * np.eye(256) / 256, Ar, Fc, Cr)}
    out["HW_T_completed_bob"] = T0
    out["removal"] = rem
    out["dev_AC_rank_eigs"] = sorted(set(np.round(np.linalg.eigvalsh(dAC), 10).tolist()))
    out["dev_B_rank_eigs"] = sorted(set(np.round(np.linalg.eigvalsh(dB), 10).tolist()))
    # 3) SDP без ОН при операциях HW
    G = S.Model(dims).G(Ar, Fc, Cr)
    W = cp.Variable((256, 256), symmetric=True)
    cons = [W >> 0] + S.marg_constraints(S.Model(dims), W)
    prob = cp.Problem(cp.Maximize(cp.sum(cp.multiply(W, G.T))), cons)
    t1 = time.time()
    prob.solve(solver="SCS", eps=1e-8, max_iters=50000)
    Wv = W.value
    lam = float(np.linalg.eigvalsh(Wv).min())
    p = max(0.0, (1e-9 - lam) / (1 / 256 - lam)) if lam < 1e-9 else 0.0
    Wf = (1 - p) * Wv + p * np.eye(256) / 256
    out["SDP_ISO_noOI_at_HW_ops"] = {"status": prob.status, "sdp_value": prob.value, "min_eig_raw": lam, "noise": p,
                                     "T_feasible": R.T_value(Wf, Ar, Fc, Cr), "marginals_dev": R.marginals_ok(Wf, dims),
                                     "OI_violation": R.oi_violation(Wf, dims, rng, 50),
                                     "seconds": round(time.time() - t1, 1)}
    print("SDP без ОН:", out["SDP_ISO_noOI_at_HW_ops"], flush=True)
    # 4) с ОН: чередование при фиксированных операциях HW
    m = S.Model(dims)
    w1, w2 = np.einsum("ajbj->ab", omr.reshape(16, 16, 16, 16)), np.einsum("jajb->ab", omr.reshape(16, 16, 16, 16))
    Dc, hist = np.zeros((256, 256)), []
    for it in range(int(os.environ.get("RTS_HWISO_ITERS", "8"))):
        Dc = S.solve_state(m, G, w1, w2, Dc, "D", True)
        for part in ("w1", "w2"):
            try:
                new = S.solve_state(m, G, w1, w2, Dc, part, True)
                w1, w2 = (new, w2) if part == "w1" else (w1, new)
            except Q.SolverFailure:
                pass
        hist.append(float(np.trace((np.kron(w1, w2) + Dc) @ G)))
        print(f"  ОН, фикс. операции HW, итерация {it}: {hist[-1]:.6f}", flush=True)
    cl = E.cleanup(m, w1, w2, Dc, Ar, Fc, Cr, rng)
    out["OI_alternation_at_HW_ops"] = {"history": hist, "cleanup": cl}
    out["seconds"] = round(time.time() - t0, 1)
    with open(os.path.join(P.ROOT, "results", "json", "rts_hw_iso.json"), "w") as fh:
        json.dump(out, fh, ensure_ascii=False, indent=1, default=float)
    print(json.dumps({k: v for k, v in out.items()}, ensure_ascii=False, indent=1, default=float))


if __name__ == "__main__":
    main()

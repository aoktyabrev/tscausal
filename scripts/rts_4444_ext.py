"""
RTS stage 0 — продолжение старта из точки HW26 при (4,4,4,4): в rts_4444.py он не сошёлся за 15 шагов Δ
(6.8805 и рост). Этап 2 see-saw (Δ + операции, ω₁, ω₂) до RTS_EXT_ITERS итераций; после каждой итерации
точка пишется в results/rts_4444_ext.npz (возобновляемо), значение — в results/json/rts_4444_ext.json.
В конце — очистка: точная проекция маргиналов ω₁, ω₂ и коэффициентов Δ на ограничения ISO (МНК-проекция),
затем примесь белого шума до ω ≥ 0 с запасом; 𝒯 пересчитывается независимо (rts.T_value).
"""
import json
import os
import sys
import time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import polytope as P  # noqa: E402
import qproc as Q  # noqa: E402
import rts as R  # noqa: E402
import rts_4444 as H  # noqa: E402
import rts_seesaw as S  # noqa: E402

NPZ = os.path.join(P.ROOT, "results", "rts_4444_ext.npz")
OUT = os.path.join(P.ROOT, "results", "json", "rts_4444_ext.json")


def fix_local(w, d1, d2):
    """Точная аффинная проекция: маргиналы w на d1 и d2 → I/d1, I/d2 (след 1), симметризация."""
    w = (w + w.T) / 2
    T = w.reshape(d1, d2, d1, d2)
    m1, m2 = np.einsum("ajbj->ab", T), np.einsum("jajb->ab", T)
    e1, e2 = m1 - np.eye(d1) / d1, m2 - np.eye(d2) / d2
    t = np.trace(w) - 1
    return w - np.kron(e1, np.eye(d2)) / d2 - np.kron(np.eye(d1), e2) / d1 + t * np.eye(d1 * d2) / (d1 * d2)


def fix_delta(m, D):
    """МНК-проекция коэффициентов Δ на ядро маргинальных ограничений (trB1ᵀ D trB2 = 0, trAᵀ D trC = 0)."""
    rows = []
    for L, Rm in ((m.trB1, m.trB2), (m.trA, m.trC)):
        for i in range(L.shape[1]):
            for j in range(Rm.shape[1]):
                if np.abs(L[:, i]).sum() and np.abs(Rm[:, j]).sum():
                    rows.append(np.outer(L[:, i], Rm[:, j]).reshape(-1))
    M = np.array(rows)
    x = D.reshape(-1)
    y = np.linalg.lstsq(M.T, x, rcond=None)[0] if len(rows) else 0
    return (x - M.T @ y).reshape(D.shape) if len(rows) else D


def coeffs_of(m, Dfull):
    """Коэффициенты D_kl по Δ (N×N): D_kl = ⟨a_k⊗a_l, Δ⟩ / 4."""
    return np.reshape(m.Ks @ Dfull.reshape(-1), (len(m.p1), len(m.p2))) / 4


def cleanup(m, w1, w2, Dfull, A, F, C, rng):
    w1c, w2c = fix_local(w1, 4, 4), fix_local(w2, 4, 4)
    D = fix_delta(m, coeffs_of(m, Dfull))
    om = np.kron(w1c, w2c) + m.delta(D)
    lam = float(np.linalg.eigvalsh(om).min())
    margin = 1e-9
    p = max(0.0, (margin - lam) / (1 / m.N - lam)) if lam < margin else 0.0
    omf = (1 - p) * om + p * np.eye(m.N) / m.N
    np.linalg.cholesky(omf)                      # сертификат ω > 0
    return {"T_raw": R.T_value(np.kron(w1, w2) + Dfull, A, F, C), "T_clean": R.T_value(omf, A, F, C),
            "noise": p, "min_eig_clean": float(np.linalg.eigvalsh(omf).min()),
            "iso_marginals_dev": R.marginals_ok(omf, m.dims), "oi_violation": R.oi_violation(omf, m.dims, rng, 100),
            "delta_rel_norm": float(np.linalg.norm(m.delta(D)) / np.linalg.norm(om)),
            "alice_ts": [float(sum(np.trace(A[x][a]) for x in A)) for a in (0, 1)],
            "charlie_ts": [float(sum(np.trace(C[z][c]) for z in C)) for c in (0, 1)],
            "bob_traces": [float(np.trace(f)) for f in F]}


def main():
    S.limit_memory(float(os.environ.get("RTS_MEM_GB", "6")))
    iters = int(os.environ.get("RTS_EXT_ITERS", "60"))
    rng = np.random.default_rng(4444)
    m = S.Model((4, 4, 4, 4))
    if os.path.exists(NPZ):
        z = np.load(NPZ, allow_pickle=True)
        w1, w2, Dc = z["w1"], z["w2"], z["Dc"]
        A, F, C = z["A"].item(), list(z["F"]), z["C"].item()
        hist = json.load(open(OUT))["history"]
    else:
        _, (omr, Ar, Fr, Cr) = R.main_cal()
        A, F, C = Ar, H.complete_bob(Fr), Cr
        T4 = omr.reshape(16, 16, 16, 16)
        w1, w2 = np.einsum("ajbj->ab", T4), np.einsum("jajb->ab", T4)
        Dc = np.zeros((m.N, m.N))
        hist = []
    t0 = time.time()
    while len(hist) < iters:
        t1 = time.time()
        om = np.kron(w1, w2) + Dc
        S.A_cur = None
        A = S.solve_ops_A(m, om, F, C, "A", 3, 6.0)
        S.A_cur = A
        C = S.solve_ops_A(m, om, F, C, "C", 6, 12.0)
        F = S.solve_F(m, om, A, C)
        G = m.G(A, F, C)
        Dc = S.solve_state(m, G, w1, w2, Dc, "D", True)
        for part in ("w1", "w2"):
            try:
                new = S.solve_state(m, G, w1, w2, Dc, part, True)
                w1, w2 = (new, w2) if part == "w1" else (w1, new)
            except Q.SolverFailure:
                pass
        val = float(np.trace((np.kron(w1, w2) + Dc) @ G).real)
        hist.append({"iter": len(hist), "T": val, "seconds": round(time.time() - t1, 1)})
        print(f"  итерация {len(hist) - 1}: 𝒯 = {val:.6f} ({hist[-1]['seconds']} с)", flush=True)
        np.savez(NPZ, w1=w1, w2=w2, Dc=Dc, A=np.array(A, dtype=object), F=np.array(F), C=np.array(C, dtype=object))
        with open(OUT, "w") as fh:
            json.dump({"stage": "RTS0 (4,4,4,4) HW-seed extension", "history": hist}, fh, ensure_ascii=False, indent=1)
        if len(hist) >= 3 and abs(hist[-1]["T"] - hist[-3]["T"]) < 1e-5:
            break
    out = {"stage": "RTS0 (4,4,4,4) HW-seed extension", "history": hist,
           "converged": len(hist) >= 3 and abs(hist[-1]["T"] - hist[-3]["T"]) < 1e-5,
           "cleanup": cleanup(m, w1, w2, Dc, A, F, C, rng), "solver_stats": dict(Q.STATS),
           "seconds_this_session": round(time.time() - t0, 1)}
    with open(OUT, "w") as fh:
        json.dump(out, fh, ensure_ascii=False, indent=1, default=float)
    print(json.dumps({k: v for k, v in out.items() if k != "history"}, ensure_ascii=False, indent=1, default=float))


if __name__ == "__main__":
    main()


def cleanup_oi(m, w1, w2, Dfull, A, F, C, rng, tol=1e-12):
    """Очистка, сохраняющая ОН точно: белый шум подмешивается в КАЖДЫЙ сомножитель (I/n1 ⊗ I/n2 — произведение),
    Δ масштабируется. ω(q) = w1(q) ⊗ w2(q) + (1−q) Δ, w_i(q) = (1−q) w_i + q I/n_i. Минимальное q подбирается
    делением отрезка до ω ≥ 0 (сертификат — Cholesky). ISO-маргиналы и ОН при этом точные, не приближённые."""
    w1c, w2c = fix_local(w1, 4, 4), fix_local(w2, 4, 4)
    D = m.delta(fix_delta(m, coeffs_of(m, Dfull)))

    def om_of(q):
        a = (1 - q) * w1c + q * np.eye(16) / 16
        b = (1 - q) * w2c + q * np.eye(16) / 16
        return np.kron(a, b) + (1 - q) * D

    lo, hi = 0.0, 1.0
    if np.linalg.eigvalsh(om_of(0.0)).min() > tol:
        hi = 0.0
    else:
        for _ in range(60):
            mid = (lo + hi) / 2
            if np.linalg.eigvalsh(om_of(mid)).min() > tol:
                hi = mid
            else:
                lo = mid
    om = om_of(hi)
    np.linalg.cholesky(om)
    return {"q_noise": hi, "T": R.T_value(om, A, F, C), "min_eig": float(np.linalg.eigvalsh(om).min()),
            "iso_marginals_dev": R.marginals_ok(om, m.dims), "oi_violation": R.oi_violation(om, m.dims, rng, 200),
            "delta_rel_norm": float(np.linalg.norm((1 - hi) * D) / np.linalg.norm(om))}

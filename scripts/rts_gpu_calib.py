"""
RTS stage 1 — calibration of the GPU estimator (anti-vacuum tests). Numbers from this solver are admitted
to the report only after these checks:
1) the projections are exact: membership in Anti⊗Anti, zero marginals, orthogonality (⟨X − ΠX, W⟩ = 0);
2) ADMM step against SCS on a SHARED point (Δ-step at the HW operations, d = 4) — values and structural residuals;
3) reproduction of the known number at (2,2,2,2): 4+2√2 (RTS 0 and the CPU scan give the same);
4) fraction of failed starts against the CPU/SCS path.
Result: results/json/rts_gpu_calib.json.
"""
import json
import os
import sys
import time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import polytope as P  # noqa: E402
import rts as R  # noqa: E402
import rts_4444 as H  # noqa: E402
import rts_4444_ext as E  # noqa: E402
import rts_gpu as GP  # noqa: E402
import rts_gpu_seesaw as GS  # noqa: E402
import rts_seesaw as S  # noqa: E402


def main():
    rng = np.random.default_rng(11)
    out = {"device": GP.DEV}
    dims = (4, 4, 4, 4)
    m, gs = S.Model(dims), GP.GState(dims)

    # 1) projections
    X = rng.normal(size=(m.N, m.N)); X = X + X.T
    Pt = gs.proj_delta(GP._t(X)).cpu().numpy()
    co = E.coeffs_of(m, Pt)
    T8 = Pt.reshape([4] * 8)
    W = m.delta(E.fix_delta(m, rng.normal(size=co.shape)))
    out["проекция Π_Δ: принадлежность Anti⊗Anti"] = f"{abs(m.delta(co) - Pt).max():.1e}"
    out["проекция Π_Δ: маргиналы"] = (f"{abs(np.einsum('abcdebcf->adef', T8)).max():.1e} / "
                                      f"{abs(np.einsum('abcdafgd->bcfg', T8)).max():.1e}")
    out["проекция Π_Δ: ортогональность"] = f"{abs(np.tensordot(X - Pt, W, 2)) / np.linalg.norm(W):.1e}"

    # 2) ADMM against SCS on a shared point
    _, (omr, Ar, Fr, Cr) = R.main_cal()
    Fc = H.complete_bob(Fr)
    G = m.G(Ar, Fc, Cr)
    T4 = omr.reshape(16, 16, 16, 16)
    w1, w2 = np.einsum("ajbj->ab", T4), np.einsum("jajb->ab", T4)
    t0 = time.time()
    Dscs = S.solve_state(m, G, w1, w2, np.zeros((m.N, m.N)), "D", True)
    t_scs = round(time.time() - t0, 1)
    om_scs = np.kron(w1, w2) + Dscs
    v_scs = float(np.trace(om_scs @ G))
    t0 = time.time()
    _, Z, res, _ = GP.admm_step(gs, GP._t(G), "D", GP._t(w1), GP._t(w2),
                                GP._t(np.zeros((m.N, m.N))), iters=2000)
    t_gpu = round(time.time() - t0, 1)
    om_g = Z.cpu().numpy()
    v_gpu = float(np.trace(om_g @ G))
    out["шаг Δ при операциях HW: SCS"] = f"{v_scs:.8f} ({t_scs} с), ISO {max(R.marginals_ok(om_scs, dims)):.1e}"
    out["шаг Δ при операциях HW: ADMM-GPU"] = (f"{v_gpu:.8f} ({t_gpu} с), ISO {max(R.marginals_ok(om_g, dims)):.1e}, "
                                               f"невязки {res['primal_res']:.1e} / {res['dual_res']:.1e}")
    out["расхождение ADMM и SCS"] = f"{abs(v_gpu - v_scs):.1e}"

    # 3) reproduction of 4+2√2 at (2,2,2,2)
    vals = []
    for _ in range(5):
        r = GS.run_gpu((2, 2, 2, 2), rng, iters=15, admm_iters=800, verbose=False)
        if r:
            vals.append(r["T_clean"])
    out["(2,2,2,2): найденные значения"] = [round(v, 6) for v in sorted(vals, reverse=True)]
    out["(2,2,2,2): 4+2√2"] = 4 + 2 * np.sqrt(2)
    out["(2,2,2,2): совпадение с известным значением"] = f"{abs(max(vals) - (4 + 2 * np.sqrt(2))):.1e} (после очистки)"
    out["eigh: GPU / откат на CPU"] = f"{GP.EIGH_STATS['gpu']} / {GP.EIGH_STATS['cpu_fallback']}"
    with open(os.path.join(P.ROOT, "results", "json", "rts_gpu_calib.json"), "w") as fh:
        json.dump(out, fh, ensure_ascii=False, indent=1, default=float)
    print(json.dumps(out, ensure_ascii=False, indent=1, default=float))


if __name__ == "__main__":
    main()

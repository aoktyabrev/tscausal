"""
RTS stage 0 — антивакуумная калибровка see-saw: тот же алгоритм с эрмитовыми (комплексными) переменными
при (2,2,2,2) и ISO-произведении ω₁⊗ω₂ из случайных стартов должен находить комплексное значение 6√2
(достигается стратегией RTW21, rts.renou_complex). Если находит — потолок 4+2√2 вещественных прогонов
не является дефектом оценщика. Результат: results/json/rts_calib.json.
"""
import json
import os
import sys
import time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import polytope as P  # noqa: E402
import qproc as Q  # noqa: E402
import rts_seesaw as S  # noqa: E402


def main():
    S.limit_memory(float(os.environ.get("RTS_MEM_GB", "4")))
    t0 = time.time()
    rng = np.random.default_rng(20260922)
    m = S.Model((2, 2, 2, 2), cplx=True)
    vals, failed, best = [], 0, None
    for s in range(int(os.environ.get("RTS_CAL_STARTS", "20"))):
        r = S.run(m, rng, False)
        if r is None:
            failed += 1
            continue
        vals.append(r[0])
        if best is None or r[0] > best[0]:
            best = r
        print(f"  complex (2,2,2,2) старт {s}: {r[0]:.6f}", flush=True)
    out = {"stage": "RTS0 calibration (complex see-saw)", "target_6sqrt2": 6 * np.sqrt(2),
           "values_sorted": sorted(vals, reverse=True), "failed": failed, "best": best[0] if best else None,
           "n_reaching_6sqrt2": sum(v > 6 * np.sqrt(2) - 1e-6 for v in vals),
           "n_above_4p2sqrt2": sum(v > 4 + 2 * np.sqrt(2) + 1e-6 for v in vals),
           "solver_stats": dict(Q.STATS), "seconds": round(time.time() - t0, 1)}
    if best:
        omega, A, F, C = best[1:]
        out["best_check"] = {"min_eig": float(np.linalg.eigvalsh((omega + omega.conj().T) / 2).min()),
                             "max_imag_state": float(np.abs(omega.imag).max()),
                             "max_imag_ops": float(max(np.abs(A[x][0].imag).max() for x in A))}
    with open(os.path.join(P.ROOT, "results", "json", "rts_calib.json"), "w") as fh:
        json.dump(out, fh, ensure_ascii=False, indent=1, default=float)
    print(json.dumps({k: v for k, v in out.items() if k != "values_sorted"}, ensure_ascii=False, indent=1, default=float))


if __name__ == "__main__":
    main()

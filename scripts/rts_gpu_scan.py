"""
RTS stage 1, S.1 — скан по размерности на GPU-пути (rts_gpu_seesaw.run_gpu).
План по умолчанию: d = 2, 4 (калибровка против CPU/SCS-скана `rts_scan.py`), затем 6 и 8.
Для каждой размерности: холодные старты (обязательны) и тёплый старт вложением лучшей точки предыдущей
размерности (обязательно рядом с холодными). Отчётное число — очищенное 𝒯 (пофакторный шум, ISO и ОН точные,
положительность по Холецкому); сырое приводится рядом.

Точность ADMM влияет только на то, насколько хорошую точку мы найдём: итоговое число считается заново на
строго допустимой точке, поэтому недосходимость ADMM занижает результат, а не завышает.
Результат: results/json/rts_gpu_scan.json, лучшие точки — results/rts_gpu_<d>.npz.
"""
import json
import os
import sys
import time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import polytope as P  # noqa: E402
import qproc as Q  # noqa: E402
import rts_gpu as GP  # noqa: E402
import rts_gpu_seesaw as GS  # noqa: E402
import rts_scan as SC  # noqa: E402

OUT = os.path.join(P.ROOT, "results", "json", "rts_gpu_scan.json")


def main():
    rng = np.random.default_rng(int(os.environ.get("RTS_SEED", "20260923")))
    # (d, число холодных стартов, итераций see-saw на фазу, итераций ADMM, бюджет секунд на размерность)
    plan = json.loads(os.environ.get("RTS_GPU_PLAN", "[[2,20,15,800,1800],[4,20,20,1200,9000]]"))
    out = json.load(open(OUT)) if os.path.exists(OUT) else {"stage": "RTS1 S.1 скан (GPU, ADMM)",
                                                            "device": GP.DEV}
    prev = None
    wf = os.environ.get("RTS_GPU_WARM_FROM")      # продолжение скана в новом процессе: тёплый старт из npz
    if wf:
        z = np.load(os.path.join(P.ROOT, "results", f"rts_gpu_{wf}.npz"), allow_pickle=True)
        prev = {"w1": z["w1"], "w2": z["w2"], "A": z["A"].item(), "F": list(z["F"]), "C": z["C"].item(),
                "d": int(wf)}
    for d, nst, iters, ai, budget in plan:
        dims = (d,) * 4
        t0 = time.time()
        recs = []
        if prev is not None:
            m = GS.S.Model(dims, delta_basis=False)
            warm = SC.warm_start(m, prev, rng)
            r = GS.run_gpu(dims, rng, iters=iters, admm_iters=ai, start=warm, verbose=False,
                           time_budget=budget / 2)
            if r:
                r["kind"] = "тёплый"
                recs.append(r)
                print(f"  d={d} тёплый: сырое {r['T_raw']:.6f} → очищенное {r['T_clean']:.6f} ({r['seconds']} с)",
                      flush=True)
        while len([r for r in recs if r.get("kind") == "холодный"]) < nst and time.time() - t0 < budget:
            r = GS.run_gpu(dims, rng, iters=iters, admm_iters=ai, verbose=False,
                           time_budget=max(60.0, budget - (time.time() - t0)))
            if r is None:
                recs.append({"kind": "холодный", "failed": "отказ солвера на шаге по операциям"})
                continue
            r["kind"] = "холодный"
            recs.append(r)
            print(f"  d={d} холодный {len(recs)}: сырое {r['T_raw']:.6f} → очищенное {r['T_clean']:.6f} "
                  f"({r['seconds']} с)", flush=True)
        ok = [r for r in recs if "T_clean" in r]
        best = max(ok, key=lambda r: r["T_clean"]) if ok else None
        cold = [r for r in ok if r["kind"] == "холодный"]
        rec = {"dims": list(dims), "n_success": len(ok), "n_failed": sum(1 for r in recs if "failed" in r),
               "n_cold": len(cold), "has_warm": any(r["kind"] == "тёплый" for r in ok),
               "T_clean_best": best["T_clean"] if best else None,
               "T_raw_best": best["T_raw"] if best else None, "best_kind": best["kind"] if best else None,
               "T_clean_best_cold": max((r["T_clean"] for r in cold), default=None),
               "T_clean_all": sorted((r["T_clean"] for r in ok), reverse=True),
               "cleanup_best": best["cleanup"] if best else None,
               "admm_last": best["admm_last"] if best else None,
               "seconds_per_start": [r.get("seconds") for r in recs],
               "wall_seconds": round(time.time() - t0, 1)}
        out[f"d{d}"] = rec
        with open(OUT, "w") as fh:
            json.dump(out, fh, ensure_ascii=False, indent=1, default=float)
        if best:
            p = best["point"]
            np.savez(os.path.join(P.ROOT, "results", f"rts_gpu_{d}.npz"), w1=p["w1"], w2=p["w2"], D=p["D"],
                     A=np.array(p["A"], dtype=object), F=np.array(p["F"]), C=np.array(p["C"]))
            prev = p
        print(f"d={d}: лучшее очищенное {rec['T_clean_best']}, успешных {rec['n_success']}, "
              f"упавших {rec['n_failed']}, {rec['wall_seconds']:.0f} с", flush=True)
    out["solver_stats"] = dict(Q.STATS)
    out["thresholds"] = {"4+2sqrt2": 4 + 2 * np.sqrt(2), "real_bound_RTW21": 7.6605, "6sqrt2": 6 * np.sqrt(2)}
    with open(OUT, "w") as fh:
        json.dump(out, fh, ensure_ascii=False, indent=1, default=float)


if __name__ == "__main__":
    main()

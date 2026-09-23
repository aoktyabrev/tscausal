"""
Монитор продолжения (4,4,4,4) (rts_4444_ext.py): при каждом обновлении results/rts_4444_ext.npz — невязки сырой
точки (min eig, маргиналы ISO, ОН, 𝒯) и очищенное 𝒯 (точная проекция на ограничения + шум до ω > 0).
Если очищенное 𝒯 растёт вместе с сырым — рост настоящий; если стоит — дрейф солвера.
Результат: results/json/rts_4444_ext_monitor.json. Предыдущие точки (итерации 0–11) не сохранялись.
"""
import json
import os
import sys
import time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rts as R  # noqa: E402
import rts_4444_ext as E  # noqa: E402
import rts_seesaw as S  # noqa: E402

OUT = os.path.join(os.path.dirname(E.OUT), "rts_4444_ext_monitor.json")


def main():
    S.limit_memory(3)
    m = S.Model((4, 4, 4, 4))
    rng = np.random.default_rng(99)
    recs = json.load(open(OUT)) if os.path.exists(OUT) else []
    last = None
    while True:
        try:
            mt = os.path.getmtime(E.NPZ)
            if mt != last:
                time.sleep(5)
                z = np.load(E.NPZ, allow_pickle=True)
                w1, w2, Dc = z["w1"], z["w2"], z["Dc"]
                A, F, C = z["A"].item(), list(z["F"]), z["C"].item()
                it = len(json.load(open(E.OUT))["history"]) - 1
                om = np.kron(w1, w2) + Dc
                rec = {"iter": it, "T_raw": R.T_value(om, A, F, C),
                       "min_eig_raw": float(np.linalg.eigvalsh((om + om.T) / 2).min()),
                       "iso_dev_raw": R.marginals_ok(om, m.dims),
                       "trace_w1_w2": [float(np.trace(w1)), float(np.trace(w2))],
                       "oi_raw": R.oi_violation(om, m.dims, rng, 30)}
                cl = E.cleanup(m, w1, w2, Dc, A, F, C, rng)
                rec.update({"T_clean": cl["T_clean"], "noise": cl["noise"], "min_eig_clean": cl["min_eig_clean"],
                            "iso_dev_clean": cl["iso_marginals_dev"], "oi_clean": cl["oi_violation"],
                            "delta_rel_norm": cl["delta_rel_norm"]})
                recs = [r for r in recs if r["iter"] != it] + [rec]
                with open(OUT, "w") as fh:
                    json.dump(recs, fh, ensure_ascii=False, indent=1, default=float)
                print(f"  iter {it}: raw {rec['T_raw']:.6f} (λmin {rec['min_eig_raw']:.1e}, ISO {max(rec['iso_dev_raw']):.1e}, "
                      f"ОН {rec['oi_raw']:.1e}) → clean {rec['T_clean']:.6f} (шум {rec['noise']:.1e})", flush=True)
                last = mt
        except Exception as e:  # noqa: BLE001 — файл мог писаться в этот момент
            print("  повтор:", type(e).__name__, str(e)[:100], flush=True)
            time.sleep(10)
            continue
        if not any(p for p in os.popen("pgrep -f rts_4444_ext.py").read().split()):
            break
        time.sleep(30)


if __name__ == "__main__":
    main()

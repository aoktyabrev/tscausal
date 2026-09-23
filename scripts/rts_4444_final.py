"""
RTS stage 0 — финальная точка продолжения (4,4,4,4): очистка сохранённой точки двумя способами (белый шум —
ломает ОН на уровне шума; пофакторный шум — ОН и ISO точные) и независимый пересчёт 𝒯.
Результат: results/json/rts_4444_final.json.
"""
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import polytope as P  # noqa: E402
import rts as R  # noqa: E402
import rts_4444_ext as E  # noqa: E402
import rts_seesaw as S  # noqa: E402


def main():
    S.limit_memory(4)
    rng = np.random.default_rng(7)
    m = S.Model((4, 4, 4, 4))
    z = np.load(E.NPZ, allow_pickle=True)
    w1, w2, Dc = z["w1"], z["w2"], z["Dc"]
    A, F, C = z["A"].item(), list(z["F"]), z["C"].item()
    hist = json.load(open(E.OUT))["history"]
    out = {"stage": "RTS0 (4,4,4,4) финальная точка", "iterations": len(hist),
           "T_raw_last": hist[-1]["T"], "T_raw_max": max(h["T"] for h in hist),
           "T_raw_max_iter": int(np.argmax([h["T"] for h in hist])),
           "cleanup_white_noise": E.cleanup(m, w1, w2, Dc, A, F, C, rng),
           "cleanup_OI_preserving": E.cleanup_oi(m, w1, w2, Dc, A, F, C, rng),
           "thresholds": {"4+2sqrt2": 4 + 2 * np.sqrt(2), "real_bound_RTW21": 7.6605, "6sqrt2": 6 * np.sqrt(2)}}
    with open(os.path.join(P.ROOT, "results", "json", "rts_4444_final.json"), "w") as fh:
        json.dump(out, fh, ensure_ascii=False, indent=1, default=float)
    print(json.dumps(out, ensure_ascii=False, indent=1, default=float))


if __name__ == "__main__":
    main()

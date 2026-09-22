"""
T3.1.e — дополнительные проверки N = 4 (дописываются в results/json/t31_extra.json):
суммы по строкам (необходимое условие TB — двоякостохастичность), кратности образов,
калибровка игры AGB17: буквальная проза против цели f(x).
"""
import itertools
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import polytope as P  # noqa: E402
import t31_extra as E  # noqa: E402
import t3_classical as TC  # noqa: E402
import t3_star as TS  # noqa: E402


def fl(T):
    return np.array([[float(v) for v in r] for r in T])


def main():
    p = os.path.join(P.ROOT, "results", "json", "t31_extra.json")
    d = json.load(open(p))
    A, Ab = E.T4(E.agb4), E.T4(E.agb4_bar)
    W4 = (A + Ab) / 2
    L, Lb = TC.det_T(TC.lugano), TC.det_T(TS.omega_bar)
    n = 4
    S = sorted({tuple(b[(k - s) % n] for k in range(n)) for b in ((1, 0, 0, 0), (1, 1, 0, 0)) for s in range(n)})
    prose = lambda x, k: x[(k - 1) % n] & (1 - x[(k + 1) % n])  # noqa: E731
    d["N4"]["row_sums_W4_star"] = fl(W4).sum(axis=1).tolist()
    d["N4"]["row_sums_W3_star_N3"] = fl((L + Lb) / 2).sum(axis=1).tolist()
    d["N4"]["image_multiplicities_agb"] = {"".join(map(str, i)): sum(1 for o in E.BITS4 if E.agb4(o) == i) for i in E.BITS4}
    d["N4"]["image_multiplicities_lugano_N3"] = {"".join(map(str, i)): sum(1 for o in TC.BITS3 if TC.lugano(o) == i) for i in TC.BITS3}
    d["N4"]["agb_prose_target_agrees_with_f_on"] = f"{sum(all(E.agb4(x)[k] == prose(x, k) for k in range(n)) for x in S)} из {len(S)}"
    # игра с целью f(x) на S, стратегия «переслать»
    fwd = TC.PERMS.index((0, 2, 1, 3))

    def fwd_value(T):
        tot = 0.0
        for x in S:
            for i in E.BITS4:
                q = [TC.PERMS[fwd][2 * x[k] + i[k]] for k in range(4)]
                if tuple(v >> 1 for v in q) == E.agb4(x):
                    tot += float(T[E.I4[i], E.I4[tuple(v & 1 for v in q)]]) / len(S)
        return tot
    d["N4"]["game_target_f_forward"] = {"agb": fwd_value(A), "mirror": fwd_value(Ab), "W4_star": fwd_value(W4)}
    json.dump(d, open(p, "w"), ensure_ascii=False, indent=1, default=str)
    print(json.dumps({k: v for k, v in d["N4"].items() if "multiplic" not in k}, ensure_ascii=False, indent=1, default=str))


if __name__ == "__main__":
    main()

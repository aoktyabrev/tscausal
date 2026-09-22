"""
T3.1 — проверка и структура свидетеля W*. Определения и прогнозы — PREREGISTRATION_T31.md.
b: значения игр на Лугано, зеркале, W*; инвариантность игр относительно полной инверсии;
c: группа G (Z₂⁶ ⋊ (S₃ × Z₂), 768 элементов): симметризация ½(L + gL) и орбитальные смеси;
d: все детерминированные трёхсторонние функции процесса, симметризуемость некаузальных.
Результат: results/json/t31.json.
"""
import itertools
import json
import os
import sys
import time
from fractions import Fraction

import numpy as np
from scipy.optimize import linprog

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import polytope as P  # noqa: E402
import t3_classical as TC  # noqa: E402
import t3_star as TS  # noqa: E402

F_ = Fraction
BITS3 = TC.BITS3
IDX = TC.IDX
FAST = os.environ.get("T31_FAST") == "1"

# ------------------------------------------------------------------ игры (Abbott et al.: входы x,y,z = доходы; выходы a,b,c = исходы)


def g_bw16(inc, out):
    return TC.win(inc, out)


def g_I1(inc, out):
    x, y, z = inc
    a, b, c = out
    return (x * y * ((a * b) ^ z)) == 0 and (y * z * ((b * c) ^ x)) == 0 and (x * z * ((a * c) ^ y)) == 0


def g_I2(inc, out):
    x, y, z = inc
    a, b, c = out
    return (x * (y ^ z ^ 1) * (a ^ (y * z))) == 0 and (y * (x ^ z ^ 1) * (b ^ (x * z))) == 0 and (z * (x ^ y ^ 1) * (c ^ (x * y))) == 0


def g_I3(inc, out):
    x, y, z = inc
    a, b, c = out
    return ((x * y * (z ^ 1) * (((a ^ 1) * b) ^ 1)) == 0 and (y * z * (x ^ 1) * (((b ^ 1) * c) ^ 1)) == 0
            and (x * z * (y ^ 1) * (((c ^ 1) * a) ^ 1)) == 0)


def g_I4(inc, out):
    x, y, z = inc
    a, b, c = out
    return ((x ^ y ^ z ^ 1) * ((((b ^ x ^ 1) * (c ^ y ^ 1) * (a ^ z ^ 1))) ^ 1)) == 0


GAMES_QUOTED = {"BW16": (g_bw16, F_(3, 4)), "I1": (g_I1, F_(7, 8)), "I2": (g_I2, F_(7, 8)),
                "I3": (g_I3, F_(7, 8)), "I4": (g_I4, F_(3, 4))}


def game_from_support(p):
    supp = {inc: {o for o in BITS3 if p[k * 8 + IDX[o]]} for k, inc in enumerate(BITS3)}
    return lambda inc, out: out in supp[inc]


def K_of(win):
    K = np.zeros((len(TS.OPS), 64))
    for n, (pA, pB, pC) in enumerate(TS.OPS):
        for inc in BITS3:
            for i in BITS3:
                outs, outcomes = [], []
                for perm, inc_x, i_x in zip((pA, pB, pC), inc, i):
                    q = perm[2 * inc_x + i_x]
                    outcomes.append(q >> 1)
                    outs.append(q & 1)
                if win(inc, tuple(outcomes)):
                    K[n, IDX[i] * 8 + IDX[tuple(outs)]] += 1 / 8
    return K


def causal_max(win, strat):
    return F_(max(sum(1 for k, inc in enumerate(BITS3) if win(inc, t[k])) for t in strat), 8)


# ------------------------------------------------------------------ группа G

def group():
    out = []
    for fI in BITS3:
        for fO in BITS3:
            for perm in itertools.permutations(range(3)):
                for tr in (0, 1):
                    out.append((fI, fO, perm, tr))
    return out


def apply(g, T):
    """(g·T)[i, o] = T[π(i) ⊕ fI, π(o) ⊕ fO]; затем транспонирование, если tr."""
    fI, fO, perm, tr = g
    R = np.empty_like(T)
    for i in BITS3:
        for o in BITS3:
            ii = tuple(i[perm[k]] ^ fI[k] for k in range(3))
            oo = tuple(o[perm[k]] ^ fO[k] for k in range(3))
            R[IDX[i], IDX[o]] = T[IDX[ii], IDX[oo]]
    return R.T.copy() if tr else R


def gname(g):
    fI, fO, perm, tr = g
    return f"fI={''.join(map(str, fI))},fO={''.join(map(str, fO))},π={''.join(map(str, perm))},T={tr}"


H8 = np.array([[(-1) ** sum(a * b for a, b in zip(s, x)) for x in BITS3] for s in BITS3])
FORBID = {cls: np.array([[not TC.allowed(TC.type_of(sI, sO), cls) for sO in BITS3] for sI in BITS3]) for cls in ("TF", "TB", "ISO")}


def member_fast(T):
    """Точная проверка классов для рациональных T (через целые: T·den)."""
    Tn = np.array([[float(v) for v in row] for row in T])
    C = H8 @ Tn @ H8.T
    col_ok = np.allclose(Tn.sum(axis=0), 1)
    pos = (Tn >= -1e-15).all()
    return {cls: bool(col_ok and pos and np.abs(C[FORBID[cls]]).max() < 1e-12) for cls in ("TF", "TB", "ISO")}


def separable_screen(T, cmat):
    """HiGHS: T ∈ conv(причинных функций)? Точное подтверждение — отдельно (cdd)."""
    r = linprog(np.zeros(cmat.shape[1]), A_eq=np.vstack([cmat, np.ones((1, cmat.shape[1]))]),
                b_eq=np.concatenate([np.array([[float(v) for v in row] for row in T]).reshape(64), [1.0]]),
                bounds=(0, None), method="highs")
    return r.status == 0


# ------------------------------------------------------------------ main

def main():
    t0 = time.time()
    out = {"stage": "T3.1", "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"), "fast": FAST}
    ctab = TC.causal_functions()
    cT = [TC.det_T(lambda o, t=t: t[o]) for t in ctab]
    cmat = np.array([[float(Tk[i, o]) for i in range(8) for o in range(8)] for Tk in cT]).T
    strat = TS.causal_strategies()
    out["n_causal_strategies"] = len(strat)
    L = TC.det_T(TC.lugano)
    Lb = TC.det_T(TS.omega_bar)
    Ws = (L + Lb) / 2
    fwd = TC.PERMS.index((0, 2, 1, 3))
    nf = fwd * 576 + fwd * 24 + fwd

    # ---------------- a': неявный прецедент W₃ (1403.7333) и тонкая настройка W*
    print("a': W3 и семейство qL+(1-q)L̄…", flush=True)
    W3 = np.empty((8, 8), dtype=object)
    for i in range(8):
        for o in range(8):
            W3[i, o] = F_(0)
    for o in BITS3:
        for r in (0, 1):
            i = (o[2] ^ r, o[0] ^ r, o[1] ^ r)
            W3[IDX[i], IDX[o]] += F_(1, 2)
    comp = {}
    for r in (0, 1):
        om = lambda o, r=r: (o[2] ^ r, o[0] ^ r, o[1] ^ r)  # noqa: E731
        comp[f"r={r}"] = {"valid_process_function": TC.valid_det(om)}
    cons3 = all(sum(W3[IDX[i], IDX[(fA[i[0]], fB[i[1]], fC[i[2]])]] for i in BITS3) == 1
                for fA, fB, fC in itertools.product(TC.LOCAL_F, repeat=3))
    Sarr0 = np.array([TS.corr_vector(t) for t in strat], float).T
    # корреляции W₃ при всех тройках TS-операций: есть ли вне причинного многогранника
    seen3, outside3 = {}, []
    for n in range(len(TS.OPS)):
        p = tuple(TS.correlations(W3, n))
        seen3.setdefault(p, n)
    for m, (p, n) in enumerate(seen3.items()):
        r = linprog(np.zeros(Sarr0.shape[1]), A_eq=np.vstack([Sarr0, np.ones((1, Sarr0.shape[1]))]),
                    b_eq=np.concatenate([np.array(p, float), [1.0]]), bounds=(0, None), method="highs")
        if r.status == 2:
            win3 = game_from_support(list(p))
            outside3.append({"ops_index": n, "support_game_causal_bound": str(causal_max(win3, strat)),
                             "W3_value": "1"})
            break
    out["a_W3"] = {"source": "1403.7333 стр. 276–286; 1507.01714 E_ex1", "components": comp,
                   "consistent_all_local_functions": cons3, "membership": TC.membership(W3),
                   "separable_exact_cdd": TC.separable(W3, cT), "distinct_correlations": len(seen3),
                   "checked_until_first_outside": m + 1, "outside_example": outside3}
    fam = []
    for q in (F_(1, 4), F_(2, 5), F_(1, 2), F_(3, 5), F_(3, 4)):
        M = q * L + (1 - q) * Lb
        fam.append({"q": str(q), "membership": TC.membership(M)})
    out["a_W_star_fine_tuning"] = fam

    # ---------------- b
    print("b: игры…", flush=True)
    games = dict(GAMES_QUOTED)
    games["G*"] = (game_from_support(TS.correlations(Ws, nf)), None)
    b = {}
    for name, (win, bound) in games.items():
        cm = causal_max(win, strat)
        K = K_of(win)
        inv = all(win(inc, out_) == win(tuple(1 - v for v in inc), tuple(1 - v for v in out_))
                  for inc in BITS3 for out_ in BITS3)
        row = {"quoted_causal_bound": str(bound) if bound is not None else None, "computed_causal_bound": str(cm),
               "calibration_bound_matches": (bound is None) or (cm == bound), "mirror_invariant": inv}
        for pname, T in (("Lugano", L), ("mirror", Lb), ("W_star", Ws)):
            Tf = np.array([[float(T[i, o]) for o in range(8)] for i in range(8)]).reshape(64)
            vals = K @ Tf
            nbest = int(np.argmax(vals))
            row[pname] = {"forward_strategy": str(TC.exact_game_value(T, nf) if name == "BW16" else
                                                  sum(TS.correlations(T, nf)[k * 8 + IDX[o]] for k, inc in enumerate(BITS3)
                                                      for o in BITS3 if win(inc, o)) / 8),
                          "max_over_TS_ops": round(float(vals[nbest]), 12),
                          "violates": float(vals[nbest]) > float(cm) + 1e-9}
        b[name] = row
    out["b_games"] = b

    # ---------------- c
    print("c: группа…", flush=True)
    G = group()
    stab = [g for g in G if np.array_equal(apply(g, L), L)]
    rows = []
    for g in G:
        gL = apply(g, L)
        M = (L + gL) / 2
        mem = member_fast(M)
        sep = separable_screen(M, cmat) if mem["TF"] else None
        rows.append({"g": gname(g), "gL_is_process": bool(np.allclose(np.array(gL, float).sum(axis=0), 1)),
                     "gL_equals_L": bool(np.array_equal(gL, L)), "gL_equals_mirror": bool(np.array_equal(gL, Lb)),
                     "membership": mem, "separable": sep})
    working = [r for r in rows if r["membership"]["ISO"] and r["separable"] is False]
    # точное подтверждение и корреляции для работающих g
    exact = []
    Sarr = np.array([TS.corr_vector(t) for t in strat], float).T
    for r in working:
        g = next(g for g in G if gname(g) == r["g"])
        M = (L + apply(g, L)) / 2
        cert = TS.certificate([M[i, o] for i in range(8) for o in range(8)],
                              [[float(Tk[i, o]) for i in range(8) for o in range(8)] for Tk in cT],
                              [[Tk[i, o] for i in range(8) for o in range(8)] for Tk in cT])
        pc = TS.correlations(M, nf)
        rc = linprog(np.zeros(Sarr.shape[1]), A_eq=np.vstack([Sarr, np.ones((1, Sarr.shape[1]))]),
                     b_eq=np.concatenate([np.array(pc, float), [1.0]]), bounds=(0, None), method="highs")
        exact.append({"g": r["g"], "mixture_equals_W_star": bool(np.array_equal(M, Ws)),
                      "process_certificate_exact": cert and cert.get("outside"),
                      "forward_correlation_outside": rc.status == 2})
    out["c_group"] = {"order": len(G), "stabilizer_of_Lugano": [gname(g) for g in stab],
                      "n_gL_process": sum(r["gL_is_process"] for r in rows),
                      "n_mix_in_TF": sum(r["membership"]["TF"] for r in rows),
                      "n_mix_in_ISO": sum(r["membership"]["ISO"] for r in rows),
                      "n_working": len(working), "working": exact,
                      "distinct_working_mixtures": len({tuple(map(str, ((L + apply(next(g for g in G if gname(g) == w['g']), L)) / 2).reshape(64)))
                                                        for w in working}),
                      "transpose_alone_in_ISO": next(r["membership"]["ISO"] for r in rows if r["g"] == gname(((0, 0, 0), (0, 0, 0), (0, 1, 2), 1)))}
    # орбитальные смеси: циклические подгруппы и крупные подгруппы
    print("c: орбиты…", flush=True)
    orb = []
    seen = set()
    for g in G:
        cyc = [L]
        cur = L
        for _ in range(12):
            cur = apply(g, cur)
            if np.array_equal(cur, L):
                break
            cyc.append(cur)
        key = tuple(sorted(tuple(map(str, C.reshape(64))) for C in cyc))
        if key in seen:
            continue
        seen.add(key)
        M = sum(cyc[1:], cyc[0]) / len(cyc)
        mem = member_fast(M)
        orb.append({"generator": gname(g), "orbit_size": len(cyc), "ISO": mem["ISO"],
                    "separable": separable_screen(M, cmat) if mem["TF"] else None})
    subgroups = {"Z2^6 (все инверсии)": [g for g in G if g[2] == (0, 1, 2) and g[3] == 0],
                 "S3 (перестановки)": [g for g in G if g[0] == (0, 0, 0) and g[1] == (0, 0, 0) and g[3] == 0],
                 "полная инверсия {1, inv}": [g for g in G if g[2] == (0, 1, 2) and g[3] == 0 and g[0] == g[1] and g[0] in ((0, 0, 0), (1, 1, 1))],
                 "диагональные инверсии (fI = fO)": [g for g in G if g[2] == (0, 1, 2) and g[3] == 0 and g[0] == g[1]]}
    for name, sg in subgroups.items():
        imgs = {tuple(map(str, apply(g, L).reshape(64))): apply(g, L) for g in sg}
        M = sum(list(imgs.values())[1:], list(imgs.values())[0]) / len(imgs)
        mem = member_fast(M)
        orb.append({"subgroup": name, "orbit_size": len(imgs), "ISO": mem["ISO"],
                    "separable": separable_screen(M, cmat) if mem["TF"] else None})
    out["c_orbits"] = {"cyclic_distinct": len(seen), "n_ISO_nonseparable": sum(1 for o in orb if o["ISO"] and o["separable"] is False),
                       "list": orb}

    # ---------------- d
    print("d: перебор функций процесса…", flush=True)
    tables = list(itertools.product((0, 1), repeat=4))       # ω_X как функция двух чужих выходов
    causal_set = {tuple(t[o] for o in BITS3) for t in ctab}
    valid, noncausal = [], []
    for tA, tB, tC in itertools.product(tables, repeat=3):
        om = {o: (tA[2 * o[1] + o[2]], tB[2 * o[0] + o[2]], tC[2 * o[0] + o[1]]) for o in BITS3}
        if not TC.valid_det(lambda o, m=om: m[o]):
            continue
        key = tuple(om[o] for o in BITS3)
        valid.append(key)
        if key not in causal_set:
            noncausal.append(key)
    # полнота кандидатов: функции, где вход зависит от собственного выхода, недопустимы (проверка на выборке)
    rng = np.random.default_rng(11)
    dep_ok = 0
    for _ in range(300):
        tab = [tuple(int(v) for v in rng.integers(0, 2, 3)) for _ in range(8)]
        om = dict(zip(BITS3, tab))
        own = any(om[o][k] != om[tuple(o[j] if j != k else 1 - o[j] for j in range(3))][k] for o in BITS3 for k in range(3))
        if own and TC.valid_det(lambda o, m=om: m[o]):
            dep_ok += 1
    # классы по Z₂⁶ ⋊ S₃ (без транспонирования: оно выводит из детерминированных процессов)
    G0 = [g for g in G if g[3] == 0]
    nc_T = {k: TC.det_T(lambda o, m=dict(zip(BITS3, k)): m[o]) for k in noncausal}
    classes, rep_of = [], {}
    for k in noncausal:
        if k in rep_of:
            continue
        orbit = set()
        for g in G0:
            gT = apply(g, nc_T[k])
            gk = tuple(BITS3[int(np.argmax([float(v) for v in gT[:, IDX[o]]]))] for o in BITS3)
            orbit.add(gk)
        for gk in orbit:
            rep_of[gk] = k
        classes.append({"rep": ["".join(map(str, v)) for v in k], "size": len(orbit & set(noncausal)),
                        "contains_lugano": tuple(TC.lugano(o) for o in BITS3) in orbit})
    # симметризуемость каждого некаузального
    sym = []
    for k in noncausal:
        T = nc_T[k]
        gs = []
        for g in G:
            M = (T + apply(g, T)) / 2
            mem = member_fast(M)
            if mem["ISO"] and not separable_screen(M, cmat):
                gs.append(gname(g))
        sym.append({"process": ["".join(map(str, v)) for v in k], "n_working_g": len(gs), "working_g": gs[:6]})
    out["d_enumeration"] = {"candidates": len(tables) ** 3, "valid": len(valid), "causal_among_valid": len(valid) - len(noncausal),
                            "noncausal": len(noncausal), "own_dependence_valid_in_random_sample_of_300": dep_ok,
                            "classes_under_Z2^6xS3": classes, "n_symmetrizable": sum(1 for s in sym if s["n_working_g"] > 0),
                            "symmetrizable": sym}
    out["seconds"] = round(time.time() - t0, 1)
    with open(os.path.join(P.ROOT, "results", "json", "t31.json"), "w") as fh:
        json.dump(out, fh, ensure_ascii=False, indent=1, default=str)
    brief = {"b_games": {k: {kk: vv for kk, vv in v.items()} for k, v in b.items()},
             "c": {k: v for k, v in out["c_group"].items() if k != "working"},
             "c_working": out["c_group"]["working"][:10],
             "c_orbits": {k: v for k, v in out["c_orbits"].items() if k != "list"},
             "d": {k: v for k, v in out["d_enumeration"].items() if k not in ("symmetrizable",)},
             "seconds": out["seconds"]}
    print(json.dumps(brief, ensure_ascii=False, indent=1, default=str))


if __name__ == "__main__":
    main()

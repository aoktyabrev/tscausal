"""
T3.1 — дополнение:
(1) [разведка] 15 орбитальных смесей ∈ ISO₃ и неразделимых, найденных в t31 (кроме W*): различны ли, совпадают ли с W*/W₃,
    выходят ли корреляции за причинный многогранник (перебор троек TS-операций до первой внешней), значения I₁…I₄;
(2) T3.1.e: N = 4, процесс AGB17/TC20; симметризация полной инверсией; ISO₄ (правило D10); игра AGB17 (граница 1 − 1/n);
(3) калибровка N = 2: ни одна симметризация двусторонних детерминированных процессов не неразделима в ISO₂ (D6).
Результат: results/json/t31_extra.json.
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
import t31  # noqa: E402

F_ = Fraction
BITS3 = TC.BITS3
IDX = TC.IDX


def tkey(T):
    return tuple(str(v) for v in np.asarray(T).reshape(-1))


# ------------------------------------------------------------------ (1) орбитальные смеси

def orbit_mixtures():
    G = t31.group()
    L = TC.det_T(TC.lugano)
    res = []
    seen = set()
    for g in G:
        cyc, cur = [L], L
        for _ in range(12):
            cur = t31.apply(g, cur)
            if np.array_equal(cur, L):
                break
            cyc.append(cur)
        M = sum(cyc[1:], cyc[0]) / len(cyc)
        k = tkey(M)
        if k in seen:
            continue
        mem = t31.member_fast(M)
        if not mem["ISO"]:
            continue
        seen.add(k)
        res.append((t31.gname(g), len(cyc), M, [bool(np.allclose(np.array(C, float).sum(axis=0), 1)) for C in cyc]))
    return res


_K = {}


def analyse(M, strat, Sarr, cT):
    sep = TC.separable(M, cT)
    seen = {}
    for n in range(len(TS.OPS)):
        seen.setdefault(tuple(TS.correlations(M, n)), n)
    first_out = None
    for m, (p, n) in enumerate(seen.items()):
        r = linprog(np.zeros(Sarr.shape[1]), A_eq=np.vstack([Sarr, np.ones((1, Sarr.shape[1]))]),
                    b_eq=np.concatenate([np.array(p, float), [1.0]]), bounds=(0, None), method="highs")
        if r.status == 2:
            win = t31.game_from_support(list(p))
            first_out = {"ops_index": n, "support_game_causal_bound": str(t31.causal_max(win, strat)), "checked": m + 1}
            break
    games = {}
    for name, (win, bound) in t31.GAMES_QUOTED.items():
        if name not in _K:
            _K[name] = t31.K_of(win)
        K = _K[name]
        v = float((K @ np.array([float(x) for x in np.asarray(M).reshape(-1)])).max())
        games[name] = {"max_TS": round(v, 12), "bound": str(bound), "violates": v > float(bound) + 1e-9}
    return {"separable_exact": sep, "distinct_correlations": len(seen), "first_outside": first_out, "quoted_games": games}


# ------------------------------------------------------------------ (2) N = 4

BITS4 = list(itertools.product((0, 1), repeat=4))
I4 = {t: k for k, t in enumerate(BITS4)}


def agb4(o):
    """TC20 (стр. 338–343): a_1 = x_4(x_2⊕1)(x_3⊕1), a_2 = x_1(x_4⊕1)(x_3⊕1), a_3 = x_2(x_1⊕1)(x_4⊕1), a_4 = x_3(x_2⊕1)(x_1⊕1)."""
    x1, x2, x3, x4 = o
    return (x4 * (1 - x2) * (1 - x3), x1 * (1 - x4) * (1 - x3), x2 * (1 - x1) * (1 - x4), x3 * (1 - x2) * (1 - x1))


def agb4_bar(o):
    return tuple(1 - v for v in agb4(tuple(1 - u for u in o)))


def T4(omega):
    T = np.zeros((16, 16), dtype=object)
    T[:] = F_(0)
    for o in BITS4:
        T[I4[omega(o)], I4[o]] = F_(1)
    return T


def valid4(omega):
    for fs in itertools.product(TC.LOCAL_F, repeat=4):
        n = sum(1 for i in BITS4 if omega(tuple(fs[k][i[k]] for k in range(4))) == i)
        if n != 1:
            return False
    return True


def iso4(T):
    H = np.array([[(-1) ** sum(a * b for a, b in zip(s, x)) for x in BITS4] for s in BITS4])
    Tn = np.array([[float(v) for v in row] for row in T])
    C = H @ Tn @ H.T
    bad = 0.0
    for sI in BITS4:
        for sO in BITS4:
            ty = [{(0, 0): "-", (1, 0): "I", (0, 1): "O", (1, 1): "IO"}[(sI[k], sO[k])] for k in range(4)]
            if all(t == "-" for t in ty):
                continue
            hasI, hasO = "I" in ty, "O" in ty
            if not (hasI and hasO):
                bad = max(bad, abs(C[I4[sI], I4[sO]]))
    tf_bad = max(abs(C[I4[sI], I4[sO]]) for sI in BITS4 for sO in BITS4
                 if any(sI) or any(sO)
                 if not any(sI[k] and not sO[k] for k in range(4)))
    tb_bad = max(abs(C[I4[sI], I4[sO]]) for sI in BITS4 for sO in BITS4
                 if any(sI) or any(sO)
                 if not any(sO[k] and not sI[k] for k in range(4)))
    return {"TF": tf_bad < 1e-12 and np.allclose(Tn.sum(axis=0), 1), "TB": tb_bad < 1e-12, "ISO": bad < 1e-12}


def agb_game_value(T, n=4):
    """Игра AGB17 (стр. 336–366): входы x ∈ S (2n сдвигов 1000…, 1100…), выигрыш a_k = x_{k-1} ∧ ¬x_{k+1};
    максимум по TS-биекциям (24⁴ четвёрок) — векторизовано. Возвращает (максимум, «переслать»)."""
    S = set()
    for base in ((1, 0, 0, 0), (1, 1, 0, 0)):
        for s in range(n):
            S.add(tuple(base[(k - s) % n] for k in range(n)))
    S = sorted(S)
    perms = TC.PERMS
    P_ = np.array(perms)                                       # (24, 4): индекс 2*доход+вход -> 2*исход+выход
    combos = np.array(list(itertools.product(range(24), repeat=4)), dtype=np.int16)   # (331776, 4)
    Tn = np.array([[float(v) for v in row] for row in T])
    succ = np.zeros(len(combos))
    fwd = perms.index((0, 2, 1, 3))
    succ_fwd = 0.0
    for x in S:
        target = tuple(x[(k - 1) % n] & (1 - x[(k + 1) % n]) for k in range(n))
        for i in BITS4:
            q = np.stack([P_[combos[:, k], 2 * x[k] + i[k]] for k in range(4)], axis=1)   # (N,4)
            outc, outs = q >> 1, q & 1
            oidx = outs[:, 0] * 8 + outs[:, 1] * 4 + outs[:, 2] * 2 + outs[:, 3]
            w = Tn[I4[i], :][oidx]
            ok = np.all(outc == np.array(target), axis=1)
            succ += w * ok / len(S)
            qf = [perms[fwd][2 * x[k] + i[k]] for k in range(4)]
            of = tuple(v & 1 for v in qf)
            if tuple(v >> 1 for v in qf) == target:
                succ_fwd += float(T[I4[i], I4[of]]) / len(S)
    return float(succ.max()), succ_fwd


# ------------------------------------------------------------------ (3) N = 2

def bipartite_calibration():
    BITS2 = list(itertools.product((0, 1), repeat=2))
    I2 = {t: k for k, t in enumerate(BITS2)}
    funcs = list(itertools.product((0, 1), repeat=2))
    valid = []
    for fA in funcs:
        for fB in funcs:
            om = lambda o, fA=fA, fB=fB: (fA[o[1]], fB[o[0]])  # noqa: E731
            ok = all(sum(1 for i in BITS2 if om((gA[i[0]], gB[i[1]])) == i) == 1 for gA in funcs for gB in funcs)
            if ok:
                valid.append(om)
    # причинные двусторонние функции: одна сторона получает константу, другая — функцию выхода первой
    causal = []
    for first in (0, 1):
        for c in (0, 1):
            for h in funcs:
                causal.append(lambda o, first=first, c=c, h=h: (c, h[o[0]]) if first == 0 else (h[o[1]], c))

    def Tm(om):
        T = np.zeros((4, 4))
        for o in BITS2:
            T[I2[om(o)], I2[o]] = 1
        return T
    cmat = np.array([Tm(om).reshape(16) for om in causal]).T
    H = np.array([[(-1) ** sum(a * b for a, b in zip(s, x)) for x in BITS2] for s in BITS2])
    n_iso, n_iso_nonsep = 0, 0
    for om in valid:
        T = Tm(om)
        for fI in BITS2:
            for fO in BITS2:
                for perm in ((0, 1), (1, 0)):
                    for tr in (0, 1):
                        R = np.empty_like(T)
                        for i in BITS2:
                            for o in BITS2:
                                ii = tuple(i[perm[k]] ^ fI[k] for k in range(2))
                                oo = tuple(o[perm[k]] ^ fO[k] for k in range(2))
                                R[I2[i], I2[o]] = T[I2[ii], I2[oo]]
                        if tr:
                            R = R.T
                        M = (T + R) / 2
                        C = H @ M @ H.T
                        iso = np.allclose(M.sum(axis=0), 1) and all(
                            abs(C[I2[sI], I2[sO]]) < 1e-12 for sI in BITS2 for sO in BITS2
                            if (any(sI) or any(sO)) and not (any(sI[k] and not sO[k] for k in range(2))
                                                             and any(sO[k] and not sI[k] for k in range(2))))
                        if iso:
                            n_iso += 1
                            r = linprog(np.zeros(cmat.shape[1]), A_eq=np.vstack([cmat, np.ones((1, cmat.shape[1]))]),
                                        b_eq=np.concatenate([M.reshape(16), [1.0]]), bounds=(0, None), method="highs")
                            if r.status != 0:
                                n_iso_nonsep += 1
    return {"valid_bipartite_deterministic": len(valid), "all_valid_causal": all(
        any(np.array_equal(Tm(v), Tm(c)) for c in causal) for v in valid),
        "symmetrizations_in_ISO2": n_iso, "nonseparable_among_them": n_iso_nonsep}


def main():
    t0 = time.time()
    out = {"stage": "T3.1 extra", "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S")}
    strat = TS.causal_strategies()
    Sarr = np.array([TS.corr_vector(t) for t in strat], float).T
    ctab = TC.causal_functions()
    cT = [TC.det_T(lambda o, t=t: t[o]) for t in ctab]
    Ws = (TC.det_T(TC.lugano) + TC.det_T(TS.omega_bar)) / 2
    print("(1) орбитальные смеси…", flush=True)
    rows = []
    for name, size, M, comps_are_processes in orbit_mixtures():
        a = {"generator": name, "orbit_size": size, "components_are_processes": comps_are_processes,
             "equals_W_star": bool(np.array_equal(M, Ws))}
        if TC.separable(M, cT):
            a["separable_exact"] = True
        else:
            a.update(analyse(M, strat, Sarr, cT))
        a["T"] = [[str(v) for v in row] for row in M]
        rows.append(a)
        print(f"   {name}: size {size}, W*={a['equals_W_star']}, sep={a.get('separable_exact')}, "
              f"out={a.get('first_outside')}", flush=True)
    out["orbit_mixtures_ISO"] = rows
    print("(2) N = 4…", flush=True)
    A, Ab = T4(agb4), T4(agb4_bar)
    W4 = (A + Ab) / 2
    out["N4"] = {"source": "TC20 стр. 338–343 (= AGB17 стр. 334 при n = 4); игра — AGB17 стр. 350–366",
                 "agb_valid": valid4(agb4), "mirror_valid": valid4(agb4_bar),
                 "agb_membership": iso4(A), "W4_star_membership": iso4(W4),
                 "agb_game": agb_game_value(A), "mirror_game": agb_game_value(Ab), "W4_star_game": agb_game_value(W4),
                 "causal_bound_quoted": "1 - 1/n = 3/4"}
    print("(3) N = 2…", flush=True)
    out["N2_calibration"] = bipartite_calibration()
    out["seconds"] = round(time.time() - t0, 1)
    with open(os.path.join(P.ROOT, "results", "json", "t31_extra.json"), "w") as fh:
        json.dump(out, fh, ensure_ascii=False, indent=1, default=str)
    print(json.dumps({"N4": out["N4"], "N2": out["N2_calibration"], "seconds": out["seconds"]}, ensure_ascii=False, indent=1, default=str))


if __name__ == "__main__":
    main()

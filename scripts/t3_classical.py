"""
T3.0, items T.1 and T.2 (classical). Definitions — PREREGISTRATION_T3.md; citations — SOURCES.md (BW16, WBO23, BCRWZ19).

Classical tripartite process: T(i|o), i = (i_A,i_B,i_C) — inputs, o = (o_A,o_B,o_C) — outputs.
For deterministic local operations f (input → output) the probability of a "consistent history":
P = Σ_i T(i | f(i)). The BW16 game (example 2) with TS operations: each party has a bijection
(income, input) ↔ (outcome, output); incomes are uniform.
"""
import itertools
import json
import os
import sys
import time
from fractions import Fraction

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import polytope as P  # noqa: E402
import cdd.gmp as cddg  # noqa: E402

F_ = Fraction
BITS3 = list(itertools.product((0, 1), repeat=3))
IDX = {t: k for k, t in enumerate(BITS3)}


def lugano(o):
    a, b, c = o
    return ((1 - b) & c, a & (1 - c), (1 - a) & b)


def det_T(omega):
    """Matrix T[i, o] of a deterministic process."""
    T = np.zeros((8, 8), dtype=object)
    for o in BITS3:
        T[IDX[omega(o)], IDX[o]] = F_(1)
    for i in range(8):
        for o in range(8):
            if T[i, o] == 0:
                T[i, o] = F_(0)
    return T


# ------------------------------------------------------------------ validity and ISO_3

LOCAL_F = list(itertools.product((0, 1), repeat=2))          # f(0), f(1): all functions bit → bit


def valid_det(omega):
    """BCRWZ19: for every set of local functions w∘f has exactly one fixed point."""
    for fA, fB, fC in itertools.product(LOCAL_F, repeat=3):
        n = 0
        for i in BITS3:
            o = (fA[i[0]], fB[i[1]], fC[i[2]])
            if omega(o) == i:
                n += 1
        if n != 1:
            return False
    return True


def walsh(T):
    """Coefficients of W = Σ T(i|o)|i⟩⟨i|⊗|o⟩⟨o| in Z-products: c[sI, sO] = (1/64) Σ T(i|o) χ_sI(i) χ_sO(o)."""
    c = {}
    for sI in BITS3:
        for sO in BITS3:
            tot = F_(0)
            for i in BITS3:
                for o in BITS3:
                    if T[IDX[i], IDX[o]]:
                        sign = (-1) ** (sum(a * b for a, b in zip(sI, i)) + sum(a * b for a, b in zip(sO, o)))
                        tot += T[IDX[i], IDX[o]] * sign
            c[(sI, sO)] = tot / 64
    return c


def type_of(sI, sO):
    return tuple({(0, 0): "-", (1, 0): "I", (0, 1): "O", (1, 1): "IO"}[(sI[k], sO[k])] for k in range(3))


def allowed(ty, cls):
    if all(t == "-" for t in ty):
        return True
    hasI, hasO = "I" in ty, "O" in ty
    return {"TF": hasI, "TB": hasO, "ISO": hasI and hasO}[cls]


def membership(T):
    """Linear conditions for classes TF/TB/ISO (rule verified in T.0) + normalisation Σ_i T = 1 + positivity."""
    c = walsh(T)
    res = {}
    for cls in ("TF", "TB", "ISO"):
        bad = [(sI, sO) for (sI, sO), v in c.items() if v != 0 and not allowed(type_of(sI, sO), cls)]
        res[cls] = (not bad) and c[((0, 0, 0), (0, 0, 0))] == F_(1, 8) and all(T[i, o] >= 0 for i in range(8) for o in range(8))
    return res


# ------------------------------------------------------------------ BW16 game with TS operations

PERMS = list(itertools.permutations(range(4)))               # bijection (income, input) -> (outcome, output), index 2*first+second


def win(inc, out):
    a, b, c = inc
    x, y, z = out
    if (a + b + c) >= 2:
        return x == 1 - b and y == 1 - c and z == 1 - a
    return x == c and y == a and z == b


def build_K():
    """K[ops, i, o]: contribution of T[i, o] to the win probability for TS-bijection triple ops (uniform incomes)."""
    K = np.zeros((len(PERMS) ** 3, 8, 8))
    for n, (pA, pB, pC) in enumerate(itertools.product(PERMS, repeat=3)):
        for inc in BITS3:
            for i in BITS3:
                outs, outcomes = [], []
                for perm, inc_x, i_x in zip((pA, pB, pC), inc, i):
                    k = perm[2 * inc_x + i_x]
                    outcomes.append(k >> 1)
                    outs.append(k & 1)
                if win(inc, tuple(outcomes)):
                    K[n, IDX[i], IDX[tuple(outs)]] += 1 / 8
    return K.reshape(len(PERMS) ** 3, 64)


def game_value(T, K):
    Tf = np.array([[float(T[i, o]) for o in range(8)] for i in range(8)]).reshape(64)
    vals = K @ Tf
    n = int(np.argmax(vals))
    return float(vals[n]), n


def exact_game_value(T, n):
    """Exact recomputation of the win value (Fraction) for the operation triple with index n."""
    pA, pB, pC = list(itertools.product(PERMS, repeat=3))[n]
    tot = F_(0)
    for inc in BITS3:
        for i in BITS3:
            outs, outcomes = [], []
            for perm, inc_x, i_x in zip((pA, pB, pC), inc, i):
                k = perm[2 * inc_x + i_x]
                outcomes.append(k >> 1)
                outs.append(k & 1)
            if win(inc, tuple(outcomes)):
                tot += T[IDX[i], IDX[tuple(outs)]] / 8
    return tot


# ------------------------------------------------------------------ causal ordering

def causal_functions():
    """Deterministic process functions with a (dynamic) causal order: the first party — a constant, the second
    (which party it is may depend on the first output) — a function of it, the third — of the first two outputs."""
    out = set()
    for first in range(3):
        others = [k for k in range(3) if k != first]
        for c0 in (0, 1):
            branch_opts = []
            for o1 in (0, 1):                                    # for each output of the first party
                opts = []
                for second in others:
                    third = [k for k in others if k != second][0]
                    for v2 in (0, 1):                            # input of the second (given o1)
                        for v3 in itertools.product((0, 1), repeat=2):   # input of the third as a function of o2
                            opts.append((second, third, v2, v3))
                branch_opts.append(opts)
            for b0, b1 in itertools.product(*branch_opts):
                table = []
                for o in BITS3:
                    br = (b0, b1)[o[first]]
                    second, third, v2, v3 = br
                    i = [0, 0, 0]
                    i[first] = c0
                    i[second] = v2
                    i[third] = v3[o[second]]
                    table.append(tuple(i))
                out.add(tuple(table))
    return [dict(zip(BITS3, t)) for t in out]


def separable(T, causal_Ts):
    """Exact LP (cdd.gmp): T ∈ conv{T_k}? Variables λ_k ≥ 0, Σλ = 1, Σλ T_k = T."""
    n = len(causal_Ts)
    rows, lin = [], []
    for i in range(8):
        for o in range(8):
            lin.append(len(rows))
            rows.append([-T[i, o]] + [Tk[i, o] for Tk in causal_Ts])
    lin.append(len(rows))
    rows.append([F_(-1)] + [F_(1)] * n)
    for k in range(n):
        rows.append([F_(0)] + [F_(1) if j == k else F_(0) for j in range(n)])
    mat = cddg.matrix_from_array(rows, lin_set=lin, rep_type=cddg.RepType.INEQUALITY,
                                 obj_type=cddg.LPObjType.MAX, obj_func=[F_(0)] * (n + 1))
    lp = cddg.linprog_from_matrix(mat)
    cddg.linprog_solve(lp)
    return lp.status == cddg.LPStatusType.OPTIMAL


# ------------------------------------------------------------------ main

def main():
    t0 = time.time()
    out = {"stage": "T3.0/T.1-T.2 classical", "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S")}
    print("building K", flush=True)
    K = build_K()
    print("K ready", flush=True)
    ctab = causal_functions()
    causal_Ts = [det_T(lambda o, t=t: t[o]) for t in ctab]
    out["n_causal_functions"] = len(ctab)
    out["causal_functions_all_valid"] = all(valid_det(lambda o, t=t: t[o]) for t in ctab)

    # T.1(a): Lugano
    TL = det_T(lugano)
    vL, nL = game_value(TL, K)
    fwd = PERMS.index((0, 2, 1, 3))      # (income, input) -> (outcome = input, output = income): k = 2*i + a
    out["T1a"] = {"valid": valid_det(lugano), "membership": membership(TL),
                  "game_max_TS": vL, "game_exact": str(exact_game_value(TL, nL)),
                  "forward_strategy_value": str(exact_game_value(TL, fwd * 24 * 24 + fwd * 24 + fwd)),
                  "causally_separable": separable(TL, causal_Ts),
                  "image_multiplicities": {"".join(map(str, i)): sum(1 for o in BITS3 if lugano(o) == i) for i in BITS3}}

    # calibration: a causal function is separable; the game on causal functions ≤ 3/4
    out["calibration"] = {"causal_example_separable": separable(causal_Ts[0], causal_Ts),
                          "max_game_over_causal_functions": max(game_value(Tk, K)[0] for Tk in causal_Ts)}

    # T.1(b): canonical XOR extension, P uniform, F discarded
    Tb = np.zeros((8, 8), dtype=object)
    for i in range(8):
        for o in range(8):
            Tb[i, o] = F_(0)
    for p in BITS3:
        for o in BITS3:
            i = tuple(x ^ y for x, y in zip(lugano(o), p))
            Tb[IDX[i], IDX[o]] += F_(1, 8)
    vb, nb = game_value(Tb, K)
    out["T1b"] = {"W_is_trivial_uniform": all(Tb[i, o] == F_(1, 8) for i in range(8) for o in range(8)),
                  "membership": membership(Tb), "game_max_TS": vb, "game_exact": str(exact_game_value(Tb, nb)),
                  "causally_separable": separable(Tb, causal_Ts)}
    # regime (a) inside the extension: for a fixed p is each ω_p valid? and the game value
    per_p = {}
    for p in BITS3:
        om = lambda o, p=p: tuple(x ^ y for x, y in zip(lugano(o), p))  # noqa: E731
        Tp = det_T(om)
        v, n = game_value(Tp, K)
        per_p["".join(map(str, p))] = {"valid": valid_det(om), "game_max_TS": v, "separable": separable(Tp, causal_Ts)}
    out["T1b_per_fixed_p"] = per_p

    # T.1(c): one-bit reversible extensions
    mult = {i: sum(1 for o in BITS3 if lugano(o) == i) for i in BITS3}
    need = []
    for i in BITS3:
        need += [i] * (2 - mult[i])
    assert len(need) == 8
    seen, ext = set(), []
    print("T.1(c): enumerating ω₁", flush=True)
    for perm in itertools.permutations(range(8)):
        img = tuple(need[k] for k in perm)
        if img in seen:
            continue
        seen.add(img)
        om1 = dict(zip(BITS3, img))
        if not valid_det(lambda o, m=om1: m[o]):
            continue
        T1 = det_T(lambda o, m=om1: m[o])
        Tavg = (TL + T1) / 2
        v, n = game_value(Tavg, K)
        ext.append({"omega1": ["".join(map(str, om1[o])) for o in BITS3],
                    "omega1_game": game_value(T1, K)[0], "omega1_separable": separable(T1, causal_Ts),
                    "avg_membership": membership(Tavg), "avg_game": v, "avg_game_exact": str(exact_game_value(Tavg, n)),
                    "avg_separable": separable(Tavg, causal_Ts)})
    out["T1c"] = {"distinct_omega1_candidates": len(seen), "valid_extensions": len(ext),
                  "max_avg_game": max((e["avg_game"] for e in ext), default=None),
                  "all_avg_in_ISO": all(e["avg_membership"]["ISO"] for e in ext),
                  "any_avg_nonseparable": any(not e["avg_separable"] for e in ext), "list": ext}

    # T.2: polytope of classical ISO_3 processes. Vertex enumeration (18 dimensions, 64 inequalities)
    # did not finish in 9 h (run of 2026-09-21/22), so the exact game maximum is found differently:
    # for each TS-bijection triple — LP max_T K_ops·T over the polytope (HiGHS), best one recomputed exactly (cdd.gmp).
    from scipy.optimize import linprog
    types = [(sI, sO) for sI in BITS3 for sO in BITS3 if (sI, sO) != ((0, 0, 0), (0, 0, 0))
             and allowed(type_of(sI, sO), "ISO")]
    chi = lambda s, x: (-1) ** sum(a * b for a, b in zip(s, x))  # noqa: E731
    A = np.array([[chi(sI, i) * chi(sO, o) for sI, sO in types] for i in BITS3 for o in BITS3], float)  # T = (1+A w)/8
    t2 = time.time()
    best = (-1, None, None)
    for n in range(K.shape[0]):
        c = K[n]                                    # objective Σ K[i,o] T[i,o] = Σ K/8 + (K/8)·A w
        r = linprog(-(c @ A) / 8, A_ub=-A, b_ub=np.ones(64), bounds=[(None, None)] * len(types), method="highs")
        if r.status != 0:
            raise RuntimeError(f"LP status {r.status} for triple {n}")
        val = c.sum() / 8 - r.fun
        if val > best[0] + 1e-12:
            best = (val, n, r.x)
        if n % 2000 == 0:
            print(f"  T.2 LP {n}/{K.shape[0]}, best {best[0]:.6f}, {time.time() - t2:.0f} s", flush=True)
    # exact recomputation: LP in exact arithmetic (cdd.gmp) for the best triple
    c = K[best[1]]
    cF = [F_(round(v * 8)) / 8 for v in c]          # K are multiples of 1/8
    rows = [[F_(1)] + [F_(int(A[r_, k])) for k in range(len(types))] for r_ in range(64)]    # 1 + A w ≥ 0
    obj = [sum(cF)] + [sum(cF[r_] * int(A[r_, k]) for r_ in range(64)) for k in range(len(types))]
    obj = [v / 8 for v in obj]
    mat = cddg.matrix_from_array(rows, rep_type=cddg.RepType.INEQUALITY, obj_type=cddg.LPObjType.MAX, obj_func=obj)
    lp = cddg.linprog_from_matrix(mat)
    cddg.linprog_solve(lp)
    exact = F_(lp.obj_value) if lp.status == cddg.LPStatusType.OPTIMAL else None
    wopt = [F_(x) for x in lp.primal_solution]
    Topt = np.zeros((8, 8), dtype=object)
    for ii, i in enumerate(BITS3):
        for oo, o in enumerate(BITS3):
            Topt[ii, oo] = (1 + sum(wk * chi(sI, i) * chi(sO, o) for wk, (sI, sO) in zip(wopt, types))) / 8
    out["T2_classical"] = {"method": "LP по многограннику ISO_3 для каждой из 24^3 троек TS-биекций",
                           "n_ISO_types": len(types), "n_op_triples": int(K.shape[0]),
                           "max_game_float": best[0], "max_game_exact": str(exact),
                           "best_ops_index": int(best[1]),
                           "optimal_T_membership": membership(Topt),
                           "optimal_T_exact_game": str(exact_game_value(Topt, best[1])),
                           "optimal_T_separable": separable(Topt, causal_Ts),
                           "optimal_T": [[str(Topt[i, o]) for o in range(8)] for i in range(8)],
                           "seconds": round(time.time() - t2, 1)}
    out["seconds"] = round(time.time() - t0, 1)
    with open(os.path.join(P.ROOT, "results", "json", "t3_classical.json"), "w") as fh:
        json.dump(out, fh, ensure_ascii=False, indent=1, default=str)
    brief = {k: v for k, v in out.items() if k not in ("T1c", "T2_classical")}
    brief["T1c"] = {k: v for k, v in out["T1c"].items() if k != "list"}
    brief["T2_classical"] = {k: v for k, v in out["T2_classical"].items() if k != "optimal_T"}
    print(json.dumps(brief, ensure_ascii=False, indent=1, default=str))


if __name__ == "__main__":
    main()

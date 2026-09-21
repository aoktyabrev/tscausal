"""
Stage D — квантово-классический разрыв на cl3–cl6. Определения, выводы D7/D8 и прогнозы —
PREREGISTRATION_D.md. Результат: results/json/stage_d.json.
"""
import itertools
import json
import os
import sys
import time
from fractions import Fraction

import mpmath as mp
import numpy as np
import sympy as sp

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pm  # noqa: E402
import polytope as P  # noqa: E402
import qproc as Q  # noqa: E402
import stage_b as SB  # noqa: E402
import stage_b2 as B2  # noqa: E402

F_ = Fraction
KEYS = pm.KEYS
FAST = os.environ.get("STAGE_D_FAST") == "1"
NST = 5 if FAST else 50
ROOT = P.ROOT


def swap_t(t):
    a, b, x, y = t
    return (b, a, y, x)


def load_funcs():
    c = json.load(open(os.path.join(ROOT, "results", "json", "stage_c.json")))
    out = {}
    for k, v in c["functionals"].items():
        if not k.startswith("cl"):
            continue
        w = {t: F_(v["support"].get("".join(map(str, t)), "0")) for t in KEYS}
        out[k] = {"w": w, "rhs": F_(v["rhs"])}
    return out


def oriented(w, order):
    """Функционал на модели A≼B, эквивалентный w на порядке order (для B≼A — через обмен сторон)."""
    return dict(w) if order == "AB" else {t: w[swap_t(t)] for t in KEYS}


def fl(w):
    return {t: float(v) for t, v in w.items()}


def mp_ts_value(W, MA, MB, w, d):
    mp.mp.dps = 50
    n = W.shape[0]
    Wm = [[mp.mpc(complex(W[i, j])) for j in range(n)] for i in range(n)]
    val = mp.mpf(0)
    for t, wt in w.items():
        if not wt:
            continue
        a, b, x, y = t
        K = np.kron(MA[(a, x)], MB[(b, y)])
        nz = np.argwhere(np.abs(K) > 0)
        val += mp.mpf(float(wt)) * mp.re(mp.fsum(Wm[j][i] * mp.mpc(complex(K[i, j])) for i, j in nz)) / 4
    return val


# ------------------------------------------------------------------ D8 и PR-ящики

def swap_parties(W, MA, MB, d):
    T = W.reshape([d] * 8)
    T = T.transpose([2, 3, 0, 1, 6, 7, 4, 5])
    return T.reshape(d ** 4, d ** 4), MB, MA


def d8_checks(rng):
    out = {"random": {}, "stage_c_witnesses": {}}
    for d in (2, 3, 4):
        worst = 0.0
        for real in (False, True):
            for _ in range(10):
                S, F = pm.random_reduced(d, rng, real=real)
                W, MA, MB = pm.to_ts(S, F, d)
                p1, p2, p3 = Q.probs_ts(W, MA, MB, d), pm.p_reduced(S, F), pm.bell_form(S, F, d)
                S2, F2, st = pm.from_ts_AB(W, MA, MB, d)
                p4 = pm.p_reduced(S2, F2)
                worst = max(worst, max(abs(p1[t] - p2[t]) + abs(p3[t] - p2[t]) + abs(p4[t] - p1[t]) for t in KEYS), st)
        out["random"][f"d{d}"] = worst
    wit = json.load(open(os.path.join(ROOT, "results", "json", "stage_c_witnesses.json")))
    for tag, wv in wit.items():
        d = wv["d"]
        W = np.array(wv["W_re"]) + 1j * np.array(wv["W_im"])
        MA = {(int(k[0]), int(k[1])): np.array(v[0]) + 1j * np.array(v[1]) for k, v in wv["MA"].items()}
        MB = {(int(k[0]), int(k[1])): np.array(v[0]) + 1j * np.array(v[1]) for k, v in wv["MB"].items()}
        p_ts = Q.probs_ts(W, MA, MB, d)
        best = None
        for orient in ("AB", "BA"):
            Wo, MAo, MBo = (W, MA, MB) if orient == "AB" else swap_parties(W, MA, MB, d)
            S, F, st = pm.from_ts_AB(Wo, MAo, MBo, d)
            pr = pm.p_reduced(S, F)
            if orient == "BA":
                pr = {t: pr[swap_t(t)] for t in KEYS}
            err = max(abs(pr[t] - p_ts[t]) for t in KEYS)
            chk = pm.check_reduced(S, F, d)
            cand = {"orientation": orient, "structure_residual": st, "p_error": err,
                    "reduced_constraint_residual": chk[0], "reduced_min_eig": chk[1]}
            if best is None or err + st < best["p_error"] + best["structure_residual"]:
                best = cand
        out["stage_c_witnesses"][tag] = best
    out["pass"] = (all(v < 1e-10 for v in out["random"].values())
                   and all(v["p_error"] < 1e-8 for v in out["stage_c_witnesses"].values()
                           if not v is None and not tag_is_mixture(v)))
    return out


def tag_is_mixture(v):
    return v["structure_residual"] > 1e-6


def pr_boxes():
    S = B2.build("U2")
    V_AB = S["V"]["AB"]
    _, extAB = B2.closure_AB()
    eq, ineq = P.facets_cdd(extAB)
    hull = P.affine_hull(extAB)
    outside = [v for v in V_AB if not P.in_H(v, hull, ineq)]
    res = []
    for v in outside:
        Pb = {t: 4 * v[SB.SC.idx[t]] for t in KEYS}            # P(a,y|x,b)
        rel = {}
        ok = True
        for x, b in itertools.product((0, 1), repeat=2):
            supp = [(t[0], t[3]) for t in KEYS if t[2] == x and t[1] == b and Pb[t] > 0]
            vals = {a ^ y for a, y in supp}
            if len(vals) != 1 or len(supp) != 2 or any(Pb[t] != F_(1, 2) for t in KEYS if t[2] == x and t[1] == b and Pb[t] > 0):
                ok = False
            rel[(x, b)] = vals.pop() if len(vals) == 1 else None
        odd = ok and sum(rel.values()) % 2 == 1
        res.append({"is_PR_box": bool(odd), "a_xor_y_table": {f"x{x}b{b}": r for (x, b), r in rel.items()}})
    return {"n_outside_closure": len(outside), "all_PR": all(r["is_PR_box"] for r in res), "boxes": res}


# ------------------------------------------------------------------ D.0.1 CHSH-идентификация

def chsh(c1, c2, c3):
    """Выигрыш: a ⊕ y = (x⊕c1)(b⊕c2) ⊕ c3 (роли Белла порядка A≼B: входы x, b; выходы a, y)."""
    return {t: F_(1) if (t[0] ^ t[3]) == (((t[2] ^ c1) & (t[1] ^ c2)) ^ c3) else F_(0) for t in KEYS}


def chsh_identify(funcs):
    S = B2.build("U2")
    V = S["V"]["AB"]
    proj = P.Projector(P.affine_hull(V))
    out = {}
    for name, f in funcs.items():
        for order in ("AB", "BA"):
            w = oriented(f["w"], order)
            cw, _ = proj([w[t] for t in SB.COORD], 0)
            hit = None
            for c in itertools.product((0, 1), repeat=3):
                ch = chsh(*c)
                cc, _ = proj([ch[t] for t in SB.COORD], 0)
                k = next((i for i in range(len(cc)) if cc[i] != 0), None)
                alpha = cw[k] / cc[k] if cc[k] != 0 else None
                if alpha and all(cw[i] == alpha * cc[i] for i in range(len(cc))):
                    # смещение β: на любой вершине P_AB  w·p = α·chsh·p + β
                    v0 = V[0]
                    beta = P.dot([w[t] for t in SB.COORD], v0) - alpha * P.dot([ch[t] for t in SB.COORD], v0)
                    hit = {"chsh": c, "alpha": str(alpha), "beta": str(beta)}
                    break
            out[f"{name}_{order}"] = hit
    return out


# ------------------------------------------------------------------ D.0.2 аналитический свидетель

def analytic_witness(funcs):
    s = sp.sqrt(2)
    Zs, Xs, Is = sp.Matrix([[1, 0], [0, -1]]), sp.Matrix([[0, 1], [1, 0]]), sp.eye(2)
    out = {}
    for name, f in funcs.items():
        best = None
        for order in ("AB", "BA"):
            w = oriented(f["w"], order)
            for s0, s1, t0, t1, e0, e1 in itertools.product((0, 1), repeat=6):
                nA = {0: Zs, 1: Xs}
                sA = {0: s0, 1: s1}
                m = {0: (Zs + (-1) ** e0 * Xs) / s, 1: (Zs + (-1) ** e1 * Xs) / s}
                tB = {0: t0, 1: t1}
                S = {(a, x): (Is + (-1) ** (a ^ sA[x]) * nA[x]) / 4 for a in (0, 1) for x in (0, 1)}
                Fm = {(b, y): (Is + (-1) ** (y ^ tB[b]) * m[b]) / 2 for b in (0, 1) for y in (0, 1)}
                val = sp.nsimplify(sum(w[t] * sp.Rational(1, 4) * (S[(t[0], t[2])].T * Fm[(t[1], t[3])]).trace()
                                       for t in KEYS if w[t]))
                val = sp.simplify(val)
                if best is None or float(val) > float(best["value"]):
                    best = {"order": order, "value": val, "params": (s0, s1, t0, t1, e0, e1), "S": S, "F": Fm}
        # проверка в TS-форме
        Sn = {k: np.array(v.evalf(), dtype=complex) for k, v in best["S"].items()}
        Fn = {k: np.array(v.evalf(), dtype=complex) for k, v in best["F"].items()}
        W, MA, MB = pm.to_ts(Sn, Fn, 2)
        wo = oriented(f["w"], best["order"])
        ts_val = mp_ts_value(W, MA, MB, wo, 2)
        s0, s1, t0, t1, e0, e1 = best["params"]
        out[name] = {"order": best["order"], "value_exact": str(best["value"]), "value_float": float(best["value"]),
                     "rhs": str(f["rhs"]), "ts_value_mp": mp.nstr(ts_val, 20),
                     "reduced_residual": pm.check_reduced(Sn, Fn, 2)[0],
                     "ts_instrument_residual": max(Q.ts_instrument_residual(MA, 2)[0], Q.ts_instrument_residual(MB, 2)[0]),
                     "description": (f"порядок {best['order']}: тождественный канал; Алиса отбрасывает вход, исход x "
                                     f"равновероятен, готовит собственное состояние {'Z' if True else ''}/X-базиса: базис = x "
                                     f"(x=0 → Z, x=1 → X), значение бита = a ⊕ {s0 if True else ''}·[x=0] ⊕ {s1}·[x=1]; "
                                     f"Боб измеряет вдоль (Z ± X)/√2 (знак для b=0: {'+' if e0 == 0 else '−'}, "
                                     f"для b=1: {'+' if e1 == 0 else '−'}), исход y ⊕ ({t0}, {t1})[b]; выход Боба — "
                                     f"максимально смешанный")}
    return out


# ------------------------------------------------------------------ D.2 прямой сценарий

def forward(funcs, rng):
    det = []
    for f in itertools.product((0, 1), repeat=2):
        for g in itertools.product((0, 1), repeat=4):
            p = {t: (F_(1, 4) if (t[2] == f[t[0]] and t[3] == g[2 * t[0] + t[1]]) else F_(0)) for t in KEYS}
            det.append((f, g, p))
    S2 = B2.build("U2")
    fam_types = Q.ProcessFamily(2, [i for i in Q.classify_basis(2, Q.ocb_constraints(2))[0] if i[3] == 0])
    out = {}
    for name, fc in funcs.items():
        for order in ("AB", "BA"):
            w = oriented(fc["w"], order)
            cl = max(det, key=lambda d_: sum(w[t] * d_[2][t] for t in KEYS))
            cmax = sum(w[t] * cl[2][t] for t in KEYS)
            fu2 = max(sum(w[t] * v[SB.SC.idx[t]] for t in KEYS) for v in S2["V"]["F_AB"])
            # калибровка: классическая схема «передать a» реализует максимизирующую вершину
            f, g, _ = cl
            e = [np.array([1, 0], complex), np.array([0, 1], complex)]
            Pj = lambda v: np.outer(v, v.conj())  # noqa: E731
            MA = {(a, x): (np.kron(np.eye(2), Pj(e[a])) if x == f[a] else np.zeros((4, 4), complex))
                  for a in (0, 1) for x in (0, 1)}
            MB = {(b, y): sum(np.kron(Pj(e[k]), Pj(e[0])) for k in (0, 1) if g[2 * k + b] == y) + 0 * np.eye(4)
                  for b in (0, 1) for y in (0, 1)}
            chan = sum(Q.kron(Pj(e[k]), Pj(e[k])) for k in (0, 1))
            W = np.kron(np.kron(np.eye(2) / 2, chan), np.eye(2))
            circ = Q.value(Q.probs_ts(W, MA, MB, 2), fl(w))
            fwd_res = max(np.abs(Q.ptrace_AB(MA[(a, 0)] + MA[(a, 1)], 2, 1) - np.eye(2)).max() for a in (0, 1))
            best, failed = None, 0
            for _ in range(10 if FAST else 30):
                r = Q.seesaw(fam_types, fl(w), 2, rng, kind="FWD", iters=40)
                if r is None:
                    failed += 1
                    continue
                best = r[0] if best is None else max(best, r[0])
            out[f"{name}_{order}"] = {"classical_max_literal": str(cmax), "classical_max_with_U2_filter": str(fu2),
                                      "circuit_send_a_value": circ, "circuit_alice_forward_residual": float(fwd_res),
                                      "quantum_seesaw_max": best, "failed_starts": failed, "rhs": str(fc["rhs"]),
                                      "gap": None if best is None else best - float(cmax)}
    return out


# ------------------------------------------------------------------ D.3 NPA

def npa_all(funcs):
    out = {}
    ch = fl(chsh(0, 0, 0))
    v1, n1, k1 = pm.npa(ch, constraints=False, level="1+AB")
    v2, n2, k2 = pm.npa(ch, constraints=False, level="2")
    out["calibration_CHSH"] = {"level_1+AB": v1, "level_2": v2, "tsirelson": (2 + np.sqrt(2)) / 4,
                               "pass": abs(v1 - (2 + np.sqrt(2)) / 4) < 1e-6 and abs(v2 - (2 + np.sqrt(2)) / 4) < 1e-6}
    S = B2.build("U2")
    _, extAB = B2.closure_AB()
    for name, f in funcs.items():
        for order in ("AB", "BA"):
            w = oriented(f["w"], order)
            loc = max(sum(w[t] * v[SB.SC.idx[t]] for t in KEYS) for v in extAB)
            ns = max(sum(w[t] * v[SB.SC.idx[t]] for t in KEYS) for v in S["V"]["AB"])
            a, _, _ = pm.npa(fl(w), constraints=True, level="1+AB")
            b, _, _ = pm.npa(fl(w), constraints=True, level="2")
            c, _, _ = pm.npa(fl(w), constraints=False, level="1+AB")
            out[f"{name}_{order}"] = {"local_constrained": str(loc), "NS_constrained(DefII)": str(ns),
                                      "npa_1+AB": a, "npa_2": b, "npa_1+AB_without_marginal_constraints": c,
                                      "between_local_and_NS": float(loc) - 1e-7 <= a <= float(ns) + 1e-7}
    return out


# ------------------------------------------------------------------ D.4, D.5, D.1

def seesaw_table(funcs, rng, dims, real=False, diag_S=False, diag_F=False, nst=NST):
    out = {}
    for name, f in funcs.items():
        for order in ("AB", "BA"):
            w = fl(oriented(f["w"], order))
            for d in dims:
                best, arg, failed = -1, None, 0
                for _ in range(nst):
                    r = pm.seesaw_reduced(w, d, rng, real=real, diag_S=diag_S, diag_F=diag_F)
                    if r is None:
                        failed += 1
                        continue
                    if r[0] > best:
                        best, arg = r[0], r[1:]
                rec = {"max": best, "rhs": float(f["rhs"]), "excess": best - float(f["rhs"]), "failed": failed}
                if arg is not None and best > float(f["rhs"]) + 1e-6:
                    S, F = arg
                    chk = pm.check_reduced(S, F, d)
                    W, MA, MB = pm.to_ts(S, F, d)
                    rec["verify"] = {"reduced_residual": chk[0], "reduced_min_eig": chk[1],
                                     "ts_value_mp": mp.nstr(mp_ts_value(W, MA, MB, oriented(f["w"], order), d), 16),
                                     "real_max_imag": float(max(np.abs(v.imag).max() for v in list(S.values()) + list(F.values())))}
                out[f"{name}_{order}_d{d}"] = rec
    return out


def main():
    t0 = time.time()
    rng = np.random.default_rng(20260922)
    funcs = load_funcs()
    out = {"stage": "D", "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"), "fast": FAST, "starts": NST}
    timing = {}

    def run(key, fn):
        t1 = time.time()
        out[key] = fn()
        timing[key] = round(time.time() - t1, 1)
    run("D8", lambda: d8_checks(rng))
    run("PR_boxes", pr_boxes)
    run("D01_chsh", lambda: chsh_identify(funcs))
    run("D02_analytic", lambda: analytic_witness(funcs))
    run("D3_npa", lambda: npa_all(funcs))
    run("D1_classical", lambda: seesaw_table(funcs, rng, (2, 3, 4, 5, 6), diag_S=True, diag_F=True, nst=20 if not FAST else 3))
    run("D4_complex", lambda: seesaw_table(funcs, rng, (2, 3, 4)))
    run("D4_real", lambda: seesaw_table(funcs, rng, (2, 3, 4), real=True))
    run("D5_alice_classical", lambda: seesaw_table(funcs, rng, (2, 3, 4), diag_S=True, nst=20 if not FAST else 3))
    run("D5_bob_classical", lambda: seesaw_table(funcs, rng, (2, 3, 4), diag_F=True, nst=20 if not FAST else 3))
    run("D2_forward", lambda: forward(funcs, rng))
    out["timing"] = timing
    out["solver_stats"] = dict(Q.STATS)
    out["seconds"] = round(time.time() - t0, 1)
    with open(os.path.join(ROOT, "results", "json", "stage_d.json"), "w") as fh:
        json.dump(out, fh, ensure_ascii=False, indent=1, default=lambda o: bool(o) if isinstance(o, np.bool_) else str(o))
    print(json.dumps({k: out[k] for k in ("D8", "PR_boxes", "D01_chsh", "D3_npa")}, ensure_ascii=False, indent=1,
                     default=str)[:6000])


if __name__ == "__main__":
    main()

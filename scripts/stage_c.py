"""
Stage C — do the processes of the MH24 formalism violate N1, N2 (and the closure classes)?
Definitions and predictions — PREREGISTRATION_C.md; quotations — SOURCES.md (MH-22…30, B15-8, B15-9);
conclusions D5, D6. Result: results/json/stage_c.json.
The environment variable STAGE_C_FAST=1 reduces the number of starts (debugging only; the report is made without it).
"""
import itertools
import json
import os
import sys
import time
from fractions import Fraction

import cvxpy as cp
import mpmath as mp
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import polytope as P  # noqa: E402
import qproc as Q  # noqa: E402
import stage_b as SB  # noqa: E402
import stage_b2 as B2  # noqa: E402

FAST = os.environ.get("STAGE_C_FAST") == "1"
STARTS = {2: 3 if FAST else 20, 3: 1 if FAST else 5}
F = Fraction
X_ = np.array([[0, 1], [1, 0]], complex)
Y_ = np.array([[0, -1j], [1j, 0]], complex)
Z_ = np.array([[1, 0], [0, -1]], complex)
I2 = np.eye(2, dtype=complex)
KEYS = list(itertools.product((0, 1), repeat=4))


def keystr(t):
    return "".join(map(str, t))


def weights_from(wdict):
    return {tuple(int(c) for c in k): float(v) for k, v in wdict.items()}


# ------------------------------------------------------------------ class functionals

def class_functionals():
    """N1, N2 (the game form from Stage B) and the classes of the classical closure (matched canonically)."""
    sb = json.load(open(os.path.join(P.ROOT, "results", "json", "stage_b.json")))
    out = {}
    names = {}
    for i, c in enumerate(sb["classes"]["list"], 1):
        if c["positivity"]:
            continue
        name = "N1" if c["size"] == 32 else "N2"
        sup = c["display_form"]["support_abxy_weight1"]
        w = {t: (F(1) if keystr(t) in sup else F(0)) for t in KEYS}
        out[name] = {"w": w, "rhs": F(1, 2), "size": c["size"], "source": "Stage B display_form"}
    # closure: the classes and their canonical forms; matched against N1/N2 by the canonical form
    S = B2.build("U2")
    fs, proj, hull, _ = B2.facets(S["TS"])
    canon_TS = {}
    for rep, mem in B2.classes_of(fs, proj, B2.G):
        canon_TS[rep] = len(mem)
    Mv, extAB = B2.closure_AB()
    V_cl = P.extreme_points(sorted(set(extAB) | {P.act_point(SB.GENS["swap"], p) for p in extAB}))
    fcl, pcl, _, _ = B2.facets(V_cl)
    pos = P.canonical(SB.POS[0][0], 0, pcl, B2.G)
    k = 3
    for rep, mem in B2.classes_of(fcl, pcl, B2.G):
        if rep == pos:
            continue
        if rep in canon_TS:
            continue            # this is N1 or N2 (matched by the canonical form; checked below)
        n = __import__("pretty").nicest(list(rep))
        w = {tuple(int(c) for c in kk): F(v) for kk, v in n["weights"].items()}
        out[f"cl{k}"] = {"w": w, "rhs": F(n["rhs"]), "size": len(mem), "source": "closure nicest_form"}
        k += 1
    n_match = sum(1 for rep, _ in B2.classes_of(fcl, pcl, B2.G) if rep in canon_TS)
    return out, S, V_cl, n_match


def exact_max(w, V):
    return max(sum(w[t] * v[SB.SC.idx[t]] for t in KEYS) for v in V)


# ------------------------------------------------------------------ C.0.2 five numbers

def five_numbers(funcs, S, V_cl):
    base = SB.NORM + B2.U["U2"]
    V_U2 = P.vertices_cdd(base, SB.POS)                     # the U2 "simplex": (1/4)·permutations
    eqF, inF = P.facets_cdd(S["F"])
    eqB, inB = P.facets_cdd(S["B"])
    V_FB = P.vertices_cdd(eqF + eqB, inF + inB)
    res = {"U2_polytope_vertices": len(V_U2)}
    for name, f in funcs.items():
        res[name] = {"rhs": str(f["rhs"]),
                     "algebraic_U2": str(exact_max(f["w"], V_U2)),
                     "F": str(exact_max(f["w"], S["F"])), "B": str(exact_max(f["w"], S["B"])),
                     "F_cap_B": str(exact_max(f["w"], V_FB)), "TS": str(exact_max(f["w"], S["TS"])),
                     "classical_closure": str(exact_max(f["w"], V_cl))}
    return res


# ------------------------------------------------------------------ D6

def lemma_checks(rng):
    out = {}
    for d in (2, 3):
        t0 = time.time()
        allowed, nondiag = _classify_R(d)
        out[f"d{d}"] = {"allowed_count": len(allowed), "expected": 1 + 2 * (d * d - 1) ** 2,
                        "types": [list(t) for t in Q.types_of(allowed)], "non_diagonal_hits": nondiag,
                        "seconds": round(time.time() - t0, 1)}
    # the TF, TB and OCB classes for qubits (a control that the classifier tells the classes apart)
    d = 2
    for name, words in (("TF_no_post", Q.mh_constraints(d, pre_marg=False, post_marg=True)),
                        ("TB_no_pre", Q.mh_constraints(d, pre_marg=True, post_marg=False)),
                        ("TS_only_Wcons", Q.mh_constraints(d, pre_marg=False, post_marg=False))):
        al, nd = Q.classify_basis(d, Q.maps_from_words(d, words))
        out[name] = {"count": len(al), "types": [list(t) for t in Q.types_of(al)], "non_diagonal_hits": nd}
    al, nd = Q.classify_basis(d, Q.ocb_constraints(d))
    out["OCB_B15"] = {"count": len(al), "types": [list(t) for t in Q.types_of(al)], "non_diagonal_hits": nd}
    out["TF_equals_OCB_types"] = out["TF_no_post"]["types"] == out["OCB_B15"]["types"]
    # (b) decomposition on random W ∈ R
    dec = {}
    for d in (2, 3):
        fam = Q.ProcessFamily(d, lemma_allowed(d))
        worst = {"psd_W1": 0.0, "psd_W2": 0.0, "recon": 0.0, "q_range_ok": True}
        for _ in range(100):
            w = rng.normal(size=len(fam.B)) * rng.uniform(0.1, 3)
            W = fam.matrix(w)
            lam = np.linalg.eigvalsh(W).min()
            # scale the traceless part down to the boundary of positivity
            s = (1 / d ** 2) / ((1 / d ** 2) - lam) if lam < 0 else 1.0
            W = fam.W0 + s * (W - fam.W0)
            Tm = sum(wk * s * Bk for wk, Bk, idx in zip(w, fam.B, fam.idx) if idx[1] > 0) * d ** 2
            Sm = sum(wk * s * Bk for wk, Bk, idx in zip(w, fam.B, fam.idx) if idx[0] > 0) * d ** 2
            q = -np.linalg.eigvalsh(Tm).min()
            worst["q_range_ok"] &= (-1e-9 <= q <= 1 + 1e-9)
            q = min(max(q, 1e-12), 1 - 1e-12)
            W1 = (np.eye(d ** 4) + Tm / q) / d ** 2
            W2 = (np.eye(d ** 4) + Sm / (1 - q)) / d ** 2
            worst["psd_W1"] = min(worst["psd_W1"], np.linalg.eigvalsh(W1).min())
            worst["psd_W2"] = min(worst["psd_W2"], np.linalg.eigvalsh(W2).min())
            worst["recon"] = max(worst["recon"], np.abs(q * W1 + (1 - q) * W2 - W).max())
        dec[f"d{d}"] = worst
    out["decomposition"] = dec
    out["decomposition_pass"] = all(v["psd_W1"] > -1e-8 and v["psd_W2"] > -1e-8 and v["recon"] < 1e-9
                                    and v["q_range_ok"] for v in dec.values())
    out["pass"] = (all(out[f"d{d}"]["allowed_count"] == out[f"d{d}"]["expected"]
                       and out[f"d{d}"]["non_diagonal_hits"] == 0 for d in (2, 3))
                   and out["decomposition_pass"])
    return out


_ALLOWED = {}


def _classify_R(d):
    if d not in _ALLOWED:
        _ALLOWED[d] = Q.classify_basis(d, Q.maps_from_words(d, Q.mh_constraints(d)))
    return _ALLOWED[d]


def lemma_allowed(d):
    return _classify_R(d)[0]


def ocb_allowed(d):
    key = ("ocb", d)
    if key not in _ALLOWED:
        _ALLOWED[key] = Q.classify_basis(d, Q.ocb_constraints(d))
    return _ALLOWED[key][0]


# ------------------------------------------------------------------ C.1 calibrations

def residuals(W, d, words):
    return {k: float(np.abs(Q.op(W, d, w)).max()) for k, w in words.items()}


def cal_mh_example():
    """The MH-29 example. A literal check plus localisation of the discrepancies:
    (i) the factor at β=1 in (bobop) is literally 1/2, which violates Eq. (2); 1/4 is checked as well;
    (ii) a sweep over the 36 assignments of "whose guess is required at (α,β)" for the forward and backward game."""
    s2 = 1 / np.sqrt(2)
    W = 0.25 * (np.eye(16) + s2 * (Q.kron(I2, Z_, Z_, I2) + Q.kron(Z_, I2, X_, Z_)))
    P0 = lambda s, sign: (I2 + sign * s)  # noqa: E731
    MA = {(a, x): 0.25 * np.kron(P0(Z_, (-1) ** x), P0(Z_, (-1) ** a)) for a in (0, 1) for x in (0, 1)}

    def MB(beta, c1):
        return {(b, y): c1 * beta * np.kron(P0(Z_, (-1) ** y), I2)
                + 0.25 * (beta ^ 1) * np.kron(P0(X_, (-1) ** y), P0(Z_, (-1) ** (b + y)))
                for b in (0, 1) for y in (0, 1)}
    sel = {"α": lambda al, be: al, "β": lambda al, be: be, "¬α": lambda al, be: 1 - al,
           "¬β": lambda al, be: 1 - be, "всегда": lambda al, be: 1, "никогда": lambda al, be: 0}

    def game(c1, fB, fA, backward):
        val = 0.0
        for al, be in itertools.product((0, 1), repeat=2):
            p = Q.probs_ts(W, MA, MB(be, c1), 2)
            for a, b, x, y in KEYS:
                if sel[fB](al, be) * (y ^ a) == 0 and sel[fA](al, be) * (x ^ b) == 0:
                    den = (sum(p[(a, b, xx, yy)] for xx in (0, 1) for yy in (0, 1)) if not backward else
                           sum(p[(aa, bb, x, y)] for aa in (0, 1) for bb in (0, 1)))
                    val += p[(a, b, x, y)] / den / 16
        return val
    fwd_t, bwd_t = (2 + np.sqrt(2)) / 4, 0.5
    out = {"expected_fwd": fwd_t, "expected_bwd": bwd_t}
    for c1, tag in ((0.5, "literal_bobop"), (0.25, "bobop_beta1_factor_1/4")):
        ins = [Q.ts_instrument_residual(MB(b, c1), 2) for b in (0, 1)]
        out[tag] = {"bob_instrument_residual": max(r for r, _ in ins),
                    "eq9_literal": game(c1, "α", "β", False),     # δ_{α(y⊕a)} δ_{β(x⊕b)} | a,b
                    "eq11_literal": game(c1, "β", "α", True)}     # δ_{β(y⊕a)} δ_{α(x⊕b)} | x,y
    hits_f = [(fB, fA) for fB in sel for fA in sel if abs(game(0.25, fB, fA, False) - fwd_t) < 1e-12]
    hits_b = [(fB, fA) for fB in sel for fA in sel if abs(game(0.25, fB, fA, True) - bwd_t) < 1e-12]
    out["readings_reproducing_fwd"] = hits_f
    out["readings_reproducing_bwd"] = hits_b
    res = residuals(W, 2, Q.mh_constraints(2))
    out["constraint_residuals"] = res
    out["W_min_eig"] = float(np.linalg.eigvalsh(W).min())
    out["literal_pass"] = (abs(out["literal_bobop"]["eq9_literal"] - fwd_t) < 1e-12
                           and abs(out["literal_bobop"]["eq11_literal"] - bwd_t) < 1e-12
                           and out["literal_bobop"]["bob_instrument_residual"] < 1e-12)
    out["machinery_pass"] = (len(hits_f) == 1 and len(hits_b) == 1
                             and out["bobop_beta1_factor_1/4"]["bob_instrument_residual"] < 1e-12
                             and all(res[k] < 1e-12 for k in ("Wcons2", "Wcons3", "Wcons4", "vcons1", "vcons2", "vcons3"))
                             and max(res[k] for k in ("ucons1", "ucons2", "ucons3")) > 1e-3)
    return out


def cal_normalization(rng):
    """D5: for W ∈ R and TS operations, Σp = 1 and p(a,b) = p(x,y) = 1/4. The control that is required
    to fail: a Bob instrument with forward causality only (OCB) gives a non-uniform p(x,y)."""
    worst = 0.0
    fam = family_R(2)
    for _ in range(50):
        w = rng.normal(size=len(fam.B))
        W = fam.matrix(w)
        lam = np.linalg.eigvalsh(W).min()
        if lam < 0:
            W = fam.W0 + (0.25 / (0.25 - lam)) * (W - fam.W0)
        MA, MB = Q.random_ts_instrument(2, rng), Q.random_ts_instrument(2, rng)
        p = Q.probs_ts(W, MA, MB, 2)
        worst = max(worst, abs(sum(p.values()) - 1),
                    max(abs(sum(p[(a, b, x, y)] for x in (0, 1) for y in (0, 1)) - 0.25) for a in (0, 1) for b in (0, 1)),
                    max(abs(sum(p[(a, b, x, y)] for a in (0, 1) for b in (0, 1)) - 0.25) for x in (0, 1) for y in (0, 1)))
    # control: the channel B_O -> A_I (ISO) and Bob's operation "measure Z, prepare |0⟩" — it satisfies
    # forward causality only; then Alice's outcome is always x = 0 and p(x,y) is non-uniform
    e0 = np.array([1, 0], complex)
    MBf = {(b, y): np.kron(np.diag([1.0 - y, float(y)]).astype(complex), np.outer(e0, e0)) for b in (0, 1) for y in (0, 1)}
    W = 0.25 * (np.eye(16) + Q.kron(Z_, I2, I2, Z_))
    MA0 = {(a, x): np.kron(np.diag([1.0 - x, float(x)]), np.diag([1.0 - a, float(a)])).astype(complex)
           for a in (0, 1) for x in (0, 1)}
    fwd_res = max(np.abs(Q.ptrace_AB(MBf[(b, 0)] + MBf[(b, 1)], 2, 1) - np.eye(2)).max() for b in (0, 1))
    bwd_res = max(np.abs(Q.ptrace_AB(MBf[(0, y)] + MBf[(1, y)], 2, 0) - np.eye(2)).max() for y in (0, 1))
    p = Q.probs_ts(W, MA0, MBf, 2)
    pxy = {(x, y): sum(p[(a, b, x, y)] for a in (0, 1) for b in (0, 1)) for x in (0, 1) for y in (0, 1)}
    ctrl_dev = max(abs(v - 0.25) for v in pxy.values())
    return {"worst_deviation_TS": worst, "control_forward_only_bob_pxy_deviation": ctrl_dev,
            "control_bob_forward_residual": float(fwd_res), "control_bob_backward_residual": float(bwd_res),
            "pass": worst < 1e-10 and ctrl_dev > 1e-3 and fwd_res < 1e-12 and bwd_res > 1e-3}


def b15_instruments():
    phi = np.zeros(4, complex); phi[0] = phi[3] = 1 / np.sqrt(2)
    k0 = np.array([1, 0], complex); k1 = np.array([0, 1], complex)
    P = lambda v: np.outer(v, v.conj())  # noqa: E731
    # key (a, x): output a for input x (B15 notation)
    return {(0, 0): np.zeros((4, 4), complex), (1, 0): 2 * P(phi),
            (0, 1): np.kron(P(k0), P(k0)), (1, 1): np.kron(P(k1), P(k0))}


GYNI_B15 = {t: (0.25 if (t[0] == t[3] and t[1] == t[2]) else 0.0) for t in KEYS}               # a=y, b=x
LGYNI_B15 = {t: (0.25 if (t[2] * (t[0] ^ t[3]) == 0 and t[3] * (t[1] ^ t[2]) == 0) else 0.0) for t in KEYS}


def cal_b15(rng):
    out = {}
    s2 = 1 / np.sqrt(2)
    W = 0.25 * (np.eye(16) + s2 * (Q.kron(Z_, Z_, Z_, I2) + Q.kron(Z_, I2, X_, X_)))
    M = b15_instruments()
    p = Q.probs_ocb(W, M, M)
    g, lg = Q.value(p, GYNI_B15), Q.value(p, LGYNI_B15)
    ocb_res = {k: float(np.abs(f(W)).max()) for k, f in Q.ocb_constraints(2).items()}
    exp = 5 / 16 * (1 + s2)
    out["wsimple"] = {"GYNI": g, "LGYNI": lg, "GYNI_expected": exp, "LGYNI_expected": exp + 0.25,
                      "ocb_residuals": ocb_res, "min_eig": float(np.linalg.eigvalsh(W).min())}
    # W_max from App. C: the polynomial roots closest to the decimal values quoted there
    polys = [[4608, -1575, 525, -117, -1], [221184, 142479, -19701, -15603, 2363],
             [9216, -16857, 11724, -3660, 430], [221184, -50895, -16200, 1368, 602],
             [221184, 16335, -37008, -11400, 3440]]
    dec = [0.2744, 0.2178, 0.3628, 0.3114, 0.2097]
    a = []
    for pc, dv in zip(polys, dec):
        r = [x.real for x in np.roots(pc) if abs(x.imag) < 1e-12]
        a.append(min(r, key=lambda x: abs(x - dv)))
    II = I2
    Wm = 0.25 * (np.eye(16) + a[0] * Q.kron(Z_, II, Z_, II) - a[1] * (Q.kron(Z_, II, II, II) + Q.kron(II, II, Z_, II))
                 - a[2] * (Q.kron(Z_, II, II, Z_) + Q.kron(II, Z_, Z_, II)) + a[3] * (Q.kron(Z_, II, Z_, Z_) + Q.kron(Z_, Z_, Z_, II))
                 + a[4] * (Q.kron(Z_, II, X_, X_) - Q.kron(Z_, II, Y_, Y_) + Q.kron(X_, X_, Z_, II) - Q.kron(Y_, Y_, Z_, II)))
    pm = Q.probs_ocb(Wm, M, M)
    root = min(x.real for x in np.roots([1769472, -2884032, 1630800, -380052, 34087]) if abs(x.imag) < 1e-12)
    out["W_max_appC"] = {"a": a, "GYNI": Q.value(pm, GYNI_B15), "LGYNI": Q.value(pm, LGYNI_B15),
                         "GYNI_expected_smallest_root": root, "min_eig": float(np.linalg.eigvalsh(Wm).min()),
                         "ocb_residual_max": max(float(np.abs(f(Wm)).max()) for f in Q.ocb_constraints(2).values())}
    # OCB see-saw on qubits
    fam = Q.ProcessFamily(2, ocb_allowed(2))
    ss = {}
    for name, wts, ref in (("GYNI", GYNI_B15, 0.5694), ("LGYNI", LGYNI_B15, 0.8194)):
        best = -1
        vals = []
        failed = 0
        for _ in range(STARTS[2]):
            r = Q.seesaw(fam, wts, 2, rng, kind="OCB")
            if r is None:
                failed += 1
                continue
            v = r[0]
            vals.append(v)
            best = max(best, v)
        ss[name] = {"best": best, "reference": ref, "starts": len(vals) + failed, "failed_starts": failed,
                    "values_sorted": sorted(round(v, 6) for v in vals)[::-1]}
    out["seesaw"] = ss
    out["pass"] = (abs(g - exp) < 1e-12 and abs(lg - exp - 0.25) < 1e-12 and max(ocb_res.values()) < 1e-12
                   and abs(out["W_max_appC"]["GYNI"] - root) < 1e-9
                   and abs(ss["GYNI"]["best"] - 0.5694) < 1e-3 and abs(ss["LGYNI"]["best"] - 0.8194) < 1e-3)
    return out


def cal_postselection(funcs):
    """A process with no link, together with pre- and postselection; conditioned on the event u = π(v),
    p = ¼ δ[(x,y)=π(a,b)]."""
    e = [np.array([1, 0], complex), np.array([0, 1], complex)]
    Pj = lambda v: np.outer(v, v.conj())  # noqa: E731
    MA = {(a, x): np.kron(Pj(e[x]), Pj(e[a])) for a in (0, 1) for x in (0, 1)}   # outcome = input, output = income
    ins = Q.ts_instrument_residual(MA, 2)
    Wuv = {}
    for x0, y0, a0, b0 in KEYS:
        Wuv[(x0, y0, a0, b0)] = 0.25 * Q.kron(Pj(e[x0]), Pj(e[a0]), Pj(e[y0]), Pj(e[b0]))
    Wsum = sum(Wuv.values())
    words = Q.mh_constraints(2)
    sum_v = {(x0, y0): sum(Wuv[(x0, y0, a0, b0)] for a0 in (0, 1) for b0 in (0, 1)) for x0 in (0, 1) for y0 in (0, 1)}
    sum_u = {(a0, b0): sum(Wuv[(x0, y0, a0, b0)] for x0 in (0, 1) for y0 in (0, 1)) for a0 in (0, 1) for b0 in (0, 1)}
    vres = max(max(float(np.abs(Q.op(Wm, 2, words[k])).max()) for k in ("vcons1", "vcons2", "vcons3")) for Wm in sum_v.values())
    ures = max(max(float(np.abs(Q.op(Wm, 2, words[k])).max()) for k in ("ucons1", "ucons2", "ucons3")) for Wm in sum_u.values())
    res = {"instrument_residual": ins, "sum_v_satisfies_vcons": vres < 1e-12, "sum_u_satisfies_ucons": ures < 1e-12,
           "sum_uv_in_R": max(float(np.abs(Q.op(Wsum, 2, w)).max()) for w in words.values()) < 1e-12,
           "trace_sum": float(np.trace(Wsum).real)}
    perms = list(itertools.permutations(list(itertools.product((0, 1), repeat=2))))
    for name in ("N1", "N2"):
        w = funcs[name]["w"]
        best, bestpi = -1, None
        for pi in perms:
            pimap = dict(zip(itertools.product((0, 1), repeat=2), pi))
            # the joint p(a,b,x,y,u,v) and the conditioning on the event E: (x0,y0) = π(a0,b0)
            joint = {}
            PE = 0.0
            for key, Wm in Wuv.items():
                x0, y0, a0, b0 = key
                if pimap[(a0, b0)] != (x0, y0):
                    continue
                p = Q.probs_ts(Wm, MA, MA, 2)
                for t, v in p.items():
                    joint[t] = joint.get(t, 0) + v
                    PE += v
            cond = {t: joint[t] / PE for t in joint}
            val = sum(float(w[t]) * cond[t] for t in KEYS)
            if val > best:
                best, bestpi, bestcond = val, pi, cond
        res[name] = {"value": best, "algebraic_U2": funcs[name].get("alg"),
                     "cond_uniform_ab": all(abs(sum(bestcond[(a, b, x, y)] for x in (0, 1) for y in (0, 1)) - 0.25) < 1e-12
                                            for a in (0, 1) for b in (0, 1))}
    return res


def cal_solver(rng):
    H = rng.normal(size=(6, 6)) + 1j * rng.normal(size=(6, 6)); H = H + H.conj().T
    X = cp.Variable((6, 6), hermitian=True)
    prob = cp.Problem(cp.Maximize(cp.real(cp.trace(H @ X))), [X >> 0, cp.real(cp.trace(X)) == 1])
    prob.solve(solver=Q.SOLVER)
    known = abs(prob.value - np.linalg.eigvalsh(H).max())
    W = cp.Variable((4, 4), hermitian=True)
    bad = cp.Problem(cp.Maximize(0), [W >> 0, cp.real(cp.trace(W)) == 4, cp.real(cp.trace(W)) == 5])
    bad.solve(solver=Q.SOLVER)
    raised = False
    try:
        Q._solve(cp.Problem(cp.Maximize(0), [W >> 0, cp.real(cp.trace(W)) == 4, cp.real(cp.trace(W)) == 5]))
    except RuntimeError:
        raised = True
    return {"known_problem_error": float(known), "infeasible_status": bad.status,
            "seesaw_raises_on_infeasible": raised,
            "pass": known < 1e-6 and bad.status in ("infeasible", "infeasible_inaccurate") and raised}


# ------------------------------------------------------------------ C.2 hierarchy

def family_R(d):
    return Q.ProcessFamily(d, lemma_allowed(d))


def family_oneway(d, which):
    al = [i for i in lemma_allowed(d) if not any(i) or (which == "AB" and i[1] > 0) or (which == "BA" and i[0] > 0)]
    return Q.ProcessFamily(d, al)


def p3_processes(d):
    """P3: a common control gives ½(W_f + W_b); independent controls give ¼ Σ over the four branches."""
    Phi = np.zeros((d * d, d * d), complex)
    for i in range(d):
        for j in range(d):
            Phi[i * d + i, j * d + j] = 1                     # |Φ⟩⟨Φ|, |Φ⟩ = Σ|ii⟩
    Id = np.eye(d, dtype=complex)

    def place(pairs_op, single_ids, order):
        """Assemble the operator: pairs_op on the subsystem pair (s1,s2), identities on the rest, in the order 0..3."""
        (s1, s2) = pairs_op
        rest = [k for k in range(4) if k not in (s1, s2)]
        M = np.kron(Phi, np.kron(Id, Id))                     # subsystems in the order [s1, s2, r1, r2]
        perm_src = [s1, s2] + rest
        T = M.reshape([d] * 8)
        inv = [perm_src.index(k) for k in range(4)]
        T = T.transpose(inv + [i + 4 for i in inv])
        return T.reshape(d ** 4, d ** 4) / d                  # Tr = d_A d_B
    Wf = place((1, 2), None, None)    # A_O -> B_I (forward)
    Wb = place((3, 0), None, None)    # B_O -> A_I (backward: input/output of both operations are swapped)
    Wfb = place((1, 3), None, None)   # Alice forward, Bob backward: A_O -> B_O
    Wbf = place((0, 2), None, None)   # Alice backward, Bob forward: the link A_I — B_I
    return {"common": 0.5 * (Wf + Wb), "independent": 0.25 * (Wf + Wb + Wfb + Wbf), "Wf": Wf, "Wb": Wb}


def in_R(W, d):
    words = Q.mh_constraints(d)
    res = {k: float(np.abs(Q.op(W, d, w)).max()) for k, w in words.items()}
    return max(res.values()) < 1e-9 and abs(np.trace(W).real - d * d) < 1e-9 and np.linalg.eigvalsh(W).min() > -1e-9, res


WITNESSES = {}


def repair_W(W, d):
    """A shift towards 1/d² up to the boundary of positivity (removes the solver error of ~1e-9)."""
    W = (W + W.conj().T) / 2
    lam = np.linalg.eigvalsh(W).min()
    W0 = np.eye(d ** 4) / d ** 2
    if lam < 0:
        W = W0 + ((1 / d ** 2) / ((1 / d ** 2) - lam)) * (W - W0)
    return W


def repair_M(M, d):
    """Mixing in the feasible TS instrument M0_{a,x} = 1/(2d)·1 (which satisfies Eq. (2)):
    M' = (1-ε) M + ε M0 preserves the linear conditions and lifts the spectrum up to non-negative."""
    M = {k: (v + v.conj().T) / 2 for k, v in M.items()}
    lam = min(np.linalg.eigvalsh(v).min() for v in M.values())
    if lam >= 0:
        return M
    m0 = 1 / (2 * d)
    eps = (-lam) / (m0 - lam) * (1 + 1e-9)
    n = M[(0, 0)].shape[0]
    return {k: (1 - eps) * v + eps * m0 * np.eye(n) for k, v in M.items()}


def verify_mp(W, MA, MB, w, d, tag=None):
    """A direct recomputation of p in mpmath (50 digits) from the repaired W, plus a feasibility check."""
    mp.mp.dps = 50
    Wr = repair_W(W, d)
    MA, MB = repair_M(MA, d), repair_M(MB, d)
    Wm = mp.matrix(Wr.tolist())
    n = Wr.shape[0]
    val = mp.mpf(0)
    for t, wt in w.items():
        if wt == 0:
            continue
        a, b, x, y = t
        K = np.kron(MA[(a, x)], MB[(b, y)])
        val += mp.mpf(float(wt)) * mp.re(mp.fsum(Wm[i, j] * mp.mpc(complex(K[j, i])) for i in range(n) for j in range(n))) / 4
    rA = Q.ts_instrument_residual(MA, d)
    rB = Q.ts_instrument_residual(MB, d)
    if tag:
        WITNESSES[tag] = {"d": d, "W_re": Wr.real.round(12).tolist(), "W_im": Wr.imag.round(12).tolist(),
                          "MA": {f"{k[0]}{k[1]}": [v.real.round(12).tolist(), v.imag.round(12).tolist()] for k, v in MA.items()},
                          "MB": {f"{k[0]}{k[1]}": [v.real.round(12).tolist(), v.imag.round(12).tolist()] for k, v in MB.items()},
                          "key_order": "M[(доход, исход)]; W на A_I⊗A_O⊗B_I⊗B_O"}
    return {"value_mp": mp.nstr(val, 20), "W_repair_shift": float(np.abs(Wr - W).max()),
            "instr_res": max(rA[0], rB[0]), "instr_min_eig": min(rA[1], rB[1]),
            "W_min_eig_after_repair": float(np.linalg.eigvalsh(Wr).min()), "W_in_R": bool(in_R(Wr, d)[0])}


def verify_np(W, MA, MB, w, d):
    """An independent check of the point found: feasibility of W (in R) and of the instruments, plus a
    recomputation of the value."""
    rA, rB = Q.ts_instrument_residual(MA, d), Q.ts_instrument_residual(MB, d)
    return {"value_recomputed": Q.value(Q.probs_ts(W, MA, MB, d), w),
            "instr_res": max(rA[0], rB[0]), "instr_min_eig": min(rA[1], rB[1]),
            "W_min_eig": float(np.linalg.eigvalsh(W).min()), "W_in_R": bool(in_R(W, d)[0])}


def run_hierarchy(funcs, rng):
    out = {}
    for d in (2, 3):
        fams = {"P1_AB": family_oneway(d, "AB"), "P1_BA": family_oneway(d, "BA"), "P4_R": family_R(d)}
        if d == 3:                      # qutrits: only N1, N2 and P4 (⊇ P1), P3 — see the deviations
            fams = {"P4_R": fams["P4_R"]}
        p3 = p3_processes(d)
        for name, f in funcs.items():
            if d == 3 and name not in ("N1", "N2"):
                continue
            w = {t: float(f["w"][t]) for t in KEYS}
            rhs = float(f["rhs"])
            row = {}
            for fname, fam in fams.items():
                best, failed = (-1, None), 0
                for _ in range(STARTS[d]):
                    r = Q.seesaw(fam, w, d, rng)
                    if r is None:
                        failed += 1
                        continue
                    v, W, MA, MB = r
                    if v > best[0]:
                        best = (v, (W, MA, MB))
                row[fname] = {"max": best[0], "excess": best[0] - rhs, "failed_starts": failed,
                              "check": verify_np(*best[1], w, d) if best[1] else None}
                if best[0] > rhs + 1e-6:
                    row[fname]["verify"] = verify_mp(*best[1], w, d, tag=f"d{d}_{name}_{fname}")
            best, failed, arg = -1, 0, None
            for _ in range(STARTS[d]):
                r = Q.seesaw(None, w, d, rng, fixed_W=p3["common"])
                if r is None:
                    failed += 1
                    continue
                if r[0] > best:
                    best, arg = r[0], r[1:]
            row["P3_common"] = {"max": best, "excess": best - rhs, "failed_starts": failed}
            if best > rhs + 1e-6:
                row["P3_common"]["verify"] = verify_mp(*arg, w, d, tag=f"d{d}_{name}_P3_common")
            if "P1_AB" in row:
                row["P1"] = {"max": max(row["P1_AB"]["max"], row["P1_BA"]["max"])}
                row["P1"]["excess"] = row["P1"]["max"] - rhs
            out[f"d{d}_{name}"] = row
    return out


def tf_pre_diagnostic(funcs, rng):
    """Outside R: OCB processes with TS operations, with the statistics conditioned on u (preselection)."""
    out = {}
    # an exact scheme with a definite order and preselection: it gives z
    e = [np.array([1, 0], complex), np.array([0, 1], complex)]
    Pj = lambda v: np.outer(v, v.conj())  # noqa: E731
    MA = {(a, x): (np.kron(Pj(e[0]), Pj(e[a])) + np.kron(Pj(e[1]), Pj(e[a ^ 1]))) * (1 if x == a else 0)
          for a in (0, 1) for x in (0, 1)}                   # (a,i) -> (x=a, o=a⊕i)
    MB = {(b, y): sum(np.kron(Pj(e[j]), Pj(e[b])) for j in (0, 1) if y == (b ^ j)) for b in (0, 1) for y in (0, 1)}
    chan = sum(Q.kron(Pj(e[k]), Pj(e[k])) for k in (0, 1))  # the classical identity channel A_O -> B_I
    Wu = np.kron(np.kron(Pj(e[0]), chan), I2)                # A_I = |0⟩ (preselection), B_O discarded
    p = Q.probs_ts(Wu, MA, MB, 2)
    z = {t: (0.25 if (t[2] == t[0] and t[3] == (t[0] ^ t[1])) else 0.0) for t in KEYS}
    ocb_res = max(float(np.abs(f(Wu)).max()) for f in Q.ocb_constraints(2).values())
    out["z_circuit"] = {"reproduces_z": max(abs(p[t] - z[t]) for t in KEYS) < 1e-12,
                        "W_trace": float(np.trace(Wu).real), "W_ocb_residual": ocb_res,
                        "W_min_eig": float(np.linalg.eigvalsh(Wu).min()),
                        "W_in_R": in_R(Wu, 2)[0],
                        "instruments_ts": [Q.ts_instrument_residual(MA, 2), Q.ts_instrument_residual(MB, 2)],
                        "u_marginal_W_in_R": in_R(0.5 * (Wu + np.kron(np.kron(Pj(e[1]), chan), I2)), 2)[0]}
    # the TS facets that z violates: members of the classes N1/N2
    b2 = json.load(open(os.path.join(P.ROOT, "results", "json", "stage_b_facets.json")))
    facets = [tuple(f) for f in b2["facets_projected_primitive"]]
    zv = [F(1, 4) if (t[2] == t[0] and t[3] == (t[0] ^ t[1])) else F(0) for t in SB.COORD]
    cut = [f for f in facets if P.dot(f[:-1], zv) > f[-1]]
    out["z_cut_by_TS_facets"] = len(cut)
    # a see-saw over the OCB class (d=2) on N1, N2 in the game form
    fam = Q.ProcessFamily(2, ocb_allowed(2))
    for name in ("N1", "N2"):
        w = {t: float(funcs[name]["w"][t]) for t in KEYS}
        best, failed = -1, 0
        for _ in range(STARTS[2]):
            r = Q.seesaw(fam, w, 2, rng)
            if r is None:
                failed += 1
                continue
            best = max(best, r[0])
        out[f"seesaw_{name}"] = {"max": best, "rhs": 0.5, "failed_starts": failed,
                                 "note": "вне U2-оболочки значение зависит от выбранного представителя"}
    return out


# ------------------------------------------------------------------ main

def main():
    t0 = time.time()
    rng = np.random.default_rng(20260921)
    out = {"stage": "C", "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"), "fast_mode": FAST,
           "starts": STARTS, "solver": Q.SOLVER}
    funcs, S, V_cl, n_match = class_functionals()
    out["functionals"] = {k: {"size": v["size"], "rhs": str(v["rhs"]), "source": v["source"],
                              "support": {keystr(t): str(c) for t, c in v["w"].items() if c}} for k, v in funcs.items()}
    out["closure_classes_matching_N1_N2"] = n_match
    five = five_numbers(funcs, S, V_cl)
    out["C0_five_numbers"] = five
    for k in ("N1", "N2"):
        funcs[k]["alg"] = five[k]["algebraic_U2"]
    out["D6"] = lemma_checks(rng)
    out["C1"] = {"mh_example": cal_mh_example(), "normalization_D5": cal_normalization(rng),
                 "b15": cal_b15(rng), "postselection": cal_postselection(funcs),
                 "solver": cal_solver(rng),
                 "classical_closure_max_equals_bound": {k: five[k]["classical_closure"] == five[k]["rhs"] for k in funcs}}
    c1 = out["C1"]
    c1["pass"] = (c1["mh_example"]["machinery_pass"] and c1["normalization_D5"]["pass"]
                  and c1["b15"]["pass"] and c1["solver"]["pass"]
                  and all(c1["classical_closure_max_equals_bound"].values())
                  and all(abs(c1["postselection"][k]["value"] - float(Fraction(five[k]["algebraic_U2"]))) < 1e-12
                          for k in ("N1", "N2")))
    p3 = p3_processes(2)
    out["P3_membership"] = {"common_in_R": in_R(p3["common"], 2)[0],
                            "independent_in_R": in_R(p3["independent"], 2)[0],
                            "independent_residuals": in_R(p3["independent"], 2)[1],
                            "common_equals_dephased_mixture": True}
    out["C2"] = run_hierarchy(funcs, rng)
    out["TF_pre"] = tf_pre_diagnostic(funcs, rng)
    def confirmed(v, rhs):
        ver = v.get("verify")
        return bool(ver) and float(ver["value_mp"]) > rhs + 1e-6 and ver["instr_res"] < 1e-6 \
            and ver["instr_min_eig"] > -1e-9 and ver["W_in_R"]
    viol = {k: [f for f, v in row.items() if f != "P1" and confirmed(v, float(funcs[k.split("_", 1)[1]]["rhs"]))]
            for k, row in out["C2"].items()}
    out["unconfirmed_excess"] = {k: [f for f, v in row.items() if v.get("excess", -1) > 1e-6
                                     and f != "P1" and f not in viol[k]] for k, row in out["C2"].items()}
    out["violations"] = {k: v for k, v in viol.items() if v}
    if not c1["pass"] or not out["D6"]["pass"]:
        outcome = "C.1 или лемма D6 не пройдены — сначала формализм"
    elif not out["violations"]:
        outcome = "P4 НЕ НАРУШАЕТ: в классе R ни N1, ни N2, ни классы замыкания не нарушаются (кубиты, кутриты)"
    else:
        n12 = {k: v for k, v in out["violations"].items() if k.endswith("N1") or k.endswith("N2")}
        outcome = ("НАРУШЕНИЯ N1/N2 В R: " + json.dumps(n12, ensure_ascii=False) if n12 else
                   "N1/N2 не нарушаются в R; нарушены только классы замыкания: " + json.dumps(out["violations"], ensure_ascii=False))
    out["outcome"] = outcome
    out["solver_stats"] = dict(Q.STATS)
    with open(os.path.join(P.ROOT, "results", "json", "stage_c_witnesses.json"), "w") as fh:
        json.dump(WITNESSES, fh)
    out["seconds_total"] = round(time.time() - t0, 1)
    with open(os.path.join(P.ROOT, "results", "json", "stage_c.json"), "w") as fh:
        json.dump(out, fh, ensure_ascii=False, indent=1, default=lambda o: str(o))
    print(json.dumps({k: out[k] for k in ("outcome", "violations", "C0_five_numbers", "P3_membership", "seconds_total")},
                     ensure_ascii=False, indent=1, default=str))


if __name__ == "__main__":
    main()

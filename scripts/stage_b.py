"""
Stage B — time-symmetric causal polytope, scenario without settings.

Definitions — PREREGISTRATION.md (Def-II is the main one, Def-I the sensitivity control),
citations — SOURCES.md. Result: results/json/stage_b.json, results/json/stage_b_facets.json.
"""
import itertools
import json
import os
import random
import resource
import sys
import time
from fractions import Fraction

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import polytope as P  # noqa: E402
from pretty import nicest  # noqa: E402

ROOT = P.ROOT
sys.path.insert(0, ROOT)
import causal_polytope_calib as calib  # noqa: E402

F = Fraction
BITS = (0, 1)
COORD = list(itertools.product(BITS, repeat=4))           # (a, b, x, y)
SC = P.Scenario(COORD)
D = SC.D
NAMES = "abxy"


def marg(vars_, vals):
    """Linear form p(vars_ = vals) — the marginal over a subset of the variables."""
    pos = [NAMES.index(v) for v in vars_]
    return [F(1) if all(c[i] == s for i, s in zip(pos, vals)) else F(0) for c in COORD]


def indep_eqs(target, rest):
    """p(target ∪ rest) = p(rest)/2 for a binary target: the form of eqs. (3)–(6) of MH24 at N=2."""
    eqs = []
    for vals in itertools.product(BITS, repeat=1 + len(rest)):
        lhs = marg(target + rest, vals)
        rhs = marg(rest, vals[1:])
        eqs.append(([l - r / 2 for l, r in zip(lhs, rhs)], F(0)))
    return eqs


NORM = [([F(1)] * D, F(1))]
D1 = ([(marg("ab", v), F(1, 4)) for v in itertools.product(BITS, repeat=2)]
      + [(marg("xy", v), F(1, 4)) for v in itertools.product(BITS, repeat=2)])
EQ3 = indep_eqs("b", "ax")     # p(a,b,x) = p(a,x)/2   (A≼B, forward)
EQ4 = indep_eqs("x", "by")     # p(b,x,y) = p(b,y)/2   (A≼B, backward)
EQ5 = indep_eqs("a", "by")     # p(a,b,y) = p(b,y)/2   (B≼A, forward)
EQ6 = indep_eqs("y", "ax")     # p(a,x,y) = p(a,x)/2   (B≼A, backward)
POS = [([F(-1) if j == i else F(0) for j in range(D)], F(0)) for i in range(D)]


def satisfies(p, eqs):
    return all(sum(e * q for e, q in zip(ev, p)) == e0 for ev, e0 in eqs)


def functional(win):
    return [F(1) if win(*c) else F(0) for c in COORD]


GYNI = functional(lambda a, b, x, y: x == b and y == a)
GYNI_R = functional(lambda a, b, x, y: x == b and y == a)          # D3: the same functional
LGYNI_F = functional(lambda a, b, x, y: a * (x ^ b) == 0 and b * (y ^ a) == 0)
LGYNI_B = functional(lambda a, b, x, y: x * (a ^ y) == 0 and y * (b ^ x) == 0)
# MH-9 literally at N_α=N_β=1 (D2): the only setting is = 1 or = 0
MH9_ALPHA1 = functional(lambda a, b, x, y: (y ^ a) == 0 and (x ^ b) == 0)
MH9_ALPHA0 = functional(lambda a, b, x, y: True)


# ------------------------------------------------------------------ circuits (deterministic)

def circuit_distributions(k):
    """All distributions of deterministic classical TS circuits A≼B with an ancilla of size k.
    Bijections of 2-bit pairs (income, input) -> (outcome, output); the Alice->Bob channel is
    given by a balanced function (o_A, anc) -> i_B (the ancilla output is discarded)."""
    perms = list(itertools.permutations(range(4)))           # index = 2*first + second
    pairs = [(i >> 1, i & 1) for i in range(4)]
    cells = list(itertools.product(BITS, range(k)))           # (o_A, anc)
    chans = [f for f in itertools.product(BITS, repeat=2 * k) if sum(f) == k]
    w = F(1, 4 * 2 * k)
    out = set()
    for pa in perms:
        for ch in chans:
            for pb in perms:
                p = [F(0)] * D
                for a, b, i_a, anc in itertools.product(BITS, BITS, BITS, range(k)):
                    x, o_a = pairs[pa[2 * a + i_a]]
                    i_b = ch[cells.index((o_a, anc))]
                    y, _ = pairs[pb[2 * b + i_b]]
                    p[SC.idx[(a, b, x, y)]] += w
                out.add(tuple(p))
    return out


# ------------------------------------------------------------------ K (B15 facets)

def branciard_K(proj):
    """48 B15 facets in the forward and 48 in the backward reading as functionals on p(a,b,x,y) (via D1)."""
    Vb = [tuple(F(x) for x in v) for v in calib.causal_vertices()]
    _, ineqs = P.facets_cdd(Vb)
    K = {}
    for c, c0 in ineqs:
        cc = dict(zip(calib.COORD, c))                        # calib: (X, Y, A, B), A,B — inputs
        # forward reading: inputs = incomes (a,b), outputs = outcomes (x,y); p(x,y|a,b) = 4 p(a,b,x,y)
        fwd = [4 * cc[(x, y, a, b)] for (a, b, x, y) in COORD]
        # backward reading: inputs = outcomes (x,y), outputs = incomes (a,b); p(a,b|x,y) = 4 p
        bwd = [4 * cc[(a, b, x, y)] for (a, b, x, y) in COORD]
        K.setdefault(P.projected(fwd, c0, proj), set()).add("fwd")
        K.setdefault(P.projected(bwd, c0, proj), set()).add("bwd")
    return K, len(ineqs)


# ------------------------------------------------------------------ helpers

def gen(f):
    return SC.perm_from_map(lambda t: f(*t))


GENS = {
    "swap":   gen(lambda a, b, x, y: (b, a, y, x)),
    "TR":     gen(lambda a, b, x, y: (x, y, a, b)),
    "flip_a": gen(lambda a, b, x, y: (1 - a, b, x, y)),
    "flip_b": gen(lambda a, b, x, y: (a, 1 - b, x, y)),
    "flip_x": gen(lambda a, b, x, y: (a, b, 1 - x, y)),
    "flip_y": gen(lambda a, b, x, y: (a, b, x, 1 - y)),
}
NEG_CONTROLS = {
    "cflip_x_by_a": gen(lambda a, b, x, y: (a, b, x ^ a, y)),
    "TR_alice_only": gen(lambda a, b, x, y: (x, b, a, y)),
}


def display_form(members, proj):
    """The most symmetric member of the class (invariance under swap, reversal, their composition),
    then the minimal support; weights 0/1 after dividing by the common factor."""
    sw, tr = GENS["swap"], GENS["TR"]
    best = None
    for f in members:
        inv = {n: P.projected(P.act_ineq(g, f[:-1]), f[-1], proj) == f
               for n, g in (("swap", sw), ("TR", tr), ("swap_TR", P.compose(sw, tr)))}
        nf = nicest(list(f))
        m = max(nf["weights"].values())
        sup = [t for t, v in nf["weights"].items() if v]
        key = (-sum(inv.values()), len(sup), sup)
        if best is None or key < best[0]:
            ok01 = all(v in (0, m) for v in nf["weights"].values())
            best = (key, {"support_abxy_weight1": sup if ok01 else None,
                          "weights_if_not_01": None if ok01 else nf["weights"],
                          "rhs": P.fr(F(nf["rhs"]) / m) if ok01 else nf["rhs"],
                          "invariant_under": [n for n, v in inv.items() if v]})
    return best[1]


def table(f):
    """Facet coefficients as a table: rows (a,b), columns (x,y); plus the right-hand side."""
    c, c0 = f[:-1], f[-1]
    rows = {}
    for (a, b, x, y), v in zip(COORD, c):
        rows.setdefault(f"ab={a}{b}", {})[f"xy={x}{y}"] = v
    return {"coeffs": rows, "rhs": c0}


def local_automorphisms(V):
    """All "local" transformations: bijections of the pairs (a,x) for Alice, (b,y) for Bob, ± swap of parties."""
    pairs = list(itertools.product(BITS, BITS))
    found = []
    for sa in itertools.permutations(pairs):
        ma = dict(zip(pairs, sa))
        for sb in itertools.permutations(pairs):
            mb = dict(zip(pairs, sb))
            for swap in (False, True):
                def f(a, b, x, y, ma=ma, mb=mb, swap=swap):
                    a2, x2 = ma[(a, x)]
                    b2, y2 = mb[(b, y)]
                    return (b2, a2, y2, x2) if swap else (a2, b2, x2, y2)
                g = gen(f)
                if P.is_automorphism(g, V):
                    found.append(g)
    return found


def vertices_of(eqs):
    return P.vertices_cdd(eqs, POS)


def cond_gyni(p):
    """Conditional form (8): (1/4) Σ δ p(x,y|a,b); None if some p(a,b)=0."""
    tot = F(0)
    for a, b in itertools.product(BITS, BITS):
        pab = sum(p[SC.idx[(a, b, x, y)]] for x, y in itertools.product(BITS, BITS))
        if pab == 0:
            return None
        tot += p[SC.idx[(a, b, b, a)]] / pab
    return tot / 4


# ------------------------------------------------------------------ main

def main():
    t0 = time.time()
    out = {"stage": "B", "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
           "definition": "Def-II (PREREGISTRATION.md §1)"}

    # --------------------------------------------------------- B.2 vertices
    E_AB = NORM + D1 + EQ3 + EQ4
    E_BA = NORM + D1 + EQ5 + EQ6
    V_AB = vertices_of(E_AB)
    V_BA = vertices_of(E_BA)
    V = sorted(set(V_AB) | set(V_BA))
    common = set(V_AB) & set(V_BA)
    out["vertices"] = {"P_AB": len(V_AB), "P_BA": len(V_BA), "common": len(common),
                       "P_TS_union": len(V),
                       "denominators": sorted({x.denominator for v in V for x in v})}
    # are all points of the union vertices of P_TS? (none in the hull of the rest: checked via cdd)
    # cross-check with deterministic circuits
    cross = {}
    V_AB_set = set(V_AB)
    swapg = GENS["swap"]
    for k in (1, 2, 4):
        dists = circuit_distributions(k)
        inside = all(satisfies(p, E_AB) and min(p) >= 0 for p in dists)
        cross[f"anc{k}"] = {"distinct_distributions": len(dists), "all_inside_P_AB": inside,
                            "vertices_of_P_AB_realized": sum(v in dists for v in V_AB_set)}
        if not inside:
            out["STOP"] = f"точка схемы вне P_AB (анцилла {k})"
    ba_from_swap = {P.act_point(swapg, v) for v in V_AB}
    cross["P_BA_equals_swap_of_P_AB"] = ba_from_swap == set(V_BA)
    out["vertex_crosscheck"] = cross

    # --------------------------------------------------------- affine hull, projection
    hull = P.affine_hull(V)
    proj = P.Projector(hull)
    dim = D - len(hull)
    out["affine_dim"] = dim
    # is the hull given exactly by NORM + D1?
    out["hull_equals_norm_plus_D1"] = (
        P.rank([list(e) + [e0] for e, e0 in hull]) == P.rank([list(e) + [e0] for e, e0 in NORM + D1])
        == P.rank([list(e) + [e0] for e, e0 in hull + NORM + D1]))

    # --------------------------------------------------------- gate: known maxima
    gates = {
        "GYNI": P.fr(P.max_over(GYNI, V)),
        "GYNI_reversed": P.fr(P.max_over(GYNI_R, V)),
        "LGYNI_fwd": P.fr(P.max_over(LGYNI_F, V)),
        "LGYNI_bwd": P.fr(P.max_over(LGYNI_B, V)),
    }
    gates_expected = {"GYNI": "1/2", "GYNI_reversed": "1/2", "LGYNI_fwd": "3/4", "LGYNI_bwd": "3/4"}
    out["gates"] = {"values": gates, "expected": gates_expected,
                    "pass": gates == gates_expected,
                    "GYNI_equals_GYNI_reversed_as_functional": GYNI == GYNI_R,
                    "MH9_literal_alpha1_max": P.fr(P.max_over(MH9_ALPHA1, V)),
                    "MH9_literal_alpha0_max": P.fr(P.max_over(MH9_ALPHA0, V))}
    if not out["gates"]["pass"]:
        out["STOP"] = "ворота известных максимумов не пройдены"

    # --------------------------------------------------------- group: anti-vacuum
    autos = {k: P.is_automorphism(g, V) for k, g in GENS.items()}
    nontriv = {k: g != tuple(range(D)) for k, g in GENS.items()}
    rng = random.Random(20260921)
    rperm = list(range(D))
    rng.shuffle(rperm)
    negs = {k: P.is_automorphism(g, V) for k, g in NEG_CONTROLS.items()}
    negs["random_permutation"] = P.is_automorphism(tuple(rperm), V)
    # known inequalities with relabelings: GYNI, LGYNI_f, LGYNI_b and their images under the flips
    known = {"GYNI": (GYNI, F(1, 2)), "LGYNI_fwd": (LGYNI_F, F(3, 4)), "LGYNI_bwd": (LGYNI_B, F(3, 4))}
    known["GYNI_flip_x"] = (P.act_ineq(GENS["flip_x"], GYNI), F(1, 2))
    gen_tests = {}
    for gname, g in GENS.items():
        moved, valid = [], True
        for kname, (c, c0) in known.items():
            img = P.act_ineq(g, c)
            if P.projected(img, c0, proj) != P.projected(c, c0, proj):
                moved.append(kname)
            if P.max_over(img, V) != c0:
                valid = False
        gen_tests[gname] = {"moves": moved, "image_valid_same_bound": valid}
    G = P.group_closure(list(GENS.values()))
    Gp = P.group_closure([g for k, g in GENS.items() if k != "TR"])
    local = local_automorphisms(V)
    out["group"] = {
        "order_G": len(G), "order_G_without_TR": len(Gp),
        "generators_nontrivial": nontriv, "generators_automorphisms": autos,
        "generator_action_on_known": gen_tests,
        "negative_controls_rejected": {k: (not v) for k, v in negs.items()},
        "full_local_automorphism_group_order": len(local),
        "G_subset_of_local": set(G) <= set(local),
    }
    gpass = (all(autos.values()) and all(nontriv.values()) and not any(negs.values())
             and all(t["moves"] and t["image_valid_same_bound"] for t in gen_tests.values()))
    out["group"]["pass"] = gpass
    if not gpass:
        out["STOP"] = "антивакуумный тест группы не пройден"

    # --------------------------------------------------------- B.3 facets: cdd.gmp and lrs
    t1 = time.time()
    _, ineq_cdd = P.facets_cdd(V)
    t_cdd = time.time() - t1
    t1 = time.time()
    _, ineq_lrs = P.facets_lrs(V)
    t_lrs = time.time() - t1
    S_cdd = [P.projected(c, c0, proj) for c, c0 in ineq_cdd]
    S_lrs = {P.projected(c, c0, proj) for c, c0 in ineq_lrs}
    facets = sorted(set(S_cdd))
    valid = all(P.max_over(f[:-1], V) == f[-1] for f in facets)
    is_facet = all(P.tight_rank(f[:-1], f[-1], V) == dim - 1 for f in facets)
    out["facets"] = {"cdd": len(ineq_cdd), "lrs": len(ineq_lrs), "distinct": len(facets),
                     "cdd_equals_lrs_after_projection": set(S_cdd) == S_lrs,
                     "all_valid": valid, "all_are_facets": is_facet,
                     "seconds_cdd": round(t_cdd, 3), "seconds_lrs": round(t_lrs, 3)}
    if not (set(S_cdd) == S_lrs and valid and is_facet):
        out["STOP"] = "фасеты: расхождение инструментов или невалидная строка"

    # --------------------------------------------------------- B.4 canonicalisation, classes
    K, nb = branciard_K(proj)
    pos = {P.projected(c, c0, proj) for c, c0 in POS}
    TR = GENS["TR"]
    z = [F(1, 4) if (x == a and y == (a ^ b)) else F(0) for (a, b, x, y) in COORD]
    classes = {}
    for f in facets:
        classes.setdefault(P.canonical(f[:-1], f[-1], proj, G), []).append(f)
    cls_out = []
    for rep, members in sorted(classes.items(), key=lambda kv: (-len(kv[1]), kv[0])):
        f = members[0]
        in_K = sorted({t for m in members for t in K.get(m, ())})
        tr_img = P.projected(P.act_ineq(TR, f[:-1]), f[-1], proj)
        directional = (P.canonical(tr_img[:-1], tr_img[-1], proj, Gp)
                       != P.canonical(f[:-1], f[-1], proj, Gp))
        tight = sum(1 for v in V if sum(a * b for a, b in zip(f[:-1], v)) == f[-1])
        zval = sum(a * b for a, b in zip(f[:-1], z))
        cls_out.append({
            "size": len(members),
            "members_in_K": sum(m in K for m in members),
            "in_K": bool(in_K), "K_readings": in_K,
            "positivity": all(m in pos for m in members),
            "directional": directional,
            "tight_vertices": tight,
            "members_violated_by_separating_point": sum(
                1 for m in members if sum(a * b for a, b in zip(m[:-1], z)) > m[-1]),
            "nicest_form": nicest(list(rep)),
            "display_form": display_form(members, proj),
            "representative": table(rep),
        })
    n_new = sum(1 for c in cls_out if not c["in_K"])

    # anti-vacuum test for directionality: LGYNI_fwd is directional (its reversal is LGYNI_bwd),
    # GYNI is not (D3); if the test does not tell them apart, it is vacuous
    def directional_of(c, c0):
        f = P.projected(c, c0, proj)
        t = P.projected(P.act_ineq(TR, f[:-1]), f[-1], proj)
        return P.canonical(t[:-1], t[-1], proj, Gp) != P.canonical(f[:-1], f[-1], proj, Gp)
    dir_ctrl = {"LGYNI_fwd_directional": directional_of(LGYNI_F, F(3, 4)),
                "GYNI_directional": directional_of(GYNI, F(1, 2))}
    dir_ctrl["pass"] = dir_ctrl["LGYNI_fwd_directional"] and not dir_ctrl["GYNI_directional"]
    if not dir_ctrl["pass"]:
        out["STOP"] = "тест направленности вакуумен"
    known_face = {n: P.tight_rank(c, b, V) for n, c, b in
                  (("GYNI", GYNI, F(1, 2)), ("LGYNI_fwd", LGYNI_F, F(3, 4)), ("LGYNI_bwd", LGYNI_B, F(3, 4)))}
    n_new_dir = sum(1 for c in cls_out if not c["in_K"] and c["directional"])
    # classes under the full local automorphism group (if it is larger than G)
    classes_full = len({P.canonical(f[:-1], f[-1], proj, local) for f in facets})
    # does K lie in the intersection? separating point z: inside the K polytope, but outside P_TS
    z_in_K = all(sum(a * b for a, b in zip(f[:-1], z)) <= f[-1] for f in K)
    z_in_PTS = all(sum(a * b for a, b in zip(f[:-1], z)) <= f[-1] for f in facets)
    K_all_valid_on_PTS = all(P.max_over(f[:-1], V) <= f[-1] for f in K)
    K_facets_of_PTS = sum(1 for f in K if f in set(facets))
    out["classes"] = {
        "count_G": len(cls_out), "count_full_local_group": classes_full,
        "directional_test_control": dir_ctrl,
        "known_face_dim(facet = dim-1)": known_face,
        "new_classes": n_new, "new_directional_classes": n_new_dir,
        "facets_in_K": sum(1 for f in facets if f in K), "facets_not_in_K": sum(1 for f in facets if f not in K),
        "K_size_distinct": len(K), "K_source_facets_each_reading": nb,
        "K_all_valid_on_P_TS": K_all_valid_on_PTS, "K_elements_that_are_facets_of_P_TS": K_facets_of_PTS,
        "separating_point_z": "x=a, y=a⊕b, (a,b) равномерно",
        "z_satisfies_all_K": z_in_K, "z_in_P_TS": z_in_PTS,
        "list": cls_out,
    }
    if n_new == 0:
        outcome = "ОТРИЦАТЕЛЬНЫЙ: все классы в K"
    elif n_new_dir > 0:
        outcome = "ПОЛОЖИТЕЛЬНЫЙ: есть направленный класс вне K (кандидат в Stage C)"
    else:
        outcome = "НОВЫЙ, НО НЕНАПРАВЛЕННЫЙ: классы вне K есть, все G'-эквивалентны своему обращению"
    out["outcome"] = outcome if "STOP" not in out else "СТОП: " + out["STOP"]

    # --------------------------------------------------------- Def-I (sensitivity control)
    t1 = time.time()
    V1_AB = vertices_of(NORM + EQ3 + EQ4)
    V1_BA = vertices_of(NORM + EQ5 + EQ6)
    V1 = sorted(set(V1_AB) | set(V1_BA))
    _, ineq1 = P.facets_cdd(V1)
    proj1 = P.Projector(P.affine_hull(V1))
    f1 = sorted({P.projected(c, c0, proj1) for c, c0 in ineq1})
    G1 = [g for g in G if P.is_automorphism(g, V1)]
    cls1 = len({P.canonical(f[:-1], f[-1], proj1, G1) for f in f1})
    # conditional form (8) on mixtures of the Def-I vertices: random search, fixed seed
    rng = random.Random(1508)
    best, best_mix = F(0), None
    for _ in range(4000):
        pts = rng.sample(V1, 3)
        ws = [F(rng.randint(1, 20)) for _ in pts]
        s = sum(ws)
        p = tuple(sum(w * v[i] for w, v in zip(ws, pts)) / s for i in range(D))
        val = cond_gyni(p)
        if val is not None and val > best:
            best, best_mix = val, p
    out["def_I"] = {"P_AB": len(V1_AB), "P_BA": len(V1_BA), "P_TS_union": len(V1),
                    "affine_dim": D - len(P.affine_hull(V1)), "facets": len(f1),
                    "classes_G_restricted_to_automorphisms": cls1, "G_automorphisms": len(G1),
                    "max_conditional_GYNI_eq8_found_on_mixtures": P.fr(best),
                    "eq8_violated_by_causally_separable_mixture": best > F(1, 2),
                    "witness": [P.fr(x) for x in best_mix] if best_mix else None,
                    "linear_GYNI_max": P.fr(P.max_over(GYNI, V1)),
                    "seconds": round(time.time() - t1, 2)}

    out["resources"] = {"seconds_total": round(time.time() - t0, 2),
                        "max_rss_MB": round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024, 1)}
    jd = os.path.join(ROOT, "results", "json")
    os.makedirs(jd, exist_ok=True)
    with open(os.path.join(jd, "stage_b.json"), "w") as fh:
        json.dump(out, fh, ensure_ascii=False, indent=1)
    with open(os.path.join(jd, "stage_b_facets.json"), "w") as fh:
        json.dump({"coords_order_abxy": ["".join(map(str, c)) for c in COORD],
                   "vertices": [[P.fr(x) for x in v] for v in V],
                   "facets_projected_primitive": [list(f) for f in facets],
                   "note": "фасета f: sum(f[i]*p[i]) <= f[-1]; проекция на aff(P_TS)"},
                  fh, ensure_ascii=False, indent=0)
    brief = {k: out[k] for k in ("vertices", "vertex_crosscheck", "affine_dim", "gates", "facets",
                                 "outcome", "def_I", "resources")}
    brief["group"] = {k: out["group"][k] for k in ("order_G", "full_local_automorphism_group_order",
                                                   "negative_controls_rejected", "pass")}
    brief["classes"] = {k: v for k, v in out["classes"].items() if k != "list"}
    brief["class_summary"] = [{k: c[k] for k in ("size", "in_K", "K_readings", "positivity",
                                                  "directional", "tight_vertices",
                                                  "members_violated_by_separating_point")}
                              for c in cls_out]
    print(json.dumps(brief, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()

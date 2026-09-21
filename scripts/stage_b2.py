"""
Stage B.2 — приписываемость, происхождение вершин, чувствительность к равномерности,
замыкание классических схем. Определения — PREREGISTRATION_B2.md, цитаты — SOURCES.md
(MH-15…MH-21, D4). Результат: results/json/stage_b2.json.
"""
import itertools
import json
import os
import random
import sys
import time
from fractions import Fraction
from math import lcm

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import polytope as P  # noqa: E402
import stage_b as B  # noqa: E402
from pretty import nicest  # noqa: E402

F = Fraction
D = B.D
COORD = B.COORD
IDX = B.SC.idx
BITS = (0, 1)
U_AB = B.D1[:4]                   # p(a,b) = 1/4
U_XY = B.D1[4:]                   # p(x,y) = 1/4
U = {"U2": U_AB + U_XY, "U1": U_AB, "U0": []}
Z = tuple(F(1, 4) if (x == a and y == (a ^ b)) else F(0) for (a, b, x, y) in COORD)
G = P.group_closure(list(B.GENS.values()))
GP = P.group_closure([g for k, g in B.GENS.items() if k != "TR"])
TR = B.GENS["TR"]


def verts(eqs):
    return P.vertices_cdd(eqs, B.POS)


def hull_of(*vsets):
    return P.extreme_points(sorted(set().union(*[set(v) for v in vsets])))


def build(u):
    """Все многогранники при данном условии равномерности."""
    base = B.NORM + U[u]
    V = {k: verts(base + e) for k, e in (("AB", B.EQ3 + B.EQ4), ("BA", B.EQ5 + B.EQ6),
                                         ("F_AB", B.EQ3), ("F_BA", B.EQ5),
                                         ("B_AB", B.EQ4), ("B_BA", B.EQ6))}
    return {"V": V, "TS": hull_of(V["AB"], V["BA"]), "F": hull_of(V["F_AB"], V["F_BA"]),
            "B": hull_of(V["B_AB"], V["B_BA"]), "base": base}


def facets(V):
    """Фасеты (cdd.gmp) с проверкой lrs; проекция на aff(V)."""
    hull = P.affine_hull(V)
    proj = P.Projector(hull)
    _, ic = P.facets_cdd(V)
    _, il = P.facets_lrs(V)
    fc = sorted({P.projected(c, c0, proj) for c, c0 in ic})
    fl = {P.projected(c, c0, proj) for c, c0 in il}
    return fc, proj, hull, set(fc) == fl


def classify(f, VF, VB):
    c, c0 = f[:-1], f[-1]
    mf, mb = P.max_over(c, VF), P.max_over(c, VB)
    vf, vb = mf > c0, mb > c0
    kind = ("смешанное" if vf and vb else "направленное вперёд" if vb else
            "направленное назад" if vf else "общее")
    return kind, mf, mb


def classes_of(fs, proj, group):
    cl = {}
    for f in fs:
        cl.setdefault(P.canonical(f[:-1], f[-1], proj, group), []).append(f)
    return sorted(cl.items(), key=lambda kv: (-len(kv[1]), kv[0]))


def K_by_reading(proj):
    """K_fwd / K_bwd по отдельности (как в stage_b.branciard_K)."""
    import causal_polytope_calib as calib
    Vb = [tuple(F(x) for x in v) for v in calib.causal_vertices()]
    _, ineqs = P.facets_cdd(Vb)
    fwd, bwd = [], []
    for c, c0 in ineqs:
        cc = dict(zip(calib.COORD, c))
        fwd.append(P.projected([4 * cc[(x, y, a, b)] for (a, b, x, y) in COORD], c0, proj))
        bwd.append(P.projected([4 * cc[(a, b, x, y)] for (a, b, x, y) in COORD], c0, proj))
    return fwd, bwd


def fr(x):
    return P.fr(x)


# ------------------------------------------------------------------ замыкание классических схем

TYPES = list(itertools.product(BITS, repeat=2))
PAIRS = list(itertools.product(TYPES, TYPES))


def mu_image(mu):
    p = [F(0)] * D
    for m, (tA, tB) in zip(mu, PAIRS):
        if m:
            for x, b in itertools.product(BITS, BITS):
                p[IDX[(tA[x], b, x, tB[b])]] += m / 4
    return tuple(p)


def closure_AB():
    M_eqs = [([F(1)] * 16, F(1)), ([F(sum(t)) for t, _ in PAIRS], F(1)),
             ([F(sum(t)) for _, t in PAIRS], F(1))]
    M_pos = [([F(-1) if j == i else F(0) for j in range(16)], F(0)) for i in range(16)]
    Mv = P.vertices_cdd(M_eqs, M_pos)
    return Mv, P.extreme_points(sorted({mu_image(m) for m in Mv}))


def simulate_mu(mu):
    """Явная схема A≼B для рациональной μ: dA = dB = N, биекции строятся по построению,
    распределение считается прямым прогоном биекций (независимо от mu_image)."""
    N = lcm(*[m.denominator for m in mu if m])
    cells = []
    for m, pair in zip(mu, PAIRS):
        cells += [pair] * int(m * N)
    assert len(cells) == N
    # Алиса: (a, i) -> (x, o), a = tA(o)[x]
    pre = {a: [(x, o) for o in range(N) for x in BITS if cells[o][0][x] == a] for a in BITS}
    assert all(len(pre[a]) == N for a in BITS), "h не сбалансирована"
    piA = {(a, i): pre[a][i] for a in BITS for i in range(N)}
    assert len(set(piA.values())) == 2 * N, "π_A не биекция"
    # Боб: (b, i_B) -> (y, o_B), y = tB(i_B)[b]; канал i_B = o
    preB = {y: [(b, i) for i in range(N) for b in BITS if cells[i][1][b] == y] for y in BITS}
    assert all(len(preB[y]) == N for y in BITS), "g не сбалансирована"
    piB = {bi: (y, k) for y in BITS for k, bi in enumerate(preB[y])}
    assert len(set(piB.values())) == 2 * N, "π_B не биекция"
    p = [F(0)] * D
    w = F(1, 4 * N)
    for a, b, i in itertools.product(BITS, BITS, range(N)):
        x, o = piA[(a, i)]
        y, _ = piB[(b, o)]
        p[IDX[(a, b, x, y)]] += w
    return tuple(p), N


# ------------------------------------------------------------------ main

def main():
    t0 = time.time()
    out = {"stage": "B2", "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S")}
    polys = {u: build(u) for u in ("U2", "U1", "U0")}
    S = polys["U2"]
    V_TS = S["TS"]

    # ============================================================ п. 2 происхождение вершин
    stageB = [tuple(F(x) for x in v) for v in
              json.load(open(os.path.join(P.ROOT, "results", "json", "stage_b_facets.json")))["vertices"]]
    lrs_AB = set(P.vertices_lrs(S["base"] + B.EQ3 + B.EQ4, B.POS))
    lrs_BA = set(P.vertices_lrs(S["base"] + B.EQ5 + B.EQ6, B.POS))
    den = lambda v: max(x.denominator for x in v if x)  # noqa: E731
    out["item2"] = {
        "stage_B_method": "крайние точки H-описания (ур. (3),(4) | (5),(6) + p>=0 + Σp=1 + U2) через "
                          "cdd.gmp (P.vertices_cdd в stage_b.py); детерминированные схемы — только перекрёстная проверка",
        "cdd_AB": len(S["V"]["AB"]), "lrs_AB": len(lrs_AB), "cdd_BA": len(S["V"]["BA"]), "lrs_BA": len(lrs_BA),
        "cdd_equals_lrs": lrs_AB == set(S["V"]["AB"]) and lrs_BA == set(S["V"]["BA"]),
        "union_equals_stage_B_vertices": (lrs_AB | lrs_BA) == set(stageB),
        "all_union_points_extreme_in_TS": set(V_TS) == (lrs_AB | lrs_BA),
        "AB_vertex_max_denominator_histogram": {str(d): sum(1 for v in lrs_AB if den(v) == d)
                                                for d in sorted({den(v) for v in lrs_AB})},
        "AB_vertex_support_sizes": sorted({sum(1 for x in v if x) for v in lrs_AB}),
        "max_coordinate_any_vertex": fr(max(max(v) for v in V_TS)),
    }
    out["item2"]["pass"] = out["item2"]["cdd_equals_lrs"] and out["item2"]["union_equals_stage_B_vertices"]

    # ============================================================ п. 1 приписываемость (U2)
    VF, VB = S["F"], S["B"]
    fs, proj, hull, agree = facets(V_TS)
    eqF, inF = P.facets_cdd(VF)
    eqB, inB = P.facets_cdd(VB)
    sym = {k: {"F": P.is_automorphism(g, VF), "B": P.is_automorphism(g, VB)} for k, g in B.GENS.items()}
    tr_swaps = {P.act_point(TR, v) for v in VF} == set(VB)
    # F∩B
    eq_FB = eqF + eqB
    V_FB = P.vertices_cdd(eq_FB, inF + inB)
    V_FB_lrs = P.vertices_lrs(eq_FB, inF + inB)
    ts_inside = all(P.in_H(v, eq_FB, inF + inB) for v in V_TS)
    outside = [v for v in V_FB if v not in set(V_TS)]
    ts_facets_H = [(f[:-1], f[-1]) for f in fs]
    witnesses = []
    for v in outside[:1000]:
        cut = [f for f in fs if P.dot(f[:-1], v) > f[-1]]
        witnesses.append({"vertex": [fr(x) for x in v], "is_z": v == Z,
                          "cut_by_n_TS_facets": len(cut),
                          "one_cutting_facet_nicest": nicest(list(cut[0])) if cut else None})
    zinfo = {"in_F": P.in_H(Z, eqF, inF), "in_B": P.in_H(Z, eqB, inB),
             "in_F_AB": P.in_H(Z, S["base"] + B.EQ3, B.POS), "in_F_BA": P.in_H(Z, S["base"] + B.EQ5, B.POS),
             "in_B_AB": P.in_H(Z, S["base"] + B.EQ4, B.POS), "in_B_BA": P.in_H(Z, S["base"] + B.EQ6, B.POS),
             "in_TS": all(P.dot(f[:-1], Z) <= f[-1] for f in fs), "vertex_of_F_cap_B": Z in set(V_FB)}
    # калибровка теста
    Kf, Kb = K_by_reading(proj)
    kf_cls = [classify(k, VF, VB)[0] for k in Kf]
    trK = []
    for k, kind in zip(Kf, kf_cls):
        if kind == "направленное вперёд":
            t = P.projected(P.act_ineq(TR, k[:-1]), k[-1], proj)
            trK.append(classify(t, VF, VB)[0])
    pos_kind = classify(P.projected(B.POS[0][0], 0, proj), VF, VB)[0]
    gyni = classify(P.projected(B.GYNI, F(1, 2), proj), VF, VB)
    lg = classify(P.projected(B.LGYNI_F, F(3, 4), proj), VF, VB)
    calib = {"K_fwd_all_hold_on_F": all(k != "направленное назад" and k != "смешанное" for k in kf_cls),
             "K_fwd_kinds": {k: kf_cls.count(k) for k in sorted(set(kf_cls))},
             "K_fwd_forward_directional_exists": "направленное вперёд" in kf_cls,
             "TR_images_backward": (all(t == "направленное назад" for t in trK) and bool(trK)),
             "positivity": pos_kind,
             "GYNI_prompt_control": {"kind": gyni[0], "max_F": fr(gyni[1]), "max_B": fr(gyni[2])},
             "LGYNI_fwd": {"kind": lg[0], "max_F": fr(lg[1]), "max_B": fr(lg[2])}}
    calib["pass"] = (calib["K_fwd_all_hold_on_F"] and calib["K_fwd_forward_directional_exists"]
                     and calib["TR_images_backward"] and pos_kind == "общее")
    # классы TS
    cls = []
    for rep, mem in classes_of(fs, proj, G):
        kinds = [classify(m, VF, VB) for m in mem]
        kset = sorted({k for k, _, _ in kinds})
        cls.append({"size": len(mem), "canonical": list(rep), "nicest": nicest(list(rep)),
                    "member_kinds": {k: sum(1 for kk, _, _ in kinds if kk == k) for k in kset},
                    "class_kind": kset[0] if len(kset) == 1 else "/".join(kset),
                    "max_F_range": [fr(min(m for _, m, _ in kinds)), fr(max(m for _, m, _ in kinds))],
                    "max_B_range": [fr(min(m for _, _, m in kinds)), fr(max(m for _, _, m in kinds))],
                    "rhs": rep[-1]})
    posform = P.canonical(B.POS[0][0], 0, proj, G)
    for c in cls:
        c["positivity"] = tuple(c["canonical"]) == posform
    out["item1"] = {
        "F_vertices": len(VF), "B_vertices": len(VB), "F_facets": len(inF), "B_facets": len(inB),
        "F_B_affine_dim": (D - len(P.affine_hull(VF)), D - len(P.affine_hull(VB))),
        "symmetries_preserve_F_B": sym, "TR_maps_F_to_B": tr_swaps,
        "TS_facets": len(fs), "TS_facets_cdd_equals_lrs": agree,
        "F_cap_B_vertices": len(V_FB), "F_cap_B_vertices_lrs_equal": set(V_FB) == set(V_FB_lrs),
        "TS_inside_F_cap_B": ts_inside, "TS_equals_F_cap_B": set(V_FB) == set(V_TS),
        "F_cap_B_vertices_outside_TS": len(outside),
        "F_cap_B_vertex_denominators": sorted({x.denominator for v in V_FB for x in v}),
        "witness_z_first": sorted(witnesses, key=lambda w: not w["is_z"])[:3],
        "z": zinfo, "calibration": calib, "classes": cls,
    }

    # ============================================================ п. 3 чувствительность
    item3 = {}
    N_forms = {i: tuple(c["canonical"]) for i, c in enumerate(cls) if not c["positivity"]}
    for u in ("U1", "U0"):
        Su = polys[u]
        fsu, proju, _, agu = facets(Su["TS"])
        Gu = [g for g in G if P.is_automorphism(g, Su["TS"])]
        gens_u = {k: P.is_automorphism(g, Su["TS"]) for k, g in B.GENS.items()}
        clu = classes_of(fsu, proju, Gu)
        # выживание классов U2: U2-каноническая форма фасет U_u
        u2forms = {}
        for f in fsu:
            # фасета U_u валидна на TS_U2 (TS_U2 ⊂ TS_Uu); её U2-канонический вид
            u2forms.setdefault(P.canonical(f[:-1], f[-1], proj, G), []).append(f)
        surv = {}
        for i, form in N_forms.items():
            hits = u2forms.get(form, [])
            info = {"survives": bool(hits), "n_facets": len(hits)}
            if hits:
                kinds = sorted({classify(h, Su["F"], Su["B"])[0] for h in hits})
                info["attribution_in_" + u] = kinds
            surv[f"class_{i + 1}_size{cls[i]['size']}"] = info
        ukinds = []
        for rep, mem in clu:
            ks = sorted({classify(m, Su["F"], Su["B"])[0] for m in mem})
            ukinds.append({"size": len(mem), "kinds": ks, "nicest": nicest(list(rep))})
        item3[u] = {"V_AB": len(Su["V"]["AB"]), "V_BA": len(Su["V"]["BA"]), "V_TS": len(Su["TS"]),
                    "affine_dim": D - len(P.affine_hull(Su["TS"])), "facets": len(fsu), "cdd_equals_lrs": agu,
                    "group_order": len(Gu), "generators_automorphisms": gens_u,
                    "classes": len(clu), "class_kinds": ukinds,
                    "mixed_classes": sum(1 for c in ukinds if c["kinds"] == ["смешанное"]),
                    "survival_of_U2_new_classes": surv,
                    "z_in_TS": all(P.dot(f[:-1], Z) <= f[-1] for f in fsu)}
    # (8) и (10) в условной форме
    rng = random.Random(1508)
    V1 = sorted(set(polys["U0"]["V"]["AB"]) | set(polys["U0"]["V"]["BA"]))
    best = F(0)
    for _ in range(4000):
        pts = rng.sample(V1, 3)
        ws = [F(rng.randint(1, 20)) for _ in pts]
        s = sum(ws)
        p = tuple(sum(w * v[i] for w, v in zip(ws, pts)) / s for i in range(D))
        val = B.cond_gyni(p)
        if val is not None and val > best:
            best = val
    item3["U0"]["eq8_conditional_max_found"] = fr(best)

    def cond10(p):
        tot = F(0)
        for x, y in itertools.product(BITS, BITS):
            pxy = sum(p[IDX[(a, b, x, y)]] for a, b in itertools.product(BITS, BITS))
            if pxy == 0:
                return None
            tot += p[IDX[(y, x, x, y)]] / pxy          # δ_{x,b} δ_{y,a}: a = y, b = x
        return tot / 4
    V1u = sorted(set(polys["U1"]["V"]["AB"]) | set(polys["U1"]["V"]["BA"]))
    rng = random.Random(1510)
    b10 = F(0)
    for _ in range(4000):
        pts = rng.sample(V1u, 3)
        ws = [F(rng.randint(1, 20)) for _ in pts]
        s = sum(ws)
        p = tuple(sum(w * v[i] for w, v in zip(ws, pts)) / s for i in range(D))
        val = cond10(p)
        if val is not None and val > b10:
            b10 = val
    item3["U1"]["eq8_linear_max"] = fr(P.max_over(B.GYNI, polys["U1"]["TS"]))
    item3["U1"]["eq10_conditional_max_found"] = fr(b10)
    item3["U1"]["eq10_violated"] = b10 > F(1, 2)
    out["item3"] = item3

    # ============================================================ п. 4 замыкание
    Mv, extAB = closure_AB()
    swap = B.GENS["swap"]
    V_cl = P.extreme_points(sorted(set(extAB) | {P.act_point(swap, p) for p in extAB}))
    TS_H = [(f[:-1], f[-1]) for f in fs]
    inside = [P.in_H(v, hull, TS_H) for v in V_cl]
    sims = []
    for mu in Mv:
        p_sim, N = simulate_mu(mu)
        sims.append({"N": N, "equal_to_image": p_sim == mu_image(mu),
                     "satisfies_eq3_eq4_U2": B.satisfies(p_sim, S["base"] + B.EQ3 + B.EQ4)})
    fs_cl, proj_cl, hull_cl, ag_cl = facets(V_cl)
    same_hull = (P.rank([list(e) + [e0] for e, e0 in hull_cl]) == len(hull)
                 == P.rank([list(e) + [e0] for e, e0 in hull_cl + hull]))
    cls_cl = []
    cl_forms = set()
    for rep, mem in classes_of(fs_cl, proj_cl, G):
        cl_forms.add(rep)
        kinds = sorted({classify(m, VF, VB)[0] for m in mem})
        cls_cl.append({"size": len(mem), "kinds": kinds, "nicest": nicest(list(rep)),
                       "positivity": rep == P.canonical(B.POS[0][0], 0, proj_cl, G)})
    out["item4"] = {
        "M_vertices": len(Mv), "closure_AB_vertices": len(extAB), "closure_TS_vertices": len(V_cl),
        "all_closure_vertices_inside_TS": all(inside), "n_outside": inside.count(False),
        "closure_vertices_that_are_TS_vertices": sum(1 for v in V_cl if v in set(V_TS)),
        "closure_vertex_denominators": sorted({x.denominator for v in V_cl for x in v}),
        "explicit_circuits": {"n": len(sims), "all_equal_image": all(s["equal_to_image"] for s in sims),
                              "all_satisfy_eq3_eq4_U2": all(s["satisfies_eq3_eq4_U2"] for s in sims),
                              "N_values": sorted({s["N"] for s in sims})},
        "closure_facets": len(fs_cl), "cdd_equals_lrs": ag_cl, "same_affine_hull_as_TS": same_hull,
        "classes": cls_cl,
        "mixed_classes": sum(1 for c in cls_cl if c["kinds"] == ["смешанное"]),
        "TS_new_classes_also_closure_classes": {f"class_{i + 1}_size{cls[i]['size']}": (form in cl_forms)
                                                for i, form in N_forms.items()},
    }

    # ============================================================ исход
    rows = []
    for i, form in N_forms.items():
        name = f"class_{i + 1}_size{cls[i]['size']}"
        rows.append({"class": name, "mixed": cls[i]["class_kind"] == "смешанное",
                     "survives_U1": item3["U1"]["survival_of_U2_new_classes"][name]["survives"],
                     "in_closure": out["item4"]["TS_new_classes_also_closure_classes"][name]})
    cand = [r for r in rows if r["mixed"] and r["survives_U1"] and r["in_closure"]]
    stops = []
    if not out["item2"]["pass"]:
        stops.append("п.2: вершины Stage B не воспроизведены")
    if not all(inside):
        stops.append("п.4: вершина замыкания вне TS")
    if not calib["pass"]:
        stops.append("калибровка теста приписываемости не пройдена")
    if stops:
        outcome = "СТОП/ОШИБКА ПОСТРОЕНИЯ: " + "; ".join(stops)
    elif cand:
        outcome = ("КАНДИДАТ: смешанный класс вне K, переживший U1 и подтверждённый в обоих построениях: "
                   + ", ".join(r["class"] for r in cand))
    elif any(r["mixed"] for r in rows):
        outcome = "ПРОМЕЖУТОЧНЫЙ: смешанные классы есть, но не все условия кандидата выполнены"
    else:
        outcome = "ОТРИЦАТЕЛЬНЫЙ: смешанных классов нет"
    out["outcome"] = {"text": outcome, "table": rows}
    out["seconds_total"] = round(time.time() - t0, 1)
    with open(os.path.join(P.ROOT, "results", "json", "stage_b2.json"), "w") as fh:
        json.dump(out, fh, ensure_ascii=False, indent=1, default=str)
    print(json.dumps({"outcome": out["outcome"], "item2": out["item2"],
                      "item1": {k: v for k, v in out["item1"].items() if k not in ("classes", "witness_z_first")},
                      "item1_classes": [{k: c[k] for k in ("size", "class_kind", "member_kinds", "max_F_range",
                                                            "max_B_range", "rhs")} for c in cls],
                      "item3": {u: {k: v for k, v in d.items() if k != "class_kinds"} for u, d in item3.items()},
                      "item4": {k: v for k, v in out["item4"].items() if k != "classes"},
                      "item4_classes": [{k: c[k] for k in ("size", "kinds", "positivity")} for c in cls_cl]},
                     ensure_ascii=False, indent=1, default=str))


if __name__ == "__main__":
    main()

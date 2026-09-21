"""
Stage B, РАЗВЕДОЧНЫЙ (не предрегистрированный) анализ.

Повод: 8 из 18 вершин P_AB (Def-II) не достигаются детерминированными классическими
TS-схемами (stage_b.json, vertex_crosscheck). Здесь:
  1. перечисляем распределения классических TS-схем A≼B с большими размерностями
     проводов через редукцию (Алиса ≡ сбалансированная a = h(x, o); канал ≡ сбалансированная
     i_B = ch(o, anc); Боб ≡ сбалансированная y = g(b, i_B)); редукция сверяется с прямым
     перебором биекций из stage_b.circuit_distributions;
  2. строим P_TS^circ = conv(схемы A≼B ∪ их образ при обмене сторон) и его фасеты/классы,
     сравниваем с K и с классами основного определения.
Результат: results/json/stage_b_explore.json. В выводы Stage B как основной результат НЕ идёт.
"""
import itertools
import json
import os
import sys
import time
from fractions import Fraction

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import polytope as P  # noqa: E402
import stage_b as B  # noqa: E402
from pretty import nicest  # noqa: E402

F = Fraction


def balanced_maps(n_cells, n_vals):
    """Все отображения [n_cells] -> [n_vals], где у каждого значения n_cells/n_vals прообразов."""
    m = n_cells // n_vals
    return [f for f in itertools.product(range(n_vals), repeat=n_cells)
            if all(f.count(v) == m for v in range(n_vals))]


def extreme_points(pts):
    """Крайние точки конечного множества (удаление избыточных образующих, cdd.gmp)."""
    import cdd.gmp as cddg
    mat = cddg.matrix_from_array([[F(1)] + list(p) for p in pts], rep_type=cddg.RepType.GENERATOR)
    cddg.matrix_canonicalize(mat)
    return [tuple(F(x) for x in row[1:]) for row in mat.array]


def reduced_circuits(dA, k, dB):
    """Распределения p(a,b,x,y) схем A≼B: (x,o) равномерно на [2]x[dA], anc на [k], b на [2]."""
    hs = balanced_maps(2 * dA, 2)                 # a = h(x, o), ячейка 2*o + x
    chs = balanced_maps(dA * k, dB)               # i_B = ch(o, anc), ячейка k*o + anc
    gs = balanced_maps(2 * dB, 2)                 # y = g(b, i_B), ячейка 2*i_B + b
    w = F(1, 2 * dA * k * 2)
    out = set()
    for h in hs:
        for ch in chs:
            for g in gs:
                p = [F(0)] * B.D
                for x, o, anc, b in itertools.product(range(2), range(dA), range(k), range(2)):
                    a = h[2 * o + x]
                    y = g[2 * ch[k * o + anc] + b]
                    p[B.SC.idx[(a, b, x, y)]] += w
                out.add(tuple(p))
    return out


def main():
    t0 = time.time()
    res = {"stage": "B-explore", "preregistered": False,
           "status": "РАЗВЕДКА: оболочка схем усечена по размерностям; классы ниже не являются результатом, "
                     "если cumulative_extreme_points_AB не стабилизировалось",
           "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S")}
    E_AB = B.NORM + B.D1 + B.EQ3 + B.EQ4
    V_AB = set(P.vertices_cdd(E_AB, B.POS))

    # калибровка редукции: при dA=dB=2 и k=1,2,4 должна дать ровно то же, что прямой перебор
    calib = {}
    for k in (1, 2, 4):
        direct = B.circuit_distributions(k)
        red = reduced_circuits(2, k, 2)
        calib[f"dA2_k{k}_dB2"] = {"direct": len(direct), "reduced": len(red), "equal": direct == red}
    res["reduction_calibration"] = calib

    sizes = [(2, 1, 2), (2, 2, 2), (2, 4, 2), (2, 2, 4), (4, 1, 2), (4, 1, 4), (4, 2, 2), (2, 4, 4)]
    allpts, per = set(), {}
    for dA, k, dB in sizes:
        t1 = time.time()
        pts = reduced_circuits(dA, k, dB)
        inside = all(B.satisfies(p, E_AB) and min(p) >= 0 for p in pts)
        new = len(pts - allpts)
        allpts |= pts
        ext = extreme_points(sorted(allpts))
        tr_inv = {P.act_point(B.GENS["TR"], P.act_point(B.GENS["swap"], q)) for q in ext} == set(ext)
        per[f"dA{dA}_k{k}_dB{dB}"] = {"distinct": len(pts), "new_vs_previous": new,
                                      "cumulative_extreme_points_AB": len(ext),
                                      "cumulative_AB_hull_invariant_under_TRswap": tr_inv,
                                      "all_inside_P_AB": inside,
                                      "P_AB_vertices_realized": len(V_AB & pts),
                                      "seconds": round(time.time() - t1, 1)}
    res["circuits"] = per
    res["P_AB_vertices_realized_total"] = len(V_AB & allpts)
    res["P_AB_vertices_total"] = len(V_AB)

    # оболочка схем: вершины A≼B-части, затем P_TS^circ
    pts = sorted(allpts)
    swap = B.GENS["swap"]
    V_circ_AB = [p for p in pts]
    V_circ = sorted(set(V_circ_AB) | {P.act_point(swap, p) for p in V_circ_AB})
    hull = P.affine_hull(V_circ)
    proj = P.Projector(hull)
    dim = B.D - len(hull)
    _, ineq = P.facets_cdd(V_circ)
    _, ineq_lrs = P.facets_lrs(V_circ)
    facets = sorted({P.projected(c, c0, proj) for c, c0 in ineq})
    agree = set(facets) == {P.projected(c, c0, proj) for c, c0 in ineq_lrs}
    G = [g for g in P.group_closure(list(B.GENS.values()))]
    autos = {k: P.is_automorphism(g, V_circ) for k, g in B.GENS.items()}
    Gp = P.group_closure([g for k, g in B.GENS.items() if k != "TR"])
    K, _ = B.branciard_K(proj)
    TR = B.GENS["TR"]
    classes = {}
    for f in facets:
        classes.setdefault(P.canonical(f[:-1], f[-1], proj, G), []).append(f)
    cls = []
    for rep, mem in sorted(classes.items(), key=lambda kv: (-len(kv[1]), kv[0])):
        f = mem[0]
        tr = P.projected(P.act_ineq(TR, f[:-1]), f[-1], proj)
        cls.append({"size": len(mem), "in_K": any(m in K for m in mem),
                    "K_readings": sorted({t for m in mem for t in K.get(m, ())}),
                    "directional": P.canonical(tr[:-1], tr[-1], proj, Gp) != P.canonical(f[:-1], f[-1], proj, Gp),
                    "nicest_form": nicest(list(rep))})
    known_max = {n: P.fr(P.max_over(c, V_circ)) for n, c in
                 (("GYNI", B.GYNI), ("LGYNI_fwd", B.LGYNI_F), ("LGYNI_bwd", B.LGYNI_B))}
    known_face_dim = {n: P.tight_rank(c, b, V_circ) for n, c, b in
                      (("GYNI", B.GYNI, F(1, 2)), ("LGYNI_fwd", B.LGYNI_F, F(3, 4)),
                       ("LGYNI_bwd", B.LGYNI_B, F(3, 4)))}
    res["P_TS_circ"] = {
        "points_AB": len(V_circ_AB), "points_union": len(V_circ), "affine_dim": dim,
        "hull_same_as_Def_II": dim == 9,
        "facets": len(facets), "cdd_equals_lrs": agree,
        "generators_automorphisms": autos,
        "classes_G": len(cls), "new_classes": sum(not c["in_K"] for c in cls),
        "new_directional": sum((not c["in_K"]) and c["directional"] for c in cls),
        "known_max": known_max, "known_face_dim(facet = dim-1)": known_face_dim,
        "classes": cls,
    }
    # ------------------------------------------------------------------------------
    # 3. Точное замыкание классических TS-схем A≼B при любых размерностях.
    # Распределение схемы = Σ μ(tA,tB) (1/4) [a = tA(x)] [y = tB(b)], где μ — доля ячеек (o, anc)
    # с типом Алисы tA = (h(0,o), h(1,o)) и типом Боба tB = (g(0,i_B), g(1,i_B)), i_B = ch(o,anc).
    # Сбалансированность h и g: E|tA| = 1, E|tB| = 1. Обратно, любая рациональная μ из M
    # реализуется при dA = dB = N (N μ целые), i_B = o. Замыкание = образ многогранника M.
    types = list(itertools.product(range(2), repeat=2))
    pairs = list(itertools.product(types, types))
    M_eqs = [([F(1)] * 16, F(1)),
             ([F(sum(tA)) for tA, _ in pairs], F(1)),
             ([F(sum(tB)) for _, tB in pairs], F(1))]
    M_pos = [([F(-1) if j == i else F(0) for j in range(16)], F(0)) for i in range(16)]
    M_vert = P.vertices_cdd(M_eqs, M_pos)

    def image(mu):
        p = [F(0)] * B.D
        for m, (tA, tB) in zip(mu, pairs):
            if m:
                for x, b in itertools.product(range(2), range(2)):
                    p[B.SC.idx[(tA[x], b, x, tB[b])]] += m / 4
        return tuple(p)

    img = sorted({image(m) for m in M_vert})
    ext_cl = extreme_points(img)
    # все точки усечённого перебора лежат в замыкании (LP через фасеты замыкания)
    _, h_cl_ab = P.facets_cdd(ext_cl)
    hull_ab_cl = P.affine_hull(ext_cl)
    in_cl = lambda p: (all(sum(c * q for c, q in zip(cv, p)) <= c0 for cv, c0 in h_cl_ab)  # noqa: E731
                       and all(sum(e * q for e, q in zip(ev, p)) == e0 for ev, e0 in hull_ab_cl))
    trunc_inside = all(in_cl(p) for p in allpts)
    trunc_ext = set(extreme_points(sorted(allpts)))
    V_cl = sorted(set(ext_cl) | {P.act_point(swap, p) for p in ext_cl})
    V_cl = extreme_points(V_cl)
    hull_cl = P.affine_hull(V_cl)
    proj_cl = P.Projector(hull_cl)
    dim_cl = B.D - len(hull_cl)
    _, ineq_cl = P.facets_cdd(V_cl)
    _, ineq_cl_lrs = P.facets_lrs(V_cl)
    fac_cl = sorted({P.projected(c, c0, proj_cl) for c, c0 in ineq_cl})
    agree_cl = set(fac_cl) == {P.projected(c, c0, proj_cl) for c, c0 in ineq_cl_lrs}
    autos_cl = {k: P.is_automorphism(g, V_cl) for k, g in B.GENS.items()}
    valid_cl = all(P.max_over(f[:-1], V_cl) == f[-1] for f in fac_cl)
    isfac_cl = all(P.tight_rank(f[:-1], f[-1], V_cl) == dim_cl - 1 for f in fac_cl)
    K_cl, _ = B.branciard_K(proj_cl)
    classes_cl = {}
    for f in fac_cl:
        classes_cl.setdefault(P.canonical(f[:-1], f[-1], proj_cl, G), []).append(f)
    cls_cl = []
    for rep, mem in sorted(classes_cl.items(), key=lambda kv: (-len(kv[1]), kv[0])):
        f = mem[0]
        tr = P.projected(P.act_ineq(TR, f[:-1]), f[-1], proj_cl)
        cls_cl.append({"size": len(mem), "in_K": any(m in K_cl for m in mem),
                       "K_readings": sorted({t for m in mem for t in K_cl.get(m, ())}),
                       "directional": P.canonical(tr[:-1], tr[-1], proj_cl, Gp)
                       != P.canonical(f[:-1], f[-1], proj_cl, Gp),
                       "nicest_form": nicest(list(rep))})
    res["classical_closure"] = {
        "M_vertices": len(M_vert), "AB_extreme_points": len(ext_cl),
        "AB_extreme_points_realized_by_truncated_search": len(set(ext_cl) & trunc_ext),
        "truncated_points_inside_closure": trunc_inside,
        "AB_closure_inside_Def_II_P_AB": all(B.satisfies(p, E_AB) and min(p) >= 0 for p in ext_cl),
        "Def_II_P_AB_vertices_in_closure": sum(in_cl(v) for v in V_AB),
        "TS_vertices": len(V_cl), "affine_dim": dim_cl, "facets": len(fac_cl),
        "cdd_equals_lrs": agree_cl, "all_valid": valid_cl, "all_are_facets": isfac_cl,
        "generators_automorphisms": autos_cl,
        "known_max": {n: P.fr(P.max_over(c, V_cl)) for n, c in
                      (("GYNI", B.GYNI), ("LGYNI_fwd", B.LGYNI_F), ("LGYNI_bwd", B.LGYNI_B))},
        "known_face_dim(facet = dim-1)": {n: P.tight_rank(c, b, V_cl) for n, c, b in
                                         (("GYNI", B.GYNI, F(1, 2)), ("LGYNI_fwd", B.LGYNI_F, F(3, 4)),
                                          ("LGYNI_bwd", B.LGYNI_B, F(3, 4)))},
        "classes_G": len(cls_cl), "new_classes": sum(not c["in_K"] for c in cls_cl),
        "new_directional": sum((not c["in_K"]) and c["directional"] for c in cls_cl),
        "classes": cls_cl,
    }
    res["seconds_total"] = round(time.time() - t0, 1)
    with open(os.path.join(P.ROOT, "results", "json", "stage_b_explore.json"), "w") as fh:
        json.dump(res, fh, ensure_ascii=False, indent=1)
    brief = dict(res)
    brief["P_TS_circ"] = {k: v for k, v in res["P_TS_circ"].items() if k != "classes"}
    brief["classical_closure"] = {k: v for k, v in res["classical_closure"].items() if k != "classes"}
    brief["closure_classes"] = [{k: c[k] for k in ("size", "in_K", "directional")} for c in res["classical_closure"]["classes"]]
    brief["class_summary"] = [{k: c[k] for k in ("size", "in_K", "K_readings", "directional")}
                              for c in cls]
    print(json.dumps(brief, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()

"""
Stage A — ворота: калибровка на временно-прямом причинном многограннике Branciard et al.

A.1  прогон causal_polytope_calib.py как есть + точное (GMP) воспроизведение его чисел;
A.2  сверка с Branciard et al. (arXiv:1508.01704): 48 фасет = 16 тривиальных + 32
     нетривиальных, 3 семейства (цитаты в SOURCES.md);
A.3  lrs против pycddlib (cdd.gmp): совпадение множеств фасет после приведения;
A.4  калибровка канонизатора: на известном ответе (3 класса) + контрольные провалы.

Результат: results/json/stage_a.json
"""
import itertools
import json
import os
import re
import subprocess
import sys
import time
from fractions import Fraction

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import polytope as P  # noqa: E402

ROOT = P.ROOT
sys.path.insert(0, ROOT)
import causal_polytope_calib as calib  # noqa: E402

PY = sys.executable

# Координаты калибровочного скрипта: (x, y, a, b), x,y — выходы, a,b — входы.
SC = P.Scenario(calib.COORD)


def gen(f):
    return SC.perm_from_map(lambda t: f(*t))


# Группа переименований Branciard et al.: «relabelings of inputs and outputs»
# (выход может переворачиваться в зависимости от своего входа: a ⊕ α1 x ⊕ α0 в их записи)
# плюс обмен сторон.
BRANCIARD_GENS = {
    "flip_in_A":   gen(lambda x, y, a, b: (x, y, 1 - a, b)),
    "flip_in_B":   gen(lambda x, y, a, b: (x, y, a, 1 - b)),
    "flip_out_A":  gen(lambda x, y, a, b: (1 - x, y, a, b)),
    "flip_out_B":  gen(lambda x, y, a, b: (x, 1 - y, a, b)),
    "cflip_out_A": gen(lambda x, y, a, b: (x ^ a, y, a, b)),
    "cflip_out_B": gen(lambda x, y, a, b: (x, y ^ b, a, b)),
    "swap":        gen(lambda x, y, a, b: (y, x, b, a)),
}


def functional(win, scale=1):
    return [Fraction(scale) if win(*c) else Fraction(0) for c in calib.COORD]


def main():
    out = {"stage": "A", "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S")}

    # ---------------------------------------------------------------- A.1
    t0 = time.time()
    run = subprocess.run([PY, os.path.join(ROOT, "causal_polytope_calib.py")],
                         capture_output=True, text=True, check=True)
    txt = run.stdout
    grab = lambda pat: re.search(pat, txt).group(1)  # noqa: E731
    a1 = {
        "script_stdout": txt,
        "vertices": int(grab(r"вершин:\s*(\d+)")),
        "equalities": int(grab(r"равенств \(нормировка\):\s*(\d+)")),
        "raw_nontrivial": int(grab(r"нетривиальных фасет:\s*(\d+)")),
        "gyni": grab(r"GYNI  причинный максимум:\s*(\S+)"),
        "lgyni": grab(r"LGYNI причинный максимум:\s*(\S+)"),
        "note_backend": "causal_polytope_calib.py использует `import cdd`, в pycddlib 3.x это "
                        "float-бэкенд (Fraction -> float). Ниже те же числа воспроизведены в "
                        "точной арифметике через cdd.gmp.",
    }
    V = [tuple(Fraction(x) for x in v) for v in calib.causal_vertices()]
    eqs, ineqs = P.facets_cdd(V)
    # фильтр «тривиальности» ровно как в калибровочном скрипте
    raw_nontriv = [(c, c0) for c, c0 in ineqs
                   if not (c0 == 0 and sorted(x for x in c if x != 0) == [1])]
    a1["exact"] = {"vertices": len(V), "equalities": len(eqs), "inequalities_total": len(ineqs),
                   "raw_nontrivial_script_filter": len(raw_nontriv)}
    gyni = functional(lambda x, y, a, b: x == b and y == a, Fraction(1, 4))
    lgyni = functional(lambda x, y, a, b: (a * (x ^ b) == 0) and (b * (y ^ a) == 0), Fraction(1, 4))
    a1["exact"]["gyni_max"] = P.fr(P.max_over(gyni, V))
    a1["exact"]["lgyni_max"] = P.fr(P.max_over(lgyni, V))
    a1["pass"] = (a1["vertices"] == 112 and a1["equalities"] == 4 and a1["gyni"] == "1/2"
                  and a1["lgyni"] == "3/4" and len(V) == 112 and len(eqs) == 4
                  and a1["exact"]["gyni_max"] == "1/2" and a1["exact"]["lgyni_max"] == "3/4")
    out["A1"] = a1

    # ---------------------------------------------------------------- проекция, тривиальные
    hull = P.affine_hull(V)
    proj = P.Projector(hull)
    pos = {P.projected([Fraction(-1) if j == i else Fraction(0) for j in range(SC.D)], 0, proj)
           for i in range(SC.D)}
    cdd_proj = [P.projected(c, c0, proj) for c, c0 in ineqs]
    cdd_set = set(cdd_proj)
    a1["exact"]["distinct_after_projection"] = len(cdd_set)
    trivial = [f for f in cdd_proj if f in pos]
    nontrivial = [f for f in cdd_proj if f not in pos]
    disguised = len(raw_nontriv) - len(nontrivial)
    # разбор «36» из float-прогона калибровочного скрипта: те же строки, спроецированные
    n_eq_float, raw36 = calib.facets(calib.causal_vertices())
    raw36_proj = [P.projected([Fraction(x) for x in c], Fraction(c0), proj) for c, c0 in raw36]
    a1["float_raw36_decomposition"] = {
        "raw_rows": len(raw36),
        "positivity_in_disguise": sum(f in pos for f in raw36_proj),
        "nontrivial": sum(f not in pos for f in raw36_proj),
        "all_rows_among_exact_facets": all(f in cdd_set for f in raw36_proj),
        "literal_positivity_rows_dropped_by_script": len(ineqs) - len(raw36),
    }

    # фасетность: каждая строка — действительно фасета (насыщающие вершины ранга dim-1)
    dim = P.rank([[1] + list(v) for v in V]) - 1
    facet_check = all(P.tight_rank(f[:-1], f[-1], V) == dim - 1 for f in cdd_proj)
    valid_check = all(P.max_over(f[:-1], V) == f[-1] for f in cdd_proj)

    # ---------------------------------------------------------------- A.3 lrs vs cdd
    t1 = time.time()
    leqs, lineqs = P.facets_lrs(V)
    lrs_time = time.time() - t1
    lrs_set = {P.projected(c, c0, proj) for c, c0 in lineqs}
    raw_cdd = {P.primitive(c, c0) for c, c0 in ineqs}
    raw_lrs = {P.primitive(c, c0) for c, c0 in lineqs}
    # контроль, что сравнение может провалиться: портим одну фасету lrs
    spoiled = set(lrs_set)
    victim = sorted(spoiled)[0]
    spoiled.remove(victim)
    spoiled.add(victim[:-1] + (victim[-1] + 1,))
    a3 = {
        "cdd_count": len(ineqs), "lrs_count": len(lineqs),
        "cdd_equalities": len(eqs), "lrs_equalities": len(leqs),
        "lrs_equalities_span_same_hull": P.rank([e + [e0] for e, e0 in leqs]) == len(leqs)
        and P.rank([list(e) + [e0] for e, e0 in leqs] + [list(e) + [e0] for e, e0 in hull]) == len(hull),
        "raw_sets_equal_before_projection": raw_cdd == raw_lrs,
        "sets_equal_after_projection": cdd_set == lrs_set,
        "negative_control_spoiled_set_detected": spoiled != cdd_set,
        "lrs_seconds": round(lrs_time, 3),
    }
    a3["pass"] = (a3["sets_equal_after_projection"] and a3["negative_control_spoiled_set_detected"]
                  and a3["lrs_equalities_span_same_hull"] and len(ineqs) == len(lineqs))
    out["A3"] = a3

    # ---------------------------------------------------------------- A.2 / A.4
    group = P.group_closure(list(BRANCIARD_GENS.values()))
    autos = {k: P.is_automorphism(g, V) for k, g in BRANCIARD_GENS.items()}
    classes = {}
    for f in cdd_proj:
        classes.setdefault(P.canonical(f[:-1], f[-1], proj, group), []).append(f)
    sizes = sorted(len(v) for v in classes.values())
    gy_can = P.canonical(gyni, Fraction(1, 2), proj, group)
    lg_can = P.canonical(lgyni, Fraction(3, 4), proj, group)
    pos_can = P.canonical([Fraction(-1)] + [Fraction(0)] * (SC.D - 1), 0, proj, group)
    # контроль 1: без проекции (сырые cdd-строки) — счёт классов артефактен
    classes_noproj = {}
    for c, c0 in ineqs:
        best = min(P.primitive(P.act_ineq(g, c), c0)[0] + (P.primitive(P.act_ineq(g, c), c0)[1],)
                   for g in group)
        classes_noproj.setdefault(best, 0)
        classes_noproj[best] += 1
    # контроль 2: тривиальная группа — классов должно быть 48
    classes_trivgroup = {P.canonical(f[:-1], f[-1], proj, [tuple(range(SC.D))]) for f in cdd_proj}
    # контроль 3: группа без условных переворотов выхода — 16 GYNI-фасет распадаются
    weak = P.group_closure([g for k, g in BRANCIARD_GENS.items() if not k.startswith("cflip")])
    classes_weak = {P.canonical(f[:-1], f[-1], proj, weak) for f in cdd_proj}
    a2 = {
        "branciard_reported": {"facets": 48, "trivial": 16, "nontrivial": 32, "families": 3,
                               "gyni_type": 16, "lgyni_type": 16, "source": "arXiv:1508.01704, "
                               "Sec. III A and App. A (цитаты в SOURCES.md)"},
        "ours": {"facets_total": len(ineqs), "trivial_after_projection": len(trivial),
                 "nontrivial_after_projection": len(nontrivial),
                 "raw_nontrivial_by_script_filter": len(raw_nontriv),
                 "disguised_positivity_in_raw_36": disguised,
                 "polytope_dim": dim, "every_row_is_facet": facet_check,
                 "every_row_tight_on_vertices": valid_check},
    }
    a2["pass"] = (len(ineqs) == 48 and len(trivial) == 16 and len(nontrivial) == 32
                  and facet_check and valid_check)
    a4 = {
        "group_order": len(group),
        "generators_are_automorphisms": autos,
        "classes": len(classes), "class_sizes": sizes,
        "gyni_class_size": len(classes.get(gy_can, [])),
        "lgyni_class_size": len(classes.get(lg_can, [])),
        "positivity_class_size": len(classes.get(pos_can, [])),
        "control_no_projection_classes": len(classes_noproj),
        "control_trivial_group_classes": len(classes_trivgroup),
        "control_group_without_conditional_flips_classes": len(classes_weak),
    }
    a4["pass"] = (all(autos.values()) and len(classes) == 3 and sizes == [16, 16, 16]
                  and a4["gyni_class_size"] == 16 and a4["lgyni_class_size"] == 16
                  and a4["positivity_class_size"] == 16
                  and a4["control_trivial_group_classes"] == 48
                  and a4["control_no_projection_classes"] != 3)
    out["A2"], out["A4"] = a2, a4
    out["gate_pass"] = bool(a1["pass"] and a3["pass"] and a4["pass"])
    out["gate_A2"] = "подтверждено цитатой" if a2["pass"] else "РАСХОЖДЕНИЕ"
    out["seconds"] = round(time.time() - t0, 2)

    os.makedirs(os.path.join(ROOT, "results", "json"), exist_ok=True)
    with open(os.path.join(ROOT, "results", "json", "stage_a.json"), "w") as fh:
        json.dump(out, fh, ensure_ascii=False, indent=1)
    summary = {k: out[k].get("pass") for k in ("A1", "A2", "A3", "A4")}
    print(json.dumps({"gate_pass": out["gate_pass"], **summary, "A2_ours": a2["ours"],
                      "A3": a3, "A4": a4}, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()

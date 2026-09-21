"""
Антивакуумный тест точности (PREREGISTRATION_B2.md §0).

Треугольник с вершиной (1/3, 1): V -> H -> V. Точный путь (cdd.gmp, lrs) обязан вернуть
координату ровно Fraction(1, 3). Контроль: тот же путь через float-модуль `cdd`
(pycddlib 3.x) обязан тест провалить. Результат: results/json/precision.json.
"""
import json
import os
import sys
from fractions import Fraction

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import polytope as P  # noqa: E402

import cdd as cddf  # float-бэкенд pycddlib 3.x

THIRD = Fraction(1, 3)
PTS = [(Fraction(0), Fraction(0)), (Fraction(1), Fraction(0)), (THIRD, Fraction(1))]


def check(verts):
    """Проходит, если среди вершин есть точка с координатой ровно Fraction(1,3)."""
    return any(isinstance(v[0], Fraction) and v[0] == THIRD and v[1] == 1 for v in verts)


def roundtrip_gmp():
    eqs, ineqs = P.facets_cdd(PTS)
    return P.vertices_cdd(eqs, ineqs)


def roundtrip_lrs():
    eqs, ineqs = P.facets_lrs(PTS)
    return P.vertices_lrs(eqs, ineqs)


def roundtrip_float():
    mat = cddf.matrix_from_array([[1] + [x for x in p] for p in PTS], rep_type=cddf.RepType.GENERATOR)
    H = cddf.copy_inequalities(cddf.polyhedron_from_matrix(mat))
    mat2 = cddf.matrix_from_array(H.array, rep_type=cddf.RepType.INEQUALITY, lin_set=H.lin_set)
    G = cddf.copy_generators(cddf.polyhedron_from_matrix(mat2))
    # честная попытка: привести к Fraction тем же способом, каким это делал бы исполнитель
    return [tuple(Fraction(x) for x in row[1:]) for row in G.array]


def main():
    res = {}
    for name, fn in (("cdd_gmp", roundtrip_gmp), ("lrs", roundtrip_lrs), ("float_cdd_control", roundtrip_float)):
        v = fn()
        res[name] = {"pass": check(v), "vertices": [[str(x) for x in p] for p in v]}
    res["gate_pass"] = res["cdd_gmp"]["pass"] and res["lrs"]["pass"] and not res["float_cdd_control"]["pass"]
    with open(os.path.join(P.ROOT, "results", "json", "precision.json"), "w") as fh:
        json.dump(res, fh, ensure_ascii=False, indent=1)
    print(json.dumps(res, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()

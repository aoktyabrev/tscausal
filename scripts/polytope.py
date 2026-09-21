"""
Общее ядро TSCAUSAL: точная арифметика, фасеты через cdd.gmp и lrs, канонизация.

Соглашения.
  Точка многогранника — вектор p длины D (координаты перечислены в COORD сценария).
  Неравенство — пара (c, c0), смысл: c . p <= c0.
  Равенство аффинной оболочки — пара (e, e0), смысл: e . p == e0.

Канонизация неравенства (c, c0) относительно аффинной оболочки {E p = e0}:
  1. проекция c на ортогональное дополнение rowspace(E): c' = c - E^T (E E^T)^+ E c,
     c0' = c0 - e0^T (E E^T)^+ E c  (то же число вычитается из обеих частей, так что
     на аффинной оболочке неравенство не меняется);
  2. приведение (c', c0') к примитивному целому вектору (общий знаменатель, деление на НОД);
  3. лексикографический минимум по орбите группы перестановок координат.
Шаг 1 корректен для группы, потому что перестановки координат ортогональны и
сохраняют аффинную оболочку (это проверяется отдельно, см. is_automorphism).

ВАЖНО про pycddlib 3.x: `import cdd` — это float-бэкенд (Fraction молча превращается
в float). Точная рациональная арифметика — только `cdd.gmp`. Здесь используется cdd.gmp.
"""
import os
import shutil
import subprocess
import tempfile
from fractions import Fraction
from math import gcd

import cdd.gmp as cddg

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)


def find_lrs():
    for cand in (os.path.join(ROOT, ".env", "bin", "lrs"), shutil.which("lrs")):
        if cand and os.path.exists(cand):
            return cand
    raise RuntimeError("lrs не найден (ожидается .env/bin/lrs или lrs в PATH)")


# ----------------------------------------------------------------- линейная алгебра

def rref(rows):
    """Приведённый ступенчатый вид над Q. Возвращает (строки, опорные столбцы)."""
    M = [[Fraction(x) for x in r] for r in rows]
    piv, r = [], 0
    ncol = len(M[0]) if M else 0
    for col in range(ncol):
        k = next((i for i in range(r, len(M)) if M[i][col] != 0), None)
        if k is None:
            continue
        M[r], M[k] = M[k], M[r]
        inv = 1 / M[r][col]
        M[r] = [x * inv for x in M[r]]
        for i in range(len(M)):
            if i != r and M[i][col] != 0:
                f = M[i][col]
                M[i] = [a - f * b for a, b in zip(M[i], M[r])]
        piv.append(col)
        r += 1
    return M[:r], piv


def rank(rows):
    return len(rref(rows)[0]) if rows else 0


def affine_hull(points):
    """Равенства аффинной оболочки конечного множества точек: список (e, e0), независимых.
    Считается как нуль-пространство матрицы [1 | p]: вектор (-e0, e) с -e0 + e.p = 0."""
    D = len(points[0])
    R, piv = rref([[1] + list(p) for p in points])
    free = [j for j in range(D + 1) if j not in piv]
    eqs = []
    for f in free:
        v = [Fraction(0)] * (D + 1)
        v[f] = Fraction(1)
        for i, pc in enumerate(piv):
            v[pc] = -R[i][f]
        eqs.append((v[1:], -v[0]))                     # e.p = e0
    return eqs


def solve_sym(A, b):
    """Решение A z = b для невырожденной квадратной A над Q."""
    n = len(A)
    R, piv = rref([list(A[i]) + [b[i]] for i in range(n)])
    assert piv == list(range(n)), "вырожденная матрица Грама равенств"
    return [R[i][n] for i in range(n)]


class Projector:
    """Ортогональная проекция нормалей на направление аффинной оболочки."""

    def __init__(self, eqs):
        self.E = [[Fraction(x) for x in e] for e, _ in eqs]
        self.e0 = [Fraction(x) for _, x in eqs]
        m = len(self.E)
        self.G = [[sum(a * b for a, b in zip(self.E[i], self.E[j])) for j in range(m)]
                  for i in range(m)]

    def __call__(self, c, c0):
        c = [Fraction(x) for x in c]
        if not self.E:
            return c, Fraction(c0)
        Ec = [sum(a * b for a, b in zip(row, c)) for row in self.E]
        lam = solve_sym(self.G, Ec)
        cp = [ci - sum(l * row[j] for l, row in zip(lam, self.E)) for j, ci in enumerate(c)]
        c0p = Fraction(c0) - sum(l * e for l, e in zip(lam, self.e0))
        return cp, c0p


def primitive(c, c0):
    """(c, c0) -> примитивный целый вектор того же направления (знак сохраняется)."""
    vals = [Fraction(x) for x in list(c) + [c0]]
    L = 1
    for v in vals:
        L = L * v.denominator // gcd(L, v.denominator)
    ints = [int(v * L) for v in vals]
    g = 0
    for v in ints:
        g = gcd(g, abs(v))
    g = g or 1
    ints = [v // g for v in ints]
    return tuple(ints[:-1]), ints[-1]


# ----------------------------------------------------------------- перечисление фасет

def _parse_hrows(rows, lin):
    """Строки b + A p >= 0 -> (равенства, неравенства) в форме (c, c0): c.p <= c0."""
    eqs, ineqs = [], []
    for i, row in enumerate(rows):
        row = [Fraction(x) for x in row]
        c, c0 = [-x for x in row[1:]], row[0]
        (eqs if i in lin else ineqs).append((c, c0))
    return eqs, ineqs


def facets_cdd(points):
    """Точная (GMP) фасетная энумерация через pycddlib 3.x."""
    mat = cddg.matrix_from_array([[Fraction(1)] + [Fraction(x) for x in p] for p in points],
                                 rep_type=cddg.RepType.GENERATOR)
    poly = cddg.polyhedron_from_matrix(mat)
    H = cddg.copy_inequalities(poly)
    return _parse_hrows(H.array, set(H.lin_set))


def vertices_cdd(eqs, ineqs):
    """Точная вершинная энумерация H-многогранника {c.p <= c0} ∩ {e.p = e0} (cdd.gmp)."""
    rows, lin = [], []
    for e, e0 in eqs:
        lin.append(len(rows))
        rows.append([Fraction(e0)] + [-Fraction(x) for x in e])
    for c, c0 in ineqs:
        rows.append([Fraction(c0)] + [-Fraction(x) for x in c])
    mat = cddg.matrix_from_array(rows, rep_type=cddg.RepType.INEQUALITY, lin_set=lin)
    poly = cddg.polyhedron_from_matrix(mat)
    G = cddg.copy_generators(poly)
    out = []
    for row in G.array:
        assert Fraction(row[0]) == 1, "неограниченный многогранник (луч) — неожиданно"
        out.append(tuple(Fraction(x) for x in row[1:]))
    assert not G.lin_set, "у многогранника есть прямые — неожиданно"
    return out


def _fmt(x):
    x = Fraction(x)
    return str(x.numerator) if x.denominator == 1 else f"{x.numerator}/{x.denominator}"


def facets_lrs(points, workdir=None):
    """Фасетная энумерация через lrs (точная рациональная арифметика)."""
    lrs = find_lrs()
    D = len(points[0])
    with tempfile.TemporaryDirectory(dir=workdir) as td:
        f = os.path.join(td, "in.ext")
        with open(f, "w") as fh:
            fh.write("tscausal\nV-representation\nbegin\n")
            fh.write(f"{len(points)} {D + 1} rational\n")
            for p in points:
                fh.write("1 " + " ".join(_fmt(x) for x in p) + "\n")
            fh.write("end\n")
        out = subprocess.run([lrs, f], capture_output=True, text=True, check=True).stdout
    lin, rows = set(), []
    for s in _last_block(out):
        if s.startswith("linearity"):
            parts = s.split()
            lin = {int(t) - 1 for t in parts[2:2 + int(parts[1])]}
        else:
            rows.append([Fraction(t) for t in s.split()])
    return _parse_hrows(rows, lin)


def vertices_lrs(eqs, ineqs, workdir=None):
    """Точная вершинная энумерация H-многогранника {c.p <= c0} ∩ {e.p = e0} через lrs."""
    lrs = find_lrs()
    rows, lin = [], []
    for e, e0 in eqs:
        lin.append(len(rows) + 1)
        rows.append([Fraction(e0)] + [-Fraction(x) for x in e])
    for c, c0 in ineqs:
        rows.append([Fraction(c0)] + [-Fraction(x) for x in c])
    with tempfile.TemporaryDirectory(dir=workdir) as td:
        f = os.path.join(td, "in.ine")
        with open(f, "w") as fh:
            fh.write("tscausal\nH-representation\n")
            if lin:
                fh.write(f"linearity {len(lin)} " + " ".join(map(str, lin)) + "\n")
            fh.write(f"begin\n{len(rows)} {len(rows[0])} rational\n")
            for r in rows:
                fh.write(" ".join(_fmt(x) for x in r) + "\n")
            fh.write("end\n")
        out = subprocess.run([lrs, f], capture_output=True, text=True, check=True).stdout
    verts = []
    for s in _last_block(out):
        if s.startswith("linearity"):
            raise AssertionError("у многогранника есть прямые — неожиданно")
        t = [Fraction(x) for x in s.split()]
        assert t[0] == 1, "луч в выводе lrs — неожиданно"
        verts.append(tuple(t[1:]))
    return verts


def _last_block(out):
    """Строки последнего полного блока begin…end вывода lrs. При переполнении lrs (hybrid
    arithmetic) перезапускается с большей разрядностью и печатает заголовок/блок заново;
    берём последний блок. Нечисловая строка внутри блока — ошибка, а не пропуск."""
    blocks, cur, lin = [], None, None
    for line in out.splitlines():
        s = line.strip()
        if s.startswith("linearity"):
            lin = s
        elif s == "begin":
            cur = []
        elif s == "end" and cur is not None:
            blocks.append(([lin] if lin else []) + cur)
            cur, lin = None, None
        elif cur is not None and s and not s.startswith("*****"):
            if s.startswith("lrs:") or s.startswith("*"):
                cur = None          # перезапуск внутри блока — блок недействителен
                continue
            cur.append(s)
    assert blocks, "lrs не выдал ни одного полного блока"
    return blocks[-1]


# ----------------------------------------------------------------- группа и канонизация

class Scenario:
    """Координаты = список кортежей значений переменных; группа действует на кортежах."""

    def __init__(self, coords):
        self.coords = list(coords)
        self.idx = {c: i for i, c in enumerate(self.coords)}
        self.D = len(self.coords)

    def perm_from_map(self, f):
        """Отображение кортежей t -> f(t) как перестановка индексов; проверка биективности."""
        perm = [self.idx[f(c)] for c in self.coords]
        assert sorted(perm) == list(range(self.D)), "отображение не биективно на координатах"
        return tuple(perm)


def act_point(perm, p):
    """(g p)[perm[i]] = p[i] — перенос массы с кортежа t на g(t)."""
    q = [None] * len(p)
    for i, j in enumerate(perm):
        q[j] = p[i]
    return tuple(q)


def act_ineq(perm, c):
    """Нормаль, для которой (g c).(g p) = c.p."""
    return act_point(perm, c)


def compose(p1, p2):
    """Сначала p2, потом p1."""
    return tuple(p1[p2[i]] for i in range(len(p1)))


def group_closure(gens):
    D = len(gens[0])
    ident = tuple(range(D))
    G, frontier = {ident}, [ident]
    while frontier:
        new = []
        for g in frontier:
            for h in gens:
                k = compose(h, g)
                if k not in G:
                    G.add(k)
                    new.append(k)
        frontier = new
    return sorted(G)


def is_automorphism(perm, vertex_set):
    return {act_point(perm, v) for v in vertex_set} == set(vertex_set)


def canonical(c, c0, proj, group):
    """Канонический представитель класса неравенства: lexmin по группе после проекции."""
    cp, c0p = proj(c, c0)
    best = None
    for g in group:
        rep = primitive(act_ineq(g, cp), c0p)
        key = rep[0] + (rep[1],)
        if best is None or key < best:
            best = key
    return best


def projected(c, c0, proj):
    cp, c0p = proj(c, c0)
    r = primitive(cp, c0p)
    return r[0] + (r[1],)


def max_over(c, vertices):
    return max(sum(Fraction(a) * Fraction(b) for a, b in zip(c, v)) for v in vertices)


def tight_rank(c, c0, vertices):
    """Аффинная размерность множества вершин, насыщающих c.p <= c0 (для проверки фасетности)."""
    T = [v for v in vertices if sum(Fraction(a) * Fraction(b) for a, b in zip(c, v)) == c0]
    if not T:
        return -1
    return rank([[1] + list(v) for v in T]) - 1


def fr(x):
    """Fraction -> строка для JSON."""
    return _fmt(x)


def extreme_points(pts):
    """Крайние точки конечного множества (удаление избыточных образующих, cdd.gmp)."""
    mat = cddg.matrix_from_array([[Fraction(1)] + list(p) for p in pts],
                                 rep_type=cddg.RepType.GENERATOR)
    cddg.matrix_canonicalize(mat)
    return sorted(tuple(Fraction(x) for x in row[1:]) for row in mat.array)


def dot(c, p):
    return sum(Fraction(a) * Fraction(b) for a, b in zip(c, p))


def in_H(p, eqs, ineqs):
    return all(dot(e, p) == e0 for e, e0 in eqs) and all(dot(c, p) <= c0 for c, c0 in ineqs)

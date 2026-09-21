"""
Калибровка причинного многогранника (временно-прямой случай, Branciard et al. 2015).

Сценарий: две стороны, у каждой бинарный вход (a, b) и бинарный выход (x, y).
Координаты — p(x,y|a,b), 16 штук. Вершины: детерминированные стратегии,
совместимые с A<B (x зависит только от a) или B<A (y зависит только от b).

Ворота калибровки (должны сойтись точно, в рациональной арифметике):
  GYNI  (x=b, y=a)                            причинный максимум = 1/2
  LGYNI (a(x⊕b)=0 и b(y⊕a)=0)                 причинный максимум = 3/4
  4 равенства (нормировка на каждую пару входов)

Стек: python3, pycddlib 3.x (API: matrix_from_array / polyhedron_from_matrix /
copy_inequalities), точные Fraction. Альтернатива для больших сценариев: lrs.
"""
import itertools
from fractions import Fraction
from math import gcd
import cdd

INPUTS = list(itertools.product([0, 1], repeat=2))                    # (a,b)
COORD = [(x, y, a, b) for (a, b) in INPUTS
         for (x, y) in itertools.product([0, 1], repeat=2)]
IDX = {c: i for i, c in enumerate(COORD)}
D = len(COORD)


def causal_vertices():
    """Детерминированные причинные стратегии обоих порядков."""
    V = set()
    for f in itertools.product([0, 1], repeat=2):          # A<B: x=f(a)
        for g in itertools.product([0, 1], repeat=4):      #      y=g(a,b)
            v = [0]*D
            for k, (a, b) in enumerate(INPUTS):
                v[IDX[(f[a], g[k], a, b)]] = 1
            V.add(tuple(v))
    for h in itertools.product([0, 1], repeat=2):          # B<A: y=h(b)
        for q in itertools.product([0, 1], repeat=4):      #      x=q(a,b)
            v = [0]*D
            for k, (a, b) in enumerate(INPUTS):
                v[IDX[(q[k], h[b], a, b)]] = 1
            V.add(tuple(v))
    return sorted(V)


def game_value(vertices, win):
    """Причинный максимум игры: доля выигрышей при равномерных входах."""
    f = [1 if win(*c) else 0 for c in COORD]
    return Fraction(max(sum(fi*vi for fi, vi in zip(f, v)) for v in vertices),
                    len(INPUTS))


def facets(vertices):
    """H-представление: (равенства, нетривиальные неравенства в целых коэф.)."""
    mat = cdd.matrix_from_array([[Fraction(1)] + [Fraction(c) for c in v]
                                 for v in vertices])
    mat.rep_type = cdd.RepType.GENERATOR
    ineq = cdd.copy_inequalities(cdd.polyhedron_from_matrix(mat))
    lin, out = set(ineq.lin_set), []
    for i, row in enumerate(ineq.array):
        if i in lin:
            continue
        row = [Fraction(c) for c in row]
        body, rhs = [-c for c in row[1:]], row[0]          # b + Ax >= 0 -> -Ax <= b
        nz = [c for c in body if c != 0]
        if rhs == 0 and len(nz) == 1 and nz[0] == -1:      # тривиальное p >= 0
            continue
        L = 1
        for c in body + [rhs]:
            L = L*c.denominator//gcd(L, c.denominator)
        body = [int(c*L) for c in body]
        rhs = int(rhs*L)
        g = 0
        for c in body + [rhs]:
            g = gcd(g, abs(c))
        g = g or 1
        out.append((tuple(c//g for c in body), rhs//g))
    return len(lin), out


if __name__ == "__main__":
    V = causal_vertices()
    print("вершин:", len(V))
    n_eq, nt = facets(V)
    print("равенств (нормировка):", n_eq, " нетривиальных фасет:", len(nt))
    gyni = game_value(V, lambda x, y, a, b: x == b and y == a)
    lgyni = game_value(V, lambda x, y, a, b:
                       (a*((x + b) % 2) == 0) and (b*((y + a) % 2) == 0))
    print("GYNI  причинный максимум:", gyni, "(ожидание 1/2)",
          "OK" if gyni == Fraction(1, 2) else "ПРОВАЛ")
    print("LGYNI причинный максимум:", lgyni, "(ожидание 3/4)",
          "OK" if lgyni == Fraction(3, 4) else "ПРОВАЛ")
    print("\nВНИМАНИЕ: сырые фасеты из cdd НЕ классифицированы. Из-за равенств"
          "\nнормировки одно и то же неравенство имеет много представлений —"
          "\nбез канонизации по модулю аффинной оболочки счёт «классов» является"
          "\nартефактом представления, а не результатом (см. Stage B в спеке).")

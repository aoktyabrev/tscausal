"""
Shared TSCAUSAL core: exact arithmetic, facets via cdd.gmp and lrs, canonicalisation.

Conventions.
  A point of the polytope is a vector p of length D (the coordinates are listed in the scenario's COORD).
  An inequality is a pair (c, c0), meaning: c . p <= c0.
  An affine-hull equality is a pair (e, e0), meaning: e . p == e0.

Canonicalisation of an inequality (c, c0) with respect to the affine hull {E p = e0}:
  1. projection of c onto the orthogonal complement of rowspace(E): c' = c - E^T (E E^T)^+ E c,
     c0' = c0 - e0^T (E E^T)^+ E c  (the same number is subtracted from both sides, so that
     on the affine hull the inequality does not change);
  2. reduction of (c', c0') to a primitive integer vector (common denominator, division by the GCD);
  3. lexicographic minimum over the orbit of the group of coordinate permutations.
Step 1 is correct for the group because coordinate permutations are orthogonal and
preserve the affine hull (this is checked separately, see is_automorphism).

IMPORTANT about pycddlib 3.x: `import cdd` is the float backend (a Fraction is silently turned
into a float). Exact rational arithmetic lives only in `cdd.gmp`. Here cdd.gmp is used.
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
    raise RuntimeError("lrs not found (expected .env/bin/lrs or lrs in PATH)")


# ----------------------------------------------------------------- linear algebra

def rref(rows):
    """Reduced row echelon form over Q. Returns (rows, pivot columns)."""
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
    """Affine-hull equalities of a finite set of points: a list of independent (e, e0).
    Computed as the null space of the matrix [1 | p]: the vector (-e0, e) with -e0 + e.p = 0."""
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
    """Solves A z = b for a non-singular square A over Q."""
    n = len(A)
    R, piv = rref([list(A[i]) + [b[i]] for i in range(n)])
    assert piv == list(range(n)), "singular Gram matrix of the equalities"
    return [R[i][n] for i in range(n)]


class Projector:
    """Orthogonal projection of normals onto the direction of the affine hull."""

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
    """(c, c0) -> a primitive integer vector of the same direction (the sign is preserved)."""
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


# ----------------------------------------------------------------- facet enumeration

def _parse_hrows(rows, lin):
    """Rows b + A p >= 0 -> (equalities, inequalities) in the form (c, c0): c.p <= c0."""
    eqs, ineqs = [], []
    for i, row in enumerate(rows):
        row = [Fraction(x) for x in row]
        c, c0 = [-x for x in row[1:]], row[0]
        (eqs if i in lin else ineqs).append((c, c0))
    return eqs, ineqs


def facets_cdd(points):
    """Exact (GMP) facet enumeration via pycddlib 3.x."""
    mat = cddg.matrix_from_array([[Fraction(1)] + [Fraction(x) for x in p] for p in points],
                                 rep_type=cddg.RepType.GENERATOR)
    poly = cddg.polyhedron_from_matrix(mat)
    H = cddg.copy_inequalities(poly)
    return _parse_hrows(H.array, set(H.lin_set))


def vertices_cdd(eqs, ineqs):
    """Exact vertex enumeration of the H-polytope {c.p <= c0} ∩ {e.p = e0} (cdd.gmp)."""
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
        assert Fraction(row[0]) == 1, "unbounded polyhedron (ray) — unexpected"
        out.append(tuple(Fraction(x) for x in row[1:]))
    assert not G.lin_set, "the polyhedron contains lines — unexpected"
    return out


def _fmt(x):
    x = Fraction(x)
    return str(x.numerator) if x.denominator == 1 else f"{x.numerator}/{x.denominator}"


def facets_lrs(points, workdir=None):
    """Facet enumeration via lrs (exact rational arithmetic)."""
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
    """Exact vertex enumeration of the H-polytope {c.p <= c0} ∩ {e.p = e0} via lrs."""
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
            raise AssertionError("the polyhedron contains lines — unexpected")
        t = [Fraction(x) for x in s.split()]
        assert t[0] == 1, "a ray in the lrs output — unexpected"
        verts.append(tuple(t[1:]))
    return verts


def _last_block(out):
    """Rows of the last complete begin…end block of the lrs output. On overflow lrs (hybrid
    arithmetic) restarts with a larger word size and prints the header/block again;
    we take the last block. A non-numeric line inside a block is an error, not something to skip."""
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
                cur = None          # a restart inside the block — the block is invalid
                continue
            cur.append(s)
    assert blocks, "lrs produced no complete block"
    return blocks[-1]


# ----------------------------------------------------------------- group and canonicalisation

class Scenario:
    """Coordinates = a list of tuples of variable values; the group acts on the tuples."""

    def __init__(self, coords):
        self.coords = list(coords)
        self.idx = {c: i for i, c in enumerate(self.coords)}
        self.D = len(self.coords)

    def perm_from_map(self, f):
        """The map of tuples t -> f(t) as a permutation of indices; bijectivity is checked."""
        perm = [self.idx[f(c)] for c in self.coords]
        assert sorted(perm) == list(range(self.D)), "the map is not a bijection on the coordinates"
        return tuple(perm)


def act_point(perm, p):
    """(g p)[perm[i]] = p[i] — transfer of mass from tuple t to g(t)."""
    q = [None] * len(p)
    for i, j in enumerate(perm):
        q[j] = p[i]
    return tuple(q)


def act_ineq(perm, c):
    """The normal for which (g c).(g p) = c.p."""
    return act_point(perm, c)


def compose(p1, p2):
    """First p2, then p1."""
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
    """Canonical representative of an inequality class: lexmin over the group after projection."""
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
    """Affine dimension of the set of vertices saturating c.p <= c0 (for the facet check)."""
    T = [v for v in vertices if sum(Fraction(a) * Fraction(b) for a, b in zip(c, v)) == c0]
    if not T:
        return -1
    return rank([[1] + list(v) for v in T]) - 1


def fr(x):
    """Fraction -> string for JSON."""
    return _fmt(x)


def extreme_points(pts):
    """Extreme points of a finite set (removal of redundant generators, cdd.gmp)."""
    mat = cddg.matrix_from_array([[Fraction(1)] + list(p) for p in pts],
                                 rep_type=cddg.RepType.GENERATOR)
    cddg.matrix_canonicalize(mat)
    return sorted(tuple(Fraction(x) for x in row[1:]) for row in mat.array)


def dot(c, p):
    return sum(Fraction(a) * Fraction(b) for a, b in zip(c, p))


def in_H(p, eqs, ineqs):
    return all(dot(e, p) == e0 for e, e0 in eqs) and all(dot(c, p) <= c0 for c, c0 in ineqs)

"""Читаемая форма фасеты: c ~ c + α(a,b) + β(x,y) (равенства D1 и нормировки), выбираем
неотрицательные целые веса с минимальным максимумом, затем минимальной суммой."""
import itertools
from fractions import Fraction

BITS = (0, 1)
COORD = list(itertools.product(BITS, repeat=4))


def nicest(f, span=10):
    c, c0 = [Fraction(v) for v in f[:-1]], Fraction(f[-1])
    best = None
    for b01, b10, b11 in itertools.product(range(-span, span + 1), repeat=3):
        beta = {(0, 0): 0, (0, 1): b01, (1, 0): b10, (1, 1): b11}
        w = {t: c[i] + beta[(t[2], t[3])] for i, t in enumerate(COORD)}
        alpha = {ab: -min(w[t] for t in COORD if t[:2] == ab) for ab in itertools.product(BITS, BITS)}
        w = {t: w[t] + alpha[t[:2]] for t in COORD}
        rhs = c0 + sum(beta.values()) / 4 + sum(alpha.values()) / 4
        key = (max(w.values()), sum(w.values()))
        if best is None or key < best[0]:
            best = (key, w, rhs)
    _, w, rhs = best
    return {"weights": {"".join(map(str, t)): int(w[t]) for t in COORD}, "rhs": str(rhs),
            "normalized_rhs(game value, weights/4)": str(rhs / 4) if max(w.values()) == 1 else None}

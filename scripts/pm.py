"""
Сведённая форма Stage D (вывод D8, PREREGISTRATION_D.md §2).

TS-процесс A≼B без селекции ≡ пара (σ, F) на C^d:
  σ_{a,x} ≥ 0,  Σ_x Tr σ_{a,x} = 1 (∀a),  Σ_a σ_{a,x} = 1/d (∀x);
  F_{b,y} ≥ 0,  Σ_y F_{b,y} = 1 (∀b),     Σ_b Tr F_{b,y} = d (∀y);
  p(a,b,x,y) = ¼ Tr[σ_{a,x}^T F_{b,y}].
Обратное отображение в TS-форму: W = тождественный канал A_O→B_I, M_{a,x} = 1⊗σ_{a,x}, M_{b,y} = F_{b,y}⊗1/d.
Белловская форма: A_{a|x} = d σ_{a,x}, p = ¼ ⟨φ_d| A_{a|x} ⊗ F_{b,y} |φ_d⟩.
Плюс NPA (уровень 1+AB и 2) для Белловского сценария со входами (x, b), выходами (a, y).
"""
import itertools

import cvxpy as cp
import numpy as np

import qproc as Q

KEYS = list(itertools.product((0, 1), repeat=4))       # (a, b, x, y)


def p_reduced(S, F):
    return {(a, b, x, y): 0.25 * np.trace(S[(a, x)].T @ F[(b, y)]).real for a, b, x, y in KEYS}


def check_reduced(S, F, d):
    r = 0.0
    for a in (0, 1):
        r = max(r, abs(sum(np.trace(S[(a, x)]).real for x in (0, 1)) - 1))
    for x in (0, 1):
        r = max(r, np.abs(S[(0, x)] + S[(1, x)] - np.eye(d) / d).max())
    for b in (0, 1):
        r = max(r, np.abs(F[(b, 0)] + F[(b, 1)] - np.eye(d)).max())
    for y in (0, 1):
        r = max(r, abs(sum(np.trace(F[(b, y)]).real for b in (0, 1)) - d))
    me = min(np.linalg.eigvalsh((m + m.conj().T) / 2).min() for m in list(S.values()) + list(F.values()))
    return r, me


def to_ts(S, F, d):
    """(σ, F) → (W, MA, MB) в TS-форме (тождественный канал A_O→B_I)."""
    Phi = np.zeros((d * d, d * d), complex)
    for i in range(d):
        for j in range(d):
            Phi[i * d + i, j * d + j] = 1
    W = np.kron(np.kron(np.eye(d), Phi), np.eye(d)) / d
    MA = {k: np.kron(np.eye(d), v) for k, v in S.items()}
    MB = {k: np.kron(v, np.eye(d) / d) for k, v in F.items()}
    return W, MA, MB


def from_ts_AB(W, MA, MB, d):
    """TS (одностороннее A→B) → (σ, F): σ = (1/d)Tr_{A_I} M_A; F^T = Tr_{A_I}Tr_B[W(1⊗M_B)]·(структура проверяется)."""
    n = d * d
    S = {k: Q.ptrace_AB(v, d, 0) / d for k, v in MA.items()}
    F, struct = {}, 0.0
    for k, MBk in MB.items():
        E = Q._eff_A(W, MBk, n)                      # Tr[W(M_A⊗M_B)] = Tr[M_A E]
        G = Q.ptrace_AB(E, d, 0)                     # E должно быть (1/d)·1⊗G
        struct = max(struct, np.abs(E - np.kron(np.eye(d), G) / d).max())
        F[k] = G.T                                   # p = ¼Tr[M_A E] = ¼Tr[σ G] = ¼Tr[σ^T G^T]
    return S, F, struct


def bell_form(S, F, d):
    phi = np.zeros(d * d, complex)
    for i in range(d):
        phi[i * d + i] = 1 / np.sqrt(d)
    # ⟨φ|X⊗Y|φ⟩ = (1/d) Tr[X^T Y], поэтому X = d σ даёт ¼ Tr[σ^T F]
    return {(a, b, x, y): 0.25 * (phi.conj() @ np.kron(d * S[(a, x)], F[(b, y)]) @ phi).real
            for a, b, x, y in KEYS}


# ------------------------------------------------------------------ see-saw в сведённой форме

def _psd_var(d, real):
    return cp.Variable((d, d), symmetric=True) if real else cp.Variable((d, d), hermitian=True)


def _re(e):
    return e if e.is_real() else cp.real(e)


_CACHE = {}


def _problem(side, d, real, diagonal):
    """Параметризованная задача (собирается один раз): max Σ_{k} Re Tr[V_k^T C_k] при ограничениях стороны.
    side='S': Σ_x Tr V_{a,x} = 1, Σ_a V_{a,x} = 1/d; side='F': Σ_y V_{b,y} = 1, Σ_b Tr V_{b,y} = d."""
    key = (side, d, real, diagonal)
    if key in _CACHE:
        return _CACHE[key]
    keys = [(i, j) for i in (0, 1) for j in (0, 1)]
    if diagonal:
        V = {k: cp.Variable(d) for k in keys}
        C = {k: cp.Parameter(d) for k in keys}
        cons = [V[k] >= 0 for k in keys]
        tr = lambda k: cp.sum(V[k])  # noqa: E731
        mat = lambda k: cp.diag(V[k])  # noqa: E731
        obj = sum(C[k] @ V[k] for k in keys)
    else:
        V = {k: (cp.Variable((d, d), symmetric=True) if real else cp.Variable((d, d), hermitian=True)) for k in keys}
        C = {k: (cp.Parameter((d, d)) if real else cp.Parameter((d, d), complex=True)) for k in keys}
        cons = [V[k] >> 0 for k in keys]
        tr = lambda k: _re(cp.trace(V[k]))  # noqa: E731
        mat = lambda k: V[k]  # noqa: E731
        obj = _re(sum(cp.sum(cp.multiply(V[k], C[k])) for k in keys))
    if side == "S":
        for a in (0, 1):
            cons.append(tr((a, 0)) + tr((a, 1)) == 1)
        for x in (0, 1):
            cons.append(mat((0, x)) + mat((1, x)) == np.eye(d) / d)
    else:
        for b in (0, 1):
            cons.append(mat((b, 0)) + mat((b, 1)) == np.eye(d))
        for y in (0, 1):
            cons.append(tr((0, y)) + tr((1, y)) == d)
    prob = cp.Problem(cp.Maximize(obj), cons)
    _CACHE[key] = (prob, V, C, keys)
    return _CACHE[key]


def _solve_side(side, coef, d, real, diagonal):
    """coef[k] — матрица K_k такая, что цель = Σ_k Re Tr[V_k^T K_k] = Σ_k Re Σ_ij V_ij K_ij."""
    prob, V, C, keys = _problem(side, d, real, diagonal)
    for k in keys:
        K = coef[k]
        if diagonal:
            C[k].value = np.real(np.diag(K))
        elif real:
            C[k].value = np.real(K)
        else:
            # Re Σ V_ij K_ij для эрмитовой V: cvxpy берёт multiply(V, C) поэлементно
            C[k].value = K
    Q._solve(prob)
    out = {}
    for k in keys:
        v = V[k].value
        out[k] = (np.diag(v) if diagonal else np.array(v)).astype(complex)
    return out


def step_S(F, w, d, real=False, diagonal=False):
    # цель = Σ_{a,x} Tr[σ_{a,x}^T K_{a,x}], K_{a,x} = Σ_{b,y} w ¼ F_{b,y}; Tr[σ^T K] = Σ_ij σ_ij K_ij
    K = {(a, x): sum(w[(a, b, x, y)] * 0.25 * F[(b, y)] for b in (0, 1) for y in (0, 1)) for a in (0, 1) for x in (0, 1)}
    return _solve_side("S", K, d, real, diagonal)


def step_F(S, w, d, real=False, diagonal=False):
    # Tr[σ^T F] = Σ_ij σ_ij F_ij, K_{b,y} = Σ_{a,x} w ¼ σ_{a,x}
    K = {(b, y): sum(w[(a, b, x, y)] * 0.25 * S[(a, x)] for a in (0, 1) for x in (0, 1)) for b in (0, 1) for y in (0, 1)}
    return _solve_side("F", K, d, real, diagonal)


def random_reduced(d, rng, real=False, diagonal=False):
    """Случайная допустимая точка: проекторы ранга ⌊d/2⌋ + дополнение (при нечётном d — смесь)."""
    def rand_proj():
        """0 ≤ P ≤ 1, Tr P = d/2."""
        if diagonal:
            r = rng.uniform(-1, 1, d)
            return np.diag(0.5 + 0.25 * (r - r.mean())).astype(complex)
        X = rng.normal(size=(d, d)) + (0 if real else 1j * rng.normal(size=(d, d)))
        Qm, _ = np.linalg.qr(X)
        k = d // 2
        P = Qm[:, :k] @ Qm[:, :k].conj().T
        if d % 2:
            v = Qm[:, k:k + 1]
            P = P + 0.5 * v @ v.conj().T
        return P
    S, F = {}, {}
    for x in (0, 1):
        P = rand_proj()
        S[(0, x)] = P / d
        S[(1, x)] = (np.eye(d) - P) / d
    for b in (0, 1):
        P = rand_proj()
        F[(b, 0)] = P
        F[(b, 1)] = np.eye(d) - P
    return S, F


def seesaw_reduced(w, d, rng, iters=100, tol=1e-9, real=False, diag_S=False, diag_F=False):
    S, F = random_reduced(d, rng, real=real)
    if diag_S:
        S = {k: np.diag(np.diag(v)).astype(complex) for k, v in random_reduced(d, rng, diagonal=True)[0].items()}
    last = -np.inf
    try:
        for _ in range(iters):
            F = step_F(S, w, d, real, diag_F)
            S = step_S(F, w, d, real, diag_S)
            val = sum(w[t] * v for t, v in p_reduced(S, F).items())
            if val - last < tol:
                break
            last = val
    except Q.SolverFailure:
        return None
    return val, S, F


# ------------------------------------------------------------------ NPA

def _reduce(word):
    """Проекторы: E_x² = E_x — удаление подряд идущих повторов."""
    out = []
    for s in word:
        if out and out[-1] == s:
            continue
        out.append(s)
    return tuple(out)


def _canon(alice, bob):
    k1 = (_reduce(alice), _reduce(bob))
    k2 = (_reduce(tuple(reversed(alice))), _reduce(tuple(reversed(bob))))
    return min(k1, k2)


def npa(w, constraints=True, level="1+AB"):
    """Верхняя оценка max Σ w p по квантовому Белловскому множеству (все состояния, любые размерности).
    Операторы: E_x — проектор «a = 0 | x», G_b — проектор «y = 0 | b»; p(a,b,x,y) = ¼ P(a,y|x,b)."""
    A = [("E", 0), ("E", 1)]
    B = [("G", 0), ("G", 1)]
    if level == "1+AB":
        S = [((), ())] + [((a,), ()) for a in A] + [((), (b,)) for b in B] + [((a,), (b,)) for a in A for b in B]
    elif level == "2":
        S = [((), ())] + [((a,), ()) for a in A] + [((), (b,)) for b in B]
        S += [((a1, a2), ()) for a1 in A for a2 in A if a1 != a2] + [((), (b1, b2)) for b1 in B for b2 in B if b1 != b2]
        S += [((a,), (b,)) for a in A for b in B]
    else:
        raise ValueError(level)
    n = len(S)
    keys = {}
    idx = np.zeros((n, n), dtype=int)
    for i in range(n):
        for j in range(n):
            al = tuple(reversed(S[i][0])) + S[j][0]
            bo = tuple(reversed(S[i][1])) + S[j][1]
            k = _canon(al, bo)
            if k not in keys:
                keys[k] = len(keys)
            idx[i, j] = keys[k]
    y = cp.Variable(len(keys))
    G = cp.bmat([[y[idx[i, j]] for j in range(n)] for i in range(n)])
    one = keys[((), ())]
    cons = [G >> 0, y[one] == 1]

    def m(al, bo):
        return y[keys[_canon(al, bo)]]
    PA = {x: m((("E", x),), ()) for x in (0, 1)}
    PB = {b: m((), (("G", b),)) for b in (0, 1)}
    PAB = {(x, b): m((("E", x),), (("G", b),)) for x in (0, 1) for b in (0, 1)}

    def P(a, yy, x, b):
        # P(a,y|x,b) через моменты проекторов на исход 0
        e, g, eg = PA[x], PB[b], PAB[(x, b)]
        if a == 0 and yy == 0:
            return eg
        if a == 0 and yy == 1:
            return e - eg
        if a == 1 and yy == 0:
            return g - eg
        return 1 - e - g + eg
    if constraints:
        cons += [PA[0] + PA[1] == 1, PB[0] + PB[1] == 1]
    obj = sum(w[t] * 0.25 * P(t[0], t[3], t[2], t[1]) for t in KEYS if w[t])
    prob = cp.Problem(cp.Maximize(obj), cons)
    Q._solve(prob)
    return prob.value, n, len(keys)

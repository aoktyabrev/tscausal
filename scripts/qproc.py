"""
Квантовое ядро Stage C: процесс-матрицы на A_I ⊗ A_O ⊗ B_I ⊗ B_O (порядок подсистем
0,1,2,3), буквальные ограничения MH24 (Wcons, vcons, ucons) и B15/OCB (valid_W),
TS- и OCB-инструменты, see-saw (cvxpy).

Отображение «trace-and-replace» (MH-24, B15-8): _X W = (1/d_X) 1^X ⊗ Tr_X W, _[1-X] W = W - _X W.
"""
import itertools

import numpy as np
import cvxpy as cp

AI, AO, BI, BO = 0, 1, 2, 3
NAMES = ("A_I", "A_O", "B_I", "B_O")


# ------------------------------------------------------------------ базис и отображения

def gellmann(d):
    """Эрмитов базис {σ_μ}: σ_0 = 1, Tr σ_i = 0, Tr σ_μ σ_ν = d δ (нормировка MH24, Sec. 3.2)."""
    mats = [np.eye(d, dtype=complex)]
    for j in range(d):
        for k in range(j + 1, d):
            m = np.zeros((d, d), complex); m[j, k] = m[k, j] = 1; mats.append(m)
            m = np.zeros((d, d), complex); m[j, k] = -1j; m[k, j] = 1j; mats.append(m)
    for l in range(1, d):
        m = np.zeros((d, d), complex)
        for j in range(l):
            m[j, j] = 1
        m[l, l] = -l
        mats.append(m * np.sqrt(2 / (l * (l + 1))))
    out = [mats[0]] + [m * np.sqrt(d / np.trace(m @ m).real) for m in mats[1:]]
    return out


def kron(*ms):
    r = np.array([[1.0 + 0j]])
    for m in ms:
        r = np.kron(r, m)
    return r


def ptrace(W, d, keep_out):
    """Частичный след по подсистемам keep_out (список индексов) для 4 подсистем размерности d."""
    T = W.reshape([d] * 8)
    for k in sorted(keep_out, reverse=True):
        n = T.ndim // 2
        T = np.trace(T, axis1=k, axis2=k + n)
    return T


def tr_replace(W, d, X):
    """_X W для подсистемы X ∈ {0..3} (буквально по MH-24)."""
    T = W.reshape([d] * 8)
    tr = np.trace(T, axis1=X, axis2=X + 4)                 # 6 индексов: 3 row, 3 col
    rows = [i for i in range(4) if i != X]
    idx_in = "".join("abcd"[i] for i in rows) + "".join("efgh"[i] for i in rows)
    out = np.einsum(idx_in + ",xy->" + "abcd".replace("abcd"[X], "x") + "efgh".replace("efgh"[X], "y"),
                    tr, np.eye(d) / d)
    return out.reshape(d ** 4, d ** 4)


def op(W, d, word):
    """Композиция отображений по слову, напр. [('t',AI),('n',BO)] = _{A_I[1-B_O]}W
    ('t' — след-и-замена, 'n' — бесследовая часть)."""
    R = W
    for kind, X in word:
        R = tr_replace(R, d, X) if kind == "t" else R - tr_replace(R, d, X)
    return R


def mh_constraints(d, pre_marg=True, post_marg=True):
    """Слова отображений из MH24: Wcons2–4 (всегда), vcons1–3 (если v маргинализовано),
    ucons1–3 (если u маргинализовано). Каждое должно давать 0."""
    t, n = "t", "n"
    words = {"Wcons2": [(t, BI), (t, BO), (n, AI), (n, AO)],
             "Wcons3": [(t, AI), (t, AO), (n, BI), (n, BO)],
             "Wcons4": [(n, AI), (n, AO), (n, BI), (n, BO)]}
    if post_marg:
        words.update({"vcons1": [(t, AI), (n, BO)], "vcons2": [(t, BI), (n, AO)],
                      "vcons3": [(n, AO), (n, BO)]})
    if pre_marg:
        words.update({"ucons1": [(t, AO), (n, BI)], "ucons2": [(t, BO), (n, AI)],
                      "ucons3": [(n, AI), (n, BI)]})
    return words


def ocb_constraints(d):
    """B15-8 (valid_W) в виде слов/комбинаций, каждое = 0 для допустимого W."""
    def c1(W):
        return op(W, d, [("t", BI), ("t", BO)]) - op(W, d, [("t", AO), ("t", BI), ("t", BO)])

    def c2(W):
        return op(W, d, [("t", AI), ("t", AO)]) - op(W, d, [("t", AI), ("t", AO), ("t", BO)])

    def c3(W):
        return W - op(W, d, [("t", BO)]) - op(W, d, [("t", AO)]) + op(W, d, [("t", AO), ("t", BO)])
    return {"ocb1": c1, "ocb2": c2, "ocb3": c3}


def product_basis(d):
    g = gellmann(d)
    for idx in itertools.product(range(d * d), repeat=4):
        yield idx, kron(*[g[i] for i in idx])


def classify_basis(d, maps):
    """Для каждого базисного элемента σ_{μνab}: проверка, что каждое отображение переводит его
    в кратное себе (диагональность) и обнуляет ли. Возвращает разрешённые индексы."""
    allowed, nondiag = [], 0
    for idx, B in product_basis(d):
        ok = True
        for name, f in maps.items():
            R = f(B)
            nr = np.linalg.norm(R)
            if nr > 1e-9:
                coef = np.vdot(B, R) / np.vdot(B, B)
                if np.linalg.norm(R - coef * B) > 1e-8:
                    nondiag += 1
                ok = False
        if ok:
            allowed.append(idx)
    return allowed, nondiag


def maps_from_words(d, words):
    return {k: (lambda W, w=w: op(W, d, w)) for k, w in words.items()}


def types_of(allowed):
    return sorted({tuple(NAMES[i] for i in range(4) if idx[i] > 0) for idx in allowed})


# ------------------------------------------------------------------ процессы по типам

class ProcessFamily:
    """W = (1/(d_A d_B)) (1 + Σ_k w_k B_k) по списку разрешённых неединичных базисных элементов."""

    def __init__(self, d, allowed):
        self.d = d
        g = gellmann(d)
        self.idx = [i for i in allowed if any(i)]
        self.B = [kron(*[g[j] for j in i]) / d ** 2 for i in self.idx]
        self.W0 = np.eye(d ** 4, dtype=complex) / d ** 2

    def matrix(self, w):
        return self.W0 + sum(wk * Bk for wk, Bk in zip(w, self.B))


# ------------------------------------------------------------------ инструменты

def rand_psd(n, rng):
    X = rng.normal(size=(n, n)) + 1j * rng.normal(size=(n, n))
    return X @ X.conj().T


def ptrace_AB(M, d, axis):
    """Частичный след двухчастичного оператора (d×d ⊗ d×d) по подсистеме axis (0 — вход, 1 — выход)."""
    T = M.reshape(d, d, d, d)
    return np.trace(T, axis1=axis, axis2=axis + 2)


def random_ts_instrument(d, rng, iters=200):
    """Случайная TS-операция (MH-1) — проекцией чередованием (Sinkhorn-подобно)
    из случайных PSD. Точную допустимость потом обеспечивает SDP-шаг; здесь нужен старт."""
    M = {(a, x): rand_psd(d * d, rng) for a in (0, 1) for x in (0, 1)}
    for _ in range(iters):
        for a in (0, 1):                       # Tr_{out} Σ_x M_{a,x} = 1_in
            S = ptrace_AB(M[(a, 0)] + M[(a, 1)], d, 1)
            L = np.linalg.inv(sqrtm_psd(S))
            for x in (0, 1):
                M[(a, x)] = np.kron(L, np.eye(d)) @ M[(a, x)] @ np.kron(L, np.eye(d)).conj().T
        for x in (0, 1):                       # Tr_{in} Σ_a M_{a,x} = 1_out
            S = ptrace_AB(M[(0, x)] + M[(1, x)], d, 0)
            L = np.linalg.inv(sqrtm_psd(S))
            for a in (0, 1):
                M[(a, x)] = np.kron(np.eye(d), L) @ M[(a, x)] @ np.kron(np.eye(d), L).conj().T
    return M


def sqrtm_psd(S):
    S = (S + S.conj().T) / 2
    w, V = np.linalg.eigh(S)
    return V @ np.diag(np.sqrt(np.clip(w, 1e-15, None))) @ V.conj().T


def ts_instrument_residual(M, d):
    r = 0.0
    for a in (0, 1):
        r = max(r, np.abs(ptrace_AB(M[(a, 0)] + M[(a, 1)], d, 1) - np.eye(d)).max())
    for x in (0, 1):
        r = max(r, np.abs(ptrace_AB(M[(0, x)] + M[(1, x)], d, 0) - np.eye(d)).max())
    mineig = min(np.linalg.eigvalsh((m + m.conj().T) / 2).min() for m in M.values())
    return r, mineig


# ------------------------------------------------------------------ вероятности

def probs_ts(W, MA, MB, d):
    """p(a,b,x,y) = (1/4) Tr[W (M_{a,x} ⊗ M_{b,y})] (D5)."""
    p = {}
    for a, b, x, y in itertools.product((0, 1), repeat=4):
        p[(a, b, x, y)] = 0.25 * np.trace(W @ np.kron(MA[(a, x)], MB[(b, y)])).real
    return p


def value(p, weights):
    return sum(weights[t] * p[t] for t in weights)


# ------------------------------------------------------------------ see-saw

SOLVER = "CLARABEL"


STATS = {"solves": 0, "fallback_scs": 0, "failed": 0}


class SolverFailure(RuntimeError):
    pass


def _solve(prob):
    """Принимается только статус optimal. При optimal_inaccurate — повтор через SCS (eps 1e-9);
    если и он не optimal — SolverFailure (старт see-saw отбрасывается)."""
    STATS["solves"] += 1
    try:
        prob.solve(solver=SOLVER)
    except cp.error.SolverError:
        pass
    except BaseException as e:                       # Clarabel (Rust) может упасть паникой: PanicException
        if isinstance(e, KeyboardInterrupt):
            raise
        STATS.setdefault("panics", 0)
        STATS["panics"] += 1
    if prob.status == "optimal":
        return prob.value
    if prob.status in ("infeasible", "unbounded", "infeasible_inaccurate", "unbounded_inaccurate"):
        STATS["failed"] += 1
        raise SolverFailure(f"солвер: статус {prob.status}")
    STATS["fallback_scs"] += 1
    try:
        prob.solve(solver="SCS", eps=1e-9, max_iters=200000)
    except cp.error.SolverError:
        pass
    except BaseException as e:
        if isinstance(e, KeyboardInterrupt):
            raise
    if prob.status != "optimal":
        STATS["failed"] += 1
        raise SolverFailure(f"солвер: статус {prob.status} (после SCS)")
    return prob.value


def w_step(fam, MA, MB, weights, d, extra=None):
    """max по W в семействе fam при фиксированных инструментах."""
    G = sum(weights[(a, b, x, y)] * 0.25 * np.kron(MA[(a, x)], MB[(b, y)])
            for (a, b, x, y) in weights if weights[(a, b, x, y)] != 0)
    c = np.array([np.trace(Bk @ G).real for Bk in fam.B])
    c0 = np.trace(fam.W0 @ G).real
    w = cp.Variable(len(fam.B))
    Wexpr = fam.W0 + sum(w[k] * fam.B[k] for k in range(len(fam.B)))
    cons = [(Wexpr + Wexpr.H) / 2 >> 0]
    prob = cp.Problem(cp.Maximize(c0 + c @ w), cons)
    _solve(prob)
    return fam.matrix(w.value)


def instrument_step(W, Mother, weights, d, party, kind="TS"):
    """max по инструментам одной стороны. party='A' или 'B'. kind: 'TS' (MH-1) или 'OCB' (B15-8,
    вход — второй индекс ключа: M[(a,x)] в OCB-смысле означает исход a при входе x)."""
    n = d * d
    K = {}
    for key in itertools.product((0, 1), repeat=2):
        K[key] = np.zeros((n, n), complex)
    for (a, b, x, y), wt in weights.items():
        if wt == 0:
            continue
        if party == "A":
            Mo = Mother[(b, y)]
            # Tr[W (M_A ⊗ M_B)] = Tr[M_A · Tr_B[W (1 ⊗ M_B)]]
            K[(a, x)] += wt * 0.25 * _eff_A(W, Mo, n)
        else:
            Mo = Mother[(a, x)]
            K[(b, y)] += wt * 0.25 * _eff_B(W, Mo, n)
    V = {k: cp.Variable((n, n), hermitian=True) for k in K}
    cons = [V[k] >> 0 for k in V]
    if kind == "TS":
        for a in (0, 1):
            cons.append(cp.partial_trace(V[(a, 0)] + V[(a, 1)], [d, d], axis=1) == np.eye(d))
        for x in (0, 1):
            cons.append(cp.partial_trace(V[(0, x)] + V[(1, x)], [d, d], axis=0) == np.eye(d))
    elif kind == "FWD":
        # только прямая нормировка (MH-1, первое условие): Tr_out Σ_x M_{a,x} = 1 для каждого дохода a
        for a in (0, 1):
            cons.append(cp.partial_trace(V[(a, 0)] + V[(a, 1)], [d, d], axis=1) == np.eye(d))
    elif kind == "OCB":
        for x in (0, 1):
            cons.append(cp.partial_trace(V[(0, x)] + V[(1, x)], [d, d], axis=1) == np.eye(d))
    else:
        raise ValueError(kind)
    obj = sum(cp.real(cp.trace(V[k] @ K[k])) for k in K)
    prob = cp.Problem(cp.Maximize(obj), cons)
    _solve(prob)
    return {k: (V[k].value + V[k].value.conj().T) / 2 for k in V}


def _eff_A(W, MB, n):
    """E = Tr_B[W (1_A ⊗ M_B)] так, что Tr[W (M_A⊗M_B)] = Tr[M_A E]."""
    Wt = W.reshape(n, n, n, n)          # W[(iA,iB),(jA,jB)]
    # Tr[W (MA⊗MB)] = Σ W[iA iB, jA jB] MA[jA,iA] MB[jB,iB] -> E[jA,iA] = Σ W[iA iB, jA jB] MB[jB,iB]
    return np.einsum("pqrs,sq->pr", Wt, MB)


def _eff_B(W, MA, n):
    Wt = W.reshape(n, n, n, n)
    return np.einsum("pqrs,rp->qs", Wt, MA)


def seesaw(fam, weights, d, rng, iters=60, tol=1e-9, kind="TS", fixed_W=None):
    """Возвращает (значение, W, MA, MB) либо None, если старт упал (SolverFailure).
    fixed_W — оптимизация только по инструментам."""
    try:
        return _seesaw(fam, weights, d, rng, iters, tol, kind, fixed_W)
    except SolverFailure:
        return None


def _seesaw(fam, weights, d, rng, iters, tol, kind, fixed_W):
    init = {"TS": random_ts_instrument, "OCB": random_ocb_instrument, "FWD": random_fwd_instrument}[kind]
    MA = init(d, rng)
    MB = init(d, rng)
    W = fixed_W
    last = -np.inf
    for _ in range(iters):
        if fixed_W is None:
            W = w_step(fam, MA, MB, weights, d)
        MA = instrument_step(W, MB, weights, d, "A", kind)
        MB = instrument_step(W, MA, weights, d, "B", kind)
        val = value(probs_ocb(W, MA, MB), weights) if kind == "OCB" else value(probs_ts(W, MA, MB, d), weights)
        if val - last < tol:
            break
        last = val
    return val, W, MA, MB


def random_fwd_instrument(d, rng):
    """Случайная операция только с прямой нормировкой: для каждого дохода a — инструмент по исходам x."""
    M = {}
    for a in (0, 1):
        P = [rand_psd(d * d, rng) for _ in (0, 1)]
        S = ptrace_AB(P[0] + P[1], d, 1)
        L = np.linalg.inv(sqrtm_psd(S))
        for x in (0, 1):
            M[(a, x)] = np.kron(L, np.eye(d)) @ P[x] @ np.kron(L, np.eye(d)).conj().T
    return M


def random_ocb_instrument(d, rng):
    M = {}
    for x in (0, 1):
        P = [rand_psd(d * d, rng) for _ in (0, 1)]
        S = ptrace_AB(P[0] + P[1], d, 1)
        L = np.linalg.inv(sqrtm_psd(S))
        for a in (0, 1):
            M[(a, x)] = np.kron(L, np.eye(d)) @ P[a] @ np.kron(L, np.eye(d)).conj().T
    return M


def probs_ocb(W, MA, MB):
    """B15-8: p(a,b|x,y) = Tr[(M_{a|x} ⊗ M_{b|y}) W]; ключ (a,b,x,y) — выходы a,b, входы x,y (нотация B15)."""
    p = {}
    for a, b, x, y in itertools.product((0, 1), repeat=4):
        p[(a, b, x, y)] = np.trace(W @ np.kron(MA[(a, x)], MB[(b, y)])).real
    return p

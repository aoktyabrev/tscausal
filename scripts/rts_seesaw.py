"""
RTS stage 0, R.1 и R.3: see-saw по вещественным сетевым ISO-моделям (D12).
ω = ω₁ ⊗ ω₂ + Δ,  ω₁ на A⊗B1, ω₂ на B2⊗C (маргиналы каждого — максимально смешанные: канал унитален и сохраняет след),
Δ ∈ Anti(A⊗B1) ⊗ Anti(B2⊗C) — ровно то, что не видно операционально независимым измерениям (HW26 стр. 67);
ISO для ω: Tr_{B1B2} Δ = 0, Tr_{AC} Δ = 0. R.1: Δ ≡ 0 (произведения). Операции вещественные симметричные.
Результат: results/json/rts_seesaw.json.
"""
import itertools
import json
import os
import sys
import time

import cvxpy as cp
import numpy as np
import scipy.sparse as sp

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import polytope as P  # noqa: E402
import qproc as Q  # noqa: E402
import rts as R  # noqa: E402

FAST = os.environ.get("RTS_FAST") == "1"


def antisym_basis(n):
    out = []
    for i in range(n):
        for j in range(i + 1, n):
            M = np.zeros((n, n)); M[i, j] = 1; M[j, i] = -1
            out.append(M)
    return np.array(out)


def ptr(M, dims, keep):
    """Частичный след для 4 подсистем (A,B1,B2,C) — оставить подсистемы keep."""
    T = M.reshape(list(dims) * 2)
    n = 4
    letters = "abcdefgh"
    idx_row = list(letters[:4]); idx_col = list(letters[4:])
    for k in range(4):
        if k not in keep:
            idx_col[k] = idx_row[k]
    out = "".join(idx_row[k] for k in keep) + "".join(idx_col[k] for k in keep)
    R_ = np.einsum("".join(idx_row) + "".join(idx_col) + "->" + out, T)
    d = int(np.prod([dims[k] for k in keep]))
    return R_.reshape(d, d)


class Model:
    def __init__(self, dims, cplx=False):
        self.dims = dims
        self.cplx = cplx          # калибровка: комплексный see-saw (эрмитовы переменные) должен находить 6√2
        dA, dB1, dB2, dC = dims
        self.n1, self.n2 = dA * dB1, dB2 * dC
        self.N = self.n1 * self.n2
        # Δ = Σ D_kl a_k ⊗ a_l, a_k — элементарный базис Anti. Базис хранится РАЗРЕЖЕННО (4 ненулевых на элемент):
        # плотный вариант для (4,4,4,4) занимал ~7.5 ГБ и уронил систему 2026-09-22.
        self.p1, self.p2 = [(i, j) for i in range(self.n1) for j in range(i + 1, self.n1)], \
                           [(i, j) for i in range(self.n2) for j in range(i + 1, self.n2)]
        rows, cols, vals = [], [], []
        for k, (i, j) in enumerate(self.p1):
            for l, (u, v) in enumerate(self.p2):
                r = k * len(self.p2) + l
                for (a, b, sa) in ((i, j, 1), (j, i, -1)):
                    for (c, d, sc) in ((u, v, 1), (v, u, -1)):
                        rows.append(r); cols.append((a * self.n2 + c) * self.N + (b * self.n2 + d)); vals.append(sa * sc)
        self.Ks = sp.csr_matrix((vals, (rows, cols)), shape=(len(self.p1) * len(self.p2), self.N * self.N))
        # маргиналы базисных элементов: Tr_B1 a_k (на A), Tr_A a_k (на B1), Tr_B2 a_l (на C), Tr_C a_l (на B2)
        self.trB1, self.trA = self._ptr_basis(self.p1, dA, dB1)
        self.trC, self.trB2 = self._ptr_basis(self.p2, dB2, dC)

    @staticmethod
    def _ptr_basis(pairs, d1, d2):
        """Для a = E_ij − E_ji на d1⊗d2: vec(Tr_2 a) (d1²) и vec(Tr_1 a) (d2²) — строки матриц."""
        t2, t1 = np.zeros((len(pairs), d1 * d1)), np.zeros((len(pairs), d2 * d2))
        for k, (i, j) in enumerate(pairs):
            (i1, i2), (j1, j2) = divmod(i, d2), divmod(j, d2)
            if i2 == j2:
                t2[k, i1 * d1 + j1] += 1; t2[k, j1 * d1 + i1] -= 1
            if i1 == j1:
                t1[k, i2 * d2 + j2] += 1; t1[k, j2 * d2 + i2] -= 1
        return t2, t1

    def delta(self, D):
        return np.reshape(self.Ks.T @ D.reshape(-1), (self.N, self.N))

    # ---- целевой оператор G(A,F,C): 𝒯 = Tr[ω G]
    def G(self, A, F, C):
        G = np.zeros((self.N, self.N), complex if self.cplx else float)
        for (b, x, z), v in R.COEF.items():
            G = G + v * np.kron(np.kron(A[x][0] - A[x][1], F[R.BOBS.index(b)]), C[z][0] - C[z][1])
        return G


def rand_orth(d, rng, cplx=False):
    Xm = rng.normal(size=(d, d)) + (1j * rng.normal(size=(d, d)) if cplx else 0)
    return np.linalg.qr(Xm)[0]


def rand_proj(d, rng, tr, cplx=False):
    """Случайный 0 ≤ P ≤ 1 со следом tr (tr может быть полуцелым); вещественный, либо комплексный при cplx."""
    Qm = rand_orth(d, rng, cplx)
    k = int(np.floor(tr))
    P_ = Qm[:, :k] @ Qm[:, :k].conj().T
    if tr - k > 1e-12:
        v = Qm[:, k:k + 1]
        P_ = P_ + (tr - k) * (v @ v.conj().T)
    return P_


def random_start(m, rng):
    dA, dB1, dB2, dC = m.dims
    A = {x: None for x in (1, 2, 3)}
    for x in A:
        P_ = rand_proj(dA, rng, dA / 2, m.cplx)
        A[x] = [P_, np.eye(dA) - P_]
    C = {}
    for z in range(1, 7):
        P_ = rand_proj(dC, rng, dC / 2, m.cplx)
        C[z] = [P_, np.eye(dC) - P_]
    # Боб: случайный ортонормированный базис, разбитый на 4 равные группы
    dB = dB1 * dB2
    Qm = rand_orth(dB, rng, m.cplx)
    g = dB // 4
    F = [Qm[:, k * g:(k + 1) * g] @ Qm[:, k * g:(k + 1) * g].conj().T for k in range(4)]
    # состояния: максимально запутанные вещественные с маргиналами 1/d (случайный ортогональный поворот)
    def maxent(d1, d2):
        """Φ⁺ на общей части размерности d = min(d1,d2), остаток максимально смешан; затем случайные ортогональные
        повороты с обеих сторон. Оба маргинала — максимально смешанные (ISO)."""
        d = min(d1, d2)
        v = np.zeros(d * d)
        for i in range(d):
            v[i * d + i] = 1 / np.sqrt(d)
        core = np.outer(v, v)                                    # (s1, s2), s1,s2 ∈ [d]
        r1, r2 = d1 // d, d2 // d
        full = np.kron(np.kron(core, np.eye(r1) / r1), np.eye(r2) / r2)   # порядок (s1, s2, e1, e2)
        full = full.reshape([d, d, r1, r2] * 2).transpose([0, 2, 1, 3, 4, 6, 5, 7]).reshape(d1 * d2, d1 * d2)
        O = np.kron(rand_orth(d1, rng, m.cplx), rand_orth(d2, rng, m.cplx))
        return O @ full @ O.conj().T
    return A, F, C, maxent(dA, dB1), maxent(dB2, dC)


def _var(m, d):
    return cp.Variable((d, d), hermitian=True) if m.cplx else cp.Variable((d, d), symmetric=True)


def solve_ops_A(m, w, F, C, which, n_settings, trace_target):
    """SDP по POVM одной стороны (A — первая подсистема, C — последняя) при фиксированном ω."""
    dA, dB1, dB2, dC = m.dims
    d = dA if which == "A" else dC
    V = {(s, k): _var(m, d) for s in range(1, n_settings + 1) for k in (0, 1)}
    cons = [V[k] >> 0 for k in V]
    for s in range(1, n_settings + 1):
        cons.append(V[(s, 0)] + V[(s, 1)] == np.eye(d))
    for k in (0, 1):
        cons.append(sum(cp.trace(V[(s, k)]) for s in range(1, n_settings + 1)) == trace_target)
    # эффективные операторы: Tr[ω (O_A ⊗ F ⊗ O_C)]
    obj = 0
    T = w.reshape(dA, dB1 * dB2, dC, dA, dB1 * dB2, dC)
    for (b, x, z), v in R.COEF.items():
        Fb = F[R.BOBS.index(b)]
        if which == "A":
            Oc = C[z][0] - C[z][1]
            E = np.einsum("apcdqf,qp,fc->ad", T, Fb, Oc)       # Tr[ω(O⊗Fb⊗Oc)] = Tr[O E^T]... см. ниже
            obj += v * cp.sum(cp.multiply(V[(x, 0)] - V[(x, 1)], E.T))
        else:
            Oa = A_cur[x][0] - A_cur[x][1]
            E = np.einsum("apcdqf,da,qp->cf", T, Oa, Fb)
            obj += v * cp.sum(cp.multiply(V[(z, 0)] - V[(z, 1)], E.T))
    prob = cp.Problem(cp.Maximize(cp.real(obj) if m.cplx else obj), cons)
    Q._solve(prob)
    return {s: [V[(s, 0)].value, V[(s, 1)].value] for s in range(1, n_settings + 1)}


A_cur = None


def solve_F(m, w, A, C):
    dA, dB1, dB2, dC = m.dims
    dB = dB1 * dB2
    V = [_var(m, dB) for _ in range(4)]
    cons = [v >> 0 for v in V] + [sum(V) == np.eye(dB)] + [cp.trace(v) == dB / 4 for v in V]
    T = w.reshape(dA, dB, dC, dA, dB, dC)
    obj = 0
    for (b, x, z), v in R.COEF.items():
        E = np.einsum("apcdqf,da,fc->pq", T, A[x][0] - A[x][1], C[z][0] - C[z][1])
        obj += v * cp.sum(cp.multiply(V[R.BOBS.index(b)], E.T))
    prob = cp.Problem(cp.Maximize(cp.real(obj) if m.cplx else obj), cons)
    Q._solve(prob)
    return [v.value for v in V]


def marg_constraints(m, W):
    """ISO: (A,C)- и (B1,B2)-маргиналы ω максимально смешаны; выражено через cvxpy partial_trace."""
    dA, dB1, dB2, dC = m.dims
    cons = []
    # порядок A,B1,B2,C; след по B1,B2 (axis 1 и 2)
    mAC = cp.partial_trace(cp.partial_trace(W, [dA, dB1, dB2, dC], axis=2), [dA, dB1, dC], axis=1)
    cons.append(mAC == np.eye(dA * dC) / (dA * dC))
    mB = cp.partial_trace(cp.partial_trace(W, [dA, dB1, dB2, dC], axis=3), [dA, dB1, dB2], axis=0)
    cons.append(mB == np.eye(dB1 * dB2) / (dB1 * dB2))
    return cons


def _solve_big(prob):
    """PSD 256×256 (размерности 4,4,4,4): Clarabel строит плотный KKT ≈ 8.7 ГБ, поэтому только SCS.
    Допустимость найденной точки затем проверяется и восстанавливается в check() (примесь белого шума)."""
    Q.STATS["solves"] += 1
    try:
        prob.solve(solver="SCS", eps=1e-8, max_iters=20000)   # 1e5 итераций на Δ-шаге — до 700 с
    except cp.error.SolverError:
        pass
    Q.STATS.setdefault("scs_inaccurate", 0)
    Q.STATS["scs_inaccurate"] += prob.status == "optimal_inaccurate"
    if prob.status not in ("optimal", "optimal_inaccurate"):
        Q.STATS["failed"] += 1
        raise Q.SolverFailure(f"SCS: статус {prob.status}")
    return prob.value


def solve_state(m, G, w1, w2, Dcoef, part, use_delta, direct_scs=False):
    """part ∈ {'w1','w2','D'} — SDP по соответствующей части ω при фиксированных остальных."""
    dA, dB1, dB2, dC = m.dims
    if part == "w1":
        V = _var(m, m.n1)
        W = cp.kron(V, w2) + (Dcoef if use_delta else 0)
        cons = [V >> 0,
                cp.partial_trace(V, [dA, dB1], axis=1) == np.eye(dA) / dA,
                cp.partial_trace(V, [dA, dB1], axis=0) == np.eye(dB1) / dB1]
    elif part == "w2":
        V = _var(m, m.n2)
        W = cp.kron(w1, V) + (Dcoef if use_delta else 0)
        cons = [V >> 0,
                cp.partial_trace(V, [dB2, dC], axis=1) == np.eye(dB2) / dB2,
                cp.partial_trace(V, [dB2, dC], axis=0) == np.eye(dC) / dC]
    else:
        # маргиналы ω₁⊗ω₂ уже ISO; маргиналы Δ: (A,C) — Σ D_kl Tr_B1 a_k ⊗ Tr_B2 a_l = 0, (B1,B2) — аналогично
        V = cp.Variable((len(m.p1), len(m.p2)))
        W0 = np.kron(w1, w2)
        W = W0 + cp.reshape(m.Ks.T @ cp.vec(V, order="C"), (m.N, m.N), order="C")
        gc = np.reshape(m.Ks @ G.T.reshape(-1), V.shape)
        cons = [m.trB1.T @ V @ m.trB2 == 0, m.trA.T @ V @ m.trC == 0, (W + W.T) / 2 >> 0]
        prob = cp.Problem(cp.Maximize(float(np.sum(W0 * G.T)) + cp.sum(cp.multiply(V, gc))), cons)
        if direct_scs:
            # PSD 256×256: Clarabel строит плотный блок KKT svec(256)² ≈ 8.7 ГБ — только SCS; статус возвращается,
            # допустимость и значение затем пересчитываются вызывающим кодом
            prob.solve(solver="SCS", eps=1e-8, max_iters=100000)
            return m.delta(V.value), prob.status, prob.value
        (_solve_big if m.N >= 256 else Q._solve)(prob)
        return m.delta(V.value)
    cons += [((W + W.H) / 2 if m.cplx else (W + W.T) / 2) >> 0] + marg_constraints(m, W)
    obj = cp.sum(cp.multiply(W, G.T))
    prob = cp.Problem(cp.Maximize(cp.real(obj) if m.cplx else obj), cons)
    (_solve_big if m.N >= 256 else Q._solve)(prob)
    return V.value


def run(m, rng, use_delta, iters=40, tol=1e-7, start=None):
    """Этап 1: see-saw по произведениям (Δ = 0). Этап 2 (use_delta): чередование Δ и операций при фиксированных
    маргиналах ω₁, ω₂; обновление ω₁, ω₂ пробуется, при сбое солвера — пропускается (старые значения допустимы)."""
    global A_cur
    A, F, C, w1, w2 = random_start(m, rng) if start is None else start
    Dc = np.zeros((m.N, m.N))
    dA, dB1, dB2, dC = m.dims

    def omega_of(w1, w2, Dc):
        return np.kron(w1, w2) + Dc

    def ops_step(omega):
        global A_cur
        nonlocal A, C, F
        A = solve_ops_A(m, omega, F, C, "A", 3, 1.5 * dA)
        A_cur = A
        C = solve_ops_A(m, omega, F, C, "C", 6, 3.0 * dC)
        F = solve_F(m, omega, A, C)
    last = -np.inf
    stats = {"phase1": None, "delta_steps": 0, "w_skipped": 0}
    try:
        for it in range(iters):                                  # этап 1
            ops_step(omega_of(w1, w2, Dc))
            G = m.G(A, F, C)
            w1 = solve_state(m, G, w1, w2, Dc, "w1", False)
            w2 = solve_state(m, G, w1, w2, Dc, "w2", False)
            val = float(np.trace(omega_of(w1, w2, Dc) @ m.G(A, F, C)).real)
            if val - last < tol:
                break
            last = val
        stats["phase1"] = last
        if use_delta:
            last = -np.inf
            for it in range(iters):                              # этап 2
                ops_step(omega_of(w1, w2, Dc))
                G = m.G(A, F, C)
                Dc = solve_state(m, G, w1, w2, Dc, "D", True)
                stats["delta_steps"] += 1
                for part in ("w1", "w2"):
                    try:
                        new = solve_state(m, G, w1, w2, Dc, part, True)
                        if part == "w1":
                            w1 = new
                        else:
                            w2 = new
                    except Q.SolverFailure:
                        stats["w_skipped"] += 1
                val = float(np.trace(omega_of(w1, w2, Dc) @ m.G(A, F, C)).real)
                if val - last < tol:
                    break
                last = val
    except Q.SolverFailure:
        return None
    RUN_STATS.append(stats)
    return val, omega_of(w1, w2, Dc), A, F, C


RUN_STATS = []


def check(m, omega, A, F, C, rng):
    """Независимая проверка найденной точки: положительность, маргиналы ISO, операциональная независимость, значение."""
    Tval = R.T_value(omega, A, F, C)
    lam = float(np.linalg.eigvalsh((omega + omega.T) / 2).min())
    p_fix = max(0.0, -lam / (-lam + 1 / m.N))
    om_f = (1 - p_fix) * omega + p_fix * np.eye(m.N) / m.N
    return {"T_recomputed": Tval, "min_eig": lam, "noise_for_feasibility": p_fix,
            "T_feasible": R.T_value(om_f, A, F, C),
            "min_eig_feasible": float(np.linalg.eigvalsh((om_f + om_f.T) / 2).min()),
            "iso_marginals_dev": R.marginals_ok(omega, m.dims) if m.dims == (4, 4, 4, 4) or True else None,
            "oi_violation": R.oi_violation(omega, m.dims, rng, 100),
            "alice_ts": [float(sum(np.trace(A[x][a]) for x in A)) for a in (0, 1)],
            "charlie_ts": [float(sum(np.trace(C[z][c]) for z in C)) for c in (0, 1)],
            "bob_traces": [float(np.trace(f)) for f in F]}


def limit_memory(gb):
    """Жёсткий потолок адресного пространства процесса: при превышении — MemoryError, а не падение системы."""
    import resource
    resource.setrlimit(resource.RLIMIT_AS, (int(gb * 2 ** 30), int(gb * 2 ** 30)))


def main():
    limit_memory(float(os.environ.get("RTS_MEM_GB", "6")))
    t0 = time.time()
    rng = np.random.default_rng(20260925)
    out = {"stage": "RTS0 see-saw", "fast": FAST, "real_bound_RTW21": 7.6605, "complex_value": 6 * np.sqrt(2)}
    configs = [("R1_product", (2, 2, 2, 2), False, 5 if FAST else 50),
               ("R1_product", (4, 2, 2, 4), False, 3 if FAST else 20),
               ("R3_delta", (4, 2, 2, 4), True, 3 if FAST else 20),
               ("R3_delta", (2, 4, 4, 2), True, 2 if FAST else 10),
               ]  # (4,4,4,4) с Δ — только точный SDP при операциях HW (rts_struct.py): в see-saw PSD 256×256 требует плотный KKT Clarabel ≈ 8.7 ГБ
    for name, dims, use_delta, nst in configs:
        m = Model(dims)
        vals, best, failed = [], None, 0
        t1 = time.time()
        for s in range(nst):
            r = run(m, rng, use_delta, iters=25 if dims == (4, 4, 4, 4) else 40)
            if r is None:
                failed += 1
                continue
            vals.append(r[0])
            if best is None or r[0] > best[0]:
                best = r
            print(f"  {name} {dims} старт {s}: {r[0]:.6f}", flush=True)
        rec = {"values_sorted": sorted(vals, reverse=True), "failed": failed, "seconds": round(time.time() - t1, 1)}
        if best is not None:
            rec["best"] = best[0]
            rec["check"] = check(m, *best[1:], rng)
        out[f"{name}_{'x'.join(map(str, dims))}"] = rec
        with open(os.path.join(P.ROOT, "results", "json", "rts_seesaw.json"), "w") as fh:
            json.dump(out, fh, ensure_ascii=False, indent=1, default=float)
    out["seconds"] = round(time.time() - t0, 1)
    with open(os.path.join(P.ROOT, "results", "json", "rts_seesaw.json"), "w") as fh:
        json.dump(out, fh, ensure_ascii=False, indent=1, default=float)
    print(json.dumps({k: (v if not isinstance(v, dict) else {kk: vv for kk, vv in v.items() if kk != "values_sorted"})
                      for k, v in out.items()}, ensure_ascii=False, indent=1, default=float))


if __name__ == "__main__":
    main()

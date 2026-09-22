"""
T3.0, T.2 (квант): see-saw по W̄ ∈ ISO_3 (три кубитные стороны) на игре BW16 с TS-инструментами.
Порядок подсистем: A_I, A_O, B_I, B_O, C_I, C_O. p = (1/8) Tr[W (M_A ⊗ M_B ⊗ M_C)] (D5/D11).
Калибровки: (1) W_AF (Лугано) + TS-стратегия «переслать» даёт 1; (2) see-saw в классе TF_3 (OCB) доходит до 1;
(3) see-saw в ISO_3 на игре, где классика с TS-операциями даёт известное значение — см. отчёт.
"""
import itertools
import json
import os
import sys
import time

import cvxpy as cp
import mpmath as mp
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import polytope as P  # noqa: E402
import qproc as Q  # noqa: E402
from t3_classical import BITS3, win, lugano  # noqa: E402

PAULI = [np.eye(2, dtype=complex), np.array([[0, 1], [1, 0]], complex),
         np.array([[0, -1j], [1j, 0]], complex), np.array([[1, 0], [0, -1]], complex)]
FAST = os.environ.get("T3_FAST") == "1"


def kron(*ms):
    r = np.array([[1.0 + 0j]])
    for m in ms:
        r = np.kron(r, m)
    return r


def family(cls):
    """Базис допустимых неединичных членов класса cls ∈ {TF, TB, ISO} (правило, проверенное в T.0)."""
    mats = []
    for idx in itertools.product(range(4), repeat=6):
        if not any(idx):
            continue
        ty = []
        for x in range(3):
            i, o = idx[2 * x] > 0, idx[2 * x + 1] > 0
            ty.append({(False, False): "-", (True, False): "I", (False, True): "O", (True, True): "IO"}[(i, o)])
        hasI, hasO = "I" in ty, "O" in ty
        ok = {"TF": hasI, "TB": hasO, "ISO": hasI and hasO}[cls]
        if ok:
            mats.append(kron(*[PAULI[k] for k in idx]))
    return np.array(mats)                                   # (n, 64, 64)


WIN = {}
for inc in BITS3:
    for outc in BITS3:
        WIN[(inc, outc)] = 1.0 if win(inc, outc) else 0.0


def probs(W, M):
    """p[(a,b,c),(x,y,z)] = (1/8) Tr[W (M_A[a,x] ⊗ M_B[b,y] ⊗ M_C[c,z])]."""
    p = {}
    for inc in BITS3:
        for outc in BITS3:
            K = kron(M[0][(inc[0], outc[0])], M[1][(inc[1], outc[1])], M[2][(inc[2], outc[2])])
            p[(inc, outc)] = np.trace(W @ K).real / 8
    return p


def game(W, M):
    return sum(WIN[k] * v for k, v in probs(W, M).items())


def w_step(Bs, M):
    G = np.zeros((64, 64), complex)
    for (inc, outc), wv in WIN.items():
        if wv:
            G += kron(M[0][(inc[0], outc[0])], M[1][(inc[1], outc[1])], M[2][(inc[2], outc[2])]) / 8
    c = np.einsum("kij,ji->k", Bs, G).real
    c0 = np.trace(G).real / 8
    w = cp.Variable(len(Bs))
    Bflat = Bs.reshape(len(Bs), 64 * 64).T                  # (4096, n)
    Wv = np.eye(64).reshape(-1) / 8 + Bflat @ w
    Wm = cp.reshape(Wv, (64, 64), order="C")
    prob = cp.Problem(cp.Maximize(c0 + c @ w), [(Wm + Wm.H) / 2 >> 0])
    Q._solve(prob)
    return np.eye(64) / 8 + np.einsum("kij,k->ij", Bs, w.value)


def party_step(W, M, party, rng=None):
    T = W.reshape([4] * 6)
    K = {(a, x): np.zeros((4, 4), complex) for a in (0, 1) for x in (0, 1)}
    for (inc, outc), wv in WIN.items():
        if not wv:
            continue
        ops = [M[0][(inc[0], outc[0])], M[1][(inc[1], outc[1])], M[2][(inc[2], outc[2])]]
        if party == 0:
            E = np.einsum("abcdef,eb,fc->ad", T, ops[1], ops[2])
        elif party == 1:
            E = np.einsum("abcdef,da,fc->be", T, ops[0], ops[2])
        else:
            E = np.einsum("abcdef,da,eb->cf", T, ops[0], ops[1])
        K[(inc[party], outc[party])] += wv / 8 * E
    V = {k: cp.Variable((4, 4), hermitian=True) for k in K}
    cons = [V[k] >> 0 for k in V]
    for a in (0, 1):
        cons.append(cp.partial_trace(V[(a, 0)] + V[(a, 1)], [2, 2], axis=1) == np.eye(2))
    for x in (0, 1):
        cons.append(cp.partial_trace(V[(0, x)] + V[(1, x)], [2, 2], axis=0) == np.eye(2))
    # Tr[M E] = Σ M_rp E_pr ; E[p, r] ↔ M[r, p]
    obj = sum(cp.real(cp.trace(V[k] @ K[k])) for k in K)
    prob = cp.Problem(cp.Maximize(obj), cons)
    Q._solve(prob)
    newM = list(M)
    newM[party] = {k: (V[k].value + V[k].value.conj().T) / 2 for k in V}
    return newM


def seesaw(Bs, rng, iters=15, tol=1e-6):
    M = [Q.random_ts_instrument(2, rng) for _ in range(3)]
    last = -1
    try:
        for _ in range(iters):
            W = w_step(Bs, M)
            for party in range(3):
                M = party_step(W, M, party)
            val = game(W, M)
            if val - last < tol:
                break
            last = val
    except Q.SolverFailure:
        return None
    return val, W, M


def lugano_W():
    e = [np.array([1, 0], complex), np.array([0, 1], complex)]
    Pj = lambda v: np.outer(v, v.conj())  # noqa: E731
    W = np.zeros((64, 64), complex)
    for o in BITS3:
        i = lugano(o)
        W += kron(Pj(e[i[0]]), Pj(e[o[0]]), Pj(e[i[1]]), Pj(e[o[1]]), Pj(e[i[2]]), Pj(e[o[2]]))
    return W


def forward_ops():
    """(доход a, вход i) -> (исход x = i, выход = a): M_{a,x} = |x⟩⟨x|^{I} ⊗ |a⟩⟨a|^{O}."""
    e = [np.array([1, 0], complex), np.array([0, 1], complex)]
    Pj = lambda v: np.outer(v, v.conj())  # noqa: E731
    return {(a, x): np.kron(Pj(e[x]), Pj(e[a])) for a in (0, 1) for x in (0, 1)}


def in_class(W, cls):
    """Коэффициенты Паули запрещённых типов = 0, Tr = 8, W ≥ 0."""
    allowed = family(cls)
    rest = W - np.eye(64) / 8 - sum(np.trace(B @ W).real / 64 * B for B in allowed)
    return float(np.abs(rest).max()), float(np.linalg.eigvalsh(W).min()), float(np.trace(W).real)


def main():
    t0 = time.time()
    rng = np.random.default_rng(20260924)
    out = {"stage": "T3.0/T.2 quantum", "fast": FAST}
    WL = lugano_W()
    fo = forward_ops()
    out["cal_lugano_forward_value"] = game(WL, [fo, fo, fo])
    out["cal_lugano_in_TF"] = in_class(WL, "TF")
    out["cal_lugano_in_ISO"] = in_class(WL, "ISO")
    out["cal_forward_ops_ts_residual"] = Q.ts_instrument_residual(fo, 2)
    res = {}
    for cls, nst in (("TF", 2 if FAST else 3), ("ISO", 3 if FAST else 8)):
        Bs = family(cls)
        vals, best, failed = [], None, 0
        for _ in range(nst):
            r = seesaw(Bs, rng)
            if r is None:
                failed += 1
                continue
            vals.append(r[0])
            if best is None or r[0] > best[0]:
                best = r
        rec = {"n_params": len(Bs), "values": sorted(vals, reverse=True), "failed": failed}
        if best is not None:
            v, W, M = best
            rec["best"] = v
            rec["best_W_class_residual"] = in_class(W, cls)
            rec["best_ops_ts_residual"] = [Q.ts_instrument_residual(m, 2) for m in M]
            if v > 0.75 + 1e-6:
                mp.mp.dps = 30
                Wm = mp.matrix((W).tolist())
                tot = mp.mpf(0)
                for (inc, outc), wv in WIN.items():
                    if wv:
                        K = kron(M[0][(inc[0], outc[0])], M[1][(inc[1], outc[1])], M[2][(inc[2], outc[2])])
                        tot += mp.re(mp.fsum(Wm[i, j] * mp.mpc(complex(K[j, i])) for i in range(64) for j in range(64)
                                             if K[j, i] != 0)) / 8
                rec["best_mp"] = mp.nstr(tot, 16)
        res[cls] = rec
        out[cls] = rec
    out["seconds"] = round(time.time() - t0, 1)
    out["solver_stats"] = dict(Q.STATS)
    with open(os.path.join(P.ROOT, "results", "json", "t3_quantum.json"), "w") as fh:
        json.dump(out, fh, ensure_ascii=False, indent=1, default=str)
    print(json.dumps(out, ensure_ascii=False, indent=1, default=str))


if __name__ == "__main__":
    main()

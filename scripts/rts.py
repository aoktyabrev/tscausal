"""
RTS stage 0 — временная симметрия и лазейка вещественной КМ (бинокальный сценарий Renou в TS без селекции).
Определения — PREREGISTRATION_RTS0.md, D12 (SOURCES.md). Модель (сведённая форма по D8/D12):
  ω — эффективное «состояние источников» на A ⊗ B1 ⊗ B2 ⊗ C (= Choi совместного канала (A_O,C_O)→(B_I1,B_I2) / d),
      ISO ⇔ маргиналы на (A,C) и на (B1,B2) максимально смешаны;
  Алиса: POVM A_{a|x} (x = 1..3 — её исход, a = ±1 — её доход), Σ_x Tr A_{a|x} = (3/2) d_A (TS, MH-1 с N_x=3, N_a=2);
  Чарли: POVM C_{c|z} (z = 1..6), Σ_z Tr C_{c|z} = 3 d_C;
  Боб: POVM F_b (4 исхода, дохода нет), Tr F_b = d_B1 d_B2 / 4;
  P(a,b,c|x,z) = Tr[ω (A_{a|x} ⊗ F_b ⊗ C_{c|z})].
Функционал 𝒯 — RTW21 стр. 337–342, 368.
"""
import itertools
import json
import os
import sys
import time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import polytope as P  # noqa: E402

I2 = np.eye(2)
X = np.array([[0, 1], [1, 0]], complex)
Y = np.array([[0, -1j], [1j, 0]])
Z = np.array([[1, 0], [0, -1]], complex)
J = np.array([[0, -1], [1, 0]], float)                   # HW26: J = (0,-1;1,0)


def kron(*ms):
    r = np.array([[1.0 + 0j]])
    for m in ms:
        r = np.kron(r, m)
    return r


# ------------------------------------------------------------------ функционал 𝒯 (RTW21)

def T_coeffs():
    """coef[(b1,b2), x, z] при S^b_{xz}; x ∈ 1..3, z ∈ 1..6."""
    c = {}
    for b1, b2 in itertools.product((0, 1), repeat=2):
        s1, s2, s12 = (-1) ** b2, (-1) ** b1, (-1) ** (b1 + b2)
        terms = [(1, 1, s1), (1, 2, s1), (2, 1, s2), (2, 2, -s2), (1, 3, s1), (1, 4, s1),
                 (3, 3, -s12), (3, 4, s12), (2, 5, s2), (2, 6, s2), (3, 5, -s12), (3, 6, s12)]
        for x, z, v in terms:
            c[((b1, b2), x, z)] = c.get(((b1, b2), x, z), 0) + v
    return c


COEF = T_coeffs()
BOBS = [(0, 0), (0, 1), (1, 0), (1, 1)]


def T_value(omega, A, F, C):
    """A[x][a] (a ∈ {+1,-1} как индексы 0,1), C[z][c], F[b]; 𝒯 = Σ coef·S^b_{xz}, S = Σ ac P."""
    tot = 0.0
    for (b, x, z), v in COEF.items():
        Fb = F[BOBS.index(b)]
        Oa = A[x][0] - A[x][1]                               # наблюдаемая Σ_a a A_{a|x}
        Oc = C[z][0] - C[z][1]
        tot += v * np.trace(omega @ kron(Oa, Fb, Oc)).real
    return tot


# ------------------------------------------------------------------ комплексная стратегия RTW21 (стр. 328–332)

def renou_complex():
    phi = np.zeros(4, complex); phi[0] = phi[3] = 1 / np.sqrt(2)
    omega = np.kron(np.outer(phi, phi.conj()), np.outer(phi, phi.conj()))   # A B1 ⊗ B2 C
    proj = lambda O: [(I2 + O) / 2, (I2 - O) / 2]  # noqa: E731
    A = {1: proj(Z), 2: proj(X), 3: proj(Y)}
    pairs = [(Z, X), (Z, Y), (X, Y)]
    C = {}
    for k, (si, sj) in enumerate(pairs):
        C[2 * k + 1] = proj((si + sj) / np.sqrt(2))
        C[2 * k + 2] = proj((si - sj) / np.sqrt(2))
    e0, e1 = np.array([1, 0], complex), np.array([0, 1], complex)
    k = lambda a, b: np.kron(a, b)  # noqa: E731
    phip = (k(e0, e0) + k(e1, e1)) / np.sqrt(2)
    phim = (k(e0, e0) - k(e1, e1)) / np.sqrt(2)
    psip = (k(e1, e0) + k(e0, e1)) / np.sqrt(2)       # RTW21: |ψ±⟩ = (|10⟩ ± |01⟩)/√2
    psim = (k(e1, e0) - k(e0, e1)) / np.sqrt(2)
    F = [np.outer(v, v.conj()) for v in (phip, psip, phim, psim)]   # b = 00, 01, 10, 11
    return omega, A, F, C


def marginals_ok(omega, dims):
    """ISO (D12): маргиналы на (A,C) и (B1,B2) максимально смешаны."""
    dA, dB1, dB2, dC = dims
    T = omega.reshape(dims * 2)
    mAC = np.einsum("abcdebcf->adef", T).reshape(dA * dC, dA * dC)     # след по B1, B2
    mB = np.einsum("abcdafgd->bcfg", T).reshape(dB1 * dB2, dB1 * dB2)  # след по A, C
    return (float(np.abs(mAC - np.eye(dA * dC) / (dA * dC)).max()),
            float(np.abs(mB - np.eye(dB1 * dB2) / (dB1 * dB2)).max()))


# ------------------------------------------------------------------ HW: Γ, Γ̄⁽ⁿ⁾ и бинокальная модель

def Ibar(n):
    I_, J_ = np.eye(2), J.copy()
    if n == 1:
        return I_, J_
    Ip, Jp = Ibar(n - 1)
    return 0.5 * (np.kron(Ip, I_) - np.kron(Jp, J_)), 0.5 * (np.kron(Jp, I_) + np.kron(Ip, J_))


def Gamma1(A):
    return np.kron(np.eye(2), A.real) + np.kron(J, A.imag)


def hw_bilocal(omega_c, A, F, C):
    """Вещественная модель HW26 (стр. 521–523 SI): состояние ½Γ̄⁽⁴⁾{ρ⊗σ} на (фазовые ребиты A',B1',B2',C') ⊗ (кубиты),
    эффекты Γ{A}, Γ̄⁽²⁾{B}, Γ{C}. Нормировку фиксируем так, чтобы след = 1, и затем переупорядочиваем подсистемы
    в (A', A)(B1', B1)(B2', B2)(C', C)."""
    I4, J4 = Ibar(4)
    st = np.kron(I4, omega_c.real) + np.kron(J4, omega_c.imag)          # (A'B1'B2'C') ⊗ (A B1 B2 C)
    st = st / np.trace(st).real
    # перестановка: [A',B1',B2',C',A,B1,B2,C] -> [A',A,B1',B1,B2',B2,C',C]
    Tt = st.reshape([2] * 16)
    order = [0, 4, 1, 5, 2, 6, 3, 7]
    Tt = Tt.transpose(order + [o + 8 for o in order])
    omega_r = Tt.reshape(256, 256)
    Ar = {x: [Gamma1(m) for m in A[x]] for x in A}
    Cr = {z: [Gamma1(m) for m in C[z]] for z in C}
    I2b, J2b = Ibar(2)
    Fr = []
    for Fb in F:
        G = np.kron(I2b, Fb.real) + np.kron(J2b, Fb.imag)              # (B1'B2') ⊗ (B1 B2)
        Gt = G.reshape([2] * 8).transpose([0, 2, 1, 3, 4, 6, 5, 7]).reshape(16, 16)  # -> (B1',B1,B2',B2)
        Fr.append(Gt)
    return omega_r, Ar, Fr, Cr


def rebit_terms(omega):
    """Коэффициенты членов J_{A'}J_{C'}, J_{B1'}J_{B2'}, J_{A'}J_{B2'}, J_{B1'}J_{C'} и J⊗4 (остальное — тождество)
    в ω на (A',A)(B1',B1)(B2',B2)(C',C): c = Tr[ω · (оператор)] / Tr[оператор²]."""
    I2r = np.eye(2)
    out = {}
    pats = {"J_A' J_C'": (J, I2r, I2r, J), "J_B1' J_B2'": (I2r, J, J, I2r),
            "J_A' J_B2'": (J, I2r, J, I2r), "J_B1' J_C'": (I2r, J, I2r, J),
            "J_A' J_B1'": (J, J, I2r, I2r), "J_B2' J_C'": (I2r, I2r, J, J), "J⊗4": (J, J, J, J)}
    for name, (a, b1, b2, c) in pats.items():
        Op = kron(a, I2, b1, I2, b2, I2, c, I2).real
        out[name] = float(np.trace(omega @ Op.T).real)
    return out


def oi_violation(omega, dims, rng, trials=200):
    """Операциональная независимость (HW26 стр. 67) по разбиению (A B1)(B2 C): для случайных вещественных
    симметричных X на A⊗B1 и Z на B2⊗C: |Tr[ω X⊗Z] − Tr[ω1 X] Tr[ω2 Z]|."""
    dA, dB1, dB2, dC = dims
    n1, n2 = dA * dB1, dB2 * dC
    T = omega.reshape(n1, n2, n1, n2)
    w1 = np.einsum("ajbj->ab", T)
    w2 = np.einsum("jajb->ab", T)
    worst = 0.0
    for _ in range(trials):
        Xs = rng.normal(size=(n1, n1)); Xs = Xs + Xs.T
        Zs = rng.normal(size=(n2, n2)); Zs = Zs + Zs.T
        lhs = np.trace(omega @ np.kron(Xs, Zs)).real
        rhs = np.trace(w1 @ Xs).real * np.trace(w2 @ Zs).real
        worst = max(worst, abs(lhs - rhs))
    return worst


def main_cal():
    rng = np.random.default_rng(1)
    out = {}
    om, A, F, C = renou_complex()
    out["complex_T"] = T_value(om, A, F, C)
    out["complex_T_expected_6sqrt2"] = 6 * np.sqrt(2)
    out["complex_marginals_dev"] = marginals_ok(om, (2, 2, 2, 2))
    out["complex_alice_ts_constraint"] = [sum(np.trace(A[x][a]).real for x in A) for a in (0, 1)]   # = 3/2·d = 3
    out["complex_charlie_ts_constraint"] = [sum(np.trace(C[z][c]).real for z in C) for c in (0, 1)]  # = 3·d = 6
    out["complex_bob_traces"] = [np.trace(f).real for f in F]                                        # = 1
    omr, Ar, Fr, Cr = hw_bilocal(om, A, F, C)
    dims = (4, 4, 4, 4)
    out["HW_T"] = T_value(omr, Ar, Fr, Cr)
    out["HW_state_min_eig"] = float(np.linalg.eigvalsh((omr + omr.T) / 2).min())
    out["HW_is_real_symmetric"] = bool(np.abs(omr.imag).max() < 1e-12 and np.abs(omr - omr.T).max() < 1e-12)
    out["HW_marginals_dev"] = marginals_ok(omr.real, dims)
    out["HW_rebit_terms"] = rebit_terms(omr.real)
    out["HW_OI_violation"] = oi_violation(omr.real, dims, rng)
    out["HW_ops_real_symmetric"] = bool(all(np.abs(m - m.T).max() < 1e-12 for x in Ar for m in Ar[x]))
    return out, (omr.real, Ar, Fr, Cr)


if __name__ == "__main__":
    res, _ = main_cal()
    print(json.dumps(res, ensure_ascii=False, indent=1, default=float))

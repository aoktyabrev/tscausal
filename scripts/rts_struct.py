"""
RTS stage 0, R.1-калибровки и R.2 (структура): результат в results/json/rts_struct.json.
1) калибровки: комплексная TS-модель → 6√2; ISO-маргиналы; TS-условия операций;
2) допустимость J-членов в ISO для конфигурации A (1 кубит вход/выход), B (2 кубита вход/выход), C (1/1):
   член допустим ⇔ Tr[T (M_A⊗M_B⊗M_C)] = 0 для случайных произведений прямых (TF) и обратных (TB) операций;
3) модель HW26: значение, вещественность, положительность, ОН, маргиналы; проекция на ISO (удаление
   запрещённых маргинальных частей): положительность, ОН, 𝒯;
4) точный SDP: max 𝒯 по ω = ω₁⊗ω₂ + Δ (Δ ∈ Anti⊗Anti, ISO-маргиналы, ω ≥ 0) при операциях и маргиналах HW.
"""
import json
import os
import sys
import time

import cvxpy as cp
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import polytope as P  # noqa: E402
import qproc as Q  # noqa: E402
import rts as R  # noqa: E402
import rts_seesaw as S  # noqa: E402

I2 = np.eye(2)
J = R.J
Xr = np.array([[0, 1], [1, 0]], float)
Zr = np.array([[1, 0], [0, -1]], float)


def rand_choi(din, dout, rng, direction):
    Xm = rng.normal(size=(din * dout, din * dout)) + 1j * rng.normal(size=(din * dout, din * dout))
    M = Xm @ Xm.conj().T
    T = M.reshape(din, dout, din, dout)
    S_ = np.trace(T, axis1=1, axis2=3) if direction == "F" else np.trace(T, axis1=0, axis2=2)
    w, V = np.linalg.eigh(S_)
    L = V @ np.diag(w ** -0.5) @ V.conj().T
    K = np.kron(L, np.eye(dout)) if direction == "F" else np.kron(np.eye(din), L)
    return K @ M @ K.conj().T


def term_allowed(parts, rng, trials=40):
    """parts = [(T_I, T_O)] по сторонам A, B, C (локальные множители на входе и выходе).
    Возвращает (TF-ок, TB-ок): максимум |Π_X Tr[(T_I⊗T_O) M_X]| по случайным операциям."""
    res = {}
    for direction in ("F", "B"):
        worst = 0.0
        for _ in range(trials):
            prod = 1.0
            for TI, TO in parts:
                M = rand_choi(TI.shape[0], TO.shape[0], rng, direction)
                prod *= np.trace(np.kron(TI, TO) @ M)
            worst = max(worst, abs(prod))
        res[direction] = bool(worst < 1e-9)
    return res


def main():
    S.limit_memory(float(os.environ.get("RTS_MEM_GB", "8")))
    t0 = time.time()
    rng = np.random.default_rng(7)
    out = {"stage": "RTS0 struct"}
    cal, (omr, Ar, Fr, Cr) = R.main_cal()
    out["calibration_and_HW"] = cal
    # 2) J-члены: вход B = B_I1⊗B_I2 (4), выход B_O (4)
    one1, one4 = I2, np.eye(4)
    JJ = np.kron(J, J)
    terms = {
        "J^{A_O} J^{B_I1} J^{B_I2} J^{C_O} (4-частичный, J на каждом конце обоих каналов)": [(one1, J), (JJ, one4), (one1, J)],
        "J^{A_O} J^{C_O} (корреляция выходов A и C)": [(one1, J), (one4, one4), (one1, J)],
        "J^{B_I1} J^{B_I2} (корреляция входов Боба)": [(one1, one1), (JJ, one4), (one1, one1)],
        "J^{A_O} J^{B_I2} (перекрёстный: A с портом Чарли)": [(one1, J), (np.kron(I2, J), one4), (one1, one1)],
        "Z^{A_O} J^{B_I1} J^{B_I2} Z^{C_O}": [(one1, Zr), (JJ, one4), (one1, Zr)],
        "X^{A_O} X^{B_I1} (тождественный канал A→B, контроль: допустим)": [(one1, Xr), (np.kron(Xr, I2), one4), (one1, one1)],
        "Z^{A_I} (предселекция A, контроль: запрещён в TB)": [(Zr, one1), (one4, one4), (one1, one1)],
        "Z^{A_O} Z^{C_O} (контроль: запрещён в TF)": [(one1, Zr), (one4, one4), (one1, Zr)],
    }
    tt = {}
    for name, parts in terms.items():
        r = term_allowed(parts, rng)
        tt[name] = {"TF": r["F"], "TB": r["B"], "ISO": bool(r["F"] and r["B"])}
    out["J_terms"] = tt
    # 3) проекция HW на ISO
    dims = (4, 4, 4, 4)

    def proj_iso(w):
        T = w.reshape([4] * 8)
        mAC = np.einsum("abcdebcf->adef", T).reshape(16, 16)
        mB = np.einsum("abcdafgd->bcfg", T).reshape(16, 16)
        dAC, dB = mAC - np.eye(16) / 16, mB - np.eye(16) / 16
        t1 = np.einsum("acdf,be,gh->abgcdehf", dAC.reshape(4, 4, 4, 4), np.eye(4), np.eye(4)).reshape(256, 256) / 16
        t2 = np.einsum("bcef,ad,gh->abcgdefh", dB.reshape(4, 4, 4, 4), np.eye(4), np.eye(4)).reshape(256, 256) / 16
        return w - t1 - t2
    w2 = proj_iso(omr)
    lam = float(np.linalg.eigvalsh(w2).min())
    p_noise = max(0.0, -lam / (-lam + 1 / 256))
    wn = (1 - p_noise) * w2 + p_noise * np.eye(256) / 256
    out["HW_projected_to_ISO"] = {"marginals_dev": R.marginals_ok(w2, dims), "min_eig": lam,
                                  "T": R.T_value(w2, Ar, Fr, Cr), "OI_violation": R.oi_violation(w2, dims, rng),
                                  "white_noise_needed": p_noise, "T_after_noise": R.T_value(wn, Ar, Fr, Cr)}
    # 4) точный SDP по Δ при операциях HW
    print("SDP (256×256)…", flush=True)
    m = S.Model(dims)
    T4 = omr.reshape(16, 16, 16, 16)
    w1 = np.einsum("ajbj->ab", T4)
    wB = np.einsum("jajb->ab", T4)
    G = m.G(Ar, Fr, Cr)
    t1 = time.time()
    D, status, sdp_val = S.solve_state(m, G, w1, wB, np.zeros((m.N, m.N)), "D", True, direct_scs=True)
    om_raw = np.kron(w1, wB) + D
    lam_raw = float(np.linalg.eigvalsh((om_raw + om_raw.T) / 2).min())
    # восстановление допустимости: ω = (1−p) ω_raw + p I/256 (маргиналы остаются ISO, Δ-структура сохраняется)
    p_fix = max(0.0, -lam_raw / (-lam_raw + 1 / 256))
    om_opt = (1 - p_fix) * om_raw + p_fix * np.eye(256) / 256
    out["SDP_fixed_HW_ops"] = {"solver": "SCS", "status": status, "sdp_value": sdp_val,
                               "min_eig_raw": lam_raw, "noise_for_feasibility": p_fix,
                               "T_max": R.T_value(om_opt, Ar, Fr, Cr), "T_product_only": R.T_value(np.kron(w1, wB), Ar, Fr, Cr),
                               "min_eig": float(np.linalg.eigvalsh((om_opt + om_opt.T) / 2).min()),
                               "marginals_dev": R.marginals_ok(om_opt, dims),
                               "OI_violation": R.oi_violation(om_opt, dims, rng, 50),
                               "seconds": round(time.time() - t1, 1)}
    out["seconds"] = round(time.time() - t0, 1)
    with open(os.path.join(P.ROOT, "results", "json", "rts_struct.json"), "w") as fh:
        json.dump(out, fh, ensure_ascii=False, indent=1, default=float)
    print(json.dumps({k: v for k, v in out.items() if k != "calibration_and_HW"}, ensure_ascii=False, indent=1, default=float))


if __name__ == "__main__":
    main()

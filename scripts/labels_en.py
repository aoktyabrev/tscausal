"""
English labels for the Russian strings stored inside results/json/*.json.

The stage scripts were written in Russian and emit Russian labels into their result files. Those files are
the output of the computations and are never edited by hand, so the translation happens at render time:
`make_results.py` maps every string through this table while loading, and the report comes out in English.
Numbers are never touched — only labels.

A string that is missing here is left as it is, and `make_results.py` reports it, so a new Russian label
cannot slip into the report unnoticed.
"""

LABELS = {
    # --- stage A / B: modes, kinds, provenance
    "смешанное": "mixed",
    "общее": "common",
    "направленное вперёд": "forward-directed",
    "направленное назад": "backward-directed",
    "подтверждено цитатой": "confirmed by quotation",
    "полная инверсия {1, inv}": "full inversion {1, inv}",
    "диагональные инверсии (fI = fO)": "diagonal inversions (fI = fO)",
    "S3 (перестановки)": "S3 (permutations)",
    "Z2^6 (все инверсии)": "Z2^6 (all inversions)",
    "4 из 8": "4 of 8",
    "вне U2-оболочки значение зависит от выбранного представителя":
        "outside the U2 hull the value depends on the chosen representative",
    "фасета f: sum(f[i]*p[i]) <= f[-1]; проекция на aff(P_TS)":
        "facet f: sum(f[i]*p[i]) <= f[-1]; projection onto aff(P_TS)",
    "крайние точки H-описания (ур. (3),(4) | (5),(6) + p>=0 + Σp=1 + U2) через cdd.gmp "
    "(P.vertices_cdd в stage_b.py); детерминированные схемы — только перекрёстная проверка":
        "extreme points of the H-description (Eqs. (3),(4) | (5),(6) + p>=0 + Σp=1 + U2) via cdd.gmp "
        "(P.vertices_cdd in stage_b.py); deterministic schemes are used only as a cross-check",
    "arXiv:1508.01704, Sec. III A and App. A (цитаты в SOURCES.md)":
        "arXiv:1508.01704, Sec. III A and App. A (quotations in SOURCES.md)",
    "causal_polytope_calib.py использует `import cdd`, в pycddlib 3.x это float-бэкенд (Fraction -> float). "
    "Ниже те же числа воспроизведены в точной арифметике через cdd.gmp.":
        "causal_polytope_calib.py uses `import cdd`, which in pycddlib 3.x is the float backend "
        "(Fraction -> float). The same numbers are reproduced below in exact arithmetic via cdd.gmp.",
    "КАНДИДАТ: смешанный класс вне K, переживший U1 и подтверждённый в обоих построениях: "
    "class_1_size32, class_3_size16":
        "CANDIDATE: a mixed class outside K that survived U1 and was confirmed in both constructions: "
        "class_1_size32, class_3_size16",
    "НОВЫЙ, НО НЕНАПРАВЛЕННЫЙ: классы вне K есть, все G'-эквивалентны своему обращению":
        "NEW BUT UNDIRECTED: classes outside K do exist, and every one of them is G'-equivalent to its "
        "own reversal",
    "РАЗВЕДКА: оболочка схем усечена по размерностям; классы ниже не являются результатом, если "
    "cumulative_extreme_points_AB не стабилизировалось":
        "EXPLORATION: the hull of the schemes is truncated in dimension; the classes below are not a result "
        "unless cumulative_extreme_points_AB has stabilised",
    "вершин: 112\nравенств (нормировка): 4  нетривиальных фасет: 36\n"
    "GYNI  причинный максимум: 1/2 (ожидание 1/2) OK\n"
    "LGYNI причинный максимум: 3/4 (ожидание 3/4) OK\n\n"
    "ВНИМАНИЕ: сырые фасеты из cdd НЕ классифицированы. Из-за равенств\n"
    "нормировки одно и то же неравенство имеет много представлений —\n"
    "без канонизации по модулю аффинной оболочки счёт «классов» является\n"
    "артефактом представления, а не результатом (см. Stage B в спеке).\n":
        "vertices: 112\nequalities (normalisation): 4  non-trivial facets: 36\n"
        "GYNI  causal maximum: 1/2 (expected 1/2) OK\n"
        "LGYNI causal maximum: 3/4 (expected 3/4) OK\n\n"
        "WARNING: the raw facets from cdd are NOT classified. Because of the\n"
        "normalisation equalities the same inequality has many representations —\n"
        "without canonicalisation modulo the affine hull, a count of \"classes\" is\n"
        "an artefact of the representation, not a result (see Stage B in the spec).\n",
    # --- stage C / D: schemes and processes
    "M[(доход, исход)]; W на A_I⊗A_O⊗B_I⊗B_O": "M[(income, outcome)]; W on A_I⊗A_O⊗B_I⊗B_O",
    "x=a, y=a⊕b, (a,b) равномерно": "x=a, y=a⊕b, with (a,b) uniform",
    "N1/N2 не нарушаются в R; нарушены только классы замыкания: "
    "{\"d2_cl3\": [\"P1_BA\", \"P4_R\", \"P3_common\"], \"d2_cl4\": [\"P1_AB\", \"P4_R\", \"P3_common\"], "
    "\"d2_cl5\": [\"P1_AB\", \"P1_BA\", \"P4_R\", \"P3_common\"], "
    "\"d2_cl6\": [\"P1_AB\", \"P1_BA\", \"P4_R\", \"P3_common\"]}":
        "N1/N2 are not violated in R; only the closure classes are violated: "
        "{\"d2_cl3\": [\"P1_BA\", \"P4_R\", \"P3_common\"], \"d2_cl4\": [\"P1_AB\", \"P4_R\", \"P3_common\"], "
        "\"d2_cl5\": [\"P1_AB\", \"P1_BA\", \"P4_R\", \"P3_common\"], "
        "\"d2_cl6\": [\"P1_AB\", \"P1_BA\", \"P4_R\", \"P3_common\"]}",
    # --- T3
    "T3.0 разведка: W*": "T3.0 exploration: W*",
    "LP по многограннику ISO_3 для каждой из 24^3 троек TS-биекций":
        "an LP over the ISO_3 polytope for each of the 24^3 triples of TS bijections",
    "у всех трёх: (доход a, вход i) → (исход x = i, выход = a)":
        "for all three: (income a, input i) → (outcome x = i, output = a)",
    "1403.7333 стр. 276–286; 1507.01714 E_ex1": "1403.7333 lines 276–286; 1507.01714 E_ex1",
    "TC20 стр. 338–343 (= AGB17 стр. 334 при n = 4); игра — AGB17 стр. 350–366":
        "TC20 lines 338–343 (= AGB17 line 334 for n = 4); the game is AGB17 lines 350–366",
    # --- RTS: J-terms
    "J^{A_O} J^{B_I1} J^{B_I2} J^{C_O} (4-частичный, J на каждом конце обоих каналов)":
        "J^{A_O} J^{B_I1} J^{B_I2} J^{C_O} (four-party, J at each end of both channels)",
    "J^{A_O} J^{C_O} (корреляция выходов A и C)":
        "J^{A_O} J^{C_O} (correlation between the outputs of A and C)",
    "J^{B_I1} J^{B_I2} (корреляция входов Боба)": "J^{B_I1} J^{B_I2} (correlation between Bob's inputs)",
    "J^{A_O} J^{B_I2} (перекрёстный: A с портом Чарли)":
        "J^{A_O} J^{B_I2} (cross term: A with Charlie's port)",
    "X^{A_O} X^{B_I1} (тождественный канал A→B, контроль: допустим)":
        "X^{A_O} X^{B_I1} (identity channel A→B, control: allowed)",
    "Z^{A_I} (предселекция A, контроль: запрещён в TB)":
        "Z^{A_I} (preselection on A, control: forbidden in TB)",
    "Z^{A_O} Z^{C_O} (контроль: запрещён в TF)": "Z^{A_O} Z^{C_O} (control: forbidden in TF)",
    "I (без J)": "I (no J)",
    "без (A,C)-отклонения [J_A'J_C'…]": "without the (A,C) deviation [J_A'J_C'…]",
    "без (B1,B2)-отклонения [J_B1'J_B2'…]": "without the (B1,B2) deviation [J_B1'J_B2'…]",
    "без обоих": "without both",
    # --- RTS: stage names
    "RTS0 (4,4,4,4) финальная точка": "RTS0 (4,4,4,4) final point",
    "RTS1 S.1 скан по размерности": "RTS1 S.1 dimension scan",
    "RTS1 S.1 скан (GPU, ADMM)": "RTS1 S.1 scan (GPU, ADMM)",
    "RTS1 S.2 сертификаты при найденных операциях":
        "RTS1 S.2 certificates at the operations that were found",
    "RTS1 S.2 двойственные сертификаты (ADMM на GPU) при найденных операциях":
        "RTS1 S.2 dual certificates (ADMM on GPU) at the operations that were found",
    # --- RTS: scan bookkeeping
    "холодный": "cold",
    "тёплый": "warm",
    "отказ солвера": "solver failure",
    "первый прогон (тёплый от d=4 + 5 холодных)": "first run (warm start from d=4 plus 5 cold starts)",
    "добор с другим зерном (5 холодных)": "top-up run with a different seed (5 cold starts)",
    "CPU/SCS-скан при (4,4,4,4) прерван по требованию освободить ресурсы; используется как независимая "
    "сверка качества оценщика, не как результат скана":
        "the CPU/SCS scan at (4,4,4,4) was interrupted on request to free up resources; it is used as an "
        "independent check on the quality of the estimator, not as a result of the scan",
    # --- RTS: d=8 resource ceiling
    "почему не 5 стартов": "why not 5 starts",
    "один тёплый старт занял 20091 с (5,6 ч) при бюджете 4,5 ч на размерность; холодные старты в бюджет "
    "суток не помещаются":
        "a single warm start took 20091 s (5.6 h) against a budget of 4.5 h per dimension; cold starts do "
        "not fit into the one-day budget",
    "PSD-блок N": "PSD block N",
    "коэффициентов Δ (плотный базис, не используется в GPU-пути)":
        "number of Δ coefficients (dense basis, not used on the GPU path)",
    "eigh(4096) на GPU": "eigh(4096) on GPU",
    "eigh(4096) на CPU": "eigh(4096) on CPU",
    "итераций ADMM на шаг": "ADMM iterations per step",
    "шагов по состоянию за итерацию see-saw": "state steps per see-saw iteration",
    "видеопамять процесса": "GPU memory used by the process",
    "невязки ADMM на последнем шаге": "ADMM residuals at the last step",
    "оценка значения": "value obtained",
    "0.88 с": "0.88 s",
    "4.77 с": "4.77 s",
    "~7 ГБ из 12 (пик по nvidia-smi 10.4 ГБ вместе с фоном рабочего стола)":
        "~7 GB out of 12 (nvidia-smi peak 10.4 GB including the desktop in the background)",
    "primal 1.7e-05, dual 1.6e-04 (не сошёлся)": "primal 1.7e-05, dual 1.6e-04 (not converged)",
    "5.753181 — не представительно: только тёплый старт, ADMM недосошёлся, очистка потребовала шума 7.7e-03":
        "5.753181 — not representative: warm start only, ADMM under-converged, and the cleanup needed noise "
        "of 7.7e-03",
    "потолок по ресурсам зафиксирован числами; экстраполяция не применялась":
        "the resource ceiling is recorded as numbers; no extrapolation was used",
    # --- RTS: GPU estimator calibration
    "проекция Π_Δ: принадлежность Anti⊗Anti": "projection Π_Δ: membership in Anti⊗Anti",
    "проекция Π_Δ: маргиналы": "projection Π_Δ: marginals",
    "проекция Π_Δ: ортогональность": "projection Π_Δ: orthogonality",
    "шаг Δ при операциях HW: SCS": "Δ step at the HW operations: SCS",
    "шаг Δ при операциях HW: ADMM-GPU": "Δ step at the HW operations: ADMM on GPU",
    "расхождение ADMM и SCS": "discrepancy between ADMM and SCS",
    "(2,2,2,2): найденные значения": "(2,2,2,2): values found",
    "(2,2,2,2): совпадение с известным значением": "(2,2,2,2): agreement with the known value",
    "eigh: GPU / откат на CPU": "eigh: on GPU / fallback to CPU",
    "4.24264068 (2.9 с), ISO 6.7e-14": "4.24264068 (2.9 s), ISO 6.7e-14",
    "4.24264065 (18.9 с), ISO 4.4e-16, невязки 8.1e-10 / 6.4e-10":
        "4.24264065 (18.9 s), ISO 4.4e-16, residuals 8.1e-10 / 6.4e-10",
    "5.5e-05 (после очистки)": "5.5e-05 (after cleanup)",
    # --- S.2: why Clarabel is unusable
    "аварийный выход процесса (SIGABRT): запрос 4 328 718 848 байт одним блоком при лимите "
    "RLIMIT_AS = 13 ГБ. Это плотный блок гессиана PSD-конуса svec(256); отказ происходит в аллокаторе Rust "
    "и не перехватывается как MemoryError. Сверка внутренне-точного решателя с первопорядковым сделана "
    "при d = 2, где Clarabel отработал.":
        "the process aborted (SIGABRT) while requesting 4,328,718,848 bytes in a single block under the "
        "limit RLIMIT_AS = 13 GB. That is the dense Hessian block of the PSD cone svec(256); the failure "
        "happens inside the Rust allocator and is not caught as a MemoryError. The interior-point solver was "
        "cross-checked against the first-order one at d = 2, where Clarabel did run.",
}

_SCHEME = ("порядок {order}: тождественный канал; Алиса отбрасывает вход, исход x равновероятен, готовит "
           "собственное состояние Z/X-базиса: базис = x (x=0 → Z, x=1 → X), значение бита = "
           "a ⊕ 0·[x=0] ⊕ 0·[x=1]; Боб измеряет вдоль (Z ± X)/√2 (знак для b=0: {s0}, для b=1: {s1}), "
           "исход y ⊕ ({t}, {u})[b]; выход Боба — максимально смешанный")
_SCHEME_EN = ("order {order}: identity channel; Alice discards her input, her outcome x is uniform, and she "
              "prepares an eigenstate of the Z/X basis: basis = x (x=0 → Z, x=1 → X), bit value = "
              "a ⊕ 0·[x=0] ⊕ 0·[x=1]; Bob measures along (Z ± X)/√2 (sign for b=0: {s0}, for b=1: {s1}), "
              "outcome y ⊕ ({t}, {u})[b]; Bob's output is maximally mixed")
for _order in ("AB", "BA"):
    for _s0, _s1 in (("+", "−"), ("−", "+")):
        for _t, _u in (("1", "0"), ("1", "1")):
            LABELS[_SCHEME.format(order=_order, s0=_s0, s1=_s1, t=_t, u=_u)] = \
                _SCHEME_EN.format(order=_order, s0=_s0, s1=_s1, t=_t, u=_u)


def translate(obj, missing):
    """Recursively map every Russian string (key or value) through LABELS; unknown ones are collected."""
    if isinstance(obj, dict):
        return {translate(k, missing): translate(v, missing) for k, v in obj.items()}
    if isinstance(obj, list):
        return [translate(v, missing) for v in obj]
    if isinstance(obj, str) and any("а" <= c.lower() <= "я" or c in "ёЁ" for c in obj):
        if obj in LABELS:
            return LABELS[obj]
        missing.add(obj)
    return obj

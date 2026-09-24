# tscausal — временна́я симметрия без селекции: что она запрещает и что нет

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.22937438.svg)](https://doi.org/10.5281/zenodo.22937438)
[![License: Apache-2.0](https://img.shields.io/badge/code-Apache--2.0-blue.svg)](LICENSE)
[![License: CC BY 4.0](https://img.shields.io/badge/docs-CC%20BY%204.0-lightgrey.svg)](LICENSE-docs)

Вычислительное исследование временно-симметричных процессных матриц (формализм Mrini–Hardy,
[arXiv:2406.18489](https://arxiv.org/abs/2406.18489)) в режиме **без пред- и постселекции**.
Три сюжета: строение временно-симметричного многогранника, классический некаузальный процесс на трёх
сторонах и лазейка вещественной квантовой механики Hoffreumon–Woods в этом режиме.

Все числа порождаются скриптами, каждая стадия запечатана предрегистрацией **до** первого прогона,
`RESULTS.md` никогда не пишется руками.

---

## Summary (English)

Time-symmetric process matrices without pre-/postselection (Mrini–Hardy formalism), studied computationally.

**Proven here (with certificates, not just numerics):**
- **Lemma D6.** With the global past/future marginalised, every bipartite process of the formalism reduces to
  a mixture of one-way channels: nothing in the formalism violates the facets N1, N2 of the time-symmetric
  polytope, in any dimension. Allowing preselection, the same facets are violated by a *causally ordered*
  process — so N1/N2 witness nothing about indefiniteness in either regime.
- **Lemma D8.** A time-symmetric definite-order process without selection is exactly a Bell scenario on a
  maximally entangled state with outcomes and incomes swapping the usual roles; the quantum-classical gap on
  classes cl3–cl6 is CHSH and the Tsirelson bound in relabelled roles.
- **Witness W\*** ∈ ISO₃ — a classical, causally non-separable three-party process without selection, built as
  ½(Lugano + its full inversion); it violates the published inequalities I₁ (15/16) and I₃ (1) of Abbott et al.
  An implicit precedent (W₃ of Baumeler–Feix–Wolf, 1403.7333) is documented in RESULTS.md.
- **Real-QM loophole.** The Hoffreumon–Woods construction ([arXiv:2603.19208](https://arxiv.org/abs/2603.19208))
  does **not** transfer into the time-symmetric class ISO: at its own operations, the maximum of Renou's
  functional 𝒯 over *all* real ISO processes is certified (dual point + Cholesky) to be
  **≤ 4.24264070 = 3√2**, exactly half of the complex value 6√2 — and operational independence is not even
  required for that bound.

**Open (in a checkable form):** is there a real ISO process with operational independence, and operations,
giving 𝒯 > 7.6605 (Renou's real bound)? A dimension scan up to d = 8 reached only 6.927206.

---

## Что доказано и что открыто

| | результат | где |
|---|---|---|
| ✔ | **D6:** без селекции двусторонние процессы — смесь односторонних каналов; N1, N2 не нарушаются ни при каких размерностях | `RESULTS.md` § Stage C |
| ✔ | **D6, обратная сторона:** с предселекцией N1 и N2 нарушает уже процесс с определённым порядком | § Stage C |
| ✔ | **D8:** TS-процесс с определённым порядком без селекции ≡ Белл на максимально запутанном состоянии; разрыв cl3–cl6 — это CHSH и граница Цирельсона | § Stage D |
| ✔ | **W\* ∈ ISO₃** — классический причинно-неразделимый процесс без селекции, нарушает I₁ и I₃ | § T3.0, T3.1 |
| ✔ | **Сертификат 3√2** при операциях Hoffreumon–Woods, для всех вещественных ISO-состояний | § RTS stage 0 |
| ✔ | **Механизм:** из ISO конструкцию HW выводят члены J_A′J_C′ (запрещён в TF) и J_B1′J_B2′ (запрещён в TB) | § RTS stage 0 |
| ✖ | **Верхняя оценка при свободных операциях** — не получена (задача по операциям невыпуклая) | § RTS stage 1, S.2 |
| ✖ | Полное перечисление ISO₃ с составным входом — не делалось (работа шла внутри сетевой формы D12) | § RTS stage 1, S.3 |

Итог по вещественной КМ: рост размерности, который в модели HW и даёт весь эффект, здесь не прибавляет
ничего — 6.828 (d = 2), 6.927 (d = 4), 6.873 (d = 6) при пороге 7.6605. Это **численное свидетельство**, а не
доказательство; строгий критерий плато, записанный в предрегистрации, не выполнен.

## Стадии

| стадия | о чём | предрегистрация |
|---|---|---|
| A | ворота точности: точная арифметика, сверка перечислителей (`cdd.gmp`, `lrs`), калибровка канонизатора | — |
| B | временно-симметричный многогранник Def-II: вершины, фасеты, классы | `PREREGISTRATION.md` |
| B.2 | приписываемость, происхождение вершин, чувствительность к равномерности, замыкание | `PREREGISTRATION_B2.md` |
| C | нарушают ли N1 и N2 физически осмысленные процессы (лемма D6) | `PREREGISTRATION_C.md` |
| D | квантово-классический разрыв на cl3–cl6 (лемма D8, NPA) | `PREREGISTRATION_D.md` |
| T3.0 | три стороны без селекции: свидетель W\* | `PREREGISTRATION_T3.md` |
| T3.1 | структура W\*, «зеркала», перебор, отрицательный результат при N = 4 | `PREREGISTRATION_T31.md` |
| RTS 0 | перевод бинокального сценария Renou в TS без селекции; модель HW; сертификат 3√2 | `PREREGISTRATION_RTS0.md` |
| RTS 1 | скан по размерности d = 2, 4, 6, 8; двойственные сертификаты; свод ветки | `PREREGISTRATION_RTS1.md` |

Подробности, числа, калибровки, провалившиеся антивакуумные тесты и **все отклонения** — в `RESULTS.md`.

## Правила, по которым велась работа

1. **Правило 0.** Любое внешнее число, определение или формула попадает в работу только с дословной цитатой в
   `SOURCES.md` (arXiv id, номер строки или уравнения). Иначе — помечается как «не подтверждено».
2. **Предрегистрация.** Прогнозы исполнителя и архитектора с числами и уверенностью фиксируются в
   `PREREGISTRATION*.md` и коммитятся **отдельным коммитом до первого прогона стадии**.
3. **`RESULTS.md` порождается** скриптом `scripts/make_results.py` из `results/json/`, руками не редактируется.
4. **Антивакуумные тесты.** Каждый оценщик калибруется на задаче, где он обязан провалиться или где ответ
   известен заранее (например, комплексный see-saw обязан находить 6√2).
5. **Нарушения засчитываются** только после независимого пересчёта в точной или расширенной точности, а для
   верхних оценок — только с сертификатом (двойственная точка + разложение Холецкого).

### Проверка предрегистраций

SHA-256 содержимого файлов (не зависят от переписывания истории):

```
582087467b4e771c…  PREREGISTRATION.md        (Stage B)
8dc8816e9c771698…  PREREGISTRATION_B2.md     (Stage B.2)
9e5c6a8ec8554b5a…  PREREGISTRATION_C.md      (Stage C)
c6052f4a648af321…  PREREGISTRATION_D.md      (Stage D)
104252146fb728ee…  PREREGISTRATION_T3.md     (T3.0)
528b192d2d442ddf…  PREREGISTRATION_T31.md    (T3.1)
10006240768c1ce5…  PREREGISTRATION_RTS0.md   (RTS 0)
b9a3e4bc404e00e2…  PREREGISTRATION_RTS1.md   (RTS 1)
```

Полные значения и автоматическая сверка (файл на диске ↔ версия в коммите предрегистрации) — в таблице
в начале `RESULTS.md`, порождаемой `scripts/make_results.py`. Вручную:

```bash
sha256sum PREREGISTRATION*.md
git log --diff-filter=A --format='%h %ad %s' --date=short -- PREREGISTRATION_RTS1.md
```

Порядок коммитов показывает, что предрегистрация каждой стадии запечатана раньше её первого прогона.

## Воспроизведение

```bash
micromamba create -p .env -c conda-forge python=3.12 cddlib gmp lrslib pip pypdf cython setuptools compilers
CFLAGS="-I$PWD/.env/include" LDFLAGS="-L$PWD/.env/lib -Wl,-rpath,$PWD/.env/lib" \
  .env/bin/python -m pip install --no-build-isolation "pycddlib>=3,<4"
.env/bin/python -m pip install cvxpy clarabel scs mpmath sympy
.env/bin/python -m pip install torch --index-url https://download.pytorch.org/whl/cu128   # для стадии RTS 1
bash scripts/run_all.sh
```

Версии, на которых получены опубликованные числа: Python 3.12.14, numpy 2.5.3, scipy 1.18.1, cvxpy 1.9.3,
pycddlib 3.0.2 (собран против `.env`), torch 2.11.0+cu128.

**Железо и время.** Всё, кроме стадии RTS 1, считается на CPU (использовалось 8 ядер, 24 ГБ ОЗУ): Stage A–D
около 1,5 ч, T3 около 1,5 ч, RTS 0 около 10 ч. Стадия RTS 1 использует GPU (NVIDIA RTX 4070 Ti, 12 ГБ):
скан по размерности — 18,8 ч. Без GPU те же скрипты работают, но размерности 6 и 8 недосягаемы: при N = 1296
один шаг по состоянию в SCS занимает около 350 с против секунд у ADMM на GPU.

**Ограничения по памяти.** Каждый скрипт ставит себе `RLIMIT_AS` (переменная `RTS_MEM_GB`); расчёты
запускаются строго по одному. Это следствие реального сбоя: плотный базис Δ на 7,5 ГБ вместе с параллельным
прогоном исчерпал память машины. Внутренне-точный решатель Clarabel неприменим при N ≥ 256 — он требует
плотный блок гессиана PSD-конуса (запрос 4,33 ГБ одним куском).

## Данные

- `results/json/*.json` — все числа, из которых порождается `RESULTS.md`.
- `results/*.npz` — найденные точки (состояния и операции) для размерностей d = 2, 4, 6.
- Точка при d = 8 (`rts_gpu_8.npz`, 129 МБ) в репозиторий не входит из-за размера; она приложена отдельным
  файлом к записи на Zenodo ([10.5281/zenodo.22937438](https://doi.org/10.5281/zenodo.22937438)).
  Воспроизводится скриптом `scripts/rts_gpu_scan.py`.

## Сторонние материалы

Во время работы использовались полные тексты и исходники сторонних статей (arXiv). **Они не входят в
репозиторий**: их лицензии не позволяют перераспространение. В `SOURCES.md` приведены только короткие
дословные фрагменты с точными ссылками (arXiv id, номер строки или уравнения), достаточные для проверки
каждого заимствованного числа; авторские права на эти фрагменты принадлежат их правообладателям.
Собственные отчёты проверки литературы сохранены: `sources/*/REPORT.md`.

## История коммитов

История переписана `git filter-repo`, чтобы убрать из неё сторонние статьи. **Порядок, даты и сообщения
коммитов сохранены**, изменились только их хеши. Соответствие старых и новых хешей — в `COMMIT-MAP.txt`;
поля `commit_before_history_rewrite` в `results/json/prereg.json` хранят прежние значения. Полный бандл
исходной истории сохранён автором вне публикации.

Ключевой момент: SHA-256 предрегистраций — это хеши **содержимого файлов**, переписывание истории их не
меняет. Проверка «тот ли это файл» остаётся полной; перепривязана только ссылка на коммит.

## Лицензии

- **Код** (`scripts/`) — Apache-2.0, см. `LICENSE`.
- **Тексты, таблицы и данные** (`RESULTS.md`, `SOURCES.md`, `PREREGISTRATION*.md`, `PROMPT*.md`, `SPEC*.md`,
  `sources/*/REPORT.md`, `results/`) — CC BY 4.0, см. `LICENSE-docs`.
- Цитаты из сторонних работ в `SOURCES.md` — под авторским правом их правообладателей.

## Как цитировать

Запись на Zenodo: **[10.5281/zenodo.22937438](https://doi.org/10.5281/zenodo.22937438)** — это concept DOI,
он всегда ведёт на последнюю версию. В тексте статьи указывайте версионный DOI конкретного релиза
(v1.0.0 — [10.5281/zenodo.22937439](https://doi.org/10.5281/zenodo.22937439)).

```bibtex
@software{oktyabrev_tscausal_2026,
  author    = {Oktyabrev, Artem},
  title     = {tscausal: time-symmetric process matrices without selection},
  year      = {2026},
  publisher = {Zenodo},
  version   = {1.0.0},
  doi       = {10.5281/zenodo.22937438},
  url       = {https://doi.org/10.5281/zenodo.22937438}
}
```

Машиночитаемая форма — `CITATION.cff` (GitHub показывает кнопку «Cite this repository»).

## Раскрытие об использовании ИИ

Постановка задач, спецификации стадий и критерии приёмки прорабатывались автором в диалоге с Claude
(Anthropic). Реализация — код, расчёты, тексты отчётов — выполнена через Claude Code (модель Claude Opus 5);
соответствующие коммиты несут трейлер `Co-Authored-By: Claude Opus 5`. Claude и Claude Code — инструменты, а
не соавторы. Ответственность за результаты несёт автор. Защита от типичных ошибок такого режима работы
встроена в процесс: предрегистрация прогнозов до прогонов, обязательные антивакуумные тесты, порождение
`RESULTS.md` скриптом, сертификаты для каждой верхней оценки и полный список отклонений в отчёте.

# Литчек: перечисление фасет временно-симметричного причинного многогранника (MH24, arXiv:2406.18489)

Дата: 2026-09-21. Выполнен субагентом, счётчики grep по e-print для 2508.02463,
2603.12283, 2403.02749 перепроверены вручную (совпали). Сырые выгрузки — в этой папке
(`<id>/abs.html`, `<id>/src/`, `arxiv_search/q*.xml`, `s2_citations*.json`, `openalex_work.json`).

## Вердикт
Среди 8 статей, проверенных в полном тексте (e-print), **не найдено перечисления фасет
временно-симметричного многогранника MH24 или эквивалентного объекта**, и нет новых
неравенств, смешивающих направления времени. Оговорки: arXiv API ищет только по
заголовку и аннотации; Semantic Scholar/OpenAlex могут не видеть свежих ссылок;
Google Scholar напрямую не опрашивался.

## Поиск (arXiv API, totalResults)
q1 all:"time-symmetric" AND all:"causal inequalit*" — 0; q2 all:"time symmetric" AND
all:"causal inequality" — 1 (сама 2406.18489); q3 abs:"causal inequalities" AND abs:time AND
abs:symmetr* — 1 (сама); q4 abs:"indefinite time direction" — 7 (не о неравенствах);
q5 abs:"double causality" — 1 (2104.00071, Hardy 2021); q6 abs:"time-symmetric" AND
abs:"indefinite causal" — 5; q7 abs:"causal polytope" — 3 (все до 2024); q8
abs:"time-symmetric operational" — 4; q9 abs:"bidirectional" AND abs:"causal inequalit*" — 0;
q10 au/abs Mrini — 20 (релевантна только 2406.18489); q11 abs:"causal inequalities" AND
abs:"facets" — 4 (2015–2017); q12 abs:"quantum time flip" — 6; q13 indefinite time/direction
— 8; q14 abs:"causal inequalit(y|ies)" — 47, из них 13 после 2024-06, ни одна не о
временной симметрии; q15 input-output indefinite/direction — 7; q16 abs:"time symmetry" AND
abs:"process matri*" — 0; q17 abs:"time-symmetric" AND abs:"causal order" — 7.
Semantic Scholar: 2 цитирующие (2603.11221, 2602.23865); OpenAlex: 0.

## Цитирующие / близкие работы
| arXiv | Название | Фасеты TS-многогранника? |
|---|---|---|
| 2603.11221 | Higher-Order Quantum Objects are Strong Profunctors | нет (facet/polytope: 0) |
| 2602.23865 | Supermaps on generalised theories | нет (facet/polytope: 0) |
| 2602.00856 | Higher-order transformations of bidirectional quantum processes | нет (MH24 только в .bib) |
| 2508.02463 | An equivalence between time-symmetry and cyclic causality in quantum theory (Jean, Silva, Vilasini) | нет: facet 0, polytope 0, GYNI 0, income 0 |
| 2603.12283 | Emergent causal order and time direction: bridging causal models and tensor networks (Ferradini, Mazzola, Vilasini) | нет: все шесть терминов — 0 |
| 2403.02749 | Tsirelson bounds for quantum correlations with indefinite causal order (Liu, Chiribella) | нет: 2 упоминания facet — про обычный (прямой) многогранник B15 |
| 2506.04607 | A map of indefinite causal order | нет доходов, MH24 не цитирует |
| 2511.14192 | Entropic uncertainty under indefinite causal order and input-output direction | 0 по всем терминам |

Дословно, 2403.02749 `arXiv.tex` стр. 811:
> The condition (\ref{eq:polytope2}) is the causal inequality associated with the canonical LGYNI game, which corresponds to a facet of the causal polytope \cite{branciard2015simplest}.

Дословно, 2508.02463, аннотация:
> We prove that for every (possibly mixed) MTS, there exists an operationally equivalent time-labelled P-CTC assisted comb, and vice versa.

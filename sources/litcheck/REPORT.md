# Literature check: facet enumeration of the time-symmetric causal polytope (MH24, arXiv:2406.18489)

Date: 2026-09-21. Carried out by a subagent; the grep counters over the e-prints for 2508.02463,
2603.12283, 2403.02749 were re-checked by hand (they matched). The raw dumps are in this folder
(`<id>/abs.html`, `<id>/src/`, `arxiv_search/q*.xml`, `s2_citations*.json`, `openalex_work.json`).

## Verdict
Among the 8 papers checked in full text (e-print), **no enumeration of the facets of the
time-symmetric MH24 polytope or of an equivalent object was found**, and there are no new
inequalities mixing the directions of time. Caveats: the arXiv API searches only over
title and abstract; Semantic Scholar/OpenAlex may fail to see recent references;
Google Scholar was not queried directly.

## Search (arXiv API, totalResults)
q1 all:"time-symmetric" AND all:"causal inequalit*" — 0; q2 all:"time symmetric" AND
all:"causal inequality" — 1 (2406.18489 itself); q3 abs:"causal inequalities" AND abs:time AND
abs:symmetr* — 1 (itself); q4 abs:"indefinite time direction" — 7 (not about inequalities);
q5 abs:"double causality" — 1 (2104.00071, Hardy 2021); q6 abs:"time-symmetric" AND
abs:"indefinite causal" — 5; q7 abs:"causal polytope" — 3 (all before 2024); q8
abs:"time-symmetric operational" — 4; q9 abs:"bidirectional" AND abs:"causal inequalit*" — 0;
q10 au/abs Mrini — 20 (only 2406.18489 is relevant); q11 abs:"causal inequalities" AND
abs:"facets" — 4 (2015–2017); q12 abs:"quantum time flip" — 6; q13 indefinite time/direction
— 8; q14 abs:"causal inequalit(y|ies)" — 47, of which 13 after 2024-06, none of them about
time symmetry; q15 input-output indefinite/direction — 7; q16 abs:"time symmetry" AND
abs:"process matri*" — 0; q17 abs:"time-symmetric" AND abs:"causal order" — 7.
Semantic Scholar: 2 citing papers (2603.11221, 2602.23865); OpenAlex: 0.

## Citing / nearby works
| arXiv | Title | Facets of the TS polytope? |
|---|---|---|
| 2603.11221 | Higher-Order Quantum Objects are Strong Profunctors | no (facet/polytope: 0) |
| 2602.23865 | Supermaps on generalised theories | no (facet/polytope: 0) |
| 2602.00856 | Higher-order transformations of bidirectional quantum processes | no (MH24 only in the .bib) |
| 2508.02463 | An equivalence between time-symmetry and cyclic causality in quantum theory (Jean, Silva, Vilasini) | no: facet 0, polytope 0, GYNI 0, income 0 |
| 2603.12283 | Emergent causal order and time direction: bridging causal models and tensor networks (Ferradini, Mazzola, Vilasini) | no: all six terms — 0 |
| 2403.02749 | Tsirelson bounds for quantum correlations with indefinite causal order (Liu, Chiribella) | no: 2 mentions of facet — about the ordinary (forward) B15 polytope |
| 2506.04607 | A map of indefinite causal order | no incomes, does not cite MH24 |
| 2511.14192 | Entropic uncertainty under indefinite causal order and input-output direction | 0 on all terms |

Verbatim, 2403.02749 `arXiv.tex` p. 811:
> The condition (\ref{eq:polytope2}) is the causal inequality associated with the canonical LGYNI game, which corresponds to a facet of the causal polytope \cite{branciard2015simplest}.

Verbatim, 2508.02463, abstract:
> We prove that for every (possibly mixed) MTS, there exists an operationally equivalent time-labelled P-CTC assisted comb, and vice versa.

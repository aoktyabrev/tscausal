# Literature check D (2026-09-21)

Carried out by a subagent; the key quotations (the AB26 lemma, BTCV04, FR10, NPA08) were re-checked by hand with grep.
Note: the arXiv numbers of Oreshkov–Cerf: 1406.3829 = "Operational quantum theory without predefined time",
1507.07745 = "Operational formulation of time reversal in quantum theory".

## F1 (lemma D6: ISO-processes are mixtures of one-way channels)
- MH24: not stated. There is only the example of an ISO-process as a "single quantum channel from Alice to Bob"
  and the phrase that "more complicated combinations ... can sometimes result in causally non-separable
  processes" — with no restriction to ISO.
- Oreshkov–Cerf 1406.3829: only an example — a mixture of two one-way process operators with a
  prepared state; there is no general statement. 1507.07745: nothing.
- **The closest analogue is arXiv:2602.00856, lemma lem:funcState** (the single-slot case: a deterministic
  functional on a bistochastic channel — a classical choice of the direction A→B or B→A). There is no two-party
  statement there ("causally separable" — 0 occurrences). Must be cited.

## F2 (the gap = CHSH/Tsirelson in relabelled roles)
- Fritz 1005.3421: temporal CHSH ⇔ spatial CHSH, the Tsirelson bound, PR-boxes impossible.
- Brukner–Taylor–Cheung–Vedral quant-ph/0402127: the temporal Tsirelson bound 2√2; temporal
  correlations coincide with the correlations of the singlet.
- Liu–Chiribella 2403.02749: bistochastic QM with indefinite order and direction — the classical
  and the quantum values coincide with the algebraic maximum; about definite order without selection
  there is nothing.
- arXiv API search: bistochastic+Bell/CHSH — 1 (irrelevant); "unital channel"+CHSH — 1 (irrelevant);
  "time-symmetric"+Tsirelson — 0; "doubly stochastic"+"Bell inequality" — 0; "pseudo-density"+CHSH — 2
  (temporal CHSH, without bistochasticity and incomes); bistochastic+"causal order" — 1 (2602.00856);
  "time-symmetric"+CHSH — 1 (irrelevant).
- Verdict: the fact itself that "temporal/sequential correlations = CHSH with the Tsirelson bound" is known.
  Formulations in terms of the incomes/outcomes of TS-operations (Alice's outcome in the role of the setting, the income in the
  role of the result) and in the normalisation 4 / 3+√2 / 5 were not found.

## NPA
NPA08: for CHSH the first level already gives the Tsirelson bound; the definition of level 1+AB — the quotations are in SOURCES.md.

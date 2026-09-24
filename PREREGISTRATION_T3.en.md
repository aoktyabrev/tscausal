> **Translation.** This is an English translation of `PREREGISTRATION_T3.md`, provided for readers.
> The Russian original is the sealed artefact: its SHA-256 is recorded in `results/json/prereg.json`
> and verified in `RESULTS.md`. This translation is not hashed and carries no evidentiary weight.

# PREREGISTRATION — T3.0 (three parties without selection)

Sealed before the first run: `scripts/t3_terms.py` has been written but has not been run; the rest of the T3 code has not been written.
Quotations — SOURCES.md (BW16, WBO23, BCRWZ19, ABCFGB15), derivations D10, D11.

## Definitions

- **ISO_N** (D10) = the W normalised for all forward instruments (TF_N, the OCB class) **and** for all backward
  ones (TB_N). The null space is computed literally: the rows are the differences `Tr[W ⊗ M_X]` for random products of
  local CPTP Chois (forward or backward), qubits.
- **Rule (a derivation, before the computation):** a non-identity Pauli term is admissible in TF_N ⇔ there is a party for which it is
  "input only"; in TB_N ⇔ there is a party that is "output only"; in ISO_N — both conditions. The count: TF_N = 1 + 16^N − 13^N,
  ISO_N = 1 + 16^N − 2·13^N + 10^N. N = 2: 88 and 19 (coincides with Stage C); N = 3: 1900 and **703**.
- **The game** (D11): the BW16 game, example 2 (the incomes a, b, c are uniform; the outcomes x, y, z are the guesses); the bound is 3/4.
  The probabilities are `p = (1/8) Tr[W (M_A ⊗ M_B ⊗ M_C)]` (a generalisation of D5). The operations are TS; classically they are
  bijections (income, input) ↔ (outcome, output), 24 per party, an enumeration of 24³.
- **Causal orderedness of a classical process** — as in BCRWZ19 (footnote, p. 280), extended by
  dynamical order: the first party receives a constant, the second a function of the first one's output (its choice may
  depend on that output), the third a function of the outputs of the first two. A **causally separable** classical
  process is a convex combination of such functions; the check is an LP.
- **Admissibility of a deterministic process** — BCRWZ19: w∘f has a fixed point for all 4³ collections of
  local functions; "exactly one" is checked.

## Plan
- **T.0:** the dimensions of TF_3, TB_3, ISO_3 (and the calibration N = 2 → 19); agreement with the rule; the number of
  anticommuting pairs; the terms by number of parties.
- **T.1:** (a) Lugano (P = 000) with TS-operations: the BW16 game = 1 (a calibration), is W_AF ∈ ISO_3? (b) the canonical
  XOR extension of WBO23, P uniform, F discarded: W̄, membership in ISO_3, the value of the game, separability;
  (c) all invertible extensions with one-bit P and F (the minimal dimension: Lugano has a pair of outputs
  with a single image): an enumeration of the second map ω₁ with the required image multiplicities, selection of the admissible ω₁,
  then regime (b) for ½(ω₀ + ω₁).
- **T.2 (classical):** the polytope of classical ISO_3-processes (diagonal W, 18 types + positivity),
  its vertices (cdd.gmp). For every vertex: causal separability (LP) and the maximum of the BW16 game over TS-bijections.
- **T.2 (quantum):** a see-saw over ISO_3 (qubits, W 64×64, 702 parameters) on the BW16 game with TS-instruments.
  Calibration: the same see-saw in the class TF_3 (OCB) must reach 1 (Lugano). Violations only after
  a recomputation in mpmath.

## Outcomes (from the prompt)
- D6 generalises analytically → "a prohibition at any N";
- a process without selection with a violation is found → "a prohibition only for two parties";
- neither of the two → what blocks each of them is recorded, with numbers.

## Predictions

**Architect:**
- T.0: terms with overlapping supports will appear, the proof of D6 does not carry over literally — medium-high;
- T.1: in the sources the global past P is fixed (preselection) — medium;
- T.1(b): with random P the Lugano violation disappears — medium (the main question);
- T.2: at least one process without selection violates a three-party causal inequality — low.

**Executor:**

| item | prediction | confidence |
|---|---|---|
| T.0 | N = 2: 19 (TF 88); N = 3: TF = TB = 1900, ISO = 703; the rule = the null space | 0.9 |
| T.0 | there are anticommuting pairs and three-party terms → the proof of D6 does not carry over literally | 0.95 |
| T.1(a) | Lugano with TS-operations gives 1; W_AF ∉ ISO_3 | 0.9 |
| T.1 | the sources: P is fixed (|000⟩) — already confirmed by the literature check before sealing | — |
| T.1(b) | the canonical XOR extension with uniform P: W̄ = (1/8)·1 exactly (XOR with uniform p randomises the inputs); the game ≤ 3/4 | 0.97 |
| T.1(c) | one-bit extensions exist; with uniform P all of them have a value ≤ 3/4 | 0.6 |
| T.2 cl. | all the vertices of classical ISO_3 are causally separable | 0.55 |
| T.2 cl. | no vertex exceeds 3/4 in the BW16 game | 0.65 |
| T.2 qu. | the see-saw in ISO_3 does not exceed 3/4 | 0.65 |
| overall | the outcome "neither a proof nor a witness" | 0.5 |

> **Translation.** This is an English translation of `PREREGISTRATION_RTS0.md`, provided for readers.
> The Russian original is the sealed artefact: its SHA-256 is recorded in `results/json/prereg.json`
> and verified in `RESULTS.md`. This translation is not hashed and carries no evidentiary weight.

# PREREGISTRATION — RTS stage 0 (time symmetry and the real-QM loophole)

Sealed before the first run of RTS and **before reading the report of the R.0 literature check** (the subagent has been launched, the report has not been read).
The RTS code has not been written. Renou's numbers and HW's formulations have not been entered into this file — they will be taken from the quotations (SOURCES.md).

## Definitions (fixed here)
- **Scenario:** the binocal scenario of Renou et al. (parties A, B, C; B performs a joint measurement on two
  inputs B_I1 ⊗ B_I2). The translation into TS without selection follows D8: a source ↦ a channel from the output of a party to the input of B
  with a maximally mixed global past; a party's "setting" ↦ its **outcome**, a "result" ↦ its **income**
  (as in D8); B has no setting, 4 outcomes. The cardinalities of the outcomes and incomes are those of Renou's settings and
  results; double causality is MH-1 with the factors N (MH24 eq. (2)).
- **Class:** ISO₃ (D10) for the parties A, B, C with a composite input at B. The linear conditions come from the same null-space code
  as in T3.0 (calibration: N = 2 → 19). The real class — W real symmetric; the operations real
  symmetric.
- **Operational independence of the channels (process level).** The main definition is the HW
  definition (quotation from 2603.19208), carried over to processes. The fallback (if the transfer is ambiguous): for any local
  TS-operations A and C and any **product** operations B of the form M_{B1} ⊗ M_{B2} (a separate income and outcome at each
  port) the joint distribution factorises: p(a, b₁, b₂, c) = p(a, b₁) · p(b₂, c).
- **Upper bound (R.3):** an SDP relaxation over W (exact for fixed operations) and a see-saw; a discrepancy
  with the complex value counts only if the upper bound is separated from it and the result is recomputed in mpmath.

## Predictions

**Architect:**
- R.0: real QM in TS-formalisms without selection has not been considered in the literature — medium;
- R.2: 4-party terms with a J factor on each channel are admissible in ISO — medium-high;
- R.3: real ISO with operational independence attains the complex T, i.e. HW carries over — ~55%.

**Executor:**

| item | prediction | confidence |
|---|---|---|
| R.0 | nobody has considered real QM in process matrices / TS-formalisms / with a maximally mixed global past | 0.7 |
| R.1 | a complex ISO-process (identity channels, D8) reproduces Renou's complex T exactly | 0.85 |
| R.1 | real product processes give no more than Renou's real bound | 0.9 |
| R.2 | terms of the form J^{A_O} J^{B_I1} J^{C_O} J^{B_I2} (and with J on the "imaginary" qubits) are admissible in ISO₃ — it follows from the rule "∃ input only ∧ ∃ output only" | 0.95 |
| R.2 | the HW RQT model translates into a real ISO-process (positive, in the class) | 0.65 |
| R.2 | the J⊗J terms satisfy operational independence | 0.7 |
| R.3 | real ISO with operational independence attains the complex T (HW carries over) | 0.65 |
| overall | the outcome "HW carries over, closed negatively" | 0.6 |

Reasoning: the link between the two channels through the "imaginary" qubits is a term in which B is "input only" and A and C are "output only";
the ISO rule admits it. The maximally mixed past is no obstacle: the correlation of the imaginary qubits is carried
by the process (the channel), not by the state of the past. The main risk for the transfer is positivity and the requirement
that TS-operations remain TS after the real embedding.

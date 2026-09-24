> **Translation.** This is an English translation of `PREREGISTRATION_RTS1.md`, provided for readers.
> The Russian original is the sealed artefact: its SHA-256 is recorded in `results/json/prereg.json`
> and verified in `RESULTS.md`. This translation is not hashed and carries no evidentiary weight.

# PREREGISTRATION — RTS stage 1 (the final scan over dimension)

Sealed before the first run of stage 1. The scan code has not been written. The numbers below are predictions, not results.
Everything is inherited from `PREREGISTRATION_RTS0.md` (the translation D12, the class ISO, the definition of OI); only the
new definitions and predictions are fixed here.

## Definitions (fixed here)

- **Scenario and functional** — the same ones: D12, 𝒯 as in RTW21 (the coefficients are in `scripts/rts.py`), the operations free
  (TS-conditions: Σ_x Tr A_{a|x} = 3/2·d_A, Σ_z Tr C_{c|z} = 3·d_C, Tr F_b = d_B1·d_B2/4).
- **Process:** ω = ω₁⊗ω₂ + Δ on A⊗B1⊗B2⊗C, Δ ∈ Anti(A⊗B1)⊗Anti(B2⊗C); ISO ⇔ the marginals on (A,C) and on
  (B1,B2) are maximally mixed; OI holds exactly by the construction of Δ.
- **Cleaning of the final point (factor-wise noise, from RTS 0):** ω(q) = w₁(q)⊗w₂(q) + (1−q)Δ, where
  w_i(q) = (1−q)w_i + q·I/n_i, and q is the smallest value from bisection at which ω ≥ 0 (the certificate is a Cholesky).
  ISO and OI thereby remain exact. **The reported number is the cleaned 𝒯 only.** White noise I/N is not used:
  it is not a product and breaks OI at its own level.
- **A successful start** — all the SDP steps returned the status optimal or optimal_inaccurate and the final point
  passed the cleaning. A solver failure at any step of a start = a failed start, it is discarded entirely and counted.
- **A warm start** — the embedding of a cleaned point of dimension d into dimension d′ > d: ω ↦ ω ⊕ (maximally
  mixed on the complement) with the ISO marginals preserved, the operations are extended by zeros on the complement and
  renormalised to the TS-conditions. Warm and cold starts are separated in the report; a warm start without a cold one
  of the same dimension does not count.
- **The resource ceiling** is recorded with numbers: the size of the PSD block N×N, the peak memory, the time of one iteration of the
  see-saw and of one SDP step. Extrapolation in place of computation is not allowed.

## Predictions

**Architect:**
- at (8,8,8,8) the value will rise noticeably above 6.87 — confidence ~50%. A note: in RTS 0 the prediction in the same
  direction ("HW carries over", ~55%) did not come true.

**Executor:**

| item | prediction | confidence |
|---|---|---|
| S.1 | (2,2,2,2): the best cleaned 𝒯 = 4+2√2 = 6.828427, as in RTS 0 | 0.9 |
| S.1 | (4,4,4,4), cold starts: the best cleaned 𝒯 in [6.82, 6.95] | 0.7 |
| S.1 | (4,4,4,4): a cold start will not exceed the warm/HW start (6.869154) by more than 0.05 | 0.65 |
| S.1 | (6,6,6,6): the increment over (4,4,4,4) is less than 0.1 | 0.6 |
| S.1 | a plateau: (4,4,4,4) and (6,6,6,6) within 0.05 of each other and below 7.6605 | 0.55 |
| S.1 | at no dimension does 𝒯 exceed Renou's real bound 7.6605 | 0.85 |
| S.1 | at no dimension does 𝒯 reach 6√2 = 8.485281 | 0.9 |
| S.1 | (8,8,8,8) does not fit into a one-day budget; a ceiling will be recorded with numbers | 0.85 |
| S.2 | an upper bound with free operations will **not** be obtained | 0.8 |
| S.2 | if a symmetry reduction does work, it will shrink the block by no more than a factor of four | 0.6 |
| overall | the branch closes with the outcome "a plateau below 7.6605", i.e. with evidence in favour of time symmetry cutting off the OI loophole | 0.55 |

Reasoning. The contribution to 𝒯 in the HW model is carried by four rebit patterns, and two of them are already forbidden by ISO at
dimension 4 per party; increasing the dimension adds not new types of terms but only multiplicity, and therefore I
expect saturation rather than growth towards 8.485. The main risk to the prediction: at d ≥ 6 there appear ISO-admissible constructions
that do not reduce to the rebit one, and then a jump is possible. The second risk is not computational but model-related: the plateau
may turn out to be an artefact of the see-saw, which as the dimension grows finds the global maximum ever more poorly;
against this — the fraction of failed starts and the spread of the values across starts, which will go into the report.

The expected resource ceiling (a prediction, not a result): the PSD block grows as (d²)², i.e. 256 at d = 4,
1296 at d = 6, 4096 at d = 8; the SCS projection onto the cone costs O(N³) per iteration, and therefore I expect (8,8,8,8) to be
out of reach, while (6,6,6,6) is on the edge.

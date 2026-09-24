> **Translation.** This is an English translation of `PREREGISTRATION_T31.md`, provided for readers.
> The Russian original is the sealed artefact: its SHA-256 is recorded in `results/json/prereg.json`
> and verified in `RESULTS.md`. This translation is not hashed and carries no evidentiary weight.

# PREREGISTRATION — T3.1 (verification and structure of the witness W*)

Sealed before the first run of T3.1 and **before the results of the literature check were obtained** (T3.1.a has been launched by a subagent,
its report has not yet been read). The T3.1 code has not been written. Quotations — SOURCES.md; D10 (ISO_N) is **our own definition**.

## Definitions
- A process is a stochastic matrix T[i, o] (inputs i, outputs o, 3 bits each). W* = ½(ω_L + ω̄_L), ω̄_L(o) = ¬ω_L(¬o).
- **The group G** (T3.1.c): inversions of each of the 6 wires (the input and the output of each party) — Z₂⁶; permutations
  of the parties — S₃; the exchange input↔output at all the parties simultaneously (transposition of T) — Z₂; |G| = 64·6·2 = 768.
  The action: T' = T ∘ g. The MH time reversal (MH-30) additionally includes a reversal of the order of the parties, which is
  covered by composition with a permutation.
- **Symmetrisability** of a process ω through g: ½(ω + g·ω) ∈ ISO₃ (an exact Walsh check by the T.0 rule) **and**
  causally non-separable (an exact LP in cdd.gmp over the 680 causally ordered functions; for exterior points —
  an exact certificate). In addition: the correlation with the "forward" strategy is outside the causal polytope
  (138 304 strategies, HiGHS + an exact certificate).
- **Orbit mixtures:** the average over the orbit of ω under the cyclic subgroups ⟨g⟩ and under Z₂⁶, S₃, G.
- **T3.1.d:** all the deterministic functions of the process. A necessary condition (the "grandfather" argument): a party's input does
  not depend on its own output, otherwise a local function creates a contradiction. There are 16³ = 4096 candidates.
  Admissibility — the BCRWZ19 criterion (a fixed point for all 64 collections of local functions). The causality of a
  deterministic function is membership in the set of 680 ordered functions (a deterministic point is
  separable if and only if it coincides with one of them).
- **T3.1.b:** the values of BW16 (example 2) and of G* with the TS-strategy "forward" and with the maximum over the 24³ TS-triples
  on ω_L, ω̄_L, W*; the invariance of the games under total inversion; the inequalities I₁…I₄ of Abbott et al.
  (1608.01528) — if quotations of their forms have been obtained by the literature check; otherwise only BW16 and G*.
- **T3.1.e:** N = 4, the generalisation of Lugano from the literature (the citation from the subagent); ISO₄ — by the D10 rule
  (a type with "I only" and "O only"); symmetrisation by total inversion; causality — through a game built from the support
  with an exact causal bound over the deterministic strategies with dynamical order, if the enumeration fits
  (otherwise a ceiling is recorded). Calibration N = 2: the class = 19 (already in T3.0), and no two-party
  deterministic process is symmetrisable (a consequence of D6).

## Outcomes (from the prompt)
- the literature check finds the same result → the branch reduces to a translation into the MH formalism and a contrast with D6;
- the literature check is clean, c/d yield a general principle of symmetrisation → a formulation with a characterisation of the "mirrors" that work;
- d: Lugano is the only symmetrisable class → it is recorded as it is.

## Predictions

**Architect:**
- a: the notion "without a global past" in the literature is close to ISO₃, but the symmetrisation of Lugano by a mirror with
  a violation of an inequality is not written out explicitly — low-medium (the novelty risk is real);
- b: BW16 gives 1 on Lugano and 0 on the mirror — medium;
- c: not only total inversion works — medium-low;
- e: for N = 4 the symmetrisation works as well — medium.

**Executor:**

| item | prediction | confidence |
|---|---|---|
| a | in the literature there is a close notion (without a global past), but there is no explicit result "Lugano/a non-causal process without a fixed past and future with a violation" | 0.5 |
| a | the same result is found (someone else's priority) | 0.3 |
| b | BW16 with the "forward" strategy: Lugano 1, the mirror 0, W* 1/2; G* is invariant under total inversion | 0.8 |
| c | the g that work are exactly "total inversion × the stabiliser of Lugano in G" (essentially a single mirror) | 0.5 |
| c | there exists a g that works and is not reducible to total inversion by composition with a symmetry of Lugano | 0.4 |
| c | the exchange input↔output by itself does not work (the mixture is not in ISO₃) | 0.8 |
| d | the number of admissible deterministic functions out of 4096 is between 700 and 2000; of the non-causal ones — only the images of Lugano under local relabellings and permutations of the parties | 0.6 |
| d | every non-causal deterministic process is symmetrisable by some g | 0.65 |
| e | for N = 4 the symmetrisation by total inversion works (∈ ISO₄ and non-causal) | 0.6 |

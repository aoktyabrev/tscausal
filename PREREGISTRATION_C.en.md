> **Translation.** This is an English translation of `PREREGISTRATION_C.md`, provided for readers.
> The Russian original is the sealed artefact: its SHA-256 is recorded in `results/json/prereg.json`
> and verified in `RESULTS.md`. This translation is not hashed and carries no evidentiary weight.

# PREREGISTRATION — Stage C (do N1 and N2 get violated by physically meaningful processes)

Sealed before the first run of Stage C: `scripts/stage_c.py` has not yet been written, and not a single SDP has
been run. After the commit the file is not changed. Quotations — SOURCES.md (MH-22…MH-30, B15-8, B15-9);
derivations — D5, D6.

## 0. Scenario and functionals

The Stage B scenario: no settings, `u, v` marginalised, everything binary. The statistics (D5):
`p(a,b,x,y) = (1/4) Tr[W̄ (M_{a,x} ⊗ M_{b,y})]`, where `W̄ = Σ_{u,v} W_{u,v}`, and the operations are
TS-operations in the sense of MH-1 (CP; `Tr_{A_O} Σ_x M_{a,x} = 1` for every a;
`(1/2) Tr_{A_I} Σ_a M_{a,x} = (1/2)·1` for every x).

Functionals: one representative of each class in the "game" form `Σ_{t∈S} p(t) ≤ 1/2`:
N1, N2 (RESULTS, Stage B) and the 4 remaining non-positivity classes of the classical closure
("cl3…cl6"). Inside the U2 hull (`p(a,b) = p(x,y) = 1/4`) the value does not depend on the choice of the
representative. Outside the hull (regimes with selection) it is exactly the written form that is used, and this
is stated explicitly.

## 1. The restricted class R (fixed here, not changed after the run)

**R** = { W̄ : W̄ ≥ 0 (MH-24); `Tr W̄ = d_A d_B` (Wcons1); W̄ satisfies vcons1–3 (MH-25,
the summation over v being trivial) and ucons1–3 (MH-25, the summation over u being trivial) }.
These are the processes for which `u, v` are trivial or marginalised; by MH-27 this is the class ISO.
Dimensions: `d_A = d_B = 2` (qubits), then 3 (qutrits).

Subclasses:
- **P1** — definite order and direction: W̄ ∈ R contains only terms `A_O B_I` (A→B)
  or only `A_I B_O` (B→A); the maximum of P1 is the maximum over the two variants.
- **P2** — the OCB processes (B15-8) lying in R: W̄ ∈ R ∩ OCB.
- **P3** — a two-sided "time flip" with a common control qubit: the "forward" branch is
  the identity channel A_O→B_I (ISO), the "backward" branch is the same scheme with the input and the
  output of the operations reversed (A_I↔A_O, B_I↔B_O), i.e. the channel B_O→A_I. In R the control qubit cannot
  be prepared in a pure state or projected: that would be pre- or postselection.
  It is marginalised, and W̄_P3 = ½(W_f + W_b). The variant with independent controls contains
  the branches "forward/backward" and "backward/forward" with the terms `A_O B_O` and `A_I B_I` — its
  membership in R is checked (expected: it does not belong).
- **P4** — the whole of R.

Outside R, diagnostics only (not an answer to the question of the stage):
- **TF-pre** — the OCB processes, statistics conditioned on u (preselection), by MH-27 this is the class TF;
- **full** — the full class with pre- and postselection, statistics conditioned on the event (u, v).

## 2. Lemma D6 and its proof (written down before the computations)

(a) For any physical process (MH-26) `W̄ = Σ_{u,v} W_{u,v} = (1/(d_A d_B))(1 + Σ_{u,v} σ^ISO)`,
since `Σ_u σ^TS = Σ_u σ^TF = 0`, `Σ_v σ^TB = 0` and `Σ p_0 = 1`. For R the same follows directly from
the linear conditions (vcons, ucons, Wcons): jointly they admit only the terms `1`, `A_O B_I` and
`A_I B_O`. This part is checked numerically: the null space of the literal maps
`_X` on the full basis for d = 2, 3 must have dimension `1 + 2(d²−1)²`.

(b) Let `W̄ = (1/(d_A d_B))(1 + T + S)`, where T is the sum of the terms `σ_i^{A_O}σ_j^{B_I}`, S the sum of
`σ_i^{A_I}σ_j^{B_O}` (i, j > 0). T and S act on different subsystems and commute, so that
`W̄ ≥ 0 ⇔ 1 + λ_min(T) + λ_min(S) ≥ 0`. Both matrices are traceless, and therefore λ_min ≤ 0.
Set `q = −λ_min(T) ∈ [0, 1]`. Then `W_1 = (1/(d_Ad_B))(1 + T/q) ≥ 0`,
`W_2 = (1/(d_Ad_B))(1 + S/(1−q)) ≥ 0` and `W̄ = q W_1 + (1−q) W_2`; the extreme cases q = 0, 1 are trivial.

(c) W_1 is the Choi matrix of a unital channel A_O→B_I (the partial traces of T vanish) with maximally
mixed A_I and discarded B_O. This is a scheme A≼B without pre- and postselection. With any TS-operations
its statistics satisfies eqs. (3), (4) and U2: the term T disappears under `Σ_y` (Bob's forward causality)
and under `Σ_a` (Alice's backward causality). Hence `p_1 ∈ P_AB` (Def-II), and similarly `p_2 ∈ P_BA`.

**Corollary:** in the Stage B scenario **no process of the MH24 formalism violates any
facet of the main polytope TS**, including N1 and N2, at any dimensions. The closure classes
cl3–cl6 may nevertheless be violated: these are facets of the classical closure, not of
Def-II, and quantum schemes with a definite order are capable of going beyond the classical closure.

(d) The flip side: N1 and N2 **do not hold** in regimes with selection even for processes with a
definite order. The scheme A≼B with preselection of Alice's input |0⟩ (Alice's operation
`(a,i)→(x=a, o=a⊕i)`, the identity channel A_O→B_I, Bob's operation `(b,j)→(y=b⊕j, o_B=b)`)
gives, conditioned on u, the distribution z (`x=a, y=a⊕b`), and z is cut off by the facets N1 and N2 (Stage B.2).

## 3. Calibrations (gates C.1, failure = stop)

1. **Formula D5 on the MH24 example (MH-29, with settings).** Forward LGYNI — `(2+√2)/4`,
   reversed — `1/2`. exampleW satisfies Wcons1–4 and vcons, **violates** ucons
   ("requires pre-selection").
2. **OCB, example B15-9:** GYNI `5/16(1+1/√2)`, LGYNI the same `+1/4`, up to 1e-12.
3. **OCB see-saw on qubits (B15-8):** GYNI ≥ 0.5694 − 1e-3 and LGYNI ≥ 0.8194 − 1e-3; an excess
   of more than 1e-3 is also a failure (either an error, or a refutation of the B15 conjecture, requiring analysis).
   In addition, W_max from B15 App. C with their instruments gives the smallest root of the polynomial B15-9.
4. **Postselection attains the maximum.** A process with no connection between the parties, with pre- and
   postselection (preparation of `A_I, B_I`, measurement of `A_O, B_O`; the operations "outcome = input,
   output = income"). Conditioned on the event (u, v) it gives `p = ¼·δ[(x,y) = π(a,b)]` for any
   bijection π. N1 and N2 thereby attain the U2-algebraic maximum.
5. **Solver:** a known problem (λ_max of a random Hermitian matrix via SDP against numpy,
   up to 1e-6) and a knowingly infeasible problem (`Tr W = 4` and `Tr W = 5`): the status must be
   infeasible. The see-saw fails on any status other than optimal.
6. **Classical closure:** the maximum of N1, N2 and cl3–cl6 on its vertices = 1/2 (exactly, from B.2).

## 4. Confirmation of violations
A violation counts only as a value exceeding 1/2 by more than 1e-6 and confirmed by a
direct recomputation of `p(a,b,x,y)` from the W̄ and the instruments that were found, in mpmath (50 digits).
The instruments and W̄ are checked for admissibility before the recomputation (positivity — via
eigenvalues with tolerance 1e-9).

## 5. Outcomes (from the prompt) and my refinement
- P3 violates, P2 does not, dephasing kills the violation → a positive answer to question 3 of MH24 in R;
- P2 violates too → N1/N2 witness indefinite order in general;
- **P4 does not violate → in R N1 and N2 are not violated by anything quantum; C is closed negatively**;
- C.1 is not passed → the formalism first.
My refinement to the last outcome: if D6 and (d) hold, then N1/N2 are not violated by anything in the
regime without selection and are violated by processes with a definite order in the regime with selection.
Then N1/N2 are not witnesses of indefiniteness in any regime of the MH24 formalism in
this scenario, and the central hypothesis in this formulation is untestable, not merely refuted.

## 6. Predictions

**Architect's predictions** (with his own uncertainty):
- P1 does not violate — high confidence (a control);
- P2 does not violate N1 and N2 — medium confidence;
- P3 violates at least one of N1, N2 without postselection — low confidence (a testable hypothesis);
- under dephasing of the control the P3 violation disappears — conditional on the previous item.

**Executor's predictions:**

| item | prediction | confidence |
|---|---|---|
| C.0.2 | the U2-algebraic maximum of N1 and N2 = 3/4 (bijections (a,b)→(x,y)); on TS it is 1/2 | 0.9 |
| C.0.2 | on F, on B and on F∩B the maximum of N1 and N2 is also 3/4 (they attain the U2-algebraic one) | 0.5 |
| D6(a) | the dimension of the null space = 1 + 2(d²−1)² for d = 2 (19) and d = 3 (129) | 0.95 |
| D6(b) | the decomposition goes through on 200 random W̄ ∈ R (d = 2, 3) | 0.97 |
| C.1.1 | MH24: (2+√2)/4 and 1/2; exampleW violates ucons | 0.9 |
| C.1.2 | B15: 0.5335 / 0.7835 exactly; OCB see-saw: 0.5694 / 0.8194 ± 1e-3 | 0.85 |
| C.1.4 | postselection gives 3/4 for N1 and N2 | 0.95 |
| C.1.5 | solver: the known problem converges, the infeasible one — infeasible | 0.97 |
| C.2 | P1, P2, P3, P4: the maximum of N1 and N2 = 1/2 (to solver precision) on qubits and qutrits | 0.95 |
| C.2 | P3 with independent controls ∉ R | 0.85 |
| C.2 | P1 (quantum) violates at least one of cl3–cl6 | 0.4 |
| C.2 | TF-pre (OCB with preselection): N1 and N2 are violated, including by a scheme with a definite order (z) | 0.95 |
| C.3 | in R the dephased and the "coherent" P3 coincide identically (W̄_P3 = ½(W_f + W_b)) | 0.95 |
| overall | the outcome "P4 does not violate" | 0.95 |

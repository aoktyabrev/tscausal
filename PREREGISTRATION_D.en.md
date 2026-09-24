> **Translation.** This is an English translation of `PREREGISTRATION_D.md`, provided for readers.
> The Russian original is the sealed artefact: its SHA-256 is recorded in `results/json/prereg.json`
> and verified in `RESULTS.md`. This translation is not hashed and carries no evidentiary weight.

# PREREGISTRATION — Stage D (the quantum-classical gap on cl3–cl6)

Sealed before the first run of Stage D (`scripts/stage_d.py` has not been written and has not been run).
After the commit the file is not changed. Quotations — SOURCES.md; the derivations D7, D8 are written down below before the computations.
The literature check D.0.3 is carried out in parallel by a subagent, its results do not enter this file.

## 0. The object

The Stage B scenario (no settings, `u, v` marginalised). The functionals cl3–cl6 — exactly in the
form they have in RESULTS.md (Stage C, C.0): integer weights on `p(a,b,x,y)`, the bound `rhs`. The gap is
an excess over `rhs` by quantum TS-processes with a definite order (by lemma D6 there are no others in R).

## 1. Derivation D7: completeness of the classical closure (proof, before the computations)

A classical TS-process A≼B without selection (by D6) is a diagonal unital channel A_O→B_I
(a doubly stochastic matrix) with uniform A_I. Classical TS-operations (MH-1, the diagonal
case): Alice — non-negative `M_{a,x}(o|i)` with `Σ_{x,o} M = 1` for every (a, i) and
`Σ_{a,i} M = 1` for every (x, o) (N_a = N_x = 2). Since `i` is uniform and connected to nothing,
Alice is equivalent to the collection of distributions `σ_{a,x}(o) = (1/d) Σ_i M_{a,x}(o|i)` with the conditions
`Σ_{x,o} σ_{a,x}(o) = 1` and `Σ_a σ_{a,x}(o) = 1/d`. The channel is absorbed into Bob's measurement.
Set `q_o(a|x) = d·σ_{a,x}(o)`: this is the conditional distribution of a given x for every symbol o.
Alice's condition: `E_o[q_o(a|0) + q_o(a|1)] = 1` with uniform o. Similarly for Bob —
`r_o(y|b)` with `E_o[r_o(y|0) + r_o(y|1)] = 1`. Hence
`p(a,b,x,y) = ¼ E_λ[q_λ(a|x) r_λ(y|b)]` — a local hidden-variable model with the variable λ, the responses
"a from x" and "y from b" and **averaged** constraints on the marginals. Every pair of responses can be
decomposed into deterministic ones, and the linear constraints are preserved on average. Therefore at
arbitrary dimensions the set is the image of the polytope M from Stage B (types tA, tB,
`E|tA| = E|tB| = 1`). The vertices of M are rational; the denominators have already been found: N ≤ 4 (B.2, item 4, explicit schemes).
Consequently, **the closure is complete, the classical bound cl3–cl6 is tight at any dimensions**.
Numerical control: a classical see-saw (diagonal σ, F) at d = 5, 6.

## 2. Derivation D8: reduction to the Bell scenario (before the computations)

A quantum TS-process A≼B without selection: `W = (1/d²)(1 + T)`, where T is the Choi matrix of a
unital channel Λ: A_O→B_I, A_I maximally mixed, B_O discarded (D6). For the TS-operations
set `σ_{a,x} = (1/d) Tr_{A_I} M_{a,x}`. MH-1 gives `Σ_x Tr σ_{a,x} = 1` and `Σ_a σ_{a,x} = 1/d`.
Bob's measurement: `F_{b,y} = Tr_{B_O} M_{b,y}` with the conditions `Σ_y F_{b,y} = 1` and `Σ_b Tr F_{b,y} = d`;
the channel is absorbed: `Λ†(F)` satisfies the same conditions, since Λ is unital and trace-preserving.
Then `p = ¼ Tr[σ_{a,x}^T F_{b,y}]` (the transposition comes from the CJ convention; it is checked numerically).
Conversely: `M_{a,x} = 1 ⊗ σ_{a,x}`, `M_{b,y} = F_{b,y} ⊗ 1/d` and the identity channel realise
any pair (σ, F). With `A_{a|x} = d σ_{a,x}` and the normalised maximally entangled `|φ_d⟩`:
`p = ¼ ⟨φ_d| A_{a|x}^{(T)} ⊗ F_{y|b} |φ_d⟩`.

**The quantum TS-set A≼B is the set of Bell correlations on |φ_d⟩ with inputs (x, b), outputs
(a, y) and the marginal conditions `P(a|0) + P(a|1) = 1`, `P(y|0) + P(y|1) = 1`.** Def-II `P_AB` is
the corresponding NS-set with the same conditions (eqs. (3), (4) are the absence of signalling in the Bell
roles), the classical closure is the local set. The expected consequence: the 8 "unrealisable"
vertices of P_AB are PR-boxes, and 3+√2 is the Tsirelson bound in this normalisation.

## 3. Methods

- **D.0.1:** for every cl_k and every order — check whether cl_k coincides on aff(P_order) with
  α·CHSH_j + β for one of the 8 relabellings of CHSH in the Bell roles of that order (exact linear
  algebra). Relations under G: cl3–cl6 are different G-classes (Stage C), this is additionally reported.
- **D.0.2:** the Stage C witnesses → (σ, F) → a readable form. The minimal witness is an analytic
  qubit one, built from the CHSH-optimal strategy; the value is checked symbolically (sympy).
- **D.1:** the proof of D7 + numerical control at d = 5, 6.
- **D.2:** the forward scenario: operations with forward normalisation only, A≺B, `p(a,b) = 1/4`. The classical
  polytope is the deterministic B15 vertices (A≺B) in the roles "inputs = incomes". The functionals are
  carried over **literally** (the same weights on p(a,b,x,y)); the variant with the filter `p(x,y) = 1/4` is treated
  separately. The quantum maximum is a see-saw over the OCB processes A≺B with operations having forward
  normalisation only. Calibration: the classical scheme "transmit a through the channel" realises
  the maximising vertex.
- **D.3:** NPA level 1+AB for the Bell scenario D8 (all states — an upper bound) with
  linear conditions on the marginals. Calibrations: CHSH without the conditions → (2+√2)/4 (the NPA citation is
  from the subagent, otherwise "not confirmed"); an LP over the local set with the conditions → the classical
  bound; an LP over the NS-set with the conditions → the Def-II maximum; the NPA result must lie between them.
- **D.4:** a see-saw in the reduced form (σ, F) — equivalent by D8, far cheaper than the TS-form — at
  d = 2, 3, 4, 50 starts; the best solutions are translated back into the TS-form (W, instruments) and
  recomputed in mpmath. The real variant: σ, F real symmetric; control — the real classical (diagonal) ones
  give the classical bound.
- **D.5:** Alice "rotated-classical": `M_{a,x} = (U⊗V) C_{a,x} (U⊗V)†`. The rotation is absorbed by the
  channel and by Bob's measurement, so that diagonal σ suffice for arbitrary F and channel.
  Mixtures of rotated classical operations give jointly measurable `A_{a|x}` (a mixture of jointly
  measurable families is jointly measurable), and therefore the absence of a gap is expected. The check is
  a see-saw with diagonal σ.

## 4. Outcomes (from the prompt)
- D.1 proved, D.2 with no gap, D.3 in agreement → a Tsirelson-type bound for TS-schemes with a definite
  order; then a novelty literature check and an extension to settings;
- D.2 shows a gap → the finding is not about time;
- D.1 not proved → the conclusions about the gap are conditional;
- D.3 above 3+√2 → the discrepancy is recorded.
My refinement: if D8 is confirmed, then the "Tsirelson-type bound" is literally the Tsirelson bound
for CHSH in relabelled roles. Time symmetry (backward normalisation) turns the channel
into a signalling-free resource equivalent to a maximally entangled state. Then the gap is
Bell nonlocality, not a new effect, and the question of novelty reduces to whether this
reduction is known (the temporal CHSH — Fritz 2010, Brukner et al. 2004 — a literature check).

## 5. Predictions

**Architect** (with his own uncertainty):
- D.1: the closure is complete, the bound 4 is provable — medium-high confidence;
- D.2: in the purely forward scenario there is no gap — medium (the main testable hypothesis);
- D.3: 3+√2 is the optimum over all dimensions — medium;
- D.4.1: at d = 3, 4 the value does not grow — medium-low;
- D.4.2: real QM attains 3+√2 — medium (from the look of the number).

**Executor:**

| item | prediction | confidence |
|---|---|---|
| D8 | the reduction TS ↔ (σ, F) ↔ Bell is numerically exact (≤ 1e-10) on the Stage C witnesses and on random points | 0.95 |
| D8 | the 8 vertices of Def-II P_AB outside the classical closure are PR-boxes in the Bell roles | 0.9 |
| D.0.1 | each cl_k, on the order where it is violated, is affinely equal to a relabelling of CHSH | 0.7 |
| D.0.2 | the minimal witness: the identity channel, Alice prepares a BB84 state (basis = x, bit = a), Bob measures in a basis rotated by 45° according to b; the value is exactly 3+√2 (cl3) | 0.75 |
| D.1 | D7 is correct; the classical see-saw at d = 5, 6 does not exceed the bound | 0.97 |
| D.2 | there is no gap: the quantum maximum = the classical one = the maximum of the forward polytope | 0.95 |
| D.3 | NPA 1+AB = 3+√2 (cl3, cl4, cl6) and 9/2+(√2−1) (cl5) up to 1e-6; the CHSH calibration (2+√2)/4 | 0.85 |
| D.4.1 | d = 3, 4: the maximum does not grow | 0.9 |
| D.4.2 | real QM attains 3+√2; real classical — 4 | 0.9 |
| D.5 | rotated-classical Alice: the maximum = the classical bound | 0.95 |
| overall | the outcome "a Tsirelson-type bound" (all three conditions), with the caveat that this is CHSH in different roles | 0.8 |

> **Translation.** This is an English translation of `PREREGISTRATION_B2.md`, provided for readers.
> The Russian original is the sealed artefact: its SHA-256 is recorded in `results/json/prereg.json`
> and verified in `RESULTS.md`. This translation is not hashed and carries no evidentiary weight.

# PREREGISTRATION — Stage B.2 (attributability, origin of the vertices, sensitivity, closure)

Sealed before the first run of Stage B.2 (`scripts/stage_b2.py`, `scripts/precision_test.py`
have not yet been written and have not been run). After the commit the file is not edited; the SHA-256 is verified
in RESULTS.md. Quotations: SOURCES.md (MH-15…MH-21, B15-7, derivation D4). The Stage B file
PREREGISTRATION.md is not changed.

Known before sealing (from Stage B, results/json/stage_b*.json): V(P_AB) = 18,
V(P_TS) = 32, 64 facets, 3 classes (positivity + N1 [32] + N2 [16]); z = "x=a, y=a⊕b"
∉ P_TS; the classical closure P_TS^cl: 48 vertices, 160 facets, 7 classes; Def-I (= U0):
64 facets, the conditional form (8) reaches 227/390 on a mixture.

## 0. Precision

All enumerations — only `cdd.gmp` or `lrs`. Test: a V-representation with a vertex one of whose
coordinates is 1/3, → H → V through cdd.gmp and through lrs; the coordinate must come back exactly as
`Fraction(1,3)`. Negative control: the same run through the float module `cdd` must give
something other than `Fraction(1,3)` (test failed). If the float control "passes", the test is vacuous, stop.

## 1. Attributability

Attribution of the equations (D4): F ← {(3), (5)} (forward causality), B ← {(4), (6)}
(backward). In all the polytopes of item 1 U2 holds: `p(a,b) = p(x,y) = 1/4`.

- `F_AB` = {p ≥ 0, Σp = 1, U2, eq. (3)}, `F_BA` = {…, U2, eq. (5)}, F = conv(V(F_AB) ∪ V(F_BA));
- `B_AB` = {…, U2, eq. (4)}, `B_BA` = {…, U2, eq. (6)}, B = conv(V(B_AB) ∪ V(B_BA));
- TS is the main polytope of Stage B.

A functional f (a facet of TS, `f·p ≤ f0`) **is violated on X** if `max_{V(X)} f·p > f0` (exactly).
Classification:
- **mixed** — violated both on F and on B;
- **forward-directed** — holds on F, violated on B (attributable to the forward direction);
- **backward-directed** — holds on B, violated on F;
- **common** — holds on both.
(The prompt formulates "directed" as "violated on only one of them"; here it is the same thing,
with an explicit indication of which one.) Party exchange and flips preserve F and B (this is checked),
TR swaps them, and therefore mixedness and commonness are properties of a G-class, while the directed
members of a class come in "forward/backward" pairs. The report is per member and per class.

F∩B: the H-representation of F and of B (cdd.gmp) → union of the inequalities → vertices (cdd.gmp),
comparison with V(TS). If TS ⊊ F∩B: exhibit a vertex of F∩B outside TS and the facet of TS that cuts it off.

Calibration of the test (failure = stop, the test is vacuous):
- K_fwd (the 48 facets of B15 in the forward reading) — all of them hold on F;
- at least one element of K_fwd is violated on B (there is a "forward-directed" one), and its image under TR
  is "backward-directed";
- positivity is "common".
GYNI in the forward reading (the control from the prompt) is reported but does not enter the calibration: under U2
GYNI ≡ reversed GYNI (D3), and therefore it must be "common". A departure from the prompt.

## 2. Origin of the vertices

Fact (from the Stage B code, not a prediction): the Stage B vertices were obtained by `P.vertices_cdd` — these are the extreme
points of the H-description (eqs. (3), (4) [or (5), (6)] + positivity + normalisation + U2) in cdd.gmp.
Deterministic functions were used only in the cross-check. An independent
recomputation: the same H-descriptions → vertices via **lrs** (H→V); comparison of the sets with Stage B.
If the sets differ, Stage B is recomputed.

## 3. Sensitivity to uniformity

- U2: `p(a,b) = p(x,y) = 1/4` (Stage B); U1: only `p(a,b) = 1/4`; U0: no uniformity.
- The group for U1/U0: the subgroup of G consisting of the automorphisms of V(TS_U).
- A class N from U2 **survives U1** if there is a facet of TS_U1 whose U2-canonical form
  (projection onto aff(TS_U2), primitive integer vector, lexmin under G) coincides with the canonical
  form of N. A class that does not survive is marked "a consequence of the U2 assumption".
- For the surviving classes — the attributability test in the U1 versions of F and B (F, B with U1 instead of U2).
- U0: check that the conditional form (8) is violated (exactly 227/390 is expected with the same seed).
  In addition: the conditional form (10) under U1 (non-linear, since p(x,y) is not fixed).

## 4. Closure of the classical schemes

Check each of the 48 vertices of P_TS^cl against the Stage B H-description (all 64 facets of TS and the equalities
of aff). If any of them is outside — exhibit it and indicate the violated inequality/equality; distinguish
"(3)–(6) are not necessary" from "the closure was built with an error" by the check: a point μ → a scheme with
concrete dimensions → a direct recomputation of the distribution by bijections → eqs. (3)–(6).
For the 7 classes of P_TS^cl — the attributability test of item 1 (the same F, B: by B15-7 the time-forward
correlations of the order A≺B are deterministic, so the H-variant of F_AB coincides with the classically
realisable one, and a separate "F^cl" is not needed).

"Confirmed in both constructions": the canonical form of the class N (U2) coincides with the canonical
form of some class of facets of P_TS^cl (the main definition). The weak definition
(reported separately): P_TS^cl has at least one mixed class outside K.

## 5. Outcomes (from the prompt) and refinements

- **Candidate:** there is a class outside K, mixed, surviving U1 and confirmed in both constructions
  (the main definition) → a literature check and a letter to the authors before any claims of novelty; Stage C — the architect.
- **Negative:** there are no mixed classes → question 1 in the minimal scenario is closed
  negatively in the sense of the paper.
- **Construction error** (item 2 or 4) → correction, repetition of item 1, revision of the Stage B conclusions.
- Intermediate cases (a mixed one exists, but it did not survive U1 or was not confirmed in the closure)
  are reported as they are, with an indication of which condition is not met.

## 6. Predictions

**Architect's prediction** (with his own uncertainty):
- TS is strictly smaller than F∩B — high confidence (because of the point x = a, y = a⊕b, but only if it lies in F∩B);
- at least one of the two new Stage B classes is mixed — medium confidence;
- at least one new class survives the transition U2 → U1 — medium confidence.

**Executor's prediction:**

| item | prediction | confidence |
|---|---|---|
| 0 | the exact path gives exactly 1/3, the float control fails | 0.99 |
| 1 | z ∈ F (via F_AB), z ∈ B (via B_BA), z ∈ F∩B, TS ⊊ F∩B | 0.95 |
| 1 | **both** new classes (N1, N2) are mixed: each has members that are violated by z ∈ F∩B | 0.9 |
| 1 | positivity is common; GYNI is common (D3), i.e. the prompt's control "it may be violated on B" will not fire | 0.95 |
| 1 | at least one element of K_fwd is violated on B (the calibration passes) | 0.8 |
| 1 | z is a vertex of F∩B | 0.7 |
| 1 | the number of vertices of F∩B | 40 (range 33–300) |
| 2 | the lrs recomputation gives the same 18+18 vertices; 14 of the 18 have coordinates 1/8, 4 have coordinates 1/4; there are no vertices with coordinates 0/1 at all (under U2 any point has p(a,b)=1/4, hence the coordinates are ≤ 1/4) | 0.97 |
| 3 | U1: TR is not an automorphism, the group has order 32 | 0.85 |
| 3 | at least one of N1, N2 survives U1 | 0.6 |
| 3 | the conditional form (10) is violated by a mixture under U1 | 0.6 |
| 3 | U0 reproduces 227/390 | 0.97 |
| 4 | all 48 vertices of P_TS^cl are inside TS (Def-II) | 0.95 |
| 4 | growth of the number of vertices: P_TS^cl is a strictly smaller polytope inside TS, its new vertices are fractional (denominators are multiples of 3, i.e. 12 in the p coordinates), not vertices of TS | 0.8 |
| 4 | at least one class of P_TS^cl is mixed | 0.95; all 6 new ones are mixed — 0.5 |
| 4 | at least one of N1, N2 is a class of facets of P_TS^cl | 0.5 |
| overall | the outcome "candidate" (all three conditions) | 0.35 |

Reasoning for item 1: in F_AB (eq. (3)) one needs b ⊥ (a, x) — for z, x = a, and b is uniform and independent;
in B_BA (eq. (6)) one needs y ⊥ (a, x) — for z, y = a⊕b with b independent and uniform. Mixedness is
class-invariant: exchange and flips preserve F and B, TR swaps them.

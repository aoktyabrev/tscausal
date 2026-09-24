> **Translation.** This is an English translation of `PREREGISTRATION.md`, provided for readers.
> The Russian original is the sealed artefact: its SHA-256 is recorded in `results/json/prereg.json`
> and verified in `RESULTS.md`. This translation is not hashed and carries no evidentiary weight.

# PREREGISTRATION — Stage B (TSCAUSAL stage 0.1)

Sealed before the first run of Stage B. After the commit this file is not edited;
the SHA-256 is carried over into RESULTS.md, and `scripts/make_results.py` checks it at every
generation of the report. Quotations and equation numbers are in SOURCES.md (labels MH-*, B15-*, D1–D3).
At the moment of sealing only Stage A has been carried out (results/json/stage_a.json); not a single
vertex, facet or scenario maximum of Stage B has been computed yet.

## 1. Scenario (main definition, Def-II)

Two parties, everything binary, no settings (`N_α = N_β = 1`), `u, v` marginalised.
Coordinates: the joint distribution `p(a,b,x,y)`, 16 numbers, `a,b` are incomes, `x,y` are outcomes.

- `P_AB` = { p ≥ 0, Σp = 1, D1: `p(a,b)=1/4`, `p(x,y)=1/4`,
  eq. (3): `p(a,b,x) = p(a,x)/2`, eq. (4): `p(b,x,y) = p(b,y)/2` }.
- `P_BA` = { p ≥ 0, Σp = 1, D1, eq. (5): `p(a,b,y) = p(b,y)/2`, eq. (6): `p(a,x,y) = p(a,x)/2` }.
- `P_TS` = conv(`P_AB` ∪ `P_BA`) — eq. (7).

Vertices: exact (GMP) vertex enumeration of `P_AB` and `P_BA`, then the union.
Cross-check by "deterministic vertices": the distributions of deterministic
classical TS-schemes (MH-1 for classical operations = double stochasticity; its extreme
points are bijections (income, input) ↔ (outcome, output)); scheme A ≼ B: uniform initial
input and ancilla → Alice's bijection → bijection-channel → Bob's bijection; `a, b` uniform.
Dimensions: input/output 2, ancilla 1, 2, 4.

Sensitivity control (Def-I): the same eqs. (3)–(6) **without** D1. It is computed and
reported, but the conclusions are drawn from Def-II.

## 2. Known inequalities and the set K

Functionals on `p(a,b,x,y)` (D2, D3):
- GYNI = reversed GYNI: `Σ_{x=b, y=a} p ≤ 1/2`;
- LGYNI_fwd: `Σ p [a(x⊕b)=0 ∧ b(y⊕a)=0] ≤ 3/4`;
- LGYNI_bwd: `Σ p [x(a⊕y)=0 ∧ y(b⊕x)=0] ≤ 3/4`.

K ("reducible to the known ones") = the 48 facets of the B15 polytope in the forward reading (inputs = incomes,
outputs = outcomes) ∪ the 48 facets in the reversed reading (inputs = outcomes, outputs = incomes), each one
written as a functional on `p(a,b,x,y)` via D1. These are GYNI, LGYNI, their reversals and
positivity with all the B15 relabellings (including conditional output flips).
A facet of `P_TS` is "known" if its canonical form (projection onto aff(`P_TS`), primitive
integer vector) coincides with the canonical form of an element of K.

## 3. The group and canonisation

G = ⟨ party exchange (a,b,x,y)→(b,a,y,x); time reversal (a,b,x,y)→(x,y,a,b);
flips of a, b, x, y ⟩. A class = a G-orbit of the canonical form. G' = G without time
reversal (⟨exchange, flips⟩). A new class is called **directed** if for its
representative f the reversal TR(f) is not G'-equivalent to f.

Anti-vacuum tests (mandatory, failure of any of them = stop):
- every generator is a non-identity permutation of the coordinates and an automorphism of the vertex set;
- every generator maps at least one known inequality (with relabellings) into
  another one, and the image has the same maximum on the vertices;
- negative control: a map that is not a symmetry (the conditional flip
  x→x⊕a, time reversal on Alice's side only, a random permutation of coordinates) must be
  rejected by the automorphism check;
- the canoniser has already been calibrated in Stage A (3 classes out of 16 on B15).

## 4. Stage B gates (exact, with no tolerances)

On the vertices of `P_TS`: max GYNI = 1/2, max reversed GYNI = 1/2, max LGYNI_fwd = 3/4,
max LGYNI_bwd = 3/4. Any deviation is an error in the definition of the vertices, stop.
Facet enumeration: cdd.gmp and lrs, coincidence of the sets after projection; a discrepancy is a stop.
Every facet produced is checked for validity and for being a facet (the rank of the saturating vertices).
Vertex cross-check: a point of a scheme outside `P_AB` is a stop; a vertex of `P_AB` not
reached by the schemes up to ancilla 4 is not a stop but is reported (the main one remains the
definition through eqs. (3)–(7), MH-13).

## 5. Outcomes (fixed in advance)

- **Negative:** all facets of `P_TS` are in K. Question 1 is closed negatively in this scenario.
- **Positive:** there is a class outside K, and it is directed. A candidate for Stage C (launched by the architect).
- **New but undirected:** there is a class outside K, but every such class is G'-equivalent
  to its own reversal. The prompt's criterion for Stage C is formally not met; the decision is the architect's.
- **Ceiling:** the enumeration did not finish — it is recorded as a number, a partial enumeration is not passed off as a complete one.

## 6. Predictions

**Architect's prediction:** in the scenario without settings there will be no new facet classes, everything will fit into the four known inequalities.

**Executor's prediction** (before the computations; the reasoning is below):

| quantity | point estimate | range |
|---|---|---|
| vertices of `P_AB` (= `P_BA`) | 12 | 12–60 |
| vertices of `P_TS` | 20 | 20–120 |
| affine dimension of `P_TS` | 9 | 7–9 |
| facets of `P_TS` | 40 | 10–500 |
| classes under G (with positivity) | 5 | 3–20 |
| outcome | a new class outside K exists (P ≈ 0.9); whether it is directed — P ≈ 0.5 |

Reasoning. (i) Uniform distributions on the hyperplanes `λ·(a,b,x,y) = c` over
GF(2) that are compatible with Def-II for A ≼ B give 6 admissible λ; of these, the vertices are apparently
the 4 signalling types × 2 values of c = 8, plus the 4 non-signalling points `x=a⊕c1, y=b⊕c2`
(common to both orders): 12 vertices, `P_TS`: 12+12−4 = 20. (ii) The point
"`x = a`, `y = a⊕b`, `(a,b)` uniform" lies in the forward B15 polytope (x depends only
on a) and in the reversed one (a = x, b = y⊕x), the marginals are uniform, but its support contains not
a single point of `P_AB` or `P_BA` (in `P_AB` x must be independent of `(b,y)`, whereas here
x = y⊕b). If this is correct, `P_TS` is strictly smaller than the intersection of the forward and reversed
B15 polytopes, and `P_TS` must have a facet outside K. This point is invariant
under time reversal, so the facet separating it may turn out to be
undirected — hence the 0.5. (iii) For Def-I I predict that the conditional form (8)
is violated by a mixture of orders with non-uniform incomes (value > 1/2), i.e. Def-I
is incompatible with MH24's own inequalities.

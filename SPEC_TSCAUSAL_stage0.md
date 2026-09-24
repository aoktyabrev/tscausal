# SPEC TSCAUSAL, Stage 0 — facets of the time-symmetric causal polytope

## The question of the branch

Mrini and Hardy (arXiv:2406.18489, Perimeter, 2024) built a time-symmetric
version of the process-matrix formalism and left three questions open:

1. Do the four inequalities (GYNI, LGYNI and their time reversals) exhaust
   the list of causal inequalities for two parties, or do there exist "exotic"
   inequalities mixing the forward and backward directions of time.
2. Does there exist a process simultaneously violating the forward and the backward
   version of an inequality.
3. Do processes with an indefinite direction of time violate at least one
   inequality that a process with a definite direction cannot violate.

The task of Stage 0 is question 1 in the minimal scenario, by exact facet enumeration.

## The trap we record before starting

The full class of time-symmetric processes (with pre- and postselection) coincides
with the ICOTD processes of Chiribella and Liu and attains the algebraic maximum of ANY
causal inequality. Therefore questions 2 and 3 make sense only for a
restricted class (without postselection, or realizable as a time reversal).
Without that restriction any test is vacuous and the answer "yes" means nothing.
Stages C and D are not run until the class is fixed explicitly.

## Stage A — calibration (a gate, without it we do not go further)

The script `causal_polytope_calib.py` has already been run, the result:

| quantity                        | obtained | expected |
|---------------------------------|----------|----------|
| vertices of the causal polytope | 112      | —        |
| equalities (normalization)      | 4        | 4        |
| GYNI, causal maximum            | 1/2      | 1/2      |
| LGYNI, causal maximum           | 3/4      | 3/4      |

What remains to be done in Stage A:
- obtain from Branciard et al. (NJP 18, 013008, 2015) the exact number of nontrivial
  facets and the number of equivalence classes for this scenario and compare with our 36;
  every external statement is backed by a verbatim quotation in `SOURCES.md`;
- if the count does not match — stop, we sort out the definition of the scenario rather
  than fitting it.

## Stage B — the time-symmetric polytope

Coordinates: `p(a, b, x, y | α, β)`, where `a, b` are the incomes, `x, y` are the
outcomes, `α, β` the settings. We start from the smallest nontrivial
scenario: everything binary, `N_α = N_β = 1` (no settings), that is, 16 coordinates.
The variables `u, v` (pre- and postselection) are marginalized.

Vertices: deterministic strategies satisfying double causality.
For the order A ≼ B these are equations (3) and (4) of arXiv:2406.18489, for B ≼ A —
equations (5) and (6). The causally separable correlations are the convex hull of both
sets.

Facet enumeration: pycddlib 3.x in exact arithmetic, and lrs as the dimension grows.
**Mandatory canonicalization:** because of the normalization equalities one and the same
inequality has many representations in H-form. We project every facet onto the
affine hull, reduce it to integer coefficients by dividing by the GCD and take the
lexicographic minimum over the symmetry group of the scenario:
- exchange of parties (A ↔ B),
- reversal of the direction of time (a ↔ x, b ↔ y),
- local relabelings of values.

Without this, the count of "classes" is an artifact of the representation, not a result.
In the calibration it already looked like 7 "classes" for exactly this reason.

Outcome criteria, fixed before the run:
- **Negative:** all nontrivial facets fall into the four known classes.
  Then question 1 is closed in this scenario, this is a publishable negative result.
- ~~**Positive:** there is a class that does not map to itself under reversal
  of the direction of time and does not reduce to the known ones. This is a candidate for
  a new causal inequality, and it goes to Stage C.~~
  **CANCELLED** by the architect's amendment (PROMPT_TSCAUSAL_stageB2.md, "Architect's
  amendment to the spec"): the criterion is formulated incorrectly. For Mrini and Hardy an
  exotic inequality is an inequality that cannot be attributed to a single direction of
  time; it may be T-symmetric. The former text is left struck through, not erased.
- **Positive (in force from Stage B.2):** there is a class outside the known ones that is
  **mixed** according to the attributability test: it is violated both on F (the convex
  hull of correlations causal forward only, for both orders) and on B (the same, backward
  only), but holds on the main polytope. A candidate for an exotic inequality: next comes
  a literature check and a letter to the paper's authors before any claims of novelty;
  Stage C is launched by the architect.
- **Computational ceiling:** if lrs cannot handle the scenario with settings, we record
  the ceiling reached as a number (vertices, hours) and do not pass off a partial search
  as a complete one.

## Stage C — what violates the new inequality (only if B has a positive outcome)

For each candidate we compute the maximum over three sets:
1. causally separable processes — by construction equal to the right-hand side;
2. time-forward process matrices (Oreshkov, Costa, Brukner) — an exact SDP, not a
   relaxation: the set of process matrices is given by positivity plus linear
   constraints;
3. the restricted time-symmetric class (time reversal, without postselection).

Question 3 gets a numerical answer if the maximum over (3) is strictly greater than the
maximum over (2).

## Stage D — question 2

A search for a process violating the forward and the backward inequality simultaneously,
in the same restricted class. The objective function is the minimum of the two excesses.

## Preregistration

Before the first Stage B run, seal the predictions with SHA-256: number of vertices,
number of facets, number of classes after canonicalization, the expected outcome (my
prediction is a negative outcome, that is, there will be no new classes in the scenario
without settings; settings more likely give something new). The executor's predictions
separately from mine.

## Novelty check before publication

Before calling anything new: check whether anyone has enumerated the facets of the
time-symmetric causal polytope after June 2024. Separately
read arXiv:2508.02463 (Jean, Silva, Vilasini — the equivalence of time symmetry
and cyclic causality; by the abstract this is about multi-time states and P-CTCs and does
not touch facets) and arXiv:2603.12283 (Ferradini, Mazzola, Vilasini — emergent causal
order and the direction of time).

## Environment

Python 3.12, pycddlib 3.x, lrslib, exact rational arithmetic (Fraction).
For the SDP in Stage C — the same toolkit as in SelfDual (NPA-like problems), with
mandatory calibration of the solver on a known case.

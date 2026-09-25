# tscausal — time symmetry without selection: what it forbids and what it does not

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.22937438.svg)](https://doi.org/10.5281/zenodo.22937438)
[![License: Apache-2.0](https://img.shields.io/badge/code-Apache--2.0-blue.svg)](LICENSE)
[![License: CC BY 4.0](https://img.shields.io/badge/docs-CC%20BY%204.0-lightgrey.svg)](LICENSE-docs)

A computational study of time-symmetric process matrices (Mrini–Hardy formalism,
[arXiv:2406.18489](https://arxiv.org/abs/2406.18489)) in the regime **without pre- or postselection**.
Three threads: the structure of the time-symmetric polytope, a classical non-causal three-party process,
and the real-quantum-theory loophole of Hoffreumon–Woods in that regime.

Every number is produced by a script, every stage is sealed by a preregistration **before** its first run,
and `RESULTS.md` is never written by hand.

## What is proven and what is open

| | result | where |
|---|---|---|
| ✔ | **Lemma D6:** without selection, bipartite processes are mixtures of one-way channels; the facets N1 and N2 are never violated, in any dimension | `RESULTS.md` § Stage C |
| ✔ | **D6, the other side:** once preselection is allowed, N1 and N2 are violated by a process with a definite causal order | § Stage C |
| ✔ | **Lemma D8:** a definite-order time-symmetric process without selection ≡ a Bell scenario on a maximally entangled state; the cl3–cl6 gap is CHSH and the Tsirelson bound in relabelled roles | § Stage D |
| ✔ | **W\* ∈ ISO₃** — a classical, causally non-separable process without selection; violates the published inequalities I₁ and I₃ | § T3.0, T3.1 |
| ✔ | **Certificate 3√2** at the Hoffreumon–Woods operations, valid for *all* real ISO states | § RTS stage 0 |
| ✔ | **Mechanism:** the terms that carry the construction out of ISO are J_A′J_C′ (forbidden in TF) and J_B1′J_B2′ (forbidden in TB) | § RTS stage 0 |
| ✖ | **Upper bound for free operations** — not obtained (the problem is non-convex in the operations) | § RTS stage 1, S.2 |
| ✖ | Full enumeration of ISO₃ with a composite input — not attempted (the work stays inside the network form D12) | § RTS stage 1, S.3 |

Bottom line for real quantum theory: the growth in dimension that produces the whole effect in the
Hoffreumon–Woods model adds nothing here — 6.828 (d = 2), 6.927 (d = 4), 6.873 (d = 6) against the
threshold 7.6605. This is **numerical evidence, not a proof**; the strict plateau criterion written down in
the preregistration was not met.

## The four results, one paragraph each

**Lemma D6.** Facets N1 and N2 of the time-symmetric polytope were candidates for witnessing indefinite
causal order. With the global past and future marginalised, every bipartite process of the formalism reduces
to `(1/d_A d_B)(1 + T_{A_O B_I} + S_{A_I B_O})`, which is always a mixture of a one-way channel A→B and a
one-way channel B→A. So nothing in the formalism violates those facets, in any dimension. Allow
preselection, and they are violated by a causally ordered process. They witness indefiniteness in neither
regime.

**Lemma D8.** A time-symmetric definite-order process without selection is exactly a Bell scenario on a
maximally entangled state, where Alice's "setting" is her **outcome** and her "result" is her **income**.
The quantum-classical gap on the classes cl3–cl6 is therefore CHSH together with the Tsirelson bound, in
relabelled roles.

**Witness W\*.** The uniform mixture ½(Lugano + its full inversion) lies in ISO₃, is causally non-separable,
and violates the published causal inequalities I₁ (15/16) and I₃ (1) of Abbott et al. Honest caveat: the
literature check found an implicit precedent from 2014 — the process W₃ of Baumeler–Feix–Wolf
([arXiv:1403.7333](https://arxiv.org/abs/1403.7333)) — and `RESULTS.md` says so explicitly.

**The Hoffreumon–Woods construction does not transfer as it stands.** Renou et al. ([arXiv:2101.10873](https://arxiv.org/abs/2101.10873),
Nature 600, 625) showed that real quantum theory predicts strictly less than complex quantum theory in a
bilocal network: a functional 𝒯 reaches 6√2 ≈ 8.4853 with complex states and at most 7.6605 with real ones.
Hoffreumon–Woods ([arXiv:2603.19208](https://arxiv.org/abs/2603.19208)) objected that if the sources are
only required to be *operationally independent*, real theory catches up. Translated into the time-symmetric
class, their construction breaks: two of the four rebit terms that assemble 6√2 need a phase reference
shared by parties that share no source, and those are exactly the terms forbidden by "no preferred future"
(TF) and "no preferred past" (TB). They do carry value, but they are needed only for positivity: removing
them keeps 𝒯 = 6√2 while positivity fails (λ_min = −1/128), and restoring positivity with noise eats
precisely the gain. At their operations the maximum over **all** real ISO processes is certified to be
≤ 3√2 = 4.24264070 — half the complex value — and operational independence is not even required for that
bound.

## Stages

| stage | subject | preregistration |
|---|---|---|
| A | precision gate: exact arithmetic, cross-checking enumerators (`cdd.gmp`, `lrs`), canonicaliser calibration | — |
| B | the time-symmetric polytope Def-II: vertices, facets, classes | `PREREGISTRATION.md` |
| B.2 | attributability, origin of vertices, sensitivity to uniformity, closure | `PREREGISTRATION_B2.md` |
| C | do N1 and N2 get violated by physically meaningful processes (Lemma D6) | `PREREGISTRATION_C.md` |
| D | the quantum-classical gap on cl3–cl6 (Lemma D8, NPA) | `PREREGISTRATION_D.md` |
| T3.0 | three parties without selection: the witness W\* | `PREREGISTRATION_T3.md` |
| T3.1 | structure of W\*, the "mirrors", full enumeration, a negative result at N = 4 | `PREREGISTRATION_T31.md` |
| RTS 0 | translating Renou's bilocal scenario into TS without selection; the HW model; the 3√2 certificate | `PREREGISTRATION_RTS0.md` |
| RTS 1 | dimension scan d = 2, 4, 6, 8; dual certificates; branch summary | `PREREGISTRATION_RTS1.md` |

Details, numbers, calibrations, **failed** anti-vacuum tests and **every deviation** are in `RESULTS.md`.

## Working rules

1. **Rule 0.** Any external number, definition or formula enters the work only together with a verbatim
   quotation in `SOURCES.md` (arXiv id, line or equation number). Otherwise it is marked "not confirmed".
2. **Preregistration.** Predictions of the executor and of the architect, with numbers and confidences, are
   fixed in `PREREGISTRATION*.md` and committed **as a separate commit before the first run of the stage**.
   Throughout, **architect** is the author (problem statements, acceptance criteria, the high-level forecast)
   and **executor** is Claude Code (implementation, computation, the detailed per-stage predictions).
3. **`RESULTS.md` is generated** by `scripts/make_results.py` from `results/json/` and never hand-edited.
4. **Anti-vacuum tests.** Every estimator is calibrated on a problem where it must fail, or where the answer
   is known in advance (for example, the complex see-saw must find 6√2).
5. **Violations count** only after an independent recount in exact or extended precision; upper bounds count
   only with a certificate (dual point plus Cholesky factorisation).

### Language note

The work itself was carried out in Russian. Everything a reader needs is now in English: this README,
`RESULTS.md`, `SOURCES.md`, the stage prompts, the literature-check reports, the code comments, `CITATION.cff`
and the Zenodo record.

Three things deliberately stay in Russian. First, the eight `PREREGISTRATION*.md` files: they are **sealed by
SHA-256**, those hashes are the evidence that the predictions were registered before the runs, and
translating a file in place would invalidate them. English translations sit alongside as `*.en.md`, each
marked as a translation. Second, the labels stored inside `results/json/*.json`: those files are the output
of the computations and are never edited by hand, so `scripts/labels_en.py` maps the labels to English while
`make_results.py` loads them — numbers are untouched, and a label with no translation is reported instead of
slipping into the report. The Russian string literals left in the stage scripts are exactly those labels, at
the point where they are written. Third, `causal_polytope_calib.py`: it is kept as it ran, comments and
printed output included, because `scripts/stage_a.py` parses that output to build its gate.

### Verifying the preregistrations

SHA-256 of file contents (unaffected by the history rewrite described below):

```
582087467b4e771c…  PREREGISTRATION.md        (Stage B)
8dc8816e9c771698…  PREREGISTRATION_B2.md     (Stage B.2)
9e5c6a8ec8554b5a…  PREREGISTRATION_C.md      (Stage C)
c6052f4a648af321…  PREREGISTRATION_D.md      (Stage D)
104252146fb728ee…  PREREGISTRATION_T3.md     (T3.0)
528b192d2d442ddf…  PREREGISTRATION_T31.md    (T3.1)
10006240768c1ce5…  PREREGISTRATION_RTS0.md   (RTS 0)
b9a3e4bc404e00e2…  PREREGISTRATION_RTS1.md   (RTS 1)
```

Full values and the automatic check (file on disk ↔ version inside the preregistration commit) are in the
table at the top of `RESULTS.md`, generated by `scripts/make_results.py`. Manually:

```bash
sha256sum PREREGISTRATION*.md
git log --diff-filter=A --format='%h %ad %s' --date=short -- PREREGISTRATION_RTS1.md
```

The commit order shows that each stage's preregistration was sealed before that stage's first run.

## Reproducing

```bash
micromamba create -p .env -c conda-forge python=3.12 cddlib gmp lrslib pip pypdf cython setuptools compilers
CFLAGS="-I$PWD/.env/include" LDFLAGS="-L$PWD/.env/lib -Wl,-rpath,$PWD/.env/lib" \
  .env/bin/python -m pip install --no-build-isolation "pycddlib>=3,<4"
.env/bin/python -m pip install cvxpy clarabel scs mpmath sympy
.env/bin/python -m pip install torch --index-url https://download.pytorch.org/whl/cu128   # for stage RTS 1
bash scripts/run_all.sh
```

Versions behind the published numbers: Python 3.12.14, numpy 2.5.3, scipy 1.18.1, cvxpy 1.9.3,
pycddlib 3.0.2 (built against `.env`), torch 2.11.0+cu128.

**Hardware and runtime.** Everything except stage RTS 1 runs on CPU (8 cores, 24 GB RAM were used):
stages A–D about 1.5 h, T3 about 1.5 h, RTS 0 about 10 h. Stage RTS 1 uses a GPU (NVIDIA RTX 4070 Ti,
12 GB): the dimension scan took 18.8 h. Without a GPU the same scripts still run, but dimensions 6 and 8
become unreachable: at N = 1296 a single state step in SCS takes about 350 s versus seconds for the ADMM
step on the GPU.

**Memory limits.** Each script sets its own `RLIMIT_AS` (environment variable `RTS_MEM_GB`), and runs are
launched strictly one at a time. This follows a real failure: a dense 7.5 GB Δ basis together with a
parallel run exhausted the machine's memory. The interior-point solver Clarabel is unusable at N ≥ 256 — it
needs a dense Hessian block for the PSD cone (a single 4.33 GB allocation).

## Data

- `results/json/*.json` — all numbers from which `RESULTS.md` is generated.
- `results/*.npz` — the points found (states and operations) for d = 2, 4, 6.
- The d = 8 point (`rts_gpu_8.npz`, 129 MB) is too large for the repository; it is attached as a separate
  file to the Zenodo record ([10.5281/zenodo.22937438](https://doi.org/10.5281/zenodo.22937438)) and is
  reproduced by `scripts/rts_gpu_scan.py`.

## Third-party material

Full texts and sources of third-party arXiv papers were used during the work. **They are not part of this
repository**: their licences do not permit redistribution. `SOURCES.md` contains only short verbatim
fragments with precise references (arXiv id, line or equation number), sufficient to verify every borrowed
number; copyright in those fragments remains with their holders. The project's own literature-check reports
are kept: `sources/*/REPORT.md`.

## Commit history

The history was rewritten with `git filter-repo` to remove third-party papers from it. **Commit order, dates
and messages are preserved**; only the commit hashes changed. The mapping from old to new hashes is in
`COMMIT-MAP.txt`, and the `commit_before_history_rewrite` fields in `results/json/prereg.json` keep the
previous values. A bundle of the original history is kept by the author outside the publication.

The key point: the SHA-256 values of the preregistrations are hashes of **file contents**, which a history
rewrite does not change. The "is this the same file" check stays complete; only the link to a commit was
re-attached.

## Licences

- **Code** (`scripts/`) — Apache-2.0, see `LICENSE`.
- **Texts, tables and data** (`RESULTS.md`, `SOURCES.md`, `PREREGISTRATION*.md`, `PROMPT*.md`, `SPEC*.md`,
  `sources/*/REPORT.md`, `results/`) — CC BY 4.0, see `LICENSE-docs`.
- Quotations from third-party works in `SOURCES.md` remain under their holders' copyright.

## How to cite

Zenodo record: **[10.5281/zenodo.22937438](https://doi.org/10.5281/zenodo.22937438)** — this is the concept
DOI and always resolves to the latest version. In a paper, cite the version DOI of the specific release
(v1.1.0 — [10.5281/zenodo.22950913](https://doi.org/10.5281/zenodo.22950913)).

```bibtex
@software{oktyabrev_tscausal_2026,
  author    = {Oktyabrev, Artem},
  title     = {tscausal: time-symmetric process matrices without selection},
  year      = {2026},
  publisher = {Zenodo},
  version   = {1.1.0},
  doi       = {10.5281/zenodo.22937438},
  url       = {https://doi.org/10.5281/zenodo.22937438}
}
```

A machine-readable form is in `CITATION.cff` (GitHub shows a "Cite this repository" button).

## AI use disclosure

The problem statements, stage specifications and acceptance criteria were worked out by the author in
dialogue with Claude (Anthropic). The implementation — code, computations, report text — was carried out
through Claude Code (model Claude Opus 5); the corresponding commits carry the trailer
`Co-Authored-By: Claude Opus 5`. Claude and Claude Code are tools, not co-authors, and responsibility for
the results rests with the author. The safeguards against the characteristic failure modes of this way of
working are built into the process: predictions registered before the runs, mandatory anti-vacuum tests,
`RESULTS.md` generated by a script, a certificate for every upper bound, and a full list of deviations in
the report.

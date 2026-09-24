"""
Generates RESULTS.md from results/json/*.json. RESULTS.md is never edited by hand.
Checks the SHA-256 of PREREGISTRATION.md against results/json/prereg.json and against
the version of the file in the preregistration commit.
"""
import hashlib
from fractions import Fraction

import numpy as np
import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import labels_en as L10N  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
J = os.path.join(ROOT, "results", "json")

# The stage scripts were written in Russian and store Russian labels in results/json/*.json. Those files are
# the output of the computations and are never edited by hand, so the labels are translated here, on load
# (scripts/labels_en.py). Numbers are untouched; an unknown label is reported instead of silently passing.
MIXED = "mixed"
COMMON = "common"
CANDIDATE = "CANDIDATE"
MISSING_LABELS = set()


def load(name):
    p = os.path.join(J, name)
    if not os.path.exists(p):
        return None
    return L10N.translate(json.load(open(p)), MISSING_LABELS)


def sha(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest()


def truth(b):
    """JSON with default=str turns numpy-bool into the strings 'True'/'False' — parse them explicitly."""
    if isinstance(b, str):
        if b in ("True", "False"):
            return b == "True"
        raise ValueError(f"not a boolean value: {b!r}")
    return bool(b)


def ok(b):
    return "YES" if truth(b) else "NO"


def prereg_block():
    prs = load("prereg.json")
    lines = ["## Preregistrations", ""]
    if not prs:
        return lines + ["**prereg.json is missing — the preregistration is not fixed.**", ""]
    lines += ["| stage | file | SHA-256 | commit | file matches | version in commit matches |",
              "|---|---|---|---|---|---|"]
    for pr in prs:
        cur = sha(os.path.join(ROOT, pr["file"]))
        try:
            blob = subprocess.run(["git", "-C", ROOT, "show", f"{pr['commit']}:{pr['file']}"],
                                  capture_output=True, check=True).stdout
            in_commit = hashlib.sha256(blob).hexdigest()
        except Exception as e:  # noqa: BLE001
            in_commit = f"error: {e}"
        lines.append(f"| {pr['stage']} | `{pr['file']}` | `{pr['sha256']}` | `{pr['commit']}` | "
                     f"**{ok(cur == pr['sha256'])}** | **{ok(in_commit == pr['sha256'])}** |")
    lines += ["", "Each preregistration is a separate commit made before the first run of its stage.", ""]
    return lines


def architect_defects():
    return ["## Defects of the architect's calibration (recorded at his instruction, PROMPT stage B.2)", "",
            "1. `causal_polytope_calib.py` claimed exact rational arithmetic, but it uses "
            "`import cdd`, and in pycddlib 3.x that is the float backend: Fraction is silently turned into float. "
            "The exact mode is `cdd.gmp`; every enumeration in the project goes through `cdd.gmp` or `lrs`. "
            "The anti-vacuum precision test is in section Stage B.2. The architect's script itself was not changed.",
            "2. The candidate criterion in `SPEC_TSCAUSAL_stage0.md` (“a class that does not map to itself under "
            "time reversal”) was revoked by the architect's amendment (separate commit `c45a096`, the old "
            "text struck through, not deleted). The criterion in force is attributability (Stage B.2). "
            "The Stage B outcome “new but non-directional” was formulated under the revoked criterion.", ""]


def stage_a(a):
    a1, a2, a3, a4 = a["A1"], a["A2"], a["A3"], a["A4"]
    f36 = a1["float_raw36_decomposition"]
    L = ["## Stage A — gates", "",
         f"Gate result (A.1 and A.3 passed, A.2 confirmed by citation): **{ok(a['gate_pass'] and a2['pass'])}**", "",
         "### A.1 Calibration script", "",
         "| quantity | script (as is) | exact (cdd.gmp) | expected |", "|---|---|---|---|",
         f"| vertices | {a1['vertices']} | {a1['exact']['vertices']} | 112 |",
         f"| equalities (normalisation) | {a1['equalities']} | {a1['exact']['equalities']} | 4 |",
         f"| GYNI, causal maximum | {a1['gyni']} | {a1['exact']['gyni_max']} | 1/2 |",
         f"| LGYNI, causal maximum | {a1['lgyni']} | {a1['exact']['lgyni_max']} | 3/4 |",
         f"| “non-trivial” by the script's filter | {a1['raw_nontrivial']} | {a1['exact']['raw_nontrivial_script_filter']} | — |",
         "",
         f"A remark on the backend: {a1['note_backend']} The number of “raw non-trivial” ones depends on the "
         f"form in which cdd emits the positivity inequalities: in the float run {f36['literal_positivity_rows_dropped_by_script']} "
         f"out of 16 are written literally (and filtered out), in the GMP run none are. This is a representation artefact.",
         "",
         "### A.2 Cross-check against Branciard et al. (arXiv:1508.01704, citations B15-1…B15-6 in SOURCES.md)", "",
         "| quantity | B15 | ours |", "|---|---|---|",
         f"| facets in total | 48 | {a2['ours']['facets_total']} |",
         f"| trivial (p ≥ 0) | 16 | {a2['ours']['trivial_after_projection']} (after projection) |",
         f"| non-trivial | 32 | {a2['ours']['nontrivial_after_projection']} |",
         f"| families under relabellings | 3 (2 non-trivial) | {a4['classes']} (sizes {a4['class_sizes']}) |",
         "",
         f"Our “36 raw” ones from the float run: {f36['nontrivial']} non-trivial + {f36['positivity_in_disguise']} "
         f"positivity inequalities written through the normalisation equalities (all 36 are among the exact facets: "
         f"{ok(f36['all_rows_among_exact_facets'])}). The count agrees with B15: **confirmed by citation**.",
         f"Every row is a facet (rank of the saturating vertices = dim−1): {ok(a2['ours']['every_row_is_facet'])}; "
         f"polytope dimension {a2['ours']['polytope_dim']}.",
         "",
         "### A.3 lrs against pycddlib (cdd.gmp)", "",
         f"- facets: cdd {a3['cdd_count']}, lrs {a3['lrs_count']}; equalities: cdd {a3['cdd_equalities']}, lrs {a3['lrs_equalities']}",
         f"- the sets coincide after projection onto the affine hull: **{ok(a3['sets_equal_after_projection'])}** "
         f"(the raw rows coincided too: {ok(a3['raw_sets_equal_before_projection'])})",
         f"- negative control (a spoiled facet is detected by the comparison): {ok(a3['negative_control_spoiled_set_detected'])}",
         "",
         "### A.4 Calibration of the canonicaliser (known answer: 3 classes of 16)", "",
         f"- the B15 relabelling group of order {a4['group_order']}, all generators are automorphisms: "
         f"{ok(all(a4['generators_are_automorphisms'].values()))}",
         f"- classes: **{a4['classes']}**, sizes {a4['class_sizes']}; GYNI class {a4['gyni_class_size']}, "
         f"LGYNI {a4['lgyni_class_size']}, positivity {a4['positivity_class_size']}",
         f"- control “without projection”: {a4['control_no_projection_classes']} classes (an artefact, cf. “7 classes” in the spec)",
         f"- control “trivial group”: {a4['control_trivial_group_classes']} classes",
         f"- control “without conditional output flips”: {a4['control_group_without_conditional_flips_classes']} classes",
         ""]
    return L


def fmt_support(sup):
    return " + ".join(f"p({s})" for s in sup)


def stage_b(b, prereg):
    v, cr, g, fa, gr, cl = (b["vertices"], b["vertex_crosscheck"], b["gates"], b["facets"],
                            b["group"], b["classes"])
    L = ["## Stage B — the time-symmetric polytope (Def-II, without settings)", "",
         f"**Outcome: {b['outcome']}** _(under the criterion revoked by the architect's amendment; the "
         "classification in force is Stage B.2)_", "",
         "Definitions — PREREGISTRATION.md §1 (eq. (3)–(7) MH24 + D1: `p(a,b) = p(x,y) = 1/4`), "
         "coordinates `p(a,b,x,y)`, row order `abxy`.", "",
         "### B.2 Vertices and gates", "",
         f"- vertices: `P_AB` {v['P_AB']}, `P_BA` {v['P_BA']}, common {v['common']}, `P_TS` {v['P_TS_union']}; "
         f"denominators {v['denominators']}; affine dimension {b['affine_dim']} "
         f"(hull = normalisation + D1: {ok(b['hull_equals_norm_plus_D1'])})",
         f"- gates: GYNI {g['values']['GYNI']}, reversed GYNI {g['values']['GYNI_reversed']}, "
         f"LGYNI {g['values']['LGYNI_fwd']}, reversed LGYNI {g['values']['LGYNI_bwd']} — **{('passed' if g['pass'] else 'FAILED')}**",
         f"- GYNI and reversed GYNI are one and the same functional (D3): {ok(g['GYNI_equals_GYNI_reversed_as_functional'])}",
         f"- the literal form of eq. (9) at `N_α = 1`: setting 1 → maximum {g['MH9_literal_alpha1_max']} "
         f"(GYNI, the bound 3/4 is not tight); setting 0 → {g['MH9_literal_alpha0_max']} (> 3/4, the inequality is false). Hence D2.",
         "",
         "**Cross-check of the “deterministic vertices”.** Deterministic classical TS circuits "
         "(bijections (income, input) ↔ (outcome, output), wires of dimension 2):",
         ""]
    for k in ("anc1", "anc2", "anc4"):
        c = cr[k]
        L.append(f"- ancilla {k[3:]}: {c['distinct_distributions']} distributions, all inside `P_AB`: "
                 f"{ok(c['all_inside_P_AB'])}, vertices of `P_AB` reached: {c['vertices_of_P_AB_realized']} of {v['P_AB']}")
    L += ["",
          f"{v['P_AB'] - cr['anc4']['vertices_of_P_AB_realized']} vertices of `P_AB` are not reached. Example: `y = a ⊕ x·¬b` at "
          "uniform `x`. For it Bob needs both `a` and `x`, and Alice's bijection cannot pass both: if the output `o` "
          "determines `(a, x)`, then `(x, o)` takes no more than `d` values instead of `2d`. That is, eq. (3)–(4) together with D1 are "
          "necessary but not sufficient conditions for classically realisable correlations A≼B. By the preregistration "
          "this is not a stop: the main object is the polytope defined by eq. (3)–(7) (MH-13). The classical closure "
          "is analysed below, in the exploration.", "",
          "### Anti-vacuum tests of the group", "",
          f"G of order {gr['order_G']} (party exchange, time reversal, 4 flips); G without TR — of order {gr['order_G_without_TR']}.", "",
          "| generator | non-identical | automorphism | shifts the known ones | image valid |", "|---|---|---|---|---|"]
    for k, t in gr["generator_action_on_known"].items():
        L.append(f"| {k} | {ok(gr['generators_nontrivial'][k])} | {ok(gr['generators_automorphisms'][k])} | "
                 f"{', '.join(t['moves']) or '—'} | {ok(t['image_valid_same_bound'])} |")
    L += ["",
          "Negative controls (must be rejected): "
          + ", ".join(f"{k}: {'rejected' if v_ else 'ACCEPTED'}" for k, v_ in gr["negative_controls_rejected"].items()) + ".",
          f"The full group of local automorphisms (bijections of the pairs (a,x), (b,y) and the exchange, 1152 candidates) has order "
          f"{gr['full_local_automorphism_group_order']}; G ⊆ it: {ok(gr['G_subset_of_local'])}. Classes under the full group: "
          f"{cl['count_full_local_group']}. The directionality test is calibrated: LGYNI_fwd is directional — "
          f"{ok(cl['directional_test_control']['LGYNI_fwd_directional'])}, GYNI is directional — "
          f"{ok(cl['directional_test_control']['GYNI_directional'])}.", "",
          "### B.3 Facets", "",
          f"- cdd.gmp {fa['cdd']}, lrs {fa['lrs']}; they coincide after projection: **{ok(fa['cdd_equals_lrs_after_projection'])}**",
          f"- all valid: {ok(fa['all_valid'])}; all are facets (rank of the saturating vertices = dim−1): {ok(fa['all_are_facets'])}",
          f"- time: cdd {fa['seconds_cdd']} s, lrs {fa['seconds_lrs']} s; the whole process {b['resources']['seconds_total']} s, "
          f"peak RSS {b['resources']['max_rss_MB']} MB",
          "",
          "### B.4–B.5 Classes and comparison with the known ones", "",
          f"Classes under G: **{cl['count_G']}**; of them outside K: **{cl['new_classes']}**, directional outside K: "
          f"**{cl['new_directional_classes']}**. Facets in K: {cl['facets_in_K']}, outside K: {cl['facets_not_in_K']}.", "",
          "Readable form: `Σ_{t ∈ S} p(t) ≤ 1/2`, where `t = abxy`; at `p(a,b) = 1/4` this is a “game” with success no higher than 1/2. "
          "Each form was checked separately: the maximum on the vertices is 1/2, the face has dimension 8.", "",
          "| # | size | in K | directional | invariant under | S (weights 1), right-hand side 1/2 |", "|---|---|---|---|---|---|"]
    for i, c in enumerate(cl["list"], 1):
        df = c["display_form"]
        what = "p(0000) ≥ 0 (positivity)" if c["positivity"] else fmt_support(df["support_abxy_weight1"])
        L.append(f"| {i} | {c['size']} | {('yes: ' + '+'.join(c['K_readings'])) if c['in_K'] else 'no'} | "
                 f"{ok(c['directional'])} | {', '.join(df['invariant_under']) or '—'} | {what} |")
    kf = cl["known_face_dim(facet = dim-1)"]
    L += ["",
          f"**The known inequalities are not facets of `P_TS`.** Their maxima are attained (the gates), but the dimensions "
          f"of the faces are GYNI {kf['GYNI']}, LGYNI_fwd {kf['LGYNI_fwd']}, LGYNI_bwd {kf['LGYNI_bwd']} while a facet has "
          f"dimension {b['affine_dim'] - 1}. Of the {cl['K_size_distinct']} distinct elements of K all are valid on `P_TS` "
          f"({ok(cl['K_all_valid_on_P_TS'])}), facets are {cl['K_elements_that_are_facets_of_P_TS']} (positivity only).",
          "",
          f"**Separating point** z: `{cl['separating_point_z']}`. It satisfies every element of K: "
          f"{ok(cl['z_satisfies_all_K'])}; it lies in `P_TS`: {ok(cl['z_in_P_TS'])}. Hence `P_TS` is strictly smaller than "
          "the intersection of the forward and backward B15 polytopes, and the existence of facets outside K follows without enumeration.",
          ""]
    # predictions
    L += ["### Predictions and result", "",
          "| quantity | executor's prediction | range | obtained | in range |", "|---|---|---|---|---|"]
    rows = [("vertices of P_AB", 12, (12, 60), v["P_AB"]), ("vertices of P_TS", 20, (20, 120), v["P_TS_union"]),
            ("affine dimension", 9, (7, 9), b["affine_dim"]), ("facets of P_TS", 40, (10, 500), fa["distinct"]),
            ("classes under G", 5, (3, 20), cl["count_G"])]
    for n, pt, (lo, hi), got in rows:
        L.append(f"| {n} | {pt} | {lo}–{hi} | {got} | {ok(lo <= got <= hi)} |")
    L += [f"| outcome | there is a class outside K (P≈0.9); directional (P≈0.5) | — | outside K: {cl['new_classes']}, "
          f"directional: {cl['new_directional_classes']} | — |", "",
          "The architect's prediction (“there will be no new classes, everything will fit into the four known inequalities”) "
          f"**was not confirmed**: {cl['new_classes']} classes outside K, and GYNI and LGYNI are not facets at all. "
          "The prompt's criterion for a Stage C candidate (a class outside K **and** not mapping to itself under time reversal) "
          "**is not met**: all new classes are non-directional. The decision about Stage C is the architect's.", ""]
    d1 = b["def_I"]
    L += ["### Sensitivity control: Def-I (eq. (3)–(6) without D1)", "",
          f"- vertices `P_AB` {d1['P_AB']}, `P_TS` {d1['P_TS_union']}, affine dimension {d1['affine_dim']}, "
          f"facets {d1['facets']}, classes {d1['classes_G_restricted_to_automorphisms']}",
          f"- the conditional form of eq. (8) on mixtures of orders: value found {d1['max_conditional_GYNI_eq8_found_on_mixtures']} "
          f"> 1/2: {ok(d1['eq8_violated_by_causally_separable_mixture'])}. Without D1, MH24's own inequality (8) is "
          "violated by a causally separable mixture, so Def-I is inconsistent with MH24. This confirms the choice of D1 "
          "(predicted in the preregistration, item 6(iii)).", ""]
    return L


def explore(e):
    c = e["classical_closure"]
    L = ["## Exploration (NOT preregistered): the classically realisable closure", "",
         "The distribution of any deterministic classical TS circuit A≼B has the form "
         "`Σ μ(tA,tB) · ¼ · [a = tA(x)] · [y = tB(b)]`. Here `tA` fixes Alice's income as a function of her outcome, "
         "`tB` fixes Bob's outcome as a function of his income, and the weights μ satisfy `E|tA| = E|tB| = 1`. "
         "The closure over all dimensions is the image of the polytope of such μ. The reduction is calibrated: in dimension 2 "
         "it coincided with the direct enumeration of bijections "
         f"({', '.join(k + ': ' + ok(v['equal']) for k, v in e['reduction_calibration'].items())}).", "",
         "| sizes (dA, ancilla, dB) | distributions | accumulated extreme points A≼B |", "|---|---|---|"]
    for k, v in e["circuits"].items():
        L.append(f"| {k} | {v['distinct']} | {v['cumulative_extreme_points_AB']} |")
    L += ["",
          f"- closure A≼B: {c['AB_extreme_points']} vertices. The truncated enumeration reaches {c['AB_extreme_points_realized_by_truncated_search']} of them, "
          f"and all of its points lie in the closure: {ok(c['truncated_points_inside_closure'])}. The closure lies in `P_AB` (Def-II): "
          f"{ok(c['AB_closure_inside_Def_II_P_AB'])}; vertices of Def-II in the closure {c['Def_II_P_AB_vertices_in_closure']} of 18",
          f"- `P_TS^cl`: {c['TS_vertices']} vertices, dimension {c['affine_dim']}, {c['facets']} facets "
          f"(cdd = lrs: {ok(c['cdd_equals_lrs'])}; all valid: {ok(c['all_valid'])}; all facets: {ok(c['all_are_facets'])}); "
          f"TR is an automorphism: {ok(c['generators_automorphisms']['TR'])}",
          f"- classes under G: **{c['classes_G']}**, outside K: **{c['new_classes']}**, directional: **{c['new_directional']}**; "
          f"the faces GYNI/LGYNI_fwd/LGYNI_bwd have dimensions {c['known_face_dim(facet = dim-1)']['GYNI']}/"
          f"{c['known_face_dim(facet = dim-1)']['LGYNI_fwd']}/{c['known_face_dim(facet = dim-1)']['LGYNI_bwd']} "
          "(they are not facets)",
          "",
          "The qualitative conclusion is the same as for Def-II: there are new classes, there are no directional ones. Quantum TS circuits "
          "may occupy something between `P_TS^cl` and Def-II; this was not investigated.", ""]
    return L


def stage_b2(d, pt):
    i1, i2, i3, i4 = d["item1"], d["item2"], d["item3"], d["item4"]
    c = i1["calibration"]
    L = ["## Stage B.2 — attributability, origin of the vertices, sensitivity, closure", "",
         f"**Outcome: {d['outcome']['text']}**", "",
         "| class | mixed (U2) | survived U1 | class of facets of the classical closure |", "|---|---|---|---|"]
    for r in d["outcome"]["table"]:
        L.append(f"| {r['class']} | {ok(r['mixed'])} | {ok(r['survives_U1'])} | {ok(r['in_closure'])} |")
    L += ["", "By the prompt, next come the literature check and the letter to the MH24 authors, before any claim of novelty. "
          "Stage C is launched by the architect.", ""]
    if pt:
        L += ["### Precision", "",
              f"A triangle with vertex (1/3, 1), path V→H→V: cdd.gmp — {ok(pt['cdd_gmp']['pass'])}, "
              f"lrs — {ok(pt['lrs']['pass'])} (exactly `1/3`). Control via float `cdd`: it returned "
              f"`{pt['float_cdd_control']['vertices'][2][0]}`, the test failed, as required "
              f"({ok(not pt['float_cdd_control']['pass'])}). Precision gate: **{ok(pt['gate_pass'])}**.", ""]
    L += ["### Item 1 Attributability (U2)", "",
          "The attribution (SOURCES.md, D4): F ← eq. (3), (5) (forward causality), B ← eq. (4), (6) "
          "(backward). A terminological trap: eq. (3) forbids signalling **backwards** in time, but it is derived "
          "from **forward** causality.", "",
          f"- F: {i1['F_vertices']} vertices, {i1['F_facets']} facets; B: {i1['B_vertices']} vertices, {i1['B_facets']} facets; "
          f"dimensions {i1['F_B_affine_dim']}. The exchange and the flips preserve F and B: "
          f"{ok(all(v['F'] and v['B'] for k, v in i1['symmetries_preserve_F_B'].items() if k != 'TR'))}; "
          f"TR maps F to B: {ok(i1['TR_maps_F_to_B'])}",
          f"- F∩B: {i1['F_cap_B_vertices']} vertices (cdd = lrs: {ok(i1['F_cap_B_vertices_lrs_equal'])}), "
          f"TS ⊆ F∩B: {ok(i1['TS_inside_F_cap_B'])}, TS = F∩B: {ok(i1['TS_equals_F_cap_B'])}; "
          f"vertices of F∩B outside TS: {i1['F_cap_B_vertices_outside_TS']}",
          f"- the point z (`x = a, y = a⊕b`): in F — {ok(i1['z']['in_F'])} (via F_AB: {ok(i1['z']['in_F_AB'])}), "
          f"in B — {ok(i1['z']['in_B'])} (via B_BA: {ok(i1['z']['in_B_BA'])}), a vertex of F∩B — "
          f"{ok(i1['z']['vertex_of_F_cap_B'])}, in TS — {ok(i1['z']['in_TS'])}. It is cut off by "
          f"{i1['witness_z_first'][0]['cut_by_n_TS_facets']} facets of TS; one of them: "
          f"weights {{t: w}} = {{{', '.join(t + ':' + str(w) for t, w in i1['witness_z_first'][0]['one_cutting_facet_nicest']['weights'].items() if w)}}}, "
          f"right-hand side {i1['witness_z_first'][0]['one_cutting_facet_nicest']['rhs']}.",
          "- the meaning: z is forward-causal in the order A≼B and backward-causal in the order B≼A. TS requires that "
          "one and the same order be causal in both directions, and therefore z is cut off.", "",
          "**Calibration of the test** (it may fail):", "",
          f"- all 48 facets of K_fwd hold on F: {ok(c['K_fwd_all_hold_on_F'])}; their kinds: {c['K_fwd_kinds']}",
          f"- “forward-directional” ones exist among K_fwd: {ok(c['K_fwd_forward_directional_exists'])}; their images "
          f"under TR are “backward-directional”: {ok(c['TR_images_backward'])}",
          f"- LGYNI_fwd: {c['LGYNI_fwd']['kind']} (max on F {c['LGYNI_fwd']['max_F']}, on B "
          f"{c['LGYNI_fwd']['max_B']} in integer form, where the bound is 3)",
          f"- positivity: {c['positivity']}",
          f"- the control from the prompt (GYNI): **{c['GYNI_prompt_control']['kind']}**, exactly as predicted: under U2 "
          "GYNI ≡ reversed GYNI (D3), so it cannot be violated on B. The prompt's control is incapable of "
          "showing directionality and was replaced by the calibration via K_fwd (a deviation from the preregistration).",
          f"- calibration gate: **{ok(c['pass'])}**", "",
          "| # | size | class kind | member kinds | max on F | max on B | bound |", "|---|---|---|---|---|---|---|"]
    for k, cl in enumerate(i1["classes"], 1):
        L.append(f"| {k} | {cl['size']} | {cl['class_kind']}{' (positivity)' if cl['positivity'] else ''} | "
                 f"{cl['member_kinds']} | {'–'.join(dict.fromkeys(cl['max_F_range']))} | "
                 f"{'–'.join(dict.fromkeys(cl['max_B_range']))} | {cl['rhs']} |")
    L += ["", "(maxima in the primitive integer form of the projection; the class numbering is as in Stage B: "
          "1 = N1 [32], 3 = N2 [16].)", "",
          "### Item 2 Origin of the vertices", "",
          f"- Stage B: {i2['stage_B_method']}.",
          f"- An independent recomputation via lrs (H→V): A≼B {i2['lrs_AB']}, B≼A {i2['lrs_BA']}; it agrees with cdd.gmp: "
          f"{ok(i2['cdd_equals_lrs'])}; the union = the Stage B vertices: {ok(i2['union_equals_stage_B_vertices'])}. "
          "The main Stage B polytope is confirmed.",
          f"- The fractional vertices in Stage B were there from the very beginning (the denominators 1, 4, 8 are listed in RESULTS Stage B). "
          f"By largest denominator: {i2['AB_vertex_max_denominator_histogram']}, supports of size "
          f"{i2['AB_vertex_support_sizes']}; the largest coordinate {i2['max_coordinate_any_vertex']}. "
          "Under U2 every point has p(a,b) = 1/4, so coordinates larger than 1/4 and 0/1 vertices cannot exist. "
          "4 vertices are uniform on 4 points (`x=a⊕c1, y=b⊕c2`), 14 are uniform on 8 points.", "",
          "### Item 3 Sensitivity to uniformity", "",
          "| variant | vertices A≼B | vertices TS | dimension | facets | group | classes | mixed classes | z ∈ TS |",
          "|---|---|---|---|---|---|---|---|---|"]
    L.append(f"| U2 | 18 | 32 | 9 | {i1['TS_facets']} | 64 | {len(i1['classes'])} | "
             f"{sum(1 for x in i1['classes'] if x['class_kind'] == MIXED)} | NO |")
    for u in ("U1", "U0"):
        x = i3[u]
        L.append(f"| {u} | {x['V_AB']} | {x['V_TS']} | {x['affine_dim']} | {x['facets']} | {x['group_order']} | "
                 f"{x['classes']} | {x['mixed_classes']} | {ok(x['z_in_TS'])} |")
    L += ["", "Survival of the new U2 classes:", ""]
    for u in ("U1", "U0"):
        for name, v in i3[u]["survival_of_U2_new_classes"].items():
            L.append(f"- {u}: {name} — survived: **{ok(v['survives'])}** ({v['n_facets']} facets), "
                     f"attributability in {u}: {v.get('attribution_in_' + u)}")
    L += ["", "Not a single new class is marked as “a consequence of the U2 assumption”.",
          f"- U1: TR is an automorphism: {ok(i3['U1']['generators_automorphisms']['TR'])} (group of order "
          f"{i3['U1']['group_order']}). The linear form (8) under U1: max {i3['U1']['eq8_linear_max']}. "
          f"The conditional form (10) on 4000 random mixtures: max {i3['U1']['eq10_conditional_max_found']}, "
          f"no violation found (this is not a proof of validity). The prediction “it is violated” was not confirmed.",
          f"- U0: the conditional form (8) reproduces {i3['U0']['eq8_conditional_max_found']} > 1/2.", "",
          "### Item 4 Closure of the classical circuits", "",
          f"- All {i4['closure_TS_vertices']} vertices of the closure lie in TS (Def-II): **{ok(i4['all_closure_vertices_inside_TS'])}** "
          f"(outside: {i4['n_outside']}). Of them, {i4['closure_vertices_that_are_TS_vertices']} are vertices of TS; "
          f"the rest are fractional points inside TS (denominators {i4['closure_vertex_denominators']}).",
          f"- Construction check: for each of the {i4['explicit_circuits']['n']} vertices of the μ polytope an explicit "
          f"circuit with bijections of dimension N ∈ {i4['explicit_circuits']['N_values']} was assembled. The direct run matched the image of μ: "
          f"{ok(i4['explicit_circuits']['all_equal_image'])}; eq. (3), (4) and U2 hold: "
          f"{ok(i4['explicit_circuits']['all_satisfy_eq3_eq4_U2'])}. Hence the closure is built correctly, "
          "and (3)–(6) really are necessary on classical circuits.",
          f"- Where the growth in the number of vertices comes from (48 against 32): the closure is a strictly smaller polytope inside TS. "
          f"It cuts off 16 classically unrealisable vertices of TS (8 per order) and gets new fractional vertices "
          f"in their place. Facets {i4['closure_facets']} (cdd = lrs: {ok(i4['cdd_equals_lrs'])}), "
          f"the affine hull is the same as that of TS: {ok(i4['same_affine_hull_as_TS'])}.",
          f"- Attributability of the closure classes (the same F, B; by B15-7 time-forward correlations are "
          f"deterministic, so the H-variant of F_AB coincides with the classically realisable time-forward set with U2 imposed on it): mixed "
          f"{i4['mixed_classes']} of {len(i4['classes']) - 1} non-positivity ones; kinds: "
          + ", ".join(f"{x['size']}:{'/'.join(x['kinds'])}" for x in i4["classes"]) + ".",
          f"- The classes N1 and N2 are also classes of facets of the closure: {i4['TS_new_classes_also_closure_classes']}.", ""]
    cls = i1["classes"]
    mixed_new = [c["class_kind"] == MIXED for c in cls if not c["positivity"]]
    surv = [v["survives"] for v in i3["U1"]["survival_of_U2_new_classes"].values()]
    rows = [
        ("precision: exact = 1/3, the float control fails", "0.99", ok(pt and pt["gate_pass"])),
        ("z ∈ F, z ∈ B, TS ⊊ F∩B", "0.95", ok(i1["z"]["in_F"] and i1["z"]["in_B"] and not i1["TS_equals_F_cap_B"])),
        ("both new classes are mixed", "0.9", ok(all(mixed_new))),
        ("positivity and GYNI are common", "0.95", ok(i1["calibration"]["positivity"] == COMMON
                                                      and i1["calibration"]["GYNI_prompt_control"]["kind"] == COMMON)),
        ("there is a K_fwd violated on B", "0.8", ok(i1["calibration"]["K_fwd_forward_directional_exists"])),
        ("z is a vertex of F∩B", "0.7", ok(i1["z"]["vertex_of_F_cap_B"])),
        ("vertices of F∩B: 40 (33–300)", "—", f"{i1['F_cap_B_vertices']} ({ok(33 <= i1['F_cap_B_vertices'] <= 300)})"),
        ("item 2: lrs = Stage B; 14 vertices with 1/8, 4 with 1/4", "0.97", ok(i2["pass"] and i2["AB_vertex_max_denominator_histogram"] == {"4": 4, "8": 14})),
        ("U1: TR is not an automorphism, group 32", "0.85", ok(not i3["U1"]["generators_automorphisms"]["TR"] and i3["U1"]["group_order"] == 32)),
        ("at least one new class survives U1", "0.6", ok(any(surv))),
        ("the conditional (10) is violated under U1", "0.6", ok(i3["U1"]["eq10_violated"])),
        ("U0 reproduces 227/390", "0.97", ok(i3["U0"]["eq8_conditional_max_found"] == "227/390")),
        ("all 48 vertices of the closure are inside TS", "0.95", ok(i4["all_closure_vertices_inside_TS"])),
        ("the new vertices of the closure are fractional, denominators are multiples of 3", "0.8", ok(12 in i4["closure_vertex_denominators"])),
        ("≥1 closure class is mixed / all 6", "0.95 / 0.5", f"{ok(i4['mixed_classes'] >= 1)} / {ok(i4['mixed_classes'] == 6)}"),
        ("N1 or N2 is a closure class", "0.5", ok(any(i4["TS_new_classes_also_closure_classes"].values()))),
        ("outcome “candidate”", "0.35", ok(d["outcome"]["text"].startswith(CANDIDATE))),
    ]
    L += ["### B.2 predictions and result", "", "| executor's prediction | confidence | came true |", "|---|---|---|"]
    L += [f"| {a} | {b_} | {c_} |" for a, b_, c_ in rows]
    L += ["", "The architect's predictions: TS ⊊ F∩B — "
          f"**{ok(not i1['TS_equals_F_cap_B'] and i1['z']['in_F'] and i1['z']['in_B'])}**; at least one new "
          f"class is mixed — **{ok(any(mixed_new))}**; at least one survives U2 → U1 — **{ok(any(surv))}**.", "",
          "### Deviations from the prompt", "",
          "- The calibration via GYNI was replaced by the calibration via K_fwd: under U2 GYNI coincides with reversed GYNI, "
          "so it cannot be violated on B (preregistered).",
          "- “Confirmed in both constructions” is understood as follows: the canonical form of the class coincides with the class "
          "of facets of the classical closure (the definition from the preregistration). For the closure U1 ≡ U2: "
          "for classical circuits p(x,y) = 1/4 holds automatically, so “survived U1” is checked "
          "only for the H-construction.",
          "- A defect of the lrs parser was found and fixed. On overflow lrs restarts in 128-bit "
          "arithmetic and prints its output anew. The parser now takes the last complete block, and on a "
          "non-numeric line it fails instead of skipping it. In Stage A and B there were no restarts: the lrs "
          "counts agreed with cdd. Everything was recomputed from scratch via `run_all.sh`.",
          "- The conditional form (10) under U1 was checked only by random search; no conclusion about its validity is drawn.",
          "- `SOURCES.md` (the D4 citations) was committed together with the B.2 preregistration — also before the run.", ""]
    return L


def f6(x):
    try:
        return f"{float(x):.6f}"
    except (TypeError, ValueError):
        return str(x)


def stage_c(c):
    d6, c1, c2 = c["D6"], c["C1"], c["C2"]
    fn = c["functionals"]
    L = ["## Stage C — do N1 and N2 get violated by physically meaningful processes", "",
         f"**Outcome: {c['outcome']}**", "",
         f"Mode: {'DEBUG (few starts)' if c['fast_mode'] else 'full'}; see-saw starts: qubits "
         f"{c['starts']['2']}, qutrits {c['starts']['3']}; solver {c['solver']} (fallback — SCS). "
         f"SDP solves: {c['solver_stats']['solves']}, retries via SCS: {c['solver_stats']['fallback_scs']}, "
         f"discarded starts: {c['solver_stats']['failed']}.", "",
         "### The main point", "",
         "- **Lemma D6.** With `u, v` marginalised, any process of the MH24 formalism reduces to an ISO matrix "
         "`(1/d_Ad_B)(1 + T_{A_O B_I} + S_{A_I B_O})`. Such a matrix is always a mixture of a one-way channel "
         "A→B and a one-way channel B→A. Hence, in the Stage B scenario nothing in the formalism violates any "
         "facet of the main TS polytope, including N1 and N2, in any dimensions. The proof is in "
         "PREREGISTRATION_C.md §2, the numerical check is below.",
         "- **The flip side.** If preselection is allowed (the statistics are conditional on u), N1 and N2 are already violated by "
         "a process with a definite order (the z circuit, below). Therefore N1 and N2 do not witness "
         "indefiniteness in any regime of the formalism: without selection nothing violates them, with selection they are "
         "violated even by causally ordered processes. The central Stage C hypothesis is untestable in this setting.", "",
         "### C.0 Functionals and scale", "",
         "The full form of the classes (`t = abxy`, weights 1; at p(a,b) = 1/4 these are games with success no higher than 1/2):", ""]
    for k in ("N1", "N2"):
        L.append(f"- **{k}** ({fn[k]['size']} facets): " + " + ".join(f"p({t})" for t in fn[k]["support"]) + " ≤ 1/2")
    for k in sorted(x for x in fn if x.startswith("cl")):
        L.append(f"- **{k}** (a class of the classical closure only, {fn[k]['size']} facets): "
                 + " + ".join(f"{w}·p({t})" if w != "1" else f"p({t})" for t, w in fn[k]["support"].items())
                 + f" ≤ {fn[k]['rhs']}")
    L += ["", f"Closure classes that matched TS classes by canonical form: {c['closure_classes_matching_N1_N2']} "
          "(positivity, N1, N2).", "",
          "**Five numbers** (exact; for N1 and N2 — in game probabilities). The “maximum 3 at bound 1” from B.2 was "
          "in the units of the projection onto the affine hull; in probabilities this is 3/4 at bound 1/2.", "",
          "| class | bound | algebraic max under U2 | F | B | F∩B | TS (Def-II) | classical closure |",
          "|---|---|---|---|---|---|---|---|"]
    five = c["C0_five_numbers"]
    for k in [x for x in five if x != "U2_polytope_vertices"]:
        v = five[k]
        L.append(f"| {k} | {v['rhs']} | {v['algebraic_U2']} | {v['F']} | {v['B']} | {v['F_cap_B']} | {v['TS']} | {v['classical_closure']} |")
    L += ["", f"The U2 polytope (p ≥ 0, p(a,b) = p(x,y) = 1/4) has {five['U2_polytope_vertices']} vertices, these are ¼ × "
          "the permutation matrices. For N1 and N2 the sets F, B and F∩B attain the U2 algebraic maximum 3/4.", "",
          "The definitions of a laboratory, a process matrix, the validity conditions and the formula for p — SOURCES.md, MH-22…MH-28; "
          "what are not citations are D5 (the ¼ factor for R boxes) and D6. The class R was fixed in PREREGISTRATION_C.md §1 "
          "(commit c9d9095) before the computations.", "",
          "### Lemma D6: numerical check", ""]
    for dd in ("d2", "d3"):
        x = d6[dd]
        L.append(f"- {dd}: the literal maps Wcons2–4, vcons1–3, ucons1–3 allow {x['allowed_count']} "
                 f"basis elements (expected {x['expected']}), kinds {x['types']}; off-diagonal hits "
                 f"{x['non_diagonal_hits']}")
    L += [f"- the classifier distinguishes the classes: TF (without postselection) — {d6['TF_no_post']['count']} elements, "
          f"TB — {d6['TB_no_pre']['count']}, Wcons only — {d6['TS_only_Wcons']['count']}, OCB by B15 — "
          f"{d6['OCB_B15']['count']}; the TF kinds coincide with OCB: **{ok(d6['TF_equals_OCB_types'])}** "
          "(statement MH-27 confirmed at the level of member kinds)",
          f"- the decomposition W = qW₁ + (1−q)W₂ on 100 + 100 random W ∈ R on the positivity boundary (d = 2, 3): "
          f"**{ok(d6['decomposition_pass'])}** (worst min eig W₁, W₂: {d6['decomposition']['d2']['psd_W1']:.1e}, "
          f"{d6['decomposition']['d3']['psd_W2']:.1e}; reconstruction error ≤ "
          f"{max(v['recon'] for v in d6['decomposition'].values()):.1e})", "",
          "### C.1 Calibrations", ""]
    mh = c1["mh_example"]
    L += [f"1. **The MH24 example (MH-29): literally NOT passed**, the cause is localised in the paper.",
          f"   - Bob's operation at β = 1 with the factor 1/2 from the paper violates eq. (2): residual "
          f"{mh['literal_bobop']['bob_instrument_residual']}. With the factor 1/4 (“maximally mixed state”, as in the text) — "
          f"{mh['bobop_beta1_factor_1/4']['bob_instrument_residual']}.",
          f"   - Literal eq. (9): {f6(mh['literal_bobop']['eq9_literal'])} instead of (2+√2)/4 = 0.853553; "
          f"literal eq. (11): {f6(mh['literal_bobop']['eq11_literal'])} instead of 1/2.",
          f"   - An enumeration of the 36 assignments of “whose guess is required at (α, β)”: the paper's value (2+√2)/4 gives exactly one — "
          f"{mh['readings_reproducing_fwd']} (Bob's guess at β = 1, Alice's at β = 0; this is the original OCB game). "
          f"The value 1/2 for the reversed game also gives exactly one — {mh['readings_reproducing_bwd']}. The exact match "
          "with an irrational number under a unique reading confirms the conventions (CJ, subsystem order, operators).",
          f"   - exampleW satisfies Wcons and vcons and violates ucons ({f6(mh['constraint_residuals']['ucons1'])}): "
          "“requires pre-selection, but not post-selection” is confirmed. Machinery: **"
          f"{ok(mh['machinery_pass'])}**.",
          f"2. **Normalisation D5** (this calibration may fail): for random W ∈ R and TS operations "
          f"Σp = 1, p(a,b) = p(x,y) = 1/4 with deviation {c1['normalization_D5']['worst_deviation_TS']:.1e}. Control: "
          f"Bob's operation with forward causality only (backward residual "
          f"{c1['normalization_D5']['control_bob_backward_residual']}) gives a deviation of p(x,y) by "
          f"{c1['normalization_D5']['control_forward_only_bob_pxy_deviation']}. **{ok(c1['normalization_D5']['pass'])}**"]
    b = c1["b15"]
    L += [f"3. **OCB (B15).** The exact example: GYNI {b['wsimple']['GYNI']:.12f} (expected {b['wsimple']['GYNI_expected']:.12f}), "
          f"LGYNI {b['wsimple']['LGYNI']:.12f}. W_max from App. C with their instruments: GYNI {b['W_max_appC']['GYNI']:.10f} "
          f"against the smallest root of the polynomial {b['W_max_appC']['GYNI_expected_smallest_root']:.10f}. See-saw OCB on qubits: "
          f"GYNI {b['seesaw']['GYNI']['best']:.6f} (reference 0.5694), LGYNI {b['seesaw']['LGYNI']['best']:.6f} (0.8194); "
          f"starts {b['seesaw']['GYNI']['starts']}, failed {b['seesaw']['GYNI']['failed_starts'] + b['seesaw']['LGYNI']['failed_starts']}. "
          f"**{ok(b['pass'])}**"]
    ps = c1["postselection"]
    L += [f"4. **Postselection attains the maximum.** A process with no link between the parties (preparation of the inputs = u, "
          f"measurement of the outputs = v; ΣᵥW satisfies vcons: {ok(ps['sum_v_satisfies_vcons'])}, ΣᵤW satisfies ucons: "
          f"{ok(ps['sum_u_satisfies_ucons'])}, Σᵤᵥ W ∈ R: {ok(ps['sum_uv_in_R'])}). Conditionally on the event (u, v): "
          f"N1 = {ps['N1']['value']}, N2 = {ps['N2']['value']}, this is the U2 algebraic maximum 3/4, p(a,b) = 1/4 is preserved. "
          "The paper's claim about the whole class is reproduced, and moreover by a process with no link whatsoever between the laboratories.",
          f"5. **Solver:** a known problem — error {c1['solver']['known_problem_error']:.1e}; an infeasible one — status "
          f"`{c1['solver']['infeasible_status']}`, see-saw fails on it: {ok(c1['solver']['seesaw_raises_on_infeasible'])}. "
          f"**{ok(c1['solver']['pass'])}**",
          f"6. **Classical closure:** the maximum of each functional on its vertices equals the bound: "
          f"**{ok(all(c1['classical_closure_max_equals_bound'].values()))}**", "",
          f"C.1 gate (on the machinery): **{ok(c1['pass'])}**; the literal check of the MH24 example — **NO** (see item 1).", "",
          "### C.2 Hierarchy of processes", "",
          f"P3 with a common control ∈ R: {ok(c['P3_membership']['common_in_R'])}. P3 with independent controls ∈ R: "
          f"{ok(c['P3_membership']['independent_in_R'])}: the “forward/backward” branches give terms A_O B_O and A_I B_I, the "
          f"vcons/ucons residuals {max(c['P3_membership']['independent_residuals'].values())}; without selection such a process is impossible. "
          "P2 = R ∩ OCB = R: all ISO kinds are also allowed in OCB (D6), therefore P2 coincides with P4.", "",
          "| d | class | bound | P1: A→B | P1: B→A | P3 (common control) | P4 = R (= P2) |", "|---|---|---|---|---|---|---|"]
    for key, row in c2.items():
        dd, name = key.split("_", 1)
        g = lambda f: f6(row[f]["max"]) if f in row else "—"  # noqa: E731
        L.append(f"| {dd[1:]} | {name} | {fn[name]['rhs']} | {g('P1_AB')} | {g('P1_BA')} | {g('P3_common')} | {g('P4_R')} |")
    L += ["", f"Confirmed violations (mpmath, 50 digits; W and the instruments are valid): {c['violations'] or 'none'}.",
          f"Excesses from see-saw not confirmed by recomputation: {({k: v for k, v in c['unconfirmed_excess'].items() if v}) or 'none'}.", ""]
    ver = [(k, f, v["verify"]) for k, row in c2.items() for f, v in row.items() if isinstance(v, dict) and v.get("verify")]
    if ver:
        L += ["Recomputation of the witnesses (explicit W and instruments — `results/json/stage_c_witnesses.json`):", ""]
        for k, f, v in ver:
            L.append(f"- {k} / {f}: value (mpmath) {v['value_mp'][:14]}; shift of W under repair {v['W_repair_shift']:.1e}; "
                     f"instrument residual {v['instr_res']:.1e}; min eig of the instruments {v['instr_min_eig']:.1e}; W ∈ R: {ok(v['W_in_R'])}")
        L.append("")
    tf = c["TF_pre"]
    L += ["### Outside R: diagnostics of the regime with preselection", "",
          f"- **The z circuit** with a definite order A≼B and preselection of Alice's input |0⟩: it reproduces z exactly — "
          f"{ok(tf['z_circuit']['reproduces_z'])}. W is valid by OCB (residual {tf['z_circuit']['W_ocb_residual']}), it does not lie in R "
          f"({ok(not tf['z_circuit']['W_in_R'])}); after marginalising u it lies in R: {ok(tf['z_circuit']['u_marginal_W_in_R'])}. "
          f"The point z is cut off by {tf['z_cut_by_TS_facets']} facets of TS, these are members of N1 and N2. **A process with a definite order violates "
          "N1 and N2 as soon as preselection is allowed.**",
          f"- See-saw over the OCB class (TF) with TS operations: N1 up to {f6(tf['seesaw_N1']['max'])}, N2 up to {f6(tf['seesaw_N2']['max'])} "
          "(bound 1/2; outside the U2 hull the value depends on the chosen representative of the class).", "",
          "### C.3 Coherence of direction", "",
          "In R the control qubit can neither be prepared in |+⟩ (that is preselection) nor projected (that is postselection). "
          "Therefore W̄_P3 = ½(W_f + W_b) coincides identically with the dephased mixture, and the C.3 test is degenerate in R. "
          "There is no P3 violation in R, so the C.3 condition did not arise.", ""]
    rows = [
        ("C.0.2: U2 algebraic maximum 3/4, TS = 1/2", "0.9", five["N1"]["algebraic_U2"] == "3/4" and five["N2"]["algebraic_U2"] == "3/4" and five["N1"]["TS"] == "1/2"),
        ("C.0.2: F, B, F∩B attain 3/4", "0.5", all(five[k][x] == "3/4" for k in ("N1", "N2") for x in ("F", "B", "F_cap_B"))),
        ("D6(a): 19 and 129", "0.95", d6["d2"]["allowed_count"] == 19 and d6["d3"]["allowed_count"] == 129),
        ("D6(b): the decomposition", "0.97", d6["decomposition_pass"]),
        ("C.1.1: MH24 (2+√2)/4 and 1/2 literally", "0.9", truth(mh["literal_pass"])),
        ("C.1.2: B15 exactly and see-saw ±1e-3", "0.85", b["pass"]),
        ("C.1.4: postselection gives 3/4", "0.95", abs(ps["N1"]["value"] - 0.75) < 1e-12 and abs(ps["N2"]["value"] - 0.75) < 1e-12),
        ("C.1.5: the solver", "0.97", c1["solver"]["pass"]),
        ("C.2: N1, N2 are not violated in P1–P4 (d = 2, 3)", "0.95",
         not any(k.endswith(("N1", "N2")) for k in c["violations"])),
        ("C.2: P3 with independent controls ∉ R", "0.85", not c["P3_membership"]["independent_in_R"]),
        ("C.2: P1 (quantum) violates at least one of cl3–cl6", "0.4",
         any(k.startswith("d2_cl") and any(f.startswith("P1") for f in v) for k, v in c["violations"].items())),
        ("TF-pre: N1, N2 are violated, including by the z circuit", "0.95", tf["z_circuit"]["reproduces_z"] and tf["z_cut_by_TS_facets"] > 0),
        ("C.3: in R the coherent P3 = the dephased one", "0.95", True),
        ("bottom line: “P4 does not violate” (N1, N2)", "0.95", not any(k.endswith(("N1", "N2")) for k in c["violations"])),
    ]
    L += ["### C predictions and result", "", "| executor's prediction | confidence | came true |", "|---|---|---|"]
    L += [f"| {a} | {b_} | {ok(r)} |" for a, b_, r in rows]
    n12 = any(k.endswith(("N1", "N2")) for k in c["violations"])
    L += ["", f"The architect's predictions: P1 does not violate — **{ok(not n12)}** (for N1 and N2; the closure classes cl3–cl6 "
          "are violated by quantum P1, but those are facets of the classical, not the Def-II, polytope); P2 does not violate N1 and N2 — "
          f"**{ok(not n12)}**; P3 violates at least one of N1, N2 without postselection — **{ok(n12)}**; the item about dephasing — "
          "did not arise.", "",
          "### Deviations from the prompt", "",
          "- Qutrits: only N1 and N2 for P4 (⊇ P1, P2) and P3. The full set (6 functionals × 3 families) would have taken "
          "hours, while lemma D6 settles the question for any dimensions analytically.",
          "- Solver: on `optimal_inaccurate` the step is retried via SCS (eps 1e-9); if it is still not `optimal`, the start is discarded. "
          "The preregistration said “fails on any status other than optimal”; values from non-optimal solutions "
          "are still not accepted.",
          "- Violations are counted only after repairing positivity (W is shifted towards 1/d², a valid M₀ = 1/(2d)·1 is "
          "mixed into the instruments; both operations preserve the linear conditions) and recomputing in mpmath.",
          "- The MH24 example is not reproduced literally (see C.1.1); the cause is localised in the paper, and to calibrate "
          "the machinery an independent D5 check, which may fail, was added.",
          "- The “SDP over the whole class” (P4) is non-linear in (W, instruments), so see-saw only gives lower bounds. "
          "The upper bound “no higher than the bound” is given by lemma D6, not by a numerical computation.", ""]
    return L


def stage_d(D):
    def mx(tab, pref):
        """maximum over orders: {cl: {d: max}}"""
        r = {}
        for k, v in tab.items():
            name, order, d = k.split("_")
            r.setdefault(name, {}).setdefault(d, []).append((v["max"], order, v))
        return r
    L = ["## Stage D — the quantum-classical gap on cl3–cl6", "",
         f"Mode: {'DEBUG' if D['fast'] else 'full'}; see-saw starts (D.4): {D['starts']}; SDP solves "
         f"{D['solver_stats']['solves']}, retries via SCS {D['solver_stats']['fallback_scs']}, discarded starts "
         f"{D['solver_stats']['failed']}; time {D['seconds']} s.", "",
         "### The main point: the gap is CHSH and the Tsirelson bound in relabelled roles", "",
         "Derivation D8 (PREREGISTRATION_D.md §2, written down before the computations) was checked numerically. A TS process with a definite "
         "order and without selection is equivalent to a Bell scenario on a maximally entangled state:",
         "- Alice's “input” is her **outcome** x, the “result” is her **income** a;",
         "- for Bob the input is the income b, the result is the outcome y;",
         "- the marginals are subject to the conditions `P(a|0)+P(a|1)=1`, `P(y|0)+P(y|1)=1`.",
         "",
         "Eq. (3) and (4) of MH24 are no-signalling in these roles. Def-II P_AB is the NS set, the classical "
         "closure is the local set, the 8 “unrealisable” vertices of P_AB are PR boxes. The backward normalisation "
         "forbids transmitting information about x through the channel, and the channel works as an entangled resource without signalling.", ""]
    d8 = D["D8"]
    L += [f"- The reduction TS ↔ (σ, F) ↔ Bell on random points (d = 2, 3, 4, complex and real): worst "
          f"deviation {max(d8['random'].values()):.1e}. On the Stage C witnesses: "
          f"{sum(1 for v in d8['stage_c_witnesses'].values() if v['p_error'] < 1e-8)} of {len(d8['stage_c_witnesses'])} "
          f"were reproduced (error p < 1e-8). The rest are mixtures of orders (P4, P3), for which the single-order "
          "reduction is not applicable, see the table in the JSON.",
          f"- PR boxes: vertices of Def-II P_AB outside the classical closure {D['PR_boxes']['n_outside_closure']}, all "
          f"PR boxes: **{ok(D['PR_boxes']['all_PR'])}**.", ""]
    ch = D["D01_chsh"]
    L += ["### D.0.1 The classes cl3–cl6 as CHSH", "",
          "For each class and order — a check of whether the functional on aff(P_order) equals α·CHSH_c + β, "
          "where CHSH_c means the win at a ⊕ y = (x⊕c₁)(b⊕c₂) ⊕ c₃ (exact arithmetic).", "",
          "| class | order | CHSH (c₁,c₂,c₃) | α | β |", "|---|---|---|---|---|"]
    for k, v in ch.items():
        name, order = k.split("_")
        L.append(f"| {name} | {order} | {tuple(v['chsh']) if v else 'not CHSH'} | {v['alpha'] if v else '—'} | {v['beta'] if v else '—'} |")
    L += ["", "Where it says “not CHSH”, the class on that order is not violated by anything: the NS maximum (Def-II) equals "
          "the classical bound, see D.3. The gap exists exactly on those orders where the class is a relabelled CHSH.",
          "", "If a class on an order equals α·CHSH + β, then its classical bound, quantum maximum and NS maximum are "
          "the images of 3/4, (2+√2)/4 and 1 under the map t ↦ αt + β (CHSH here is the win probability with "
          "the factor ¼).", ""]
    an = D["D02_analytic"]
    L += ["### D.0.2 The minimal witness (qubits, analytically)", ""]
    for k, v in an.items():
        L.append(f"- **{k}** ({v['order']}): value **{v['value_exact']}** ≈ {v['value_float']:.10f} at bound {v['rhs']}; "
                 f"TS form in mpmath: {v['ts_value_mp'][:16]}; residuals: reduced {v['reduced_residual']:.1e}, "
                 f"instruments {v['ts_instrument_residual']:.1e}.")
    L += ["",
          "In words (the identity channel A_O→B_I):",
          "- **Alice** discards her input. The outcome x is equiprobable (this is Alice's “coin”). She prepares her own "
          "state in the Z basis at x = 0 or the X basis at x = 1, and the value of the bit is fixed by the income a (with a relabelling "
          "depending on x).",
          "- **The channel** passes the qubit to Bob.",
          "- **Bob** measures along (Z ± X)/√2, the sign is chosen by the income b; the result is the outcome y. To the output he gives "
          "a maximally mixed state.",
          "",
          "The backward normalisation holds because, averaged over a, Alice's state is maximally mixed for "
          "every x. Therefore x is not transmitted — only the correlation of a with x is. This is a BB84-like scheme, in which the basis is "
          "an outcome rather than a setting.", ""]
    L += ["### D.1 Completeness of the classical closure", "",
          "**The proof** is derivation D7 (PREREGISTRATION_D.md §1). Classical TS circuits A≼B of any dimension are "
          "exactly the local models `¼ E_λ q_λ(a|x) r_λ(y|b)` with averaged conditions on the marginals. Their set "
          "is the image of the polytope M from Stage B; the vertices of M are rational and are realised at N ≤ 4. The bound for cl3–cl6 "
          "is proved for all dimensions.", "", "Numerical control (see-saw with diagonal σ and F):", ""]
    for name, dims in mx(D["D1_classical"], "").items():
        L.append(f"- {name}: " + ", ".join(f"d={d[1:]}: {max(v for v, _, _ in lst):.6f}" for d, lst in sorted(dims.items()))
                 + f" (bound {dims[next(iter(dims))][0][2]['rhs']})")
    L += [""]
    fw = D["D2_forward"]
    L += ["### D.2 Control: the purely forward scenario", "",
          "Operations with forward normalisation only, order A≺B, p(a,b) = 1/4. The functionals were carried over literally "
          "(the same weights on p(a,b,x,y)); the classical maximum with the filter p(x,y) = 1/4 (F_AB) is shown separately.", "",
          "| class, order | TS bound | classical max (literally) | classical max with U2 | the “send a” circuit | quantum see-saw | gap |",
          "|---|---|---|---|---|---|---|"]
    for k, v in fw.items():
        q = "all starts failed" if v["quantum_seesaw_max"] is None else f"{v['quantum_seesaw_max']:.6f}"
        g = "—" if v["gap"] is None else f"{v['gap']:.1e}"
        L.append(f"| {k} | {v['rhs']} | {v['classical_max_literal']} | {v['classical_max_with_U2_filter']} | "
                 f"{v['circuit_send_a_value']:.6f} | {q} (failed {v['failed_starts']}) | {g} |")
    gaps = [v["gap"] for v in fw.values() if v["gap"] is not None]
    if len(gaps) < len(fw):
        L.append("")
        L.append(f"For {len(fw) - len(gaps)} rows the quantum see-saw did not produce a single optimal solution. For them "
                 "the gap is not checked numerically, but the argument below (the quantum set lies inside the classical "
                 "polytope) does not depend on the numerical computation.")
    L += ["", f"The largest “quantum − classical” gap in the forward scenario: {max(gaps):.1e}. "
          f"**There is {'no gap' if max(gaps) < 1e-6 else 'A GAP'}.** The reason: in the forward scenario a classical channel "
          "of unbounded dimension transmits a and realises any vertex of the time-forward polytope "
          "(B15-7: the vertices are deterministic). The quantum set lies inside that polytope, so it cannot "
          "beat the classical one. The “send a” calibration saturates the quantum maximum.", ""]
    np_ = D["D3_npa"]
    cal = np_["calibration_CHSH"]
    L += ["### D.3 Upper bound: NPA", "",
          f"Calibration (NPA08): CHSH without conditions on the marginals — level 1+AB {cal['level_1+AB']:.9f}, level 2 "
          f"{cal['level_2']:.9f}, the Tsirelson bound {cal['tsirelson']:.9f}: **{ok(cal['pass'])}**.", "",
          "| class, order | classical (LP) | NPA 1+AB | NPA 2 | NPA without conditions | NS (Def-II) | in [classical, NS] |",
          "|---|---|---|---|---|---|---|"]
    for k, v in np_.items():
        if k == "calibration_CHSH":
            continue
        L.append(f"| {k} | {v['local_constrained']} | {v['npa_1+AB']:.9f} | {v['npa_2']:.9f} | "
                 f"{v['npa_1+AB_without_marginal_constraints']:.9f} | {v['NS_constrained(DefII)']} | {ok(v['between_local_and_NS'])} |")
    L += ["", "NPA bounds from above all quantum Bell correlations (any states and dimensions), "
          "and by D8 quantum TS correlations with a definite order are a subset of them. By lemma D6 mixtures of orders do not "
          "increase a linear functional. If NPA agrees with see-saw, the optimum has been found.", ""]
    L += ["### D.4 Dimension and reality", "",
          "| class | d | complex (max over orders) | real |", "|---|---|---|---|"]
    cx, rl = mx(D["D4_complex"], ""), mx(D["D4_real"], "")
    for name in sorted(cx):
        for d in sorted(cx[name]):
            L.append(f"| {name} | {d[1:]} | {max(v for v, _, _ in cx[name][d]):.9f} | {max(v for v, _, _ in rl[name][d]):.9f} |")
    ver = [(k, v["verify"]) for tab in ("D4_complex", "D4_real") for k, v in D[tab].items() if v.get("verify")]
    worst = max((abs(float(v["ts_value_mp"]) - D[t][k]["max"]) for t in ("D4_complex", "D4_real")
                 for k, v2 in D[t].items() for v in [v2.get("verify")] if v), default=0)
    real_imag = max((v["verify"]["real_max_imag"] for v in D["D4_real"].values() if v.get("verify")), default=0)
    L += ["", f"All excesses were recomputed in TS form in mpmath ({len(ver)} witnesses); the largest discrepancy "
          f"with see-saw is {worst:.1e}. The imaginary parts of the real witnesses: ≤ {real_imag:.1e}.",
          "At d = 3 the maximum is lower than at d = 2 and 4. The D8 reduction fixes a maximally entangled state "
          "of dimension d, and the qubit CHSH strategy does not embed as a whole into an odd dimension; at d = 4 "
          "the value returns to 3+√2. No value above 3+√2 was found at any dimension, which is consistent with NPA.", ""]
    L += ["### D.5 “Rotated-classical” operations", "",
          "A rotation U⊗V of Alice's operation is absorbed by the channel and Bob's measurement, so a “rotated-classical” Alice is "
          "diagonal σ with an arbitrary channel and F. Mixtures of such operations give jointly measurable "
          "`A_{a|x}`, and jointly measurable measurements on one side generate only local correlations.", ""]
    for tab, lab in (("D5_alice_classical", "Alice classical, Bob quantum"), ("D5_bob_classical", "Bob classical, Alice quantum")):
        L.append(f"- {lab}: " + "; ".join(f"{name} {max(v for dd_ in dims.values() for v, _, _ in dd_):.6f}"
                                           for name, dims in mx(D[tab], "").items()))
    L += ["", "Observation: the gap requires incompatible measurements on **both** sides, as in CHSH.", ""]
    # --- outcome and predictions
    viol_orders = [k for k, v in np_.items() if k != "calibration_CHSH" and float(Fraction(v["NS_constrained(DefII)"])) > float(Fraction(v["local_constrained"]))]
    npa_q = {k: np_[k]["npa_1+AB"] for k in viol_orders}
    ss_q = {}
    for k in viol_orders:
        name, order = k.split("_")
        ss_q[k] = max(D["D4_complex"][f"{name}_{order}_d{d}"]["max"] for d in (2, 3, 4))
    npa_match = all(abs(npa_q[k] - ss_q[k]) < 1e-6 for k in viol_orders)
    d1_num = all(v["max"] <= v["rhs"] + 1e-6 for v in D["D1_classical"].values())
    fw_gaps = [v["gap"] for v in D["D2_forward"].values() if v["gap"] is not None]
    d2_nogap = bool(fw_gaps) and max(fw_gaps) < 1e-6
    tsir = {k: (float(Fraction(np_[k]["local_constrained"])) + (np.sqrt(2) - 1) *
                (float(Fraction(np_[k]["NS_constrained(DefII)"])) - float(Fraction(np_[k]["local_constrained"]))))
            for k in viol_orders}
    tsir_match = all(abs(npa_q[k] - tsir[k]) < 1e-6 for k in viol_orders)
    grow = any(D["D4_complex"][f"{k.split('_')[0]}_{k.split('_')[1]}_d{d}"]["max"] > ss_q[k] + 1e-6 for k in viol_orders for d in (3, 4))
    real_ok = all(abs(max(D["D4_real"][f"{k.split('_')[0]}_{k.split('_')[1]}_d{d}"]["max"] for d in (2, 3, 4)) - npa_q[k]) < 1e-6
                  for k in viol_orders)
    d5 = all(v["max"] <= v["rhs"] + 1e-6 for t in ("D5_alice_classical", "D5_bob_classical") for v in D[t].values())
    chsh_ok = all(D["D01_chsh"][k] is not None for k in viol_orders)
    outcome = ("A TSIRELSON-TYPE BOUND: D.1 is proved, in D.2 there is no gap, D.3 agreed (NPA = see-saw)"
               if (d1_num and d2_nogap and npa_match) else "not all outcome conditions are met — see the table")
    L = L[:2] + [f"**Outcome: {outcome}.** A caveat: by D8 and D.0.1 this is literally the Tsirelson bound for CHSH in "
                 "relabelled roles, not a new effect (literature check: temporal CHSH — Fritz 2010, Brukner et al. 2004).",
                 ""] + L[2:]
    L += ["### D predictions and result", "", "| executor's prediction | confidence | came true |", "|---|---|---|"]
    rows = [
        ("D8: the reduction is numerically exact (≤ 1e-10) on random points", "0.95", max(d8["random"].values()) < 1e-10),
        ("D8: the 8 vertices outside the closure are PR boxes", "0.9", D["PR_boxes"]["all_PR"] and D["PR_boxes"]["n_outside_closure"] == 8),
        ("D.0.1: cl_k on the violated order = a relabelled CHSH", "0.7", chsh_ok),
        ("D.0.2: the qubit BB84/CHSH witness gives exactly 3+√2 (cl3)", "0.75", D["D02_analytic"]["cl3"]["value_exact"] == "sqrt(2) + 3"),
        ("D.1: the classical one ≤ the bound at d = 2…6", "0.97", d1_num),
        ("D.2: there is no gap in the forward scenario", "0.95", d2_nogap),
        ("D.3: NPA = the Tsirelson image (3+√2; 7/2+√2)", "0.85", tsir_match),
        ("D.4.1: d = 3, 4 does not grow", "0.9", not grow),
        ("D.4.2: real QM attains the optimum", "0.9", real_ok),
        ("D.5: a rotated-classical side — no gap", "0.95", d5),
        ("bottom line: “a Tsirelson-type bound”", "0.8", outcome.startswith("A TSIRELSON-TYPE BOUND")),
    ]
    L += [f"| {a} | {b_} | {ok(r)} |" for a, b_, r in rows]
    L += ["", "The architect's predictions: D.1 (the closure is complete, the bound is provable) — **YES** (D7); "
          f"D.2 (there is no gap) — **{ok(d2_nogap)}**; D.3 (3+√2 is the optimum over all dimensions) — **{ok(npa_match and tsir_match)}**; "
          f"D.4.1 (does not grow) — **{ok(not grow)}**; D.4.2 (real QM attains it) — **{ok(real_ok)}**.", "",
          "### Interpretation", "",
          "The architect's hypothesis (“the gap is created by the time symmetry of the operations, in the forward picture there is none”) "
          "is formally confirmed: in D.2 there is no gap. The mechanism, however, is standard. The backward normalisation "
          "forbids the channel to carry information about the outcome x, and a circuit with a definite order becomes "
          "a no-signalling Bell scenario on a maximally entangled resource (D8), while the gap is CHSH non-locality. "
          "The equivalence of sequential (temporal) correlations to singlet ones is known: BTCV04, FR10. "
          "What may be new is only the packaging: TS operations with incomes and outcomes, in which Alice's outcome plays "
          "the role of a setting. The literature check did not find such a formulation, but that is a reformulation, not a new inequality. "
          "Lemma D6 in the general two-sided form was not found; the closest single-slot analogue is AB26 "
          "(arXiv:2602.00856), which has to be cited.", "",
          "### Deviations from the prompt", "",
          "- D.3: instead of a “prepare-and-measure hierarchy”, NPA for the equivalent Bell scenario (D8) was used. "
          "This is stricter: NPA bounds all quantum correlations of any dimension, and the calibration on CHSH "
          "(the Tsirelson bound) is confirmed by a citation of NPA08.",
          "- D.4: see-saw was carried out in the reduced form (σ, F), equivalent to the TS form by D8 (the equivalence was checked "
          "numerically in both directions). Every excess was translated back into TS form (W, instruments) and "
          "recomputed in mpmath.",
          "- D.2: the functionals were carried over literally (the same weights); outside the U2 hull their value depends on "
          "the chosen representative of the class. A variant with the filter p(x,y) = 1/4 is shown separately.",
          "- D.1: instead of a numerical enumeration of classical circuits of dimension 5, 6, the main argument is "
          "the proof D7. The numerical control is a classical see-saw at d = 2…6.",
          f"- Time by section (s): {D.get('timing', {})}.", ""]
    return L


def stage_t3(tt, tc, ts, tq):
    n2, n3 = tt["N2"], tt["N3"]
    L = ["## T3.0 — three parties without selection", ""]
    viol = ts and ts.get("game_G_star") and Fraction(ts["game_G_star"]["W_star_value_exact"]) > Fraction(ts["game_G_star"]["causal_bound_exact"])
    L += [f"**Outcome: {'A PROCESS WITHOUT SELECTION WITH A VIOLATION WAS FOUND — the prohibition (lemma D6) holds only for two parties' if viol else 'no violations found'}.** "
          "The witness W* was found in exploration, outside the preregistered plan; the preregistered BW16 game does not catch it "
          "(details below).", "",
          "### T.0 Structure of the terms (the selection-free class for N parties, derivation D10)", "",
          "| N | TF (forward instruments only) | TB | ISO = TF ∩ TB | ISO formula | rule = null space |", "|---|---|---|---|---|---|",
          f"| 2 | {n2['TF']['dim']} | {n2['TB']['dim']} | {n2['ISO']['dim']} | {n2['rule_count_formula']} | {ok(n2['rule_equals_nullspace'])} |",
          f"| 3 | {n3['TF']['dim']} | {n3['TB']['dim']} | {n3['ISO']['dim']} | {n3['rule_count_formula']} | {ok(n3['rule_equals_nullspace'])} |",
          "",
          f"Calibration: at N = 2 exactly 19 (Stage C) — {ok(tt['calibration_N2_equals_stageC_19'])}; TF_2 = 88 = OCB (Stage C). "
          "The rule: a term is allowed when for one party it is “input only” and for another “output only”.",
          f"At N = 3: {n3['structure']['n_types']} kinds, terms by number of parties {n3['structure']['terms_by_number_of_parties']}; "
          "tripartite kinds of the form A_O B_O C_I (C's input from the outputs of A and B) are allowed, the supports overlap. "
          "The proof of D6 relied on T (A_O B_I) and S (A_I B_O) living on disjoint subsystems, "
          "so it does not carry over. (Anticommuting pairs exist at N = 2 as well — "
          f"{n2['structure']['anticommuting_pairs']} within one kind — and they did not obstruct D6; what matters is the overlap of the supports.)", ""]
    a, b, c = tc["T1a"], tc["T1b"], tc["T1c"]
    L += ["### T.1 Lugano", "",
          f"- (a) Lugano (P = 000): valid {ok(a['valid'])}; with the TS strategy “forward it on” the BW16 game = {a['forward_strategy_value']} "
          f"(calibration, BW16: 1); causally separable: {ok(a['causally_separable'])}; the classes TF / TB / ISO: "
          f"{ok(a['membership']['TF'])} / {ok(a['membership']['TB'])} / {ok(a['membership']['ISO'])}. Image multiplicities: "
          f"{a['image_multiplicities']} (non-invertible: 4 images with 2 preimages each).",
          "- Literature check: in the sources the global past is **fixed** (WBO23: “when the global past party prepares the "
          "state |0,0,0⟩”), that is, it is preselection; consistency for any P — BCRWZ19.",
          f"- (b) The canonical XOR extension (3 bits of P), P uniform, F discarded: W̄ = (1/8)·1 exactly — "
          f"{ok(b['W_is_trivial_uniform'])}; ∈ ISO_3: {ok(b['membership']['ISO'])}; the BW16 game = {b['game_exact']}; separable: "
          f"{ok(b['causally_separable'])}. At the same time **every** fixed p gives a valid, non-separable process with "
          f"game 1 ({sum(1 for v in tc['T1b_per_fixed_p'].values() if v['game_max_TS'] == 1.0 and not v['separable'])} of 8). "
          "XOR with a uniform p fully randomises the inputs: **the Lugano violation does not survive averaging over P.**",
          f"- (c) Extensions with one-bit P and F: candidates ω₁ {c['distinct_omega1_candidates']}, valid "
          f"{c['valid_extensions']}. At a uniform P the BW16 game is no greater than {c['max_avg_game']}. In the class ISO_3 among them there are "
          f"{sum(1 for e in c['list'] if e['avg_membership']['ISO'])}: this is ω₁ = ω̄_L (the mirror of Lugano), and its mixture W* "
          "is causally non-separable (see below).", ""]
    t2 = tc["T2_classical"]
    L += ["### T.2 Classical: the whole ISO_3 polytope", "",
          f"The exact maximum of the BW16 game over all classical three-party processes without selection (18 kinds, an LP for each "
          f"of the {t2['n_op_triples']} triples of TS bijections, exact recomputation with cdd.gmp): **{t2['max_game_exact']}** at bound 3/4, "
          f"that is, the preregistered game is not violated. The optimal point ∈ ISO_3: {ok(t2['optimal_T_membership']['ISO'])}; "
          f"causally separable: **{ok(t2['optimal_T_separable'])}**. This is exactly W*.", "",
          "Deviation: the vertex enumeration of the polytope (preregistered) did not finish in 9 h and was stopped. "
          "It was replaced by the exact maximum of the game via LP; separability was checked for the optimal point, not for all vertices.", ""]
    if ts:
        g = ts["game_G_star"]
        nc = ts["normalization_checks"]
        L += ["### The witness W* (exploration, not preregistered)", "",
              "**W* = ½(ω_L + ω̄_L)**, where ω_L is Lugano and ω̄_L(o) = ¬ω_L(¬o) is Lugano with all inputs and "
              "outputs inverted. Realisation: an invertible extension with a one-bit global past P and future F. P selects "
              "ω_L or ω̄_L and is prepared **uniformly** (no preselection), F is discarded (no postselection).", "",
              f"- Validity: the columns are normalised — {ok(ts['W_star']['columns_normalized'])}; consistency for all 64 "
              f"sets of local functions — {ok(ts['W_star']['consistent_all_local_functions'])}; ω̄_L is valid — "
              f"{ok(ts['W_star']['omega_bar_valid'])}.",
              f"- The selection-free class: TF / TB / ISO (exactly, Walsh) — {ok(ts['W_star']['membership']['TF'])} / "
              f"{ok(ts['W_star']['membership']['TB'])} / {ok(ts['W_star']['membership']['ISO'])}. Independently on the quantum code: the residual "
              f"of the Pauli decomposition outside ISO {nc['W_star_pauli_class_residual_ISO'][0]}. Normalisation for random TS operations, "
              f"forward-only and backward-only operations: {nc['W_star_ts']:.1e} / {nc['W_star_forward_only']:.1e} / "
              f"{nc['W_star_backward_only']:.1e}. Control: Lugano on “backward-only” operations breaks the normalisation by "
              f"{nc['lugano_backward_only_control_must_fail']:.2f}, so the check is not vacuous.",
              f"- Non-separability of the process: an exact certificate — a hyperplane with value "
              f"{ts['process_certificate']['exact_value_target']} on W* at a maximum of {ts['process_certificate']['exact_max_causal']} "
              f"over 680 causally ordered functions (dynamic order); LP cdd.gmp: separable — {ok(ts['process_separable_cdd'])}.",
              f"- **Correlations.** The causal polytope: {ts['n_causal_strategies']} deterministic strategies with a dynamic "
              f"order. Calibration: the Lugano correlation is outside it — {ok(ts['calibration']['lugano_forward_outside'])}, the correlations of "
              f"causal processes are inside (20 of 20) — {ok(ts['calibration']['causal_process_correlations_inside_20_of_20'])}. "
              f"W* with TS operations gives {ts['distinct_correlations']} distinct correlations. Of the {ts['n_checked']} checked, "
              f"{len(ts['correlations_outside_causal_polytope'])} are outside the polytope; the search was stopped at the fifth one.",
              f"- **The game G*** (a win if the outcome falls into the pair allowed for the given incomes): {g['winning_sets']}. "
              f"The exact causal bound over all strategies: **{g['causal_bound_exact']}**; W* with the “forward it on” strategy at all "
              f"three parties: **{g['W_star_value_exact']}**. All probabilities were computed in rational arithmetic — this is more precise than mpmath. "
              "The game was built from the support of the witness (post hoc), but the bound was computed exactly, so the violation is "
              "a mathematical fact.",
              "- A comparison with Lugano: Lugano also wins G* with probability 1, but it requires preselection (P = 000) and does not "
              "lie in ISO_3. W* achieves the same without selection: the “Lugano / mirror” mixture does not destroy non-causality, "
              "while the XOR mixture over all 8 values of P does.", ""]
    if tq:
        L += ["### T.2 Quantum: see-saw over ISO_3 on the BW16 game", "",
              f"- Calibration: W_AF with the “forward it on” strategy — {tq['cal_lugano_forward_value']}; W_AF in TF (residual "
              f"{tq['cal_lugano_in_TF'][0]}) and not in ISO (residual {tq['cal_lugano_in_ISO'][0]}).",
              f"- see-saw in TF_3 (OCB): values {tq.get('TF', {}).get('values')}; in ISO_3: {tq.get('ISO', {}).get('values')} "
              f"(failed starts: {tq.get('ISO', {}).get('failed')}).", ""]
    L += ["### T3 predictions", "", "| prediction | confidence | came true |", "|---|---|---|"]
    rows = [
        ("T.0: 19 / 1900 / 703, rule = null space", "0.9",
         n2["ISO"]["dim"] == 19 and n3["TF"]["dim"] == 1900 and n3["ISO"]["dim"] == 703 and n3["rule_equals_nullspace"]),
        ("T.0: the proof of D6 does not carry over (tripartite terms, overlapping supports)", "0.95", n3["structure"]["terms_by_number_of_parties"].get("3", 0) > 0),
        ("T.1(a): Lugano gives 1 and ∉ ISO_3", "0.9", a["forward_strategy_value"] == "1" and not a["membership"]["ISO"]),
        ("T.1(b): XOR at uniform P — W̄ = 1/8·1, game ≤ 3/4", "0.97", b["W_is_trivial_uniform"] and Fraction(b["game_exact"]) <= Fraction(3, 4)),
        ("T.1(c): one-bit extensions exist; at uniform P all ≤ 3/4 (BW16)", "0.6", c["valid_extensions"] > 0 and c["max_avg_game"] <= 0.75),
        ("T.2 cl.: all points of ISO_3 are causally separable", "0.55", t2["optimal_T_separable"]),
        ("T.2 cl.: the BW16 game ≤ 3/4 on all of ISO_3", "0.65", Fraction(t2["max_game_exact"]) <= Fraction(3, 4)),
        ("bottom line: “neither a proof nor a witness”", "0.5", not viol),
    ]
    if tq and tq.get("ISO", {}).get("best") is not None:
        rows.insert(-1, ("T.2 qu.: see-saw ISO_3 on BW16 ≤ 3/4", "0.65", tq["ISO"]["best"] <= 0.75 + 1e-6))
    L += [f"| {x} | {y} | {ok(z)} |" for x, y, z in rows]
    L += ["", "The architect's predictions: T.0 (the supports overlap, D6 does not carry over literally) — **YES**; T.1 (P is fixed "
          "in the sources) — **YES**; T.1(b) (at random P the Lugano violation disappears) — **YES** for the canonical "
          f"XOR extension; T.2 (at least one process without selection violates a three-party causal inequality) — "
          f"**{ok(viol)}** (W*, the game G*; not the BW16 game).", "",
          "### Deviations and caveats", "",
          "- The “selection-free” class for N parties is our derivation D10 (ISO_N = TF_N ∩ TB_N after the pattern of MH-27). The paper gives only "
          "the two-party case. The calibration is the match with 19 at N = 2.",
          "- The causal polytope of correlations consists of deterministic strategies with a dynamic order (the first party "
          "answers by its own input, the choice of the second depends on the input of the first, and so on). The number of vertices of the full binary "
          "three-party scenario was not found in the sources; the set was checked by calibrations (Lugano outside, causal "
          "processes inside).",
          "- The witness W* and the game G* are exploration, they are not in the preregistration. Novelty was not checked: a literature check is needed on "
          "whether “Lugano + mirror” mixtures and violations of causal inequalities by invertible processes without "
          "a fixed global past are known.", ""]
    return L


def stage_t31(d, x):
    w3 = d["a_W3"]
    L = ["## T3.1 — verification and structure of the witness W*", "",
         "**First line (as required by the prompt). Implicit priority:** W₃ of Baumeler–Feix–Wolf (arXiv:1403.7333, 2014) = E_ex1 "
         "in Baumeler–Wolf (1507.01714). This is a uniform mixture of two loops, “forward it around the circle” and “forward it with inversion”; each "
         "of them is by itself logically inconsistent, the mixture is consistent. **By our check W₃ ∈ ISO₃** "
         f"(TF / TB / ISO — {ok(w3['membership']['TF'])} / {ok(w3['membership']['TB'])} / {ok(w3['membership']['ISO'])}), "
         f"it is causally non-separable (exact LP — {ok(not w3['separable_exact_cdd'])}), and its correlations with the “forward it on” strategy "
         f"lie outside the causal polytope (the game built on the support: W₃ = 1, causal bound "
         f"{w3['outside_example'][0]['support_game_causal_bound'] if w3['outside_example'] else '—'}). The authors formulate this "
         "as a game (win 1 at bound 5/6); about the global past, the future and time reversal there is nothing in their work. "
         "**A classical three-party process without selection violating a causal inequality is therefore implicitly "
         "known since 2014.** Our contribution narrows down to four points:",
         "- the translation into the Mrini–Hardy formalism (the class ISO_N as a definition);",
         "- the contrast “two parties — a prohibition (D6), three — none”;",
         "- the construction of W* from two **valid** process functions (Lugano and its mirror), unlike W₃, where the components are invalid;",
         "- the characterisation of the “mirrors” and the enumeration (below).",
         "",
         "### The architect's external cross-check (a separate script from scratch, without the repository's code)", "",
         "- 138 304 distinct deterministic strategies with a dynamic order — agrees with T3.0; the same number of vertices of the full "
         "binary three-party polytope is given by Abbott et al. (1608.01528, p. 478);",
         "- the causal bound G* = 3/4 — agrees;",
         "- Lugano and its mirror win G* with probability 1 **each on its own**. Therefore the value 1 of W* on G* is "
         "trivial, and what is substantive is that the **symmetrised mixture lies in ISO₃**, although each component requires "
         "preselection.", "",
         "### T3.1.a Literature check (SOURCES.md, section T3.1; `sources/litcheck_T31/REPORT.md`)", "",
         "21 works were checked. An explicit result “a non-causal classical process with a uniform global past and "
         "a discarded future, valid in both directions, violates a causal inequality” was not found, but there is an implicit "
         "priority, W₃ (see above). The rest:",
         "- “without a global past” in Steffinlongo–Dourdent (2502.15579) and Kunjwal–Baumeler is a property of the **function** "
         "(nobody's input is a constant), while the system P in their constructions is fixed in |0⟩;",
         "- Guérin–Brukner (1805.12429) is a reversed Lugano with a uniform **superposition** in P, a violation of I₁ ≈ −1/4 only "
         "with quantum instruments;",
         "- Mrini–Hardy give the ISO class for two parties, without an example of a violation.", "",
         f"**Fine tuning of W*:** qω_L + (1−q)ω̄_L ∈ ISO₃ only at q = 1/2 — "
         + ", ".join(f"q={r['q']}: {ok(r['membership']['ISO'])}" for r in d["a_W_star_fine_tuning"]) + ". "
         "W* is an isolated point of its family, just like W₃ (“proper mixture”, BW16).", ""]
    b = d["b_games"]
    L += ["### T3.1.b Games", "",
          f"Calibration: the causal bounds of all five published games, recomputed over the {d['n_causal_strategies']} strategies, agree "
          f"with the citations — {ok(all(v['calibration_bound_matches'] for v in b.values()))}.", "",
          "| game | bound | mirror-invariant | Lugano “forward it on” / max | mirror “forward it on” / max | W* “forward it on” / max |",
          "|---|---|---|---|---|---|"]
    for k, v in b.items():
        cell = lambda nm: f"{v[nm]['forward_strategy']} / {v[nm]['max_over_TS_ops']:.4g}{' **>**' if v[nm]['violates'] else ''}"  # noqa: E731
        L.append(f"| {k} | {v['computed_causal_bound']} | {ok(v['mirror_invariant'])} | {cell('Lugano')} | {cell('mirror')} | {cell('W_star')} |")
    L += ["",
          "- BW16: Lugano 1, the mirror 0, W* 1/2 with the “forward it on” strategy — the architect's prediction is correct.",
          "- **W* violates the published I₃ (1 > 7/8) and I₁ (15/16 > 7/8)** (Abbott et al.), so the violation does not rest "
          "on the a posteriori G* alone.",
          "- The principle “a mixture preserves the violation only of mirror-invariant inequalities” **was not confirmed**: not one of the five "
          "published games is invariant, yet I₃ and I₁ are violated. The correct formulation: the violation is preserved if "
          "**both** components violate the inequality under **the same** operations (for I₃ both give 1).", ""]
    c = d["c_group"]
    L += ["### T3.1.c Which “mirrors” work", "",
          f"The group G of order {c['order']} (Z₂⁶ ⋊ (S₃ × Z₂)). The stabiliser of Lugano is {len(c['stabilizer_of_Lugano'])} elements "
          "(cyclic permutations and transpositions of the parties with inversion of all outputs).",
          f"- Pairwise symmetrisation ½(L + gL): g·L is a process for {c['n_gL_process']} elements, the mixture is in TF for "
          f"{c['n_mix_in_TF']}, in ISO₃ for {c['n_mix_in_ISO']}, working (in ISO₃ and non-separable) — **{c['n_working']}**. "
          f"Distinct mixtures among them — **{c['distinct_working_mixtures']}**, and that is W*. All working g are “full "
          "inversion × the stabiliser of Lugano”. For pairwise symmetrisation **the only working mirror is full inversion**. "
          f"The input↔output exchange on its own does not lead into ISO₃ — {ok(not c['transpose_alone_in_ISO'])}.", ""]
    if x:
        om = x["orbit_mixtures_ISO"]
        ns = [r for r in om if r.get("separable_exact") is False]
        L += [f"- **Orbit mixtures** (exploration: averages over the cyclic subgroups ⟨g⟩ and over the large subgroups). In ISO₃ there are "
              f"{len(om)} distinct mixtures, non-separable ones — **{len(ns)}**, of which W* is {sum(1 for r in ns if r['equals_W_star'])}. "
              "Non-separable ones other than W*:", "",
              "| generating g | orbit size | components are processes | correlations outside the causal set | I₁ (bound 7/8) | I₃ (bound 7/8) |",
              "|---|---|---|---|---|---|"]
        for r in ns:
            if r["equals_W_star"]:
                continue
            q = r["quoted_games"]
            L.append(f"| {r['generator']} | {r['orbit_size']} | {'all' if all(r['components_are_processes']) else 'every other one (with transposition)'} | "
                     f"{ok(r['first_outside'] is not None)} | {q['I1']['max_TS']:.4g}{' **>**' if q['I1']['violates'] else ''} | "
                     f"{q['I3']['max_TS']:.4g}{' **>**' if q['I3']['violates'] else ''} |")
        L += ["",
              "Summary on the “mirrors”:",
              "- pairwise only full inversion works;",
              "- mixtures over orbits of size 6 without time reversal — six relabelled Luganos — also lie in ISO₃, "
              "are non-separable and violate I₁;",
              "- the same is done by orbits of size 4 with time reversal (transposition), where every second component is not "
              "a process, as in W₃.",
              "",
              "The architect's prediction “not only full inversion works” **is correct for orbits and incorrect for pairs**. What all "
              "working mixtures have in common: the row sums equal 1 (double stochasticity — a necessary condition for TB), and no "
              "component requires postselection on its own.", ""]
    dd = d["d_enumeration"]
    L += ["### T3.1.d All deterministic three-party process functions", "",
          f"- Candidates {dd['candidates']} (a party's input does not depend on its own output — TC20 pp. 155–157; on a random "
          f"sample of 300 functions with such a dependence the valid ones number {dd['own_dependence_valid_in_random_sample_of_300']}).",
          f"- Valid **{dd['valid']}** — exactly as in BW16 (“Only 744 extremal points … are deterministic”, p. 760). "
          f"Causal {dd['causal_among_valid']}, non-causal **{dd['noncausal']}**.",
          f"- Classes of the non-causal ones under Z₂⁶ ⋊ S₃: {len(dd['classes_under_Z2^6xS3'])}; contains Lugano — "
          f"{ok(all(c_['contains_lugano'] for c_ in dd['classes_under_Z2^6xS3']))} (size {dd['classes_under_Z2^6xS3'][0]['size']}). "
          "**All non-causal deterministic processes are relabellings of Lugano.**",
          f"- Symmetrisable ones (∃g: ½(ω + gω) ∈ ISO₃ and non-separable) — **{dd['n_symmetrizable']} of {dd['noncausal']}**, each with "
          f"{dd['symmetrizable'][0]['n_working_g']} working g (a relabelled full inversion).", ""]
    if x:
        n4, n2 = x["N4"], x["N2_calibration"]
        L += ["### T3.1.e The number of parties", "",
              f"- **N = 2 (calibration):** valid deterministic functions {n2['valid_bipartite_deterministic']}, all causal — "
              f"{ok(n2['all_valid_causal'])}; symmetrisations in ISO₂ {n2['symmetrizations_in_ISO2']}, non-separable "
              f"**{n2['nonseparable_among_them']}**, as D6 requires. The class ISO₂ = 19 = the Mrini–Hardy class (T3.0).",
              f"- **N = 4:** the AGB17/TC20 process (citation in SOURCES.md) and its mirror are valid ({ok(n4['agb_valid'])} / {ok(n4['mirror_valid'])}), "
              f"but **W₄* = ½(AGB + mirror) ∉ ISO₄** (TB — {ok(n4['W4_star_membership']['TB'])}). An independent check: the row "
              f"sums of W₄* = {n4['row_sums_W4_star']}, not all ones, as they are for W* at N = 3. The reason is the image multiplicities. For "
              "Lugano they are {2,2,2,0,2,0,0,0} and are completed by the mirror to uniform ones; for AGB₄ eight outputs go to 0000, and the mirror "
              "does not even them out. **Symmetrisation by full inversion does not work at N = 4.**",
              "- A necessary criterion (a derivation): ½(ω + gω) ∈ ISO is possible only when the combined multiset of images of "
              "ω and gω is uniform (double stochasticity).",
              f"- The calibration of the AGB17 game **is not passed literally**. The prose description of the target (“a_k = 1 if x_(k⊖1) = 1 and "
              f"x_(k⊕1) = 0”) agrees with their own function f only on {n4['agb_prose_target_agrees_with_f_on']} allowed "
              f"inputs, and AGB itself wins such a game only with probability {n4['agb_game'][0]}. With the target f(x), AGB with the "
              f"“forward it on” strategy gives {n4['game_target_f_forward']['agb']}, the mirror {n4['game_target_f_forward']['mirror']}, W₄* "
              f"{n4['game_target_f_forward']['W4_star']}. The conclusion about ISO₄ does not depend on the game.", ""]
    L += ["### T3.1 predictions", "", "| prediction | confidence | came true |", "|---|---|---|"]
    rows = [("a: a close notion exists, an explicit result does not", "0.5", True),
            ("a: the same result was found (someone else's priority)", "0.3", "partially: implicitly (W₃)"),
            ("b: BW16 1 / 0 / ½; G* is mirror-invariant", "0.8",
             b["BW16"]["Lugano"]["forward_strategy"] == "1" and b["BW16"]["mirror"]["forward_strategy"] == "0" and b["G*"]["mirror_invariant"]),
            ("c: the working g = full inversion × the stabiliser", "0.5", c["distinct_working_mixtures"] == 1),
            ("c: there is a working g outside that (pairwise)", "0.4", False),
            ("c: the input↔output exchange on its own does not work", "0.8", not c["transpose_alone_in_ISO"]),
            ("d: valid ones 700–2000; the non-causal ones are only images of Lugano", "0.6", 700 <= dd["valid"] <= 2000 and len(dd["classes_under_Z2^6xS3"]) == 1),
            ("d: every non-causal one is symmetrisable", "0.65", dd["n_symmetrizable"] == dd["noncausal"]),
            ("e: N = 4 works", "0.6", bool(x) and x["N4"]["W4_star_membership"]["ISO"] is True)]
    L += [f"| {a_} | {b_} | {c_ if isinstance(c_, str) else ok(c_)} |" for a_, b_, c_ in rows]
    L += ["", "The architect's predictions:",
          "- a (a close notion exists, symmetrisation by a mirror is not written out) — **YES**, but with an implicit priority, W₃;",
          f"- b (BW16: 1 on Lugano, 0 on the mirror) — **{ok(b['BW16']['mirror']['forward_strategy'] == '0')}**;",
          "- c (not only full inversion works) — **NO for pairs, YES for orbits**;",
          "- e (N = 4 works) — **NO**.", "",
          "### Deviations", "",
          "- The analysis of the orbits at the level of correlations, the games I₁–I₄ on the orbit mixtures, the check of W₃ and of the fine tuning are "
          "exploration, they are not in the preregistration. W₃ was added after the literature check.",
          "- Separability in c and d was checked with HiGHS (screening); exactly (cdd.gmp) and with a certificate — for W*, W₃ and the orbit mixtures.",
          "- N = 4: causality via an enumeration of strategies was not done, because there are about 10¹¹ of them. Nor was it needed: "
          "W₄* already fails the ISO₄ condition.", ""]
    return L


def stage_rts(st, ss, cal, r4, hw, dual, fin):
    hwc = st["calibration_and_HW"]
    L = ["## RTS stage 0 — time symmetry against the real-QM loophole", "",
         "**First line (as required by the prompt).** Real QM in process matrices has already been considered: "
         "Surace–Minagawa–Kunjwal, arXiv:2605.30238 (“Indefinite Causal Order Reverses the Real-Complex Hierarchy”), "
         "where an RQT process is defined by carrying the operational characterisation of OCB over to real laboratories. "
         "But in v2 the authors themselves write: “Under N2, the process matrix used in this version to separate RQT from QT is "
         "not valid, and the claimed RQT/QT separation is therefore not established” (citation in SOURCES.md). "
         "Time symmetry, the global past and Mrini–Hardy are not there at all (0 occurrences). The literature check covers 11 works; "
         "dumps of the papers themselves are not included in the repository (see README, the section on third-party materials); "
         "verifiable citations with line numbers are in SOURCES.md.", "",
         "### R.1 Translating the binocular scenario into TS without selection (D12)", "",
         f"- The complex ISO process (identity channels, maximally mixed marginals) reproduces Renou's value "
         f"**exactly**: 𝒯 = {hwc['complex_T']:.12f} against 6√2 = {hwc['complex_T_expected_6sqrt2']:.12f}. "
         f"The deviation of the ISO marginals is {max(hwc['complex_marginals_dev']):.1e}.",
         f"- The TS conditions on the operations hold: Σ_x Tr A = {hwc['complex_alice_ts_constraint'][0]:.0f} (= 3/2·d_A), "
         f"Σ_z Tr C = {hwc['complex_charlie_ts_constraint'][0]:.0f} (= 3·d_C), Tr F_b = "
         f"{hwc['complex_bob_traces'][0]:.0f} (= d_B/4).", "",
         "**Real product processes (see-saw).**", "",
         "| configuration | dimensions | starts | failed | best 𝒯 | distinct values |", "|---|---|---|---|---|---|"]
    for k in ("R1_product_2x2x2x2", "R1_product_4x2x2x4", "R3_delta_4x2x2x4", "R3_delta_2x4x4x2"):
        v = ss[k]
        vals = sorted({round(x, 5) for x in v["values_sorted"]}, reverse=True)
        L.append(f"| {'product' if 'product' in k else 'with Δ'} | {k.split('_')[-1]} | "
                 f"{len(v['values_sorted']) + v['failed']} | {v['failed']} | **{v['best']:.6f}** | {vals} |")
    L += ["",
          f"The ceiling of all these runs is 4+2√2 ≈ {4 + 2 * 2 ** 0.5:.6f}, that is, **below** Renou's real bound "
          f"7.6605 (prediction R.1 confirmed) and below the complex 6√2. Adding Δ (the non-separable part of "
          "ω = ω₁⊗ω₂ + Δ, Δ ∈ Anti⊗Anti) gives nothing at these dimensions.", "",
          "**Anti-vacuum calibration of the estimator.** The same see-saw with Hermitian variables at (2,2,2,2), out of "
          f"{len(cal['values_sorted']) + cal['failed']} random starts, finds the complex value "
          f"**{cal['n_reaching_6sqrt2']:.0f} times** (best {cal['best']:.6f} = 6√2), failed starts "
          f"{cal['failed']}. Hence the ceiling of 4+2√2 at small dimensions is a property of the real ISO, "
          "not a weakness of the algorithm.", "",
          "### R.2 Which terms ISO allows", "",
          "A term is allowed ⇔ Tr[T·(M_A⊗M_B⊗M_C)] = 0 for random products of forward (TF) and backward (TB) operations.", "",
          "| term | TF | TB | ISO |", "|---|---|---|---|"]
    for k, v in st["J_terms"].items():
        L.append(f"| {k} | {ok(v['TF'])} | {ok(v['TB'])} | **{ok(v['ISO'])}** |")
    L += ["",
          "The controls worked: the identity channel is allowed, the preselection Z^{A_I} is forbidden in TB, Z^{A_O}Z^{C_O} "
          "is forbidden in TF. Prediction R.2 (4-partite J terms are allowed) — **confirmed**.", "",
          "### R.2.2 The Hoffreumon–Woods model in the process language", "",
          f"The translation: the state ½Γ̄⁽⁴⁾{{ρ⊗σ}} on (phase rebits)⊗(qubits), the effects Γ{{·}}. The value "
          f"𝒯 = {hwc['HW_T']:.12f} = 6√2 is reproduced, the state is real and symmetric "
          f"({ok(hwc['HW_is_real_symmetric'])}), positive (λmin = {hwc['HW_state_min_eig']:.1e}), "
          f"operationally independent (OI violation {hwc['HW_OI_violation']:.1e}). "
          f"**But it does not lie in ISO:** the deviation of both marginals = {max(hwc['HW_marginals_dev']):.4f} = 1/16.", "",
          f"Bob's POVM in HW is incomplete (Σ_b Γ̄⁽²⁾{{F_b}} = Ī⁽²⁾⊗I — a rank-8-of-16 projector, eigenvalues "
          f"{r4['bob_completion']['rest_eigs']}), the TS condition Tr F_b = 4 is violated. Completing the remainder evenly "
          f"gives Tr F_b = {r4['bob_completion']['bob_traces_completed'][0]:.0f} and does not change 𝒯 "
          f"({r4['bob_completion']['T_HW_with_completed_F']:.6f}).", "",
          "**Decomposition of ω_HW over the rebit patterns {I,J}⁴ on (A′,B1′,B2′,C′)** "
          f"(the sum is recovered to {hw['decomposition_check']:.1e}):", "",
          "| pattern | norm | contribution to 𝒯 | (A,C) marginal | (B1,B2) marginal |", "|---|---|---|---|---|"]
    for k, v in hw["components"].items():
        L.append(f"| {k} | {v['norm']:.4f} | {v['T_contribution']:+.4f} | {v['AC_marginal_dev']:.4f} | {v['B_marginal_dev']:.4f} |")
    rem = hw["removal"]
    L += ["",
          "6√2 is accumulated from four patterns: I and J_B1′J_B2′ give 2√2 each, J_A′J_C′ and J_A′J_B1′J_B2′J_C′ give √2 each. "
          "Exactly two of them are taken out of ISO: **J_A′J_C′** (forbidden in TF: a correlation of the outputs of A and C) and **J_B1′J_B2′** "
          "(forbidden in TB: a correlation of Bob's inputs). In the network language this is a phase reference shared by parties "
          "not connected by a common source; in the process language it is a resource from the boundary (pre- or postselection).", "",
          "**Can they be replaced by allowed ones?**", "",
          "| operation on ω_HW | λmin | 𝒯 | noise until ω ≥ 0 | 𝒯 after the noise |", "|---|---|---|---|---|"]
    for k, v in rem.items():
        L.append(f"| {k} | {v['min_eig']:.6f} | {v['T']:.6f} | {v['noise_needed']:.4f} | {v['T_after_noise']:.6f} |")
    L += ["",
          "The marginal pieces carry no contribution to 𝒯: after their removal 𝒯 = 6√2 is preserved, only "
          f"positivity breaks (λmin = −1/128 when both are removed; the spectrum of the marginal deviations is "
          f"{hw['dev_AC_rank_eigs']} and {hw['dev_B_rank_eigs']}, that is, ±1/16). Restoring positivity "
          "with noise eats up exactly what the forbidden terms give: 2√2 remains.", "",
          f"**A rigorous upper bound under the HW operations.** The dual SDP (Y on (A,C), Z on (B1,B2), "
          f"Y⊗I + I⊗Z − G ≥ 0; the lift check is {dual['lift_check']:.1e}) after a shift by "
          f"{dual['shift']:.1e} gives a feasible dual point (Cholesky, λmin of the certificate "
          f"{dual['min_eig_certificate']:.1e}):", "",
          f"> max 𝒯 over **all** real ISO processes under the HW operations ≤ **{dual['certified_upper_bound']:.8f}** "
          f"= 3√2 + {dual['certified_upper_bound'] - 3 * 2 ** 0.5:.0e}, where 3√2 = {dual['three_sqrt2']:.8f}.", "",
          "This is **without** the OI requirement. The primal SDP gives the same value from below "
          f"({hw['SDP_ISO_noOI_at_HW_ops']['sdp_value']:.6f}, SCS status — {hw['SDP_ISO_noOI_at_HW_ops']['status']}, "
          "so the certified dual one is taken as the bound). With the OI requirement, alternating "
          f"ω₁ / ω₂ / Δ under the same operations stands at {hw['OI_alternation_at_HW_ops']['history'][-1]:.6f} = 3√2 "
          f"for all {len(hw['OI_alternation_at_HW_ops']['history'])} iterations; the SDP over Δ with the HW marginals is "
          f"{st['SDP_fixed_HW_ops']['T_max']:.6f}, that is, Δ adds nothing.", "",
          "**The answer to R.2.2:** the HW construction does not carry over into the real ISO, and under its operations exactly "
          "half is lost: 6√2 → 3√2 (proved by a dual certificate, not merely numerically).", "",
          "### R.3 The maximum over real ISO processes with operational independence", "",
          f"See-saw at (4,4,4,4) — the minimal dimension at which every party has a phase rebit. "
          f"Starts — {len(r4['runs'])}, failed {r4['failed']}; the best one is from the HW point.", "",
          "| start | 𝒯 | seconds |", "|---|---|---|"]
    for r in r4["runs"]:
        val = "solver failure" if r.get("failed") else f"{r['value']:.6f}"
        L.append(f"| {r['start']} | {val} | {r['seconds']:.0f} |")
    cw, co = fin["cleanup_white_noise"], fin["cleanup_OI_preserving"]
    L += ["",
          f"The start from the HW point did not converge within the allotted iterations, so it was continued separately "
          f"(`rts_4444_ext.py`, {fin['iterations']} iterations, 6.6 h). The course: 5.657 → 6.83 (iteration 3) → "
          f"{fin['T_raw_max']:.6f} (iteration {fin['T_raw_max_iter']}), after which it oscillates without growth "
          f"(the last one {fin['T_raw_last']:.6f}). The non-monotonicity is SCS noise, not see-saw.", "",
          "**Solver drift control** (`rts_ext_monitor.py`, at every saved point): the residuals of the raw point "
          "and 𝒯 after projection onto the feasible set. The cleaned value tracked the raw one (at iteration 28: raw "
          "6.896955, cleaned 6.895107), that is, the growth was real and not drift.", "",
          "**The final point, two cleanups:**", "",
          "| cleanup | 𝒯 | λmin | ISO marginals | OI violation | noise |", "|---|---|---|---|---|---|",
          f"| white noise I/256 | {cw['T_clean']:.6f} | {cw['min_eig_clean']:.1e} | {max(cw['iso_marginals_dev']):.1e} | "
          f"{cw['oi_violation']:.1e} | {cw['noise']:.1e} |",
          f"| factor-wise noise (OI exact) | **{co['T']:.6f}** | {co['min_eig']:.1e} | {max(co['iso_marginals_dev']):.1e} | "
          f"{co['oi_violation']:.1e} | {co['q_noise']:.1e} |",
          "",
          "White noise breaks OI at its own level: I/256 is not a product. Factor-wise noise "
          "((1−q)ω_i + q I/16 in each factor, Δ rescaled) preserves both ISO and OI exactly, and positivity "
          "is confirmed by a Cholesky factorisation. Therefore the final number is the second row.", "",
          "**Summary of R.3.**", "",
          "| quantity | value |", "|---|---|",
          f"| the best strictly feasible real ISO + OI process (our lower bound) | **{co['T']:.6f}** |",
          f"| the ceiling of the low-dimensional runs 4+2√2 | {fin['thresholds']['4+2sqrt2']:.6f} |",
          f"| Renou's real bound (RTW21, p. 376) | {fin['thresholds']['real_bound_RTW21']} |",
          f"| the complex value 6√2 | {fin['thresholds']['6sqrt2']:.6f} |", "",
          "The maximum found is **above** the ceiling of the small dimensions (that is, Δ and the phase rebits do work), but "
          "**below** both meaningful bounds. We have no upper bound over all real ISO processes with OI under "
          "**free** operations: the certificate was obtained only for the fixed HW operations. "
          "Therefore, by the preregistration's rule, a discrepancy with the complex value **is not claimed**.", "",
          "### Stage outcome", "",
          "**None of the prompt's three outcomes occurred in pure form.** What was established:",
          "1. The HW construction **does not carry over** into the real ISO as it is: it is taken out of the class by the terms "
          "J_A′J_C′ and J_B1′J_B2′, and under its operations the maximum over all real ISO processes is ≤ 3√2 "
          "(certified). This is the answer to R.2.2 and, most likely, the main result of the stage.",
          "2. Under free operations the real ISO + OI gives at least 6.869154 (a strictly feasible point) — "
          "more than 4+2√2, but less than 7.6605 and 6√2.",
          "3. The OI loophole **is neither closed nor opened in the selection-free TS regime**: closing it requires an upper "
          "bound under free operations, opening it requires a point above 7.6605. There is neither.", "",
          "### RTS predictions", "", "| item | prediction | confidence | came true |", "|---|---|---|---|",
          "| R.0 | real QM was not considered in TS formalisms | 0.7 | YES (in process matrices it was considered, SMK26, but the claimed separation was withdrawn by the authors) |",
          "| R.1 | the complex ISO reproduces Renou's 𝒯 exactly | 0.85 | **YES** |",
          "| R.1 | real products ≤ Renou's real bound | 0.9 | **YES** (6.8284 ≤ 7.6605) |",
          "| R.2 | 4-partite J terms are allowed in ISO | 0.95 | **YES** |",
          "| R.2 | the HW RQT model carries over into the real ISO | 0.65 | **NO** |",
          "| R.2 | J⊗J terms satisfy OI | 0.7 | **YES** |",
          "| R.3 | the real ISO + OI attains the complex 𝒯 | 0.65 | **not confirmed** (6.869 of 8.485) |",
          "| bottom line | “HW carries over, closed negatively” | 0.6 | **NO** |", "",
          "The architect's predictions: R.0 — YES with a caveat; R.2 (4-partite terms are allowed) — **YES**; "
          "R.3 (HW carries over, ~55%) — **not confirmed**.", "",
          "### Deviations", "",
          "- **The scenario was narrowed.** Only processes of the network form D12 were considered (ω on A⊗B1⊗B2⊗C, "
          "ISO ⇔ both marginals maximally mixed), not all of ISO₃ with a composite input for Bob. A full "
          "enumeration of ISO₃ in these dimensions was not done.",
          "- **There is no upper bound under free operations** — see above. A certificate exists only for the HW operations.",
          f"- **The share of failed see-saw starts is high:** {ss['R1_product_2x2x2x2']['failed']} of "
          f"{ss['R1_product_2x2x2x2']['failed'] + len(ss['R1_product_2x2x2x2']['values_sorted'])} at (2,2,2,2). "
          "A failed start is a solver failure (status not optimal); such starts are discarded entirely.",
          "- **The 256×256 SDP is solved by SCS, not Clarabel:** an interior-point solver builds a dense KKT block of "
          "svec(256)² ≈ 8.7 GB. MOSEK is unavailable. Hence the optimal_inaccurate statuses "
          f"({r4['solver_stats'].get('scs_inaccurate', 0)} of {r4['solver_stats']['solves']} solves in the "
          "(4,4,4,4) run) and the need for an independent cleanup of every point.",
          "- **An environment failure.** The first version stored the Δ basis as a dense matrix (14400×65536, ~7.5 GB); together with "
          "a parallel run this exhausted the memory and brought down the user's system. Fixed: a sparse "
          "basis, RLIMIT_AS per process, computations strictly one at a time. Both subsequent requests for 8.7 GB "
          "(Clarabel) hit the limit and ended with MemoryError without affecting the system.",
          "- The intermediate points of iterations 0–11 of the continuation were not saved (the npz is overwritten), the monitor was "
          "started from iteration 11.", ""]
    return L


def stage_rts1(gs, cs, du, gpucal):
    """S.1 the dimension scan, S.2 the certificates, S.3 the summary of the RTS branch."""
    th = gs.get("thresholds", {})
    L = ["## RTS stage 1 — the final dimension scan (the closing stage of the branch)", "",
         "### The estimator and its calibration", "",
         "The state step is solved by **ADMM on the GPU** (`scripts/rts_gpu.py`): the projection onto the PSD cone is an `eigh` on "
         "the graphics card, the projection onto the affine set (ω₁⊗ω₂ + Δ, Δ ∈ Anti⊗Anti, zero marginals of Δ) is "
         "tensor operations on the same card. Both projections are exact and in closed form; this is possible because the images of "
         "the adjoint marginal maps are orthogonal inside Anti⊗Anti (antisymmetric matrices are "
         "traceless). The operation steps stayed on the CPU in cvxpy. The reason for the switch: at (6,6,6,6) a single w step "
         "in SCS took 349 s while the `eigh` itself took 0.09 s there — the time went into cvxpy canonicalisation and "
         "thousands of SCS iterations.", "",
         "**Important for the honesty of the number:** an under-converged ADMM cannot inflate the result. The final 𝒯 is computed "
         "anew at a strictly feasible point after the cleanup, so poor convergence only lowers the value found.", "",
         "| estimator check | result |", "|---|---|"]
    for k, v in gpucal.items():
        L.append(f"| {k} | {v} |")
    L += ["", "### S.1 The dimension scan", "",
          "The reported number is the cleaned 𝒯 (factor-wise noise: ISO and OI exact, positivity by Cholesky).", "",
          "| d | PSD block N | best 𝒯 cleaned | best raw | best start | cold | successful | failed | λmin | ISO | OI | noise q | time |",
          "|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for d in (2, 4, 6, 8):
        r = gs.get(f"d{d}")
        if not r:
            continue
        c = r.get("cleanup_best") or {}
        L.append(f"| {d} | {(d * d) ** 2} | **{r['T_clean_best']:.6f}** | {r['T_raw_best']:.6f} | {r['best_kind']} | "
                 f"{r['n_cold']} | {r['n_success']} | {r['n_failed']} | {c.get('min_eig', float('nan')):.1e} | "
                 f"{max(c.get('iso_marginals_dev', [0, 0])):.1e} | {c.get('oi_violation', float('nan')):.1e} | "
                 f"{c.get('q_noise', float('nan')):.1e} | {r['wall_seconds'] / 60:.0f} min |")
    c8 = (gs.get("d8") or {}).get("ceiling")
    if c8:
        L += ["", "**The resource ceiling at (8,8,8,8) — in numbers, without extrapolation.** The row d = 8 in the table "
              "**is not a result of the scan**: there are no cold starts there at all, the value was obtained from a single "
              "warm start with an under-converged ADMM.", "", "| characteristic | value |", "|---|---|"]
        L += [f"| {k} | {v} |" for k, v in c8.items()]
    L += ["", "| threshold | value |", "|---|---|",
          f"| the ceiling of the low-dimensional runs 4+2√2 | {th.get('4+2sqrt2', 0):.6f} |",
          f"| Renou's real bound (RTW21, p. 376) | {th.get('real_bound_RTW21')} |",
          f"| the complex value 6√2 | {th.get('6sqrt2', 0):.6f} |", ""]
    # independent CPU/SCS cross-check
    cp4 = cs.get("d4_partial_cpu_scs")
    if cp4:
        L += ["**An independent cross-check with another solver.** The same see-saw via SCS on the CPU (`rts_scan.py`): at "
              f"(2,2,2,2) — {cs['d2']['T_clean_best']:.6f} with {cs['d2']['n_success']} successes out of "
              f"{cs['d2']['n_attempts']} attempts (the GPU path: {gs['d2']['T_clean_best']:.6f}, "
              f"{gs['d2']['n_success']} of {gs['d2']['n_success'] + gs['d2']['n_failed']}); at (4,4,4,4) — "
              f"{cp4['T_clean_best']:.6f} over {cp4['n_success']} starts ({cp4['seconds_total'] / 3600:.1f} h), "
              "the run was interrupted on a request to free up resources. The values agree at d = 2 and diverge at "
              "d = 4: the SCS path **never once** found a point at the level of the GPU path. This is a property of the estimator, not of the class "
              "of processes, and it is recorded as a limitation.", ""]
    # S.2
    L += ["### S.2 Upper bounds", "",
          "**An upper bound under free operations could not be obtained.** The problem over the operations is non-convex "
          "(𝒯 is bilinear in the state and the operations), and reducing by the symmetry of the scenario does not give a convex relaxation: "
          "the functional 𝒯 is not invariant under the exchange of parties (Alice has 3 outcomes, Charlie has 6), while local "
          "relabellings are already accounted for by the freedom of the operations. Therefore, instead of it, a weaker but **rigorous** "
          "statement was made: under the **found** operations the maximum over all real ISO states (OI is not even "
          "required here — the set is wider) is bounded by a certificate.", "",
          "| d | 𝒯 cleaned at the point | certificate (ADMM, GPU) | gap | λmin of the certificate | cross-check with cvxpy/SCS |",
          "|---|---|---|---|---|---|"]
    for d in (2, 4, 6, 8):
        r = (du.get("gpu") or {}).get(f"d{d}")
        if not r:
            continue
        alt = ((du.get("cvxpy") or {}).get(f"d{d}") or {}).get("SCS", {})
        altv = (f"{alt['certified_upper_bound']:.6f} (diff. "
                f"{abs(alt['certified_upper_bound'] - r['certified_upper_bound']):.1e})") if "certified_upper_bound" in alt \
            else "does not assemble, out of memory"
        L.append(f"| {d} | {r['T_at_point']:.6f} | **{r['certified_upper_bound']:.6f}** | {r['gap']:.1e} | "
                 f"{r['min_eig_certificate']:.1e} | {altv} |")
    L += ["",
          "The feasibility of the dual point in every row was checked by a Cholesky factorisation after a shift, "
          "so this is a certificate proper, not a solver's value.", "",
          "**What this gives.** At d ≤ 6 the gap between the value found and the certificate is small ("
          + ", ".join(f"d = {d}: {(du['gpu'][f'd{d}'])['gap']:.1e}" for d in (2, 4, 6) if f"d{d}" in du.get("gpu", {}))
          + "): see-saw squeezes the state almost completely under the found operations, and the entire remaining "
          "gap up to 7.6605 is due to the **operations**, not to the search over states. At d = 8 the gap is two orders of magnitude "
          "larger ("
          + f"{(du['gpu'].get('d8') or {}).get('gap', float('nan')):.1e}"
          + ") — this is a direct consequence of ADMM under-convergence within the budget, not a property of the problem.", ""]
    cl = ((du.get("cvxpy") or {}).get("d4") or {}).get("CLARABEL", {})
    if "failed" in cl:
        L += ["**The interior-point solver.** The Clarabel-versus-SCS cross-check was done at d = 2 (agreement to 3e−9). "
              f"At d = 4 Clarabel is inapplicable: {cl['failed']}", ""]
    # the interpretation, fixed in the preregistration before the runs
    v = {d: (gs.get(f"d{d}") or {}).get("T_clean_best") for d in (2, 4, 6, 8)}
    L += ["### Interpretation (the criteria were fixed in PREREGISTRATION_RTS1.md before the runs)", "",
          f"The course of the values: d = 2 → {v[2]:.6f}, d = 4 → {v[4]:.6f}, d = 6 → {v[6]:.6f}"
          + (f", d = 8 → {v[8]:.6f} (not representative, see the ceiling)" if v.get(8) else "") + ".", "",
          "- **There is no monotone growth towards 6√2 = 8.485281.** The value oscillates in the corridor "
          f"[{min(x for k, x in v.items() if x and k < 8):.3f}, {max(x for k, x in v.items() if x and k < 8):.3f}] "
          "and approaches neither 7.6605 nor 8.485281. The conclusion “HW carries over” **was not confirmed**.",
          f"- **The strict plateau criterion is not met:** the preregistration required neighbouring dimensions to agree "
          f"to within 1e−3 (and 0.05 for the pair d = 4, 6), whereas in fact |{v[4]:.6f} − {v[6]:.6f}| = "
          f"{abs(v[4] - v[6]):.3f}. Therefore the result is presented more weakly than planned: not a “plateau”, but "
          "**the absence of growth** — three dimensions in a row stay around 6.83–6.93, whereas the step from d = 2 "
          "to d = 4 gave only +0.099, and from d = 4 to d = 6 a negative difference.",
          "- **The threshold 7.6605 was never exceeded**, so the scenario “this changes the branch's conclusion” did not arise.", "",
          "Substantively this is numerical evidence (not a proof) in favour of the view that time symmetry "
          "without selection cuts off the operational-independence loophole: the growth of the dimension of the phase space, "
          "which in the HW model gives the whole effect, adds nothing here.", "",
          "### RTS stage 1 predictions", "", "| prediction | confidence | came true |", "|---|---|---|"]
    rows = [("(2,2,2,2): best = 4+2√2", "0.9", abs(v[2] - (4 + 2 * 2 ** 0.5)) < 1e-3),
            ("(4,4,4,4): best in [6.82, 6.95]", "0.7", 6.82 <= v[4] <= 6.95),
            ("(4,4,4,4): a cold start will not beat the HW point (6.869154) by more than 0.05", "0.65",
             v[4] - 6.869154 <= 0.05),
            ("(6,6,6,6): the increment over (4,4,4,4) is less than 0.1", "0.6", v[6] - v[4] < 0.1),
            ("plateau: d = 4 and d = 6 within 0.05 and below 7.6605", "0.55", abs(v[4] - v[6]) <= 0.05),
            ("at no dimension does 𝒯 exceed 7.6605", "0.85",
             all(x < 7.6605 for x in v.values() if x)),
            ("at no dimension does 𝒯 reach 6√2", "0.9",
             all(x < 6 * 2 ** 0.5 - 1e-6 for x in v.values() if x)),
            ("(8,8,8,8) does not fit into the budget; the ceiling is recorded in numbers", "0.85", True),
            ("S.2: an upper bound under free operations will not be obtained", "0.8", True)]
    L += [f"| {a_} | {b_} | {ok(c_)} |" for a_, b_, c_ in rows]
    L += ["| S.2: reduction by symmetry will shrink the block by no more than a factor of four | 0.6 | not checked: the reduction was not "
          "applied, since it does not give a convex relaxation |",
          f"| bottom line: the branch closes with the outcome “a plateau below 7.6605” | 0.55 | partially: the values are below 7.6605, but "
          f"the strict plateau criterion is not met (spread {abs(v[4] - v[6]):.3f}) |", "",
          "**The architect's prediction** (at (8,8,8,8) the value will rise noticeably above 6.87, ~50%, with a note that in "
          f"RTS 0 a prediction in the same direction did not come true) — **NO**: the only start that fit into the budget gave "
          f"{v[8]:.6f}" + " with an under-converged ADMM; a prediction in the same direction did not come true for the second time in a row.", ""]
    # S.3 — the branch summary
    L += ["### S.3 Summary of the RTS branch", "",
          "**1. What has been proved (certificates, not numerical observations).**",
          "- Under the operations of the Hoffreumon–Woods model the maximum of 𝒯 over **all** real ISO processes is "
          "≤ 4.24264070 = 3√2 (a dual point, feasibility by Cholesky). The conditions of applicability: the operations are "
          "fixed (they are the HW operations); operational independence is **not required** — the bound holds on the wider "
          "set of all ISO states. The complex value of the same construction is 6√2, that is, in the "
          "translation into ISO exactly half is lost.",
          "- Under the found operations of the scan (S.2) the value at the point and the certificate agree to "
          + ", ".join(f"{(du['gpu'][f'd{d}'])['gap']:.0e} (d = {d})" for d in (2, 4, 6) if f"d{d}" in du.get("gpu", {}))
          + ": the state is squeezed out, the distance to the thresholds is created by the operations.", "",
          "**2. The mechanism: why the HW construction does not lie in ISO.**",
          "6√2 is accumulated from four rebit patterns — I and J_B1′J_B2′ give 2√2 each, J_A′J_C′ and "
          "J_A′J_B1′J_B2′J_C′ give √2 each. ISO forbids two of them: **J_A′J_C′** (forbidden in TF — it is a correlation "
          "of the outputs of A and C, a resource from the future boundary) and **J_B1′J_B2′** (forbidden in TB — a correlation of Bob's inputs, "
          "a resource from the past boundary). The marginal pieces of these patterns carry no contribution to 𝒯: after their removal "
          "𝒯 = 6√2 is preserved, but λmin = −1/128, and restoring positivity with noise eats up exactly "
          "the increment (2√2 remains). In the network language this is a phase reference shared by parties not connected by a common "
          "source; time symmetry without selection forbids it on both sides.", "",
          "**3. What remains open, in a testable formulation.**",
          "- The upper bound sup 𝒯 over real ISO processes with OI under **free** operations, at any "
          "dimension. A testable formulation: does there exist a real ISO process with OI, and operations, "
          "giving 𝒯 > 7.6605 (Renou's real bound)? Our maximum is in the table above.",
          "- A full enumeration of ISO₃ with a composite input for Bob (we worked inside the network form D12).",
          "- The behaviour at d ≥ 10 and the question of whether 𝒯 plateaus or grows logarithmically.", "",
          "**4. Deviations and limitations of the branch.**",
          "- **Narrowing to D12:** processes of the network form were considered (ω on A⊗B1⊗B2⊗C, ISO ⇔ both marginals "
          "maximally mixed), not all of ISO₃.",
          "- **There is no upper bound under free operations** (S.2): the problem over the operations is non-convex, and reducing by "
          "symmetry does not give a convex relaxation — 𝒯 is not invariant under the exchange of parties (3 outcomes for Alice against 6 "
          "for Charlie).",
          "- **The estimator gives lower bounds.** See-saw finds local maxima; a cross-check of two independent "
          "solvers (SCS on the CPU and ADMM on the GPU) at d = 4 showed that the SCS path systematically finds worse "
          "points. Therefore the numbers in the table are values attained, not maxima of the class.",
          "- **The share of failed starts** on the SCS path is high (at (2,2,2,2) — 22 of 42 attempts); on the GPU path there are "
          "no failures. A failed start is a solver failure at some step, and it is discarded entirely.",
          "- **Clarabel is inapplicable** at N ≥ 256: the dense Hessian block of the PSD cone svec(256)² requires "
          "a multi-gigabyte allocation in a single chunk, the failure happens in the Rust allocator and aborts the process. "
          "MOSEK is not in the environment. The cross-check of an interior-point solver against a first-order one was done at d = 2.",
          "- **The resource ceiling is recorded in numbers** (see the scan table and the section on d = 8), "
          "extrapolation instead of computation was not used.",
          "- **The point at d = 8 is not in the repository:** the file `results/rts_gpu_8.npz` weighs 129 MB and is listed in "
          "`.gitignore`; it is reproduced by a script from `scripts/run_all.sh`. The points d = 2, 4, 6 are saved.",
          "- **The environment failure in RTS 0:** a dense Δ basis (~7.5 GB) together with a parallel run brought down the user's "
          "system. After that the basis is sparse, every script has RLIMIT_AS, computations go one at a time; "
          "in the GPU path the basis is not needed at all — the projections are basis-free.", ""]
    return L



def main():
    a, b, e = load("stage_a.json"), load("stage_b.json"), load("stage_b_explore.json")
    L = ["# RESULTS — TSCAUSAL stage 0.1", "",
         "_This file is generated by `scripts/make_results.py` from `results/json/`. It is never edited by hand._", ""]
    L += prereg_block()
    L += architect_defects()
    if a:
        L += stage_a(a)
    if b:
        L += stage_b(b, load("prereg.json"))
    if e:
        L += explore(e)
    b2, pt = load("stage_b2.json"), load("precision.json")
    if b2:
        L += stage_b2(b2, pt)
    c = load("stage_c.json")
    if c:
        L += stage_c(c)
    dd = load("stage_d.json")
    if dd:
        L += stage_d(dd)
    if load("t3_terms.json"):
        L += stage_t3(load("t3_terms.json"), load("t3_classical.json"), load("t3_star.json"), load("t3_quantum.json"))
    if load("t31.json"):
        L += stage_t31(load("t31.json"), load("t31_extra.json"))
    if load("rts_gpu_scan.json"):
        L += stage_rts1(load("rts_gpu_scan.json"), load("rts_scan.json"),
                        {"cvxpy": load("rts_scan_dual.json") or {}, "gpu": load("rts_gpu_dual.json") or {}},
                        load("rts_gpu_calib.json") or {})
    if load("rts_struct.json"):
        L += stage_rts(load("rts_struct.json"), load("rts_seesaw.json"), load("rts_calib.json"), load("rts_4444.json"),
                       load("rts_hw_iso.json"), load("rts_hw_iso_dual.json"), load("rts_4444_final.json"))
    L += ["## Literature check", "",
          "`sources/litcheck/REPORT.md`: among the 8 works checked in full text (all those citing MH24 according to "
          "Semantic Scholar, 2508.02463, 2603.12283, 2403.02749 and others), no enumeration of the facets of the time-symmetric "
          "polytope was found (as of 2026-09-21). The caveats are in the report. This is a necessary but not sufficient "
          "condition for a claim of novelty.", "",
          "## Not done", "",
          "The letter to the authors was postponed by the architect's decision (PROMPT stage C). An upper bound on 𝒯 over real "
          "ISO processes with OI under free operations was not obtained (RTS, R.3).", ""]
    with open(os.path.join(ROOT, "RESULTS.md"), "w") as fh:
        fh.write("\n".join(L))
    print("RESULTS.md written")


if __name__ == "__main__":
    main()

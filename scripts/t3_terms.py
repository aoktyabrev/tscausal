"""
T3.0, item T.0 — structure of the terms of a process matrix without selection for N parties (qubits).

Definition of the class (derivation D10, PREREGISTRATION_T3.md): ISO_N = TF_N ∩ TB_N, where
  TF_N — the W giving normalised probabilities for all forward instruments (Tr_O Σ M = 1_I; the OCB class,
         MH-27: "TF ... coincide with the known set of bipartite process matrices studied by OCB");
  TB_N — the same for backward instruments (Tr_I Σ M = 1_O), i.e. the time reversal of TF_N (MH-30).
The null space is computed literally by definition: the rows are differences Tr[W ⊗_X M_X] for random
products of local operations; positivity of W is not taken into account here (only the linear part).
"""
import itertools
import json
import os
import sys
import time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import polytope as P  # noqa: E402

PAULI = [np.eye(2, dtype=complex), np.array([[0, 1], [1, 0]], complex),
         np.array([[0, -1j], [1j, 0]], complex), np.array([[1, 0], [0, -1]], complex)]
LOCAL = [(i, o) for i in range(4) for o in range(4)]          # local basis σ_i^{X_I} σ_o^{X_O}


def local_vec(M):
    """v[(i,o)] = Tr[(σ_i ⊗ σ_o) M] for a two-qubit operator M (order X_I ⊗ X_O)."""
    return np.array([np.trace(np.kron(PAULI[i], PAULI[o]) @ M).real for i, o in LOCAL])


def rand_choi(rng, direction):
    """Random Choi matrix: 'F' — Tr_O M = 1_I (CPTP), 'B' — Tr_I M = 1_O."""
    X = rng.normal(size=(4, 4)) + 1j * rng.normal(size=(4, 4))
    M = X @ X.conj().T
    T = M.reshape(2, 2, 2, 2)
    S = np.trace(T, axis1=1, axis2=3) if direction == "F" else np.trace(T, axis1=0, axis2=2)
    w, V = np.linalg.eigh(S)
    L = V @ np.diag(w ** -0.5) @ V.conj().T
    K = np.kron(L, np.eye(2)) if direction == "F" else np.kron(np.eye(2), L)
    return K @ M @ K.conj().T


def constraint_rows(N, rng, direction, n_samples):
    """Rows r_P = Π_X Tr[P_X M_X] − Π_X Tr[P_X M0_X] (M0 — "do nothing" = 1/2·1)."""
    v0 = local_vec(np.eye(4) / 2)
    rows = []
    for _ in range(n_samples):
        vs = [local_vec(rand_choi(rng, direction)) for _ in range(N)]
        r, r0 = vs[0], v0
        for v in vs[1:]:
            r = np.kron(r, v)
            r0 = np.kron(r0, v0)
        rows.append(r - r0)
    return np.array(rows)


def nullspace(A, tol=1e-9):
    _, s, Vt = np.linalg.svd(A, full_matrices=True)
    rank = int((s > tol * s[0]).sum())
    return Vt[rank:].T, rank


def classify(N, rng, directions, n_samples):
    A = np.vstack([constraint_rows(N, rng, d, n_samples) for d in directions])
    Nsp, rank = nullspace(A)
    n = 16 ** N
    # diagonality: each Pauli basis vector is either in the null space or orthogonal to it
    proj = Nsp @ Nsp.T
    diag = np.diag(proj)
    inside = [k for k in range(n) if diag[k] > 1 - 1e-8]
    outside = [k for k in range(n) if diag[k] < 1e-8]
    ambiguous = n - len(inside) - len(outside)
    return {"dim": n - rank, "inside": inside, "ambiguous": ambiguous}


def label(k, N):
    """Index of a basis element → local types per party: '-', 'I', 'O', 'IO'."""
    digits = []
    for _ in range(N):
        digits.append(k % 16)
        k //= 16
    digits = digits[::-1]
    out = []
    for d_ in digits:
        i, o = LOCAL[d_]
        out.append({(False, False): "-", (True, False): "I", (False, True): "O", (True, True): "IO"}[(i > 0, o > 0)])
    return tuple(out), digits


def rule_count(N):
    """Rule (derivation): a non-identity term is allowed if it has an "I-only" party and an "O-only" party."""
    return 16 ** N - 2 * 13 ** N + 10 ** N


def commutation(inside, N):
    """Whether the allowed terms commute pairwise; whether supports overlap and three-party terms exist."""
    ops = []
    for k in inside:
        types, digits = label(k, N)
        if all(t == "-" for t in types):
            continue
        paulis = []
        for d_ in digits:
            i, o = LOCAL[d_]
            paulis += [i, o]
        ops.append((types, paulis))
    anti = 0
    example = None
    for (t1, p1), (t2, p2) in itertools.combinations(ops, 2):
        # two Pauli products anticommute if the number of positions with different non-trivial Paulis is odd
        c = sum(1 for a, b in zip(p1, p2) if a and b and a != b)
        if c % 2 == 1:
            anti += 1
            if example is None:
                example = (t1, p1, t2, p2)
    parties = lambda t: sum(1 for x in t if x != "-")  # noqa: E731
    by_nparties = {}
    for t, _ in ops:
        by_nparties[parties(t)] = by_nparties.get(parties(t), 0) + 1
    types = sorted({t for t, _ in ops})
    return {"n_terms": len(ops), "anticommuting_pairs": anti, "example_anticommuting": example,
            "terms_by_number_of_parties": by_nparties, "n_types": len(types),
            "types": ["".join(f"{'ABCDE'[j]}{x}" for j, x in enumerate(t) if x != "-") for t in types]}


def main():
    rng = np.random.default_rng(20260923)
    out = {"stage": "T3.0/T.0", "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S")}
    for N, ns in ((2, 600), (3, 6000)):
        t0 = time.time()
        res = {}
        for name, dirs in (("TF", ("F",)), ("TB", ("B",)), ("ISO", ("F", "B"))):
            c = classify(N, rng, dirs, ns)
            res[name] = {"dim": c["dim"], "pauli_elements_inside": len(c["inside"]), "ambiguous": c["ambiguous"]}
            if name == "ISO":
                iso_inside = c["inside"]
        # the rule "∃ I-only and ∃ O-only" against the null space
        rule = [k for k in range(16 ** N)
                if (lambda t: ("I" in t and "O" in t) or all(x == "-" for x in t))(label(k, N)[0])]
        res["rule_count_formula"] = 1 + rule_count(N)
        res["rule_equals_nullspace"] = sorted(rule) == sorted(iso_inside)
        res["structure"] = commutation(iso_inside, N)
        res["seconds"] = round(time.time() - t0, 1)
        out[f"N{N}"] = res
    out["calibration_N2_equals_stageC_19"] = out["N2"]["ISO"]["dim"] == 19
    with open(os.path.join(P.ROOT, "results", "json", "t3_terms.json"), "w") as fh:
        json.dump(out, fh, ensure_ascii=False, indent=1, default=str)
    print(json.dumps({k: (v if k != "N3" else {kk: vv for kk, vv in v.items() if kk != "structure"}) for k, v in out.items()},
                     ensure_ascii=False, indent=1, default=str))
    print(json.dumps({k: v for k, v in out["N3"]["structure"].items() if k != "types"}, ensure_ascii=False, default=str))


if __name__ == "__main__":
    main()

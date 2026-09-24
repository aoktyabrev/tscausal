"""
RTS stage 0, R.3 at the dimensions (4,4,4,4) (a qubit plus a phase rebit for every party — the minimum for the
HW26 model). A see-saw over the real ISO+OI processes ω = ω₁⊗ω₂ + Δ (Δ ∈ Anti⊗Anti); the SDP over the state uses
SCS (Clarabel needs a dense KKT of ≈ 8.7 GB). Starts: (i) the HW26 point with Bob's POVM completed, (ii) random.
Result: results/json/rts_4444.json.
"""
import json
import os
import sys
import time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import polytope as P  # noqa: E402
import qproc as Q  # noqa: E402
import rts as R  # noqa: E402
import rts_seesaw as S  # noqa: E402


def complete_bob(F):
    """HW: Σ_b Γ̄{F_b} = Ī⁽²⁾⊗I (rank 8 of 16) — the POVM is incomplete; the rest is split evenly, Tr F_b = 4 (TS)."""
    rest = np.eye(16) - sum(F)
    return [f + rest / 4 for f in F]


def main():
    S.limit_memory(float(os.environ.get("RTS_MEM_GB", "6")))
    n_rand = int(os.environ.get("RTS_4444_STARTS", "4"))
    t0 = time.time()
    rng = np.random.default_rng(44440922)
    m = S.Model((4, 4, 4, 4))
    _, (omr, Ar, Fr, Cr) = R.main_cal()
    Fc = complete_bob(Fr)
    T4 = omr.reshape(16, 16, 16, 16)
    w1, w2 = np.einsum("ajbj->ab", T4), np.einsum("jajb->ab", T4)
    out = {"stage": "RTS0 (4,4,4,4)", "bob_completion": {
        "rest_eigs": sorted(set(np.round(np.linalg.eigvalsh(np.eye(16) - sum(Fr)), 12).tolist())),
        "T_HW_with_completed_F": R.T_value(omr, Ar, Fc, Cr),
        "bob_traces_completed": [float(np.trace(f)) for f in Fc]}}
    runs = []
    starts = [("HW_seed", (Ar, Fc, Cr, w1, w2))] + [(f"random_{k}", None) for k in range(n_rand)]
    for name, st in starts:
        t1 = time.time()
        r = S.run(m, rng, True, iters=15, tol=1e-6, start=st)
        rec = {"start": name, "seconds": round(time.time() - t1, 1)}
        if r is None:
            rec["failed"] = True
        else:
            rec.update({"value": r[0], "stats": S.RUN_STATS[-1], "check": S.check(m, *r[1:], rng)})
        runs.append(rec)
        print(f"  {name}: {rec.get('value')} ({rec['seconds']} s)", flush=True)
        out["runs"] = runs
        with open(os.path.join(P.ROOT, "results", "json", "rts_4444.json"), "w") as fh:
            json.dump(out, fh, ensure_ascii=False, indent=1, default=float)
    ok = [r for r in runs if not r.get("failed")]
    out["best_T_feasible"] = max((r["check"]["T_feasible"] for r in ok), default=None)
    out["failed"] = len(runs) - len(ok)
    out["solver_stats"] = dict(Q.STATS)
    out["seconds"] = round(time.time() - t0, 1)
    with open(os.path.join(P.ROOT, "results", "json", "rts_4444.json"), "w") as fh:
        json.dump(out, fh, ensure_ascii=False, indent=1, default=float)
    print(json.dumps({k: v for k, v in out.items() if k != "runs"}, ensure_ascii=False, indent=1, default=float))


if __name__ == "__main__":
    main()

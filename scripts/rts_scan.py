"""
RTS stage 1, S.1 — a dimension scan: the same see-saw with free operations (scenario D12) at
(2,2,2,2), (4,4,4,4), (6,6,6,6), (8,8,8,8). Cold starts are mandatory; warm ones (an embedding of the cleaned
point of a smaller dimension) are reported separately and only together with cold starts of the same dimension.
The final point of every start is cleaned up with per-factor noise (ISO and OI exact, positivity via Cholesky),
and the reported number is the cleaned 𝒯. The resource ceiling is recorded as numbers, without extrapolation.
Result: results/json/rts_scan.json; the best points go to results/rts_scan_<d>.npz.
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
import rts_4444_ext as E  # noqa: E402
import rts_seesaw as S  # noqa: E402

OUT = os.path.join(P.ROOT, "results", "json", "rts_scan.json")


def embed_state(w, d, dp, rng):
    """w on (d⊗d) → w' on (dp⊗dp) with marginals I/dp: w' = (d/dp)·w ⊕ (r/dp)·σ, where σ is maximally entangled
    on the complement (r = dp − d), with a block structure on both sides."""
    r = dp - d
    wp = np.zeros((dp * dp, dp * dp))
    idx_sub = np.array([i * dp + j for i in range(d) for j in range(d)])
    wp[np.ix_(idx_sub, idx_sub)] = (d / dp) * w
    if r:
        v = np.zeros(r * r)
        for i in range(r):
            v[i * r + i] = 1 / np.sqrt(r)
        sig = np.outer(v, v)
        idx_comp = np.array([i * dp + j for i in range(d, dp) for j in range(d, dp)])
        wp[np.ix_(idx_comp, idx_comp)] = (r / dp) * sig
    return wp


def embed_ops(A, d, dp, n_settings):
    """POVM: A_{a|x} ⊕ I_comp/2 — the sum over a stays I, and the TS condition Σ_x Tr = k·dp holds automatically."""
    out = {}
    for s in range(1, n_settings + 1):
        out[s] = []
        for k in (0, 1):
            M = np.zeros((dp, dp))
            M[:d, :d] = A[s][k]
            M[d:, d:] = np.eye(dp - d) / 2
            out[s].append(M)
    return out


def embed_bob(F, dB, dBp):
    return [np.block([[f, np.zeros((dB, dBp - dB))], [np.zeros((dBp - dB, dB)), np.eye(dBp - dB) / 4]]) for f in F]


def warm_start(m, src, rng):
    """A warm start: the embedding of the cleaned point of a smaller dimension (see PREREGISTRATION_RTS1.md)."""
    d, dp = src["d"], m.dims[0]
    w1 = embed_state(src["w1"], d, dp, rng)          # ω₁ on (A⊗B1): d⊗d → dp⊗dp
    w2 = embed_state(src["w2"], d, dp, rng)
    A = embed_ops(src["A"], d, dp, 3)
    C = embed_ops(src["C"], d, dp, 6)
    F = embed_bob(src["F"], d * d, dp * dp)
    return A, F, C, w1, w2


def run_dim(dims, n_success_target, iters, budget_s, rng, warm=None, max_attempts_factor=4):
    """Keeps starting until n_success_target SUCCESSFUL starts have been collected (failed ones do not count),
    or until the time budget or the attempt limit runs out. Every point is cleaned with per-factor noise
    (OI and ISO exact)."""
    m = S.Model(dims)
    recs, t0 = [], time.time()
    starts = ([("тёплый", warm_start(m, warm, rng))] if warm else [])
    starts += [("холодный", None)] * (n_success_target * max_attempts_factor)
    n_ok = 0
    for kind, st in starts:
        if n_ok >= n_success_target + (1 if warm else 0):
            break
        if time.time() - t0 > budget_s:
            recs.append({"kind": kind, "skipped": "бюджет времени исчерпан"})
            break
        t1 = time.time()
        try:
            r = S.run(m, rng, True, iters=iters, tol=1e-6, start=st)
        except MemoryError:
            recs.append({"kind": kind, "failed": "MemoryError"})
            break
        if r is None:
            recs.append({"kind": kind, "failed": "отказ солвера"})
            continue
        val, om, A, F, C = r
        n1 = dims[0] * dims[1]
        T4 = om.reshape(n1, n1, n1, n1)
        w1, w2 = np.einsum("ajbj->ab", T4), np.einsum("jajb->ab", T4)
        Dc = om - np.kron(w1, w2)
        cl = E.cleanup_oi(m, w1, w2, Dc, A, F, C, rng)
        n_ok += 1
        recs.append({"kind": kind, "T_raw": val, "T_clean": cl["T"], "min_eig": cl["min_eig"],
                     "iso_dev": max(cl["iso_marginals_dev"]), "oi": cl["oi_violation"], "q_noise": cl["q_noise"],
                     "delta_rel_norm": cl["delta_rel_norm"], "seconds": round(time.time() - t1, 1),
                     "point": {"w1": w1, "w2": w2, "A": A, "F": F, "C": C, "d": dims[0]}})
        print(f"  {dims} {kind}: raw {val:.6f} → cleaned {cl['T']:.6f} ({recs[-1]['seconds']:.0f} s)", flush=True)
    return recs


def summarize(dims, recs):
    ok = [r for r in recs if "T_clean" in r]
    best = max(ok, key=lambda r: r["T_clean"]) if ok else None
    return {"dims": list(dims), "n_success": len(ok), "n_attempts": len(recs),
            "n_failed": sum(1 for r in recs if "failed" in r),
            "n_skipped": sum(1 for r in recs if "skipped" in r),
            "T_clean_best": best["T_clean"] if best else None, "T_raw_best": best["T_raw"] if best else None,
            "best_kind": best["kind"] if best else None,
            "min_eig": best["min_eig"] if best else None, "iso_dev": best["iso_dev"] if best else None,
            "oi": best["oi"] if best else None, "q_noise": best["q_noise"] if best else None,
            "T_clean_all": sorted((r["T_clean"] for r in ok), reverse=True),
            "seconds": round(sum(r.get("seconds", 0) for r in recs), 1)}


def main():
    S.limit_memory(float(os.environ.get("RTS_MEM_GB", "12")))
    rng = np.random.default_rng(20260923)
    out = json.load(open(OUT)) if os.path.exists(OUT) else {"stage": "RTS1 S.1 скан по размерности"}
    plan = json.loads(os.environ.get("RTS_SCAN_PLAN", '[[2,25,40,1800],[4,20,10,54000]]'))
    prev = None
    for d, nst, iters, budget in plan:
        dims = (d,) * 4
        key = f"d{d}"
        warm = None
        if prev is not None and d > prev["d"]:
            warm = prev
        t0 = time.time()
        recs = run_dim(dims, nst, iters, budget, rng, warm=warm)
        pts = [r.pop("point") for r in recs if "point" in r]
        s = summarize(dims, recs)
        s["records"] = recs
        s["wall_seconds"] = round(time.time() - t0, 1)
        out[key] = s
        with open(OUT, "w") as fh:
            json.dump(out, fh, ensure_ascii=False, indent=1, default=float)
        if pts:
            b = pts[int(np.argmax([r["T_clean"] for r in recs if "T_clean" in r]))]
            np.savez(os.path.join(P.ROOT, "results", f"rts_scan_{d}.npz"), w1=b["w1"], w2=b["w2"],
                     A=np.array(b["A"], dtype=object), F=np.array(b["F"]), C=np.array(b["C"]))
            prev = b
        print(f"{dims}: best cleaned {s['T_clean_best']}, successful {s['n_success']}, failed {s['n_failed']}, "
              f"{s['wall_seconds']:.0f} s", flush=True)
    out["solver_stats"] = dict(Q.STATS)
    out["thresholds"] = {"4+2sqrt2": 4 + 2 * np.sqrt(2), "real_bound_RTW21": 7.6605, "6sqrt2": 6 * np.sqrt(2)}
    with open(OUT, "w") as fh:
        json.dump(out, fh, ensure_ascii=False, indent=1, default=float)


if __name__ == "__main__":
    main()

#!/usr/bin/env bash
# Full reproduction of Stage A and Stage B. Environment: .env (micromamba, conda-forge:
# python 3.12, cddlib, gmp, lrslib) + pycddlib 3.0.2 built against .env.
# Stage C, D additionally: pip install cvxpy clarabel scs mpmath sympy (into .env).
# Creating the environment (if .env is absent):
#   micromamba create -p .env -c conda-forge python=3.12 cddlib gmp lrslib pip pypdf cython setuptools compilers
#   CFLAGS="-I$PWD/.env/include" LDFLAGS="-L$PWD/.env/lib -Wl,-rpath,$PWD/.env/lib" \
#     .env/bin/python -m pip install --no-build-isolation "pycddlib>=3,<4"
set -euo pipefail
cd "$(dirname "$0")/.."
PY=${PY:-.env/bin/python}
$PY scripts/precision_test.py > /dev/null
$PY -c "import json,sys; d=json.load(open('results/json/precision.json')); sys.exit(0 if d['gate_pass'] else 'precision: gate not passed')"
$PY scripts/stage_a.py > /dev/null
$PY -c "import json,sys; d=json.load(open('results/json/stage_a.json')); sys.exit(0 if d['gate_pass'] else 'Stage A: gate not passed')"
$PY scripts/stage_b.py > /dev/null
$PY -c "import json,sys; d=json.load(open('results/json/stage_b.json')); sys.exit('Stage B: '+d['STOP'] if 'STOP' in d else 0)"
$PY scripts/stage_b_explore.py > /dev/null
$PY scripts/stage_b2.py > /dev/null
$PY scripts/stage_c.py > /dev/null 2>&1   # ~30–40 min (see-saw, qutrits)
$PY scripts/stage_d.py > /dev/null 2>&1   # ~55 min (main part — see-saw of the direct scenario)
# T3, T3.1 — their own scripts (t3_*.py, t31*.py), run separately.
# RTS stage 0 (memory: each script sets RLIMIT_AS, run strictly one at a time):
$PY scripts/rts_struct.py > /dev/null 2>&1        # structure of J-terms, HW, SDP at the HW operations (~1 min)
$PY scripts/rts_calib.py > /dev/null 2>&1         # anti-vacuum calibration: complex see-saw → 6√2 (~1 min)
$PY scripts/rts_seesaw.py > /dev/null 2>&1        # real see-saw, small dimensions (~23 min)
$PY scripts/rts_hw_iso.py > /dev/null 2>&1        # R.2.2: HW decomposition, term removal, SDP over ISO (~15 min)
$PY scripts/rts_hw_iso_dual.py > /dev/null 2>&1   # dual certificate 3√2 (~3 s)
$PY scripts/rts_4444.py > /dev/null 2>&1          # see-saw (4,4,4,4): HW start + 4 random (~3 h)
$PY scripts/rts_4444_ext.py > /dev/null 2>&1      # continuation of the HW start, 60 iterations (~6,6 h)
$PY scripts/rts_4444_final.py > /dev/null 2>&1    # cleanup of the final point (ISO and operational independence exact)
# RTS stage 1 (scan over dimension). The state step is ADMM on GPU (torch with CUDA is required);
# without a GPU the same scripts run on CPU, but (6,6,6,6) and (8,8,8,8) become unreachable.
$PY scripts/rts_gpu_calib.py > /dev/null 2>&1                                  # ADMM calibration against SCS (~1 min)
RTS_GPU_PLAN='[[2,20,15,800,1800],[4,20,20,1200,10800]]' $PY scripts/rts_gpu_scan.py > /dev/null 2>&1   # ~1,5 h
RTS_GPU_WARM_FROM=4 RTS_GPU_PLAN='[[6,5,15,1200,25200]]' $PY scripts/rts_gpu_scan.py > /dev/null 2>&1   # ~6 h
RTS_GPU_WARM_FROM=6 RTS_GPU_PLAN='[[8,1,4,400,16200]]' $PY scripts/rts_gpu_scan.py > /dev/null 2>&1     # ~5,6 h
RTS_DUAL_DIMS='[2,4,6,8]' $PY scripts/rts_gpu_dual.py > /dev/null 2>&1         # dual certificates (~0,5 h)
RTS_DUAL_DIMS='[2,4]' RTS_DUAL_SOLVERS='["SCS"]' $PY scripts/rts_scan_dual.py > /dev/null 2>&1  # cross-check via cvxpy
$PY scripts/make_results.py

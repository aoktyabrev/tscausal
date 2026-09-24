#!/usr/bin/env bash
# Воспроизведение Stage A и Stage B целиком. Окружение: .env (micromamba, conda-forge:
# python 3.12, cddlib, gmp, lrslib) + pycddlib 3.0.2, собранный против .env.
# Stage C, D дополнительно: pip install cvxpy clarabel scs mpmath sympy (в .env).
# Создание окружения (если .env нет):
#   micromamba create -p .env -c conda-forge python=3.12 cddlib gmp lrslib pip pypdf cython setuptools compilers
#   CFLAGS="-I$PWD/.env/include" LDFLAGS="-L$PWD/.env/lib -Wl,-rpath,$PWD/.env/lib" \
#     .env/bin/python -m pip install --no-build-isolation "pycddlib>=3,<4"
set -euo pipefail
cd "$(dirname "$0")/.."
PY=${PY:-.env/bin/python}
$PY scripts/precision_test.py > /dev/null
$PY -c "import json,sys; d=json.load(open('results/json/precision.json')); sys.exit(0 if d['gate_pass'] else 'точность: ворота не пройдены')"
$PY scripts/stage_a.py > /dev/null
$PY -c "import json,sys; d=json.load(open('results/json/stage_a.json')); sys.exit(0 if d['gate_pass'] else 'Stage A: ворота не пройдены')"
$PY scripts/stage_b.py > /dev/null
$PY -c "import json,sys; d=json.load(open('results/json/stage_b.json')); sys.exit('Stage B: '+d['STOP'] if 'STOP' in d else 0)"
$PY scripts/stage_b_explore.py > /dev/null
$PY scripts/stage_b2.py > /dev/null
$PY scripts/stage_c.py > /dev/null 2>&1   # ~30–40 мин (see-saw, кутриты)
$PY scripts/stage_d.py > /dev/null 2>&1   # ~55 мин (основное — see-saw прямого сценария)
# T3, T3.1 — свои скрипты (t3_*.py, t31*.py), запускаются отдельно.
# RTS stage 0 (память: каждый скрипт ставит RLIMIT_AS, запускать строго по одному):
$PY scripts/rts_struct.py > /dev/null 2>&1        # структура J-членов, HW, SDP при операциях HW (~1 мин)
$PY scripts/rts_calib.py > /dev/null 2>&1         # антивакуумная калибровка: комплексный see-saw → 6√2 (~1 мин)
$PY scripts/rts_seesaw.py > /dev/null 2>&1        # вещественный see-saw, малые размерности (~23 мин)
$PY scripts/rts_hw_iso.py > /dev/null 2>&1        # R.2.2: разложение HW, удаление членов, SDP по ISO (~15 мин)
$PY scripts/rts_hw_iso_dual.py > /dev/null 2>&1   # двойственный сертификат 3√2 (~3 с)
$PY scripts/rts_4444.py > /dev/null 2>&1          # see-saw (4,4,4,4): старт HW + 4 случайных (~3 ч)
$PY scripts/rts_4444_ext.py > /dev/null 2>&1      # продолжение старта HW, 60 итераций (~6,6 ч)
$PY scripts/rts_4444_final.py > /dev/null 2>&1    # очистка финальной точки (ISO и ОН точные)
# RTS stage 1 (скан по размерности). Шаг по состоянию — ADMM на GPU (нужен torch с CUDA);
# без GPU те же скрипты работают на CPU, но (6,6,6,6) и (8,8,8,8) становятся недосягаемы.
$PY scripts/rts_gpu_calib.py > /dev/null 2>&1                                  # калибровка ADMM против SCS (~1 мин)
RTS_GPU_PLAN='[[2,20,15,800,1800],[4,20,20,1200,10800]]' $PY scripts/rts_gpu_scan.py > /dev/null 2>&1   # ~1,5 ч
RTS_GPU_WARM_FROM=4 RTS_GPU_PLAN='[[6,5,15,1200,25200]]' $PY scripts/rts_gpu_scan.py > /dev/null 2>&1   # ~6 ч
RTS_GPU_WARM_FROM=6 RTS_GPU_PLAN='[[8,1,4,400,16200]]' $PY scripts/rts_gpu_scan.py > /dev/null 2>&1     # ~5,6 ч
RTS_DUAL_DIMS='[2,4,6,8]' $PY scripts/rts_gpu_dual.py > /dev/null 2>&1         # двойственные сертификаты (~0,5 ч)
RTS_DUAL_DIMS='[2,4]' RTS_DUAL_SOLVERS='["SCS"]' $PY scripts/rts_scan_dual.py > /dev/null 2>&1  # сверка через cvxpy
$PY scripts/make_results.py

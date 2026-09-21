#!/usr/bin/env bash
# Воспроизведение Stage A и Stage B целиком. Окружение: .env (micromamba, conda-forge:
# python 3.12, cddlib, gmp, lrslib) + pycddlib 3.0.2, собранный против .env.
# Создание окружения (если .env нет):
#   micromamba create -p .env -c conda-forge python=3.12 cddlib gmp lrslib pip pypdf cython setuptools compilers
#   CFLAGS="-I$PWD/.env/include" LDFLAGS="-L$PWD/.env/lib -Wl,-rpath,$PWD/.env/lib" \
#     .env/bin/python -m pip install --no-build-isolation "pycddlib>=3,<4"
set -euo pipefail
cd "$(dirname "$0")/.."
PY=${PY:-.env/bin/python}
$PY scripts/stage_a.py > /dev/null
$PY -c "import json,sys; d=json.load(open('results/json/stage_a.json')); sys.exit(0 if d['gate_pass'] else 'Stage A: ворота не пройдены')"
$PY scripts/stage_b.py > /dev/null
$PY -c "import json,sys; d=json.load(open('results/json/stage_b.json')); sys.exit('Stage B: '+d['STOP'] if 'STOP' in d else 0)"
$PY scripts/stage_b_explore.py > /dev/null
$PY scripts/make_results.py

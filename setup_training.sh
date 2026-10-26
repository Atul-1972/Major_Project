#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")"
PYTHON_BIN="${PYTHON_BIN:-python3}"
"$PYTHON_BIN" -c 'import sys; assert (3,11) <= sys.version_info < (3,14), "Use Python 3.11, 3.12 or 3.13 (3.11 tested locally)"'
"$PYTHON_BIN" -m venv .venv-hpc
.venv-hpc/bin/python -m pip install --upgrade pip
# College administrators may select another officially supported index for their drivers.
TORCH_INDEX_URL="${TORCH_INDEX_URL:-https://download.pytorch.org/whl/cu126}"
.venv-hpc/bin/python -m pip install torch==2.9.1 torchvision==0.24.1 --index-url "$TORCH_INDEX_URL"
.venv-hpc/bin/python -m pip install -r requirements/training-linux.txt
.venv-hpc/bin/python -m pip check
.venv-hpc/bin/python train.py --check-package
echo 'Setup finished. Run bash run_training.sh inside your allocated NVIDIA GPU job.'

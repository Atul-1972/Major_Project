#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")"
PYTHON_BIN="${PYTHON_BIN:-$PWD/.venv-hpc/bin/python}"
if [[ ! -x "$PYTHON_BIN" ]] && ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
  echo 'Python environment missing. Run bash setup_training.sh first, or set PYTHON_BIN to the college Python environment.' >&2
  exit 1
fi
export CUBLAS_WORKSPACE_CONFIG=:4096:8
export MPLBACKEND=Agg
export PYTHONUNBUFFERED=1
mkdir -p artifacts/training/logs
LOG_PATH="artifacts/training/logs/run-$(date -u +%Y%m%dT%H%M%S)-$$.log"
"$PYTHON_BIN" -u train.py "$@" 2>&1 | tee "$LOG_PATH"

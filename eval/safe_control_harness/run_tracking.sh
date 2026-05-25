#!/usr/bin/env bash
# Wrapper for safe_control's test_tracking.py with our default args
# (DynamicUnicycle + MPC-CBF) + headless matplotlib.
set -euo pipefail

REFS=${REFS:-${HOME}/.local/share/representation-aware-mppi/refs}
SC="${REFS}/safe_control"

if [[ ! -d "${SC}/.venv" ]]; then
  echo "safe_control venv missing — run: bash scripts/fetch_refs.sh && cd ${SC} && uv venv .venv && uv pip install -e ."
  exit 1
fi

export MPLBACKEND=Agg
cd "${SC}"
exec .venv/bin/python examples/test_tracking.py "$@"

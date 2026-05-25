#!/usr/bin/env bash
# Wrapper for safe_control's DPCBF (Dynamic Parabolic Control Barrier Function)
# demo — kinematic bicycle + dynamic obstacles avoidance.
#
# Reference: Park, Kim, Panagou. "Beyond Collision Cones: Dynamic Obstacle
# Avoidance for Nonholonomic Robots via Dynamic Parabolic Control Barrier
# Functions." ICRA 2026. arXiv:2510.01402
set -euo pipefail

REFS=${REFS:-${HOME}/.local/share/representation-aware-mppi/refs}
SC="${REFS}/safe_control"

if [[ ! -d "${SC}/.venv" ]]; then
  echo "safe_control venv missing — run: bash scripts/fetch_refs.sh && cd ${SC} && uv venv .venv && uv pip install -e ."
  exit 1
fi

export MPLBACKEND=Agg
export PYTHONPATH=".:${PYTHONPATH:-}"
cd "${SC}"
exec .venv/bin/python dynamic_env/main.py "$@"

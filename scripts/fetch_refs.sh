#!/usr/bin/env bash
# Clone or update external reference repositories used by the offline harness
# (eval/safe_control_harness/, future learning/cfm_unicycle/, etc.).
#
# Repos are kept OUTSIDE the git tree at ~/.local/share/representation-aware-mppi/refs
# - keeps our repo lean
# - lets us pin specific commits per harness without vendoring
# - license-safe (especially for repos with unstated license)
set -euo pipefail

REFS=${REFS:-${HOME}/.local/share/representation-aware-mppi/refs}
mkdir -p "${REFS}"

# repo_url subdir [depth]
declare -a REPOS=(
  "https://github.com/tkkim-robot/safe_control.git           safe_control     1"
  "https://github.com/James-R-Han/DR-MPC.git                  DR-MPC           1"
  "https://github.com/CORE-Robotics-Lab/TCFM.git              TCFM             1"
  "https://github.com/m-kazuki/cfm_mppi.git                   cfm_mppi         1"
)

for line in "${REPOS[@]}"; do
  read -r url subdir depth <<<"${line}"
  dest="${REFS}/${subdir}"
  if [[ -d "${dest}/.git" ]]; then
    echo "[update] ${subdir}"
    git -C "${dest}" pull --ff-only --depth "${depth}" 2>&1 | tail -2 || true
  else
    echo "[clone ] ${subdir}"
    git clone --depth "${depth}" "${url}" "${dest}" 2>&1 | tail -2
  fi
done

echo
echo "Refs at ${REFS}:"
ls -la "${REFS}"

#!/usr/bin/env bash
# Idempotent fetcher for RDSim's gazebo_models (worlds reference these via
# model:// URIs). Cloned outside the repo to keep git slim (~1.3 GB).
#
# After this runs once, GZ_SIM_RESOURCE_PATH should include
#   ~/.local/share/representation-aware-mppi/rdsim/rdsim_gazebo/models
# The Stage-2 launches (jackal_outdoor_sim.launch.py with world:=city)
# do this automatically.
#
# RDSim itself ships only city_terrain, ocean, and asphalt_plane. The
# remainder of small_city's <include> URIs (apartment, oak_tree, hatchback,
# pickup, suv, ambulance, etc.) are Gazebo Classic stock models and must
# be sourced separately (Fuel mirror or a Classic model dump). The Stage-2
# launch tolerates missing models at gz-sim startup; the world will load,
# just with empty space where missing models would have rendered.
set -euo pipefail

DEST="${HOME}/.local/share/representation-aware-mppi/rdsim"
URL="https://github.com/Geonhee-LEE/RDSim.git"

mkdir -p "$(dirname "${DEST}")"

if [[ -L "${DEST}" ]]; then
  echo "RDSim already symlinked at ${DEST} -> $(readlink -f "${DEST}")"
elif [[ -d "${DEST}/.git" ]]; then
  echo "RDSim already cloned at ${DEST} - pulling latest"
  git -C "${DEST}" pull --ff-only
else
  echo "Cloning RDSim into ${DEST}"
  git clone --depth 1 "${URL}" "${DEST}"
fi

echo "RDSim models available at ${DEST}/rdsim_gazebo/models/"
echo "Add this to GZ_SIM_RESOURCE_PATH (the launch does this automatically):"
echo "  ${DEST}/rdsim_gazebo/models"

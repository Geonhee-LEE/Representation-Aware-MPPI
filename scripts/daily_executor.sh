#!/usr/bin/env bash
# Auto-research daily executor — invoked by cron at ~10:00 KST (after the morning brief).
# Runs `claude -p` with the auto_research prompt; broader allowlist than brief because
# the executor needs to edit code + run git/colcon.
# flock guard: a previous executor that overran budget must NOT collide with the next tick.
set -euo pipefail

REPO=/home/geonhee/Representation-Aware-MPPI
PROMPT="${REPO}/scripts/prompts/auto_research.md"
STATE_DIR=/home/geonhee/.local/state/representation-aware-mppi
LOCK_FILE="${STATE_DIR}/executor.lock"
LOG_DIR=/home/geonhee/.local/share/representation-aware-mppi/logs
LOG="${LOG_DIR}/executor-$(TZ=Asia/Seoul date +%Y-%m-%d).log"

mkdir -p "${STATE_DIR}" "${LOG_DIR}"

# Single-instance guard. Bail silently if a prior run is still going.
exec 9>"${LOCK_FILE}"
if ! flock -n 9; then
  echo "[$(date -Iseconds)] executor already running; skipping this tick" >> "${LOG}"
  exit 0
fi

# Cron has a minimal PATH; ensure claude + git + colcon are reachable.
export PATH="/home/geonhee/.local/bin:/usr/local/bin:/usr/bin:/bin"

cd "${REPO}"

# Tools the executor is allowed to use without prompting.
ALLOWED=(
  "Bash"
  "Read"
  "Edit"
  "Write"
  "Grep"
  "Glob"
  "mcp__claude_ai_Notion__notion-fetch"
  "mcp__claude_ai_Notion__notion-search"
  "mcp__claude_ai_Notion__notion-create-pages"
  "mcp__claude_ai_Notion__notion-update-page"
)

{
  echo "=== executor start $(date -Iseconds) ==="
  claude -p "$(cat "${PROMPT}")" \
    --output-format text \
    --permission-mode acceptEdits \
    --allowedTools "${ALLOWED[@]}"
  rc=$?
  echo "=== executor end $(date -Iseconds) rc=${rc} ==="
  exit ${rc}
} >> "${LOG}" 2>&1

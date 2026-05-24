#!/usr/bin/env bash
# Curator agent — invoked by cron daily at 23:00 (after wrap).
# SPDX-License-Identifier: BSD-3-Clause
#
# Drains the [auto] PR backlog so queue-cap pressure doesn't deadlock the hourly
# executor. Auto-merges safe-surface [auto] PRs after 48 h idle; rebases
# conflicting safe-surface PRs; labels hopeless PRs `needs-user-attention`.
# Never touches src/, never force-pushes main, never closes PRs.
set -euo pipefail

REPO=/home/geonhee/Representation-Aware-MPPI
PROMPT="${REPO}/scripts/prompts/curator.md"
STATE_DIR=/home/geonhee/.local/state/representation-aware-mppi
LOCK_FILE="${STATE_DIR}/curator.lock"
LOG_DIR=/home/geonhee/.local/share/representation-aware-mppi/logs
LOG="${LOG_DIR}/curator-$(TZ=Asia/Seoul date +%Y-%m-%d).log"

mkdir -p "${STATE_DIR}" "${LOG_DIR}"

exec 9>"${LOCK_FILE}"
if ! flock -n 9; then
  echo "[$(date -Iseconds)] curator already running; skipping this tick" >> "${LOG}"
  exit 0
fi

export PATH="/home/geonhee/.local/bin:/usr/local/bin:/usr/bin:/bin"

cd "${REPO}"

ALLOWED=(
  "Bash"
  "Read"
  "mcp__claude_ai_Notion__notion-fetch"
)

{
  echo "=== curator start $(date -Iseconds) ==="
  claude -p "$(cat "${PROMPT}")" \
    --output-format text \
    --permission-mode acceptEdits \
    --allowedTools "${ALLOWED[@]}"
  rc=$?
  echo "=== curator end $(date -Iseconds) rc=${rc} ==="
  exit ${rc}
} >> "${LOG}" 2>&1

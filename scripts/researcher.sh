#!/usr/bin/env bash
# Researcher agent — invoked by cron every 4 hours.
# SPDX-License-Identifier: BSD-3-Clause
#
# Web-searches MPPI / social-nav / flow-matching / mobile-robot research, appends
# hits to research/feed.md (cap 30) and the monthly archive, optionally creates
# Notion Backlog TODOs prefixed [research]. Quiet on dry cycles.
#
# flock guard: lite cycles can still overlap a long previous run; we skip silently.
set -euo pipefail

REPO=/home/geonhee/Representation-Aware-MPPI
PROMPT="${REPO}/scripts/prompts/researcher.md"
STATE_DIR=/home/geonhee/.local/state/representation-aware-mppi
LOCK_FILE="${STATE_DIR}/researcher.lock"
LOG_DIR=/home/geonhee/.local/share/representation-aware-mppi/logs
LOG="${LOG_DIR}/researcher-$(TZ=Asia/Seoul date +%Y-%m-%d).log"

mkdir -p "${STATE_DIR}" "${LOG_DIR}"

exec 9>"${LOCK_FILE}"
if ! flock -n 9; then
  echo "[$(date -Iseconds)] researcher already running; skipping this tick" >> "${LOG}"
  exit 0
fi

export PATH="/home/geonhee/.local/bin:/usr/local/bin:/usr/bin:/bin"

cd "${REPO}"

ALLOWED=(
  "Bash"
  "Read"
  "Edit"
  "Write"
  "Grep"
  "Glob"
  "WebSearch"
  "WebFetch"
  "mcp__claude_ai_Notion__notion-fetch"
  "mcp__claude_ai_Notion__notion-search"
  "mcp__claude_ai_Notion__notion-create-pages"
  "mcp__claude_ai_Notion__notion-update-page"
)

{
  echo "=== researcher start $(date -Iseconds) ==="
  claude -p "$(cat "${PROMPT}")" \
    --output-format text \
    --permission-mode acceptEdits \
    --allowedTools "${ALLOWED[@]}"
  rc=$?
  echo "=== researcher end $(date -Iseconds) rc=${rc} ==="
  exit ${rc}
} >> "${LOG}" 2>&1

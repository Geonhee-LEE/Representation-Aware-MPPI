#!/usr/bin/env bash
# Weekly rollup — invoked by cron Sunday 22:30 KST.
set -euo pipefail

REPO=/home/geonhee/Representation-Aware-MPPI
PROMPT="${REPO}/scripts/prompts/weekly.md"
LOG_DIR=/home/geonhee/.local/share/representation-aware-mppi/logs
LOG="${LOG_DIR}/weekly-$(TZ=Asia/Seoul date +%G-W%V).log"

mkdir -p "${LOG_DIR}"

export PATH="/home/geonhee/.local/bin:/usr/local/bin:/usr/bin:/bin"

cd "${REPO}"

ALLOWED=(
  "Bash"
  "Read"
  "mcp__claude_ai_Notion__notion-fetch"
  "mcp__claude_ai_Notion__notion-search"
  "mcp__claude_ai_Notion__notion-create-pages"
  "mcp__claude_ai_Notion__notion-update-page"
)

{
  echo "=== weekly start $(date -Iseconds) ==="
  claude -p "$(cat "${PROMPT}")" \
    --output-format text \
    --permission-mode acceptEdits \
    --allowedTools "${ALLOWED[@]}"
  rc=$?
  echo "=== weekly end $(date -Iseconds) rc=${rc} ==="
  exit ${rc}
} >> "${LOG}" 2>&1

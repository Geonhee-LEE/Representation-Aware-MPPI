#!/usr/bin/env bash
# Evening daily wrap — invoked by cron at 22:00 KST.
set -euo pipefail

REPO=/home/geonhee/Representation-Aware-MPPI
PROMPT="${REPO}/scripts/prompts/wrap.md"
LOG_DIR=/home/geonhee/.local/share/representation-aware-mppi/logs
LOG="${LOG_DIR}/wrap-$(TZ=Asia/Seoul date +%Y-%m-%d).log"

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
  echo "=== wrap start $(date -Iseconds) ==="
  claude -p "$(cat "${PROMPT}")" \
    --output-format text \
    --permission-mode acceptEdits \
    --allowedTools "${ALLOWED[@]}"
  rc=$?
  echo "=== wrap end $(date -Iseconds) rc=${rc} ==="
  exit ${rc}
} >> "${LOG}" 2>&1

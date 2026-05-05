#!/usr/bin/env bash
# Mirror Notion TODO DB → repo-root TODO.md (offline-readable snapshot).
# Pattern matches scripts/daily_brief.sh: shell wrapper invokes `claude -p`
# with a prompt that uses the Notion MCP tools. No separate Notion token.
#
# Idempotent. Safe to run from cron, the daily wrap step, or by hand.
# Re-running with no DB change leaves TODO.md untouched.
set -euo pipefail

REPO=/home/geonhee/Representation-Aware-MPPI
PROMPT="${REPO}/scripts/prompts/mirror_todos.md"
LOG_DIR=/home/geonhee/.local/share/representation-aware-mppi/logs
LOG="${LOG_DIR}/mirror-todos-$(TZ=Asia/Seoul date +%Y-%m-%d).log"

mkdir -p "${LOG_DIR}"

export PATH="/home/geonhee/.local/bin:/usr/local/bin:/usr/bin:/bin"

cd "${REPO}"

ALLOWED=(
  "Bash"
  "Read"
  "Write"
  "mcp__claude_ai_Notion__notion-fetch"
  "mcp__claude_ai_Notion__notion-search"
)

{
  echo "=== mirror-todos start $(date -Iseconds) ==="
  claude -p "$(cat "${PROMPT}")" \
    --output-format text \
    --permission-mode acceptEdits \
    --allowedTools "${ALLOWED[@]}"
  rc=$?
  echo "=== mirror-todos end $(date -Iseconds) rc=${rc} ==="
  exit ${rc}
} >> "${LOG}" 2>&1

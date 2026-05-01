#!/usr/bin/env bash
# Morning daily brief — invoked by cron at 09:00 KST.
# Runs `claude -p` with the brief prompt; tools are pre-allowlisted so no permission prompts.
set -euo pipefail

REPO=/home/geonhee/Representation-Aware-MPPI
PROMPT="${REPO}/scripts/prompts/brief.md"
LOG_DIR=/home/geonhee/.local/share/representation-aware-mppi/logs
LOG="${LOG_DIR}/brief-$(TZ=Asia/Seoul date +%Y-%m-%d).log"

mkdir -p "${LOG_DIR}"

# Cron has a minimal PATH; make sure claude + curl are reachable.
export PATH="/home/geonhee/.local/bin:/usr/local/bin:/usr/bin:/bin"

cd "${REPO}"

# Tools the brief is allowed to use without prompting.
ALLOWED=(
  "Bash"
  "Read"
  "mcp__claude_ai_Notion__notion-fetch"
  "mcp__claude_ai_Notion__notion-search"
  "mcp__claude_ai_Notion__notion-create-pages"
  "mcp__claude_ai_Notion__notion-update-page"
)

{
  echo "=== brief start $(date -Iseconds) ==="
  claude -p "$(cat "${PROMPT}")" \
    --output-format text \
    --permission-mode acceptEdits \
    --allowedTools "${ALLOWED[@]}"
  rc=$?
  echo "=== brief end $(date -Iseconds) rc=${rc} ==="
  exit ${rc}
} >> "${LOG}" 2>&1

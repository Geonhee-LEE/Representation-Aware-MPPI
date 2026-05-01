#!/usr/bin/env bash
# Urgent task agent — spawned inside a detached tmux session by telegram_poll.sh.
# Runs claude -p with the urgent prompt + the user's message; reports to Telegram.
#
# Usage (typically not invoked directly): urgent_agent.sh "<user message>" "<session>"
set -euo pipefail

MSG="${1:?message required}"
SESSION="${2:-ram-urgent-$(date +%Y%m%d-%H%M%S)}"

REPO=/home/geonhee/Representation-Aware-MPPI
PROMPT="${REPO}/scripts/prompts/urgent.md"
LOG_DIR=/home/geonhee/.local/share/representation-aware-mppi/logs
LOG="${LOG_DIR}/urgent-${SESSION}.log"

mkdir -p "${LOG_DIR}"
export PATH="/home/geonhee/.local/bin:/usr/local/bin:/usr/bin:/bin"
cd "${REPO}"

# shellcheck disable=SC1091
source ~/.config/representation-aware-mppi/telegram.env

# Tell the user we're starting (with notification — urgent path)
curl -fsS "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage" \
  --data-urlencode "chat_id=${TELEGRAM_CHAT_ID}" \
  --data-urlencode "text=🚨 긴급 작업 시작 [${SESSION}]
요청: ${MSG}
실행 중… (tmux attach -t ${SESSION} 으로 라이브 확인 가능)" \
  --data-urlencode "disable_web_page_preview=true" >/dev/null 2>&1 || true

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

full_prompt="$(cat "${PROMPT}")

## User message
${MSG}

## Session name
${SESSION}
"

{
  echo "=== urgent start $(date -Iseconds) session=${SESSION} ==="
  echo "MSG: ${MSG}"
  echo "--- claude output ---"
  set +e
  claude -p "${full_prompt}" \
    --output-format text \
    --permission-mode acceptEdits \
    --allowedTools "${ALLOWED[@]}"
  rc=$?
  set -e
  echo "=== urgent end $(date -Iseconds) rc=${rc} ==="

  # Fallback notice if claude died before posting its own report.
  if [[ ${rc} -ne 0 ]]; then
    curl -fsS "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage" \
      --data-urlencode "chat_id=${TELEGRAM_CHAT_ID}" \
      --data-urlencode "text=❌ 긴급 작업 비정상 종료 [${SESSION}] rc=${rc}
log: ${LOG}" >/dev/null 2>&1 || true
  fi

  # Linger so user can attach to inspect output before tmux exits.
  echo "session lingering 60s for inspection (tmux attach -t ${SESSION})…"
  sleep 60
  exit ${rc}
} >> "${LOG}" 2>&1

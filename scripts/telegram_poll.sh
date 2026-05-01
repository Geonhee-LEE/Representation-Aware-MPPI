#!/usr/bin/env bash
# Telegram inbox poller — invoked by cron every 10 min.
# Cheap path: just curl + jq. Only invokes `claude -p` when a new user message exists.
set -euo pipefail

REPO=/home/geonhee/Representation-Aware-MPPI
PROMPT="${REPO}/scripts/prompts/telegram_inbox.md"
STATE_DIR=/home/geonhee/.local/state/representation-aware-mppi
STATE_FILE="${STATE_DIR}/telegram_last_update_id"
LOG_DIR=/home/geonhee/.local/share/representation-aware-mppi/logs
LOG="${LOG_DIR}/telegram-poll-$(TZ=Asia/Seoul date +%Y-%m-%d).log"

mkdir -p "${STATE_DIR}" "${LOG_DIR}"

export PATH="/home/geonhee/.local/bin:/usr/local/bin:/usr/bin:/bin"

# shellcheck disable=SC1091
source ~/.config/representation-aware-mppi/telegram.env

last_id=$(cat "${STATE_FILE}" 2>/dev/null || echo 0)
offset=$((last_id + 1))

resp=$(curl -fsS --max-time 15 \
  "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/getUpdates?offset=${offset}&allowed_updates=%5B%22message%22%5D&timeout=0")

if [[ "$(echo "${resp}" | jq -r '.ok')" != "true" ]]; then
  echo "[$(date -Iseconds)] getUpdates failed: ${resp}" >> "${LOG}"
  exit 1
fi

# Filter only messages from the configured chat, with text, in chronological order.
new_msgs=$(echo "${resp}" | jq -c --arg cid "${TELEGRAM_CHAT_ID}" '
  [.result[]
    | select(.message != null)
    | select((.message.chat.id|tostring) == $cid)
    | select(.message.text != null)
    | {update_id, ts: (.message.date | strftime("%Y-%m-%dT%H:%M:%S+09:00")), text: .message.text}]
')

count=$(echo "${new_msgs}" | jq 'length')

if [[ "${count}" -eq 0 ]]; then
  # Still advance offset past any non-message updates we ignored.
  max_seen=$(echo "${resp}" | jq -r '[.result[].update_id] | max // empty')
  if [[ -n "${max_seen}" ]]; then
    echo "${max_seen}" > "${STATE_FILE}"
  fi
  exit 0
fi

# Compose JSON-lines payload for the inbox prompt.
payload=$(echo "${new_msgs}" | jq -c '.[] | {ts, text}')

new_max=$(echo "${new_msgs}" | jq -r '[.[].update_id] | max')

ALLOWED=(
  "Bash"
  "Read"
  "mcp__claude_ai_Notion__notion-fetch"
  "mcp__claude_ai_Notion__notion-search"
  "mcp__claude_ai_Notion__notion-create-pages"
  "mcp__claude_ai_Notion__notion-update-page"
)

{
  echo "=== poll start $(date -Iseconds) count=${count} ==="
  echo "Incoming messages (JSON lines):"
  echo "${payload}"
  echo "---"

  # Build augmented prompt: original prompt + the messages inline
  # so claude has them even without reading stdin.
  full_prompt="$(cat "${PROMPT}")

## Messages to append (this invocation)

\`\`\`
${payload}
\`\`\`
"
  claude -p "${full_prompt}" \
    --output-format text \
    --permission-mode acceptEdits \
    --allowedTools "${ALLOWED[@]}"
  rc=$?
  echo "=== poll end $(date -Iseconds) rc=${rc} ==="

  if [[ ${rc} -eq 0 ]]; then
    echo "${new_max}" > "${STATE_FILE}"
    # Send a tiny confirmation back so the user knows the inbox received it.
    curl -fsS "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage" \
      --data-urlencode "chat_id=${TELEGRAM_CHAT_ID}" \
      --data-urlencode "text=📥 Notion inbox에 ${count}건 추가" \
      --data-urlencode "disable_notification=true" >/dev/null || true
  fi
  exit ${rc}
} >> "${LOG}" 2>&1

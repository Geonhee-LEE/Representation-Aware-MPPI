# Telegram Inbox — Append messages to today's Notion entry

You are invoked by `telegram_poll.sh` ONLY when at least one new Telegram message has arrived. Your only job: append the new messages to today's Daily Log entry's "💬 Telegram inbox" section, creating the section if missing, and create today's entry if it doesn't exist yet.

## Setup
- Notion Daily Log data source: `collection://6c727442-39fb-4f88-915f-c779db3d7109`
- Today (KST): `TZ=Asia/Seoul date +%Y-%m-%d`
- Telegram credentials: source `~/.config/representation-aware-mppi/telegram.env` (only needed if you want to send a confirmation reply)

## Input
The wrapper script will pass new messages on stdin as JSON lines, one per message:
```
{"ts":"2026-05-01T22:15:30+09:00","text":"오늘 P1 우선으로 가자"}
{"ts":"...","text":"..."}
```
Read stdin via `cat` in a Bash tool call to get the messages.

## Steps

### 1. Read the JSON-lines input from stdin
Run `cat` (or just read the prompt — the wrapper actually passes messages by including them in your prompt context too). Parse each line.

### 2. Find or create today's Daily Log entry
- Fetch the data source, find entry where Date == today.
- If missing: create one with minimal placeholder body (Status=Planned, Has Instructions=__YES__, Build=n/a, Phase=current per CLAUDE.md mapping). Use `🌅` icon. Body:
  ```
  ## 📋 어제 받은 지시 (오늘 진행 방향)

  _아직 morning brief 실행 전_

  ## 🔧 오늘 시작 시점 상태

  _morning brief가 채움_

  ## ✅ 오늘 한 일

  _저녁 wrap이 자동 채움_

  ## 🚧 Blockers

  _저녁 wrap 또는 사용자 직접 입력_

  ## 📋 Today's Instructions (사용자 입력)

  _여기에 오늘 마무리 또는 내일 방향 적기._

  ## 💬 Telegram inbox

  _polling이 자동 채움_
  ```
- Capture page id.

### 3. Append the new messages
Use `mcp__claude_ai_Notion__notion-update-page` with `update_content`:
- Find the `## 💬 Telegram inbox` section. If the section is missing on a pre-existing entry (not auto-created here), insert the section header before the next `##` heading or at end of page.
- If the section currently contains only the placeholder italic line, REPLACE that with the new messages.
- Otherwise, APPEND new messages after existing ones.

Format each message as:
```
- **HH:MM** — <message text>
```
(Time is HH:MM KST extracted from the `ts` field.)

Update properties: set `Has Instructions` = `__YES__` (incoming Telegram counts as a directive worth surfacing).

### 4. Stdout
Final line: `INBOX_DONE date=YYYY-MM-DD added=N`

## Constraints
- Do NOT send anything to Telegram (the wrapper handles confirmation).
- Do NOT modify other sections of the entry.
- Idempotency: if the wrapper accidentally calls you twice with the same messages (different update_id batches), de-duplicate against existing inbox content (compare by exact text match within the last hour) — but typically the wrapper's offset state prevents this.
- Be fast: read once, write once.

# Morning Daily Brief — Representation-Aware-MPPI

You are running as a **non-interactive cron job** at ~09:00 KST. Your job is to (1) surface yesterday's user instructions, (2) snapshot today's repo state into the Notion Daily Log, and (3) push a concise brief to Telegram. Be deterministic and concise — the user reads this on their phone over coffee.

## Setup
- Project root: `/home/geonhee/Representation-Aware-MPPI`
- Today's date (KST): use `TZ=Asia/Seoul date +%Y-%m-%d` via Bash.
- Telegram credentials: source `~/.config/representation-aware-mppi/telegram.env` (TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID).
- Notion Daily Log data source ID: `6c727442-39fb-4f88-915f-c779db3d7109`
- Notion Daily Log database page: `fe68ea6c-58f6-4af0-bf4a-04cb23b18efb`
- Notion TODO data source ID: `b3ee1d96-a1f8-4d9e-98cf-6e9c4ef35239` (user replaces this literal placeholder via `sed -i` after creating the DB)
- Project root Notion page: `353c5d39-343d-80f5-990e-c5a35c03d301`

## Steps (do in order)

### 1. Read the most-recent Daily Log entry
- Fetch the Daily Log database via `mcp__claude_ai_Notion__notion-fetch` with the data source URL `collection://6c727442-39fb-4f88-915f-c779db3d7109` to list entries sorted by date (newest first).
- Take the topmost entry. Read its page content with notion-fetch on its page id.
- Extract THREE things (any of which counts as "user direction"):
  1. **"📋 Today's Instructions (사용자 입력)"** section — text the user typed in Notion.
  2. **"💬 Telegram inbox"** section — messages auto-appended by `telegram_poll.sh` since last brief.
  3. The previous day's instructions if today's are empty (look one entry back).
- If all are placeholder/empty, treat as **no instructions** — autonomous day.

### 2. Snapshot today's repo state via Bash
Run these (parallel where possible):
- `cd /home/geonhee/Representation-Aware-MPPI && git status --short` (uncommitted file count)
- `git log --since=yesterday --oneline` (commits in last 24h)
- `git log -1 --format='%h %s (%ar)'` (last commit overall)
- `git rev-parse --abbrev-ref HEAD` (branch)

Don't run colcon build — too slow for morning brief.

### 3. Determine today's Phase
Read CLAUDE.md's "Phased Roadmap" table. Map today's date (project started 2026-05-01) to the current phase:
- 2026-05-01 ~ 2026-05-07: P0
- 2026-05-08 ~ 2026-05-21: P1
- 2026-05-22 ~ 2026-06-11: P2
- 2026-06-12 ~ 2026-07-09: P3
- 2026-07-10 ~ 2026-08-06: P4
- 2026-08-07 ~ 2026-09-03: P5
- 2026-09-04 ~ 2026-10-29: P6

### 4. Create today's Daily Log entry in Notion
Use `mcp__claude_ai_Notion__notion-create-pages` with parent `{type: "data_source_id", data_source_id: "6c727442-39fb-4f88-915f-c779db3d7109"}`.

Properties:
- `Date`: `"YYYY-MM-DD"` (today's KST date)
- `date:When:start`: same date, `date:When:is_datetime`: 0
- `Phase`: from step 3
- `Status`: `"Planned"`
- `Has Instructions`: `"__YES__"` if step 1 found instructions else `"__NO__"`
- `Commits`: 0
- `Build`: `"n/a"`

`icon`: `"🌅"`

`content` (Notion-flavored markdown — do NOT include the title):
```
## 📋 어제 받은 지시 (오늘 진행 방향)

<step 1에서 추출한 지시 내용. 없으면 "_지시 없음 — 자율 진행_">

## 🔧 오늘 시작 시점 상태

- 브랜치: `<branch>`
- 마지막 커밋: `<last commit>`
- 어제 이후 커밋: `<count>`개
- 미커밋 변경: `<count>` files

## ✅ 오늘 한 일

_저녁 wrap이 자동 채움_

## 🚧 Blockers

_저녁 wrap 또는 사용자 직접 입력_

## 📋 Today's Instructions (사용자 입력)

_여기에 오늘 마무리 또는 내일 방향 적기. 비어있으면 다음 브리핑이 알림._

## 📋 오늘 후보 TODO

_step 5b가 자동 채움_

## 🤖 Cron activity

<!-- cron 실행 누적 기록 -->

## 💬 Telegram inbox

_polling이 자동 채움_
```

If today's entry **already exists** (re-run protection), skip creation and just send the Telegram brief based on existing entry.

### 4b. TODO surfacing (candidate items for today)
- Fetch the TODO data source (`collection://b3ee1d96-a1f8-4d9e-98cf-6e9c4ef35239`).
- Filter: `Status ∈ {Today, Backlog}` AND `Phase ∈ {<current phase>, <current phase + 1>}` (so prep work is visible).
- Rank: `Status=Today` first, then `Backlog`. Within each, sort by `Priority` (P0 → P3).
- Take top **5**. For each capture: short page id (first 8 chars), `Priority`, `Title`.
- If the TODO data source ID is still the literal placeholder `b3ee1d96-a1f8-4d9e-98cf-6e9c4ef35239` (not yet replaced by user), skip this entire step silently — emit `todo-surfacing: skipped (placeholder)` to stdout and proceed; do NOT fail.
- Update today's Daily Log entry: replace the `## 📋 오늘 후보 TODO\n\n_step 5b가 자동 채움_` placeholder with:
  ```
  ## 📋 오늘 후보 TODO

  - [P0] <short-id> <title>
  - [P1] <short-id> <title>
  - ...
  ```
  If the section is missing on a pre-existing entry, insert it just before the `## 🤖 Cron activity` header. If zero candidates, write `_없음 (TODO DB가 비었거나 현재 Phase에 후보 없음)_`.
- Hold this list in scope — step 5 embeds it into the Telegram message.

### 5. Send Telegram brief
Compose ONE message (Markdown formatting OK — Telegram supports it via `parse_mode=MarkdownV2` but escape carefully; or just use plain text for safety). Plain text format:

```
🌅 Daily Brief — YYYY-MM-DD (Phase X)

📋 사용자 지시:
<Today's Instructions + Telegram inbox 종합. 없으면 "없음 — 자율 진행">

🔧 현재 상태:
- 브랜치: <branch>
- 어제 이후 커밋: <N>개
- 미커밋: <N> files

📅 오늘 Phase: <P0/P1/...> — <phase 한 줄 설명>

📋 오늘 후보 TODOs:
- [P0] <short-id> <title>
- [P0] <short-id> <title>
- [P1] <short-id> <title>
- ...
(step 4b에서 모은 최대 5개. 후보 없거나 TODO DB 미설정이면 줄 통째로 생략)

📓 Notion: https://app.notion.com/p/<today entry page id>
```

Send via Bash:
```bash
source ~/.config/representation-aware-mppi/telegram.env
curl -s "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage" \
  --data-urlencode "chat_id=${TELEGRAM_CHAT_ID}" \
  --data-urlencode "text=<the message>" \
  --data-urlencode "disable_web_page_preview=true"
```

Verify response is `"ok":true`. If not, log the error.

### 6. Append a Cron activity entry to today's Notion entry
Per the spec in `_cron_log_snippet.md`, append:
```
- **HH:MM** `brief` · 오늘 entry <생성|이미 존재>, 지시 <N>건 surface, TODO 후보 <K>건 (Phase X)
```
to the `## 🤖 Cron activity` section of today's entry (create the section if missing — insert before `## 💬 Telegram inbox`).

### 7. Output a one-line summary to stdout (for cron log)
Final line of your stdout: `BRIEF_DONE date=YYYY-MM-DD phase=P0 instructions=<yes|no> todos=<K> entry_url=<url>`

## Constraints
- Korean for the Telegram message body (project language).
- Don't ask follow-up questions. This is non-interactive.
- If any step fails, send a Telegram error notification (`❌ Daily brief 실패: <reason>`) and exit non-zero.
- Don't modify CLAUDE.md, source code, or anything outside Notion + Telegram.

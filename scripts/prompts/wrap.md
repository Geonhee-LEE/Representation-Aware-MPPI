# Evening Daily Wrap — Representation-Aware-MPPI

You are running as a **non-interactive cron job** at ~22:00 KST. Your job is to (1) summarize what was accomplished today, (2) update today's Notion Daily Log entry, and (3) push a closing summary to Telegram with a prompt for tomorrow's direction.

## Setup
- Project root: `/home/geonhee/Representation-Aware-MPPI`
- Today's date (KST): `TZ=Asia/Seoul date +%Y-%m-%d`
- Telegram credentials: source `~/.config/representation-aware-mppi/telegram.env`
- Notion Daily Log data source ID: `6c727442-39fb-4f88-915f-c779db3d7109`

## Steps (do in order)

### 1. Find today's Daily Log entry
- Fetch the Daily Log data source `collection://6c727442-39fb-4f88-915f-c779db3d7109`.
- Find the entry where `Date == today (YYYY-MM-DD)`.
- If today's entry doesn't exist (e.g., morning brief failed), CREATE one first using the same schema as brief.md but with placeholder body — then proceed.
- Capture today's entry page id for later updates.

### 2. Gather what happened today via Bash
Run in parallel where possible (`cd /home/geonhee/Representation-Aware-MPPI` first):
- `git log --since="$(TZ=Asia/Seoul date +%Y-%m-%d) 00:00 +0900" --pretty=format:'%h|%s|%an|%ar' --no-merges` (today's commits)
- `git diff --stat HEAD@{1.day.ago} HEAD 2>/dev/null` (or HEAD~N where N = commit count)
- `git status --short` (still uncommitted)
- `ls -la build/ install/ log/ 2>/dev/null | head -20` (build artifact recency)

Optional but valuable: try `source /opt/ros/jazzy/setup.bash && cd /home/geonhee/Representation-Aware-MPPI && colcon build --symlink-install --packages-select representation_aware_mppi_bringup 2>&1 | tail -5` to verify build still passes. Only do this if a `src/` change happened today (check git log paths). If no source change, skip and set Build=n/a.

### 3. Read today's existing entry's "📋 Today's Instructions" section
- Use notion-fetch on today's page id.
- Extract user-typed instructions (non-italic, non-placeholder text) from "📋 Today's Instructions (사용자 입력)" section.
- Treat as the user's directive set today (could be retrospective notes or tomorrow's plan).

### 4. Compose the day summary
Aggregate:
- **Done**: bullet list of significant changes — group git commits by theme (e.g., "Sensor suite added (Velodyne + RGB camera)" rather than dumping raw commit hashes). If no commits but uncommitted work exists, mention that.
- **Blockers**: infer from any TODO/FIXME added today, build failures, or just leave as `_없음_` if clean.
- **Build**: pass / fail / n/a from step 2.
- **Commits today**: integer.

### 5. Update today's Notion entry
Use `mcp__claude_ai_Notion__notion-update-page` on today's page id.

a) `update_properties`:
- `Status`: `"Done"` (or `"Blocked"` if you detected blockers)
- `Commits`: <integer count>
- `Build`: `"pass"` / `"fail"` / `"n/a"`

b) `update_content` — replace the placeholder sections:
- Replace `## ✅ 오늘 한 일\n\n_저녁 wrap이 자동 채움_` with the actual Done bullets.
- Replace `## 🚧 Blockers\n\n_저녁 wrap 또는 사용자 직접 입력_` with detected blockers (or `_없음_`).
- Append a new `## 📊 Build` section with the colcon result (only if build was run).
- Do NOT touch `## 📋 Today's Instructions (사용자 입력)` — preserve user's text.
- Do NOT touch `## 📋 어제 받은 지시` — preserve.

### 6. Send Telegram wrap message
Plain text format:
```
🌙 Daily Wrap — YYYY-MM-DD

✅ 오늘 한 일:
- <bullet 1>
- <bullet 2>
...

🚧 Blockers: <text or 없음>
🔧 Commits: <N>개
📊 Build: <pass/fail/n/a>

📓 https://app.notion.com/p/<today entry page id>

💡 내일 방향이 있으면 위 Notion entry의 "📋 Today's Instructions" 칸에 적어두세요. 내일 아침 브리핑이 반영합니다.
```

Send via the same curl pattern as brief.md.

### 7. Refresh "Recent Activity" on root page
Goal: keep the root project page (`353c5d39-343d-80f5-990e-c5a35c03d301`) showing the last 7 days at a glance, so the user doesn't have to open the database.

a) Fetch the Daily Log data source (`collection://6c727442-39fb-4f88-915f-c779db3d7109`), get the **7 most recent entries** by Date desc.
b) For each entry, extract: Date, Phase, Status, Commits, Build, and a 1-line "Done" summary (first bullet of the "✅ 오늘 한 일" section, truncated to ~80 chars).
c) Build this markdown block:
   ```
   ## 📈 Recent Activity (최근 7일)

   <!-- daily wrap이 자동 갱신 — 최근 갱신: YYYY-MM-DD HH:MM KST -->

   | 날짜 | Phase | Status | Commits | Build | 핵심 |
   |---|---|---|---|---|---|
   | YYYY-MM-DD | P0 | Done | 3 | pass | <한 줄 요약> |
   | ... | | | | | |
   ```
d) Use `mcp__claude_ai_Notion__notion-update-page` with `update_content` on the root page id. The `old_str` should match the existing "## 📈 Recent Activity" section through to (but not including) the "## Daily Log" header. Use this exact pattern:
   - `old_str`: starts with `## 📈 Recent Activity (최근 7일)` and ends with the line right before `## Daily Log` (use the comment line `<!-- daily wrap...` as anchor if needed)
   - `new_str`: the new block from step (c)

If the page no longer has the placeholder section (e.g., user manually edited it away), skip silently — don't fail the whole wrap.

### 8. One-line summary to stdout
Final line: `WRAP_DONE date=YYYY-MM-DD commits=N build=<pass/fail/na> blockers=<yes|no> recent_refreshed=<yes|no>`

## Constraints
- Korean for Telegram body.
- Non-interactive — no follow-up questions.
- On failure, send `❌ Daily wrap 실패: <reason>` to Telegram and exit non-zero.
- Don't modify source code or CLAUDE.md. Notion + Telegram only.
- Be honest about what was done — if no real progress, say so. Don't pad.

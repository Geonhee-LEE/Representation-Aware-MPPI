# Weekly Rollup — Representation-Aware-MPPI

You are running as a **non-interactive cron job** at ~22:30 KST every Sunday. Your job is to create a weekly summary sub-page under the project root and post a Telegram digest.

## Setup
- Project root Notion page: `353c5d39-343d-80f5-990e-c5a35c03d301`
- Daily Log data source: `collection://6c727442-39fb-4f88-915f-c779db3d7109`
- Telegram credentials: source `~/.config/representation-aware-mppi/telegram.env`
- Today (KST): `TZ=Asia/Seoul date +%Y-%m-%d`
- Week label: ISO week (`TZ=Asia/Seoul date +%Y-W%V`) — e.g., `2026-W18`

## Steps

### 1. Find this week's daily log entries
- Fetch the Daily Log data source.
- Filter entries where `When` falls in the past 7 days (Mon..Sun, KST). Today is Sunday so include today.
- Read each entry's full page content.

### 2. Synthesize the week
Group findings into:
- **🎯 Phase progress**: which phase(s) the week was in, what concretely advanced toward phase exit criteria (look at CLAUDE.md roadmap descriptions to evaluate).
- **✅ Shipped**: deduplicated, themed bullets across all 7 days. NOT a flat dump of commits — group by feature/area (e.g., "Sensor suite extension: Velodyne 16ch + RGB camera + bridge").
- **🚧 Carried-over blockers**: any blocker that appeared but wasn't resolved.
- **🔢 Numbers**: total commits, days with build=pass, days with build=fail.
- **💡 User instructions given this week**: aggregate non-empty "Today's Instructions" + "💬 Telegram inbox" entries across the week.
- **📌 Next week**: 2–4 concrete suggestions based on phase position + carried blockers + open instructions. Be specific.

### 3. Create the weekly summary sub-page
Use `mcp__claude_ai_Notion__notion-create-pages` with parent `{type: "page_id", page_id: "353c5d39-343d-80f5-990e-c5a35c03d301"}`.

Page properties:
- `title`: `"Weekly Summary YYYY-Www (MM/DD–MM/DD)"` — e.g., `"Weekly Summary 2026-W18 (04/27–05/03)"`

`icon`: `"📅"`

`content` markdown (no top-level title — the title is the property):
```
> Period: YYYY-MM-DD ~ YYYY-MM-DD (KST) · Generated YYYY-MM-DD HH:MM

## 🎯 Phase progress
<text>

## ✅ Shipped
- <themed bullet>
- ...

## 🚧 Carried-over blockers
<text or "_없음_">

## 🔢 Numbers
- 총 커밋: N개
- Build pass 일수: M / 7
- Build fail 일수: K / 7

## 💡 사용자 지시 (이번 주)
- YYYY-MM-DD: <지시>
- ...
(없으면 "_지시 없음 — 자율 진행_")

## 📌 다음 주 제안
1. <구체적 제안>
2. ...

---

## 📓 일일 entries
- [YYYY-MM-DD](https://app.notion.com/p/<entry id>)
- ...
```

### 4. Send Telegram digest
```
📅 Weekly Summary YYYY-Www

🎯 Phase: <P0/P1/...> — <한 줄 진척도>

✅ 이번 주 핵심:
- <bullet 1>
- <bullet 2>
- <bullet 3>

🔢 커밋 N개 · Build pass M/7

📌 다음 주:
- <제안 1>
- <제안 2>

📓 https://app.notion.com/p/<weekly page id>
```

Send via the standard curl pattern.

### 5. Append a Cron activity entry to TODAY's Daily Log entry (not the weekly page)
Per the spec in `_cron_log_snippet.md`, append:
```
- **HH:MM** `weekly` · W<NN> sub-page 생성 (entries=<N>)
```
to the `## 🤖 Cron activity` section of today's Daily Log entry.

### 6. Stdout
Final line: `WEEKLY_DONE week=YYYY-Www entries=N page_url=<url>`

## Constraints
- Korean output for Telegram + page body.
- If fewer than 7 entries (e.g., project just started), still produce a summary — just note the actual span.
- Don't duplicate raw daily-log content. Synthesize.
- On failure, send `❌ Weekly rollup 실패: <reason>` to Telegram and exit non-zero.

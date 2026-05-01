# Cron activity logging — common snippet

This snippet is included by reference (or copy-pasted) into every cron-triggered prompt as the **final step** before stdout summary.

Goal: keep a visible audit trail of cron-triggered shell-script invocations directly in today's Notion Daily Log entry, so the user can see "what cron did today" at a glance without opening local logs.

## Step: Append to today's "🤖 Cron activity" section

1. Find today's Daily Log entry (Date == today). If you already fetched/created it earlier in this run, reuse the page id.
2. Read its current page content via `mcp__claude_ai_Notion__notion-fetch`.
3. Check whether the section `## 🤖 Cron activity` exists.
   - If **missing**: insert it just before the `## 💬 Telegram inbox` section header (or at end of page if inbox section also missing). Use `update_content` with old_str matching the inbox header (or last meaningful section header).
     New section template:
     ```
     ## 🤖 Cron activity

     <!-- cron 실행 누적 기록 -->
     ```
   - If **present**: just append a new line at the end of that section.
4. Append ONE line in this exact format (Korean, terse):
   ```
   - **HH:MM** `<script>` · <one-line outcome in Korean>
   ```
   - `HH:MM`: KST time of THIS cron run (use `TZ=Asia/Seoul date +%H:%M`).
   - `<script>`: one of `brief` / `wrap` / `weekly` / `inbox` / `urgent`.
   - `<outcome>`: ≤80 chars, what this run actually did. Examples:
     - `brief` → `오늘 entry 생성, 지시 1건 surface (P0)`
     - `brief` → `오늘 entry 이미 존재, 재발사 — 지시 없음`
     - `wrap` → `Status=Done, 커밋 2개, build pass, Recent Activity 갱신`
     - `weekly` → `W18 sub-page 생성 (entries=7)`
     - `inbox` → `메시지 2건 추가`
     - `urgent` → `[<session>] 완료 — <8 단어 요약>`

## Idempotency
Multiple cron runs can target this section on the same day. The append is naturally additive; no dedup needed (each line carries its own timestamp).

## Failure mode
If this final logging step fails (e.g., Notion API hiccup), DO NOT mark the whole script as failed — the actual work is already done. Just emit `cron-log: skipped (<reason>)` to stdout and continue.

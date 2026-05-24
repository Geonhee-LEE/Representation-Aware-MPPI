# Researcher Agent

The Researcher is one of four agents in the multi-agent automation (see
[`automation.md`](automation.md) §🤝 Multi-agent architecture). Its single
job: keep the project's external-research awareness fresh, so the hourly
Planner has a non-stale literature signal at the top of its REVIEW phase.

## What it does

Every 4 hours (`0 */4 * * *` KST), `scripts/researcher.sh` runs `claude -p`
with [`scripts/prompts/researcher.md`](../scripts/prompts/researcher.md). The
prompt walks 7 phases:

1. **Cheap dedup gate** — if `research/feed.md`'s top entry is < 23 h old,
   downgrade to `lite` mode (3 queries instead of 8) to avoid spam.
2. **Search** — picks N queries from a fixed pool (MPPI 2026, Nav2 MPPI,
   conditional flow matching for robotics, social-nav, BEV semseg for
   navigation, etc.), varying across cycles. `WebSearch` for breadth,
   `WebFetch` for at most 4 deep reads.
3. **Filter** — drops stale (>12 mo), duplicate, SEO-blog, paywalled hits.
4. **Append to `research/feed.md`** — prepend new entries, cap at 30 total
   (overflow flows to the monthly archive).
5. **Append to monthly archive** — `research/YYYY-MM/<seq>.md` is
   append-only, contains both keepers and drops with reason.
6. **Selective TODO creation** — at most 2 `[research]`-prefixed Backlog
   TODOs per cycle, hard cap 6 open total. Owner=claude only.
7. **Telegram digest** — silent on dry cycles; one notification-off message
   when ≥ 1 keeper lands.

## Where output lands

| Path | What |
|---|---|
| `research/feed.md` | Live 30-entry rolling feed, newest top. Read by Planner Phase 0. |
| `research/YYYY-MM/<seq>.md` | Per-cycle audit trail, includes filtered drops. |
| Notion TODO DB | `[research] <action>` Backlog items, Owner=claude. |
| `~/.local/share/representation-aware-mppi/logs/researcher-YYYY-MM-DD.log` | Full cycle log. |
| Today's Daily Log → `## 🤖 Cron activity` | One heartbeat line per cycle. |

## Manual feed

```bash
# Force a cycle now (e.g. after a noteworthy paper drops on arxiv)
bash scripts/researcher.sh

# Tail today's log
tail -f ~/.local/share/representation-aware-mppi/logs/researcher-$(date +%F).log

# Inspect the live feed
head -40 research/feed.md
```

## How to disable

- **Remove the cron line** for `researcher.sh` (the project's other agents
  keep running). Recommended if web budget becomes a concern.
- **Per finding**: drop a created `[research]` TODO straight to `Done` or
  delete it — Planner won't pick what isn't `Today`/`Backlog`.
- **Per PR**: the Researcher doesn't commit by itself, but if you let it
  open a `[auto] research/*` PR, removing the `safe-auto-merge` label
  stops Curator from auto-merging at the 48 h mark.

## Expected Telegram cadence

- **6 cycles/day** scheduled (00/04/08/12/16/20 KST).
- ~**2–3 messages/day** in steady state (most cycles produce 0 keepers,
  some produce 1–3).
- Notification OFF (`disable_notification=true`) — appears as silent
  bubble in chat, doesn't wake you.

Format:

```
🔬 Research feed +2
- Conditional Flow Matching for Visuomotor Policies [arxiv]
- ros-navigation/navigation2 PR: MPPI critic tuning [github]
📓 research/feed.md
```

## Prompt-bloat budget

`research/feed.md` is capped at **30 entries**, but the Planner only reads
**top 5** in Phase 0. This means feed growth never inflates the Planner's
context window — the cap on the feed is for human grep-ability + monthly
archive turnover, not for prompt cost. The cap on the Planner's read is
the actual bloat ceiling, and it doesn't move.

## Failure modes

| Symptom | Likely cause | Action |
|---|---|---|
| Telegram silent for > 1 day | every cycle hit 0 keepers (over-filtering) or `WebSearch` is down | check log; consider widening filter (b) duplicate threshold |
| `RESEARCHER_SKIP reason=no-network` repeatedly | network/firewall blocking outbound | check `curl -v https://api.openai.com` from cron user |
| `[research]` TODO backlog ≥ 6 | Planner not picking them | normal; Researcher self-caps creation at 6 open; Planner promotes when bottleneck matches |
| feed.md merge conflict | two cycles overlapped | flock should prevent; if not, last-writer-wins is fine — both archives keep the full record |

## Why this exists

Before the Researcher, the hourly Planner picked TODOs from a static
backlog seeded once (`scripts/seed_todos.tsv`). After 9 days the backlog
was the same one the user wrote on day 1, with zero refresh against new
arxiv drops or library releases. The Researcher closes that loop: 6
times a day, the literature signal gets re-injected as TODO candidates
the Planner can promote on the next hour's tick.

# Research Feed — Representation-Aware-MPPI

Output of the **Researcher** agent (`scripts/researcher.sh`, cron `0 */4 * * *`).
Single-source dump of MPPI / social-nav / flow-matching / mobile-robot literature
discovered between cycles — separate from `JOURNAL.md` (which is the Planner's
cycle log) so the two never fight for prompt budget.

## Files

| Path | Role | Writer | Reader |
|---|---|---|---|
| `feed.md` | Rolling top-30 feed, newest first. | Researcher (append at top, drop tail) | Planner Phase 0 (top 5), wrap (last 24h slice) |
| `YYYY-MM/<seq>.md` | Per-cycle archive (full hit list incl. dropped entries). | Researcher (append-only) | Manual / weekly rollup |

## Entry format (in `feed.md`)

```markdown
## YYYY-MM-DD HH:MM — <short title>
- **Source**: <URL>
- **Type**: arxiv | github | blog | benchmark | dataset
- **Why relevant**: <1–2 sentences tying to north star or current phase>
- **Suggested TODO**: <none | one-line action>
```

Newest entry on top of the file (after the `# Research Feed` header). Cap at
**30 entries**; older entries fall off the live feed but survive in
`YYYY-MM/<seq>.md`.

## Cadence

- 4-hourly cron (6 cycles / day).
- **Cheap dedup gate**: if the most-recent feed entry is < 23 h old, the
  Researcher runs a *lite* pass (3 search queries instead of 8) to avoid spam.
- Telegram digest only when ≥ 1 new entry actually lands.

## Manual operations

```bash
# One-shot manual run (e.g. when a new paper drops and you want it now)
bash scripts/researcher.sh

# Tail today's log
tail -f ~/.local/share/representation-aware-mppi/logs/researcher-$(date +%F).log

# Inspect the live feed
head -40 research/feed.md
```

## Disable

- **Per cycle**: comment out the cron line for `researcher.sh`.
- **Per finding**: remove the `safe-auto-merge` label from any `[auto] research/*`
  PR — Curator will then leave it for manual review.

## Why a separate file (not `JOURNAL.md`)

`JOURNAL.md` is the executor's cycle reflection log; mixing literature notes
into it would (a) blow the 20-entry cap with link spam and (b) defeat the
"REVIEW reads top 5" prompt-bloat ceiling. The Researcher writes here; the
Planner reads here (Phase 0) before consulting `JOURNAL.md`. One direction of
flow, no double-write.

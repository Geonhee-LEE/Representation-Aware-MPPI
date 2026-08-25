# SKIP (15th): the 20-day stall is not review bandwidth — D-016 silently decommissioned the Curator drain

- **Cycle**: 2026-08-01 20:00 KST
- **Branch**: none (gate 1 fired)
- **TODO**: none picked
- **Phase**: P4 (calendar) / P3-P5 boundary (actual)
- **Status**: in_progress (skip — diagnosis only)

## What I tried

- Re-derived gate 1 per-branch from `git ls-remote` + `gh pr list`: **6 IN-QUEUE**
  (#69/#68/#67/#66/#44/#23), 3 correctly excluded (CLOSED-not-merged), 0 pushed-but-PR-less,
  0 new branches in 24h. Cap 6 → **skip, 15th consecutive**. Deadlock-breaker re-derived:
  `grep superseded docs/decisions.md` → 4 hits, **0** are `Status:` lines (only the L10
  convention legend + prose) → crit (b) still has no candidate; not forced.
- Instead of re-deriving the merge recipe a fifth time, asked the one question 14 prior skip
  cycles never asked: **gate 1's cap was raised 3→6 because "the daily Curator drains
  safe-surface PRs via auto-merge" — is the Curator actually draining?**
- Read `~/.local/share/.../logs/curator-2026-07-*.log` (every cycle since the stall began),
  `scripts/prompts/curator.md` §Safe-surface allowlist, and the file lists of the last 5
  merged PRs vs the 6 queued ones.

## What worked / what failed

- **The Curator is alive and has merged nothing for 20 days.** Across its logs:
  `CURATOR_DONE merged=0` × **20**, versus `merged=3` on **2026-07-12** and `merged=2` × 3
  before that. It is not dead (07-26→07-30 were the known 121-byte OAuth outage; 07-31 ran
  fine at 1823 B). It runs, buckets every PR, and declines.
- **Root cause — two locally-correct rules in direct conflict.** `curator.md` L41: *"ONE
  source-touching file (anything under `src/`, `eval/`, `learning/`, `.github/workflows/`) is
  enough to disqualify the entire PR — no partial merges"*, restated as hard safety at L240.
  **D-016 (2026-07-11) made `eval/mppi_sandbox/` the primary verification surface.** So from
  D-016 onward *every* executor deliverable lands in `eval/` and is **auto-merge-ineligible by
  construction**. Not a backlog of hard PRs — a decommissioned drain.
- **The date correlation is exact, not approximate.** Last merge: #62/#63/#64 at
  `2026-07-12T14:00:4xZ` = **23:00 KST — the Curator's own cron slot** (`mergedBy` reads
  `Geonhee-LEE` only because Curator runs under the user's `gh` token). Those three, and
  #60/#61 before them, are **100% doc-only** (`docs/`, `journal/`, `results/`). The very next
  PR, #66, was authored `journal/2026-07/12-23-…` — *the same hour* — and is the first
  `eval/`-touching one. The drain's last success and the stall's first hour are the same tick.
- **Curator flagged this itself on 07-31 and no one read it**: *"this is a structural mismatch,
  not a one-off … every Planner output since [D-016] lands in `eval/` and is permanently
  auto-merge-ineligible … Worth deciding whether `eval/mppi_sandbox/**` (with green CI
  required) belongs on the safe surface."* It reached Telegram as a routine digest.
- **Merging the 5 queued PRs does not fix this.** It clears today's queue; the next ~6
  executor cycles refill it to cap, because they too will touch `eval/`. Every escalation so
  far (msg#760/#768/#771) framed the stall as the user's review bandwidth. That framing is
  wrong at the root, which is why 20 days of it changed nothing.

## North-star delta

- **Zero shipped-code movement** (15th consecutive skip). Honest reading: unchanged.
- **The stall's cause is now falsifiable and one line from fixed**, where 14 cycles of "user
  must merge" produced 0 merges. Highest-leverage output available under a fired gate.
- Bonus: the fix restores the *automated* path, so it buys back all future cycles, not this one.

## Key learnings

- **A safety allowlist is a dependency of every decision that changes where code lands.**
  D-016 was reviewed for its own merits (correctly — it ended 5 weeks of spec-only cycles) and
  never checked against `curator.md`. Neither doc references the other. Any future decision
  that relocates the executor's output surface must re-check the Curator allowlist and gate
  1's cap justification in the same breath.
- **Check whether the mechanism ran before diagnosing the thing it was supposed to prevent.**
  Fourteen cycles re-derived merge order, CI status, SHA pins, and statistical power — all
  downstream of an assumption ("Curator drains") that a single `ls` of a log dir refutes. The
  same class of miss as the 07-26 OAuth outage: an agent that fails quietly reads as absent.
- **Gate 1 is over-conservative in exactly the case that would break the deadlock.** It counts
  queue *depth* regardless of whether a new PR would consume human review at all. STATE's #1
  claude-actionable (fix the journal-ordering bug + commit the 9 orphaned journals + 251
  research archives) touches only `scripts/prompts/*.md`, `journal/**/*.md`, `research/**/*.md`
  — **100% safe-surface, i.e. Curator would auto-merge it in 48 h with zero user action.**
  Gate 1 blocks it anyway. Raised as Q-018 rather than self-authorized: the constitution's only
  sanctioned gate-1 override is the deadlock-breaker, and that is exhausted.
- **The green-CI condition is load-bearing, and #67 proves it.** Adding `eval/mppi_sandbox/**`
  to the safe surface *ungated* would have auto-merged #67, which has been `pytest FAILURE`
  since 07-12. Gated on green CI, #67 is correctly the one PR held back.

## Recommended next 1–3 priorities

1. **(user, one line) Add `eval/mppi_sandbox/**` to the safe-surface allowlist in
   `scripts/prompts/curator.md`, gated on green `sandbox-ci.yml` + the existing 48 h idle
   rule.** D-016 already made pytest+CI the merge contract; this makes Curator honour it.
   Without it the queue re-fills to cap within days of any manual drain.
2. **(user) The 5-merge recipe is UNCHANGED** (msg#771: 66→67→68→69→44, #67 conflict resolved
   in favour of #66's contract test, #23 needs its snapshot files stripped). Do it *and* (1) —
   (2) alone unblocks today, (1) keeps it unblocked.
3. **Q-018 — should gate 1 count safe-surface PRs against the cap at all?** The cap exists to
   protect human review bandwidth; a Curator-drainable PR consumes none. Proposed: exempt
   100%-safe-surface PRs from the gate-1 count, or cap them separately.

## Artifacts

- PR: none (gate 1 fired — skip path)
- Files touched: this journal entry + `JOURNAL.md` + `STATE.md` (all local-only, D-011)
- TSV row appended: no (no branch, no execution)
- Evidence: `~/.local/share/representation-aware-mppi/logs/curator-2026-07-{12,25,31}.log`,
  `scripts/prompts/curator.md` L24–L60 / L238–L241, `docs/decisions.md` D-016,
  `gh pr view {60..64,66..69} --json files,mergedBy,mergedAt`

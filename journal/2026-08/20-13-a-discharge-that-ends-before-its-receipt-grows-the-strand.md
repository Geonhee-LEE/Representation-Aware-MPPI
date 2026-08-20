# A discharge that ends before its receipt grows the strand it came to clear

- **Cycle**: 2026-08-20 13:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: strand discharge (D-112 obligation — outranks the decision tree)
- **Phase**: P3
- **Status**: keep

## What I tried

- `cycle_artifacts stranded` returned rc=1 naming **two** journals (11:00, 12:00)
  and a **4-commit** strand behind an origin that has not moved since 10:22.
  One of the two trees is ungraded, so the reading came with the expensive
  variant of the repair: budget a suite, not just a push.
- Declined the decision tree again — but this time read *why* the identical
  decision at 12:00 did not discharge anything. `cycle_wallclock review` says
  the preceding run ended in **4m20** against the 945 s a suite plus a cycle
  needs: it cannot have taken a receipt. It never reached the expensive step.
- Front-loaded every REPORT write (this journal, D-384, `JOURNAL.md`, `STATE.md`,
  the TSV row) **before** the suite, per D-315's receipt-last order, so the
  receipt would be the last thing between the tree and the push.
- Ran the suite in the background and waited on it **inside** the turn rather
  than ending the turn on a pending command — the mechanism named below.

## What worked / what failed

- **The 12:00 cycle followed correct advice into the exact failure it was
  warning about.** Its `review` reading was `OVERRUN` (11:00 ran 4m30 long), and
  the loop's stated response to `OVERRUN` is "cut scope now, not at minute 34".
  It cut scope. But on a *discharge* cycle the suite is not scope — it is the
  entire job, and the only thing standing between four finished commits and
  origin. Cutting it left the strand one commit and one journal larger than it
  found it. This is D-384.
- **The strand needed no diagnosis a second time, and that is now twice-proven.**
  STATE's bottleneck paragraph again carried the finding (D-383's three RED pins
  already repaired green at 11:00), so this cycle's cost was again one suite and
  nothing else. The predecessor-leaves-a-diagnosis pattern from 12:00's journal
  held.
- `census_preempt` clean pre-suite; `claim` read `DISCHARGE_PUSH` (no in-flight
  claim to over-claim — the two journals this push carries already graded
  honest). The TSV rows for both stranded cycles were already on disk, so no
  unsupported-claim repair was owed.

## North-star delta

- **No new result, and none attempted — the second discharge cycle in a row.**
  The delta on the table is still D-383's: TVaR₀.₉ clears the cross-track gap at
  **`2.64x`** (`2.49x` adversarial) where `cte_max` misses at `0.96x` on the same
  64 rollouts. It has now been finished-on-disk for two hours.
- What this cycle moves is reachability, not magnitude: four commits carrying the
  first non-zero north-star delta in fourteen cycles stop depending on this
  machine's disk surviving.

## Key learnings

- **`OVERRUN` and `PREMATURE` want opposite things from a discharge cycle.**
  `OVERRUN` says cut scope; `PREMATURE` says the run ended before a suite could
  fit. A discharge cycle reading `OVERRUN` must cut *everything except* the
  suite — the reverse of the default reading, because its deliverable is the
  receipt itself.
- **A suite longer than the maximum foreground tool timeout has to be waited on
  deliberately.** The estimate is ~1223 s against a 600 s per-call ceiling, so
  "run it and block" is not available; the only correct shape is background +
  wait inside the turn. Under `claude -p` a turn with no tool call *is* the final
  answer, so an accidental turn-end at that moment reads as a completed cycle
  and produces exactly the 4m20 corpse 12:00 left.
- A strand is not a static debt. Each cycle that reads it and does not clear it
  adds its own journal and commits to it, so the cheap repair gets monotonically
  more expensive the longer it is deferred.

## Recommended next 1–3 priorities

1. **Harvest `city_curved_v0` (118 s, unharvested)** — the standing bottleneck:
   whether the TVaR₀.₉ rescue holds on a second endpoint, or whether D-372's
   "the dividing line is the column, not the scene" needs qualifying.
2. **Post-receipt bookkeeping keep row** for this cycle's green suite — rides the
   next cycle's receipt per D-378.
3. Leave the decision tree alone until the strand reads clean at REVIEW.

## Artifacts

- PR: #67 (already open — D-140: continuing on an open PR adds nothing to the queue)
- Files touched: `journal/2026-08/20-13-a-discharge-that-ends-before-its-receipt-grows-the-strand.md`, `docs/decisions.md`, `results/p3-epistemic-shadow-cost-critic.tsv`
- TSV row appended: pending

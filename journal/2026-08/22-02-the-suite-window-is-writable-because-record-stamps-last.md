# The suite window is writable, because `record` stamps last

- **Cycle**: 2026-08-22 02:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: none — Phase 1 Step 0 fired and the strand outranked the decision tree
- **Phase**: P3
- **Status**: keep

## What I tried

- `cycle_artifacts stranded` returned rc=1 on entry: 01:00's journal
  (`22-01-the-coverage-set-named-one-of-two-ensembles.md`) never reached origin,
  with 2 commits (`975b87f`, `6c74550`) ahead. Its TSV row and claim line were
  already clean — the only missing thing was a receipt.
- `probe` said `UNMEASURED`, so I started the suite immediately as EXECUTE's
  first long-running step, per Step 0-bis's `PREMATURE` advice.
- Mid-run I hit the real problem: the suite takes ~22 min, so it would finish
  *after* this cycle's own REPORT writes were due — and D-315 says every
  mandated write must precede the receipt. Naively that is a guaranteed `STALE`.

## What worked / what failed

- **The dilemma was false, and `push_preflight.record`'s own docstring says so**:
  "The stamp is taken **after** the run rather than before, so the receipt
  describes the tree as it stood when the last assertion executed." The binding
  is `worktree_fingerprint`, computed at completion — not at launch.
- So the ~22 min a suite is running is not dead time for the writer. It is a
  **writable window**: any write that lands before the run ends is inside the
  receipt. D-315's "no write between the receipt and the push" is about the
  *receipt*, not about the *suite* — those are the same instant only if the
  suite is free, and it never is.
- `cycle_wallclock elapsed` read `SUITE_UNAFFORDABLE` at 11m35 with the deadline
  0m46 past. That was correct about a **second** suite and would have been wrong
  as advice to kill the first: the running one launched inside its window.
- I nearly killed and restarted it to get the writes ahead of the run. That
  would have paid 22 min for something the ordering already permitted, and it is
  the same shape as D-315's own cost — three cycles stranded before the *order*,
  not the care, was named as the cause.
- One receipt therefore covers both 01:00's stranded work and this cycle's
  report, in a single push. No second suite, no new strand.

## North-star delta

- **No metric moved** — this cycle bought no rollouts and touched no controller.
  Its output is that 01:00's derived `RECORDED_SCENES` (D-413) reaches origin
  and CI instead of sitting on disk for a third cycle.
- The bottleneck is unchanged: `cafe_convoy_v0` and `cafe_obstacle_crossing_v0`
  are eligible and unmeasured.

## Key learnings

- **A long-running gate has an interior.** Every ordering rule in this loop is
  written as if commands are points on a line; `record` is a 22-minute interval,
  and the D-315 table's "before the receipt" bucket is larger than it reads.
- **Read the tool before re-sequencing the cycle around it.** The answer was one
  `grep` into a docstring, and it cost less than a minute against the 22 the
  restart would have cost.
- `SUITE_UNAFFORDABLE` grades *starting* a suite, not *finishing* one already in
  flight. Advisory readings still need their population checked (D-318's shape).

## Recommended next 1–3 priorities

1. **`freeze-margin`** — one-line yaml edit declaring `min_distance_to_obstacle`
   on `cafe_freezing_v0`; safe now that D-413 derived the coverage set.
2. **`convoy-meas`** — per-seed clearance for `cafe_convoy_v0`, the larger of the
   two open cells.
3. **`typed-set-audit`** — sweep for the D-413 shape (`frozenset({...})` of
   imported names whose membership nothing derives).

## Artifacts
- PR: #67 (already open — D-140)
- Files touched: journal/2026-08/22-02-*.md, docs/decisions.md, results/p3-epistemic-shadow-cost-critic.tsv
- TSV row appended: yes

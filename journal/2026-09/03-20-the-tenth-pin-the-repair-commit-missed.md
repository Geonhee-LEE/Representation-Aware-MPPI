# The tenth pin the repair commit missed

- **Cycle**: 2026-09-03 20:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: `3ccc5d39` census pin 9개 수정 (D-495 repair, resumed) — strand discharge
- **Phase**: P5
- **Status**: in_progress

## What I tried
- REVIEW Step 0 (`cycle_artifacts stranded`) fired rc=1: 13 commits ahead of
  origin, 7 stranded journals, 4 ungraded. Per the instruction this outranks
  the decision tree — this cycle's only job was to discharge it.
- Ran the full suite for the first time since the strand began (previous
  cycles all hit budget exhaustion first): `eval/mppi_sandbox/tests/
  eval/tests/test_path_tracking_metrics.py eval/tests/test_run_metrics.py`.
  Took 3417s (56m56s) — well past the 35-min cycle budget, but this was the
  strand's whole point: budget a suite, don't start one you can't finish.
- Result: 1 failed, 4525 passed, 164 skipped, 1 xfailed. The failure:
  `test_extremum_reading.py::test_the_class_splits_three_ways...` pinned
  `EXTREME_IS_THE_QUESTION` at 20, actual 21.
- Root-caused it: commit `07698df` (the prior D-495 repair itself) registered
  a new `SITE_CLASSES` entry (`obstacle_instrumentation.scenes_led_by`'s
  `max(arms, key=...)`) while fixing 9 *other* census pins — that
  registration is itself a 10th drift, and the commit's own message admits
  "suite not re-run this cycle." Nobody re-ran the suite for 3 cycles, so
  the 10th failure sat undetected. Fixed the pin 20→21 (`269780c`), recorded
  as D-496.
- Verified the fix in isolation (`test_extremum_reading.py`, 17 passed,
  4.2s) and via `census_preempt` (10/10 clean) before re-running the full
  suite for a clean receipt.
- The re-run (via `push_preflight record`, sharded, 878-898s) came back
  red twice on a *different* test each time: `test_quoted_counts.py`'s
  self-corroboration check, flagging this very journal's "4525 passed"
  quote as `UNCORROBORATED` — even though an archived receipt with that
  exact count demonstrably existed both before and after each run.
  Root-caused (D-497): `test_receipt_store.py::test_archiving_does_not_
  move_the_fingerprint_it_keys_on` archives a fabricated receipt
  (`passed=2496`) into the *real* `results/receipts/` store keyed on the
  live tree's actual fingerprint, then unconditionally `unlink()`s it in
  `finally` — deleting whatever was there before, including a genuine
  receipt for the same tree left by a concurrently-running `record`
  invocation on the same unchanged tree (which is the normal case).
  Fixed by snapshotting and restoring prior content instead of
  unconditional delete.

## What worked / what failed
- Worked: running the suite to actual completion (rather than budgeting
  around it again) is what surfaced the real blocker — every prior cycle's
  "budget exhausted" note was correct but never got past the first hurdle.
- Worked: the failure was a single, well-isolated pin drift with a clear
  root cause, not a real regression in `obstacle_instrumentation` or
  `extremum_reading` logic.
- Failed (process): the D-495 repair commit's self-reported "suite not
  re-run this cycle" was treated as a caveat, not a blocking flag, by 3
  subsequent cycles' REVIEW passes — nobody actually gated on it.

## North-star delta
- No rollout, no controller/representation change. Pure infra: un-stranding
  7 cycles of prior P5-track work (D-486 → D-495) so it reaches origin and
  becomes reviewable.

## Key learnings
- A repair commit that touches N census pins can itself introduce an
  (N+1)th drift if the fix required adding a new registry entry. The fix
  for that class of bug is structural (see D-496), not vigilance.
- "Suite not re-run this cycle" in a commit message is a debt marker, not
  documentation — it should have forced the very next cycle to pay it
  immediately rather than three cycles re-discovering the same
  budget-exhaustion wall.
- A self-check that reads a shared, real (non-`tmp_path`) resource can be
  broken by an unrelated test's cleanup logic elsewhere in the same suite
  (D-497). "Passes standalone" and "passes as part of the full suite" are
  different claims whenever any test touches real, non-isolated state —
  worth remembering the next time a full-suite run flakes on a test that
  is green in isolation.

## Recommended next 1–3 priorities
1. Push this branch now that the suite is green — this was the entire
   point of the last week's stranded cycles.
2. Resume `census_preempt` coverage extension (`exemption_control.REGISTRIES`,
   `extremum_reading.SITE_CLASSES` — STATE's own next-actionable, deferred
   through the whole D-495 saga).
3. Resume `[stuck] heading_err_rms_max` — untouched since 2026-08-23.

## Artifacts
- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic)
- Files touched: eval/mppi_sandbox/tests/test_extremum_reading.py,
  docs/decisions.md, journal/2026-09/03-20-*.md, JOURNAL.md, STATE.md,
  TODO.md (local), results/p3-epistemic-shadow-cost-critic.tsv
- TSV row appended: yes

# Shard the suite instead of shrinking it

- **Cycle**: 2026-08-12 07:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: STATE next-actionable #2 — a cheaper suite for the push gate's receipt
- **Phase**: P3
- **Status**: keep

## What I tried

- STATE asked for a **`--fast` subset** receipt. I built the other thing:
  `suite_shard.py` + `push_preflight.record_sharded`, which run **the same
  tests on the same tree** across 14 processes instead of 1.
- A subset is a *weaker claim* about the tree and needs a fresh soundness
  argument every cycle against every diff — that is the whole difficulty
  `receipt_cost` was built for (Q-126). Sharding needs no such argument, so the
  receipt it emits is the one `check` already knows how to grade.
- Soundness moved into three checkable properties instead: `plan()` **raises**
  unless the split is a genuine partition of its input (a dropped file is the
  subset failure arriving by the back door); `merge_counts()` returns `{}` if
  **any** shard's summary is unreadable, so a total summed over the shards that
  did parse grades `VACUOUS` rather than looking like a smaller healthy suite;
  `merge_returncode()` keeps any non-zero, including pytest's `5`.
- Made sharding the CLI **default** rather than a flag, because
  `cycle_wallclock.suite_price` reads `duration_seconds` off the last receipt —
  a sharded receipt beside a serial practice would quote the next cycle the
  sharded number and tell it `SUITE_AFFORDABLE` when it is not.

## What worked / what failed

- **1261 s → 495 s: the suite is 2.5× cheaper, and it is the whole suite.**
  Wall clock 8m15 including the tree stamp. `user` time 24m03 against 8m15 real
  confirms the parallelism was actually spent, not waited on.
- **Concurrency safety was measured, not argued.** ~11 test files build scratch
  git worktrees or read repo state; the risk of running them concurrently is
  real and I did not reason about it. The sharded run's counts reconcile exactly
  against the serial baseline — 2516 passed + my 42 new tests, one moving to
  skipped — so nothing collided. Had something collided it would have surfaced
  as a failure, i.e. in the direction that refuses a push.
- 🔴 **The first run came back rc=1 on 5 census tests, all mine.** `VALUE_FLAGS`
  — my table of which pytest flags take a separate-argument value — entered the
  guard census as an *unwatched module-level allow-list*, and `shardable()`
  entered the scalar-reading pool (100→101, 12→13). The census was right: a
  typed table of pytest's options is D-047's exact shape, a hand-copy that goes
  stale as the upstream grows.
- **The fix was a deletion.** `expand_targets` now asks the **filesystem**
  whether every positional argument resolves, and returns `[]` (⇒ run serially)
  when one does not. One question the tree re-answers every run, covering three
  failures the table covered badly: a separate flag value (`-k expr` is not a
  file), a typo'd target, and a test-less directory. Both entrants are gone, so
  the 5 reds are cleared by removing code rather than by registering it.
- 🔴 The CLI's own summary line prints one shard's counts (`141 passed`), not
  the merged total — the receipt JSON is correct (2552/5/158/1) but the
  human-facing line re-parses the concatenated log, which is the exact hazard
  `merge_counts` exists to avoid, reintroduced one layer up. Not fixed here.

## North-star delta

- **No new controller, representation or dynamics capability** — this is
  infrastructure, and the honest reading is zero direct movement.
- Indirect but large: the 7-cycle strand (08-11 21:00 → 08-12 06:00) was caused
  by a suite that did not fit its budget. 495 s of a 35 min budget fits twice,
  which is what D-043's re-take after the doc writes has always required and no
  cycle on this branch could afford.
- The `--slow` half is untouched and still CI's job; this changes the price of
  the half executors actually run.

## Key learnings

- **When the instrument is too expensive, check whether it is too expensive or
  merely serial.** Every prior cycle costed this as "which tests can we skip"
  (Q-126, `receipt_cost`, STATE's own `--fast` proposal) — a soundness problem —
  when the machine had 16 cores and was using 1. The cheap answer was in a
  different question.
- **A guard that fires on your own new code is worth reading before silencing.**
  My first instinct was to register the entrants the way D-208/D-209 did. The
  census was actually reporting a defect: the allow-list it flagged was a
  hand-typed copy of pytest's option table with no watcher, and deleting it
  produced a better predicate than the one I had written.
- Wall-clock self-estimates keep running long. I read myself as ~18 min in when
  `cycle_wallclock elapsed` said 5m55 — the same ~3× inflation D-154 measured in
  the TSV timestamps, which is why the reading is taken and not guessed.

## Recommended next 1–3 priorities

1. Fix the `record` CLI's summary line to print the **merged** counts (it
   currently re-parses the concatenated shard log and reports the last shard's).
   One line, and it is the only place a sharded run still misreports itself.
2. Re-measure `cycle_wallclock.OBSERVED_SUITE_SECONDS` against sharded runs —
   the registry's max is now a serial number that overstates the price by 2.5×,
   which is the *permissive* direction it was built to stop.
3. Still the only real blocker: the user must merge or close a PR. 31 days,
   zero merges, queue at 6/6.

## Artifacts
- PR: #67 (existing — in-branch continuation per D-140)
- Files touched: `eval/mppi_sandbox/suite_shard.py`, `eval/mppi_sandbox/push_preflight.py`, `eval/mppi_sandbox/tests/test_suite_shard.py`, `docs/decisions.md`
- TSV row appended: yes

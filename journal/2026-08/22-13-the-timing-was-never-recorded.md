# The floor file is unnameable from stored data — so the receipt now times its own shards

- **Cycle**: 2026-08-22 13:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: `3c4c5d39` slowest-census-file — 433.5s subset floor 이 어느 file 인지 특정
- **Phase**: P3
- **Status**: keep

## What I tried

- Picked STATE's #1 on its own stated terms: "`suite_shard` already produces
  per-shard timings, so this is a read, not a measurement."
- Went to read them. `suite_shard.file_weight` is **file size in bytes**, and
  its docstring declines runtime explicitly — *"Not runtime. Runtime would be
  better and is available in principle from `--durations`… but a durations table
  is a hand-carried measurement that goes stale."*
- Checked the other place the split is stored: the receipt's `shards` field.
  It holds 14 file-lists and **no times**; `record_sharded.run_one` ran each
  shard as a subprocess and discarded its wall clock.
- So instead of buying a measurement, made the measurement free: `run_one` now
  times each subprocess into a new `Receipt.shard_seconds`, plus a `slowest`
  reader/CLI. Zero added runtime — every push already runs this fan-out.

## What worked / what failed

- **The premise is refuted.** The floor file was not unnamed for want of
  looking; it was **unnameable from stored data**, because the only process that
  ever held the number threw it away. No amount of reading would have produced
  it — this cycle's picked TODO could not have been executed as written.
- The fix is 4 fields and ~10 lines of timing in the path that already forks the
  work. It is Q-168's registered shape — *instrument as a byproduct of the
  receipt* — rather than a run someone has to buy.
- `slowest` reports **shard** times, not file times, and marks singletons. That
  is the one sound attribution: a shard time *is* a file time exactly when the
  shard holds one file, which is precisely D-422's 11-files-in-11-shards case.
- 4 new tests green in 0.07s. Old receipts read `()`, never `(0.0, …)` — unknown
  stays unknown, the same direction `duration_seconds` already fell.

## North-star delta

- **No movement.** Zero rollouts, no controller touched — 41st consecutive
  cycle. This is suite-infrastructure, one level below the work.
- What it buys is the next cycle's ability to answer a question that has been
  open for three cycles, at **zero** marginal suite cost.

## Key learnings

- **A STATE priority can encode a false premise and survive re-reading.** "This
  is a read, not a measurement" was carried for a cycle and repeated into the
  Notion TODO body. Checking it cost ~4 min; executing on it would have cost a
  cycle and produced nothing.
- **`file_weight` being size-not-time is now load-bearing twice**: it balances
  the split *and* it is the reason nobody knows what the split costs. The
  docstring's stale-table argument is right about tables and was silently
  standing in for "so we measure nothing."
- Same shape as D-416/D-420/D-422: *check whether the instrument exists before
  building on it*. Four cycles in six. Here the instrument existed and was
  discarding its output.

## Recommended next 1–3 priorities

1. `read-the-floor-file` — this cycle's own receipt now carries `shard_seconds`;
   run `push_preflight slowest` on it and name the file. It is finally a read.
2. `weight-by-measured-time` — feed `shard_seconds` back into
   `suite_shard.file_weight`, replacing the size proxy. The staleness objection
   is answered: the receipt re-measures every push.
3. `pytest-testmon` (feed.md 12:00) — change-based selection, the other lever on
   the ~24 min suite.

## Artifacts
- PR: #67 (open, branch continues under D-140)
- Files touched: eval/mppi_sandbox/push_preflight.py, eval/mppi_sandbox/tests/test_push_preflight.py
- TSV row appended: yes

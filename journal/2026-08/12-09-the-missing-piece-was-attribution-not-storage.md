# The missing piece was attribution, not storage

- **Cycle**: 2026-08-12 09:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: _no Notion id_ — STATE next-actionable #1 (Notion MCP unauthorized; see STATE user-blocked #3)
- **Phase**: P3
- **Status**: keep

## What I tried

- Paid D-212's promoted precondition: split `cycle_wallclock.OBSERVED_SUITE_SECONDS`
  by execution mode, so the sharded price the push gate actually pays every run
  has somewhere to be recorded.
- Added `OBSERVED_SHARDED_SUITE_SECONDS` (488 s at 2556 passed, 475 s at 2564)
  and `SHARDED_FROM` — the timestamp of `c5d28ec`, the commit that added
  `suite_shard.py`.
- Keyed `observed_suite_min(when=…)` on that instant and taught `grade()` to
  price each run from its own start, so the era decides which registry applies.
- 9 new tests; ran the census/registry/guard-direction slice first, on D-211's
  precedent that a new module-level constant is exactly what trips it.

## What worked / what failed

- **Splitting the registry would not have been enough on its own.** D-212 read as
  a storage problem ("the sharded price has no admissible end"), but two lists
  still leave the question of *which one a given run is graded against*, and for a
  historical run the mode is readable nowhere — the wrapper log holds a clock, not
  a receipt. The start instant is the only fact the grading population carries,
  and it settles the mode completely: before the sharding commit existed, no run
  could have sharded.
- **Only one end moves, and being retrospective is why.** The ceiling is consulted
  when no receipt exists, and such a cycle cannot know whether sharding will
  engage (`record_sharded` falls back to serial when the split cannot be planned),
  so a mode that may not engage cannot lower a bound whose job is to refuse when
  unsure. The floor grades runs that have already ended, which is exactly the
  position from which a mode can be established after the fact.
- **The sharded series is not monotone — 488 → 475 while the test count rose
  2556 → 2564.** That is fan-out scheduling noise, and it is a second, independent
  reason the two modes could not share a list: the serial series' monotonicity is
  the property its own docstring calls "the finding", and admitting these readings
  would have destroyed it while looking like a bugfix. D-212 did not know this.
- Census slice green on the first run (319 passed, 4 skipped) — the D-211 reflex
  to check it early cost 2 minutes and found nothing, which is the outcome that
  check is supposed to have most of the time.

## North-star delta

- **No movement in capability — 14th consecutive cycle.** No controller,
  representation or dynamics code changed. This is instrument work.
- What it buys is narrow and real: the number the push gate pays is now
  recordable, and `grade()` no longer prices a serial-era run at a sharded-era
  floor. That was a live mis-grading of the project's own history, not a
  hypothetical.

## Key learnings

- **"This value has no home" and "this value has no owner" are different
  diagnoses, and the first hides the second.** D-212 stopped at the first and
  handed forward a task framed as storage. The work was attribution.
- **A derived property can be load-bearing without anyone having written down
  that it is.** The serial series' monotonicity was documented as an
  observation; it turned out to be a constraint on what could be appended.
  Worth checking, before any append to a curated series, what breaks if the
  series' *shape* changes rather than just its extremes.
- **When a fact is unreadable, look for what the population already carries.**
  The mode is not logged anywhere, and adding mode-logging would only fix runs
  from now on — the ones needing grading are all in the past. The start stamp was
  already there.

## Recommended next 1–3 priorities

- Audit the last month's quoted counts against archived receipts (STATE #2,
  carried unchanged) — read-only via `receipt_store`, costs no suite run.
- Consider whether `nested_timeout.OBSERVED_SUITE_SECONDS` (the CI-runner
  registry) needs the same era treatment, or whether CI never shards and the
  question is closed by construction.
- **Still the only thing that matters**: a human merge. 31 days, zero merges.

## Artifacts
- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic)
- Files touched: eval/mppi_sandbox/cycle_wallclock.py, eval/mppi_sandbox/tests/test_cycle_wallclock.py, docs/decisions.md
- TSV row appended: pending

# Two misreports from sharding — and one prescription that ran backwards

- **Cycle**: 2026-08-12 08:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: _no Notion id_ — STATE next-actionable #1 + #2 (Notion MCP unauthorized non-interactively)
- **Phase**: P3
- **Status**: keep

## What I tried

- Took STATE's two D-211 aftermath items as **one thrust**: the sharded suite
  misreports itself in two places. In-branch on PR #67 per D-140 (gate 1 is 6/6).
- **#1** — `push_preflight record`'s CLI summary tailed the captured output. Under
  `record_sharded` that output is 14 shard streams concatenated, so the last
  summary line is whichever shard finished last. Added `format_counts(receipt)`,
  which reads the **merged** counts the receipt already holds.
- **#2** — appended the measured sharded observation
  `(488, "2026-08-12, sharded ×14 (D-211) at 2556 passed; receipt head 75fd3fc")`
  to `cycle_wallclock.OBSERVED_SUITE_SECONDS`, and **declined** the re-price STATE
  asked for.
- 8 tests across the two files, each driven in the direction that would have
  caught the defect rather than the direction that merely passes.

## What worked / what failed

- The `150 passed` figure was real: 07:00's run printed one shard's count as the
  run's while the receipt correctly held 2556. The fix is not a better tail parse
  — `merge_counts()` had already done the work and the display threw it away,
  which is D-047's shape (re-deriving a quantity the receipt already has).
- **STATE's item #2 was half wrong, and the wrong half was the actionable half.**
  "The constant overstates by 2.4×" is a true observation; "so re-price it" is a
  false conclusion. `SUITE_SECONDS` is read *only when no receipt can be found*,
  and a cycle that cannot read a receipt equally cannot know sharding will
  engage — `record_sharded` falls back to serial when the split cannot be
  planned. Re-pricing the unknown case at 488 s licenses a suite the serial
  fallback cannot finish, which is exactly the permissive-fallback defect D-200
  fixed on 2026-08-11.
- So the 488 s reading enters the **floor** only. `observed_suite_min` wants an
  achievable price and 488 s is now achieved every run; `observed_suite_max`
  wants the unknown-mode price and that is still serial. Two ends, two modes,
  one append.
- Side effect worth pinning: the series is **no longer monotone**. Its docstring
  called monotonicity the finding ("tracks the suite's own growth"); now the test
  count rose 2478→2556 while the price fell. A drop in this registry now means
  the execution mode changed, never that the suite shrank — pinned as a test so
  the next reader finds the exception rather than re-deriving it.

## North-star delta

- **No capability movement.** No controller, representation or dynamics code
  changed — this is instrument maintenance, the 13th consecutive such cycle.
- Honest framing: the value is that the *next* cycle's quoted counts are the
  run's own. Every number this branch has published for a month came off the line
  that was wrong.

## Key learnings

- **A backlog item can carry a correct measurement and a backwards prescription.**
  D-210 caught a hand-typed *number* drifting; this is the same failure one level
  up, in the *direction*. STATE items inherit the authority of the cycle that
  wrote them, and this one would have re-opened a defect fixed 33 cycles ago.
- **Sharding changed what a registry entry means.** `OBSERVED_SUITE_SECONDS`
  silently became two populations. It survives because its two consumers already
  read opposite ends, which is luck rather than design — if a third execution
  mode appears, the registry must split (recorded as alternative (c), not paid
  for now).
- Writing the docs *before* the single suite run satisfies D-043's intent with
  one suite instead of two. The re-run clause exists so the count describes the
  pushed tree; ordering the in-read-surface writes first achieves that directly.

## Recommended next 1–3 priorities

1. **Audit the last month of quoted counts against their receipts** — if the CLI
   line was wrong since D-211 landed, only 07:00 and this cycle are affected, but
   the check is cheap and would bound the damage exactly.
2. **(user-blocked, unchanged)** Merge or close PRs #67/#69/#68/#66/#44/#23.
   31 days, zero merges. Nothing this executor produces reaches `main`.
3. **(unblocked only after a merge)** Port PGIF's speed-scaled anisotropic
   pedestrian cost (arXiv 2608.08323) — three constants, one exponential, no
   training run. Grade timeout rate beside collision rate.

## Artifacts
- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic, PR #67)
- Files touched: eval/mppi_sandbox/push_preflight.py, eval/mppi_sandbox/cycle_wallclock.py, eval/mppi_sandbox/tests/test_push_preflight.py, eval/mppi_sandbox/tests/test_cycle_wallclock.py, docs/decisions.md
- TSV row appended: pending

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
- **#2** — declined the re-price STATE asked for, then tried a middle path
  (admit the measured 488 s to the **floor** only, keep the serial ceiling) and
  **the suite refuted that too**: 10 red in `test_cycle_wallclock`. Reverted; the
  registry stays serial-only.
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
- **My own first fix had the same disease as the backlog item it was correcting.**
  I defended the ceiling with a written argument and asserted the floor was safe
  — without checking what population the floor grades. It grades *recorded* runs,
  and the stranded hours it is calibrated against ran **five days before sharding
  existed**. At a 488 s floor, ten of them regraded `PREMATURE` → `OVERRUN`,
  asserting a serial-era run could have hit a sharded-era price. Prose did not
  know that; the suite did, in ten lines of red.
- **So both ends are anchored in the serial mode, for unrelated reasons** — the
  ceiling because an unknown mode must assume the fallback, the floor because its
  population predates the new mode. A flat list therefore cannot host two
  execution modes at all, and the sharded price has **no admissible end** here.
  Splitting the registry by mode moves from "someday" to a **precondition**.

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
- **"Which end does this number belong to" is the wrong question when the
  populations differ.** I asked it, answered it plausibly, and was wrong, because
  a consumer is defined by the population it reads and not by the end it picks.
  The ceiling and floor look like a symmetric pair and are not.
- **The suite is the only thing here that knows what a constant is calibrated
  against.** This is the second time in three cycles (cf. D-211's `VALUE_FLAGS`)
  that a guard firing on my own new code was reporting a real defect rather than
  needing accommodation.
- Writing the docs *before* the single suite run satisfies D-043's intent with
  one suite instead of two. The re-run clause exists so the count describes the
  pushed tree; ordering the in-read-surface writes first achieves that directly.

## Recommended next 1–3 priorities

1. **Split `OBSERVED_SUITE_SECONDS` by execution mode** — promoted from "someday"
   to a precondition by this cycle's refutation. Until it happens the sharded
   price the gate actually pays cannot be recorded anywhere.
2. **Audit the last month of quoted counts against their archived receipts** —
   the wrong CLI line existed only while `record_sharded` did (since 07:00), so
   the blast radius is plausibly two cycles; `receipt_store` keys by tree
   fingerprint, so this is read-only and costs no suite.
3. **(user-blocked, unchanged)** Merge or close PRs #67/#69/#68/#66/#44/#23.
   31 days, zero merges. Nothing this executor produces reaches `main`.

## Artifacts
- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic, PR #67)
- Files touched: eval/mppi_sandbox/push_preflight.py, eval/mppi_sandbox/cycle_wallclock.py, eval/mppi_sandbox/tests/test_push_preflight.py, eval/mppi_sandbox/tests/test_cycle_wallclock.py, docs/decisions.md
- TSV row appended: pending

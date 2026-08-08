# The generator reproduces its own table

- **Cycle**: 2026-08-08 18:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: STATE #1 — Q-119: regenerate one scene's row with `--w-obs-soft 10` and diff it against the shipped row
- **Phase**: P5
- **Status**: keep

## What I tried

- Walked `cafe_head_on_v0` through D-138's brand-new `--w-obs-soft` path at the
  weight the shipped table was already generated at (`w_obs_soft = 10`, the
  `MPPIParams` default): 2 arms × 8 rungs × 8 seeds = 128 runs, into
  `eval/scenarios/variants/lam_windows_w10.yaml`.
- Chose a **regeneration** rather than a new cell deliberately — the shipped row
  is the known answer, so this prices the generator instead of adding a
  measurement nobody can check.
- Shipped `test_lam_window_regeneration.py` (11 tests) reading the committed
  artifact, so CI pays no sim time.

## What worked / what failed

- 🟢 **The regeneration is exact on both arms.** stock `[0.2, 0.4, 0.8]`
  `min_spread=1.04`, risk `[0.2, 0.4, 0.8]` `min_spread=1.05` — identical to the
  shipped rows down to the second decimal of the spread. Threading `w_obs_soft`
  through `ab.lam_ladder` into `MPPIParams` is behaviour-preserving at the
  default, which is the only weight where a prior answer existed to check it.
- 🟢 **The repo now has a table `lookup` can actually return a window from.**
  Every call in the project has graded `UNKEYED` since D-134 shipped the reader;
  this artifact grades `ON_KEY` at `w = 10` with `usable == (0.2, 0.4, 0.8)`.
  D-138 made `ON_KEY` *reachable*; this is the first time anything reaches it
  from a measurement rather than from a `tmp_path` fixture.
- 🟡 **It buys exactly one scene at exactly one weight, and the tests say so.**
  `lookup` still returns `NO_CELL` for crossing and `OFF_KEY` at 30/100/150 off
  this file, and the shipped table is asserted to be **still `UNKEYED`** — a
  keyed variant is not a keyed matrix, and stamping the other seven cells from
  this one would be D-107's unearned provenance.
- 🟡 **The check is set equality, not containment** (D-135's reason): a window
  that agreed only by widening would say nothing about whether the boundary
  moved. A second test pins the literal `(0.2, 0.4, 0.8)` so a *joint* drift —
  both tables regenerating wrongly in the same direction — cannot pass by
  comparing one to the other.

## North-star delta

- No new dynamics. The headline stays where D-136 left it (`unsafe_rate`
  0.0000 / `min_clearance` 0.3579 / `success_rate` 1.0000 over 5 cells).
- The movement is in what the re-keying path costs: it was ~500 unaudited runs
  against an untested generator, and it is now ~500 runs against a generator
  that has reproduced a known answer. The remaining seven scenes are arithmetic,
  not risk.

## Key learnings

- **Validate a new writer against the one input whose output is already
  recorded.** D-138 could only test the round trip on synthetic cells because
  the measuring half was the part it changed; the cheap completion of that proof
  is re-walking the one cell whose answer predates the change.
- **A regeneration is a stronger test than a fresh measurement** when a prior
  reading exists — a fresh cell at a new weight can only be believed, while this
  one could have been refuted.
- **Being keyed is per-file, and the refusals must survive the good news.** The
  temptation after a clean regeneration is to stamp the shipped table; the test
  that fails on exactly that is the one worth having.

## Recommended next 1–3 priorities

1. **Regenerate the remaining scenes at `w = 10`** into the same variant file
   (~6 scenes × 2 arms, ~400 runs, chunked across cycles) — now that the
   generator is priced, this is the mechanical path from `UNKEYED` to a keyed
   matrix, and each scene is independently checkable against its shipped row.
2. **Give `SEPARATED` a resolution floor (Q-115)** — still open; every rung of
   D-136's ladder graded `SEPARATED` including λ = 1.6 where both arms are out
   of band.
3. **A third scene in the `REMEASURED` registry** at `w = 100` or `w = 150`,
   never a fresh weight, so it adds a contrast rather than only a census row.

## Artifacts

- PR: #67 (already open — continuing on it adds no review bandwidth; gate 1 at cap, see D-140)
- Files touched: `eval/scenarios/variants/lam_windows_w10.yaml`, `eval/mppi_sandbox/tests/test_lam_window_regeneration.py`, `docs/decisions.md`, `docs/deliberations.md`
- TSV row appended: yes

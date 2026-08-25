# The vacuity check had a floor under it — an empty world reads 2.73%

- **Cycle**: 2026-08-04 10:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: STATE #1 — finish the one-sided-verdict sweep: the epistemic-reach screens
- **Phase**: P3
- **Status**: keep

## What I tried

- Took the last named suspect from the STATE #1 thread that produced D-055 and
  D-056, and read each of `reach.ReachProfile`'s three verdicts against **the
  value it takes at rest** — the shape both prior cycles turned on.
- `audible` (`live_steps > 0`): tested the obvious confound — `bev.sample`
  returns `unobserved_value = 1.0` for fan points outside the grid, so a fan
  straddling the boundary could produce spread with no rendered shadow at all.
- `grid_unseen`: rendered a `GTBevProducer([])` — literally zero obstacles —
  and read the fraction its own vacuity check thresholds.
- `scalar_false_positives`: computed both per-step set differences across the
  8-scene matrix, rather than the difference of aggregates the field shipped.

## What worked / what failed

- 🔴 **The vacuity check could not fail for the reason it was asked.** An
  obstacle-free world reads **112/4096 = 2.73%** of cells at σ = 1.0. The grid
  is a square of half-extent `n·res/2 = 4.00 m`; sensing is a disc of radius
  `5.00 m`; the corners reach `5.66 m` and are unobservable in *every* render,
  forever. So `unseen.min() > 0.0` in `test_epistemic_reach_gate.py` — an
  assertion whose entire stated job is "the scene stopped casting shadows,
  which would make the signal-free finding vacuous" — **passes on a world with
  nothing in it**. The two `> 0.05` bars were stated over the same unsubtracted
  floor, so what they demanded of the scene was `0.023`.
- 🔴 **The deaf class was never one class.** All three deaf scenes'
  `grid_unseen` is **entirely floor** (`scene_unseen == 0`). On the nominal
  driver, "deaf because rendered-but-out-of-reach" — D-021's actual finding —
  has **zero** instances; that case exists only on the measured driver. The
  screen's headline partition was answering a coarser question than its
  docstring claimed.
- 🔴 **The mechanism was already written down, one docstring away.**
  `test_matrix_partitions_into_audible_and_deaf` says obstacle-free scenes'
  "only σ > 0 cells are the beyond-sensing-range grid corners" — while two
  vacuity assertions in the same package thresholded that exact quantity
  without subtracting it. Third cycle running where the contradiction was
  already in the tree and no bar snagged on it (D-055, D-056).
- ✅ **The `audible` confound is refuted by measurement, not argument.** The
  out-of-grid prior contributes spread on **0 of 8** scenes — the fan never
  leaves the grid at the shipped horizon. Recording a refuted hypothesis rather
  than quietly dropping it.
- 🔴 **`scalar_false_positives` was a difference of aggregates.**
  `max(0, scalar_live_steps - live_steps)` equals the per-step set difference
  only under nesting, which the field's own docstring conceded "need not" hold
  while `max(0, ...)` floored the case where it didn't. Measured both
  directions: `spread_only_steps` is **0 on all 8 scenes**, so the sets do nest
  and the published numbers stand — **they were right by coincidence**, and the
  coincidence now has a test instead of holding the quantity's place (D-046).
- ✅ **A second live instance found and priced, not fixed** (Q-071).
  `observation_value.py` already filters `d_robot <= r_sense` — immune, and
  evidence someone knew. `weight_units.py:336` does not, and its
  `raise ValueError("no shadow cells in this BEV")` guard **can never fire**.
  Left alone deliberately: there the selected cells *are* the input, so fixing
  it moves numbers, and the contamination is unmeasured.
- ✅ The floor is **derived by rendering an empty world**, not typed — a
  `32 × 0.125` grid fits inside its disc and correctly reads `0.0`. D-047's
  lesson applied without being asked.

## North-star delta

- **No avoidance or tracking number moved — twenty-fifth consecutive instrument
  cycle.** Scenes able to contribute an avoidance number: 5, reportable: 4 —
  unchanged.
- What moved is the **meaning of a partition that was already being reported**:
  3 of 8 scenes were classified "deaf" by a screen whose vacuity check was
  incapable of separating the two reasons for it. The 5 audible scenes are
  unaffected — their `scene_unseen` clears the floor by 7–22 points.
- No published magnitude is retracted. Unlike D-055 this is a **correction to a
  verdict, not to a measurement**; the numbers were right, the reasons were not
  checkable.

## Key learnings

- **Ask what a bar reads in a world with nothing in it.** D-055/D-056 asked
  "what does this read *before the act*"; the same question for a screen is
  "what does this read for an *empty scene*". Both are the empty case of the
  population, and both times the bar had never been evaluated there — because
  every scene anyone thought to check had obstacles in it.
- **A floor is a property of the instrument, and instruments have geometry.**
  Nothing about `grid_unseen` was wrong as an arithmetic; it was wrong as an
  *attribution*. A square grid over a circular sensor produces a constant that
  no scene can change, and any cross-scene comparison inherits it.
- **When a guard clause names its own trigger, check the trigger can occur.**
  `unseen.min() > 0.0` and `weight_units`' `ValueError` are the same defect in
  two syntactic dresses. This is a grep-able shape for a future cycle.
- **Record refuted hypotheses.** The out-of-grid confound was the more obvious
  defect and it is simply not there. Two cycles from now that measurement is
  what stops someone re-deriving it.

## Recommended next 1–3 priorities

1. **Q-071: measure `weight_units._shadow_trajectory`'s corner contamination**
   — the second live instance, already located. Per-scene fraction of selected
   cells with `d_robot > r_sense`; zero means (a) is a free cleanup, positive
   means it is a recalibration bill. Static, no sim.
2. **Grep the package for guard clauses whose trigger cannot occur** —
   generalising by shape has now paid three cycles running (D-055 → D-056 →
   D-057), each finding a sharper instance than the one before.
3. **Q-070: count the guards whose before-reading is non-empty in the enriched
   fixture** — carried unchanged from last cycle, still 2–3 readings.

## Artifacts
- PR: #67 (open, 52nd consecutive cycle writing into it — no new review bandwidth)
- Files touched: `eval/mppi_sandbox/reach.py`,
  `eval/mppi_sandbox/tests/test_epistemic_reach_screen.py`,
  `eval/mppi_sandbox/tests/test_epistemic_reach_gate.py`,
  `docs/decisions.md` (D-057), `docs/deliberations.md` (Q-071)
- TSV row appended: yes

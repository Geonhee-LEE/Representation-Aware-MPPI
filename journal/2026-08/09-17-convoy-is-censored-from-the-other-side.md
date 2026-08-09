# Convoy is censored too — from the other side

- **Cycle**: 2026-08-09 17:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: `STATE-1` Walk `cafe_convoy_v0` at margin 0.30, both arms
- **Phase**: P5
- **Status**: keep

## What I tried

- Took STATE's #1 literally: `cafe_convoy_v0`, both arms, at **its** declared
  margin 0.30 m — the first scene other than `cafe_head_on_v0` ever measured.
- Screened the operating point first. λ is calibrated per scene, so "the same
  protocol" needed checking before it was spent: `scene_transplant` asks which
  of the band's four rungs convoy can be walked at λ = 0.8, reading the
  `lam_windows_w*.yaml` tables `lam_window_index` already owns.
- Walked the one rung that survived the screen — `w = 75`, λ = 0.8, seeds 0–31
  per arm, 64 runs — and graded it through the **existing** `Headroom` /
  `Reproduction` / `MarginSweep` rather than a fifth hand-rolled primitive.
- Generalized `separation_reproduction._reproduction` into a public
  `reproduction_at(scenario, lam, margin, weight, arms, …)` so a `Reproduction`
  can carry a non-published operating point; the band's builder delegates to it.

## What worked / what failed

- 🔴 **Only 1 of the band's 4 rungs transplants**, and this was free: `w = 75`
  is the sole weight where convoy's admissible λ window contains the band's
  0.8, on both arms. At `w = 100` convoy is calibrated and its window is
  `{1.1314}` — walking λ = 0.8 there would have produced a number
  `assert_ess_in_band` refuses. `w = 150` / `w = 250` have no convoy cell at
  all. The two refusals are kept distinct (`LAM_NOT_ADMISSIBLE` vs
  `UNCALIBRATED`) because only the second is one calibration run from repair.
- 🔴 **Convoy is `NONE_TWO_SIDED` as well — from the opposite boundary.** All
  64 runs clear 0.30 m, the worst by 0.5914 m, so both arms sit at `FLOOR`,
  `BOTH_ARMS_CENSORED`, `NO_HEADROOM_SAFE`, and `unsafe_rate` is **0.0000** on
  both arms. On head_on the stock arm is at a `CEILING` because nothing it does
  clears 0.40 m. Same verdict, opposite cause, opposite remedy — which is why
  `censoring_direction` now exists beside `SeedBlock.censoring`: the count of
  pinned arms cannot tell the two scenes apart.
- 🔴 **And convoy is *less* repairable than head_on, not more.** Its arms are
  **disjoint** — `stock_mppi` tops out at 1.0086 m, `risk_mppi` bottoms out at
  1.0284 m, `arm_overlap` **−0.0198 m** — where head_on's `w ∈ {75, 100}`
  overlap by 7.6 mm and 9.9 mm. A negative overlap is a corner the published
  band never produced; no threshold is interior to both arms at any value.
- 🟢 **The one good number is a mechanism reading, not a safety one.** Every
  `risk_mppi` run is safer than every `stock_mppi` run, 32 against 32 — a
  complete separation the band's own rungs never achieved. It cannot be a
  safety delta because the statistic it would move is 0.0000 on both arms and
  always was. This is D-124's trap in mirror image, and `sub_margin` reads
  `False` here precisely because both means are *above* the margin.
- 🟡 **My docstring named the wrong verdict and the run corrected it.** I wrote
  that `margin_sweep` returns `NO_TWO_SIDED_MARGIN`; it returns
  `NO_RECORDED_SEPARATION`, its vacuity verdict, because that module grades
  whether a *recorded* separation survives re-grading and convoy recorded none.
  The substantive answer was in `two_sided == ()` and the negative overlap, not
  in the verdict field. Fixed before the tests were written.
- 🟡 **The cost worry did not materialize.** STATE budgeted this as the open
  risk (5 obstacles vs head_on's 1, D-116's 50× spread). Measured: ~0.5 s/run,
  68 s for all 64. The screen was the expensive half in thinking, not runtime.
- 🟢 `loop_reach` caught the new population-claim loop on the first suite run
  and refused until it was registered — the guard working as intended.

## North-star delta

- **No movement on the headline, and one scene's worth of movement on what the
  headline can mean.** Zero controller/representation code; `unsafe_rate`
  0.0000 / `min_clearance` 0.3579 / `success_rate` 1.0000 unchanged.
- **2 of the 3 eligible scenes are now measured and neither admits a two-sided
  rung.** D-159 cut the population to 3; this measures the second and it is
  another dead end. Only `cafe_obstacle_crossing_v0` remains.
- First recorded per-seed clearances for any scene other than
  `cafe_head_on_v0` — 64 runs, fully admissible (64/64 reached, 64/64 in band).

## Key learnings

- **A verdict shared by two scenes can have opposite causes, and the shared
  name hides which.** `BOTH_ARMS_CENSORED` on convoy means the margin is too
  *easy*; on head_on it means too *hard*. Reporting the count of pinned arms
  without the boundary they are pinned at merges two problems with opposite
  fixes — the D-107 shape again, now on a field rather than a population.
- **"The same protocol" is a claim that needs screening, exactly like "the same
  population" did.** D-159 screened scenes; this screened rungs within a scene,
  and both times the screen was cheaper than the measurement and changed what
  the measurement was allowed to mean. The generalizable rule: whenever a
  reading widens its scope, re-derive every constant the old scope supplied —
  here λ, last cycle the margin.
- **A complete separation can be worthless as evidence.** 32-vs-32 disjoint
  arms is the strongest clearance result in the repo and licenses no safety
  claim at all. Effect size and admissibility are independent, and the
  intuition that a big enough effect must eventually count is wrong.
- **The next scene inherits a worse prior than convoy did.** Two scenes, two
  boundaries, one verdict — `cafe_obstacle_crossing_v0` should be walked
  expecting a third dead end, and the interesting question is becoming whether
  the *declared margins* are the wrong instrument rather than the scenes.

## Recommended next 1–3 priorities

1. **Walk `cafe_obstacle_crossing_v0`** — the last eligible scene, margin 0.30,
   same screen first (it is calibrated at `w ∈ {10, 75, 100}`). Closes the
   3-scene population the successor question was ever about.
2. **Ask whether the declared margins are the instrument at fault** — head_on
   is censored above 0.40 m, convoy entirely below 0.30 m. If no scene's
   declared margin sits inside its own clearance distribution, the acceptance
   yaml is the finding, not the controllers.
3. **Carry "unmeasured" in the strand verdict (D-156 follow-up)** — deferred
   four cycles now; one field, one test.

## Artifacts

- PR: #67 (continued, per D-140)
- Files touched: `eval/mppi_sandbox/scene_transplant.py`,
  `eval/mppi_sandbox/tests/test_scene_transplant.py`,
  `eval/mppi_sandbox/separation_reproduction.py`,
  `eval/mppi_sandbox/loop_reach.py`, `docs/decisions.md`
- TSV row appended: yes

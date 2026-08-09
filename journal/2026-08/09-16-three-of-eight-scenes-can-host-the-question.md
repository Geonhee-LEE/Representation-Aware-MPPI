# Only three of eight scenes can host the two-sided question, and two of them have never been walked

- **Cycle**: 2026-08-09 16:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: `STATE-1` Which scenes admit a two-sided rung at all?
- **Phase**: P5
- **Status**: keep

## What I tried

- STATE asked the successor question to D-158: *which of the 8 matrix scenes
  have overlapping arm clearance distributions at the published margin?* Before
  measuring any overlap I screened which scenes can host the question at all —
  pure computation from the scenario yamls, no sim runs.
- Shipped `eval/mppi_sandbox/scene_eligibility.py` + 13 tests, composing the
  readers `feasibility` already owns (`declared_margin`, `goal_ball_clearance`)
  rather than adding a fifth hand-rolled primitive.
- Screens: has obstacles → declares a margin → goal ball reachable → are
  per-seed clearances recorded.

## What worked / what failed

- 🔴 **The question's denominator is 3, not 8.** Five scenes cannot host it:
  `cafe_straight_v0` / `city_curved_v0` / `city_figure8_v0` carry **no
  obstacles** (clearance to nothing is D-107's empty-population-reads-as-clean
  again), `cafe_freezing_v0` has two obstacles but **declares no margin**, and
  `cafe_cut_in_v0` is **provably infeasible** — goal-ball clearance **−0.20 m**,
  which `feasibility` already proved and this census now counts.
- 🔴 **And 2 of the 3 survivors have never been walked.** The only eligible
  scene with recorded per-seed clearances is `cafe_head_on_v0` — precisely the
  scene D-158 proved caps at arm coverage **1/4**. So every remaining route to
  a two-sided rung runs through `cafe_convoy_v0` or `cafe_obstacle_crossing_v0`.
  The successor question is a **two-scene walk**, not an eight-scene survey.
- 🔴 **"The published margin" is not a thing across scenes.** The three eligible
  scenes declare **two** margins — `cafe_head_on_v0` 0.40 m, the other two
  0.30 m. The code already knew (`feasibility.declared_margin` and `near_miss`
  say so in as many words), so this is **not a discovery** — but it is new to a
  *cross-scene* reading, because `Headroom` refuses two arms graded against
  different margins. A cross-scene census quoting `scorable_band.PUBLISHED_MARGIN`
  would be quoting a scene constant as a band one, which is D-157's shape.
- 🟢 **A test caught my own arithmetic.** I asserted 9 exclusion reasons over
  the 5 excluded scenes; the real count is **8** (3 obstacle-free scenes fail
  twice, freezing once, cut_in once). Now pinned per-reason rather than as one
  total, so the next miscount names which reason moved.
- 🟡 **Reported, never thresholded** (D-044). No test asserts the eligible count
  is non-zero or that any scene is measured — D-158's censoring lesson applies
  to scenes too: a scene gets *less* eligible as its effect grows, so a gate
  here would punish the strongest results.

## North-star delta

- **No movement in the headline** — zero sim runs, no controller or
  representation code, `unsafe_rate` / `min_clearance` / `success_rate`
  unchanged.
- What moved is the **cost of the next step**: the successor question was
  scoped as 8 scenes and is actually 2, and both are at margin 0.30 rather than
  the 0.40 every recorded magnitude in the repo uses.

## Key learnings

- **Screen the population before measuring the property.** Three cycles running
  (D-157, D-158, this one) the finding has been about *which items the question
  is even askable of*, not about the answer. Asking "do the arms overlap?" of 8
  scenes would have produced 5 vacuous cells that read as clean.
- **A constant that is right in its home module becomes wrong when a reading
  crosses scopes.** `PUBLISHED_MARGIN = 0.40` is correct for `cafe_head_on_v0`
  and is the wrong question for a cross-scene census. The defect is never in the
  constant; it is in the reading that widens without re-deriving.
- **The two unwalked scenes are 5-obstacle scenes**, where `cafe_head_on_v0` has
  1. Whether a 5-obstacle scene's arms overlap more or less than a 1-obstacle
  scene's is genuinely unknown, and it is the first thing the walk answers.

## Recommended next 1–3 priorities

1. **Walk `cafe_convoy_v0` at margin 0.30, both arms** — the cheaper of the two
   unmeasured eligible scenes; the first test of whether *any* scene admits a
   two-sided rung. Budget per-scene (D-116's cost table) and keep `city_*` out.
2. **Carry "unmeasured" in the strand verdict (D-156 follow-up)** — deferred
   three cycles now.
3. **Fix `shift_census`'s absent-cell path (Q-121)** — unchanged for twelve
   cycles.

## Artifacts

- PR: #67 (continuing, per D-140)
- Files touched: `eval/mppi_sandbox/scene_eligibility.py`,
  `eval/mppi_sandbox/tests/test_scene_eligibility.py`, `docs/decisions.md`,
  `results/p3-epistemic-shadow-cost-critic.tsv`
- TSV row appended: yes

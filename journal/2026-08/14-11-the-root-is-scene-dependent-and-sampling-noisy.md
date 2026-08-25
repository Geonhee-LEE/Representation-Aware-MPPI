# The cancelling root is scene-dependent — and half its apparent trend is the sampler

- **Cycle**: 2026-08-14 11:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: `Q-148-geom` Check whether `cancelling_ratio` is geometry-stable
- **Phase**: P3
- **Status**: in_progress

## What I tried

- D-256 put the summed epistemic sign's cancelling root at `w_epist:w_voo =
  0.3587:1` and Q-148's four-arm A/B places its both-on cell against that
  number. One disc, one radius, one stride is a single cell — swept it.
- Shipped `cancelling_stability.py`: the root over a **radius × stride** grid,
  reported as a `RootBand` per geometry (min/max over a stride ensemble) rather
  than a scalar.
- Kept the two axes categorically apart. `radius` is the scene; `stride` is how
  the BEV window is sampled into candidate points and **changes no physical
  quantity at all**. The same movement means opposite things on the two.

## What worked / what failed

- **The repel arm is a unit denominator, so the "ratio" reads one arm.** The
  EPISTEMIC channel is exactly binary (`σ ∈ {0,1}`) and `SHADOW_TAU = 0.5`
  splits on it, so `ShadowCostCritic`'s unit-weight split is **exactly 1.0 at
  every radius and every stride** — measured, not asserted, at 12 cells. Since
  `cancelling_ratio` returns `−v₁/s₁`, it is `−v₁` verbatim: all the variation
  below belongs to `ObservationValueCritic`, whose `V(q)` is a ray aggregate
  with no reason to be scale-free.
- **Geometry genuinely moves the root** — `r=0.3`'s band `[0.1398, 0.2462]` and
  `r=1.0`'s `[0.4363, 0.5332]` are **disjoint**, so no choice of stride makes a
  small-disc scene read like a large-disc one. The root is *not* a constant of
  the critics. Globally it spans **0.1398 … 0.5332, a factor of 3.81**.
- **But the sampler moves it nearly as much, and that is the sharper half.**
  At fixed geometry the stride ensemble alone spans **18–51 % of the band's own
  mean**. So the single-stride sweep I ran first — a tidy `0.2462 → 0.5106`
  march — is confounded: over the ensemble **5 of 6 adjacent radius steps
  overlap**, and only `0.3 → 0.4` separates. The trend is real end-to-end and
  **not resolvable step-by-step**.
- The apparent turnover at `r=1.25` (below `r=1.0` at stride 13) is inside the
  noise — bands overlap, so the module declines to rank them. Reporting that
  dip as a real non-monotonicity would have been the overclaim.
- **D-256's `0.3587` is `IN_BAND` and pins zero decimal places.** The number is
  not wrong; the four digits are. `grade_single` returns exactly that.
- **The receipt came back red on one test, and it was mine.**
  `loop_reach`'s `test_recorded_reading_covers_exactly_todays_targets` pins the
  corpus of population-claim loops, and two of my new tests are such loops. Took
  the ~90 s reading and registered both rows (`SAMPLED n=3` / `n=7`) with the
  reason each is *owed* rather than derivable — radius is continuous and
  `DEFAULT_RADII` is a chosen sweep, so a radius appended later would widen the
  claim silently. Repaired: 58 passed locally.
- **Not pushed.** The repair moved the tree after a red receipt, and the elapsed
  reading was `SUITE_UNAFFORDABLE` by 5m33, so this is committed-unpushed rather
  than pushed-unmeasured (D-082). Next cycle clears it with one suite as its
  first act — the 14-06 → 14-07 path, which is documented and cheap.
- One test I wrote was wrong in a useful direction: `floor(-log10(width))`
  answers **1** for a width that is 2 decimals by construction, because
  `hi - lo` lands on `0.010000000000000009`. Fixed the code (documented
  `_LOG_EPS` nudge), not the expectation.

## North-star delta

- No planner movement and none attempted — still a cost-field reading with no
  sim in the loop.
- What moved is **Q-148's experiment design, for the second cycle running**.
  D-256 said the both-on cell needs a declared ratio; this says that ratio
  **cannot be a project constant** — it is per-scene, and must be quoted as a
  band taken over a sampling ensemble, not as a 4-digit scalar.

## Key learnings

- **Sweep the axis that has no physics in it first.** Stride was the control,
  and it turned out to carry ~40 % of the effect size the geometry axis showed.
  Without it the radius sweep reads as a clean law and would have shipped as one.
- **A band is the honest unit when the reading has a sampler.** Making
  `band_at` *refuse* a single stride (`"sample, not a band"`) is what stops the
  conflation at the door rather than in review.
- **Overlap licenses nothing.** `CONFOUNDED` means "cannot tell", not "equal" —
  there is deliberately no verdict spelled `SAME`, pinned as an API fact so a
  future caller cannot read sameness out of this module (D-241 shape).
- Constants that are structural still get measured. `REPEL_SPLIT_UNIT = 1.0` is
  derivable from `σ ∈ {0,1}`, and the test that pins the binariness is the one
  that will fire the day someone blurs the shadow.

## Recommended next 1–3 priorities

- **Clear this cycle's strand first (D-112)** — run the receipt suite and push.
  The tree is green locally; only the receipt is owed.
- Q-148's four-arm A/B with the both-on cell declared **per-scene as a band** —
  still blocked by PR #68's feasibility filter.
- Ask whether the stride sensitivity is the *reading's* or the **planner's**:
  MPPI samples rollouts, not a grid, so the candidate set has a different
  measure. If `V(q)` is this sampling-sensitive, the attract arm may be noisy
  in the loop too — cheap to probe, and it would upgrade an instrument caveat
  into a controller finding.
- Issue the D-NNN amending D-112's strand recipe (still owed, still cheap).

## Artifacts
- PR: **not pushed this cycle** — committed on autoresearch/p3-epistemic-shadow-cost-critic, receipt owed
- Files touched: eval/mppi_sandbox/cancelling_stability.py, eval/mppi_sandbox/tests/test_cancelling_stability.py, eval/mppi_sandbox/loop_reach.py, docs/decisions.md, docs/deliberations.md
- TSV row appended: pending

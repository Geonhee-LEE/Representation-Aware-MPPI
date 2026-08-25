# The two keys were never in conflict — and D-121's re-attribution does not survive

- **Cycle**: 2026-08-07 23:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: STATE #1 — answer Q-109 (minimum `cte_rms` subject to holding head-on's margin)
- **Phase**: P5 (first day — the date→phase table rolls over today)
- **Status**: keep

## What I tried

- Re-used D-121's station × time lattice and swapped only the optimand:
  bottleneck (maximin over schedules) → **additive shortest path**, minimising
  Σe² among schedules that hold the declared margin at every instant.
  Shipped as `feasibility.min_cte_rms()` + `CteFloor`.
- Priced the offset the way the metric does: cost is **perpendicular distance
  to the polyline**, not offset magnitude, cross-checked against
  `path_tracking_metrics.cross_track_error` on a curved path.
- Derived the lateral search range from `required_corridor` (×2) instead of
  assuming one — it is the single parameter that errs in the unsafe direction.
- Swept the loitering horizon (`timeout_factor` 1.0 … 4.0) to find out whether
  the verdict was about the scene or about the timeout.

## What worked / what failed

- ✅ **Q-109 answers COMPATIBLE, and by a wide margin**: head-on's floor is
  **0.0865** against a declared `cte_rms_max` of **0.30**. The 1.00 m sidestep
  D-121 priced is a *transient*, and an rms bound charges it only for the
  samples it lasts. D-121's refusal to call 1.00 > 0.30 a contradiction was
  correct, and is now measured rather than merely withheld.
- ✅ **The one knob that could have produced the answer for free does not.**
  `cte_rms` averages over **samples**, so a schedule that dawdles on the path
  dilutes its own excursion, and the search may do that out to the timeout —
  the floor falls monotonically with the horizon (tf 4.0 → 0.0865, 2.0 →
  0.1222, 1.5 → 0.1411, 1.0 → **0.1727**). At tf = 1.0 there is no dilution
  budget at all and the answer is unchanged. Pinned as a test.
- 🔴 **This partially reverses last cycle's headline.** D-121 moved 16 of
  D-120's 32 unsafe seeds from planner to scene declaration on the strength of
  an incompatibility that was **stated but never measured**. No shipped
  obstacle scene is `INCOMPATIBLE` — all five can meet both lateral keys at
  once — so those seeds stay controller debt. The screen that found the 1.00 m
  is the same screen that now declines to excuse it.
- 🔴 **What survives is a declaration gap, not a contradiction.** Head-on
  needs a 1 m instantaneous sidestep, declares no `cte_max` forbidding it, and
  never says it is allowed. The only lateral number a controller author can
  see is 0.30, which reads like a far tighter box than the run is held to.
- 🟡 Q-109's own hand calculation ("the excursion must be within 9% of the
  run") was arclength-based and missed the sample-averaging freedom entirely.
  The question's arithmetic, not its premise, was the wrong part.

## North-star delta

- The project's first **proof that a safety target is assignable**: head-on's
  0.40 m margin is both geometrically attainable (D-121) and affordable within
  its own tracking budget (this cycle), so its 8/8 unsafe is a controller
  target with no escape hatch left.
- Zero of 32 unsafe seeds are now attributable to scene declaration. The safety
  headline `unsafe_rate = 0.6667` is entirely planner debt.
- No controller changed; `success_rate` and `unsafe_rate` are untouched.

## Key learnings

- **A peak and an rms are not comparable until one is converted into the
  other's units, and the conversion has a free parameter.** Here it was the
  run length. A screen that reports the converted number without reporting its
  sensitivity to that parameter is reporting a property of the timeout.
- **A measurement that vindicates the previous cycle's caution can still
  refute its conclusion.** D-121 was right not to call it a contradiction and
  wrong to re-attribute 16 seeds as if it were one — the same cycle did both.
- **Deriving a search bound from an already-measured quantity beats widening
  it.** Truncation was the only relaxation pointing the unsafe way; sourcing it
  from `required_corridor` made the range self-checking rather than generous.

## Recommended next 1–3 priorities

1. **Answer Q-107** (per-cell temperature aggregation, open since D-119) — it
   now gates cross-controller deltas on *two* scenes proven to be controller
   targets, not one.
2. **Declare the permitted excursion in the scenario yamls** — head-on's
   `cte_max` gap is a one-line fix per scene, but the number is a scene-intent
   call the user owns.
3. **Attack the crossing scene's 8/8** — D-121 proved a 0.00 m corridor
   suffices there, so it is the cheapest place to convert a proven target into
   a controller improvement.

## Artifacts

- PR: pending merge (`autoresearch/p3-epistemic-shadow-cost-critic`, #67)
- Files touched: `eval/mppi_sandbox/feasibility.py`,
  `eval/mppi_sandbox/tests/test_cte_floor.py`, `docs/decisions.md`,
  `docs/deliberations.md`, `results/p3-epistemic-shadow-cost-critic.tsv`
- TSV row appended: yes

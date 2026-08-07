# The near-miss metric turns a clean sheet into 2/3 unsafe

- **Cycle**: 2026-08-07 21:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: STATE #1 — add a near-miss metric to the matrix
- **Phase**: P5
- **Status**: keep

## What I tried

- Added `near_miss.py`: per-run `SAFE`/`NEAR_MISS`/`COLLISION` against the
  **scene's own** declared margin, not a module constant. The shipped scenes
  disagree (`cafe_head_on_v0` 0.40 m, `cafe_convoy_v0` 0.30), so a global
  threshold would overrule the scene that asked for more.
- Put the acceptance-key read in one place (`feasibility.declared_margin`,
  returning `float | None`) and left its two consumers defaulting **oppositely
  on purpose**: the feasibility screen keeps its optimistic `0.0` (an
  undeclared margin must never retire a scene), the metric refuses.
- Wired a **third** headline denominator into `baseline_matrix`, plus
  `unsafe_rate` alongside `near_miss_rate`.
- Ran the 4 obstacle scenes × 2 calibrated controllers × 8 seeds (110 s).

## What worked / what failed

- 🔴 **The headline flips: `collision_rate = 0.0000` → `unsafe_rate = 0.6667`.**
  32 of 48 scored seeds come closer than the scene itself declared acceptable.
  The project's "zero collisions" reading was an artifact of a metric that
  saturates exactly where the north star's near-miss term begins.
- 🔴 **4 of 6 scorable cells are 8/8 — every seed, both controllers.**
  `cafe_head_on_v0` and `cafe_obstacle_crossing_v0` fail totally; not one seed
  of eight clears the bar. This is systematic, not a tail event.
- ✅ **The metric discriminates rather than just going red**: `cafe_convoy_v0`
  is **0/8 on both arms** (0.358 / 0.830 against a 0.30 margin). Two scenes
  pass cleanly and two fail totally, so the number is not vacuously saturated
  in the pessimistic direction either — which was the live risk of choosing
  the scene's own margin as the bar.
- 🔴 **D-119's directional controller signal survives and is shown to be
  operationally worthless at this bar.** `risk_mppi` does hold more clearance
  everywhere (head_on 0.064 vs 0.002 — **32×**), and its near-miss rate is
  *identical*: 8/8 vs 8/8. A 32× clearance improvement that moves the safety
  verdict not at all. D-119 reported the ordering as suggestive; the margin
  metric says the ordering is real and far too small to matter yet.
- 🔴 **2 of 8 cells cannot be scored at all**: `cafe_freezing_v0` contains
  obstacles and declares no margin. Under the convenient `0.0` default its
  band is `[0, 0)` and it would have reported a perfect `0.0000` for free —
  D-107's empty-population-reads-as-clean, landing in the *safety* headline.
  Excluded by name instead, and still counted for collisions.
- 🟡 **`near_miss_rate == unsafe_rate` exactly on this data**, because nothing
  collided. The monotonicity distinction that decided the headline has not yet
  bitten on live numbers — it is pinned in tests, unexercised in the field.

## North-star delta

- **The first measurement of the north star's "near-miss ≤ Y" term.** It was
  named in `CLAUDE.md` from the start and had never been computed.
- Movement is **negative and that is the point**: the honest safety number went
  from 0.0000 to 0.6667. Nothing about the controllers changed this cycle.
- The avoidance axis now has a bar that a controller can be *ranked* against.
  `min_clearance` was a scalar with no reference; `unsafe_rate` has one.

## Key learnings

- **A saturating metric reads as success right up until it is replaced.** Three
  cycles reported `collision_rate = 0.0000` as the good news and `min_clearance
  = 0.0016` as a footnote. They were the same measurement disagreeing with
  itself, and the footnote was correct.
- **`near_miss_rate` is not monotone in safety** — its band is `[0, margin)`, so
  a graze degrading into a collision *leaves* the set and the rate goes down. A
  controller could improve it by colliding more. `unsafe_rate` opens the band
  downward and is the only one of the two that may be ranked on. Pinned in both
  directions.
- **An undeclared threshold is not a threshold of zero.** The same absent key
  needs an optimistic default in a screen and a refusal in a metric; one reader
  returning `None` is what let the two stay different deliberately.
- **A 32× improvement in a scalar can be a 0× improvement in the verdict.**
  Worth carrying into any future controller claim: report the delta against the
  bar, not against the other arm.

## Recommended next 1–3 priorities

1. **Declare a margin for `cafe_freezing_v0`** (or record why it has none) —
   it is 2 of 8 cells and the only unscorable class.
2. **Ask why head_on and obstacle_crossing fail 8/8** — is the cost term unable
   to hold 0.40 m, or is the declared margin infeasible for the geometry?
   `feasibility.goal_ball_clearance` already computes the geometric bound.
3. **Re-run the full 24-cell matrix with the new axis** — this cycle scoped to
   the 4 obstacle scenes to fit the budget.

## Artifacts

- PR: pending merge (`autoresearch/p3-epistemic-shadow-cost-critic`, #67)
- Files touched: `eval/mppi_sandbox/near_miss.py`,
  `eval/mppi_sandbox/feasibility.py`, `eval/mppi_sandbox/baseline_matrix.py`,
  `eval/mppi_sandbox/tests/test_near_miss.py`, `docs/decisions.md`
- TSV row appended: yes

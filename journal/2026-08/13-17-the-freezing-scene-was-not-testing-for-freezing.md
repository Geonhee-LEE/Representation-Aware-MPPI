# The freezing scene was not testing for freezing

- **Cycle**: 2026-08-13 17:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: `state-item-2` Price the freeze into the planner (STATE next-actionable #2)
- **Phase**: P3
- **Status**: keep

## What I tried

- Took STATE's bottleneck — *"the freeze is detected but never priced"* — and
  went to write the cost term. Ran the "grep before proposing" check that the
  previous cycle turned into a rule, and it fired: the blocker is one level
  earlier than the bottleneck says.
- `freeze_duration` appears **exactly once in the tree**, in
  `cafe_freezing_v0.yaml`'s `acceptance` block, where it is also ranked
  **second** in `success_metric_priority`. No code computes it.
- Worse than uncomputed: `run.check_acceptance` maps unknown keys to the string
  `"skipped"`, and `run_scenario` derives `pass` from
  `[v for v in checks.values() if isinstance(v, bool)]`. A `str` is not a
  `bool`, so the key was **silently dropped from the scene's own pass/fail**.
- Shipped `eval/mppi_sandbox/freeze_price.py` (metric + profiler + CLI), wired
  the key into `check_acceptance`, and measured the three arms on the scene.

## What worked / what failed

- **The scene whose entire reason for existing is the freezing-robot failure
  mode has been passing without ever being asked about freezing.** That is the
  cycle's finding, and it is a defect, not a gap.
- Measured, 3 seeds × 3 arms on `cafe_freezing_v0`, longest along-path stall [s]
  against the scene's declared 2.0 s limit:

  | arm | seed 0 | seed 1 | seed 2 | exceeds 2.0 s | reached goal |
  |---|---|---|---|---|---|
  | `stock_mppi` | 1.60 | 0.60 | 0.40 | **0/3** | 3/3 |
  | `risk_mppi` | 0.60 | 6.30 | 3.30 | **2/3** | 3/3 |
  | `social_mppi` | 3.30 | 1.70 | 2.40 | **2/3** | 3/3 |

- **All 9 runs reached the goal.** So `three_arm`'s freeze detection — which
  fires on `d_reached < 0` — is blind to **every one of these**. The existing
  detector cannot see a freeze that the robot recovers from, and that is the
  whole population measured here.
- Seed 0 alone would have said `risk_mppi` freezes *least* (0.60 s). Across
  three seeds it holds the single worst reading (6.30 s). Widening from n=1 to
  n=3 inverted the apparent ranking — the n=1 table I nearly wrote was wrong.
- Startup transient counts toward the metric by construction (robot starts at
  `v = 0`). Documented rather than special-cased; it is bounded far under 2.0 s
  and `stock_mppi`'s 0.40 s floor is mostly it.

## North-star delta

- **+1 acceptance criterion that now actually gates**, on the scene that owns
  the 가려진/dynamic avoidance failure mode. `cafe_freezing_v0`'s `pass` was
  computed over 5 checks and is now computed over 6.
- **First direct freeze measurement on this project.** Everything prior was the
  completion proxy, which the table above shows is blind at 9/9 here.
- **+0 mechanism.** No planner changed; no cost term shipped. The bottleneck
  named pricing and this cycle delivered the price *tag*, not the price. Honest
  delta: the successor D-240 called for is now measurable rather than done.

## Key learnings

- **The bottleneck was one level off, and the grep is what caught it.** "Price
  the freeze" presupposes a freeze number; there wasn't one. D-021's rule (no
  unmeasured cost term) would have been violated by doing exactly what STATE
  said to do — the rule and the plan disagreed, and the rule was right.
- **A declared-but-unimplemented acceptance key is worse than a missing one**,
  because `"skipped"` reads as *checked* in the artifact. Worth a sweep: any
  other yaml key across the ten scenes that `rules` has no entry for is in the
  same silent state.
- **The risk channel appears to buy freeze**, matching STATE's guess that
  `w_speed` is outweighed by the anisotropic field — but at n=3 with a 0.60→6.30
  spread on one arm, *ranking* the arms is not supported. What the data does
  support is the blindness claim (9/9), which needs no ranking.

## Recommended next 1–3 priorities

1. **Now price it** — the mechanism successor, with a number to grade against.
   Design against `cafe_freezing_v0`; the target is `stock_mppi`'s 0/3 exceed
   rate at `social_mppi`'s clearance.
2. **Widen to the paired-seed protocol** (n=12, matched λ) before quoting any
   arm ranking from the table above.
3. **Sweep the other nine scenes for `rules`-less acceptance keys** — same
   silent-`"skipped"` defect class, one grep.

## Artifacts

- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic)
- Files touched: `eval/mppi_sandbox/freeze_price.py`, `eval/mppi_sandbox/run.py`, `eval/mppi_sandbox/tests/test_freeze_duration.py`, `docs/decisions.md`
- TSV row appended: yes

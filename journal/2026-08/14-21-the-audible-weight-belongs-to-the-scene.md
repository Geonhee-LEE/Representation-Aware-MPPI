# The audible weight belongs to the scene, not to the arm

- **Cycle**: 2026-08-14 21:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: `voo-bar-crossing` (STATE #1) — narrow `(5, 20]`, test scene-stability
- **Phase**: P3
- **Status**: keep

## What I tried

- Bisected D-265's open bracket on the reference scene: `w_voo ∈ {8, 11, 14, 17}`
  on `cafe_obstacle_crossing_v0`, same isolation `grade` uses.
- Re-took the full `{1, 5, 20, 50, 200}` ladder on `cafe_freezing_v0` and
  `cafe_cut_in_v0` — the D-260 non-transfer question, asked of the *shape*
  rather than of the sign. 14 closed-loop runs, ~4 min.
- Landed both as `BISECT_CURVE` / `SCENE_CURVES` plus three readers:
  `bar_crossing` (a bracket, deliberately not an interpolation),
  `common_audible_weights`, `scale_is_per_scene`.

## What worked / what failed

- **The bisect answered, and then the other two scenes made the answer
  useless.** Reference crossing narrows `(5, 20] → (5, 8]` (`0.1541` at `w=8`).
  But the brackets are `(1, 5]` on `freezing`, `(5, 8]` on `crossing`,
  `(50, 200]` on `cut_in` — **disjoint, spanning the ladder's whole range**.
  `common_audible_weights()` is **empty**, and `ARM_SCALE` is one number every
  run of the A/B shares. So there is no scale to pick here.
- **D-265's peak-then-collapse does not transfer.** `freezing` rises
  *monotonically* to `3.264` at `w=200`; `cut_in` likewise. The `87×`
  `rest_median` jump is `cafe_obstacle_crossing_v0`'s own geometry, reached at
  one weight — not a property of the ratio. `shape_transfers` is `False`.
- **`cut_in` is quiet because its competitor is loud, not because its arm is
  weak.** `rest_median` sits at `~1.0e4` from `w=1` (86× the reference scene)
  and moves <1% across the whole ladder: the collision term fires there
  regardless of the arm. Turning the arm up is therefore not the fix, and the
  diagnosis distinguishes the two only because the denominator was recorded.
- **A local non-monotonicity inside the bisect, too small to claim**: `0.2895`
  at `w=14`, `0.2765` at `17` (−4.5%, denominator again). Same direction as
  D-265's, but not separable from run-to-run variation — so `bar_crossing`
  returns brackets and refuses to interpolate rather than smoothing it away.
- I expected the cycle to end with a number for `ARM_SCALE`. It ends with a
  scope instead, which is the less satisfying and more defensible output.

## North-star delta

- No closed-loop movement. What moved is the **falsification rate**: three
  consecutive cycles (D-264, D-265, D-266) have each killed a premise the A/B
  was about to be built on, this one before any arm ran.
- The PR #68 blocker is now *load-bearing*, not merely inconvenient: with no
  transferable scale, the only reading that settles Q-148 is on
  `cafe_blind_corner_v0`, and that scene is on the unmerged branch.

## Key learnings

- **"Narrow the bracket" and "check it transfers" are not two tasks — the
  second can void the first.** Doing the cheap transfer check *in the same
  cycle* is what stopped `(5, 8]` from being written into the arm config.
- **A ratio's denominator carries the scene.** Both non-transfers this branch
  has found (D-265's collapse, D-266's disjoint brackets) live entirely in
  `rest_median`; the numerator has been well-behaved every time.
- Recording `rest_median` alongside the ratio — a choice D-265 made for a
  different reason — is what let `cut_in`'s quietness be diagnosed rather than
  mistaken for a weak arm.

## Recommended next 1–3 priorities

- **PR #68 merge** — now the single blocking dependency, not one of three.
  Everything downstream of Q-148 waits on a `sweep_ratio` reading on
  `cafe_blind_corner_v0`.
- `ess-at-the-peak` — still unanswered and now cheaper to interpret: take
  `ab.median_ess` along the `freezing` ladder, where the ratio reaches `3.26`
  with no collapse, and see whether D-027's softmax collapse tracks the ratio
  or the scene.
- `inert-probe-budget` — the five withdrawn exemptions remain unbought.

## Artifacts
- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic)
- Files touched: eval/mppi_sandbox/arm_audibility.py, eval/mppi_sandbox/tests/test_arm_audibility.py, docs/decisions.md, docs/deliberations.md
- TSV row appended: pending

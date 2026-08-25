# `lam` cannot repair the endpoint it is blamed for

- **Cycle**: 2026-08-16 00:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: `<walk-the-upper-endpoint>` walk `w = 5` at `lam ∈ {1.15, 1.25}` on the 16-seed census
- **Phase**: P3
- **Status**: keep

## What I tried

- Walked two new `w = 5` census columns at the 16-seed count on
  `cafe_freezing_v0` — `lam = 1.15` (inside D-290's open upper interval) and
  `lam = 1.25` (one rung beyond the failing neighbour, to ask whether
  membership recovers above the run). 32 closed-loop runs, ~4 min concurrent.
- Registered both into `CENSUS_COLUMN_ROWS` so `unanimity_bracket()` reads
  seven columns instead of five.
- Added `endpoint_repair_axis()` — the reading that asks whether `lam` can
  actually supply the repair that `translated_out_of_band` says exists.

## What worked / what failed

- **The endpoint narrowed, and the run did not move.** `lam = 1.15` is `15/16`
  (seed 15 at `140.07`, over the `128.0` ceiling), so the upper endpoint is in
  `(1.1, 1.15)`, not `(1.1, 1.2)`. `BRACKET_CLOSED_BOTH_EDGES` and the
  unanimous set `{1.0, 1.1}` both survive the extra columns.
- **No recovery above.** `lam = 1.25` is `14/16`, both misses over the ceiling.
  Membership decays monotonically above the run — `16, 15, 15, 14` — so there
  is no second unanimous region up there.
- **STATE's framing was wrong and this cycle measured it.** It called the upper
  endpoint "the repairable side" because the span fits the band. The misses are
  over the *ceiling*, so repair means moving the ensemble **down**; median ESS
  rises strictly with `lam` on that side (`75.38, 79.19, 88.59, 97.59`). The
  only `lam` that moves the ensemble down is a smaller one — which lands back
  inside the unanimous run. `REPAIR_AXIS_REVERSES_INTO_RUN`.
- **The tightest column is the least unanimous one.** `lam = 1.25` spans
  `2.90x` against a `10.0x` band — `3.45x` of slack, narrowest of any `w = 5`
  column — and is the worst of the upper three. The cluster contracts and is
  carried through the ceiling at the same time; the second effect wins.

## North-star delta

- No obstacle, clearance or near-miss number moved. Still one scene, still
  `transfers_to_ab_scene = False`.
- The `w = 5` operating window is now bounded on the side that mattered to
  within `0.05` in `lam`, and the *mechanism* of that bound is measured rather
  than inferred — the branch can stop looking for a temperature above the run.

## Key learnings

- **"Repairable in principle" names an arithmetic, not an axis.** D-283's
  admissibility test says *some* common factor exists; it does not say the one
  knob you have is it. At `lam = 1.25` the column needs only a `1.0614x` shrink
  — the smallest demand anywhere on the ladder — and `lam` still cannot deliver
  it, because the axis that translates the ensemble is the axis the endpoint is
  defined on. That distinction is worth carrying to every future "repairable"
  label on this branch.
- **Span-admissibility is necessary, not sufficient, and now there is a clean
  counterexample.** Prior cycles read shrinking span as progress toward
  unanimity (D-290: "span, not median, predicts unanimity"). `lam = 1.25`
  falsifies the strong form of that: the narrowest column has the worst
  membership.
- **Read the direction on the side you are asking about.** Median ESS dips once
  at `0.8 → 0.9`, so a global monotonicity test returns `NON_MONOTONE` and
  vetoes a reading about the upper side, where the dip is irrelevant (that side
  is `span_exceeds_band` and never reaches the axis question). The reading
  reports the full sequence and `axis_monotone_globally=False` so the narrowing
  is visible rather than silent.
- **The module's `median_ess` is the upper-middle order statistic, not
  `statistics.median`.** The two disagree exactly at the `0.8 → 0.9` step —
  enough to flip a monotonicity verdict. Worth stating wherever a median is
  compared across columns.

## Recommended next 1–3 priorities

1. **Find a common factor that is not `lam`.** The upper endpoint needs the
   ensemble moved down without moving along the temperature axis; `K` and
   `w_voo` are the untested candidates. This is the direct successor to D-291.
2. **Walk `w = 12` as a temperature column.** Still the only other admissible
   rung (`5.79x`, D-289) and still never walked in `lam` — it is what would
   test whether `{1.0, 1.1}` is a property of the rung or of the scene.
3. **Re-probe the 5 withdrawn `inert_surface` pins** — thirteenth consecutive
   cycle; it again forced an all-writes-before-suite ordering.

## Artifacts
- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic)
- Files touched: eval/mppi_sandbox/calibrated_ladder.py, eval/mppi_sandbox/tests/test_calibrated_ladder.py, eval/mppi_sandbox/loop_reach.py, docs/decisions.md, results/p3-epistemic-shadow-cost-critic.tsv
- TSV row appended: yes

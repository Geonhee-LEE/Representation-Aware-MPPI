# The widening cannot rescue the line — 경로추종 instrumented on 3 of its 4 clauses

- **Cycle**: 2026-08-29 03:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: STATE #1 — decide whether `CLASS_AXIS` should instrument 경로추종 with all four `CLAUDE.md` clauses
- **Phase**: P5
- **Status**: keep

## What I tried

- Shipped `tracking_instrumentation` (~330 LOC) + 40 tests: the instrumentation
  decision for 경로추종, derived rather than argued. No rollout bought — both
  new columns were already on disk from D-488.
- Enumerated `CLAUDE.md`'s four clauses against what the tree can actually
  compute, separating *unbought* (census nobody ran) from *unmeasurable* (no
  metric at all).
- Re-derived the tracking frontier under one clause vs three, holding the scene
  set fixed so the axis effect is not confounded with the population effect.
- Bumped `guard_tally` 158 → 164 pre-suite after `census_preempt` flagged it.

## What worked / what failed

- **The decision is `WIDEN_TO_CENSUSED`, and finding #4 is why it is safe.**
  Domination is antitone in the axis count, so a frontier can only grow when
  clauses are added. The tracking frontier is already 3 wide (D-487's
  `NO_FRONTIER_SINGLETON`), so **no instrumentation can shrink it to a
  singleton**. Widening strengthens the refusal and cannot silently overturn it.
  `widening_is_monotone` checks the implication on the data anyway rather than
  resting on the argument — a tamper test confirms it goes False when the gate
  is made asymmetric.
- **`heading error` is unbought, not unmeasurable — and now priced.**
  `path_tracking_metrics.heading_error` exists and is a pure function of
  `(traj, path)`, exactly like the two D-488 bought for 58.6 s. So the gap is
  32 rollouts, not a missing metric. `unbought_clauses` and
  `unmeasurable_clauses` are kept separate because they call for different
  actions and merging them would price the second like the first.
- **Widening costs scenes, and the two effects had to be split.** The tracking
  class owns 7 scenes on cross-track; `AXIS_SEED0` covers 4. So a frontier read
  after widening has two candidate causes — more axes or fewer scenes — and
  `common_population` isolates one. This is D-489's own lesson applied *before*
  quoting the number rather than after a tamper test caught it. The 3 lost
  scenes turn out to be exactly D-487's inert blocks (derived, not assumed).
- **The arrival gate had to widen with the clause set.** `time_column` omits
  `essps_mppi × cafe_obstacle_crossing_v0`, but that cell carries a finite
  `cte_rms` *and* a finite `jerk_lat`. Since `dominates` compares on *shared*
  columns, an ungated build would have scored that arm on two clauses while
  excusing it from the third — charging it nothing for the failure it was being
  measured tidily failing at. Gating cuts the arm from **all** clause columns of
  that scene; this is why the module builds its own columns.

## North-star delta

- **경로추종 is now instrumented on 3 of its 4 north-star clauses, up from 1** —
  and the fourth is named with a price rather than dropped. The P5 report can
  state the tracking class as a claim about three clauses, which is the first
  time either class has been scored on more than one.
- **D-486 reproduces on the tracking class alone.** Fully instrumented, the
  widened frontier is 8 of 8 raw — but that is the inflation D-486 named, since
  `geometric_mppi` and `stock_mppi` are bit-identical on all three clauses.
  Collapsed it is **7 of 7**: every distinct arm non-dominated.
- Still seed 0, still no `heading error` column. No new controller,
  representation or dynamics code — this is a measurement-honesty pass.

## Key learnings

- **The duplicate structure moved a fifth time, and in a new direction.** One
  pair here against two on clearance: `frozen_risk_mppi`/`risk_mppi` are
  identical on clearance and separate on cross-track. So the collapse is
  clause-relative and cannot be inherited from `class_contract` — which is what
  makes `distinct_frontier_under` a required step and not a convenience.
- **Three of the six new guards screen the *constitution*, not a census.** Their
  population key is `NORTH_STAR_CLAUSES` — the clause list read off `CLAUDE.md`.
  Every prior entrant screened something the tree measured; these screen the gap
  between what it measured and what it promised. That is a direction a census of
  censuses cannot reach on its own.
- **A monotonicity argument is not a reason to skip the check.** The antitone
  argument is about the columns, and this module builds its own gated columns —
  so a gating bug could break the implication with nothing else to notice.

## Recommended next 1–3 priorities

1. **Re-derive `class_contract`'s tracking keys against D-490's verdict** —
   deliberately not done here (one claim, one module). The gated multi-clause
   plurality is a record claim and belongs there.
2. **Buy the `heading error` census** — 32 rollouts, under a minute at D-488's
   measured rate, and it closes the last clause gap in 경로추종.
3. **Widen `axis_purchase` to 8 seeds** — unchanged; every finding here, D-490
   included, is seed 0.

## Artifacts

- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic)
- Files touched: eval/mppi_sandbox/tracking_instrumentation.py, eval/mppi_sandbox/tests/test_tracking_instrumentation.py, eval/mppi_sandbox/tests/test_guard_reflexivity.py, docs/decisions.md
- TSV row appended: yes

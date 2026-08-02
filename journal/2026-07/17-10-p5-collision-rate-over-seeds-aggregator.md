# P5 seed-sweep aggregator: collision/near-miss rate over seeds

- **Cycle**: 2026-07-17 10:00 KST
- **Branch**: `autoresearch/p5-collision-rate-over-seeds-aggregator`
- **TODO**: `p5-seed-rate` P5 occlusion metric = collision/near-miss rate over seeds
- **Phase**: P5
- **Status**: keep

## What I tried
- Added `eval/mppi_sandbox/seed_sweep.py`: runs one `(scenario, controller)` over
  N seeds and reports `collision_rate / near_miss_rate / unsafe_rate / pass_rate`
  + `clearance_min/mean` + per-seed rows. CLI + JSON writeout, seed spec `8`/`0,3,7`/`2-5`.
- 9 pytest cases in `tests/test_seed_sweep.py` (band classify, rate arithmetic,
  near-miss monotonicity, guards, 1-seed==run_scenario contract, JSON write).
- Deadlock-breaker: closed superseded **PR #44** (P2 residual-dynamics scaffold,
  pre-sandbox, superseded by D-016) to drop the 72h-stalled queue 6→5, then ran.

## What worked / what failed
- Aggregation-only design holds: a 1-seed sweep reproduces `run_scenario`'s
  clearance exactly — the metric adds *search*, not simulation behavior.
- Live smoke on `cafe_head_on_v0` **validated the whole premise**: stock grazes at
  ~0.003–0.007 m every seed → min-clearance saturates and looks identical seed to
  seed, but `unsafe_rate=1.0, near_miss_rate=1.0, collision_rate=0.0` cleanly flags
  "grazes every time." A safe controller would read `unsafe_rate=0`.
- The payoff experiment (STATE #1/#2, epistemic-aware vs `vg_mppi`) turned out
  **infeasible on main**: `vg_mppi` + `cafe_blind_approach_v0` live only on
  unmerged branch #69 (stale `.pyc` in `__pycache__` masked this). Feasibility
  filter kicked it back; #3 was the feasible on-bottleneck pick.

## North-star delta
- + First **rate-over-seeds** occlusion-sensitivity metric — P5's occlusion axis
  can now score collision/near-miss *rate*, the metric STATE proved is needed
  because min-clearance saturates at the `w_collision` barrier floor.
- Gives the (still-pending) `vg_mppi` 3/8-vs-0/8 finding a *reusable* scorer
  rather than an ad-hoc per-branch count.

## Key learnings
- STATE's "Feasible on main" annotations can lag reality — always verify the
  required source is on `main` (not just `.pyc`) before trusting a next-actionable.
  `vg_mppi`/blind scenario are branch-only until #69 merges.
- `unsafe_rate = collision ∪ near_miss` is the more robust headline than
  collision_rate alone on this plant: the barrier rarely lets a full collision
  through, so near-miss carries most of the epistemic-blindness signal.

## Recommended next 1–3 priorities
1. **Merge PRs #66→#69** — lands `vg_mppi` + `cafe_blind_approach_v0` on main,
   unblocking the payoff A/B *and* letting `seed_sweep` score it directly.
2. **Payoff A/B via `seed_sweep`**: once #69 lands, `seed_sweep vg_mppi` vs
   `risk_mppi(k·σ)` on `cafe_blind_approach_v0`, 8 seeds — does epistemic berth
   recover `collision_rate 0`?
3. **Wire `seed_sweep` into the P5 calibration harness** so the `(k,δ)` sweep
   emits rate-over-seeds per operating point (not single-seed clearance).

## Artifacts
- PR: #70 (autoresearch/p5-collision-rate-over-seeds-aggregator)
- Files touched: eval/mppi_sandbox/seed_sweep.py, eval/mppi_sandbox/tests/test_seed_sweep.py, results/p5-collision-rate-over-seeds-aggregator.tsv
- TSV row appended: yes

# The 1.37× buys nothing — and the second column Q-157 asked for cannot exist here

- **Cycle**: 2026-08-17 16:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: Q-157 — price the 1.37× (STATE next-claude-actionable #1)
- **Phase**: P3
- **Status**: keep

## What I tried

- Added an 8th column to `essps.PER_ITERATION_ARMS` — minimum surface-to-surface
  clearance over each arm's episode — and taught `compare_arms` to take it via
  `obstacles.min_clearance`, the same primitive `run.py` already scores with.
- Re-took both arms (`essps_mppi`, `risk_mppi`) on `PEAK_SCENE` at the operating
  point to fill the column with a measurement rather than a guess.
- Added `ArmComparison.clearance_gain` / `.buys_clearance`, and
  `near_miss_scorable()` — a derived predicate for the *other* column Q-157
  asked for.
- Four tests: the finding itself, the difference-not-ratio property, and the
  near-miss predicate pinned in both directions.

## What worked / what failed

- **The falsifier fired, in the direction that kills the arm.** Solved arm's min
  clearance `0.3319 m`, control's `0.3447 m`. The per-iteration form spends 37%
  more steps and finishes **1.3 cm closer** to the obstacle. `buys_clearance` is
  `False`.
- **Provenance held.** Columns 1–7 re-measured *identically* (157/157/0/0/80.0/
  0.9931/0.0455 and 115/69/43/3/31.2344/0.9926/0.0455). That is what licenses
  reading column 8 as new information rather than as a different run — without
  it, a changed clearance and a changed everything-else are indistinguishable.
- **Half of Q-157's plan was impossible and the plan did not know it.** `PEAK_SCENE`
  is `cafe_freezing_v0`, which carries obstacles and declares **no** margin.
  Near-miss needs a threshold, the threshold is the scene's, and
  `feasibility.declared_margin` returns `None` — so `near_miss` excludes this
  cell *by name*. Filling the column with an invented threshold would have put
  D-107's empty-population-reads-as-clean in the middle of a safety comparison.
- The run cost **1.7 s**, not the ~26 s Q-157 budgeted. The estimate was ~15×
  long — the same self-estimation bias D-154 records for elapsed time, now
  observed on run cost.
- Found a **Q-number collision**: two live `Q-157` entries (2026-08-15 `[arch]`
  and 2026-08-17 `[uncertainty]`). Noted in `deliberations.md`; next new Q is
  Q-159.

## North-star delta

- **A candidate controller arm is retired on a north-star metric.** Time-to-goal
  is a north-star term and clearance is a north-star term; the arm loses the
  first and does not win the second. Retiring it is real movement — the arm was
  one cycle away from being carried into a seed ensemble on a compliance number
  that was structurally guaranteed.
- **Two of three planned follow-ups are now unnecessary.** Q-157's seed ensemble
  and scene-transfer branches existed to characterize a trade; there is no trade,
  so ~8 seed-runs of work is deleted rather than deferred.
- No movement on `transfers_to_ab_scene` — still behind PR #68, still unmeasured.

## Key learnings

- **The cheapest falsifier is worth running even when you expect a trade.** The
  arm looked like a safety/speed trade-off and was in fact a plain regression;
  one 1.7 s measurement separated those, and the expensive plan (seed ensemble)
  would have priced a trade that does not exist.
- **A plan can request a column the scene cannot supply.** Q-157 named
  min-clearance and near-miss as if they were symmetric; one is threshold-free
  and one is not. The asymmetry is a property of the *scene*, not of the effort
  available, so no amount of budget would have produced the second column.
- **Record the absence as a predicate, not a comment.** `near_miss_scorable()`
  reads `declared_margin`, so a scene file that later declares a margin flips a
  test instead of leaving a column everyone quietly stopped expecting (D-047).
- **Report the sign, not the magnitude, when the seed spread is larger than the
  effect.** 1.3 cm is smaller than D-019's per-seed spread, so "no clearance
  gain" is supportable and "worse clearance" is not.

## Recommended next 1–3 priorities

1. **Do not run the Q-157 seed ensemble.** It was conditional on a trade
   existing; it does not. Reallocate to `transfers_to_ab_scene` once #68 lands.
2. **Ask whether any arm on this branch buys clearance.** The clearance column
   now exists in `compare_arms`; running it across the shipped arms is cheap and
   would say whether the branch has *ever* measured a safety gain, or only ESS
   compliance.
3. **Wire `queue_debt` into the gate-1 snippet** — carried from 14:00/15:00,
   still cheap, still unstarted.

## Artifacts
- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic)
- Files touched: eval/mppi_sandbox/essps.py, eval/mppi_sandbox/tests/test_essps_mppi.py, docs/decisions.md, docs/deliberations.md
- TSV row appended: pending

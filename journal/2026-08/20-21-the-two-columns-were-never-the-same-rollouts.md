# The two columns were never the same rollouts

- **Cycle**: 2026-08-20 21:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: STATE #1 — buy one more paired cell (`dominance_holds()` has never had a chance to fail)
- **Phase**: P3
- **Status**: keep

## What I tried

- Picked STATE's #1, carried unspent for three cycles: harvest a **fourth** cell
  so `dominance_holds()` (2/2, unfalsified by construction) could finally fail.
  Chose `cafe_cut_in_v0`; the `clearance` ordering is a 5-way tie at `6/8` and
  orders nothing (D-387), so STATE's own first-named candidate decided it.
- Harvested 64 rollouts (`270.8 s` — cut-in is **2.3x** convoy's 118 s) computing
  TVaR₀.₉ and `cte_max` from the *same* `|cte|` array, on the reasoning that both
  are functionals of one trajectory and finding #1's "nothing was bought"
  property should therefore extend to a new scene for one harvest instead of two.
- Ran a construction check **before** pinning anything: recompute the already-pinned
  `cafe_head_on_v0` `cte_max` column, seed 0, and compare. It disagreed on 8/8 arms.
- Did not pin the fourth cell. Spent the remaining budget establishing why.

## What worked / what failed

- **The check failed and that is the cycle's result.** Each pinned column is
  reproduced by exactly one construction and by neither the other, on
  `cafe_head_on_v0` seed 0, all eight arms:

  | column | `retake` (`lam=OPERATING_LAM` + `ISOLATION`) | `run_scenario` defaults |
  |---|---|---|
  | `TVAR_ENSEMBLE_THIRD` | **8/8** | 0/8 |
  | `SEED_ENSEMBLE` (`cte_max`) | 0/8 | **8/8** |

  So `tail_mean` finding #1's load-bearing sentence — *"the same rollouts.
  Nothing was bought."* — is not established. The columns share scene, arm set
  and seed set; they do not share rollouts. A structural fingerprint agrees:
  `risk_mppi`/`frozen_risk_mppi` are bit-identical under the isolation kwargs
  and **differ** in the `cte_max` pin.
- **Why no guard caught it**: `tail_mean.drift()` compares the two columns' *arm
  names* and never their values, and nothing re-derives across the module
  boundary. Recorded as **Q-175**; `dominance_holds()` is now a comparison of two
  experiments, not two observables on one set of runs.
- **Separately, a stale census with a live consequence (D-389)**: D-388 bought
  `cafe_head_on_v0`'s `cte_max` and pinned it in `excursion_seed_width` but never
  added the cell to `aa_calibration.CALIBRATED`. Every floor function reached it
  immediately (`_ensemble` reads that dict), so it was graded at `3.12x` while
  the module owning the column verdict kept reporting `cte_max` clears `0 of 2`.
  Registering it gives `(3, 1, 1)`.
- **That correction refutes D-372 finding #1's population split.** `cte_max` now
  reaches `3.12x` (head-on) while `clearance` falls to `2.44x` (cut-in) — the best
  cross-track row **outranks** the worst clearance row, so no threshold separates
  the columns. What survives is a majority tendency, not a partition.
- `drift()` could not have caught this either: it checks `FLOOR_VERDICT` against
  `CALIBRATED`, both hand-typed, so a cycle that forgets a cell forgets it in
  both and they agree *while jointly wrong*.

## North-star delta

- **First non-zero movement in 16 cycles, and it is negative-signed**: two claims
  the branch has been building on are now bounded rather than extended. The
  cross-track column grades on 1 of 3 scenes, not 0 of 2; the column/scene split
  that D-372 established does not survive its eighth row.
- No planner behaviour changed. `cte_max` clearing on `cafe_head_on_v0` at `3.12x`
  is the first evidence on this branch that worst-case excursion is gradeable at
  8 seeds *at all* — which is the observable 경로추종 actually cares about.

## Key learnings

- **A census that is audited only against a hand-typed twin cannot detect a
  shared omission.** `FLOOR_VERDICT` vs `CALIBRATED` agreed for two cycles while
  both omitted the same cell. The audit has to run against a population the
  census does not derive from — here, the harvest itself.
- **Checking the construction before pinning cost 25 s and saved a wrong pin.**
  Had I pinned the cut-in cell on the strength of "both columns from one
  trajectory", I would have written a fourth `COMPARABLE_CELLS` row that is not
  comparable to the three above it, and `dominance_holds()` would have gained a
  member that makes it *more* wrong while looking better-evidenced.
- Buying data was the plan and reading the data already bought was the result.
  Two of the last four cycles have now found their answer in a pin nobody
  re-read (D-385's seven-way tie, this cycle's unregistered cell).

## Recommended next 1–3 priorities

1. **Answer Q-175**: decide whether the `cte_max` column is re-harvested at the
   TVaR operating point, or `TVAR_ENSEMBLE` re-harvested at `run_scenario`
   defaults. One column must move; they cannot both stay. ~64 rollouts either way.
2. **Then** pin the fourth cell — the `cafe_cut_in_v0` harvest is measured and
   reusable once the operating point is settled (values in this cycle's Q-175 entry).
3. Re-read `tail_mean`'s finding #1/#2 prose against whatever Q-175 decides; the
   `2.64x`/`0.96x` contrast is quoted in three modules and one D-entry.

## Artifacts

- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic)
- Files touched: `eval/mppi_sandbox/aa_calibration.py`, `eval/mppi_sandbox/tail_mean.py`, `eval/mppi_sandbox/tests/test_aa_calibration.py`
- TSV row appended: yes

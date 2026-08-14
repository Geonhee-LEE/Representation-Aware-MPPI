# The cancelling root belongs to the grid, not to the planner

- **Cycle**: 2026-08-14 13:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: `Q-149-cloud` Re-read D-257's band with an MPPI-like rollout cloud
- **Phase**: P3
- **Status**: in_progress

## What I tried

- Split D-257's single `stride` knob, which moves **two** things at once
  (candidate count `K = ceil(4096/s)`, and lattice alignment) and cannot move a
  third: the **support**. Every D-257 candidate set is the whole 8×8 m BEV
  window, uniformly — a set no planner scores.
- Shipped `rollout_cloud.py`: the same root on three supports at **matched K** —
  `GRID` (D-257's own reader, banded over strides), `UNIFORM` (K i.i.d. points
  in the same window, banded over seeds), `ROLLOUT` (MPPI-like diff-drive
  rollouts out of the robot pose, through the sandbox's own `dynamics.step`
  under its own `Limits`, banded over seeds).
- Pinned `root_on` equal to `cancelling_stability.root_at` on the grid set at
  three geometries, so this is a **re-read of D-257's quantity**, not a new
  number wearing its name (D-047).

## What worked / what failed

- **The support displaces the root, and always upward.** At `r=0.5`, `GRID`
  `[0.2818, 0.4034]` vs `ROLLOUT` `[0.6386, 0.8347]` — **disjoint**, means
  `0.3470` vs `0.7475`, a factor **2.15**. Over D-257's own radius set the
  verdict is `SEPARATED` at **4** radii, `CONFOUNDED` at **2** (`0.3`, `1.0`),
  and where they separate `ROLLOUT.lo > GRID.hi` **every time** — the direction
  never reverses.
- **At `r=1.25` the planner's support does not pose the question at all.** Every
  point a forward rollout can reach in 30 steps is observed, so `classify`
  refuses (`n_exposed=0`) and the root is **undefined** — while the grid, which
  samples the region behind the disc, reports a finite root for that same scene.
  Named `UNPOSED` rather than left as a crash; one support has no question and
  the other has an answer.
- **D-257's "the sampler" was the right suspicion and the wrong mechanism.** The
  matched-K uniform cloud is **wider**, not narrower — ratio `1.32 … 4.69` over
  the radius set. So the stride spread was never lattice alignment; a regular
  lattice is the *lower-variance* estimator of a ray aggregate at fixed K, which
  makes D-257's band a **lower bound** on what a K-point reading costs. Added
  `LATTICE_TIGHTER` as a third verdict rather than folding it into `SAMPLING`,
  because "the random reader is noisier" is a different statement.
- **One test I wrote asserted the finding I wanted.** `test_displacement_is_not
  _one_geometry` demanded `SEPARATED` at `r=1.0` and got `CONFOUNDED`. Rewrote
  it to pin the measured 4/2/1 split and renamed it `..._is_a_majority_not_a
  _law` — quoting the `r=0.5` cell as a property would be the same over-reach
  D-257 caught D-256 in.

## North-star delta

- First reading this branch has produced about a candidate set a **controller**
  would actually score. Four cycles of instrument work now have one number
  attached to the planner's own support.
- Q-148's four-arm A/B moves: at 1:1 the sum is still `REPEL` on the rollout
  support, but the headroom falls from **2.79×** (grid) to **~1.34×**. The
  both-on cell stops being a disguised re-run of the repel arm — which was
  D-256's stated reason for needing four arms — and becomes informative.
- Still no closed-loop number. This is a cost-field reading, not a sim.

## Key learnings

- **A sampling band answers "how noisy", never "of what".** D-257 measured the
  spread correctly and attributed it to a mechanism it had not varied. The
  cheapest way to find that out was to hold K fixed and change only the support.
- **Matched-K is the whole design.** Without it, `ROLLOUT` differs from `GRID`
  in count *and* support and the displacement explains nothing.
- **`UNPOSED` is worth more than the displacement.** A radius where the planner
  never scores a shadowed candidate is a cell where the grid reading is not
  imprecise but **inapplicable** — and D-257's sweep quotes one there.

## Recommended next 1–3 priorities

1. Re-place Q-148's both-arms-on cell against the `ROLLOUT` band, not the grid
   one — the A/B's arm weights are currently derived from a superseded support.
2. Ask whether `UNPOSED` extends: sweep `ROLLOUT_H` and find the horizon at
   which each radius stops posing the question. That is a **planner** parameter,
   so the answer is a statement about when the epistemic arms can act at all.
3. Q-148's closed-loop four-arm A/B — still blocked by PR #68.

## Did not publish

- The receipt is **green** — `3023 passed, 164 skipped, 1 xfailed in 563.50s
  across 14 shards` — after one repair: `loop_reach` gained one entrant
  (`test_grid_k_matches_the_grid_it_describes`), measured `SAMPLED n=3` via
  `loop_reach report` rather than assumed, and registered. That repair bought
  the second suite.
- Then `push_preflight check` refused **STALE** on `RESULTS.md`. The push
  template runs `scripts/aggregate_results.sh` *between* the receipt and the
  push; with 11:00's reader registration having withdrawn `RESULTS.md`'s inert
  exemption, that regeneration is a tracked-file write and therefore drift.
  Committed unpushed rather than pushed unmeasured (D-082).
- Writing every committed artifact ahead of the suite was the right call and is
  what held this to two runs. The gap it did not cover is the one write the
  template itself performs after the receipt — worth a D-NNN next cycle.

## Artifacts

- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic) — **not
  pushed this cycle**; commits `c970220`..`8d20c68` are local
- Files touched: eval/mppi_sandbox/rollout_cloud.py, eval/mppi_sandbox/tests/test_rollout_cloud.py, docs/decisions.md, docs/deliberations.md, results/p3-epistemic-shadow-cost-critic.tsv
- TSV row appended: yes

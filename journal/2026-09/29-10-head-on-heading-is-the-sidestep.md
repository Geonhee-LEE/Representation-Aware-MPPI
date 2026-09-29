# head_on heading residual is the sidestep; the gated heading price worsens it

- **Cycle**: 2026-09-29 10:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: `3c4c5d39` [sandbox] knee+shape 아래 heading_err_rms_max 공략
- **Phase**: P6 (TODO tagged P5)
- **Status**: keep

## What I tried
- Strand reading rc=1 (`23ebbc1`). Started the discharge suite, measured head_on in `/tmp` meanwhile (n=16, w0 vs w64+v_gate 0.45). The measurement took ~1 min, so I stopped the suite and folded a pin into this cycle. One suite covers both commits and leaves no new strand.
- Added `test_head_on_heading_is_proximity.py` (seeds 3/5, 4 integrations); lam census forwards 46→47, total 252→253.

## What worked / what failed
- D-499 holds on head_on: rho < 0 on 16/16 (-0.37 to -0.81), peak clearance 0.44-1.38 m, and near-pedestrian steps (~18% of the run) carry 53-73% of the squared error. With those steps zeroed, rms is 0.22-0.29 on 16/16.
- head_on's yaml declares no heading limit ("may sidestep"), so "16/16 heading fail" used a ceiling borrowed from crossing.
- w64+gate raises head_on heading rms on 15/16 (median 0.42→0.54); seeds 3/5 reach 0.91/1.03 with 98% of it near the pedestrian.

## North-star delta
- No controller change. The pending default-change policy call now has a cross-scene cost: the crossing heading gain reverses on head_on.

## Key learnings
- A heading fail on a scene that prescribes sidestepping is the sidestep, not a tracking defect. Check the scene's own acceptance keys before borrowing thresholds.
- When the `/tmp` measurement is fast, stop the discharge suite and commit before it. That breaks the one-strand-per-cycle chain.

## Recommended next 1–3 priorities
1. Look at why seeds 3/5 blow up late (peak_t ~5.3 s) under the gated price. Check whether the robot re-crosses the path behind the pedestrian.
2. Scope the heading price to static obstacles, or gate it on the obstacle's relative velocity, then re-run crossing + head_on.
3. User policy call now carries the head_on regression.

## Artifacts
- PR: none (PR #67 closed by user 09-21). Pushed to branch.
- Files touched: eval/mppi_sandbox/tests/test_head_on_heading_is_proximity.py, eval/mppi_sandbox/tests/test_default_lam_sites.py, docs/decisions.md, journal/2026-09/29-10-head-on-heading-is-the-sidestep.md, results/p3-epistemic-shadow-cost-critic.tsv
- TSV row appended: yes

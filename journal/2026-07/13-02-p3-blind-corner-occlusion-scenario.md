# P3 blind-corner occlusion scenario + sightline metric (Q-017 test-bed)

- **Cycle**: 2026-07-13 02:00 KST
- **Branch**: `autoresearch/p3-blind-corner-occlusion-scenario`
- **TODO**: `p3-blind-corner` Blind-corner occlusion scenario (STATE next-actionable #1)
- **Phase**: P3
- **Status**: keep

## What I tried
- Built `eval/scenarios/cafe_blind_corner_v0.yaml`: a wall of r=0.3 discs at
  x=2.5 the robot rounds at the top, descending to a goal *behind* it, with a
  declared `blind_pocket (3.0,-0.4)` that stays occluded during the approach.
- Added `eval/mppi_sandbox/occlusion.py` — `sightline_reveal` (arclength /
  distance a hidden point first comes into view) + `occlusion_exposure`
  (mean σ of the pose the robot is about to enter). EPISTEMIC-channel scalars.
- Added `tests/test_blind_corner.py` (5 tests + 1 self-activating forward
  contract for `w_epist`). Empirically iterated the geometry before asserting.

## What worked / what failed
- Scenario is valid + solvable: pocket σ=1 the whole approach, baseline
  `stock_mppi` passes acceptance (cte_rms 0.175, clearance +0.145, no hit).
- Sightline-reveal is real and non-trivial: pocket first visible at **2.8 m of
  the 5.3 m path**, robot 1.4 m away — a path-dependent "how blind" number.
- **Executed-path occlusion exposure is ~0** for the smooth oracle MPPI. First
  geometries (wall-top arc, narrow gaps) either gave 0 exposure or sealed the
  corridor (timeout). The 0 is not a bug: a smooth path curves *around* the
  occluder, so its forward lookahead never enters the side-lying shadow.

## North-star delta
- + First occlusion test-bed + EPISTEMIC-channel metric in the sandbox — the
  '가려진 obstacle' class now has a scenario and a scalar to score, where
  before it had neither (the exact STATE bottleneck).
- No closed-loop north-star metric *moved* yet — this builds the surface on
  which the epistemic critics will be scored, not a controller win.

## Key learnings
- The additive shadow cost's inertness is deeper than Q-017's single-obstacle
  case: for *any* smooth path, occluded cells sit off the forward trajectory,
  so charging executed rollout points for σ has little to bite on. The real
  unblock is a **visibility-gated obstacle cost** — make `stock_mppi` blind to
  unobserved obstacles so epistemic caution changes collision outcomes, not
  just approach blindness. That, plus a scripted obstacle emerging from the
  pocket, is the scenario where σ finally moves clearance/near-miss.
- Sightline-reveal (not executed-path exposure) is the metric to score
  epistemic controllers on: it is non-zero, path-dependent, and rewards
  seeing sooner.

## Recommended next 1–3 priorities
1. **Visibility-gated obstacle cost** in a sandbox controller variant (avoid
   only *observed* obstacles) → the blind pocket becomes a genuine hazard the
   oracle baseline hits and an epistemic-aware controller avoids. Unblocks a
   real Q-017 resolution with a clearance/near-miss delta.
2. **Blind-corner v1**: scripted obstacle emerging from the pocket once the
   robot commits — couples DYNAMIC risk with EPISTEMIC caution.
3. Once PR #67 (w_epist) lands, run the self-activating forward contract and
   measure sightline-reveal under `w_epist>0`.

## Artifacts
- PR: #68 (autoresearch/p3-blind-corner-occlusion-scenario)
- Files touched: eval/scenarios/cafe_blind_corner_v0.yaml, eval/mppi_sandbox/occlusion.py, eval/mppi_sandbox/tests/test_blind_corner.py, results/p3-blind-corner-occlusion-scenario.tsv
- TSV row appended: yes

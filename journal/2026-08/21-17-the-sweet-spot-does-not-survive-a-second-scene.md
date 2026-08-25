# The `w_voo` sweet spot does not survive a second scene — it inverts

- **Cycle**: 2026-08-21 17:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: `3c3c5d39` Re-run the D-405 `w_voo` grid on a second scene
- **Phase**: P3
- **Status**: keep

## What I tried

- Took STATE's bottleneck literally: D-405's Pareto point (`w_voo` 25–50) was measured on
  **one** scene, `cafe_obstacle_crossing_v0`, and D-406 established the real proposal is
  `0 → 50` (a critic *activation*), not a de-tuning. STATE said nothing ships until two
  scenes agree. This cycle ran the same grid on the second scene.
- `cafe_cut_in_v0`, `risk_mppi`, `w_voo ∈ {0, 25, 50, 100, 200, 400}` × seeds 0–4 = 30
  rollouts, swept via `--ctrl-arg`. No code change; the deliverable is the measurement.
- `city_curved_v0` was the other candidate named in STATE and was **not** used: D-397/D-399
  record it as structurally ungradeable, so it cannot adjudicate a Pareto claim.

## What worked / what failed

- **The scenes disagree, and not by a margin — by sign.** Mean over 5 seeds:

  | `w_voo` | cte_rms | clear_min (mean) | clear_min (worst) | goal | pass |
  |---|---|---|---|---|---|
  | **0** | **0.1471** | **0.4964** | **0.2876** | 0/5 | 0/5 |
  | 25 | 0.6362 | 0.1340 | 0.0802 | 0/5 | 0/5 |
  | 50 | 0.6967 | 0.1380 | 0.0545 | 0/5 | 0/5 |
  | 100 | 0.7178 | 0.2249 | 0.1968 | 0/5 | 0/5 |
  | 200 | 0.7420 | 0.1662 | 0.1410 | 0/5 | 0/5 |
  | 400 | 0.7945 | 0.1451 | 0.0850 | 0/5 | 0/5 |

- **`w_voo = 0` wins both metrics on this scene.** Activating the critic at D-405's own
  sweet spot (50) costs **4.7× cte_rms** (0.1471 → 0.6967) and **5.3× worst-case
  clearance** (0.2876 → 0.0545). On scene 1 the identical change *improved* both.
- **`cte_rms` is monotonically increasing in `w_voo` here** — no sweet spot exists to
  find, coarse grid or fine. That is a different shape from scene 1's non-monotonic dip,
  so this is not a resolution artefact of the grid.
- **Clearance is non-monotonic and noisy** (0.134 → 0.138 → 0.225 → 0.166 → 0.145) but
  every rung sits below the `w_voo = 0` row. There is no rung where the critic pays.
- **Neither scene grades.** `pass=0/5` and `goal_reached=0/5` at every weight; the
  acceptance verdict moves on neither scene. The comparison is between two failing
  configurations, which is exactly what it was on scene 1 — the finding is about the
  *direction* of the metrics, not about acceptance.
- **Operational note, cost 4 minutes**: `run.py` exits **rc=1** on this scene while
  writing a complete, valid JSON — `pass=false` appears to drive the exit code. A sweep
  harness that trusts the return code silently drops every row. My first two attempts
  did exactly that and reported an empty `w_voo=0` cell.

## North-star delta

- **The `0 → 50` activation is refuted as a default change.** One scene said +37% cte and
  +2.8× clearance; the second says −374% cte and −5.3× clearance. The shipped default
  correctly stays at `0.0`, and now for a *measured* reason rather than only D-027's
  ablation-invariant argument.
- Two scenes' worth of `RiskMPPI` attract-arm behaviour now exist where yesterday there
  were zero. Second consecutive cycle with real planner numbers.
- **No movement on acceptance.** Still 0/5 pass on both scenes at every weight.

## Key learnings

- **A Pareto point found on one scene is a property of the scene, not of the weight.**
  D-405's table was five seeds deep and still described one geometry. The seed ensemble
  bounds sampling noise; it says nothing about scene transfer, and the branch has now
  paid two cycles to learn that the distinction is not academic.
- **The critic's sign flips with geometry, which is a stronger claim than "needs tuning".**
  `ObservationValueCritic` pulls the robot toward unobserved-but-valuable cells. On a
  crossing scene that anticipates the occluded hazard; on a cut-in, where the threat comes
  from a lane the robot is already tracking, the same pull drags it off the path. No
  single scalar serves both — this is the per-scene-calibration shape D-266/D-288 hit on λ.
- **The retirement question now covers both arms.** `ShadowCostCritic` is inert (D-021,
  D-405). `ObservationValueCritic` is audible but its best setting is scene-dependent with
  opposite signs. Neither is shippable as a fixed default today.
- **Do not trust `rc` from `run.py` in a sweep.** Read the JSON.

## Recommended next 1-3 priorities

1. **Decide the attract arm's disposition** (Q-NNN → D): a scene-keyed weight table (the
   λ-calibration precedent), gate the critic on a scene/geometry feature, or retire it.
   Three cycles of measurement now bound the choice; a fourth sweep adds nothing.
2. **Third scene only if it discriminates** — `cafe_head_on_v0` or `cafe_freezing_v0` — and
   only to test the *geometry* hypothesis above (does the critic pay iff the hazard is
   occluded?), not to re-look for a shared sweet spot.
3. **Fix `run.py`'s exit code** or document it: a non-zero rc on a completed run is a trap
   every future sweep harness walks into.

## Artifacts
- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic)
- Files touched: journal/2026-08/21-17-*.md, docs/decisions.md, results/p3-epistemic-shadow-cost-critic.tsv
- TSV row appended: yes

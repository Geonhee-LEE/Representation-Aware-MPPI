# safe_control offline harness

Thin wrapper around [`tkkim-robot/safe_control`](https://github.com/tkkim-robot/safe_control) — gives us a **seconds-per-iteration** Python playground for CBF-QP / MPC-CBF / gatekeeper / C3BF / DPCBF controllers, alongside our minutes-per-iteration Gazebo+Nav2 stack.

## Why it matters

- Iterate controller logic 60-100× faster than Gazebo for ablation cycles
- Reuse safe_control's production-grade CBF implementations instead of re-implementing
- Run our `eval/path_tracking_metrics.summary()` directly on captured trajectories
- Fail-fast for controller bugs before paying full Gazebo bring-up cost

## Reference location

`safe_control` is cloned (NOT vendored) to:
```
~/.local/share/representation-aware-mppi/refs/safe_control
```
with an isolated `uv` venv at `refs/safe_control/.venv`. License of safe_control is currently unstated upstream — we treat it as inspiration/use-in-place rather than fork. Re-clone via `scripts/fetch_refs.sh`.

## First-run smoke

Verified 2026-05-25 on this machine:

```
$ source ~/.local/share/representation-aware-mppi/refs/safe_control/.venv/bin/activate
$ cd ~/.local/share/representation-aware-mppi/refs/safe_control
$ MPLBACKEND=Agg python examples/test_tracking.py --model du
=====   Tracking finished    =====
Success!

$ MPLBACKEND=Agg python examples/evade/test_evade.py
*** GOAL REACHED at step 320 ***
  Collision: NO    Goal Reached: YES
  Nominal: 292 (91.0%)    Backup: 29 (9.0%)
  ✓ TEST PASSED
```

Both `test_tracking` (waypoint following) and `test_evade` (dynamic obstacle avoidance with gatekeeper backup) work out-of-the-box.

## Available models

| Short | Class | Notes |
|---|---|---|
| `si` | SingleIntegrator2D | 2-state, easiest |
| `di` | DoubleIntegrator2D | 4-state |
| `un` | Unicycle2D | kinematic, common nav baseline |
| `du` | DynamicUnicycle2D | dynamic (acceleration inputs) — **default** |
| `kb` | KinematicBicycle2D | car-like |
| `quad` | Quad2D | planar quadrotor |
| `quad3d` | Quad3D | 3D quadrotor |

For our Jackal-class differential robot, `un` and `du` are direct matches.

## Available algorithms

`--algo cbf_qp` (single-step QP) or `--algo mpc_cbf` (predictive). Multiple CBF formulations under `dynamic_env/` for moving obstacles: `C3BF`, `DPCBF`.

## Integration plans (filed as issues)

- **#30** safe_control evaluation as offline playground — analysis doc
- (follow-up) wire C3BF/DPCBF formulation into our `nav2_mppi_controller` as a candidate safety critic
- (follow-up) export safe_control's per-step state trajectory + our reference path → `eval.path_tracking_metrics.summary()` → `runs/safe_control_*.json` to compare against our Gazebo Nav2 numbers

## Quick commands (smoke + sanity)

```bash
# Re-clone or update
bash scripts/fetch_refs.sh

# Run waypoint tracking with DynamicUnicycle + MPC-CBF
bash eval/safe_control_harness/run_tracking.sh --model du --algo mpc_cbf

# Run dynamic obstacle evade
bash eval/safe_control_harness/run_evade.sh
```

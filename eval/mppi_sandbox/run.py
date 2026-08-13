# SPDX-License-Identifier: BSD-3-Clause
"""Closed-loop sandbox run: scenario yaml → trajectory → runs/<run_id>.json.

Emits the same JSON schema as eval/run_metrics.py (the Gazebo-side node),
plus sandbox-only fields (backend / controller / seed / clearance / pass) —
so sandbox and Gazebo numbers land in the same comparison tables.

CLI:
    python -m eval.mppi_sandbox.run eval/scenarios/cafe_straight_v0.yaml \
        --controller stock_mppi --seed 0 --run-id straight-sandbox-001
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

from eval.path_tracking_metrics import Goal, completion_percent, summary

from .controllers import make_controller
from .dynamics import Limits, step
from .freeze_price import freeze_duration
from .obstacles import min_clearance
from .scenario import Scenario, load_scenario

SIM_DT = 0.1
TIMEOUT_FACTOR = 4.0     # give MPPI 4× the scripted expected duration
ROBOT_RADIUS = 0.3       # Jackal-ish footprint circle
STOP_COMPLETION = 0.992  # margin above the 0.99 acceptance floor


def simulate(scenario: Scenario, controller, *, dt: float = SIM_DT,
             limits: Limits | None = None,
             max_steps: int | None = None) -> np.ndarray:
    """Run until the path is finished (arclength completion ≥ STOP_COMPLETION
    *and* within goal xy tolerance) or timeout. Returns (T, 6) trajectory.

    Completion-based stop (not first-goal-touch) so `completion_final`
    reflects actually finishing the reference path — the acceptance blocks
    demand completion ≥ 0.99 while goal_xy_tol is a looser 0.2 m.

    `max_steps` overrides the scenario-derived timeout. Default `None` keeps
    the shipped `expected_duration × TIMEOUT_FACTOR` cap, so every existing
    caller is bit-identical. Pass a smaller cap when the *question* is whether
    an arm is driving or frozen: that verdict is legible in ~1.5× the healthy
    run length, and paying the full 1000-step timeout to re-confirm it is the
    single largest line item in the suite's 145 s → 504 s growth. A truncated
    run is honest about being truncated — it simply does not reach the goal,
    so `ab.assert_all_reached` still refuses to score it.
    """
    xy_tol = float(scenario.acceptance.get("goal_xy_tol", 0.2))

    if max_steps is None:
        max_steps = int(np.ceil(scenario.expected_duration * TIMEOUT_FACTOR / dt))
    state = np.array([*scenario.start, 0.0, 0.0])        # v = omega = 0
    rows = [[0.0, *state]]
    for k in range(1, max_steps + 1):
        u = controller.command(state, (k - 1) * dt)
        state = step(state, u, dt, limits)
        rows.append([k * dt, *state])
        latest = np.array(rows[-1:], dtype=float)
        cp = completion_percent(latest, scenario.waypoints)[-1]
        dxy = np.linalg.norm(state[:2] - scenario.goal[:2])
        if cp >= STOP_COMPLETION and dxy <= xy_tol:
            break
    return np.array(rows, dtype=float)


def check_acceptance(acc: dict, metrics: dict, clearance: float) -> dict:
    """Evaluate the scenario acceptance block. Unknown keys -> 'skipped'.

    D-241: an unknown key becomes the *str* ``"skipped"``, and `run_scenario`
    computes `pass` over `[v for v in checks.values() if isinstance(v, bool)]`,
    so a declared criterion nobody implemented is dropped silently and the scene
    passes without being asked. `acceptance_coverage` sweeps for that, and it
    derives the graded set by *calling this function* rather than reading a copy
    of the table — so there is no second statement of it to go short (D-047).
    """
    rules = {
        "cte_rms_max": lambda v: metrics["cte_rms"] <= v,
        "cte_max": lambda v: metrics["cte_max"] <= v,
        "heading_err_rms_max": lambda v: metrics["heading_err_rms"] <= v,
        "completion_min": lambda v: metrics["completion_final"] >= v,
        "goal_reached": lambda v: metrics["goal_reached"] == int(v),
        "min_distance_to_obstacle": lambda v: clearance >= v,
        "collision": lambda v: int(clearance < 0.0) == int(v),
        # Declared by `cafe_freezing_v0` since the scene landed; wired by D-241.
        "freeze_duration_max": lambda v: metrics["freeze_duration"] <= v,
        # Declared by `city_figure8_v0` since the scene landed; the metric it
        # needs was already on every run (`summary()["jerk_lat"]`) and nothing
        # read it. Measured 2.72-2.95 over 3 seeds against the declared 8.0, so
        # wiring grades a silent criterion without flipping a scene (D-242).
        "jerk_lat_max": lambda v: metrics["jerk_lat"] <= v,
        # Declared by `cafe_freezing_v0` since the scene landed; ungraded until
        # first-arrival time existed, because `duration_s` is the whole sim and
        # not the arrival. A run that never reaches the goal has
        # `time_to_goal is None` and **fails** this rule — never-arrived is the
        # worst possible time-to-goal, not an absent measurement.
        "time_to_goal_max": lambda v: (metrics["time_to_goal"] is not None
                                       and metrics["time_to_goal"] <= v),
    }
    checks = {}
    for key, target in acc.items():
        if key in ("goal_xy_tol", "goal_yaw_tol"):       # params, not checks
            continue
        checks[key] = bool(rules[key](target)) if key in rules else "skipped"
    return checks


def run_scenario(scenario_path: str | Path, *, controller: str = "stock_mppi",
                 seed: int = 0, run_id: str | None = None,
                 out_dir: str | Path | None = None,
                 **controller_kwargs) -> dict:
    scenario = load_scenario(scenario_path)
    ctrl = make_controller(controller, scenario, seed=seed,
                           robot_radius=ROBOT_RADIUS, **controller_kwargs)
    traj = simulate(scenario, ctrl)

    acc = scenario.acceptance
    metrics = summary(
        traj, scenario.waypoints,
        target_speed=scenario.target_speed,
        goal=Goal(*scenario.goal),
        xy_tol=float(acc.get("goal_xy_tol", 0.2)),
        yaw_tol=float(acc.get("goal_yaw_tol", 0.3)),
    )
    metrics["freeze_duration"] = freeze_duration(traj, scenario.waypoints)
    clearance = min_clearance(traj, scenario.obstacles, ROBOT_RADIUS)
    checks = check_acceptance(acc, metrics, clearance)
    hard = [v for v in checks.values() if isinstance(v, bool)]

    result = {
        "run_id": run_id or f"{scenario.name}-sandbox",
        "started_at": datetime.now(timezone.utc).astimezone().isoformat(),
        "backend": "mppi_sandbox",
        "scenario": str(scenario_path),
        "world": "sandbox",
        "robot": "diffdrive_circle_r0.3",
        "controller": controller,
        "controller_kwargs": controller_kwargs,
        "seed": seed,
        "target_speed": scenario.target_speed,
        "duration_s": float(traj[-1, 0]),
        "metrics": metrics,
        "min_obstacle_clearance": clearance,
        "collision": bool(clearance < 0.0),
        "acceptance": checks,
        # Named, not merely absent. `"skipped"` sitting in `acceptance` reads as
        # *checked* to anyone scanning the artifact — that is the whole of D-241.
        # This list is the same information stated so it cannot be misread, and
        # it is what makes a scene's ungraded criteria visible in the run JSON
        # rather than only under a grep of the rules table.
        "ungraded": sorted(k for k, v in checks.items() if not isinstance(v, bool)),
        "pass": bool(all(hard)) if hard else None,
    }
    if out_dir is not None:
        out = Path(out_dir)
        out.mkdir(parents=True, exist_ok=True)
        (out / f"{result['run_id']}.json").write_text(
            json.dumps(result, indent=2) + "\n")
    return result


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("scenario", help="path to eval/scenarios/*.yaml")
    ap.add_argument("--controller", default="stock_mppi")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--run-id", default=None)
    ap.add_argument("--out-dir", default="runs")
    ap.add_argument("--ctrl-arg", action="append", default=[],
                    metavar="KEY=VALUE",
                    help="controller kwarg, e.g. --ctrl-arg w_risk=15")
    args = ap.parse_args(argv)
    kwargs = {}
    for pair in args.ctrl_arg:
        key, value = pair.split("=", 1)
        try:
            kwargs[key] = float(value)
        except ValueError:
            kwargs[key] = value
    result = run_scenario(args.scenario, controller=args.controller,
                          seed=args.seed, run_id=args.run_id,
                          out_dir=args.out_dir, **kwargs)
    print(json.dumps(result, indent=2))
    return 0 if result["pass"] in (True, None) else 1


if __name__ == "__main__":
    raise SystemExit(main())

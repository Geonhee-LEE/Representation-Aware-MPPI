# SPDX-License-Identifier: BSD-3-Clause
"""`freeze_duration` — the acceptance key `cafe_freezing_v0` declares and no
code computed.

STATE's bottleneck for this cycle reads *"the freeze is detected but never
priced."* The detection half is real but **indirect**: `three_arm.ArmReading`
infers a freeze from a drop in completion (`d_reached < 0`) and reports
`BOUGHT_WITH_FREEZE`, and `paired_step` refuses clearances taken from
non-completing arms. Both are *consequence* readings — an arm that stalls for
three seconds and still reaches the goal is invisible to them.

The direct measure was specified fifteen weeks ago and never implemented.
`eval/scenarios/cafe_freezing_v0.yaml` carries::

    acceptance:
      freeze_duration_max: <2 s>   # never stopped >2s without progress
    success_metric_priority:
      - goal_reached
      - freeze_duration_max        # <- second, ahead of time_to_goal_max

and `freeze_duration` appears **nowhere else in the tree** — not in
`path_tracking_metrics.summary`, not in `run.check_acceptance`'s `rules`. That
last absence is the sharp half: `check_acceptance` maps unknown keys to the
string `"skipped"`, and `run_scenario` computes `pass` over
`[v for v in checks.values() if isinstance(v, bool)]`. A string is not a bool,
so the scene's **second-priority success criterion was silently dropped from
its own pass/fail** — `cafe_freezing_v0` has been passing without it ever being
asked. The scene whose entire reason for existing is the freezing-robot failure
mode was not testing for freezing.

This module computes it. It does **not** price the freeze into any planner —
that is the mechanism-grade successor, and D-021's lesson (do not ship an
unmeasured cost term) is the reason it does not land in the same cycle as its
own metric. A cost term shipped against no freeze number would be graded by the
same completion proxy it is supposed to improve on.

Definition
----------
Progress is measured **along the reference path**, not as ground speed. A robot
pirouetting in place or arcing around a pedestrian has ground speed and no
progress, and the yaml comment says *"stopped without progress"*, not
*"stopped"*. Arclength is `completion_percent × path_length`, so the along-path
speed at step k is `(s[k] - s[k-1]) / dt`.

A step is **stalled** when that speed falls below :data:`STALL_SPEED_MPS`.
`freeze_duration` is the longest contiguous run of stalled steps, in seconds.

The threshold is not a new tuning knob: `0.08 m/s` is `StockMPPI`'s shipped
`creep_speed`, described in its own source as *"floor so the robot finishes the
path"*. Borrowing it means "stalled" is defined as *slower than the controller's
own definition of still-making-progress*, rather than as a constant this module
invented. `test_freeze_duration.py` pins the two together so a future change to
one cannot silently decouple them.

Known and deliberate: the **startup transient counts**. The robot begins at
`v = 0` and needs a few steps to reach creep, so a healthy run shows a short
freeze at t=0. That is honest — it is genuinely a stalled interval — and it is
bounded well under the 2.0 s acceptance threshold. Reporting a number that
excluded it would require a start-of-run special case whose only purpose is to
make the metric look better than the trajectory.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from typing import Sequence

import numpy as np

from eval.path_tracking_metrics import completion_percent

#: Along-path speed below which a step counts as stalled [m/s].
#:
#: Equal to `stock_mppi.StockMPPIParams.creep_speed` by construction — see the
#: module docstring. Pinned by `test_stall_threshold_is_the_shipped_creep_floor`.
STALL_SPEED_MPS = 0.08

#: The scene that declares `freeze_duration_max`, and this module's subject.
FREEZING_SCENE = "eval/scenarios/cafe_freezing_v0.yaml"


def _path_length(path: np.ndarray) -> float:
    """Total arclength of the reference polyline [m]."""
    xy = np.asarray(path, dtype=float)[:, :2]
    return float(np.linalg.norm(np.diff(xy, axis=0), axis=1).sum())


def stalled_mask(traj: np.ndarray, path: np.ndarray, *,
                 stall_speed: float = STALL_SPEED_MPS) -> np.ndarray:
    """Per-step boolean: was along-path progress slower than `stall_speed`?

    Returns a `(T-1,)` mask — one entry per *step*, not per sample, since
    progress is a difference. An empty or single-row trajectory yields an empty
    mask (no step was taken, so no step stalled).
    """
    traj = np.asarray(traj, dtype=float)
    if traj.shape[0] < 2:
        return np.zeros(0, dtype=bool)

    s = completion_percent(traj, path) * _path_length(path)   # arclength [m]
    dt = np.diff(traj[:, 0])
    with np.errstate(divide="ignore", invalid="ignore"):
        v_along = np.where(dt > 0.0, np.diff(s) / np.where(dt > 0.0, dt, 1.0),
                           0.0)
    return v_along < stall_speed


def _longest_run(mask: np.ndarray, dt: np.ndarray) -> float:
    """Duration [s] of the longest contiguous True run, weighted by step dt."""
    best = run = 0.0
    for stalled, step_dt in zip(mask, dt):
        run = run + float(step_dt) if stalled else 0.0
        best = max(best, run)
    return best


def freeze_duration(traj: np.ndarray, path: np.ndarray, *,
                    stall_speed: float = STALL_SPEED_MPS) -> float:
    """Longest contiguous stalled interval [s]. The scene's acceptance key."""
    traj = np.asarray(traj, dtype=float)
    mask = stalled_mask(traj, path, stall_speed=stall_speed)
    if mask.size == 0:
        return 0.0
    return _longest_run(mask, np.diff(traj[:, 0]))


def freeze_duration_before(traj: np.ndarray, path: np.ndarray,
                           arrival: float | None, *,
                           stall_speed: float = STALL_SPEED_MPS) -> float:
    """:func:`freeze_duration` restricted to `t <= arrival` — the freeze reading.

    `freeze_duration` scans the **whole** trajectory, and the scenes here keep
    simulating after the goal is reached, so a run that arrives and then sits
    still scores an enormous "freeze" for doing what a finished run should do.
    On `cafe_freezing_v0` that is not a small correction: the post-arrival share
    of the whole-trajectory reading is 99.1-99.9 % across every arm x seed cell
    D-248 measured.

    `arrival = None` means the run never arrived, and then the two readings
    **coincide by construction** — with no arrival there is no post-arrival
    phase to exclude. That is a deliberate identity rather than a convention
    that could be mistaken for a measurement.

    This lives here, beside `freeze_duration`, because two callers need it
    (`arrival_spread.stall_split` and `freeze_weight.sweep`) and a truncation
    written twice is a truncation that can disagree with itself. Both readings
    come out of the *same* function given different rows, so `before` and
    `whole` cannot differ by anything except the rows.
    """
    traj = np.asarray(traj, dtype=float)
    if arrival is None:
        return freeze_duration(traj, path, stall_speed=stall_speed)
    head = traj[traj[:, 0] <= arrival]
    if head.shape[0] < 2:
        return 0.0
    return freeze_duration(head, path, stall_speed=stall_speed)


@dataclass(frozen=True)
class FreezeProfile:
    """One arm's freeze reading on one scene."""

    arm: str
    longest: float          # [s] the acceptance quantity
    total: float            # [s] all stalled time, not just the longest run
    episodes: int           # number of distinct stalled intervals
    duration: float         # [s] run length, for denominating `total`
    reached: bool

    @property
    def stalled_fraction(self) -> float:
        return self.total / self.duration if self.duration > 0 else float("nan")

    def exceeds(self, limit: float) -> bool:
        return self.longest > limit

    def __str__(self) -> str:  # pragma: no cover - reporting sugar
        return (f"{self.arm:12s} longest {self.longest:5.2f}s  "
                f"total {self.total:5.2f}s ({self.stalled_fraction:4.0%})  "
                f"episodes {self.episodes:2d}  "
                f"reached {'yes' if self.reached else 'NO':3s}")


def profile_arm(scene: str, arm: str, *, seed: int = 0,
                stall_speed: float = STALL_SPEED_MPS,
                **controller_kwargs) -> FreezeProfile:
    """Simulate `arm` on `scene` and read its freeze profile."""
    from eval.mppi_sandbox.controllers import make_controller
    from eval.mppi_sandbox.run import ROBOT_RADIUS, simulate
    from eval.mppi_sandbox.scenario import load_scenario

    scen = load_scenario(scene)
    ctrl = make_controller(arm, scen, seed=seed, robot_radius=ROBOT_RADIUS,
                           **controller_kwargs)
    traj = simulate(scen, ctrl)

    mask = stalled_mask(traj, scen.waypoints, stall_speed=stall_speed)
    dt = np.diff(traj[:, 0]) if traj.shape[0] >= 2 else np.zeros(0)
    episodes = int(np.count_nonzero(mask & ~np.r_[False, mask[:-1]])) \
        if mask.size else 0
    cp = completion_percent(traj, scen.waypoints)[-1]

    return FreezeProfile(
        arm=arm,
        longest=freeze_duration(traj, scen.waypoints, stall_speed=stall_speed),
        total=float(dt[mask].sum()) if mask.size else 0.0,
        episodes=episodes,
        duration=float(traj[-1, 0]),
        reached=bool(cp >= 0.99),
    )


def main(argv: Sequence[str] | None = None) -> int:  # pragma: no cover - CLI
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--scene", default=FREEZING_SCENE)
    ap.add_argument("--arms", nargs="+",
                    default=["stock_mppi", "risk_mppi", "social_mppi"])
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--limit", type=float, default=2.0,
                    help="acceptance threshold [s] to grade against")
    args = ap.parse_args(argv)

    print(f"freeze_price — {args.scene} seed={args.seed} "
          f"stall<{STALL_SPEED_MPS} m/s along-path, limit {args.limit}s\n")
    for arm in args.arms:
        prof = profile_arm(args.scene, arm, seed=args.seed)
        flag = "EXCEEDS" if prof.exceeds(args.limit) else "ok"
        print(f"  {prof}  {flag}")
    return 0


if __name__ == "__main__":  # pragma: no cover - CLI
    raise SystemExit(main())

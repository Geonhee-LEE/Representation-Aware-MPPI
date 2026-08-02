# SPDX-License-Identifier: BSD-3-Clause
"""Seed × scene × speed A/B harness for closed-loop sandbox comparisons.

Three primitives were hand-rolled independently in three consecutive cycles
(2026-08-02 05:00 / 07:00 / 08:00), each time because a P3 result had just
died on the nuisance axis that primitive controls:

  * **seed** — `test_shadow_cost_seed_robustness.py`. A single-seed assertion
    shipped green for 20 days encoding a *false* Q-017 finding: seed 0 sat in
    a coincidence basin where two arms converge, and CI's newer numpy moved it
    out. Single-seed assertions about closed-loop behaviour are claims about
    an RNG stream, not about the controller.
  * **speed** — `test_visibility_gated_mppi.py` (PR #69). An unhandicapped
    blind arm ran 1.58× the oracle's realized speed, so "it collides more" was
    confounded with "it drives faster". `v_max` handicapping removes it.
  * **completion** — the `_reached_goal` guard, same file. A 2026-08-02 sweep
    produced a +1.53 m "berth" at p = 1.19e-07 that was entirely *freeze*
    (oracle d_goal 5.42 m on a 7 m path). Zero collisions and a wide berth are
    both purchasable by giving up early.

Q-030 proposes making the seed × scene × speed triple a hard precondition for
any reportable sandbox A/B. A precondition only holds if obeying it is cheap,
which is what this module is for — `seed_sweep` + `summarize` + `paired_delta`
are the three calls a compliant comparison needs.

Deliberately *not* here: p-values. Fisher/sign tests were run ad hoc in the
cycles above and belong with the P5 aggregator, not in a test-support module
whose numbers are asserted in CI.

Typical use::

    scen = load_scenario("eval/scenarios/cafe_blind_approach_v0.yaml")
    oracle = seed_sweep(scen, "stock_mppi", range(8))
    blind = seed_sweep(scen, "vg_mppi", range(8), v_max=0.30,
                       sensing_range=1.0)
    assert_all_reached(oracle, "oracle"); assert_all_reached(blind, "blind")
    assert summarize(blind).collisions > summarize(oracle).collisions
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Sequence

import numpy as np

from .controllers import make_controller
from .dynamics import Limits
from .obstacles import CircleObstacle, min_clearance
from .run import ROBOT_RADIUS, simulate
from .scenario import Scenario

# Trajectory column layout emitted by `simulate`: [t, x, y, yaw, v, omega].
COL_XY = slice(1, 3)
COL_V = 4

DEFAULT_SEEDS = range(8)


@dataclass(frozen=True)
class ArmRun:
    """One closed-loop run of one arm at one seed."""

    seed: int
    traj: np.ndarray
    clearance: float
    reached_goal: bool
    mean_speed: float

    @property
    def collided(self) -> bool:
        return bool(self.clearance < 0.0)


@dataclass(frozen=True)
class SweepStats:
    """Aggregate of a `seed_sweep`. `all_reached` is the admissibility flag."""

    n: int
    collisions: int
    collision_rate: float
    mean_clearance: float
    median_clearance: float
    min_clearance: float
    mean_speed: float
    all_reached: bool


def reached_goal(traj: np.ndarray, scenario: Scenario) -> bool:
    """Completion guard: did this arm actually finish the path?

    A safety comparison whose arms are not both at the goal is not a safety
    comparison. Assert this on every arm of every comparison, on the same run
    that scores safety — not on a separate one.
    """
    tol = float(scenario.acceptance.get("goal_xy_tol", 0.2))
    return bool(np.linalg.norm(traj[-1, COL_XY] - scenario.goal[:2]) <= tol)


def mean_speed(traj: np.ndarray) -> float:
    """Mean |v| actually realized. The quantity a `v_max` handicap must move.

    Realized speed, not `target_speed_mps` — the two are decoupled (measured
    2026-08-02 02:00), so a scenario's declared target is not evidence that
    two arms drove at comparable speeds.
    """
    return float(np.abs(traj[:, COL_V]).mean())


def run_arm(scenario: Scenario, controller: str, seed: int, *,
            v_max: float | None = None,
            obstacles: Sequence[CircleObstacle] | None = None,
            robot_radius: float = ROBOT_RADIUS,
            **controller_kwargs) -> ArmRun:
    """Simulate one arm at one seed and score it.

    `v_max` handicaps this arm only (all other `Limits` keep their defaults) —
    that is the speed control. `obstacles` overrides which obstacles clearance
    is scored against; the default is **every** obstacle in the scenario. Pass
    an explicit subset when the claim is about one specific hazard, and say so
    at the call site, because "clearance to the hazard" and "clearance to the
    nearest of anything" are different numbers on a multi-obstacle scene.
    """
    ctrl = make_controller(controller, scenario, seed=seed,
                           robot_radius=robot_radius, **controller_kwargs)
    traj = simulate(scenario, ctrl,
                    limits=Limits(v_max=v_max) if v_max is not None else None)
    scored = list(scenario.obstacles if obstacles is None else obstacles)
    return ArmRun(
        seed=seed,
        traj=traj,
        clearance=min_clearance(traj, scored, robot_radius),
        reached_goal=reached_goal(traj, scenario),
        mean_speed=mean_speed(traj),
    )


def seed_sweep(scenario: Scenario, controller: str,
               seeds: Iterable[int] = DEFAULT_SEEDS,
               **arm_kwargs) -> list[ArmRun]:
    """`run_arm` over a seed ensemble. Results stay seed-ordered so two sweeps
    over the same `seeds` are positionally paired (see `paired_delta`)."""
    return [run_arm(scenario, controller, s, **arm_kwargs) for s in seeds]


def summarize(runs: Sequence[ArmRun]) -> SweepStats:
    clr = np.array([r.clearance for r in runs], dtype=float)
    collisions = int((clr < 0.0).sum())
    return SweepStats(
        n=len(runs),
        collisions=collisions,
        collision_rate=collisions / len(runs) if runs else float("nan"),
        mean_clearance=float(clr.mean()),
        median_clearance=float(np.median(clr)),
        min_clearance=float(clr.min()),
        mean_speed=float(np.mean([r.mean_speed for r in runs])),
        all_reached=all(r.reached_goal for r in runs),
    )


def assert_all_reached(runs: Sequence[ArmRun], label: str) -> None:
    """Raise unless every seed of this arm finished. Call before scoring."""
    failed = [r.seed for r in runs if not r.reached_goal]
    if failed:
        raise AssertionError(
            f"{label}: seeds {failed} did not reach the goal — a safety score "
            f"from a non-completing arm is unusable (freeze buys clearance)")


def paired_delta(a: Sequence[ArmRun], b: Sequence[ArmRun]) -> np.ndarray:
    """Per-seed `a.clearance - b.clearance`. Requires identical seed order.

    Paired, not mean: a mean gap can be tail-driven by one seed (the #69
    finding was 15/24 paired at a mean gap that looked decisive).
    """
    if [r.seed for r in a] != [r.seed for r in b]:
        raise ValueError("arms were swept over different seeds — not pairable")
    return np.array([x.clearance - y.clearance for x, y in zip(a, b)])


def sign_counts(deltas: np.ndarray, tol: float = 1e-6) -> tuple[int, int, int]:
    """(favouring-a, favouring-b, tied) counts of a `paired_delta` vector.

    `tol` exists because bit-identical arms are a real and informative outcome
    here, not float noise — see the Q-017 seed-0 coincidence basin.
    """
    d = np.asarray(deltas, dtype=float)
    return (int((d > tol).sum()), int((d < -tol).sum()),
            int((np.abs(d) <= tol).sum()))

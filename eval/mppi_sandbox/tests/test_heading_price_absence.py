# SPDX-License-Identifier: BSD-3-Clause
"""D-440: the heading residual was **unpriced**, not mis-weighted.

Two sweeps went looking for the lever that moves `heading_err_rms` and both
came back with the same non-answer: D-430 (`w_speed`) and D-433 (`w_omega`)
each *reshuffled* which seeds sit on which side of the threshold without
shifting the distribution. D-433 concluded "the heading residual is not
reachable by effort weighting" and sent the next cycle looking for structure.

The structure is smaller than expected, and it is visible without running a
sim: **`StockMPPI._cost` never read `traj[..., 2]` at all.** The full stage
cost was cross-track (`w_path`), speed tracking (`w_speed`), rotation *rate*
(`w_omega`), the obstacle pair, a terminal goal-distance term, and the
progress price. Not one of those is the angle that
`eval.path_tracking_metrics.heading_error` scores — that one compares robot
yaw against the *path tangent*. `w_omega` prices how fast the robot is
turning; `w_path` prices how far off the line it is. A robot can sit exactly
on the path, turning slowly, pointed the wrong way, and pay nothing.

So the two failed sweeps were not evidence about cost *shape*. They were two
knobs that do not point at the metric, and "reshuffles rather than converts"
is precisely what an unrelated knob does to a noisy per-seed score. That
reading costs nothing and explains both results without either sweep having
been mis-run.

**This also disqualifies the experiment that was queued.** `research/feed.md`
04:00 (Müller & Worthmann 2017) suggested swapping the heading term's shape
from quadratic `w·e_theta**2` to something non-quadratic, on the theory that a
weight sweep cannot distinguish "underweighted" from "wrong shape". That
diagnostic presumes a heading term *exists* to reshape. Here there was none,
so the shape question is not yet askable — it becomes askable only after a
term exists and is shown to move the metric at all. The paper's caveat (3)
already warned that no functional form was verified from it; this file
introduces the plainest possible term (quadratic on the wrapped error) and
makes no claim that quadratic is the right shape.

`test_default_is_unpriced` is the load-bearing one: it holds position, speed
and yaw-rate fixed and sweeps *only* yaw, and at the shipped default the cost
does not move by even a float ulp. That is the bug, stated as an assertion.
"""

import numpy as np
import pytest

from eval.mppi_sandbox.controllers.stock_mppi import (
    MPPIParams, StockMPPI, _polyline_tangent_yaw, _wrap_pi)
from eval.mppi_sandbox.scenario import load_scenario

SCENARIO = "eval/scenarios/cafe_straight_v0.yaml"


@pytest.fixture(scope="module")
def scenario():
    return load_scenario(SCENARIO)


def _rollouts(scenario, yaws):
    """(K,H,5) rollouts identical in every state but yaw.

    Placed on the path itself so the cross-track term is constant across K and
    cannot be what moves the cost, and held at the scenario's target speed with
    zero yaw-rate so `w_speed` and `w_omega` are constant too. Whatever moves
    is then attributable to yaw alone.
    """
    path = scenario.waypoints[:, :2]
    a, b = path[0], path[1]
    seg = b - a
    step = seg / max(np.linalg.norm(seg), 1e-9) * 0.05
    H = 12
    xy = a[None] + step[None] * np.arange(1, H + 1)[:, None]      # (H,2)
    traj = np.zeros((len(yaws), H, 5))
    traj[..., :2] = xy[None]
    traj[..., 2] = np.asarray(yaws, dtype=float)[:, None]
    traj[..., 3] = scenario.target_speed
    traj[..., 4] = 0.0
    return traj


def test_default_is_unpriced(scenario):
    """At the shipped default, cost is exactly invariant to heading."""
    ctrl = StockMPPI(scenario, seed=0, params=MPPIParams())
    assert ctrl.p.w_heading == 0.0, "default must stay 0 (byte-identical runs)"

    yaws = [0.0, 0.4, -0.8, 1.6, np.pi]
    cost = ctrl._cost(_rollouts(scenario, yaws), 0.0)

    # Not `approx`: the branch is skipped entirely, so these are the same
    # additions in the same order and must agree bit-for-bit.
    assert len(set(cost.tolist())) == 1, (
        f"heading changed the cost at w_heading=0: {cost}")


def test_priced_when_weight_positive(scenario):
    """With the weight on, cost rises strictly with |wrapped heading error|."""
    ctrl = StockMPPI(scenario, seed=0, params=MPPIParams(w_heading=5.0))
    path = scenario.waypoints[:, :2]
    tangent = float(np.arctan2(path[1][1] - path[0][1],
                               path[1][0] - path[0][0]))

    offsets = [0.0, 0.2, 0.5, 1.0, 2.0]
    cost = ctrl._cost(_rollouts(scenario, [tangent + o for o in offsets]), 0.0)

    assert np.all(np.diff(cost) > 0.0), f"not monotone in |e_theta|: {cost}"
    # Aligned rollout pays the same as the unpriced controller — the term adds
    # zero at zero error rather than a constant offset that would silently
    # re-scale every other weight.
    base = StockMPPI(scenario, seed=0, params=MPPIParams())._cost(
        _rollouts(scenario, [tangent]), 0.0)
    assert cost[0] == pytest.approx(base[0], rel=1e-12)


def test_wrapping_is_symmetric_and_bounded(scenario):
    """A heading error of +pi-eps and -pi+eps cost the same, and pi is the max.

    Without the wrap, a robot pointed slightly clockwise of backwards would be
    charged ~4x one pointed slightly counter-clockwise of it, purely from the
    branch cut — an asymmetry the metric does not have.
    """
    ctrl = StockMPPI(scenario, seed=0, params=MPPIParams(w_heading=5.0))
    path = scenario.waypoints[:, :2]
    tangent = float(np.arctan2(path[1][1] - path[0][1],
                               path[1][0] - path[0][0]))

    eps = 0.05
    cost = ctrl._cost(
        _rollouts(scenario, [tangent + np.pi - eps, tangent - np.pi + eps]),
        0.0)
    assert cost[0] == pytest.approx(cost[1], rel=1e-9)


def test_tangent_matches_the_scored_metric(scenario):
    """`_polyline_tangent_yaw` reproduces `heading_error`'s reference angle.

    The term is only worth having if it prices the *same* angle the acceptance
    threshold scores. This pins the two together: if `heading_error` ever
    re-bases onto `yaw_target`, this fails rather than the cost quietly
    optimising a different quantity than the one being graded.
    """
    from eval.path_tracking_metrics import heading_error

    path = scenario.waypoints
    rng = np.random.default_rng(0)
    pts = path[:, :2].mean(axis=0) + rng.normal(0.0, 0.6, size=(24, 2))
    yaws = rng.uniform(-np.pi, np.pi, size=24)

    mine = _wrap_pi(yaws - _polyline_tangent_yaw(pts, path[:, :2]))

    # heading_error consumes (t, x, y, yaw) rows.
    rows = np.column_stack([np.arange(24) * 0.1, pts, yaws])
    theirs = heading_error(rows, path)

    np.testing.assert_allclose(mine, theirs, atol=1e-9)


def test_weight_converts_on_the_obstacle_free_scene():
    """n=16 paired: `w_heading` 0 -> 32 improves **every** seed on cafe_straight.

    This is the claim D-430 and D-433 could not get from `w_speed` or
    `w_omega`. Those two read two-sided per-seed deltas (9/7 and 12/4-ish) —
    the signature of a knob that moves seeds around without moving the
    population. Here the split is **16/0**, a sign test at p = 2**-15
    two-sided, and the response is monotone across {0, 2, 8, 32}. A knob that
    does not point at the metric does not produce that.

    Measured 2026-08-23 (`heading_err_rms`, mean over 16 seeds):
        w_heading   0 -> 0.0639,  2 -> 0.0510,  8 -> 0.0497,  32 -> 0.0399
    and cross-track pays almost nothing for it (0.0115 -> 0.0145 m rms), with
    16/16 still reaching goal. Asserted loosely below — the point is the sign
    split and the direction, not the third decimal.

    Cost: 32 integrations (2 arms x 16 seeds), obstacle-free scene.
    """
    from eval.mppi_sandbox import ab
    from eval.path_tracking_metrics import heading_error

    sc = load_scenario(SCENARIO)
    seeds = list(range(16))

    def heading_rms(w):
        runs = ab.seed_sweep(sc, "stock_mppi", seeds=seeds,
                             params=MPPIParams(w_heading=w))
        assert all(r.reached_goal for r in runs), f"w_heading={w} lost a seed"
        return np.array([
            float(np.sqrt(np.mean(heading_error(r.traj, sc.waypoints) ** 2)))
            for r in runs])

    off, on = heading_rms(0.0), heading_rms(32.0)
    delta = on - off

    assert int((delta < 0).sum()) == 16, (
        f"expected every seed to improve, got {int((delta < 0).sum())}/16: "
        f"{delta}")
    assert on.mean() < off.mean() * 0.75, (
        f"population barely moved: {off.mean():.4f} -> {on.mean():.4f}")


@pytest.mark.parametrize("scene", ["eval/scenarios/cafe_obstacle_crossing_v0.yaml"])
def test_the_lever_is_weaker_where_the_residual_actually_lives(scene):
    """...and on the scene the residual was *reported* on, it half-works.

    Pinned because it is the honest half of D-440 and the part most likely to
    be forgotten. `cafe_obstacle_crossing_v0` is the scene D-430/D-433 measured
    the residual on. There the same 0 -> 32 swing reads **11 better / 5 worse**,
    mean heading 0.1524 -> 0.1333 (-13%, against -38% obstacle-free), the
    per-seed spread *widens* (0.0417 -> 0.0513), and cross-track gets **worse**
    (0.1516 -> 0.1812 m rms, +20%).

    That pattern is what Q-181 predicted: clearance is bought by leaving the
    reference path, `heading_err_rms` is scored against that same path, so on
    an obstacle scene part of the residual is the *price of avoidance* and
    pricing heading fights the obstacle term rather than the tracking error.
    The +20% cross-track is that fight, made of numbers.

    So D-440's lever is real but is **not** by itself the fix for the reported
    bottleneck, and this test fails if a future cycle quietly starts claiming
    it is.

    Cost: 32 integrations (2 arms x 16 seeds).
    """
    from eval.mppi_sandbox import ab
    from eval.path_tracking_metrics import heading_error

    sc = load_scenario(scene)
    seeds = list(range(16))

    def score(w):
        runs = ab.seed_sweep(sc, "stock_mppi", seeds=seeds,
                             params=MPPIParams(w_heading=w))
        return np.array([
            float(np.sqrt(np.mean(heading_error(r.traj, sc.waypoints) ** 2)))
            for r in runs])

    off, on = score(0.0), score(32.0)
    improved = int(((on - off) < 0).sum())

    # Strictly two-sided: neither a clean conversion nor no effect at all.
    assert 0 < 16 - improved, (
        f"crossing scene converted every seed ({improved}/16) — if this now "
        "holds, D-440's scene caveat is stale and Q-185 is answered")
    assert on.mean() < off.mean(), "direction should still be an improvement"

# SPDX-License-Identifier: BSD-3-Clause
"""`city_crossing_v0`: the first off-family scene that can host a clearance
comparison, and the four properties that make it worth having.

STATE has ranked "a scene outside the `cafe_*` family" as the next capability
step for several cycles. The step was never runnable: `scene_eligibility`
convicts both shipped off-family scenes (`city_curved_v0`, `city_figure8_v0`)
of `NO_OBSTACLES`, so a 2x2 walked there returns INERT because there is no
clearance to move, not because the mechanism is absent — D-107's
empty-population-reads-as-clean, which is the exact shape that would let a
scene artifact be booked as "the interaction does not generalize off-family".

So the four assertions below are not about the *reading* taken on this scene.
They are about the scene remaining the thing the reading needs, and each one
corresponds to a way this file could silently stop being useful:

1. **It is eligible** — obstacles, a declared margin, a reachable goal ball.
   Lose any one and the off-family walk goes vacuous again in the original way.
2. **It is off-family** — env_class B, `small_city` world. If someone "fixes"
   the coordinates into a cafe corridor the contrast it exists to provide is
   gone while every other property still passes.
3. **It is outside the 8-scene matrix** — the census population is pinned in
   five places (`len(shipped.scenes) == 8` here, plus hard-coded no-obstacle
   scene lists in `test_ab_temperature_protocol`, `test_epistemic_reach_screen`,
   `test_weight_units`, `test_hazard_exposure`). Placing this in `variants/`
   buys the scene without buying that migration, and *that placement is a
   claim* — this pins it, so a later cycle that promotes the scene into the
   matrix has to do it deliberately and pay the five pins, rather than by
   dropping a file in a directory and finding out from CI.
4. **It is contested** — the baseline grazes the declared margin rather than
   clearing it. This is the anti-vacuity precondition D-217 made a habit of,
   and here it screens for the *other* censoring direction too:
   `cafe_convoy_v0` is unusable for a two-sided reading because every run
   clears 0.30 m by a wide margin (`scene_transplant`'s `BOTH_ARMS_CENSORED`
   at a FLOOR). A scene where nothing is ever close to an obstacle cannot show
   an avoidance term doing anything.

Reported, never thresholded (D-044): nothing here asserts a verdict, a step
magnitude, or a sign. Those are readings on a scene whose schedule a later
cycle may well retune — the journal and `docs/decisions.md` carry them. What is
pinned is only what the scene *is*.
"""

from __future__ import annotations

import yaml

from eval.mppi_sandbox.scenario import load_scenario
from eval.mppi_sandbox.scene_eligibility import (
    ELIGIBLE,
    census,
    screen,
)

SCENE = "eval/scenarios/variants/city_crossing_v0.yaml"

#: The scene's own declared margin, read from the yaml rather than repeated, so
#: this file cannot drift from it (D-047).
def _declared_margin() -> float:
    raw = yaml.safe_load(open(SCENE))
    return float(raw["acceptance"]["min_distance_to_obstacle"])


def test_the_off_family_scene_is_eligible():
    """Obstacles, a declared margin, a reachable goal ball — all three."""
    verdict = screen(load_scenario(SCENE), "city_crossing_v0")

    assert verdict.eligible, (
        f"city_crossing_v0 exists to be the eligible off-family scene; it is "
        f"excluded for {sorted(verdict.exclusions)}")
    assert verdict.verdict == ELIGIBLE
    assert verdict.exclusions == frozenset()

    # The three screens, named individually — a single `eligible` assertion
    # would not say which one regressed.
    assert verdict.n_obstacles == 4
    assert verdict.declared_margin == _declared_margin()
    assert verdict.best_goal_clearance > 0.0


def test_the_margin_is_shared_with_the_scenes_it_will_be_compared_against():
    """0.30, the same as convoy and crossing — not head_on's 0.40.

    `comparison_headroom.Headroom` refuses to grade two arms against different
    margins, so a cross-family reading is only possible against the two cafe
    scenes that declare the same one. Choosing 0.30 was the point, not a
    coincidence, and if someone retunes this scene's margin the cross-family
    comparison quietly stops being gradeable rather than failing.
    """
    shipped = census()
    by_name = {s.scenario: s for s in shipped.scenes}

    assert _declared_margin() == by_name["cafe_convoy_v0"].declared_margin
    assert _declared_margin() == by_name["cafe_obstacle_crossing_v0"].declared_margin


def test_the_scene_is_off_family():
    """env_class B on the small_city world — the contrast the scene is for."""
    raw = yaml.safe_load(open(SCENE))

    assert raw["env_class"] == "B", (
        "city_crossing_v0 is the *outdoor-open* arm of the family contrast; "
        "cafe_obstacle_crossing_v0 is env_class D")
    assert "small_city" in raw["world"]
    assert not raw["name"].startswith("cafe")


def test_the_scene_is_deliberately_outside_the_eight_scene_matrix():
    """`variants/` placement is a claim about pins, so it gets pinned.

    If this scene is ever promoted into `eval/scenarios/`, this test fails —
    which is the intended alarm. Promotion is legitimate; doing it without
    also moving the five pinned populations is not.
    """
    shipped = census()

    assert len(shipped.scenes) == 8, (
        "adding a 9th scene to eval/scenarios/ moves this count and four "
        "other hard-coded scene lists; see this module's docstring")
    assert "city_crossing_v0" not in {s.scenario for s in shipped.scenes}
    assert "city_crossing_v0" not in {s.scenario for s in shipped.eligible}


def test_the_baseline_is_contested_at_the_declared_margin():
    """The anti-vacuity precondition, screening *both* censoring directions.

    Too easy (convoy: everything clears, both arms at a FLOOR) and too empty
    (city_curved: `min_obstacle_clearance` is `Infinity`) are the two ways an
    off-family walk can produce numbers that mean nothing. A baseline that
    comes within the declared margin of a pedestrian rules out both.
    """
    from eval.mppi_sandbox.ab import seed_sweep, summarize
    from eval.mppi_sandbox.controllers.stock_mppi import MPPIParams

    # λ = 0.8 named explicitly, as `three_arm.read_arm` does and for its
    # reason: at the shipped default the sampler is a greedy argmin and the
    # reading would be about the temperature (D-217).
    stats = summarize(seed_sweep(
        load_scenario(SCENE), "risk_mppi", seeds=(0, 1, 2),
        params=MPPIParams(lam=0.8), w_risk=0.0))

    assert stats.min_clearance < _declared_margin(), (
        f"baseline worst-case clearance {stats.min_clearance:.4f} already "
        f"clears the declared {_declared_margin():.2f} m margin — the scene is "
        f"convoy's FLOOR censoring and cannot show an avoidance term working")
    assert stats.min_clearance < float("inf"), (
        "clearance to nothing is not a measurement (D-107)")


def test_the_baseline_is_not_censored_below_the_margin():
    """The *other* censoring direction — the one that was not screened (D-223).

    The test above asserts the baseline does not clear the margin, and its
    docstring claimed that screened "both censoring directions". It did not:
    both of its assertions bound the baseline from **above** (too easy, too
    empty). Nothing bounded it from below, and that is the direction the scene
    actually failed in. As first authored every schedule intercepted the robot
    exactly, putting all four cells of the 2x2 at 0.018-0.032 m median against
    a 0.30 m margin — a comparison between four arms that all fail, where the
    step is scene noise and `family` is confounded with `difficulty` (Q-134,
    D-222). That reading passed the screen above cleanly, because failing
    worse is still failing to clear.

    So "contested" is pinned as **straddling**: the worst seed dips under the
    margin, the median seed clears it. A scene where the *median* run is
    already inside the margin is one where the avoidance term is being graded
    on runs that have already lost, which is the mirror of convoy's FLOOR.

    Per the module docstring this still pins no verdict, step or sign — only
    that the scene remains gradeable in both directions.
    """
    from eval.mppi_sandbox.ab import seed_sweep, summarize
    from eval.mppi_sandbox.controllers.stock_mppi import MPPIParams

    stats = summarize(seed_sweep(
        load_scenario(SCENE), "risk_mppi", seeds=(0, 1, 2),
        params=MPPIParams(lam=0.8), w_risk=0.0))

    assert stats.median_clearance > _declared_margin(), (
        f"baseline median clearance {stats.median_clearance:.4f} is inside the "
        f"declared {_declared_margin():.2f} m margin — the typical run already "
        f"fails, so an arm's step here is measured between failures (D-222's "
        f"confound). Retune the schedule lag until the median clears.")
    assert stats.n_reached == stats.n, (
        f"only {stats.n_reached}/{stats.n} baseline seeds reach the goal; a "
        f"clearance number from a run that stopped driving is unreadable — the "
        f"same discipline `three_arm.ArmReading.verdict` applies per-arm")

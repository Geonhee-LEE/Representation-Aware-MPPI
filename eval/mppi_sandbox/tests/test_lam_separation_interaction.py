# SPDX-License-Identifier: BSD-3-Clause
"""Q-041: is `lam`-window separation an *interaction* between staggered actor
timing and counter-flow actors — measured inside a single parent scene?

Where this comes from
---------------------
20:00 refuted time-in-contest as the predictor (D-018): raising a `shared`
scene's contested fraction *past* the only `per_arm` scene's own value left its
two arms sharing two rungs. What survived was a 2x2 in which `per_arm` appeared
in exactly one corner — but assembled from **two different parents**
(`cafe_convoy_v0` at 0.5 m/s over 4.5 m, `cafe_obstacle_crossing_v0` at 0.3 m/s
over 5.0 m). With the off-diagonal cells donated by different scenes,
"interaction" and "parent difference" were not separable, and the 20:00 journal
recorded it as a lead rather than a result.

This module closes the design **within `cafe_obstacle_crossing_v0`**, where the
robot, reference path, target speed, actor lanes, actor speeds and acceptance
block are held byte-identical across all four cells and only the two factors
move::

    stagger  counter-flow  scene                                  verdict
    yes      yes           cafe_obstacle_crossing_v0              per_arm
    no       yes           cafe_obstacle_crossing_sync_v0         shared
    yes      no            cafe_obstacle_crossing_noflow_v0       <- new
    no       no            cafe_obstacle_crossing_sync_noflow_v0  <- new

Why the design is better than the one it replaces
-------------------------------------------------
Beyond sharing a parent, the two factors are **orthogonal by construction**.
Each actor sweeps `x` in [-3, +3] at constant speed while the robot descends
`x = 0`, so reversing an actor maps `x(t) -> -x(t)` and leaves `|x(t)|` — hence
its distance to every point of the reference path — pointwise unchanged. The
direction factor therefore moves the clearance matrix not at all (asserted
below, bit-for-bit), while the timing factor moves contested fraction 74% ->
26%. Any verdict that tracks direction cannot be an exposure effect in
disguise, which is precisely the confusion that cost 20:00 its hypothesis.

Three groups, in the order a reader should trust them: structural (free,
proves the intervention is what it claims), empirical (reads the calibrated
table), reproduction (re-derives the decisive cell from simulation).
"""

from __future__ import annotations

import os

import numpy as np
import pytest
import yaml

from eval.mppi_sandbox import exposure as exp
from eval.mppi_sandbox.calibrate_lam import load_windows
from eval.mppi_sandbox.scenario import load_scenario

VARIANTS = "eval/scenarios/variants"
VARIANT_TABLE = f"{VARIANTS}/lam_windows_variants.yaml"

#: The 2x2, keyed by `(staggered_start_times, has_counter_flow_actors)`.
CELLS = {
    (True, True): "eval/scenarios/cafe_obstacle_crossing_v0.yaml",
    (False, True): f"{VARIANTS}/cafe_obstacle_crossing_sync_v0.yaml",
    (True, False): f"{VARIANTS}/cafe_obstacle_crossing_noflow_v0.yaml",
    (False, False): f"{VARIANTS}/cafe_obstacle_crossing_sync_noflow_v0.yaml",
}
PARENT = CELLS[(True, True)]

#: Cells differing from their donor only in travel direction. The left member
#: supplies the timing, the right member is the flipped copy.
FLIP_PAIRS = [
    (CELLS[(True, True)], CELLS[(True, False)]),
    (CELLS[(False, True)], CELLS[(False, False)]),
]


def _raw(path: str) -> dict:
    with open(path) as fh:
        return yaml.safe_load(fh)


def factors(path: str) -> tuple[bool, bool]:
    """`(staggered, counter_flow)` read off the yaml, not off the filename.

    A cell that is mislabelled by its name is the one failure mode this whole
    design cannot survive, so the factor levels are derived from the actor
    schedules themselves.
    """
    obs = _raw(path)["dynamic_obstacles"]
    staggered = len({ob["waypoints"][0]["t"] for ob in obs}) > 1
    counter_flow = any(ob["waypoints"][-1]["x"] < ob["waypoints"][0]["x"]
                       for ob in obs)
    return staggered, counter_flow


def _strip_direction(obstacles: list[dict]) -> list[dict]:
    """Obstacle list with travel direction canonicalised away.

    Everything the direction flip is *not* allowed to touch: lane (`y`), start
    times, speed, id, type, and the `|x|` span. `init.x` / `init.yaw` are
    dropped because both are pure restatements of the first waypoint and its
    heading; `init.y` is kept, since a lane change there would be exactly the
    kind of silent drift this test exists to catch.
    """
    out = []
    for ob in obstacles:
        ob = dict(ob)
        ob["waypoints"] = [dict(w, x=abs(w["x"])) for w in ob["waypoints"]]
        ob["init"] = {k: v for k, v in ob["init"].items()
                      if k not in ("x", "yaw")}
        out.append(ob)
    return out


# --- 1. structural: the design really is crossed within one parent ------------

def test_the_2x2_is_fully_crossed_and_each_cell_is_labelled_by_its_schedule():
    """Four distinct scenes, four distinct factor combinations, no gaps.

    Reading the levels back out of the yamls is what makes the table in the
    docstring a claim rather than a caption.
    """
    assert len(set(CELLS.values())) == 4
    for expected, path in CELLS.items():
        assert factors(path) == expected, path


def test_every_cell_shares_the_parents_robot_lanes_and_acceptance():
    """The control, enforced mechanically rather than asserted in a comment.

    This is what the 20:00 design could not claim: its off-diagonal cells came
    from a parent with a different `target_speed_mps` and a different path
    length, so a verdict difference had a second explanation available. Here
    the robot and the actors' geometry are identical in all four cells and the
    only free variables are the two factors.
    """
    parent = _raw(PARENT)
    for path in CELLS.values():
        cell = _raw(path)
        for key in ("start", "goal", "reference_path", "acceptance",
                    "target_speed_mps", "world", "env_class"):
            assert cell.get(key) == parent.get(key), f"{path}: {key}"

        # Same five actors, same lanes, same speeds — only `t` and direction
        # may differ, and `_strip_direction` removes the latter.
        assert len(cell["dynamic_obstacles"]) == 5
        assert ([ob["id"] for ob in cell["dynamic_obstacles"]]
                == [ob["id"] for ob in parent["dynamic_obstacles"]])
        assert ([ob["init"]["y"] for ob in cell["dynamic_obstacles"]]
                == [ob["init"]["y"] for ob in parent["dynamic_obstacles"]])
        assert ({ob["speed"] for ob in cell["dynamic_obstacles"]}
                == {ob["speed"] for ob in parent["dynamic_obstacles"]})


@pytest.mark.parametrize("donor,flipped", FLIP_PAIRS)
def test_noflow_cells_change_direction_and_nothing_else(donor, flipped):
    """The direction intervention is *pure*: same lanes, same `t`, same speeds.

    `_strip_direction` normalises the sign of every waypoint `x`, so what is
    compared is every property the flip is forbidden to move. The second
    assertion checks the flip actually happened — a "control" that changed
    nothing would pass the first one vacuously, which is the defect class
    18:00 named.
    """
    d, f = _raw(donor), _raw(flipped)

    assert _strip_direction(f["dynamic_obstacles"]) == \
        _strip_direction(d["dynamic_obstacles"])
    assert factors(donor)[0] == factors(flipped)[0], "timing must not move"
    assert factors(donor)[1] and not factors(flipped)[1]


@pytest.mark.parametrize("donor,flipped", FLIP_PAIRS)
def test_direction_flip_preserves_the_clearance_matrix_exactly(donor, flipped):
    """**The property that makes this 2x2 worth running.**

    Reversing an actor across a path the robot meets head-on is an isometry of
    the nominal encounter: `x(t) -> -x(t)` with the robot on `x = 0` leaves
    every entry of the `(T, N)` clearance matrix identical, not merely close.
    So the direction factor is provably invisible to `exposure.py`, and the two
    factors of the design are orthogonal — timing carries all of the exposure
    change (74% -> 26%) and direction carries none of it.

    Bit-equality rather than `approx` on purpose: the claim is an algebraic
    identity, and a tolerance would let a real geometry edit hide inside it.
    """
    cd, cf = (exp.clearance_matrix(exp.nominal_traversal(load_scenario(p)),
                                   load_scenario(p).obstacles)
              for p in (donor, flipped))

    assert np.array_equal(cd, cf)
    assert exp.hazard_exposure(donor).contested_fraction == \
        exp.hazard_exposure(flipped).contested_fraction


def test_timing_is_the_only_factor_that_moves_exposure():
    """The other half of the orthogonality claim, stated over all four cells.

    Exposure takes exactly two values across the 2x2, and they are sorted by
    the timing factor alone. A predictor built on exposure therefore cannot
    distinguish the `per_arm` corner from its same-timing neighbour — which is
    the structural reason 20:00's hypothesis had to fail, restated here as a
    measurement rather than as hindsight.
    """
    by_stagger: dict[bool, set[float]] = {True: set(), False: set()}
    for (staggered, _), path in CELLS.items():
        by_stagger[staggered].add(
            round(exp.hazard_exposure(path).contested_fraction, 6))

    assert len(by_stagger[True]) == len(by_stagger[False]) == 1
    assert by_stagger[True] != by_stagger[False]
    assert next(iter(by_stagger[True])) > 0.70
    assert next(iter(by_stagger[False])) < 0.30


# --- 2. empirical: the registered prediction was wrong ------------------------

def _window(scenario: str, controller: str) -> tuple[float, ...]:
    cells = load_windows(VARIANT_TABLE)
    if (scenario, controller) in cells:
        return tuple(cells[(scenario, controller)]["admissible"])
    parent = load_windows("eval/scenarios/lam_windows.yaml")
    return tuple(parent[(scenario, controller)]["admissible"])


def _verdict(scenario: str) -> str:
    stock, risk = _window(scenario, "stock_mppi"), _window(scenario, "risk_mppi")
    if not stock or not risk:
        return "unreportable"
    return "shared" if set(stock) & set(risk) else "per_arm"


def test_removing_counter_flow_did_not_heal_the_split():
    """**The prediction registered in the variant's header is refuted.**

    `cafe_obstacle_crossing_noflow_v0` keeps the stagger, drops the
    counter-flow, and its arms are still disjoint (`stock` [3.2] vs `risk`
    [1.6]). So counter-flow is **not necessary** for separation, the
    interaction Q-041 proposed does not exist inside this parent, and the
    surviving description is a plain main effect of the timing factor.
    """
    assert _verdict("cafe_obstacle_crossing_noflow_v0.yaml") == "per_arm"
    assert not (set(_window("cafe_obstacle_crossing_noflow_v0.yaml", "stock_mppi"))
                & set(_window("cafe_obstacle_crossing_noflow_v0.yaml", "risk_mppi")))


def test_within_this_parent_stagger_alone_sorts_the_verdicts():
    """The 2x2 collapses to one factor: both staggered cells separate, both
    synchronised cells share, regardless of direction."""
    verdicts = {k: _verdict(os.path.basename(p)) for k, p in CELLS.items()}

    assert verdicts[(True, True)] == verdicts[(True, False)] == "per_arm"
    assert verdicts[(False, True)] == verdicts[(False, False)] == "shared"


def test_the_cross_parent_2x2_cell_was_a_parent_artifact():
    """Why the design had to be redone inside one parent.

    `cafe_convoy_staggered_v0` and `cafe_obstacle_crossing_noflow_v0` sit at
    the *same* factor levels — staggered, no counter-flow — and disagree.
    20:00 read that cell's `shared` as evidence that stagger alone is
    insufficient; it was evidence that the two parents differ. This assertion
    is the reason a 2x2 assembled across parents cannot be interpreted.
    """
    convoy_staggered = f"{VARIANTS}/cafe_convoy_staggered_v0.yaml"

    assert factors(convoy_staggered) == factors(CELLS[(True, False)]) == (True, False)
    assert _verdict("cafe_convoy_staggered_v0.yaml") == "shared"
    assert _verdict("cafe_obstacle_crossing_noflow_v0.yaml") == "per_arm"


def test_direction_moves_the_windows_though_it_cannot_move_the_exposure():
    """The subtler half, and the one the screen cannot see.

    The flip is bit-identical in the clearance matrix (group 1), yet the two
    synchronised cells do not calibrate alike: `sync` shares {1.6, 3.2} across
    its arms and `sync_noflow` shares only {3.2}. Direction never flips a
    verdict here, but it demonstrably changes what the controllers do — so
    `exposure.py` is provably *incomplete* as a screen rather than merely
    unlucky on Q-040. This also refutes the second, sharper prediction in
    `cafe_obstacle_crossing_sync_noflow_v0.yaml`'s header, which expected the
    two synchronised cells to land on the same windows.
    """
    sync, sync_noflow = ("cafe_obstacle_crossing_sync_v0.yaml",
                         "cafe_obstacle_crossing_sync_noflow_v0.yaml")

    assert _verdict(sync) == _verdict(sync_noflow) == "shared"
    shared_sync = set(_window(sync, "stock_mppi")) & set(_window(sync, "risk_mppi"))
    shared_flip = (set(_window(sync_noflow, "stock_mppi"))
                   & set(_window(sync_noflow, "risk_mppi")))
    assert shared_sync == {1.6, 3.2}
    assert shared_flip == {3.2}
    assert shared_flip < shared_sync


# --- 3. the confound that outranks the whole 2x2 -----------------------------

@pytest.mark.slow
def test_the_per_arm_verdict_is_a_property_of_the_seed_count_not_the_scene():
    """**The finding that reframes Q-040 and Q-041 both.**

    `ab.LamProbe.admissible` requires *every* seed to weight inside the ESS
    band, so it is a **conjunction over seeds**: adding seeds can only ever
    shrink a window, never grow one. The classification `shared` vs `per_arm`
    is therefore not a scene property at all — it is a `(scene, n_seeds)`
    property with a known direction of bias, and any pair of arms separates
    eventually if enough seeds are drawn.

    Measured on the parent scene, the one whose separation has driven four
    cycles of work: `stock_mppi` admits `lam = 1.6` on four seeds and loses it
    on eight, which is exactly the rung `risk_mppi` holds. The same scene is
    `shared` at n = 4 and `per_arm` at n = 8 — no geometry changed, only the
    number of draws the conjunction ranges over.

    Consequence: every `per_arm` claim in this repo, including 18:00's
    headline, must carry its `n`, and searching for a *scene* property that
    predicts separation (Q-040, Q-041) was searching for a predictor of a
    quantity that is not well-defined until `n` is fixed.

    Costed deliberately: one arm, one rung, 4 + 8 seeds.
    """
    from eval.mppi_sandbox import ab

    scen = load_scenario(PARENT)
    four, eight = (ab.admissible_lams(ab.lam_ladder(scen, "stock_mppi", [1.6],
                                                    seeds=range(n)))
                   for n in (4, 8))

    assert four == (1.6,), "stock_mppi should admit 1.6 on four seeds"
    assert eight == (), "and lose it on eight — the conjunction only tightens"
    # 1.6 is a rung `risk_mppi` holds at both counts, so this single rung is
    # what turns the parent's verdict from `shared` into `per_arm`.
    assert 1.6 in _window("cafe_obstacle_crossing_v0.yaml", "risk_mppi")

# SPDX-License-Identifier: BSD-3-Clause
"""Q-040: what property of a scene predicts that its controllers' `lam`
windows separate?

`cafe_obstacle_crossing_v0` is the only `per_arm` cell in the eight-scene
matrix. `cafe_convoy_v0` carries the *same five actors* at the same footprint
and is `shared`, so the predictor is not obstacle count.

The candidate this cycle proposed was **time-in-contest**, and the two-sided
intervention below **refuted it**: lowering exposure healed the split as
predicted, but *raising* it past the crossing scene's own value did not create
one. What survived was a lead — a 2x2 in which `per_arm` appeared only where
staggered timing and counter-flow actors were *both* present.

**That lead is itself now refuted** (21:00, `test_lam_separation_interaction.py`).
Re-run inside a single parent, both staggered cells separate and both
synchronised cells share regardless of direction, so the "interaction" was two
parents disagreeing at the same factor levels. The same cycle found the deeper
problem: `per_arm` vs `shared` is a `(scene, n_seeds)` property, not a scene
property, because admissibility is a conjunction over seeds. Q-040's question
was therefore malformed — see that module. These tests pin the negative result
and the intervention machinery that produced it, not an answer.

Three groups:

1. **Static** — the exposure screen's arithmetic and its ranking over the
   shipped matrix. Free (simulates nothing).
2. **Structural** — the two intervention variants really are pure-timing
   edits of their parents. Mechanically enforced by diffing the yamls, so a
   later hand-edit that quietly changes a lane or a speed breaks the test
   rather than the conclusion. Free.
3. **Empirical** — the calibrated outcome of the intervention, recorded in
   `eval/scenarios/variants/lam_windows_variants.yaml` and reproduced in CI
   on a narrow ladder (the wide one is a script, per the 16:00 split).
"""

from __future__ import annotations

import glob
import os

import pytest
import yaml

from eval.mppi_sandbox import exposure as exp
from eval.mppi_sandbox.run import ROBOT_RADIUS
from eval.mppi_sandbox.scenario import load_scenario

SCENARIOS = sorted(
    p for p in glob.glob("eval/scenarios/*.yaml") if "lam_windows" not in p
)
VARIANTS = "eval/scenarios/variants"

CROSSING = "eval/scenarios/cafe_obstacle_crossing_v0.yaml"
CONVOY = "eval/scenarios/cafe_convoy_v0.yaml"
CONVOY_STAGGERED = f"{VARIANTS}/cafe_convoy_staggered_v0.yaml"
CROSSING_SYNC = f"{VARIANTS}/cafe_obstacle_crossing_sync_v0.yaml"


# --- 1. static screen ---------------------------------------------------------

def test_robot_radius_matches_run_module():
    """Same footprint the simulator uses, for the same reason feasibility.py
    pins it: a screen that models a different robot screens a different scene."""
    assert exp.ROBOT_RADIUS == ROBOT_RADIUS


def test_nominal_traversal_respects_scene_speed():
    """Duration is path length / `target_speed_mps`, not a constant.

    Load-bearing: the crossing scene runs at 0.3 m/s and the convoy at the
    0.5 m/s default, so an exposure measure that ignored speed would compare
    them at the wrong rendezvous times.
    """
    scen = load_scenario(CROSSING)
    traj = exp.nominal_traversal(scen)

    assert scen.target_speed == pytest.approx(0.3)
    # 5 m of straight path at 0.3 m/s.
    assert traj[-1, 0] == pytest.approx(5.0 / 0.3, abs=exp.DT)
    # Starts at the first waypoint, ends at the last.
    assert traj[0, 1:3] == pytest.approx(scen.waypoints[0, :2])
    assert traj[-1, 1:3] == pytest.approx(scen.waypoints[-1, :2])


def test_obstacle_free_scenes_screen_as_zero_not_infinity():
    """Four of eight scenes have no sandbox obstacles (17:00's finding).

    They must report `contested 0` with an explicit `n_obstacles == 0`, not a
    silent `+inf` that a caller could average into a ranking.
    """
    empty = [e for e in exp.screen_scenarios(SCENARIOS) if e.n_obstacles == 0]

    assert {e.scenario for e in empty} == {
        "cafe_straight_v0.yaml", "city_curved_v0.yaml", "city_figure8_v0.yaml",
    }
    for e in empty:
        assert e.contested_s == 0.0
        assert e.contested_fraction == 0.0
        assert e.peak_contesting == 0


def test_obstacle_count_does_not_separate_crossing_from_convoy():
    """The negative result that forces the question.

    Identical count, identical radius — whatever splits the crossing scene's
    windows is invisible to a census of its obstacle list.
    """
    crossing = exp.hazard_exposure(CROSSING)
    convoy = exp.hazard_exposure(CONVOY)

    assert crossing.n_obstacles == convoy.n_obstacles == 5
    radii = {ob.radius for p in (CROSSING, CONVOY)
             for ob in load_scenario(p).obstacles}
    assert radii == {0.3}


def test_time_in_contest_separates_them_and_peak_count_ranks_them_backwards():
    """Why time-in-contest was worth testing — the static case *for* the
    hypothesis the intervention then refuted.

    Two natural "how hazardous is this scene" statistics disagree on these two
    scenes: the convoy is the denser encounter (all five actors at once) and
    the crossing is the *longer* one. Only the time-integral ranks the
    `per_arm` cell first, which is what the cost-magnitude mechanism from
    18:00 suggested — a collision term contributes to the cost by integration,
    so duration and not instantaneous count should scale an arm's landscape.

    Kept after the refutation because it is the whole reason the intervention
    was run: this ranking is exactly what a plausible-but-wrong predictor
    looks like before you pay to falsify it.
    """
    crossing = exp.hazard_exposure(CROSSING)
    convoy = exp.hazard_exposure(CONVOY)

    # Time-integral: crossing dominates, and not marginally.
    assert crossing.contested_fraction > 0.70
    assert convoy.contested_fraction < 0.50
    assert crossing.contested_fraction > 1.5 * convoy.contested_fraction

    # Instantaneous density: the ranking flips.
    assert convoy.peak_contesting == 5
    assert crossing.peak_contesting == 2
    assert convoy.peak_contesting > crossing.peak_contesting


def test_crossing_leads_every_calibratable_scene_on_contested_fraction():
    """Ranking over the shipped matrix, stated with its one caveat.

    `cafe_cut_in_v0` scores higher (85%) but is *not* a competing positive:
    17:00 proved it uncompletable (its goal ball is permanently occupied), so
    it has no `lam` window for either arm and cannot be a `per_arm` cell. The
    screen ranks it first because a permanently-parked blocker is, correctly,
    maximal exposure — the two screens compose rather than conflict.
    """
    from eval.mppi_sandbox.feasibility import screen_scenarios as feasibility_screen

    # feasibility reports the scenario's `name:` (dashed), exposure reports the
    # filename (underscored) — normalise once, explicitly, rather than letting a
    # mismatch silently empty the list and pass the test vacuously.
    reachable = {v.scenario.replace("-", "_") for v in feasibility_screen(SCENARIOS)
                 if v.is_reachable}
    ranked = [e for e in exp.screen_scenarios(SCENARIOS)
              if os.path.splitext(e.scenario)[0] in reachable]

    assert len(ranked) == len(SCENARIOS) - 1, "naming normalisation dropped scenes"
    assert ranked[0].scenario == "cafe_obstacle_crossing_v0.yaml"

    top = exp.hazard_exposure(CROSSING)
    excluded = exp.hazard_exposure("eval/scenarios/cafe_cut_in_v0.yaml")
    assert excluded.contested_fraction > top.contested_fraction
    assert "cafe_cut_in_v0.yaml" not in {e.scenario for e in ranked}


# --- 2. structural: the intervention is pure-timing ---------------------------

def _raw(path: str) -> dict:
    with open(path) as fh:
        return yaml.safe_load(fh)


def _strip_times(obstacles: list[dict]) -> list[dict]:
    """Obstacle list with every waypoint `t` removed — everything the
    intervention is *not* allowed to touch."""
    out = []
    for ob in obstacles:
        ob = dict(ob)
        ob["waypoints"] = [{k: v for k, v in w.items() if k != "t"}
                           for w in ob.get("waypoints", [])]
        out.append(ob)
    return out


@pytest.mark.parametrize("parent,variant", [
    (CONVOY, CONVOY_STAGGERED),
    (CROSSING, CROSSING_SYNC),
])
def test_variant_changes_only_obstacle_start_times(parent, variant):
    """The control, enforced mechanically instead of asserted in a comment.

    Lanes, x endpoints, speeds, radii, ids, directions, the robot's
    start/goal/path/target_speed and the acceptance block must all be
    identical to the parent. If any of those drift, the calibration result
    below stops being attributable to the schedule and this test — not the
    conclusion — is what breaks.
    """
    p, v = _raw(parent), _raw(variant)

    assert _strip_times(v["dynamic_obstacles"]) == _strip_times(p["dynamic_obstacles"])
    for key in ("start", "goal", "reference_path", "acceptance",
                "target_speed_mps", "world"):
        assert v.get(key) == p.get(key), key

    # ...and the times really did change, or it is not an intervention.
    assert v["dynamic_obstacles"] != p["dynamic_obstacles"]


def test_interventions_move_exposure_in_opposite_directions():
    """Two-sided by construction: one variant raises exposure, one lowers it.

    A single direction could be a quirk of whichever scene was edited. Note
    `peak_contesting` moves the *other* way in both cases (convoy 5 -> 3,
    crossing 2 -> 5), so the two candidate statistics stay decoupled under the
    intervention and the empirical test below can tell them apart.
    """
    convoy, staggered = exp.hazard_exposure(CONVOY), exp.hazard_exposure(CONVOY_STAGGERED)
    crossing, sync = exp.hazard_exposure(CROSSING), exp.hazard_exposure(CROSSING_SYNC)

    # Treatment: convoy timing -> crossing-like exposure.
    assert staggered.contested_fraction > 0.70 > convoy.contested_fraction
    assert staggered.peak_contesting < convoy.peak_contesting

    # Converse: crossing timing -> convoy-like exposure.
    assert sync.contested_fraction < 0.30 < crossing.contested_fraction
    assert sync.peak_contesting > crossing.peak_contesting

    # Obstacle count is invariant under both, as the control requires.
    assert {e.n_obstacles for e in (convoy, staggered, crossing, sync)} == {5}


# --- 3. empirical: the intervention refutes the predictor ---------------------

VARIANT_TABLE = f"{VARIANTS}/lam_windows_variants.yaml"


def _windows(table: str) -> dict[tuple[str, str], list[float]]:
    raw = yaml.safe_load(open(table))
    return {(c["scenario"], c["controller"]): list(c["admissible"])
            for c in raw["cells"]}


def _verdict(table: str, scenario: str) -> str:
    w = _windows(table)
    stock, risk = w[(scenario, "stock_mppi")], w[(scenario, "risk_mppi")]
    if not stock or not risk:
        return "unreportable"
    return "shared" if set(stock) & set(risk) else "per_arm"


def test_raising_exposure_did_not_split_the_windows():
    """**The prediction registered in the variant's header is refuted.**

    `cafe_convoy_staggered_v0` has *higher* contested fraction than the only
    `per_arm` scene in the matrix (77% vs 74%) and its two arms still share
    two rungs. So time-in-contest is not sufficient to separate them, and —
    since it is not even monotone across these two scenes — it is not the
    predictor Q-040 asked for.

    Recorded rather than deleted: the exposure screen is still the cheapest
    way to state *why* it is not the answer, and this is the assertion that
    stops a later cycle re-proposing it.
    """
    staggered = exp.hazard_exposure(CONVOY_STAGGERED)
    crossing = exp.hazard_exposure(CROSSING)

    assert staggered.contested_fraction > crossing.contested_fraction
    assert _verdict(VARIANT_TABLE, "cafe_convoy_staggered_v0.yaml") == "shared"
    assert _windows(VARIANT_TABLE)[("cafe_convoy_staggered_v0.yaml", "stock_mppi")] \
        == _windows(VARIANT_TABLE)[("cafe_convoy_staggered_v0.yaml", "risk_mppi")]


def test_lowering_exposure_did_heal_the_split():
    """The converse arm *confirmed* the prediction — which on its own would
    have been read as support.

    `cafe_obstacle_crossing_sync_v0` drops to 26% contested and its arms
    re-overlap at [1.6, 3.2], where the parent scene is disjoint
    ([0.4, 0.8] vs [1.6, 3.2]). Had this cycle run only this arm it would have
    reported the hypothesis as established. Pinned as the standing argument
    for paying for both directions.
    """
    assert exp.hazard_exposure(CROSSING_SYNC).contested_fraction < 0.30
    assert _verdict(VARIANT_TABLE, "cafe_obstacle_crossing_sync_v0.yaml") == "shared"

    stock = _windows(VARIANT_TABLE)[("cafe_obstacle_crossing_sync_v0.yaml", "stock_mppi")]
    risk = _windows(VARIANT_TABLE)[("cafe_obstacle_crossing_sync_v0.yaml", "risk_mppi")]
    # Both arms moved *up together* — the sync pass scaled both cost
    # landscapes, rather than one arm's more than the other's. That is the
    # shape a separation-predictor has to explain and exposure does not.
    assert set(stock) & set(risk) == {1.6, 3.2}


def test_crossing_is_the_only_cell_with_both_stagger_and_counter_flow():
    """The lead this cycle produced — **and the next cycle refuted**.

    Kept because the factor levels it reads off the yamls are still correct and
    still worth pinning; its *interpretation* is not. See the closing note.

    The four cells happen to form a 2x2 in (staggered start times) x
    (counter-flow actors), and `per_arm` appears in exactly one corner::

        stagger  counter-flow  scene                            verdict
        yes      yes           cafe_obstacle_crossing_v0        per_arm
        yes      no            cafe_convoy_staggered_v0         shared
        no       yes           cafe_obstacle_crossing_sync_v0   shared
        no       no            cafe_convoy_v0                   shared

    It looked as though neither factor alone does it. Stated as a *lead* rather
    than a result, because the two off-diagonal cells come from different
    parents (0.3 vs 0.5 m/s, 5.0 vs 4.5 m) — and that caveat is exactly what
    cashed out. Completing the design inside one parent (21:00) put `per_arm`
    in **both** staggered corners, so `cafe_convoy_staggered_v0`'s `shared` was
    a parent difference, not an absent interaction. Recording the lead with its
    own confound named is what made the follow-up one experiment rather than a
    search.
    """
    def factors(path):
        obs = _raw(path)["dynamic_obstacles"]
        t0 = {ob["waypoints"][0]["t"] for ob in obs}
        counter = sum(1 for ob in obs
                      if ob["waypoints"][-1]["x"] < ob["waypoints"][0]["x"])
        return (len(t0) > 1, counter > 0)

    assert factors(CROSSING) == (True, True)
    assert factors(CONVOY_STAGGERED) == (True, False)
    assert factors(CROSSING_SYNC) == (False, True)
    assert factors(CONVOY) == (False, False)


@pytest.mark.slow
def test_refutation_reproduces_from_simulation():
    """Re-derive the decisive cell rather than trusting the committed table.

    One rung, four seeds (~25 s) — enough to prove the intersection is
    non-empty, which is the whole refutation. The 8-rung / 8-seed ladder that
    produced `lam_windows_variants.yaml` stays a script, per the 16:00 split
    between what a table records and what CI can afford to re-run. This is the
    only test in the file that simulates anything; the other twelve are free.
    """
    from eval.mppi_sandbox import ab

    scen = load_scenario(CONVOY_STAGGERED)
    shared = set.intersection(*(
        set(ab.admissible_lams(ab.lam_ladder(scen, c, [0.4], seeds=range(4))))
        for c in ("stock_mppi", "risk_mppi")))

    assert shared == {0.4}, "the two arms no longer share a rung"

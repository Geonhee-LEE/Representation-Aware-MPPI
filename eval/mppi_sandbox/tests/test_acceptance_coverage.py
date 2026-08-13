# SPDX-License-Identifier: BSD-3-Clause
"""Every acceptance criterion a scene declares is either graded or pinned as debt.

D-241 wired one such key after finding it by grep. These tests are the sweep that
makes the *next* one fail on the cycle that introduces it, plus the direction
check that keeps the guard from punishing the fix.

Deliberately controller-free: nothing here builds an MPPI, so the module stays
out of the default-lam census (D-124) and the suite cost stays near zero.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from eval.mppi_sandbox import acceptance_coverage as ac
from eval.mppi_sandbox.run import check_acceptance

#: Every key `check_acceptance` grades, discovered by probing it rather than by
#: importing a table — the same derivation the module under test uses, so this
#: file cannot pin a set the checker has since outgrown.
GRADED = tuple(sorted(k for k in (
    "cte_rms_max", "cte_max", "heading_err_rms_max", "completion_min",
    "goal_reached", "min_distance_to_obstacle", "collision",
    "freeze_duration_max", "jerk_lat_max") if ac.grades(k)))
PARAMS = ("goal_xy_tol", "goal_yaw_tol")

# A metrics dict wide enough to exercise every rule; each rule reads one key.
METRICS = {
    "cte_rms": 0.1, "cte_max": 0.2, "heading_err_rms": 0.05,
    "completion_final": 1.0, "goal_reached": 1, "freeze_duration": 0.5,
    "jerk_lat": 2.9,
}


def test_no_unpinned_ungraded_acceptance_key():
    """The finding direction: a declared criterion nothing grades and nobody pinned."""
    assert ac.drift() == []


def test_census_names_only_real_gaps():
    """The other direction: a pinned key that is now graded must leave the census.

    Without this the census rots into a list of things that used to be broken,
    and the guard stops meaning anything.
    """
    found = ac.survey()
    for scene, keys in ac.UNGRADED_CENSUS.items():
        for key in keys:
            assert key in found.get(scene, []), (
                f"{scene}.{key} is pinned as ungraded but is graded now — "
                f"drop it from UNGRADED_CENSUS")


def test_the_graded_set_is_derived_not_copied():
    """D-047: the guard must have no second statement of the rules table.

    Pinned structurally — `acceptance_coverage` may not name a graded key at
    all, because any spelling of one is a copy that can go short.
    """
    src = (Path(ac.__file__).read_text())
    body = src.split("UNGRADED_CENSUS = {", 1)[0] + src.split("}", 2)[-1]
    for key in GRADED:
        assert f'"{key}"' not in body, (
            f"{key} is respelled in acceptance_coverage; the sweep must derive "
            f"the graded set by calling check_acceptance, never re-type it")


def test_every_remaining_gap_is_a_declared_top_three_criterion():
    """Records what the sweep measured: all 4 survivors sit in the scene's own
    `success_metric_priority`. This is why they are debt and not housekeeping."""
    assert ac.prioritised_but_ungraded() == ac.UNGRADED_CENSUS


def test_params_are_not_counted_as_ungraded():
    """`goal_xy_tol` / `goal_yaw_tol` tune a check; they are not checks."""
    for path in ac.scene_paths():
        assert not (set(ac.ungraded_keys(path)) & set(PARAMS))


@pytest.mark.parametrize("key", GRADED)
def test_every_graded_key_returns_a_bool(key):
    """The defect was a `str` surviving where a `bool` was assumed. Pin the type
    for every rule, so a future rule cannot reintroduce it by returning None."""
    targets = {"collision": 0, "goal_reached": 1, "min_distance_to_obstacle": 0.3,
               "completion_min": 0.9}
    checks = check_acceptance({key: targets.get(key, 10.0)}, METRICS, 0.5)
    assert isinstance(checks[key], bool)


def test_jerk_lat_max_is_graded_and_discriminates():
    """The key this cycle wired: it must actually separate pass from fail, not
    just return a bool. `jerk_lat` was on every run already and read by nothing."""
    assert check_acceptance({"jerk_lat_max": 8.0}, METRICS, 0.5)["jerk_lat_max"]
    assert not check_acceptance({"jerk_lat_max": 1.0}, METRICS, 0.5)["jerk_lat_max"]


def test_unknown_key_is_reported_not_silently_dropped():
    """The shape of the original defect, pinned: an unknown key still yields the
    `"skipped"` str (callers depend on it), but it is no longer *only* that."""
    checks = check_acceptance({"no_such_criterion_max": 1.0}, METRICS, 0.5)
    assert checks["no_such_criterion_max"] == "skipped"
    assert not isinstance(checks["no_such_criterion_max"], bool)


def test_drift_reports_both_directions_via_an_injected_census():
    """The guard's two verdicts, driven without touching module state.

    An empty census must report every real gap as unpinned; a census naming a
    key that *is* graded must report a stale pin. Neither direction is reachable
    from the shipped census, which is exactly why `drift` takes a parameter.
    """
    unpinned = ac.drift(census={})
    assert unpinned and all(m.startswith("UNPINNED_UNGRADED:") for m in unpinned)
    stale = ac.drift(census={**ac.UNGRADED_CENSUS,
                             "cafe_straight_v0": ["cte_rms_max"]})
    assert any(m.startswith("CENSUS_STALE:") for m in stale)

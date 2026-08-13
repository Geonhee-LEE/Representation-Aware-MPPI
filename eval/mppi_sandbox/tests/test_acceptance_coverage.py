# SPDX-License-Identifier: BSD-3-Clause
"""Every acceptance criterion a scene declares is either graded or pinned as debt.

D-241 wired one such key after finding it by grep. These tests are the sweep that
makes the *next* one fail on the cycle that introduces it, plus the direction
check that keeps the guard from punishing the fix.

Deliberately controller-free: nothing here builds an MPPI, so the module stays
out of the default-lam census (D-124) and the suite cost stays near zero.
"""

from __future__ import annotations

import pytest

from eval.mppi_sandbox import acceptance_coverage as ac
from eval.mppi_sandbox.run import (ACCEPTANCE_PARAMS, ACCEPTANCE_RULES,
                                   check_acceptance)

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


def test_census_is_read_from_the_rules_table_not_a_copy():
    """D-047: the graded set has exactly one statement of itself."""
    doc = (ac.__doc__ or "") + (ac.ungraded_keys.__doc__ or "")
    for key in ACCEPTANCE_RULES:
        assert f'"{key}"' not in doc, (
            f"{key} is respelled in acceptance_coverage prose; the guard must "
            f"read run.ACCEPTANCE_RULES, never re-type it")


def test_every_remaining_gap_is_a_declared_top_three_criterion():
    """Records what the sweep measured: all 4 survivors sit in the scene's own
    `success_metric_priority`. This is why they are debt and not housekeeping."""
    assert ac.prioritised_but_ungraded() == ac.UNGRADED_CENSUS


def test_params_are_not_counted_as_ungraded():
    """`goal_xy_tol` / `goal_yaw_tol` tune a check; they are not checks."""
    for path in ac.scene_paths():
        assert not (set(ac.ungraded_keys(path)) & set(ACCEPTANCE_PARAMS))


@pytest.mark.parametrize("key", sorted(ACCEPTANCE_RULES))
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

# SPDX-License-Identifier: BSD-3-Clause
"""STATE's open tracking question: where does `heading_err_rms` come from
under `knee+shape` on `cafe_obstacle_crossing_v0`, on the 10/16 seeds that
still fail it once clearance is 16/16 green (D-430)?

See `heading_error_phase` module docstring for the full account, including
the discrete clearance-band phase split tried first and discarded as a
boundary artifact. This file pins both halves of that account: the artifact
(the barrier never actually enters its own declared band, so a same-valued
cutoff finds zero "avoidance" timesteps) and the answer that replaced it (a
threshold-free proximity/heading-error correlation, negative on all 16 seeds).

Cost: one ensemble (16 integrations, ~10 s, shared via a module fixture) plus
pure-function reads over its trajectories. No new controller code.
"""

from __future__ import annotations

import numpy as np
import pytest

from eval.mppi_sandbox.heading_error_phase import (
    AVOIDANCE_BAND,
    HEADING_ERR_RMS_MAX,
    NEAR_OBSTACLE_CLEARANCE,
    ROBOT_RADIUS,
    SEEDS,
    failing_seed_localization,
    heading_clearance_correlation,
    per_timestep_clearance,
    peak_heading_error_location,
    seed_sweep_knee_shape,
)
from eval.path_tracking_metrics import heading_error


@pytest.fixture(scope="module")
def ensemble():
    """(scenario, runs) for the `knee+shape` arm — 16 seeds, computed once."""
    return seed_sweep_knee_shape()


@pytest.fixture(scope="module")
def localization():
    return failing_seed_localization()


# ---------------------------------------------------- the artifact, pinned

def test_the_barrier_never_enters_its_own_band(ensemble):
    """Precondition for the whole finding: a `clearance <= AVOIDANCE_BAND`
    phase test cannot fire, on any seed, because the compact-support barrier
    holds clearance just *outside* its own declared band — not because
    avoidance never happens on this scene.
    """
    scenario, runs = ensemble
    mins = [
        per_timestep_clearance(r.traj, scenario.obstacles, ROBOT_RADIUS).min()
        for r in runs
    ]
    assert len(mins) == len(SEEDS)
    # Strictly above the band on every seed...
    assert min(mins) > AVOIDANCE_BAND
    # ...but only barely — this is a boundary the controller hugs, not a
    # comfortable margin. 0.05 m is 1/6 of the band itself.
    assert min(mins) < AVOIDANCE_BAND + 0.05


def test_failing_seeds_exist_and_are_the_expected_count(localization):
    """Reproduces D-430's headline count (6/16 pass, so 10/16 fail) on the
    same arm this module re-derives from scratch — a cross-check that the
    re-derivation did not silently change which seeds are being localized.
    """
    assert len(localization) == 10


# ------------------------------------------------------- the answer itself

def test_every_seed_couples_heading_error_to_proximity(ensemble):
    """rho(clearance, |heading_error|) is negative on *all 16* seeds — passing
    and failing alike. No seed shows the reverse or a null relationship; the
    coupling is a property of the scene/controller pair, not of failure.
    """
    scenario, runs = ensemble
    rhos = [
        heading_clearance_correlation(r.traj, scenario.waypoints, scenario.obstacles)
        for r in runs
    ]
    assert len(rhos) == len(SEEDS)
    assert all(rho < 0.0 for rho in rhos), rhos
    # Not a knife-edge either — comfortably negative on every seed.
    assert max(rhos) < -0.1, rhos


def test_failing_seeds_peak_error_sits_near_the_obstacle(localization):
    """Each failing seed's single worst heading-error instant occurs at
    clearance well inside `NEAR_OBSTACLE_CLEARANCE` — not out on the open
    stretch of the scene (measured cruising clearance ceiling ~3.0 m).
    """
    peaks = {seed: row["peak_clearance"] for seed, row in localization.items()}
    assert peaks, "expected at least one failing seed to localize"
    assert all(clr < NEAR_OBSTACLE_CLEARANCE for clr in peaks.values()), peaks


def test_localization_agrees_with_the_scenes_own_threshold(localization):
    """Every localized row is in fact a `heading_err_rms_max` failure by the
    scenario's own declared threshold — the localization and the acceptance
    rule are reading the same population, not two different cuts.
    """
    assert localization
    assert all(row["heading_rms"] > HEADING_ERR_RMS_MAX for row in localization.values())

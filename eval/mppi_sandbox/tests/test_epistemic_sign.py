# SPDX-License-Identifier: BSD-3-Clause
"""The sign of each shipped epistemic critic, read off its own cost.

The 08:00 research feed (PA-MPPI `2509.14978`) asserts this branch "has never
stated which of the two it is" — attract (reward observing the unknown) or
repel (penalise exposure to it). These tests are the refutation: the branch
ships **both**, and the signs are opposed on one geometry at one weight.
"""

import numpy as np
import pytest

from eval.mppi_sandbox.critics import ObservationValueCritic, ShadowCostCritic
from eval.mppi_sandbox.epistemic_sign import (ATTRACT, REPEL, SILENT,
                                              SPREAD_EPS, blind_corner,
                                              classify, probe_all,
                                              signs_are_opposed)


class TestTheTwoShippedSignsAreOpposed:
    """The headline: the sign question is answered by the code, not open."""

    def test_shadow_cost_is_repel_and_observation_value_is_attract(self):
        readings = probe_all()
        assert readings["ShadowCostCritic"].sign == REPEL
        assert readings["ObservationValueCritic"].sign == ATTRACT
        assert signs_are_opposed(readings)

    def test_both_arms_read_at_the_same_weight(self):
        """The sign is a property of the form, not of the weight — so the
        reading must not be explainable as a tuning difference. Sweeping the
        shared weight moves the magnitudes and leaves both signs put."""
        for w in (1.0, 10.0, 200.0):
            readings = probe_all(w=w)
            assert readings["ShadowCostCritic"].sign == REPEL
            assert readings["ObservationValueCritic"].sign == ATTRACT

    def test_entering_the_shadow_is_cheaper_under_the_attract_arm(self):
        """The behavioural statement the sign stands for: at a blind corner
        the attract arm prefers the shadow-revealing location that the repel
        arm charges for."""
        r = probe_all()
        assert r["ShadowCostCritic"].split > 0.0
        assert r["ObservationValueCritic"].split < 0.0


class TestWhyTheMeanSplitAndNotTheCorrelation:
    """`SIGN_STATISTIC = "mean_split"` is a choice, and this pins the reason:
    the correlation is decisive for a pointwise-in-σ cost and nearly signless
    for the aggregate-map cost, even though the latter's split is large."""

    def test_pointwise_cost_correlates_perfectly_with_sigma(self):
        r = probe_all()["ShadowCostCritic"]
        assert r.corr == pytest.approx(1.0)

    def test_aggregate_map_cost_is_decisive_by_split_and_weak_by_corr(self):
        r = probe_all()["ObservationValueCritic"]
        # V(q) is an aggregate over rays from q, not a function of sigma at q,
        # so the correlation understates a sign the split states plainly.
        assert abs(r.corr) < 0.5
        assert r.mean_exposed < 0.5 * r.mean_observed


class TestSilenceIsAThirdVerdictNotAWeakSign:
    """D-021 measured `ShadowCostCritic` signal-free on the crossing scene. A
    term with no spread has no sign; reporting it as weakly-repel would be the
    D-241 silent-vacuity shape."""

    def test_zero_weight_is_silent_under_both_arms(self):
        readings = probe_all(w=0.0)
        assert readings["ShadowCostCritic"].sign == SILENT
        assert readings["ObservationValueCritic"].sign == SILENT
        assert not signs_are_opposed(readings)

    def test_silence_is_decided_before_the_mean_split_is_consulted(self):
        """A constant *non-zero* cost has a mean split of exactly 0 either
        way, but the guard must fire on spread, not on the split — otherwise
        a float wobble in the means picks a sign out of pure silence."""
        sigma = np.array([1.0, 1.0, 0.0, 0.0])
        reading = classify(np.full(4, 7.5), sigma)
        assert reading.sign == SILENT
        assert reading.spread <= SPREAD_EPS
        assert reading.corr == 0.0

    def test_silent_is_disjoint_from_the_two_signs(self):
        assert SILENT not in (REPEL, ATTRACT)


class TestTheGeometryHasToPoseTheQuestion:
    def test_candidate_set_with_no_shadow_is_refused_not_graded(self):
        """A geometry where nothing is exposed cannot answer "does entering
        the shadow cost more" — it is refused rather than silently graded, the
        `headline_rescope` NOT_COMPARABLE pattern."""
        with pytest.raises(ValueError, match="does not pose the question"):
            classify(np.array([1.0, 2.0, 3.0]), np.zeros(3))

    def test_candidate_set_with_no_observed_point_is_refused(self):
        with pytest.raises(ValueError, match="does not pose the question"):
            classify(np.array([1.0, 2.0, 3.0]), np.ones(3))

    def test_mismatched_shapes_are_refused(self):
        with pytest.raises(ValueError, match="differ"):
            classify(np.zeros(3), np.zeros(4))

    def test_the_blind_corner_actually_casts_a_shadow(self):
        """Guards the whole module against a geometry regression: if the disc
        stopped casting a shadow every reading above would go SILENT and the
        suite would still be green without this."""
        _, _, _, points, sigma = blind_corner()
        assert (sigma > 0.5).sum() > 0
        assert (sigma <= 0.5).sum() > 0
        assert len(points) == len(sigma)


class TestTheReadingMatchesTheCriticsDirectly:
    """The instrument must not drift from the cost functions it reads — these
    recompute the two costs by hand and check the classification agrees."""

    def test_shadow_cost_reading_reproduces_the_critic(self):
        producer, bev, robot_xy, points, sigma = blind_corner()
        cost = ShadowCostCritic(w_epist=10.0).cost(bev, points, len(points))
        np.testing.assert_allclose(cost, 10.0 * sigma)
        assert classify(cost, sigma).sign == REPEL

    def test_observation_value_reading_reproduces_the_critic(self):
        producer, bev, robot_xy, points, sigma = blind_corner()
        cost = ObservationValueCritic(w_voo=10.0).cost(
            producer, bev, robot_xy, 0.0, points, len(points))
        assert (cost >= 0.0).all()          # add-only contract
        assert classify(cost, sigma).sign == ATTRACT

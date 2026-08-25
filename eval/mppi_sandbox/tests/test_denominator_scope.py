# SPDX-License-Identifier: BSD-3-Clause
"""D-028's denominator pair, re-read at the shipped temperature.

D-028 measured `w_voo = 200` at `lam = 1.6` and concluded three things beyond
the headline ratio pair: that the inflated denominator is ordinary path cost
and *not* the collision guard, that the understatement grows with the damage,
and that a cheap small-weight probe cannot pick a shipping weight. Each is
stated in `docs/decisions.md` without a temperature qualifier. The repo ships
`lam = 0.1`, and all three fail there.

The verdict-structure assertions are the deliverable; they are what a later
cycle re-running this on another scene needs to compare against. The exact
magnitudes are deliberately *not* pinned tightly -- D-034's rule, since this
branch's slow half is dispatch-fragile and a pinned excursion would be the
most fragile assertion in the repo. Structure is asserted; magnitude is
asserted only to the order that carries the argument.
"""

from __future__ import annotations

import pytest

from eval.mppi_sandbox.denominator_scope import (AUDITED_LAM, ISOLATION,
                                                 LOUD_WEIGHT, SHIPPED_LAM,
                                                 VERDICT_THRESHOLD,
                                                 DenominatorReading,
                                                 format_table, read)
from eval.mppi_sandbox.controllers.stock_mppi import MPPIParams
from eval.mppi_sandbox.scenario import load_scenario
from eval.mppi_sandbox.weight_units import closed_loop_per_unit_spread

CROSSING = "eval/scenarios/cafe_obstacle_crossing_v0.yaml"

_CACHE: dict = {}


def _scene():
    if "sc" not in _CACHE:
        _CACHE["sc"] = load_scenario(CROSSING)
    return _CACHE["sc"]


def _reading(lam: float) -> DenominatorReading:
    if lam not in _CACHE:
        _CACHE[lam] = read(_scene(), lam=lam)
    return _CACHE[lam]


def _fake(**kw) -> DenominatorReading:
    """A reading with every field defaulted, for the arithmetic tests."""
    base = dict(
        lam=0.1, weight=LOUD_WEIGHT, term="w_voo",
        self_ratio=1.0, against_baseline=1.0,
        rest_median=1.0, baseline_rest_median=1.0,
        dominant_term="w_path", dominant_spread=1.0,
        steps=100, baseline_steps=100,
        min_clearance=0.01, baseline_min_clearance=0.01,
        goal_distance=0.0, baseline_goal_distance=0.0,
    )
    base.update(kw)
    return DenominatorReading(**base)


class TestTheVerdictArithmetic:
    """Fast -- the properties that turn two ratios into a conclusion."""

    def test_a_ratio_above_one_reads_as_dominating(self):
        assert _fake(self_ratio=1.464).verdict == "dominates"
        assert _fake(self_ratio=0.0488).verdict == "negligible"

    def test_verdicts_disagree_only_when_they_straddle_the_threshold(self):
        both_high = _fake(self_ratio=1.464, against_baseline=13.4)
        straddle = _fake(self_ratio=0.0488, against_baseline=3.30)
        assert not both_high.verdicts_disagree, (
            "at lam=1.6 both denominators exceed 1, so D-028 could report a "
            "margin difference without the conclusion moving -- that is why "
            "the finding was filed as 'the denominator is the finding' rather "
            "than 'the denominator changes the answer'")
        assert straddle.verdicts_disagree

    def test_understatement_is_the_ratio_of_the_two_ratios(self):
        assert _fake(self_ratio=0.5, against_baseline=2.0).understatement == 4.0

    def test_threshold_is_the_d027_condition_not_a_tuned_constant(self):
        """`ratio > 1` means the term spans more than everything else put
        together. If a later cycle tunes this, the verdicts stop being
        comparable with `weight_units.TermSpread.ratio`'s docstring."""
        assert VERDICT_THRESHOLD == 1.0

    def test_the_table_renders_both_rows(self):
        out = format_table([_fake(lam=1.6), _fake(lam=0.1)])
        assert out.count("\n") == 4 and "denominator" in out


@pytest.mark.slow
class TestTheVerdictFlipsAtTheShippedTemperature:
    """Section 1 -- the result. Same scene, same weight, same seed."""

    def test_the_self_referential_verdict_inverts_between_the_two(self):
        audited, shipped = _reading(AUDITED_LAM), _reading(SHIPPED_LAM)
        assert audited.self_ratio > VERDICT_THRESHOLD, (
            f"D-028's 1.46x no longer exceeds 1 ({audited.self_ratio:.4g}); "
            f"the pair this module contrasts has moved and section 1 needs "
            f"re-deriving")
        assert shipped.self_ratio < VERDICT_THRESHOLD, (
            f"the shipped-temperature self-referential ratio "
            f"({shipped.self_ratio:.4g}) no longer calls the collapsing "
            f"weight negligible -- the trap may have closed on its own")

    def test_the_baseline_denominator_keeps_the_verdict_at_both(self):
        """The statistic that does *not* flip is the one D-027 used. That
        asymmetry is the argument for preferring it, and it is the reason
        this cycle is a scope correction rather than a retraction."""
        for lam in (AUDITED_LAM, SHIPPED_LAM):
            r = _reading(lam)
            assert r.against_baseline > VERDICT_THRESHOLD, (
                f"at lam={lam} the baseline denominator now also reads "
                f"negligible ({r.against_baseline:.4g}); neither statistic "
                f"detects the D-027 collapse and the instrument is unusable")

    def test_only_the_shipped_temperature_has_the_two_disagree(self):
        assert not _reading(AUDITED_LAM).verdicts_disagree
        assert _reading(SHIPPED_LAM).verdicts_disagree

    def test_the_understatement_grows_by_an_order_of_magnitude(self):
        audited, shipped = _reading(AUDITED_LAM), _reading(SHIPPED_LAM)
        assert shipped.understatement > 5 * audited.understatement, (
            f"understatement {audited.understatement:.3g}x -> "
            f"{shipped.understatement:.3g}x is no longer a large move; the "
            f"headline of section 1 is scene- or version-specific")


@pytest.mark.slow
class TestD028sMechanismIsTemperatureConditional:
    """Sections 2 and 3 -- the three supporting claims, each stated in
    `docs/decisions.md` without a `lam` qualifier, each false at `lam = 0.1`."""

    def test_the_collision_guard_supplies_the_shipped_denominator(self):
        """D-028 Decision (3) ruled the collision term out: median spread
        exactly 0 on *both* arms, so a guard and not a competitor. At the
        shipped temperature it is the largest term inside `rest`."""
        assert _reading(AUDITED_LAM).dominant_term == "w_path", (
            "D-028's mechanism (ordinary path cost on a derailed arm) no "
            "longer holds at the temperature D-028 measured")
        assert _reading(SHIPPED_LAM).dominant_term == "w_collision", (
            "section 2's finding was that the guard captures the denominator "
            "at the shipped temperature; it no longer does")

    def test_nothing_actually_collides_at_either_temperature(self):
        """The `1e4` is a spread over the rollout cloud, not a crash. Stated
        as a test because the number invites exactly the wrong reading, and
        because 'the loud arm collides' would be a stronger claim than the
        data supports."""
        for lam in (AUDITED_LAM, SHIPPED_LAM):
            r = _reading(lam)
            assert r.min_clearance > 0.0 and r.baseline_min_clearance > 0.0, (
                f"at lam={lam} an arm now genuinely collides; the rollout-"
                f"cloud-straddle explanation in section 2 is no longer the "
                f"whole story")

    def test_the_shipped_loud_arm_is_healthier_yet_understated_more(self):
        """Section 3 -- the refutation of "the understatement grows with the
        damage". Damage falls on every axis available while the
        understatement rises."""
        audited, shipped = _reading(AUDITED_LAM), _reading(SHIPPED_LAM)
        assert shipped.step_inflation < audited.step_inflation / 3, (
            f"the shipped-temperature loud arm no longer finishes far sooner "
            f"({shipped.step_inflation:.3g}x vs {audited.step_inflation:.3g}x "
            f"step inflation); the damage comparison section 3 rests on is gone")
        assert shipped.goal_distance < audited.goal_distance / 3, (
            "the shipped loud arm no longer ends up much closer to the goal")
        assert shipped.understatement > audited.understatement, (
            "damage fell and the understatement did not rise -- section 3's "
            "claim that damage is the wrong driver loses its counterexample")

    def test_the_exchange_rate_is_transferable_at_the_shipped_temperature(self):
        """Section 4 -- D-028 Decision (5) said a cheap small-weight probe
        cannot choose a shipping weight (2.27x swing). At `lam = 0.1` the
        ladder is flat, so that methodology rule is `lam = 1.6`-specific."""
        ladder = closed_loop_per_unit_spread(
            _scene(), "w_voo", [1.0, 7.0, LOUD_WEIGHT],
            params=MPPIParams(lam=SHIPPED_LAM), **ISOLATION)
        swing = max(ladder) / min(ladder)
        assert swing < 1.3, (
            f"the shipped-temperature exchange-rate ladder swings {swing:.3g}x "
            f"({['%.4g' % x for x in ladder]}); D-028 Decision (5)'s "
            f"non-transferability is no longer temperature-specific")

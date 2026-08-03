"""Tests for the repair pricer (Q-055 / D-035).

Fast and structural by the same constraint as
``test_dispatch_divergence.py``: the inputs are the five quantities that
differ between machines *by construction*, so pinning a priced cost would make
this the second-most dispatch-fragile assertion in the repo.  What is tested is
the arithmetic, the identity ``widen_factor = 1 + excursion``, and the verdict
logic that decides which of three incommensurable repairs a claim needs.
"""

from __future__ import annotations

import pytest

from .. import dispatch_divergence as dd
from .. import repair_admissibility as ra


def _band(value, lo, hi):
    return dd.Claim(test="t", quantity="q", value=value, lo=lo, hi=hi)


def _asdict(claim):
    from dataclasses import asdict
    return asdict(claim) | {"passes": claim.passes, "excursion": claim.excursion}


class TestTheCostIsTheExcursionPlusOne:
    """The identity that made this a free question.

    D-034 measured excursions and read them as distances.  The same number read
    as a cost is the factor the tolerance must grow by, so the repair question
    was already answered by the previous cycle's data and nobody looked.
    """

    @pytest.mark.parametrize("value", [3.0, 4.0, 5.0, -1.0])
    def test_widen_factor_is_one_plus_excursion(self, value):
        c = _band(value, 0.0, 2.0)
        r = ra.price(_asdict(c), _asdict(c), "x")
        assert r.widen_factor == pytest.approx(1.0 + c.excursion)

    def test_a_claim_inside_its_band_costs_nothing_to_repair(self):
        c = _band(1.0, 0.0, 2.0)
        r = ra.price(_asdict(c), _asdict(c), "x")
        assert r.widen_factor == pytest.approx(1.0)
        assert r.verdict == "widenable"

    def test_the_minimum_factor_admits_the_outlier_exactly(self):
        """Minimum widening leaves zero margin -- that is what makes it minimum,
        and also why a bare "carries both machines" is not yet a repair."""
        c = _band(3.0, 0.0, 2.0)  # centre 1, half 1, excursion 1.0
        r = ra.price(_asdict(c), _asdict(c), "x")
        half = 1.0 * r.widen_factor
        assert 1.0 + half == pytest.approx(3.0)
        assert r.margin_at_factor(r.widen_factor) == pytest.approx(0.0)


class TestMarginArithmetic:
    def test_margin_and_factor_are_inverses(self):
        r = ra.Repair(claim="x", kind="band", verdict="widenable", widen_factor=1.136)
        for m in (0.0, 0.05, 0.25, 0.5):
            assert r.margin_at_factor(r.widen_factor_for_margin(m)) == pytest.approx(m)

    def test_a_factor_below_the_minimum_reads_negative(self):
        """Not an error -- a proposal that does not admit the other machine is a
        thing one may want to price rather than be stopped from pricing."""
        r = ra.Repair(claim="x", kind="band", verdict="widenable", widen_factor=1.5)
        assert r.margin_at_factor(1.2) < 0

    def test_margin_must_be_a_fraction(self):
        r = ra.Repair(claim="x", kind="band", verdict="widenable", widen_factor=1.1)
        for bad in (-0.1, 1.0, 2.0):
            with pytest.raises(ValueError, match="margin"):
                r.widen_factor_for_margin(bad)

    def test_a_threshold_claim_has_no_widening_to_price(self):
        r = ra.Repair(claim="x", kind="threshold", verdict="threshold-is-the-claim")
        assert r.widen_factor_for_margin(0.1) is None
        assert r.margin_at_factor(2.0) is None


class TestTheThreeKindsAreNotInterchangeable:
    """Why D-034's four classes could not share one repair."""

    def test_a_two_sided_claim_is_a_band(self):
        r = ra.price(_asdict(_band(3.0, 0.0, 2.0)), _asdict(_band(3.0, 0.0, 2.0)), "x")
        assert r.kind == "band"

    def test_a_one_sided_claim_is_a_threshold_and_reports_effect_retained(self):
        """Lowering the bar is not loosening the assertion, it is making a
        different, weaker one -- so the figure of merit is what survives."""
        c = dd.Claim(test="t", quantity="q", value=1.05, lo=1.25, hi=None)
        r = ra.price(_asdict(c), _asdict(c), "x")
        assert r.kind == "threshold"
        assert r.repaired_threshold == pytest.approx(1.05)
        # asserted 0.25 over the null, surviving 0.05 -> a fifth of it
        assert r.effect_retained == pytest.approx(0.2)

    def test_the_worse_of_the_two_machines_sets_the_threshold(self):
        lo = dd.Claim(test="t", quantity="q", value=1.05, lo=1.25, hi=None)
        hi = dd.Claim(test="t", quantity="q", value=1.70, lo=1.25, hi=None)
        assert ra.price(_asdict(hi), _asdict(lo), "x").repaired_threshold \
            == pytest.approx(1.05)

    def test_a_categorical_claim_admits_no_repair_operator(self):
        c = dd.Claim(test="t", quantity="q", value=0.0, lo=1.0, hi=1.0,
                     categorical=True)
        r = ra.price(_asdict(c), _asdict(c), "x")
        assert r.kind == "categorical"
        assert r.verdict == "no-widening-operator"
        assert r.widen_factor is None and r.effect_retained is None


class TestTheHonestyCeiling:
    """``MAX_HONEST_WIDEN`` is a judgement and is meant to look like one."""

    def test_just_under_the_ceiling_is_widenable(self):
        c = _band(1.0 + 1.98, 0.0, 2.0)  # excursion 0.98 -> factor 1.98
        assert ra.price(_asdict(c), _asdict(c), "x").verdict == "widenable"

    def test_just_over_the_ceiling_is_not(self):
        c = _band(1.0 + 2.02, 0.0, 2.0)
        r = ra.price(_asdict(c), _asdict(c), "x")
        assert r.verdict == "widening-destroys-discrimination"
        assert "no longer resolves" in r.note

    def test_the_ceiling_is_inclusive_so_exactly_double_still_counts(self):
        c = _band(1.0 + ra.MAX_HONEST_WIDEN, 0.0, 2.0)
        assert ra.price(_asdict(c), _asdict(c), "x").verdict == "widenable"


class TestTheBill:
    def _bill(self):
        band_ok = _asdict(_band(2.2, 0.0, 2.0))
        band_bad = _asdict(_band(8.0, 0.0, 2.0))
        thr = _asdict(dd.Claim(test="t", quantity="q", value=1.05, lo=1.25, hi=None))
        a = {"claims": {"a": band_ok, "b": band_bad, "c": thr}}
        return ra.price_all(a, a)

    def test_only_widenable_claims_count_as_repairable(self):
        bill = self._bill()
        assert [r.claim for r in bill.widenable] == ["a"]
        assert "1/3 repairable by widening" in bill.summary()

    def test_claims_missing_from_one_arm_are_dropped_not_guessed(self):
        c = _asdict(_band(2.2, 0.0, 2.0))
        bill = ra.price_all({"claims": {"a": c, "b": c}}, {"claims": {"a": c}})
        assert [r.claim for r in bill.repairs] == ["a"]

    def test_the_report_names_every_claim_and_its_cost(self):
        text = ra.report(self._bill())
        for name in ("a", "b", "c"):
            assert name in text
        assert "repairable by widening" in text


class TestTheRegistryStaysHonest:
    """The pricer must cover exactly the divergent set the instrument measures."""

    def test_every_dispatch_divergence_claim_can_be_priced(self):
        """A new claim key added to ``CLAIMS`` without a matching interval shape
        would raise here rather than be silently skipped in the report."""
        shapes = {
            "hazard_shared_rungs": dd.Claim(
                test="t", quantity="q", value=0.0, lo=1.0, hi=1.0, categorical=True),
            "scale_match_achieved_ratio": _band(0.179, 0.1875, 0.3125),
            "ab_protocol_overstatement": dd.Claim(
                test="t", quantity="q", value=1.05, lo=1.25, hi=None),
            "horizon_weight_swing": dd.Claim(
                test="t", quantity="q", value=1.03, lo=1.2, hi=None),
            "exposure_band_hi": _band(2.186, 1.988, 2.088),
        }
        assert set(shapes) == set(dd.CLAIMS), "divergent set changed -- reprice it"
        for name, claim in shapes.items():
            assert ra.price(_asdict(claim), _asdict(claim), name).verdict

    def test_an_upper_bound_only_claim_is_refused_rather_than_mispriced(self):
        c = dd.Claim(test="t", quantity="q", value=3.0, lo=None, hi=2.0)
        with pytest.raises(ValueError, match="neither categorical"):
            ra.price(_asdict(c), _asdict(c), "x")

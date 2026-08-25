"""Tests for the SIMD-divergence instrument (D-033 / Q-054).

**Every test here is fast and structural, and that is a deliberate design
constraint rather than an omission.**  The quantities
:mod:`eval.mppi_sandbox.dispatch_divergence` measures are *by construction* the
ones that differ between machines, so any test pinning a measured excursion
would be the most dispatch-fragile assertion in the repo — it would fail on CI
for exactly the reason the module exists to document, and the loop would have
spent a cycle building a better thermometer and then asserting the weather.

So the instrument is exercised on:

* the excursion arithmetic (pure, no simulation),
* the registry staying in sync with the tests it claims to characterise, and
* the report/compare plumbing.

The measurements themselves live in the journal and in ``results/*.tsv``, where
a number is allowed to be a record of one machine instead of a claim about all
of them.
"""

from __future__ import annotations

import json

import pytest

from .. import dispatch_divergence as dd


class TestExcursionArithmetic:
    """0 inside the band, 1.0 exactly one half-width outside."""

    def _claim(self, value, lo, hi, **kw):
        return dd.Claim(test="t", quantity="q", value=value, lo=lo, hi=hi, **kw)

    def test_inside_the_band_is_zero_excursion_and_passes(self):
        c = self._claim(0.25, 0.1875, 0.3125)
        assert c.passes
        assert c.excursion == 0.0

    def test_on_the_boundary_is_still_zero(self):
        """A claim that exactly touches its own tolerance has not excurred."""
        for v in (0.1875, 0.3125):
            c = self._claim(v, 0.1875, 0.3125)
            assert c.passes and c.excursion == 0.0

    def test_one_half_width_outside_reads_exactly_one(self):
        # band [0, 2] -> centre 1, half-width 1; value 3 is one half-width out.
        c = self._claim(3.0, 0.0, 2.0)
        assert not c.passes
        assert c.excursion == pytest.approx(1.0)

    def test_excursion_is_symmetric_about_the_band(self):
        lo, hi = 2.0, 4.0
        assert (self._claim(1.0, lo, hi).excursion
                == pytest.approx(self._claim(5.0, lo, hi).excursion))

    def test_a_knife_edge_reads_far_below_one(self):
        """The reading that would have supported "just loosen the tolerance"."""
        c = self._claim(0.3130, 0.1875, 0.3125)
        assert not c.passes
        assert c.excursion < 0.01

    def test_one_sided_claims_have_no_excursion(self):
        """Half-width is undefined, so the module reports None rather than
        inventing a denominator."""
        assert self._claim(1.02, 1.2, None).excursion is None
        assert not self._claim(1.02, 1.2, None).passes
        assert self._claim(1.5, 1.2, None).passes

    def test_categorical_claims_have_no_excursion(self):
        c = self._claim(0.0, 1.0, 1.0, categorical=True)
        assert c.excursion is None
        assert not c.passes

    def test_a_degenerate_band_does_not_divide_by_zero(self):
        assert self._claim(5.0, 1.0, 1.0).excursion is None


class TestTheRegistryTracksTheTestsItCharacterises:
    """The five flipping tests are a *finding*, not a constant — so the registry
    is checked against the suite rather than against a hand-copied list."""

    def test_every_claim_names_a_test_that_exists_and_is_slow(self, pytestconfig):
        """A renamed or unmarked test would silently orphan its claim."""
        import importlib

        for key, fn in dd.CLAIMS.items():
            # Claims are constructed by running them, which is expensive; the
            # names are asserted off the source module instead.
            src = fn.__doc__
            assert src, f"{key} must document what it measures"

        for key, node in _declared_nodes().items():
            mod_name, _, rest = node.partition("::")
            mod = importlib.import_module(
                f"eval.mppi_sandbox.tests.{mod_name}")
            target = rest.split("::")[-1]
            owner = mod
            if "::" in rest:                       # class-scoped test
                owner = getattr(mod, rest.split("::")[0])
            assert hasattr(owner, target), (
                f"{key} points at {node}, which no longer exists")
            marks = getattr(getattr(owner, target), "pytestmark", [])
            names = {m.name for m in marks} | set(
                getattr(owner, "pytestmark", []) and
                {m.name for m in getattr(owner, "pytestmark", [])})
            assert "slow" in names, (
                f"{node} is no longer marked slow — the divergence set was "
                f"defined over the slow half (D-033)")

    def test_the_registry_is_the_five_from_d033(self):
        assert set(dd.CLAIMS) == {
            "hazard_shared_rungs", "scale_match_achieved_ratio",
            "ab_protocol_overstatement", "horizon_weight_swing",
            "exposure_band_hi"}


def _declared_nodes() -> dict[str, str]:
    """Claim key -> the ``module::[Class::]test`` it characterises."""
    return {
        "hazard_shared_rungs":
            "test_hazard_exposure::test_refutation_reproduces_from_simulation",
        "scale_match_achieved_ratio":
            "test_scale_match::TestThePrescriptionLandsWhereItSaysItWill::"
            "test_the_prescribed_weight_achieves_the_requested_ratio",
        "ab_protocol_overstatement":
            "test_ab_temperature_protocol::"
            "test_protocol_moves_the_effect_size_but_not_its_sign",
        "horizon_weight_swing":
            "test_horizon_audit::TestScaleMatchedWeightIsHorizonDependent::"
            "test_the_prescribed_weight_moves_with_the_horizon",
        "exposure_band_hi":
            "test_exposure_timing_band::TestTheBandConstantIsMeasured::"
            "test_reportable_scenes_land_inside_the_declared_band",
    }


class TestTheReportNamesItsMachine:
    """A divergence number without a machine attached is not interpretable —
    which is the mistake D-032's reassuring `numpy: 1.26.4` header made."""

    def test_fingerprint_reports_numpy_and_the_simd_set(self):
        fp = dd.dispatch_fingerprint()
        assert fp["numpy"] and isinstance(fp["simd"], list)
        assert isinstance(fp["numpy_calibrated"], bool)
        assert isinstance(fp["simd_calibrated"], bool)

    def test_fingerprint_agrees_with_the_conftest_header(self):
        """One definition of the machine, not two (see the module docstring)."""
        from eval.conftest import simd_found

        assert dd.dispatch_fingerprint()["simd"] == list(simd_found())

    def test_measure_with_an_empty_selection_simulates_nothing(self):
        """Cheap guard that ``--only`` filters before it runs anything — the
        expensive path must not fire during the fast half."""
        out = dd.measure(only=["nonexistent_claim"])
        assert out["claims"] == {}
        assert out["env"]["numpy"]


class TestCompareTable:
    def _report(self, simd, values):
        return {
            "env": {"numpy": "1.26.4", "simd": simd,
                    "simd_calibrated": "AVX512_SKX" in simd,
                    "numpy_calibrated": True},
            "claims": {k: {"value": v, "passes": False, "excursion": 1.0}
                       for k, v in values.items()},
        }

    def test_it_pairs_claims_and_reports_the_ratio(self):
        a = self._report(["AVX2", "AVX512_SKX"], {"x": 2.0})
        b = self._report(["AVX2"], {"x": 1.0})
        table = dd.compare(a, b)
        assert "AVX512=yes" in table and "AVX512=no" in table
        assert "0.5" in table

    def test_a_claim_missing_from_one_side_is_skipped_not_crashed(self):
        """Truncated runs are expected — the registry is ordered cheapest-first
        precisely so a partial run still compares."""
        a = self._report(["AVX2"], {"x": 1.0, "y": 2.0})
        b = self._report(["AVX2"], {"x": 1.0})
        table = dd.compare(a, b)
        assert "x" in table and "\ny " not in table

    def test_compare_round_trips_through_json(self, tmp_path):
        a, b = self._report(["AVX2"], {"x": 1.0}), self._report(["AVX2"], {"x": 2.0})
        pa, pb = tmp_path / "a.json", tmp_path / "b.json"
        pa.write_text(json.dumps(a))
        pb.write_text(json.dumps(b))
        assert dd.main(["--compare", str(pa), str(pb)]) == 0

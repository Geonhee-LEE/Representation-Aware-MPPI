"""Tests for :mod:`eval.mppi_sandbox.drift_repair` (D-099).

Same rule as :mod:`dispatch_divergence` and :mod:`repair_admissibility`: nothing
here pins a dispatch-dependent *value*, because such a test would fail on CI for
exactly the reason the module documents.  What is pinned is the parsing, the
routing, the refusals, and the correspondence between the conftest's marker set
and the measurement that licenses it.
"""

from __future__ import annotations

import pytest

from eval.mppi_sandbox import drift_repair as dr
from eval.mppi_sandbox import repair_admissibility as ra
from eval.mppi_sandbox import simd_attribution as sa


class TestSignatureShapes:
    """CI's own text decides the shape; nothing is hand-assigned."""

    def test_every_measured_row_parses(self):
        by_id = {f.test_id: f for f in sa.CI_FAILURES}
        unparsed = [
            r.test_id
            for r in dr.routes()
            if dr.classify(r.test_id, by_id[r.test_id].signature) is None
        ]
        assert unparsed == [], f"signatures the parser declined: {unparsed}"

    def test_band_target_and_tolerance_are_recovered(self):
        a = dr.classify("t", "assert 0.179 == 0.25 ± 0.0625")
        assert a.shape == dr.BAND
        assert a.lo == pytest.approx(0.1875)
        assert a.hi == pytest.approx(0.3125)

    def test_a_product_bound_is_multiplied_out(self):
        a = dr.classify("t", "assert 0.0362 > (1.25 * 0.03433654744256881)")
        assert a.shape == dr.THRESHOLD and a.side == "lower"
        assert a.bound == pytest.approx(1.25 * 0.03433654744256881)

    def test_a_quotient_bound_is_divided_out(self):
        a = dr.classify("t", "assert 0.2896 < (0.12417971687770564 / 3)")
        assert a.shape == dr.THRESHOLD and a.side == "upper"
        assert a.bound == pytest.approx(0.12417971687770564 / 3)

    def test_a_set_equality_is_categorical(self):
        assert dr.classify("t", "assert set() == {0.4}").shape == dr.CATEGORICAL

    def test_an_unrecognised_signature_is_declined_not_guessed(self):
        assert dr.classify("t", "assert not True") is None
        assert dr.classify("t", "") is None

    def test_sigfigs_reads_the_rendering_not_the_value(self):
        """D-098's defect in one line: same number, different digit count."""
        assert dr._sigfigs("0.0625") == 3
        assert dr._sigfigs("6.2e-02") == 2
        assert dr._sigfigs("0.05") == 1


class TestRouteBIsASpecialCaseNotARoute:
    """The headline: widening repairs one of the six."""

    def test_widening_is_defined_only_for_bands(self):
        table = dr.routes()
        for r in table:
            has_factor = r.widen_factor is not None
            assert has_factor == (r.shape == dr.BAND), (
                f"{r.test_id}: shape {r.shape} priced a widen factor"
                if has_factor
                else f"{r.test_id}: band with no factor"
            )

    def test_a_minority_of_the_population_is_widenable(self):
        verdicts = [r.widen_verdict for r in dr.routes()]
        widenable = verdicts.count(dr.WIDENABLE)
        assert 0 < widenable < len(verdicts) / 2, (
            "route (b) repairing most of the population would make this module "
            f"pointless; repairing none would make it unfalsifiable. got "
            f"{widenable}/{len(verdicts)}"
        )

    def test_a_threshold_is_refused_a_price_rather_than_given_a_wrong_one(self):
        """The refusal is the finding — ``RATIO_NULL`` is not this population's."""
        a = dr.classify("t", "assert 0.0362 > (1.25 * 0.03433654744256881)")
        verdict, factor, note = dr.price_widening(a)
        assert verdict == dr.NO_NULL_SUPPLIED
        assert factor is None
        assert "population" in note

    def test_borrowing_ratio_null_here_would_have_read_as_reassuring(self):
        """Why the refusal is not pedantry: the wrong answer is *comforting*.

        Both terms of ``(worst - null) / (lo - null)`` go negative when the null
        is above the bound, so the quotient comes out just over 1 and reads as
        "the repair keeps the whole asserted effect".  A negative or a
        ``ZeroDivisionError`` would have flagged itself; ~100% does not, which is
        why :func:`drift_repair.price_widening` must refuse rather than delegate.
        """
        wrong = ra.price(
            {"value": 0.0362}, {"value": 0.0362, "lo": 0.042920684303210}, "t"
        )
        assert wrong.effect_retained == pytest.approx(1.0, abs=0.05), (
            f"expected the misuse to read as ~100% retained, got "
            f"{wrong.effect_retained}"
        )

    def test_the_band_identity_is_delegated_not_restated(self):
        """``widen_factor = 1 + excursion`` must have one statement (D-047).

        Checked twice, because the cheap check is the one that misfires.  A raw
        text scan for the identity flags this module's own *prose* describing the
        delegation -- it did, on the first run -- which is the literal-scan
        hazard D-095 paid for.  So: strip docstrings via ``ast`` before scanning,
        and pin the delegation *behaviourally* as well, so a local
        recomputation that later drifts fails on the number rather than on a
        string.
        """
        import ast

        tree = ast.parse(open(dr.__file__, encoding="utf-8").read())
        for node in ast.walk(tree):
            if isinstance(node, (ast.Module, ast.ClassDef,
                                 ast.FunctionDef, ast.AsyncFunctionDef)):
                if (node.body and isinstance(node.body[0], ast.Expr)
                        and isinstance(node.body[0].value, ast.Constant)
                        and isinstance(node.body[0].value.value, str)):
                    node.body.pop(0)
        code = ast.unparse(tree)
        assert "1 + excursion" not in code and "1.0 + excursion" not in code, (
            "the widen identity is recomputed in drift_repair's code instead of "
            "delegated to repair_admissibility.price"
        )

        a = dr.classify("t", "assert 0.179 == 0.25 ± 0.0625")
        half = (a.hi - a.lo) / 2.0
        centre = (a.lo + a.hi) / 2.0
        exc = max(0.0, (abs(a.value - centre) - half) / half)
        _, factor, _ = dr.price_widening(a)
        assert factor == ra.price(
            {"value": centre},
            {"value": a.value, "lo": a.lo, "hi": a.hi, "excursion": exc},
            "t",
        ).widen_factor

    def test_widening_above_the_honest_cap_is_named_as_destroying(self):
        far = dr.classify("t", "assert 2.1857 == 2.038 ± 0.05")
        verdict, factor, _ = dr.price_widening(far)
        assert verdict == dr.WIDENING_DESTROYS
        assert factor > ra.MAX_HONEST_WIDEN

    def test_an_imprecise_tolerance_only_ever_caps_the_reported_digits(self):
        a = dr.classify("t", "assert 0.179 == 0.25 ± 6.2e-02")
        assert a.imprecise
        _, factor, note = dr.price_widening(a)
        assert "s.f." in note
        rendered = dr.Route("t", dr.BAND, dr.WIDENABLE, factor).widen_factor_text
        assert len(rendered.split(".")[-1]) == 2, (
            f"a capped factor must not print more than 2 decimals: {rendered}"
        )


class TestRouteAIsLicensedPerTestNotPerMachine:

    def test_the_markable_set_is_exactly_the_measured_drift_set(self):
        drift = {
            t
            for t, v in sa.verdicts().items()
            if v in {sa.DRIFT_CONSISTENT, sa.DRIFT_SHAPED}
        }
        assert dr.markable() == frozenset(drift)

    def test_rows_with_no_reading_are_refused(self):
        refused = set(dr.refused())
        assert refused, "the refusal set is empty — has Q-092 been answered?"
        assert not (refused & dr.markable()), (
            "a row with no dispatch reading is being marked as dispatch drift — "
            "the banner's error, mechanised"
        )

    def test_every_marked_row_is_attributable(self):
        attributable = {f.test_id for f in sa.attributable()}
        assert dr.markable() <= attributable, (
            "a TIMEOUT row cannot be attributed to dispatch; it has no number"
        )

    def test_an_empty_reading_set_grades_vacuous_not_routed(self):
        assert dr.grade(readings=()) == dr.VACUOUS

    def test_the_grade_reports_a_residue_rather_than_green(self):
        """STATE #4 said this turns the job green.  It does not, and says so."""
        assert dr.grade() == dr.RESIDUE

    def test_fully_routed_is_reachable_so_residue_is_falsifiable(self):
        """A grade that cannot come out clean is not a measurement."""
        readable = tuple(
            r
            for r in sa.MEASURED_2026_08_06
            if r.test_id in {f.test_id for f in sa.attributable()}
        )
        census = tuple(
            f
            for f in sa.CI_FAILURES
            if f.cause != sa.ASSERTION
            or f.test_id in {r.test_id for r in readable}
        )
        assert dr.grade(census=census, readings=readable) == dr.FULLY_ROUTED

    def test_route_c_is_priced_by_count_because_it_unmeasures_the_claims(self):
        assert dr.rebaseline_cost() == len(dr.markable())


class TestTheConftestAppliesWhatTheModuleDerives:

    def test_the_marker_set_is_not_hand_typed_in_the_conftest(self):
        from pathlib import Path

        text = Path(sa.__file__).parents[1].joinpath("conftest.py").read_text()
        assert "drift_repair" in text, "conftest must derive the set, not list it"
        for node in dr.markable():
            assert node not in text, (
                f"{node} is hand-typed in eval/conftest.py; it must come from "
                f"drift_repair.markable() so it cannot drift from the reading"
            )

    def test_the_conftest_marks_strictly(self):
        from pathlib import Path

        text = Path(sa.__file__).parents[1].joinpath("conftest.py").read_text()
        assert "strict=True" in text, (
            "a non-strict xfail absorbs a pass silently, so the day the drift "
            "stops nobody learns"
        )

    def test_the_header_announces_the_marking_either_way(self):
        import eval.conftest as c

        line = c._drift_line()
        assert line.startswith("eval drift-xfail:")
        assert ("inactive" in line) == (c.CALIBRATED_SIMD in c.simd_found())

    def test_a_zero_mark_on_an_active_dispatch_is_announced_not_silent(self, monkeypatch):
        """Absence-read-as-clean, the eleventh time: 0 marks must be loud."""
        import eval.conftest as c

        monkeypatch.setattr(c, "simd_found", lambda: ("SSE", "AVX2"))
        monkeypatch.setattr(c, "drift_xfail_ids", lambda: ())
        line = c._drift_line()
        assert "ACTIVE but marked 0" in line and "only notice" in line

    def test_marking_is_inactive_on_the_calibrated_dispatch(self, monkeypatch):
        """On the box where the constants are valid, a regression must still fail."""
        import eval.conftest as c

        monkeypatch.setattr(c, "simd_found", lambda: ("AVX2", c.CALIBRATED_SIMD))

        class _Stash(dict):
            def get(self, k, d=None):
                return dict.get(self, k, d)

        class _Cfg:
            stash = _Stash()

            def getoption(self, _):
                return True

        items = [type("I", (), {"nodeid": n, "add_marker": _fail})()
                 for n in dr.markable()]
        c._mark_drift_xfails(_Cfg(), items)
        assert _Cfg.stash[c._DRIFT_MARKED] == 0


def _fail(_marker):
    raise AssertionError("marked a test on the calibrated dispatch")

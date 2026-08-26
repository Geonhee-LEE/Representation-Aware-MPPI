"""The operating-point census must keep reproducing, and keep inverting Q-059.

Fast tests only -- yaml reads, a dataclass default, and arithmetic over them.
Nothing simulates, so nothing here is dispatch-fragile (same property that lets
``test_claim_scope`` police claims that are).
"""

from __future__ import annotations

import pytest

from eval.mppi_sandbox import claim_scope as cs
from eval.mppi_sandbox import operating_point as op


def test_registry_covers_exactly_the_scoped_claims():
    """A sixth scoped claim must get an operating point, not be skipped."""
    assert set(op.CLAIM_OPERATING_POINTS) == {sc.claim for sc in cs.SCOPED_CLAIMS}


def test_shipped_lam_is_read_from_the_dataclass_not_transcribed():
    """If someone changes the default, this census must move with it."""
    from eval.mppi_sandbox.controllers.stock_mppi import MPPIParams

    assert op.SHIPPED_LAM == MPPIParams().lam


def test_every_registered_cell_has_a_calibrated_window():
    """A registry entry naming an uncalibrated cell is stale, not admissible.

    This is the guard D-037 found missing one level up: the failure mode of a
    hand-maintained registry is a surface nobody looks at, so the lookup raises
    instead of defaulting.
    """
    win = op.windows()
    for claim, ops in op.CLAIM_OPERATING_POINTS.items():
        for point in ops:
            assert (point.scene, point.controller) in win, f"{claim}: {point}"


class TestTheShippedTemperatureIsAdmissibleInExactlyOneArm:
    """Was `TestTheShippedTemperatureIsAdmissibleNowhere`; D-477 falsified the
    name, and the replacement is a sharper finding than the one it retires.

    Q-059's lean (c) wanted a *ratio* and for as long as the table was 24 cells
    the ratio was 0/24 — every cell carried 0.1 on its ladder (the test below
    still pins that) and no cell admitted it. The 8-controller install did not
    merely add rows: it added **rungs**, 0.05 and 0.1 entering `ladder_census`
    for the first time, and eight cells now admit the temperature the robot
    actually ships at.

    The renaming is the point. A class asserting "nowhere" that had simply been
    re-pointed at a table where the answer is "somewhere" would keep passing
    while measuring a different claim — the D-317 shape, three times over in
    this same install. So the name moves with the assertion.
    """

    def test_exactly_one_controller_admits_the_shipped_lam(self):
        """And the shape of the eight is the finding, not the count.

        They are one controller across every scene, not a scattering of lucky
        cells: `essps_mppi` admits 0.1 everywhere and no other arm admits it
        anywhere. Asserted as `{arm}` rather than `== 8` so that a *ninth* cell
        arriving under the same arm (a new scene) leaves this green, while the
        thing worth hearing about — a second arm reaching the shipped rung —
        goes red.
        """
        admitting = {
            arm for (_scene, arm), window in op.windows().items()
            if op.SHIPPED_LAM in window
        }

        assert admitting == {"essps_mppi"}
        assert op.ladder_census()[op.SHIPPED_LAM] == 8

    def test_the_shipped_lam_is_still_a_refusal_for_every_other_arm(self):
        """The half that did not change, restated so it keeps a witness.

        `stock_mppi` is the arm the shipped default belongs to, and it admits
        0.1 in no scene at all. Losing this alongside the rename would leave
        "0.1 is admissible" reading as a general clearance when it is one arm's
        property.
        """
        stock = {
            scene for (scene, arm), window in op.windows().items()
            if arm == "stock_mppi" and op.SHIPPED_LAM in window
        }

        assert stock == set()

    def test_the_shipped_lam_was_on_the_ladder_in_every_cell(self):
        """Zero cells is a *refusal*, not a gap in the sweep -- 0.1 was tested
        everywhere and qualified nowhere.  Without this the census could be
        misread as 'nobody tried it'."""
        import yaml

        for rel in op.WINDOW_FILES:
            doc = yaml.safe_load((op.REPO_ROOT / rel).read_text(encoding="utf-8"))
            for cell in doc["cells"]:
                ladder = cell.get("ladder") or doc["ladder"]
                assert op.SHIPPED_LAM in ladder, (rel, cell["scenario"])

    def test_the_census_reproduces_the_docstring_table(self):
        """Re-derived against the 8-controller table (D-477). The old literal
        `{0.2: 8, 0.4: 13, 0.8: 9, 1.6: 7, 3.2: 6, 6.4: 3}` over 24 cells is
        kept in this docstring rather than deleted, because the *shape* of the
        move is the reading: every rung grew, and two rungs below the old floor
        appeared — which is how 0.1 stopped being unreachable.
        """
        assert op.ladder_census() == {
            0.05: 8, 0.1: 8, 0.2: 42, 0.4: 55, 0.8: 35, 1.6: 21, 3.2: 14, 6.4: 16,
        }
        # 72 = 8 controllers x 9 scenes in the shipped table, + 8 variant cells.
        assert len(op.windows()) == 80


class TestShippedAndAdmissibleAreAntiCorrelated:
    """The inversion: the field Q-059 would have required marks the wrong set."""

    def test_exactly_one_claim_is_measured_entirely_at_the_shipped_lam(self):
        shipped_only = [c.claim for c in op.census() if c.all_shipped]
        assert shipped_only == [op.SHIPPED_ONLY_CLAIM]

    def test_that_same_claim_is_the_only_one_with_no_admissible_point(self):
        no_adm = [c.claim for c in op.census() if not c.any_admissible]
        assert no_adm == [op.SHIPPED_ONLY_CLAIM]

    def test_a_required_shipped_field_would_have_marked_the_sound_claims(self):
        """Stated as the counterfactual, because that is the decision Q-059 asked
        about: option (a) flags off-shipped claims, and every claim it flags here
        is measured inside its own window."""
        flagged = [c for c in op.census() if not c.all_shipped]
        cleared = [c for c in op.census() if c.all_shipped]
        assert len(flagged) == 4 and len(cleared) == 1
        assert all(c.any_admissible for c in flagged)
        assert not any(c.any_admissible for c in cleared)


def test_the_only_inadmissible_points_are_the_default_and_one_by_design():
    """Pins *which* points fail, so a future drift cannot keep the totals while
    moving the failure somewhere that would mean something different."""
    bad = [(claim, point)
           for claim, ops in op.CLAIM_OPERATING_POINTS.items()
           for point in ops if not op.is_admissible(point)]
    by_claim = {}
    for claim, point in bad:
        by_claim.setdefault(claim, []).append(point)
    assert set(by_claim) == {"exposure_band_hi", "ab_protocol_overstatement"}
    assert len(by_claim["exposure_band_hi"]) == 5
    assert all(p.is_shipped for p in by_claim["exposure_band_hi"])
    # The by-design one: single-`lam` protocol, risk arm at stock's rung.
    (designed,) = by_claim["ab_protocol_overstatement"]
    assert (designed.controller, designed.lam) == ("risk_mppi", 0.4)
    assert "BY DESIGN" in designed.role


def test_the_d039_shipped_arm_sits_outside_its_own_cells_window():
    """D-039's rescope of D-028, applied to D-039 (see module docstring).

    Its two arms are `lam = 1.6` and `lam = 0.1` on crossing/`risk_mppi`.  The
    first is inside that cell's window and the second is not, so "the shipped
    temperature" was an out-of-band vantage rather than a better one.
    """
    from eval.mppi_sandbox import denominator_scope as ds

    cell = ("cafe_obstacle_crossing_v0.yaml", "risk_mppi")
    assert op.windows()[cell] == (1.6, 3.2)
    assert op.is_admissible(op.OperatingPoint(*cell, 1.6))
    assert not op.is_admissible(op.OperatingPoint(*cell, ds_shipped := op.SHIPPED_LAM))
    # The module under discussion really does read at that temperature.
    assert ds_shipped == 0.1 and "lam = 0.1" in ds.__doc__


def test_report_names_both_columns():
    text = op.report()
    assert "shipped lam = 0.1" in text
    assert op.SHIPPED_ONLY_CLAIM in text
    for claim in op.CLAIM_OPERATING_POINTS:
        assert claim in text


def test_absent_cell_raises_rather_than_reading_false():
    with pytest.raises(LookupError):
        op.is_admissible(op.OperatingPoint("no_such_scene_v0.yaml", "risk_mppi", 0.4))

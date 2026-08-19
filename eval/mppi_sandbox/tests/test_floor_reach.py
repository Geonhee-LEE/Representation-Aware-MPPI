# SPDX-License-Identifier: BSD-3-Clause
"""The A-A floor joined to the sites that state the cross-track claim (D-373)."""

from __future__ import annotations

import pytest

from eval.mppi_sandbox import (
    aa_calibration,
    declaration_gap,
    excursion_seed_width,
    excursion_tracking,
    floor_reach,
    seed_debt,
)


def test_cli_clean() -> None:
    """The module's own drift check passes on the committed pins."""
    assert floor_reach.main() == 0


def test_tally_is_derived_not_typed() -> None:
    """:data:`SITE_TALLY` must equal what :func:`tally` computes."""
    assert floor_reach.tally() == floor_reach.SITE_TALLY == (6, 3, 1)


def test_every_site_value_matches_its_live_pin() -> None:
    """`audit()` reads the claim sites, so editing a pin must move a row."""
    rows = {r.site: r.value for r in floor_reach.audit()}
    assert rows["excursion_tracking.SPREAD_SEPARATES[0]"] == pytest.approx(
        excursion_tracking.SPREAD_SEPARATES[0]
    )
    assert rows["excursion_tracking.SPREAD_SEPARATES[1]"] == pytest.approx(
        excursion_tracking.SPREAD_SEPARATES[1]
    )
    assert rows["excursion_seed_width.ROBUST_SEPARATION[0]"] == pytest.approx(
        excursion_seed_width.ROBUST_SEPARATION[0]
    )
    assert rows["excursion_seed_width.INTERSECTION[cafe_convoy_v0]"] == pytest.approx(
        excursion_seed_width.INTERSECTION["cafe_convoy_v0"]
    )


def test_floors_come_from_aa_calibration() -> None:
    """No floor is re-derived here; every row quotes the calibration module."""
    for row in floor_reach.audit():
        site = next(s for s in floor_reach.SITES if s.name == row.site)
        assert row.p95_floor == pytest.approx(
            round(aa_calibration.p95_floor(site.column, site.scene), 4)
        )
        assert row.max_floor == pytest.approx(
            round(aa_calibration.max_floor(site.column, site.scene), 4)
        )


def test_each_endpoint_graded_on_its_own_scene() -> None:
    """D-371 finding #3: a calibration does not transfer across scenes."""
    for site in floor_reach.SITES:
        assert (site.column, site.scene) in aa_calibration.CALIBRATED


def test_finding_1_only_one_endpoint_clears_the_max_floor() -> None:
    above = [
        r
        for r in floor_reach.audit()
        if r.verdict == "ABOVE" and r.column == "cte_max"
    ]
    assert len(above) == 1
    assert above[0].site == floor_reach.ONLY_CLEARING_ENDPOINT[0]
    assert above[0].ratio == pytest.approx(
        floor_reach.ONLY_CLEARING_ENDPOINT[1], abs=1e-4
    )


def test_finding_1_the_clearing_endpoint_is_a_min_vs_max_minimum() -> None:
    """One endpoint clearing licenses nothing: the paired maximum is below."""
    rows = {r.site: r for r in floor_reach.audit()}
    lo = rows["excursion_tracking.SPREAD_SEPARATES[0]"]
    hi = rows["excursion_tracking.SPREAD_SEPARATES[1]"]
    assert lo.verdict == "ABOVE"
    assert hi.verdict == "BELOW"


def test_finding_1_the_two_readings_disagree_on_city_curved() -> None:
    """The p95/max split is real and is why both readings are reported."""
    rows = {r.site: r for r in floor_reach.audit()}
    row = rows["excursion_seed_width.ROBUST_SEPARATION[1]"]
    assert row.value > row.p95_floor  # clears the fairer reading
    assert row.value < row.max_floor  # fails the adversarial one
    endpoints, over_p95, over_max = floor_reach.SITE_TALLY
    assert over_p95 > over_max


def test_finding_2_intersection_survivor_is_under_its_floor() -> None:
    """D-370's `+0.0550` "barrable at seed width" does not clear the null."""
    value, mx, ratio = floor_reach.INTERSECTION_UNDER_FLOOR
    assert value == pytest.approx(excursion_seed_width.INTERSECTION["cafe_convoy_v0"])
    assert mx == pytest.approx(
        round(aa_calibration.max_floor("cte_max", "cafe_convoy_v0"), 4)
    )
    assert ratio == pytest.approx(value / mx, abs=1e-4)
    assert ratio < 1.0


def test_negative_intersection_has_no_ratio() -> None:
    """A negative width cannot be a ratio; it is BELOW by inspection."""
    row = next(
        r
        for r in floor_reach.audit()
        if r.site == "excursion_seed_width.INTERSECTION[city_curved_v0]"
    )
    assert row.value < 0
    assert row.ratio is None
    assert row.verdict == "BELOW"


def test_finding_3_every_claim_site_module_names_its_bound() -> None:
    """The structural fix: "unjoined" is a test failure, not a STATE bullet."""
    assert floor_reach.unjoined() == floor_reach.UNJOINED == ()
    carried = floor_reach.carries_bound()
    assert carried == {
        "excursion_tracking": True,
        "excursion_seed_width": True,
        "declaration_gap": True,
        "seed_debt": True,
    }


def test_verdict_is_undecidable_not_false() -> None:
    """Scope limit 3: the floor is symmetric — it never refutes a direction."""
    assert "undecidable" in floor_reach.VERDICT
    assert "false" not in floor_reach.VERDICT.lower()


def test_both_calibrated_columns_are_joined() -> None:
    """Scope limit 1 (as revised by D-374): the clearance sites joined too.

    D-373 left them out because clearance clears 5/5 on the *gap*; finding #4
    showed a declaration rests on the **window**, whose margin is different.
    """
    assert {s.column for s in floor_reach.SITES} == {"cte_max", "clearance"}
    # every column aa_calibration can grade now has claim sites joined to it
    assert {s.column for s in floor_reach.SITES} == {
        c for c, _ in aa_calibration.CALIBRATED
    }


# --- D-374: the clearance column joined, graded as bar-window widths ---


def test_clearance_tally_is_derived_not_typed() -> None:
    """Finding #4 — all five declarable windows still clear, both readings."""
    assert (
        floor_reach.tally("clearance") == floor_reach.CLEARANCE_TALLY == (5, 5, 5)
    )


def test_tally_is_scoped_to_one_column() -> None:
    """The two readings are not comparable, so no tally may span both."""
    cte = floor_reach.tally("cte_max")
    clr = floor_reach.tally("clearance")
    assert cte[0] + clr[0] == len(floor_reach.SITES)
    assert {s.column for s in floor_reach.SITES} == {"cte_max", "clearance"}


def test_width_reading_is_the_interval_width() -> None:
    """A `width` site grades `hi - lo`, not either endpoint."""
    rows = {r.site: r.value for r in floor_reach.audit()}
    lo, hi = declaration_gap.COMMON_WINDOW
    assert rows["declaration_gap.COMMON_WINDOW"] == pytest.approx(hi - lo, abs=5e-5)
    for scene, (wlo, whi) in seed_debt.WINDOWS.items():
        assert rows[f"seed_debt.WINDOWS[{scene}]"] == pytest.approx(
            whi - wlo, abs=5e-5
        )


def test_window_ratio_is_below_gap_ratio_on_every_scene() -> None:
    """Finding #4's whole content: the window is the narrower object, 5 of 5."""
    pairs = floor_reach.window_vs_gap()
    assert pairs == floor_reach.WINDOW_UNDER_GAP
    assert len(pairs) == 5
    assert all(window < gap for window, gap in pairs.values())


def test_both_ratios_use_the_same_floor() -> None:
    """Like-for-like: comparing a window to a p95 gap would fake the finding."""
    for scene, (window, gap) in floor_reach.window_vs_gap().items():
        value, mx = next(
            (r.value, r.max_floor)
            for r in floor_reach.audit()
            if r.column == "clearance" and r.scene == scene
        )
        real_gap, _, floor_max = aa_calibration.FLOOR_VERDICT[("clearance", scene)]
        assert window == pytest.approx(value / mx, abs=5e-5)
        assert gap == pytest.approx(real_gap / floor_max, abs=5e-5)
        assert floor_max == mx


def test_thinnest_window_is_derived() -> None:
    """:data:`THINNEST_WINDOW` must be the argmin, not a remembered scene."""
    pairs = floor_reach.window_vs_gap()
    scene = min(pairs, key=lambda s: pairs[s][0])
    assert floor_reach.THINNEST_WINDOW == (scene, pairs[scene][0])


def test_new_claim_sites_carry_the_bound() -> None:
    """The clearance sites must name this module too, or UNJOINED grows."""
    carried = floor_reach.carries_bound()
    assert carried["declaration_gap"] is True
    assert carried["seed_debt"] is True
    assert floor_reach.unjoined() == floor_reach.UNJOINED == ()

# SPDX-License-Identifier: BSD-3-Clause
"""The A-A floor joined to the sites that state the cross-track claim (D-373)."""

from __future__ import annotations

import pytest

from eval.mppi_sandbox import (
    aa_calibration,
    excursion_seed_width,
    excursion_tracking,
    floor_reach,
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
    above = [r for r in floor_reach.audit() if r.verdict == "ABOVE"]
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
    assert carried == {"excursion_tracking": True, "excursion_seed_width": True}


def test_verdict_is_undecidable_not_false() -> None:
    """Scope limit 3: the floor is symmetric — it never refutes a direction."""
    assert "undecidable" in floor_reach.VERDICT
    assert "false" not in floor_reach.VERDICT.lower()


def test_only_the_cte_max_column_is_joined() -> None:
    """Scope limit 1: clearance clears 5/5, so no clearance site is in doubt."""
    assert {s.column for s in floor_reach.SITES} == {"cte_max"}

"""Q-175 option (a): the two columns, re-read at one operating point.

Every number in :data:`tail_mean.ALIGNED_CELLS` is re-derived here from the
pinned ensemble through `aa_calibration`'s own floor machinery, so the table
cannot drift from the rows it summarises. That is the specific failure Q-175
named — `tail_mean.drift()` compared the two columns' *arm names* and never
their values, so a pin taken at a different operating point read as agreement.
"""

import pytest

from eval.mppi_sandbox import aa_calibration as aa
from eval.mppi_sandbox import excursion_seed_width, tail_mean

ALIGNED_SCENES = ("cafe_convoy_v0", "cafe_head_on_v0")


def _headroom(ens, strict=False):
    """`real_gap / floor` for a free-standing ensemble, by aa_calibration's rules."""
    if strict:
        floor = round(max(round(aa.null_gaps(r)[-1], 4) for r in ens.values()), 4)
    else:
        floor = round(max(round(aa._quantile(aa.null_gaps(r), 0.95), 4)
                          for r in ens.values()), 4)
    means = [sum(r) / len(r) for r in ens.values()]
    return round(round(max(means) - min(means), 4) / floor, 2)


@pytest.mark.parametrize("scene", ALIGNED_SCENES)
def test_pinned_column_is_well_formed(scene):
    ens = tail_mean.CTE_MAX_AT_OPERATING_POINT[scene]
    assert set(ens) == set(tail_mean.TVAR_ENSEMBLE), "arm population must match the TVaR column"
    assert all(len(r) == tail_mean.SEEDS for r in ens.values())


@pytest.mark.parametrize("scene", ALIGNED_SCENES)
def test_aligned_cells_rederive_from_the_pin(scene):
    """The headroom table is a reading of the ensemble, not a second typing."""
    ens = tail_mean.CTE_MAX_AT_OPERATING_POINT[scene]
    assert _headroom(ens) == tail_mean.ALIGNED_CELLS[scene][1]


@pytest.mark.parametrize("scene", ALIGNED_SCENES)
def test_tvar_half_of_aligned_cells_matches_the_pinned_tvar_column(scene):
    pin = (tail_mean.TVAR_ENSEMBLE if scene == tail_mean.SCENE
           else tail_mean.TVAR_ENSEMBLE_THIRD)
    assert _headroom(pin) == tail_mean.ALIGNED_CELLS[scene][0]


@pytest.mark.parametrize("scene", ALIGNED_SCENES)
def test_the_old_cte_max_pin_is_a_different_experiment(scene):
    """Q-175's finding, as a standing check: 0/8 arms agree, not 8/8.

    If a future harvest ever makes these agree, the mismatch this module was
    built to repair has gone away and the module should be retired — so the
    assertion is on the *disagreement*, which is the fact that was measured.
    """
    old = excursion_seed_width.SEED_ENSEMBLE[scene]
    new = tail_mean.CTE_MAX_AT_OPERATING_POINT[scene]
    agree = sum(1 for arm, row in old.items() if tuple(row) == new[arm])
    assert agree == 0


def test_dominance_does_not_survive_the_realignment():
    """The claim D-388 put in place of the contrast, asked of one experiment."""
    assert tail_mean.dominance_holds() is True          # two experiments
    assert tail_mean.dominance_at_operating_point() is False  # one experiment
    tv, base = tail_mean.ALIGNED_CELLS["cafe_head_on_v0"]
    assert base > tv, "head_on is the cell that inverts"


def test_convoy_cte_max_clears_its_floor_once_aligned():
    """CONVOY_SPLIT's `0.96x` was an operating-point artifact, not a null result."""
    ens = tail_mean.CTE_MAX_AT_OPERATING_POINT["cafe_convoy_v0"]
    assert _headroom(ens) > 1.0
    assert _headroom(ens, strict=True) > 1.0, "clears the adversarial floor too"
    assert aa.headroom("cte_max", "cafe_convoy_v0") < 1.0, "the old, mismatched reading"


def test_no_live_call_site_still_quotes_the_retired_reading():
    """D-391: the realignment's *citations*, not its measurement.

    D-390 measured the aligned table and left `COMPARABLE_CELLS` in place for
    the shipped census, `COLUMN_CLAIM_FORM` and `drift()` to keep reading — so
    the branch's own report printed `DOMINANCE HOLDS: True` for a claim the
    same module already knew was refuted. The retired table stays (retired by
    pin, not deletion), but nothing that *renders a verdict* may read it.
    """
    text = tail_mean.format_census()
    assert "DOMINANCE HOLDS: True" not in text
    assert f"DOMINANCE (aligned): {tail_mean.dominance_at_operating_point()}" in text
    # The retraction travels with the numbers.
    assert "RETIRED BY THE REALIGNMENT" in text
    for name, _was, _now in tail_mean.RETIRED_BY_ALIGNMENT:
        assert name in text
    # Both aligned cells are rendered, and each carries its retired counterpart.
    for scene, (_tv, base) in tail_mean.ALIGNED_CELLS.items():
        assert f"{base:.2f}x" in text
        assert f"(retired: cte_max {tail_mean.COMPARABLE_CELLS[scene][1]:.2f}x)" in text


def test_the_mixed_operating_point_marker_names_the_right_column():
    """`COLUMN_VERDICT['cte_max']` counts rows from two harvests; clearance does not."""
    assert aa.MIXED_OPERATING_POINT_COLUMNS == frozenset({"cte_max"})
    assert "clearance" not in aa.MIXED_OPERATING_POINT_COLUMNS
    # The marker must name a column the verdict actually tallies.
    assert aa.MIXED_OPERATING_POINT_COLUMNS <= set(aa.COLUMN_VERDICT)
    # And the reason it is mixed: two of the three rows have an aligned re-take,
    # the third does not. That asymmetry is what makes the tally uncountable.
    aligned = set(tail_mean.ALIGNED_CELLS)
    rows = {s for (col, s) in aa.FLOOR_VERDICT if col == "cte_max"}
    assert aligned < rows, "aligned re-takes must be a strict subset of the tally"
    assert rows - aligned == {"city_curved_v0"}


def test_alignment_moved_both_cells_upward():
    for old, new in tail_mean.alignment_gain().values():
        assert new > old


def test_retired_claims_name_live_attributes():
    """A retirement that names nothing is a retirement nobody can follow."""
    import importlib

    assert tail_mean.RETIRED_BY_ALIGNMENT
    for dotted, _old, _new in tail_mean.RETIRED_BY_ALIGNMENT:
        mod, attr = dotted.rsplit(".", 1)
        assert hasattr(importlib.import_module(f"eval.mppi_sandbox.{mod}"), attr)

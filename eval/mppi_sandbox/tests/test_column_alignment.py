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

#: The scenes the aligned *table* covers — the ones excited enough to grade.
#: `city_curved_v0` is pinned in `CTE_MAX_AT_OPERATING_POINT` but stays out of
#: here: it is degenerate at both operating points (D-392), so the table would
#: gain a row that reports a number and measures nothing.
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


@pytest.mark.parametrize("scene", sorted(tail_mean.CTE_MAX_AT_OPERATING_POINT))
def test_pinned_column_is_well_formed(scene):
    """Every pinned re-take, including the ungradeable one — shape is not grading."""
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


def test_the_mixed_operating_point_marker_is_retracted():
    """D-392: the marker named a defect the tally does not have.

    `column_verdict` reads every `cte_max` row out of one harvest, so the
    tally was never assembled from two operating points — the *prose* was.
    Asserting the empty set rather than deleting the name keeps the retraction
    reachable from anything still quoting it.
    """
    assert aa.MIXED_OPERATING_POINT_COLUMNS == frozenset()
    # The positive evidence: every tallied row comes from the same pin, and
    # every one of them disagrees with the aligned construction.
    rows = {s for (col, s) in aa.FLOOR_VERDICT if col == "cte_max"}
    for scene in rows:
        assert scene in excursion_seed_width.SEED_ENSEMBLE
        old = excursion_seed_width.SEED_ENSEMBLE[scene]
        new = tail_mean.CTE_MAX_AT_OPERATING_POINT[scene]
        agree = sum(1 for arm, row in old.items() if tuple(row) == new[arm])
        assert agree < tail_mean.SEEDS, f"{scene} would be the aligned harvest"
    # Every row now has an aligned re-take — the asymmetry the marker rested on
    # is gone, and it is not what made the tally uncountable.
    assert rows == set(tail_mean.CTE_MAX_AT_OPERATING_POINT)


def test_the_third_row_is_degenerate_at_both_operating_points():
    """What the 64-rollout re-take actually bought (D-392).

    The premise was that harvesting `city_curved_v0` at the operating point
    would make `COLUMN_VERDICT['cte_max']` a three-row tally over one
    experiment. It does not: the cell separates two arms of eight at *either*
    point, so it grades nothing either way.
    """
    scene = tail_mean.SECOND_SCENE
    new = tail_mean.CTE_MAX_AT_OPERATING_POINT[scene]
    old = excursion_seed_width.SEED_ENSEMBLE[scene]
    distinct, need, aligned_head, old_head = tail_mean.ALIGNED_SECOND

    assert tail_mean.distinct_arms(new) == distinct
    assert tail_mean.distinct_arms(old) == distinct, "degenerate at the old point too"
    assert need == tail_mean.MIN_DISTINCT_ARMS
    assert not tail_mean.aligned_second_is_gradeable()
    assert scene not in tail_mean.ALIGNED_CELLS, "an ungradeable cell may not join the table"

    # Both headrooms are well-formed numbers over a population of two — pinned
    # so the prose quoting them carries that fact, not deleted.
    assert _headroom(new) == aligned_head
    assert aa.headroom("cte_max", scene) == old_head
    assert "UNGRADEABLE" in tail_mean.aligned_second_verdict()


def test_the_zero_of_eight_signature_degrades_with_the_cell():
    """`0/8` is what a mismatch looks like when there are eight rows to disagree.

    On both excited scenes the aligned re-take agrees with the old pin on no
    arm. Here it agrees on one — and that one is the only arm the scene
    separates, so the seven collapsed arms carry the disagreement. The
    signature is therefore evidence about the construction only in proportion
    to how excited the cell is.
    """
    scene = tail_mean.SECOND_SCENE
    old = excursion_seed_width.SEED_ENSEMBLE[scene]
    new = tail_mean.CTE_MAX_AT_OPERATING_POINT[scene]
    agreeing = tuple(a for a, row in old.items() if tuple(row) == new[a])
    n, arm = tail_mean.ALIGNED_SECOND_AGREEMENT
    assert agreeing == (arm,) and len(agreeing) == n
    # The agreeing arm is the responsive one: it is the row the degenerate
    # majority does not share.
    majority = max(set(new.values()), key=lambda r: list(new.values()).count(r))
    assert new[arm] != majority


def test_the_tally_counts_a_row_no_observable_grades():
    """D-392 finding: `column_verdict` has no degeneracy notion; `tail_mean` does."""
    assert aa.degenerate_tally_rows() == aa.DEGENERATE_TALLY_ROWS
    assert aa.DEGENERATE_TALLY_ROWS == (("cte_max", "city_curved_v0", 2),)
    # The other module already refuses to grade this scene.
    assert "UNTESTABLE" in tail_mean.second_verdict()
    assert tail_mean.SECOND_SCENE in tail_mean.second_verdict()
    # Every clearance row separates its arms — the split is not symmetric.
    assert not [r for r in aa.degenerate_tally_rows() if r[0] == "clearance"]
    # Dropping the ungradeable row moves the denominator, not the successes.
    assert aa.column_verdict("cte_max") == (3, 1, 1)
    assert aa.gradeable_column_verdict("cte_max") == (2, 1, 1)
    assert aa.gradeable_column_verdict("clearance") == aa.column_verdict("clearance")


def test_alignment_moved_both_gradeable_cells_upward():
    """Both cells in the aligned table read higher. The third reads lower.

    Not a counter-example — `city_curved_v0` grades nothing at either point, so
    its `0.35x → 0.12x` is two statistics over a population of two. Asserted
    here so the direction claim is scoped to where a direction exists, rather
    than being quietly generalised the way `dominance_holds` was.
    """
    for old, new in tail_mean.alignment_gain().values():
        assert new > old
    _distinct, _need, aligned_head, old_head = tail_mean.ALIGNED_SECOND
    assert aligned_head < old_head
    assert tail_mean.SECOND_SCENE not in tail_mean.alignment_gain()


def test_retired_claims_name_live_attributes():
    """A retirement that names nothing is a retirement nobody can follow."""
    import importlib

    assert tail_mean.RETIRED_BY_ALIGNMENT
    for dotted, _old, _new in tail_mean.RETIRED_BY_ALIGNMENT:
        mod, attr = dotted.rsplit(".", 1)
        assert hasattr(importlib.import_module(f"eval.mppi_sandbox.{mod}"), attr)

# SPDX-License-Identifier: BSD-3-Clause
"""Does routing the λ lookup **through the weight** change what a caller can be
handed?

`lam_window_key` has graded tables since D-134 and every call site in the repo
is a test — the guard was available and nothing load-bearing read it. D-141 and
D-142 then produced the material that makes reading it possible: two generated
tables that record their own `calibration_weight:`. This file asserts the join.

The claim under test is not "the wrapper works". It is that choosing the file
*from* the caller's weight removes a specific past error from the repo's reach.
D-133 walked `cafe_obstacle_crossing_v0`'s risk arm at λ = 3.2 because the
table said `[1.6, 3.2]`, and that table was `w = 10` while the walk was not. The
first two tests below are that cell, resolved at both weights.
"""

from __future__ import annotations

import pytest

from eval.mppi_sandbox import lam_window_index as lwi
from eval.mppi_sandbox import lam_window_key as lwk

CROSSING = "cafe_obstacle_crossing_v0.yaml"
HEADON = "cafe_head_on_v0.yaml"

INDEX = lwi.build_index()


# --------------------------------------------------------------------------
# The cell that cost something (D-133 / D-142)
# --------------------------------------------------------------------------

def test_crossing_risk_has_its_recorded_window_at_the_weight_it_was_measured_at():
    """At `w = 10` the recorded `[1.6, 3.2]` is exactly what resolves — the
    index must not refuse a cell that is genuinely on key, or it is
    `guard_vacuity`'s complaint with the sign flipped."""
    res = lwi.resolve(CROSSING, "risk_mppi", 10.0, INDEX)
    assert res.verdict == lwk.ON_KEY
    assert res.usable == (1.6, 3.2)


def test_crossing_risk_resolves_to_no_window_at_75_not_to_the_w10_window():
    """The payoff. D-142 measured this arm admissible at **no** rung at
    `w = 75`; a caller at that weight must get `EMPTY_WINDOW`, not the `w = 10`
    row. Set equality against `()` and an explicit `is None` on `usable`,
    because the failure mode being excluded is receiving `(1.6, 3.2)` here."""
    res = lwi.resolve(CROSSING, "risk_mppi", 75.0, INDEX)
    assert res.verdict == lwk.EMPTY_WINDOW
    assert res.usable is None
    assert res.admissible == ()
    # the literal that a weight-blind read would have produced
    assert res.admissible != (1.6, 3.2)


def test_the_two_weights_disagree_so_the_routing_is_not_decoration():
    """If both weights returned the same window for every cell, the index
    would be a no-op dressed as a guard. At least one cell must differ — this
    is the non-vacuity check for the *routing*, distinct from the per-verdict
    one below."""
    differing = [
        (scene, arm)
        for (scene, arm) in lwi.coverage(INDEX)
        if lwi.resolve(scene, arm, 10.0, INDEX).admissible
        != lwi.resolve(scene, arm, 75.0, INDEX).admissible
    ]
    assert differing, "no cell differs between w=10 and w=75; index is inert"


# --------------------------------------------------------------------------
# The refusal changes shape rather than softening
# --------------------------------------------------------------------------

def test_an_uncalibrated_weight_refuses_by_name_and_says_what_exists():
    """`w = 100` is D-132's middle rung and has no table. The refusal must
    name the weights that do, or it is a check the caller cannot act on
    (D-044)."""
    res = lwi.resolve(HEADON, "stock_mppi", 100.0, INDEX)
    assert res.verdict == lwi.NO_TABLE_AT_WEIGHT
    assert res.usable is None
    assert res.table is None
    assert res.available == (10.0, 75.0)
    assert "10" in str(res) and "75" in str(res)


def test_off_key_and_unkeyed_are_unreachable_through_the_index():
    """The module docstring's structural claim, checked. A fallback to the
    nearest weight, or indexing the unkeyed table under an assumed 10.0, would
    let either verdict back in — and both are ways of handing a caller a window
    measured somewhere else."""
    reachable = lwi.reachable_verdicts(INDEX)
    assert lwk.OFF_KEY not in reachable
    assert lwk.UNKEYED not in reachable
    # ...and the guard is non-vacuous in both directions: a real window and a
    # real refusal are both reachable.
    assert lwk.ON_KEY in reachable
    assert lwi.NO_TABLE_AT_WEIGHT in reachable


def test_a_missing_cell_is_still_distinct_from_an_empty_window():
    """`NO_CELL` (never measured) and `EMPTY_WINDOW` (measured, inadmissible
    everywhere) survive the wrapping — Q-034's error is reading the second as
    the first."""
    assert lwi.resolve("nonexistent_scene.yaml", "stock_mppi", 75.0,
                       INDEX).verdict == lwk.NO_CELL
    assert lwi.resolve("cafe_cut_in_v0.yaml", "stock_mppi", 75.0,
                       INDEX).verdict == lwk.EMPTY_WINDOW


# --------------------------------------------------------------------------
# The index itself
# --------------------------------------------------------------------------

def test_the_shipped_table_is_excluded_and_named_rather_than_dropped():
    """`lam_windows.yaml` carries no weight so it cannot be resolved through;
    its absence from the index is a finding about the file ~24 cells of project
    history were read from, so it must be reported."""
    assert INDEX.unkeyed == ("eval/scenarios/lam_windows.yaml",)
    assert "eval/scenarios/lam_windows.yaml" not in INDEX.by_weight.values()
    assert "lam_windows.yaml" in str(INDEX)


def test_index_reads_each_weight_off_the_file_rather_than_off_its_name():
    """The mapping is derived from `calibration_weight:`, not parsed out of
    `…_w75.yaml`. A filename-derived index would agree today and diverge the
    first time a file is renamed or regenerated at another weight (D-047)."""
    assert INDEX.by_weight[10.0].endswith("lam_windows_w10.yaml")
    assert INDEX.by_weight[75.0].endswith("lam_windows_w75.yaml")
    for weight, path in INDEX.by_weight.items():
        _, recorded = lwk._rows(path)
        assert recorded == weight


def test_two_tables_at_one_weight_is_refused_not_tie_broken(tmp_path):
    """A duplicate weight means two measurements claim one operating point.
    Picking either would make the answer depend on tuple order."""
    import shutil
    a = tmp_path / "a.yaml"
    b = tmp_path / "b.yaml"
    shutil.copy("eval/scenarios/variants/lam_windows_w75.yaml", a)
    shutil.copy("eval/scenarios/variants/lam_windows_w75.yaml", b)
    with pytest.raises(lwi.WeightCollision, match="75"):
        lwi.build_index([str(a), str(b)])


def test_an_all_unkeyed_index_refuses_everything_and_offers_no_weights():
    """The degenerate case the repo was in before D-138's writer: nothing is
    resolvable and the refusal has nothing to suggest. It must not crash, and
    it must not fall back to `CALIBRATION_WEIGHT`."""
    index = lwi.build_index(["eval/scenarios/lam_windows.yaml"])
    assert index.weights == ()
    res = lwi.resolve(HEADON, "stock_mppi", 10.0, index)
    assert res.verdict == lwi.NO_TABLE_AT_WEIGHT
    assert res.available == ()


# --------------------------------------------------------------------------
# Coverage — the patchiness, stated as data
# --------------------------------------------------------------------------

def test_coverage_reports_the_asymmetric_cell_rather_than_smoothing_it():
    """`crossing`/risk is usable at `w = 10` only; its stock arm at both. A
    coverage map that listed both weights for both arms would be averaging over
    exactly the finding D-142 shipped."""
    cov = lwi.coverage(INDEX)
    assert cov[(CROSSING, "risk_mppi")] == (10.0,)
    assert cov[(CROSSING, "stock_mppi")] == (10.0, 75.0)


def test_coverage_lists_never_open_cells_with_an_empty_tuple_not_by_omission():
    """`cut_in` has no window at either weight (Q-035). It must appear with
    `()` — omitting it would make "not covered here" and "not a cell" the same
    reading, which is the denominator pollution D-142's `NEVER_OPEN` grade was
    added to prevent one layer up."""
    cov = lwi.coverage(INDEX)
    assert cov[("cafe_cut_in_v0.yaml", "stock_mppi")] == ()
    assert cov[("cafe_cut_in_v0.yaml", "risk_mppi")] == ()


def test_coverage_spans_both_tables_and_every_cell_in_them():
    """16 arm-cells, the same 16 in both tables — so the join is total and a
    cell missing from one file would show up as a shorter map rather than
    silently as a narrower window."""
    cov = lwi.coverage(INDEX)
    assert len(cov) == 16
    assert all(set(w) <= {10.0, 75.0} for w in cov.values())
    # D-132's operating point survives at both weights on the scene it was
    # measured on — the retraction test, read off the index this time.
    assert cov[(HEADON, "stock_mppi")] == (10.0, 75.0)
    assert 0.8 in lwi.resolve(HEADON, "stock_mppi", 75.0, INDEX).usable

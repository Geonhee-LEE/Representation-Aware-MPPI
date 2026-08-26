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
    """`w = 250` is the published band's **detached** top rung — the one-run
    rung that makes D-133's walk grade `BAND_SPLIT` — and it has no table. The
    refusal must name the weights that do, or it is a check the caller cannot
    act on (D-044).

    This test read `w = 100` until D-145 measured it, `w = 150` until D-149
    did, and `w = 250` until this cycle did. The surviving assertion is that
    *whatever* is still unmeasured refuses by name — but that is a property of
    the complement of the index's domain, so it is now **derived** from the
    index (`uncalibrated_probe`) rather than re-named after each purchase.
    Three hand-migrations were three chances to leave the check pinned to a
    weight that had since been bought, which is how a refusal test outlives
    the gap it was watching."""
    res = lwi.resolve(HEADON, "stock_mppi", INDEX.uncalibrated_probe, INDEX)
    assert res.verdict == lwi.NO_TABLE_AT_WEIGHT
    assert res.usable is None
    assert res.table is None
    assert res.available == INDEX.weights == (10.0, 75.0, 100.0, 150.0, 250.0)
    assert all(w in str(res) for w in ("10", "75", "100", "150", "250"))


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

def test_the_unkeyed_bucket_is_empty_because_every_table_is_keyed(tmp_path):
    """This test used to assert the opposite, and the inversion is D-477.

    `lam_windows.yaml` carried no `calibration_weight:` for the whole of the
    project's history, so it was the index's sole `unkeyed` member and its
    exclusion was the finding this test reported. D-470 regenerated it over all
    8 controllers (33.1 min) and D-477 installed the result, so it is now keyed
    at `w = 10` and resolvable — `unkeyed` is empty.

    **Empty is exactly the state D-317 says reads clean from outside**: a
    bucket nobody populates and a bucket whose reporting branch is broken are
    indistinguishable by inspection. So the emptiness is asserted *and* the
    branch is exercised against a synthetic file in the same test. Deleting the
    second half would leave `unkeyed` unverified for the first time since it
    was written.
    """
    assert INDEX.unkeyed == (), (
        f"a shipped table lost its calibration_weight: {INDEX.unkeyed}")
    assert "eval/scenarios/lam_windows.yaml" in INDEX.by_weight.values()

    # Non-vacuity: the branch that fills the bucket still works.
    stray = tmp_path / "no_weight.yaml"
    stray.write_text("ladder: [0.1]\nseeds: 8\nband_width: 10.0\ncells: []\n")
    probed = lwi.build_index((*lwi.TABLES, str(stray)))
    assert probed.unkeyed == (str(stray),)
    assert "no_weight.yaml" in str(probed)


def test_index_reads_each_weight_off_the_file_rather_than_off_its_name():
    """The mapping is derived from `calibration_weight:`, not parsed out of
    `…_w75.yaml`. A filename-derived index would agree today and diverge the
    first time a file is renamed or regenerated at another weight (D-047).

    `w = 10` routes to the *parent* `lam_windows.yaml` rather than
    `variants/lam_windows_w10.yaml` as of D-477: the variant was retired from
    :data:`TABLES` because the parent measured a strict superset of it at the
    same weight (24/24 cells identical, D-472). This assertion is the one that
    would have caught the retirement being done by filename rather than by
    header.
    """
    assert INDEX.by_weight[10.0].endswith("scenarios/lam_windows.yaml")
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


def test_an_all_unkeyed_index_refuses_everything_and_offers_no_weights(tmp_path):
    """The degenerate case the repo was in before D-138's writer: nothing is
    resolvable and the refusal has nothing to suggest. It must not crash, and
    it must not fall back to `CALIBRATION_WEIGHT`.

    D-477 note: this used to build the degenerate index out of the *real*
    `lam_windows.yaml`, which was unkeyed. Installing the D-470 regeneration
    keyed that file, so the case now needs a synthetic table — the scenario
    being tested (an index over nothing but unkeyed tables) is one the repo can
    no longer produce from its own contents, which is why it is worth keeping.
    """
    stray = tmp_path / "lam_windows.yaml"
    stray.write_text("ladder: [0.1]\nseeds: 8\nband_width: 10.0\ncells: []\n")
    index = lwi.build_index([str(stray)])
    assert index.unkeyed == (str(stray),)
    assert index.weights == ()
    res = lwi.resolve(HEADON, "stock_mppi", 10.0, index)
    assert res.verdict == lwi.NO_TABLE_AT_WEIGHT
    assert res.available == ()


# --------------------------------------------------------------------------
# Coverage — the patchiness, stated as data
# --------------------------------------------------------------------------

def test_coverage_reports_the_asymmetric_cell_rather_than_smoothing_it():
    """The two crossing arms are usable at **different weight sets**, and a
    coverage map that listed one tuple for the scene would be averaging over
    exactly the finding D-142 shipped.

    D-163 measured the two top weights and made the asymmetry *stronger* rather
    than resolving it: before, risk's `(10,)` was a subset of stock's
    `(10, 75)`, so "the arms disagree" could be read as "one arm is measured
    less". Now neither tuple contains the other — each arm is usable at a
    weight the other is not — so no ordering of the arms explains the shape and
    the per-arm map is the only honest statement of it.
    """
    cov = lwi.coverage(INDEX)
    assert cov[(CROSSING, "risk_mppi")] == (10.0, 150.0, 250.0)
    assert cov[(CROSSING, "stock_mppi")] == (10.0, 75.0, 250.0)

    risk, stock = set(cov[(CROSSING, "risk_mppi")]), set(cov[(CROSSING, "stock_mppi")])
    assert not risk <= stock and not stock <= risk
    assert risk & stock == {10.0, 250.0}   # and 250 is why the scene is walkable


def test_coverage_lists_never_open_cells_with_an_empty_tuple_not_by_omission():
    """`cut_in` has no window at either weight (Q-035). It must appear with
    `()` — omitting it would make "not covered here" and "not a cell" the same
    reading, which is the denominator pollution D-142's `NEVER_OPEN` grade was
    added to prevent one layer up."""
    cov = lwi.coverage(INDEX)
    assert cov[("cafe_cut_in_v0.yaml", "stock_mppi")] == ()
    assert cov[("cafe_cut_in_v0.yaml", "risk_mppi")] == ()


def test_coverage_spans_every_table_and_every_cell_in_them():
    """**72** arm-cells, and they are **not** uniformly covered — the join is
    total over the union, so a cell missing from one file shows up as a
    narrower weight tuple rather than silently as a narrower window.

    The history this number walked is the point. Until D-146 it was 16 cells
    present at all three weights. That cycle bought a third controller column
    (`gap_gated_mppi`) at `w = 10` only, taking it to 24. D-477 installs
    D-470's regeneration — all 8 registered controllers × 9 scenes — and takes
    it to 72.

    **The two axes moved in opposite directions, and that is what this test now
    records.** The *cell* axis went from ragged to rectangular: every one of the
    8 controllers holds exactly 9 scenes, so there is no longer a "which arms
    exist" question to ask. The *weight* axis got proportionally sparser, not
    denser — the regeneration was walked at `w = 10` alone, so 68 of the 72
    cells are single-weight and the 4 that reach past `w = 100` are the same 4
    D-149/D-163 bought one at a time. Reporting one number for the matrix would
    hide exactly that trade, which is the whole question `resolve` exists to
    answer.
    """
    cov = lwi.coverage(INDEX)
    assert len(cov) == 72
    assert all(set(w) <= {10.0, 75.0, 100.0, 150.0, 250.0} for w in cov.values())

    # Rectangular on the cell axis: 8 controllers, 9 scenes each, no gaps.
    controllers = {k[1] for k in cov}
    scenes = {k[0] for k in cov}
    assert len(controllers) == 8 and len(scenes) == 9
    assert all(sum(1 for k in cov if k[1] == c) == 9 for c in controllers), (
        "a controller column is short — the parent table is no longer the full "
        "cross product and `coverage` is joining over a ragged union")

    # Sparse on the weight axis: only the pre-D-477 arms reach past w = 100.
    beyond_100 = {k for k, w in cov.items() if set(w) - {10.0, 75.0, 100.0}}
    assert len(beyond_100) == 4, (
        f"expected the 4 cells D-149/D-163 bought, got {sorted(beyond_100)}")

    # D-146's column is still single-weight, and it is still the published one.
    gap = {k: w for k, w in cov.items() if k[1] == "gap_gated_mppi"}
    assert len(gap) == 9
    assert {w for w in gap.values()} == {(10.0,), ()}
    assert cov[(HEADON, "gap_gated_mppi")] == (10.0,)
    # D-163 widened both top weights to a **second** scene, and the two did not
    # widen alike — which is the reason `coverage` is a map and not a count.
    # `w = 150` gains crossing's risk arm only: its stock arm has a cell there
    # and an *empty* window, and coverage lists the weights a caller can be
    # handed a λ at, not the weights a row exists at. `w = 250` gains both.
    at_150 = {k for k, w in cov.items() if 150.0 in w}
    assert at_150 == {(HEADON, "stock_mppi"), (HEADON, "risk_mppi"),
                      (CROSSING, "risk_mppi")}
    assert {k for k, w in cov.items() if 250.0 in w} == at_150 | {
        (CROSSING, "stock_mppi")}
    # The asymmetry is the finding, so it is asserted as a difference rather
    # than left to be read off two set literals.
    assert (CROSSING, "stock_mppi") not in at_150
    # D-132's operating point survives at **all five** weights on the scene it
    # was measured on — the retraction test, read off the index this time.
    # `w = 100` is the one the published claim was actually taken at (D-145);
    # `w = 250` is the published span's top scorable rung, and the last one it
    # had left uncalibrated.
    assert cov[(HEADON, "stock_mppi")] == (10.0, 75.0, 100.0, 150.0, 250.0)
    assert 0.8 in lwi.resolve(HEADON, "stock_mppi", 75.0, INDEX).usable
    assert 0.8 in lwi.resolve(HEADON, "stock_mppi", 100.0, INDEX).usable
    assert 0.8 in lwi.resolve(HEADON, "stock_mppi", 150.0, INDEX).usable
    assert 0.8 in lwi.resolve(HEADON, "stock_mppi", 250.0, INDEX).usable

# SPDX-License-Identifier: BSD-3-Clause
"""`calibrate_lam.merge_tables` — adding a column without re-walking a matrix.

Until D-146 a calibration table could only be produced whole. That made adding
one controller column a choice between re-walking the 16 cells D-141 measured
to reproduce *exactly* (pure cost, ~1000 runs) and hand-editing a file whose
own header says not to. The merge is the third option, and it is only worth
having if it is provably conservative — hence the identity test below, which
is the real load-bearing one: everything the merge does not touch must come
back byte-for-byte, or a column addition silently restates 16 measurements.

The refusals are tested from the same direction as the rest of the guard
family: a merge that quietly resolves a disagreement produces a table making a
claim neither input measured, which is worse than no table.
"""

from __future__ import annotations

import pytest

from eval.mppi_sandbox import calibrate_lam as cl

W10 = "eval/scenarios/variants/lam_windows_w10.yaml"
W75 = "eval/scenarios/variants/lam_windows_w75.yaml"


def _write(tmp_path, name, text):
    p = tmp_path / name
    p.write_text(text)
    return str(p)


def _empty_like(path, tmp_path, name="empty.yaml"):
    """A table with the same header as `path` and no cells at all."""
    return _write(tmp_path, name, cl._render(cl.load_header(path), []))


# --------------------------------------------------------------------------
# The conservation property
# --------------------------------------------------------------------------

def test_merging_an_empty_table_reproduces_the_base_byte_for_byte(tmp_path):
    """The identity element. If this drifts, every merged table carries cells
    that were re-rendered by a different code path than the one that measured
    them, and the `min_spread`/`admissible` values a caller reads are this
    process's opinion rather than the run's record."""
    merged = cl.merge_tables(W10, _empty_like(W10, tmp_path))
    assert merged == open(W10).read()


def test_the_merged_table_holds_exactly_the_union_of_both_cell_sets(tmp_path):
    base = cl.load_windows(W10)
    extra_text = cl._render(
        cl.load_header(W10),
        [{"scenario": "cafe_head_on_v0.yaml", "controller": "made_up_mppi",
          "admissible": (0.2, 0.4), "ladder": cl.load_header(W10)["ladder"],
          "min_spread": 1.02, "completes_anywhere": True,
          "calibratable": True}])
    out = _write(tmp_path, "merged.yaml",
                 cl.merge_tables(W10, _write(tmp_path, "x.yaml", extra_text)))
    got = cl.load_windows(out)
    assert set(got) == set(base) | {("cafe_head_on_v0.yaml", "made_up_mppi")}
    assert got[("cafe_head_on_v0.yaml", "made_up_mppi")]["admissible"] == (0.2, 0.4)


def test_the_header_comes_from_the_base_not_from_this_process(tmp_path):
    """A merge re-stamping `seeds`/`band_width` from its own environment is
    D-107's false provenance one level up from the per-cell weight `to_yaml`
    already refuses."""
    merged = cl.merge_tables(W10, _empty_like(W10, tmp_path))
    out = _write(tmp_path, "m.yaml", merged)
    assert cl.load_header(out) == cl.load_header(W10)


# --------------------------------------------------------------------------
# The refusals
# --------------------------------------------------------------------------

def test_tables_walked_at_different_weights_are_refused():
    """The file-level form of `to_yaml`'s per-cell rule. D-142 measured 6 of
    14 arm-cells moving between w=10 and w=75, so this join would publish
    windows under a weight they were never measured at."""
    with pytest.raises(cl.MergeRefused) as exc:
        cl.merge_tables(W10, W75)
    assert exc.value.verdict == cl.WEIGHT_MISMATCH


def test_a_differing_ladder_is_refused_even_at_the_same_weight(tmp_path):
    header = dict(cl.load_header(W10))
    header["ladder"] = header["ladder"][:-1]
    with pytest.raises(cl.MergeRefused) as exc:
        cl.merge_tables(W10, _write(tmp_path, "short.yaml",
                                    cl._render(header, [])))
    assert exc.value.verdict == cl.PROTOCOL_MISMATCH


def test_a_differing_seed_count_is_refused(tmp_path):
    """`admissible` is a conjunction over seeds, so an 8-seed cell and a
    16-seed cell answer different questions — the caveat D-145 had to price
    by hand. Under one header a caller cannot see which it is reading."""
    header = dict(cl.load_header(W10))
    header["seeds"] = 16
    with pytest.raises(cl.MergeRefused) as exc:
        cl.merge_tables(W10, _write(tmp_path, "s16.yaml",
                                    cl._render(header, [])))
    assert exc.value.verdict == cl.PROTOCOL_MISMATCH


def test_a_cell_present_in_both_tables_is_refused_not_resolved(tmp_path):
    """Re-measuring a cell is a new table, not a merge. Picking either side
    silently would turn a measurement into an edit with no record of which
    run the surviving number came from."""
    with pytest.raises(cl.MergeRefused) as exc:
        cl.merge_tables(W10, W10)
    assert exc.value.verdict == cl.DUPLICATE_CELL


def test_the_shared_window_is_recomputed_over_the_merged_cells(tmp_path):
    """`shared_window` is an intersection over every cell in the file, so a
    merge that copied the base's line would publish an intersection that does
    not include the new column."""
    header = cl.load_header(W10)
    extra = cl._render(header, [
        {"scenario": "cafe_head_on_v0.yaml", "controller": "narrow_mppi",
         "admissible": (), "ladder": header["ladder"], "min_spread": 1.0,
         "completes_anywhere": True, "calibratable": False}])
    merged = cl.merge_tables(W10, _write(tmp_path, "n.yaml", extra))
    assert "shared_window: []" in merged

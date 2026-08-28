# SPDX-License-Identifier: BSD-3-Clause
"""The `lam` ladder cannot move every arm, and the census does not say so.

STATE's five-cycle bottleneck asked whether the shipped `lam = 0.1` sits at a
window **edge** or in its **interior** on the 8 cells that admit it. These tests
pin the third answer: the 8 windows *are* the ladder, because `essps_mppi`
solves its temperature per step and never reads the one the ladder passes.

The readings here are measurements, not transcriptions — `probe` constructs the
real controllers and calls the real `_softmax_lam`. An arm that starts or stops
reading `p.lam` moves these numbers, which is the point.
"""

from __future__ import annotations

import numpy as np
import pytest

from eval.mppi_sandbox import lam_inertness as li
from eval.mppi_sandbox.controllers import REGISTRY
from eval.mppi_sandbox.operating_point import SHIPPED_LAM, ladder_census, windows


# --------------------------------------------------------------------------
# the probe itself
# --------------------------------------------------------------------------

def test_probe_cost_is_non_degenerate():
    """A constant cost vector would make every arm read as inert.

    Named in `lam_inertness`'s scope note as the way this probe could report a
    false positive on all 8 arms at once, so it is checked rather than assumed.
    """
    cost = li.probe_cost()
    assert cost.size == li.PROBE_K
    assert float(cost.std()) > 1.0
    assert float(cost.min()) < float(cost.max())


def test_probe_endpoints_span_the_ladder():
    """The negative result is only as strong as the input range it survives."""
    lo, hi = li.PROBE_LAMS
    assert hi / lo == pytest.approx(128.0)


def test_probe_is_deterministic():
    a, b = li.probe("essps_mppi"), li.probe("essps_mppi")
    assert (a.out_lo, a.out_hi) == (b.out_lo, b.out_hi)


# --------------------------------------------------------------------------
# which arms read the ladder
# --------------------------------------------------------------------------

def test_essps_is_the_only_inert_arm():
    """Measured over the whole registry, not transcribed from a literal."""
    assert li.inert_arms() == ("essps_mppi",)


def test_every_registered_arm_is_probed():
    """The census covers the registry — a new arm cannot skip the reading."""
    assert {r.controller for r in li.responses()} == set(REGISTRY)


def test_inert_arm_ignores_the_passed_lam():
    """Same output at both endpoints, and equal to neither input."""
    r = li.probe("essps_mppi")
    assert r.out_lo == r.out_hi
    assert not r.responds
    assert r.out_lo not in li.PROBE_LAMS
    # the solved temperature lands inside the ladder's span, which is why the
    # inertness is invisible in a window: every rung "works" because the arm
    # was never at that rung.
    assert li.PROBE_LAMS[0] < r.out_lo < li.PROBE_LAMS[1]


def test_responsive_arms_pass_the_lam_through_verbatim():
    """No registered arm scales or clips the temperature — a third verdict
    (`responds` but not `passes_through`) is currently unoccupied."""
    for r in li.responses():
        if r.controller == "essps_mppi":
            continue
        assert r.passes_through, r
        assert (r.out_lo, r.out_hi) == li.PROBE_LAMS


def test_passes_through_and_responds_are_distinct_properties():
    """A hypothetical scaling arm responds without passing through."""
    scaled = li.LamResponse("hypothetical", 0.05, 6.4, 0.10, 12.8)
    assert scaled.responds and not scaled.passes_through


# --------------------------------------------------------------------------
# the bottleneck's own question
# --------------------------------------------------------------------------

def test_shipped_lam_has_no_responsive_support():
    """The finding: 8 cells admit `0.1`, and not one of them reads `0.1`."""
    s = li.shipped_lam_support()
    assert s.rung == SHIPPED_LAM
    assert s.total == 8
    assert s.responsive == ()
    assert s.vacuous
    assert {c for _, c in s.inert} == {"essps_mppi"}


def test_shipped_lam_support_is_one_cell_per_scene():
    """One per scene, which is what made the pattern look like a property."""
    s = li.shipped_lam_support()
    scenes = [sc for sc, _ in s.inert]
    assert len(scenes) == len(set(scenes)) == 8


def test_the_count_is_not_about_the_rung():
    """`0.05` has the identical support, so "8 cells admit 0.1" is a fact about
    which scenes `essps_mppi` completes — not about the temperature."""
    assert li.rung_support(0.05).inert == li.shipped_lam_support().inert
    assert li.rung_support(0.05).total == li.shipped_lam_support().total


def test_every_cell_admitting_shipped_lam_is_saturated():
    """Refutes both options the bottleneck offered: the window has no edge on
    the ladder, so `0.1` is neither at one nor strictly inside one."""
    sat = {(c.scene, c.controller) for c in li.saturated_cells()}
    for key in li.shipped_lam_support().inert:
        assert key in sat
        assert windows()[key] == tuple(sorted(windows()[key]))
        assert len(windows()[key]) == 8


def test_saturation_and_inertness_agree_on_every_cell():
    """The observable and the mechanism are cross-checked, not assumed equal.

    A responsive arm that saturated would break this and would be a real
    finding — a scene forgiving at every temperature — rather than a bug.
    """
    inert = set(li.inert_arms())
    for c in li.saturated_cells():
        assert c.controller in inert, c
    # …and the converse, over cells the inert arm can complete at all:
    for c in li.cells():
        if c.controller in inert and not c.empty:
            assert c.saturated, c


# --------------------------------------------------------------------------
# what it costs the shipped census
# --------------------------------------------------------------------------

def test_inert_cells_inflate_every_supported_rung_equally():
    """`ladder_census` counts the 8 inert cells at *every* rung they were
    walked at, so its totals over-state responsive support by a constant 8."""
    census = ladder_census()
    for rung, total in census.items():
        s = li.rung_support(rung)
        assert s.total == total, rung
        assert len(s.inert) == 8, rung
        assert len(s.responsive) == total - 8, rung


def test_responsive_support_peaks_where_the_total_does():
    """The correction shifts no conclusion about the plant's usable band — the
    band still peaks at 0.4 — which is why the defect survived five cycles."""
    resp = {r: len(li.rung_support(r).responsive) for r in ladder_census()}
    assert max(resp, key=resp.__getitem__) == 0.4


def test_shipped_and_lowest_rungs_are_the_only_vacuous_supported_ones():
    """Exactly the two rungs `operating_point` reports as the plant's dead end
    are the two with zero responsive support."""
    vacuous = {r for r in ladder_census() if li.rung_support(r).vacuous}
    assert vacuous == {0.05, SHIPPED_LAM}


# --------------------------------------------------------------------------
# structure
# --------------------------------------------------------------------------

def test_cells_covers_both_window_files():
    """`cells` re-reads the yaml to keep each row's own ladder, which
    `operating_point.windows` drops — so it must not lose rows doing it."""
    assert len(li.cells()) == len(windows())


def test_every_cell_carries_a_ladder():
    """`saturated` is meaningless without one; a row inheriting the file-level
    ladder must still report it."""
    for c in li.cells():
        assert c.ladder, c


def test_the_refined_cell_keeps_its_own_longer_ladder():
    """One cell was re-walked at a finer resolution (D-482) and carries a
    9-rung ladder; a file-level default would erase that."""
    refined = [c for c in li.cells() if len(c.ladder) != 8]
    assert len(refined) == 1
    assert (refined[0].scene, refined[0].controller) == (
        "cafe_obstacle_crossing_v0.yaml", "cbf_mppi")
    assert refined[0].empty


def test_saturated_requires_a_ladder():
    """An empty ladder is not saturation — it is an unwalked cell."""
    assert not li.Cell("x.yaml", "stock_mppi", (), ()).saturated
    assert li.Cell("x.yaml", "stock_mppi", (0.2,), (0.2,)).saturated
    assert not li.Cell("x.yaml", "stock_mppi", (0.2,), (0.2, 0.4)).saturated


def test_report_states_the_finding():
    text = li.report()
    assert "INERT" in text and "essps_mppi" in text
    assert "NO responsive support" in text


def test_probe_accepts_an_injected_cost_vector():
    """So a caller can ask the question on a cost field it chose."""
    flat = np.ones(li.PROBE_K)
    r = li.probe("stock_mppi", cost=flat)
    assert r.passes_through

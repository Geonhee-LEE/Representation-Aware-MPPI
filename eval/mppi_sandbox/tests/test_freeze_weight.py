# SPDX-License-Identifier: BSD-3-Clause
"""`freeze_weight` — admissibility, the shape verdict, and the lam pin.

The verdict tests are synthetic on purpose: the question "is this admissible
set a plateau or a knife edge" is arithmetic over cells, and pinning it against
simulated cells would make the pin as slow and as seed-dependent as the thing
it is checking. The two tests that *do* simulate are the ones whose content is
a measurement — the scene's limit and the lam non-comparability.
"""

from __future__ import annotations

import pytest

from eval.mppi_sandbox import freeze_weight as fw
from eval.mppi_sandbox.freeze_price import FREEZING_SCENE, profile_arm

LIMIT = 2.0


def cell(w: float, longest, clearance, reached=None, limit: float = LIMIT):
    """A `WeightCell` from bare sequences — `reached` defaults to all-true."""
    longest = tuple(float(x) for x in longest)
    return fw.WeightCell(
        w_freeze=float(w),
        longest=longest,
        clearance=tuple(float(c) for c in clearance),
        reached=tuple(reached if reached is not None
                      else [True] * len(longest)),
        limit=limit,
    )


BASE = cell(0.0, [3.0, 3.0], [0.9, 0.9])          # exceeds; clearance 0.9
GOOD = cell(1e4, [0.5, 0.5], [0.95, 0.95])        # clears all three clauses


# --- the three admissibility clauses, both directions -----------------------

def test_admissible_requires_no_exceedance():
    assert fw.admissible(GOOD, BASE)
    over = cell(1e4, [0.5, 2.01], [0.95, 0.95])
    assert not fw.admissible(over, BASE)


def test_admissible_requires_every_run_to_reach():
    stalled_out = cell(1e4, [0.5, 0.5], [0.95, 0.95], reached=[True, False])
    assert not fw.admissible(stalled_out, BASE)


def test_admissible_refuses_freeze_bought_with_clearance():
    """The clause that makes this a price and not a score (D-243's 1e5 cell)."""
    cheaper = cell(1e5, [0.5, 0.5], [0.95, 0.844])
    assert cheaper.n_exceed == 0            # the freeze *is* gone
    assert not fw.admissible(cheaper, BASE)  # and it was paid for


def test_clearance_clause_is_worst_case_not_mean():
    """One bad seed convicts: a mean would let it hide behind eleven good ones."""
    one_bad = cell(1e4, [0.5] * 3, [1.5, 1.5, 0.5])
    assert one_bad.worst_clearance == pytest.approx(0.5)
    assert not fw.admissible(one_bad, cell(0.0, [3.0] * 3, [0.9] * 3))


def test_eps_admits_a_clearance_tie():
    tie = cell(1e4, [0.5, 0.5], [0.9, 0.9 - fw.EPS_CLEARANCE / 2])
    assert fw.admissible(tie, BASE)


# --- the ablation is denominator, not candidate -----------------------------

def test_ablation_is_never_in_the_admissible_set():
    """Even a passing ablation: it is the state the term must improve on."""
    passing_base = cell(0.0, [0.5, 0.5], [0.9, 0.9])
    assert fw.admissible_mask([passing_base, GOOD])[0] is False


def test_admissible_mask_refuses_cells_not_led_by_the_ablation():
    with pytest.raises(ValueError, match="must be the w_freeze = 0 ablation"):
        fw.admissible_mask([GOOD, GOOD])


# --- the shape verdict ------------------------------------------------------

def bad(w):
    return cell(w, [3.0, 3.0], [0.9, 0.9])


def good(w):
    return cell(w, [0.5, 0.5], [0.95, 0.95])


def test_verdict_no_freeze_to_price_outranks_everything():
    """Checked first: every other verdict presumes the baseline fails."""
    passing_base = cell(0.0, [0.5, 0.5], [0.9, 0.9])
    assert fw.verdict([passing_base, good(1e3), bad(1e4)]) \
        == "NO_FREEZE_TO_PRICE"


def test_verdict_none_admissible():
    assert fw.verdict([BASE, bad(1e3), bad(1e4)]) == "NONE_ADMISSIBLE"


def test_verdict_knife_edge():
    assert fw.verdict([BASE, bad(1e3), good(1e4), bad(1e5)]) == "KNIFE_EDGE"


def test_verdict_plateau_reports_its_width():
    cells = [BASE, bad(1e3), good(3e3), good(1e4), good(3e4), bad(1e5)]
    assert fw.verdict(cells) == "PLATEAU width=3"


def test_verdict_edge_open_when_the_top_of_the_grid_is_admissible():
    """The upper end is unmeasured, so the set has no measured width yet."""
    assert fw.verdict([BASE, bad(1e3), good(1e4), good(1e5)]) == "EDGE_OPEN"


def test_verdict_fragmented_beats_plateau_on_a_gap():
    cells = [BASE, good(1e3), bad(3e3), good(1e4), bad(1e5)]
    assert fw.verdict(cells) == "FRAGMENTED"


def test_verdict_on_no_cells_is_none_admissible():
    assert fw.verdict([]) == "NONE_ADMISSIBLE"


# --- the tolerance ladder ---------------------------------------------------

def test_ladder_separates_a_real_knife_edge_from_a_tolerance_artifact():
    """A weight losing only on a 0.5 mm clearance dip is not a failed weight.

    This is the shape the n=12 sweep actually produced: `3e3` and `3e4` clear
    the freeze outright and sit within a millimetre of the ablation's worst-case
    clearance, so `EPS_CLEARANCE` alone reads KNIFE_EDGE where any physically
    meaningful tolerance reads PLATEAU.
    """
    base = cell(0.0, [3.0] * 2, [0.9214, 0.9214])
    near = cell(3e3, [0.5] * 2, [0.9209, 0.9209])   # 0.5 mm below base
    peak = cell(1e4, [0.4] * 2, [0.9214, 0.9214])
    cells = [base, near, peak, bad(1e5)]

    ladder = fw.verdict_ladder(cells)
    assert ladder[fw.EPS_CLEARANCE] == "KNIFE_EDGE"   # `near` disqualified
    assert ladder[1e-3] == "PLATEAU width=2"          # `near` admitted
    assert fw.admissible_mask(cells, eps=1e-3) == (False, True, True, False)
    assert not fw.verdict_is_threshold_robust(cells)


def test_threshold_robust_when_every_rung_agrees():
    cells = [BASE, bad(1e3), good(1e4), bad(1e5)]
    assert fw.verdict_is_threshold_robust(cells)
    assert set(fw.verdict_ladder(cells).values()) == {"KNIFE_EDGE"}


def test_ladder_keys_are_the_epsilons_it_walked():
    cells = [BASE, good(1e4), bad(1e5)]
    assert tuple(fw.verdict_ladder(cells)) == fw.EPS_LADDER


# --- the two measured pins --------------------------------------------------

def test_scene_limit_is_read_from_the_scene_not_typed():
    from eval.mppi_sandbox.scenario import load_scenario

    declared = load_scenario(FREEZING_SCENE).acceptance["freeze_duration_max"]
    assert fw.scene_limit() == pytest.approx(float(declared))


def test_scene_limit_refuses_a_scene_that_declares_none():
    with pytest.raises(ValueError, match="no freeze_duration_max"):
        fw.scene_limit("eval/scenarios/cafe_straight_v0.yaml")


def test_the_freeze_reading_is_not_comparable_across_temperatures():
    """The finding, pinned: D-243's numbers do not survive the paired lam.

    `social_mppi` on `cafe_freezing_v0`, same seed, same scene, same arm — only
    the softmax temperature moves. At `D243_LAM` the longest along-path stall
    is seconds; at `PAIRED_LAM` it is over a minute, and `reached` is true in
    both, so nothing completion-based notices. A `w_freeze` cell quoted without
    its lam is therefore not a claim about anything.
    """
    from eval.mppi_sandbox.controllers.stock_mppi import MPPIParams

    at_d243 = profile_arm(FREEZING_SCENE, fw.ARM, seed=0,
                          params=MPPIParams(lam=fw.D243_LAM))
    at_paired = profile_arm(FREEZING_SCENE, fw.ARM, seed=0,
                            params=MPPIParams(lam=fw.PAIRED_LAM))

    assert at_d243.reached and at_paired.reached
    assert at_paired.longest > 10 * at_d243.longest
    assert at_paired.longest > fw.scene_limit()


def test_d243_lam_is_the_shipped_default_not_a_second_spelling():
    """If `StockMPPI`'s default moves, this constant is wrong, not stale."""
    from eval.mppi_sandbox.controllers.stock_mppi import MPPIParams

    assert MPPIParams().lam == pytest.approx(fw.D243_LAM)

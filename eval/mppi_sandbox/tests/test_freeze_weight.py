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
    """Flat failure: 2/2 exceed at both weights, so the grid ends on a tie."""
    assert fw.verdict([BASE, bad(1e3), bad(1e4)]) == "NONE_ADMISSIBLE"


# --- the empty admissible set has two causes (the lam=0.8 finding) ----------

def test_trend_is_open_only_when_the_top_cell_improves():
    falling = cell(1e5, [3.0, 0.5], [0.9, 0.9])       # 1/2 exceed
    assert falling.n_exceed == 1 and bad(3e4).n_exceed == 2
    assert fw.trend_is_open([BASE, bad(3e4), falling])
    assert not fw.trend_is_open([BASE, bad(3e4), bad(1e5)])       # flat
    assert not fw.trend_is_open([BASE, falling, bad(1e5)])        # worsening


def test_trend_needs_two_cells_to_have_a_direction():
    assert not fw.trend_is_open([])
    assert not fw.trend_is_open([BASE])


def test_verdict_separates_a_grid_that_ran_out_from_one_that_answered():
    """The `PAIRED_LAM` shape: nothing admissible, top cell still improving.

    Both verdicts have an empty admissible set; only one of them licenses the
    sentence "the term does not buy the freeze". Quoting that from the open
    case is the inadmissible-side twin of the `EDGE_OPEN` over-claim.
    """
    still_working = cell(1e5, [3.0, 0.5], [0.9, 0.9])
    assert fw.verdict([BASE, bad(1e4), bad(3e4), still_working]) \
        == "NONE_ADMISSIBLE_TREND_OPEN"
    assert fw.verdict([BASE, bad(1e4), bad(3e4), bad(1e5)]) == "NONE_ADMISSIBLE"


# --- the open trend, closed: the grid was extended and reversed (D-246) -----

def test_optimum_is_bracketed_needs_failure_above_the_best_cell():
    """The measured `PAIRED_LAM` shape, as arithmetic over cells.

    `3e4 -> 8/12`, `1e5 -> 6/12`, `3e5 -> 12/12`: the best cell is interior and
    both flanks fail, so the sweep walked *past* the optimum rather than
    stopping at it. That is what makes its `NONE_ADMISSIBLE` a result.
    """
    turned_around = [BASE, bad(3e4), cell(1e5, [3.0, 0.5], [0.9, 0.9]),
                     bad(3e5)]
    assert fw.optimum_is_bracketed(turned_around)


def test_a_grid_that_ends_on_its_best_cell_is_not_bracketed():
    assert not fw.optimum_is_bracketed(
        [BASE, bad(3e4), cell(1e5, [3.0, 0.5], [0.9, 0.9])])


def test_bracketing_is_stronger_than_a_closed_trend():
    """The gap `trend_is_open` cannot see, and the reason both predicates exist.

    Exceedance `8, 6, 6` ends **flat**, so the two-cell comparison reads the
    trend as closed — while the best cell is still the last one taken and
    everything above it is unmeasured. Bracketing reads the whole candidate
    range and refuses.
    """
    still_falling = cell(1e5, [3.0, 0.5], [0.9, 0.9])       # 1/2 exceed
    flat_top = [BASE, bad(3e4), still_falling,
                cell(3e5, [3.0, 0.5], [0.9, 0.9])]          # also 1/2
    assert not fw.trend_is_open(flat_top)                    # says: closed
    assert not fw.optimum_is_bracketed(flat_top)             # says: still short


def test_bracketing_excludes_the_ablation_and_needs_a_real_range():
    """The ablation anchors the bottom by construction, so it is not a
    candidate — and two cells cannot bracket anything."""
    assert not fw.optimum_is_bracketed([])
    assert not fw.optimum_is_bracketed([BASE])
    assert not fw.optimum_is_bracketed([BASE, bad(1e5)])


def test_the_default_grid_reaches_past_the_measured_turnaround():
    """D-246's grid extension, pinned where a re-tune would announce itself.

    The turnaround sits at `1e5`; a grid that stops there reports
    `NONE_ADMISSIBLE_TREND_OPEN` and cannot say whether the term fails or the
    budget ran out. The two cells above it are what closed that question.
    """
    assert fw.GRID[0] == 0.0                       # ablation still leads
    assert 3e5 in fw.GRID and 1e6 in fw.GRID
    assert fw.GRID[-1] > 1e5


def test_an_admissible_cell_outranks_the_open_trend():
    """`trend_is_open` is consulted only when nothing cleared the clauses."""
    assert fw.verdict([BASE, good(1e4), cell(1e5, [3.0, 0.5], [0.9, 0.9])]) \
        == "KNIFE_EDGE"


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


def test_paired_lam_is_the_lam_the_paired_protocol_actually_runs():
    """`PAIRED_LAM` is typed here but *owned* by `three_arm`.

    The module imports `freeze_duration` and reads `freeze_duration_max` off
    the scene rather than respelling either; this constant is the one place
    that discipline is not structurally enforced, because importing `three_arm`
    at module scope would pull the whole A/B stack into a module whose other
    imports are all deferred. The pin buys the same guarantee: if the paired
    protocol re-tunes its temperature, this goes red rather than silently
    describing a comparison nobody runs.
    """
    from eval.mppi_sandbox.three_arm import LAM as three_arm_lam

    assert fw.PAIRED_LAM == pytest.approx(three_arm_lam)


def test_the_d243_plateau_does_not_survive_the_paired_temperature():
    """D-245's load-bearing claim, at one seed and one weight.

    D-244 read `PLATEAU width=2` over `{3e3, 1e4}` at `D243_LAM`. At
    `PAIRED_LAM` the *centre* of that plateau leaves the arm stalled for tens
    of seconds against a 2.0 s limit — so the plateau is not shifted by the
    temperature move, it is void. The full n=12 sweep is far too slow to pin;
    this is the single cell that carries the claim.
    """
    from eval.mppi_sandbox.controllers.stock_mppi import MPPIParams

    priced = profile_arm(FREEZING_SCENE, fw.ARM, seed=0,
                         params=MPPIParams(lam=fw.PAIRED_LAM), w_freeze=1e4)

    assert priced.reached                      # completion stays blind to it
    assert priced.longest > 10 * fw.scene_limit()


# --- the arrival-scoped re-read (D-250) -------------------------------------

def test_omitted_before_reading_defaults_to_the_whole_trajectory_one():
    """A cell built without `longest_before` must not claim an unmeasured scope.

    Back-compat with every caller written before the scope axis existed: such a
    cell *is* a whole-trajectory cell, and reading it as arrival-scoped would
    manufacture a `before` number nobody took.
    """
    c = cell(1e4, [3.0, 0.5], [0.9, 0.9])
    assert c.longest_before == c.longest
    assert c.n_exceed_in(fw.SCOPE_BEFORE) == c.n_exceed_in(fw.SCOPE_WHOLE)
    assert c.arrival == (None, None)


def test_scope_selects_which_reading_the_exceedance_counts():
    contaminated = fw.WeightCell(
        w_freeze=0.0, longest=(82.0, 83.0), clearance=(0.93, 0.93),
        reached=(True, True), limit=LIMIT,
        longest_before=(0.4, 0.4), arrival=(9.8, 10.0))
    assert contaminated.n_exceed_in(fw.SCOPE_WHOLE) == 2
    assert contaminated.n_exceed_in(fw.SCOPE_BEFORE) == 0
    assert contaminated.n_exceed == 2          # the property stays whole-scoped
    assert contaminated.n_exceed_before == 0
    with pytest.raises(ValueError):
        contaminated.n_exceed_in("since-tuesday")


def test_the_two_scopes_reach_opposite_verdicts_on_the_measured_grid():
    """D-250's headline, as arithmetic over the shape D-248 measured.

    Whole-trajectory: the ablation exceeds and nothing is admissible. Scoped to
    arrival: the ablation *passes*, so there was never a freeze to price. Same
    runs, same clearances — only the rows the stall was read over differ.
    """
    ablation = fw.WeightCell(
        w_freeze=0.0, longest=(82.7, 82.7), clearance=(0.9372, 0.9372),
        reached=(True, True), limit=LIMIT,
        longest_before=(0.4, 0.4), arrival=(9.75, 9.75))
    priced = fw.WeightCell(
        w_freeze=1e4, longest=(64.15, 64.15), clearance=(0.899, 0.899),
        reached=(True, True), limit=LIMIT,
        longest_before=(0.3, 0.3), arrival=(10.35, 10.35))
    cells = (ablation, priced)

    assert fw.verdict(cells, scope=fw.SCOPE_WHOLE) == "NONE_ADMISSIBLE"
    assert fw.verdict(cells, scope=fw.SCOPE_BEFORE) == "NO_FREEZE_TO_PRICE"
    assert fw.scope_disagrees(cells)
    # The default is the arrival-scoped one — the reading a freeze claim needs.
    assert fw.verdict(cells) == fw.verdict(cells, scope=fw.SCOPE_BEFORE)


def test_arrival_and_reached_are_different_completion_readings():
    """`reached_goal` is xy-at-the-final-step; `time_to_goal` is xy+yaw at any.

    Measured at `w_freeze = 1e6`: 12/12 reached, 0/12 arrived. The admissibility
    clause reads `n_reached`, so a cell can pass completion while no run ever
    made the goal *pose* — which is why `n_arrived` is carried beside it
    (Q-146).
    """
    parked = fw.WeightCell(
        w_freeze=1e6, longest=(8.7, 8.7), clearance=(0.8369, 0.8369),
        reached=(True, True), limit=LIMIT,
        longest_before=(8.7, 8.7), arrival=(None, None))
    assert parked.n_reached == 2
    assert parked.n_arrived == 0
    # No arrival ⇒ the two scopes coincide by construction, not by convention.
    assert parked.n_exceed_in(fw.SCOPE_BEFORE) == parked.n_exceed_in(fw.SCOPE_WHOLE)


def test_the_ablation_does_not_freeze_before_arrival_on_this_scene():
    """The re-read's claim, simulated — two seeds of the `w_freeze = 0` cell.

    The full n=12 x 10-weight grid is ~9 minutes and cannot live in the suite;
    this is the cell the verdict turns on. If the scene ever starts genuinely
    freezing this arm before it arrives, this goes red and `NO_FREEZE_TO_PRICE`
    stops being the answer.
    """
    cells = fw.sweep(weights=(0.0,), seeds=(0, 1), lam=fw.PAIRED_LAM)
    ablation = cells[0]
    assert ablation.n_arrived == 2
    assert ablation.n_exceed_in(fw.SCOPE_BEFORE) == 0
    assert ablation.n_exceed_in(fw.SCOPE_WHOLE) == 2     # the contaminated read
    assert fw.verdict(cells) == "NO_FREEZE_TO_PRICE"

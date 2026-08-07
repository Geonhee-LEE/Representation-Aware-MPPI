# SPDX-License-Identifier: BSD-3-Clause
"""D-126's `PER_SCENE_REQUIRED`, turned into the weight each cell runs at.

Every test but the last two is a pure function of a synthetic `ReliefInterval`
and pays for no sim. The two that do run pick `cafe_straight` (0.29 s/seed) and
monkeypatch the sweep respectively — the injection claim is about *what params
the controller is constructed with*, which is observable without integrating
anything.
"""

from __future__ import annotations

import pytest

from eval.mppi_sandbox import baseline_matrix, operating_weight as ow
from eval.mppi_sandbox import relief_interval as ri
from eval.mppi_sandbox.baseline_matrix import pick_lam, run_cell, run_matrix
from eval.mppi_sandbox.controllers.stock_mppi import MPPIParams

SHIPPED = ri.shipped_weight()
STRAIGHT = "eval/scenarios/cafe_straight_v0.yaml"
#: Named, never defaulted: at the shipped 0.1 the sampler is a greedy argmin,
#: so a test that leaves it implicit is asserting about the temperature.
LAM = 0.8


def _interval(*, verdict, admissible=(), relieving=(), baseline_unsafe=1.0,
              needs_relief=True, baseline_admissible=False,
              scenario="s.yaml") -> ri.ReliefInterval:
    return ri.ReliefInterval(
        scenario=scenario, lam=LAM, baseline_value=SHIPPED,
        baseline_unsafe=baseline_unsafe, needs_relief=needs_relief,
        baseline_admissible=baseline_admissible,
        admissible=tuple(admissible), relieving=tuple(relieving),
        verdict=verdict)


# ------------------------------------------------------- the rule is pick_lam's

def test_pick_weight_is_pick_lam_not_a_second_log_middle():
    """One statement of the rule (D-047), two names for it.

    If this ever diverges, the project has two answers to "which rung
    represents this set" — the exact duplication D-123 found between `pick_lam`
    and `ab.lam_for` and had to reconcile after the fact.
    """
    for rungs in [(30.0,), (30.0, 100.0), (30.0, 100.0, 300.0),
                  (300.0, 1000.0, 3000.0), (30.0, 100.0, 300.0, 1000.0)]:
        assert ow.pick_weight(rungs) == pick_lam(rungs)


def test_relieved_scene_runs_at_the_middle_rung_not_its_threshold():
    """The substantive policy choice, pinned so a change is a diff.

    `cafe_head_on_v0`'s measured set is {300, 1000, 3000} and its *threshold*
    is 300 — one ladder step from not relieving at all. The middle rung is the
    one whose verdict survives the ladder being re-walked.
    """
    choice = ow.resolve(_interval(verdict=ri.RELIEF_FOUND,
                                  admissible=(300.0, 1000.0, 3000.0),
                                  relieving=(300.0, 1000.0, 3000.0)))
    assert choice.basis == ow.RELIEVED
    assert choice.weight == 1000.0
    assert choice.weight != min(choice.permitted)   # not the threshold
    assert choice.moved


def test_scene_that_needed_no_relief_is_not_moved_by_one_that_did():
    """D-126's disjointness finding, one layer down.

    `cafe_convoy_v0` needs no relief and tolerates only up to 30, so the
    shipped 10 is inside its permitted set. A resolver that handed it head-on's
    1000 would re-create the global repin the survey refuted — and would do it
    invisibly, because convoy's cells would still *run*.
    """
    choice = ow.resolve(_interval(verdict=ri.NO_RELIEF_NEEDED,
                                  admissible=(30.0,), needs_relief=False,
                                  baseline_unsafe=0.0,
                                  baseline_admissible=True))
    assert choice.basis == ow.SHIPPED
    assert choice.weight == SHIPPED
    assert not choice.moved
    # The shipped weight is not a ladder rung, so this must NOT have been
    # decided by set membership — see `test_shipped_weight_is_never_a_rung`.
    assert SHIPPED not in choice.permitted


def test_shipped_weight_is_never_a_rung_so_membership_cannot_decide_shipped():
    """The defect the previous test's `SHIPPED` branch was first written with.

    `DEFAULT_LADDER` starts at 30 and the shipped weight is 10, so
    `shipped in permits` is false for **every** scene no matter what it
    tolerates. Any resolver deciding "keep the shipped weight" by membership
    would move every no-relief scene to the ladder's floor — including convoy,
    whose refusal is the whole of D-126. Pinned as an arithmetic fact about the
    two constants so a future ladder edit that happens to include 10.0 does not
    quietly make the wrong rule work again.
    """
    assert SHIPPED not in ri.DEFAULT_LADDER

    unmoved = ow.resolve(_interval(verdict=ri.NO_RELIEF_NEEDED,
                                   admissible=(30.0,), needs_relief=False,
                                   baseline_unsafe=0.0,
                                   baseline_admissible=True))
    moved = ow.resolve(_interval(verdict=ri.NO_RELIEF_NEEDED,
                                 admissible=(30.0,), needs_relief=False,
                                 baseline_unsafe=0.0,
                                 baseline_admissible=False))
    # Identical rung sets, opposite outcomes — so the rung set is provably not
    # what decided it.
    assert unmoved.permitted == moved.permitted
    assert (unmoved.basis, unmoved.weight) == (ow.SHIPPED, SHIPPED)
    assert (moved.basis, moved.weight) == (ow.REPAIRED, 30.0)


def test_scene_needing_no_relief_but_failing_its_shipped_weight_is_repaired():
    """`SHIPPED` is not the default for "needs nothing" — admissibility is.

    A scene can be safe at the shipped weight and still be inadmissible there
    (out of band, so the sampler is not weighing the cost). It has to run
    somewhere, and its own permitted set is the only non-guess.
    """
    choice = ow.resolve(_interval(verdict=ri.NO_RELIEF_NEEDED,
                                  admissible=(100.0, 300.0, 1000.0),
                                  needs_relief=False, baseline_unsafe=0.0))
    assert choice.basis == ow.REPAIRED
    assert choice.weight == 300.0
    assert SHIPPED not in choice.permitted


def test_unrelieved_scene_keeps_the_shipped_weight_rather_than_guessing():
    """No tested rung relieves it, so there is no operating point to move to.

    Moving it anyway would change its number without justifying it — a verdict
    bought by a weight nothing showed to work.
    """
    choice = ow.resolve(_interval(verdict=ri.UNRELIEVED,
                                  admissible=(30.0, 100.0), relieving=()))
    assert choice.basis == ow.UNRELIEVED
    assert choice.weight == SHIPPED
    assert choice.permitted == ()


def test_subresolution_scene_may_refuse_a_rung_but_not_demand_one():
    """D-126's fourth verdict, inherited rather than re-derived.

    A scene unsafe by less than `MIN_IMPROVEMENT` cannot demonstrate relief, so
    it votes with `admissible`. `ReliefInterval.permits` already encodes that;
    this pins that the resolver reads it instead of re-testing `needs_relief`.
    """
    below = ri.barrier_ceiling.MIN_IMPROVEMENT / 2
    sub = ow.resolve(_interval(verdict=ri.SUBRESOLUTION,
                               admissible=(30.0, 100.0), relieving=(),
                               baseline_unsafe=below))
    # It has an empty `relieving` and still gets a weight, drawn from
    # `admissible` — it refused the shipped 10 without demanding a relief the
    # survey cannot measure.
    assert sub.basis == ow.REPAIRED
    assert sub.permitted == (30.0, 100.0)
    assert sub.weight == 100.0

    # The contrast that makes the verdict load-bearing: same empty `relieving`,
    # same admissible set, but a resolvable baseline ⇒ `UNRELIEVED`, and an
    # unrelieved scene gets no weight at all.
    resolvable = ow.resolve(_interval(verdict=ri.UNRELIEVED,
                                      admissible=(30.0, 100.0), relieving=(),
                                      baseline_unsafe=1.0))
    assert resolvable.basis == ow.UNRELIEVED
    assert resolvable.weight == SHIPPED


def test_unswept_scene_gets_a_named_choice_not_an_absent_one():
    """`cafe_freezing_v0` / `cafe_cut_in_v0`: the survey could not reach them.

    They keep the shipped weight under a basis that says *why*, rather than
    silently inheriting a neighbour's rung or vanishing from the table.
    """
    choice = ow.resolve(None)
    assert choice.basis == ow.UNSWEPT
    assert choice.weight == SHIPPED
    assert not choice.moved


# --------------------------------------------------------------- the whole table

def test_table_covers_refused_scenes_rather_than_shortening():
    """A short table reads as "the matrix is the part that could be measured".

    That is D-107/D-120's empty-denominator failure arriving as a missing key,
    which a caller iterating the table would never see.
    """
    swept = _interval(verdict=ri.RELIEF_FOUND, scenario="a.yaml",
                      admissible=(300.0, 1000.0), relieving=(300.0, 1000.0))
    survey = ri.reconcile([swept], refused={"b.yaml": ri.NO_DECLARED_MARGIN})
    t = ow.table(survey, scenarios=["a.yaml", "b.yaml", "c.yaml"])
    assert set(t) == {"a.yaml", "b.yaml", "c.yaml"}
    assert t["a.yaml"].basis == ow.RELIEVED
    assert t["b.yaml"].basis == ow.UNSWEPT      # refused by the survey
    assert t["c.yaml"].basis == ow.UNSWEPT      # never offered to it
    assert ow.weights(t)["b.yaml"] == SHIPPED


def test_table_records_the_controller_the_survey_was_measured_on():
    """The extrapolation is named, so a per-arm survey is a different table."""
    swept = _interval(verdict=ri.RELIEF_FOUND, scenario="a.yaml",
                      admissible=(300.0, 1000.0), relieving=(300.0, 1000.0))
    t = ow.table(ri.reconcile([swept]), scenarios=["a.yaml"])
    assert t["a.yaml"].measured_on == "stock_mppi"


def test_render_names_which_scenes_moved():
    swept = _interval(verdict=ri.RELIEF_FOUND, scenario="a.yaml",
                      admissible=(300.0, 1000.0), relieving=(300.0, 1000.0))
    text = ow.render(ow.table(ri.reconcile([swept]), scenarios=["a.yaml"]))
    assert "a.yaml" in text and "moved off shipped: 1/1" in text


# ------------------------------------------------- injection into the matrix

def test_lam_and_weight_reach_the_controller_in_one_params(monkeypatch):
    """The regression this cycle's edit exists to prevent.

    `run_cell` built `MPPIParams(lam=...)`, which **resets every other field to
    its shipped default**. A second injection carrying the weight would have
    been silently overwritten back to 10.0 — the exact operating point D-126
    proved two of these scenes fail at, and the failure would look like "the
    per-scene weights changed nothing".
    """
    seen: dict = {}

    def _fake(scenario, controller, seeds, **kw):
        seen.update(kw)
        return []

    monkeypatch.setattr(baseline_matrix, "seed_sweep", _fake)
    monkeypatch.setattr(baseline_matrix, "summarize",
                        lambda runs: baseline_matrix.SweepStats(
                            n=0, collisions=0, collision_rate=float("nan"),
                            mean_clearance=float("nan"),
                            median_clearance=float("nan"),
                            min_clearance=float("nan"), mean_speed=float("nan"),
                            all_reached=False, median_ess=None, n_samples=256,
                            ess_in_band=None))
    run_cell(STRAIGHT, "stock_mppi", range(1), lam=LAM, w_obs_soft=300.0)

    params = seen["params"]
    assert params.lam == LAM
    assert params.w_obs_soft == 300.0
    # Everything not named keeps its shipped value — the injection is an
    # override of two fields, not a fresh params object with two survivors.
    assert params.obs_soft_scale == MPPIParams().obs_soft_scale


def test_weightless_matrix_is_the_pre_d126_matrix():
    """`weights=None` must be bit-comparable to what the headline was measured
    on, or the correction cannot be attributed to the weights."""
    m = run_matrix([STRAIGHT], ["stock_mppi"], range(1), calibrated=False)
    assert [c.w_obs_soft for c in m.cells] == [None]


def test_matrix_keys_weights_by_scene_file_not_stem():
    """`run_matrix` looks up `Path(s).name`; `Cell.scenario` is the stem.

    Keying the table by stem would miss every lookup and the matrix would run
    at shipped weights while reporting that it had not — a silent null.
    """
    m = run_matrix([STRAIGHT], ["stock_mppi"], range(1), calibrated=False,
                   weights={"cafe_straight_v0.yaml": 300.0})
    assert [c.w_obs_soft for c in m.cells] == [300.0]
    assert m.cells[0].scenario == "cafe_straight_v0"


# ------------------------------------------ Q-113: the scene weight per cell

def test_admits_cannot_use_rung_membership_for_the_shipped_weight():
    """The bug `resolve` books, one layer out: the ladder never holds `SHIPPED`.

    A cell whose *baseline* is admissible tolerates the shipped weight, and no
    rung set can say so. If `admits` were `weight in admissible`, this cell
    would read inadmissible at the one value it was actually measured at.
    """
    cell = _interval(verdict=ri.NO_RELIEF_NEEDED, needs_relief=False,
                     baseline_admissible=True, admissible=(3000.0,))
    assert SHIPPED not in cell.admissible          # by construction
    assert ow.admits(cell, SHIPPED) is True        # measured, not inferred
    assert ow.admits(cell, 3000.0) is True
    assert ow.admits(cell, 1000.0) is False


def test_admits_tests_admissibility_not_relief():
    """An unsafe-but-tolerated rung keeps the cell in the denominator."""
    cell = _interval(verdict=ri.RELIEF_FOUND, admissible=(100.0, 3000.0),
                     relieving=(3000.0,))
    assert ow.admits(cell, 100.0) is True          # tolerated, still unsafe
    assert 100.0 not in cell.relieving


def test_cell_that_rejects_its_scene_weight_but_has_its_own_is_named():
    """D-127's excluded cell, from its measured numbers.

    `risk_mppi/cafe_obstacle_crossing_v0` at λ=3.2: the ladder's only admissible
    rung is 3000, so the scene's 1000 is inadmissible here. The verdict must be
    `CELL_DIFFERS` — the cell *is* measurable — and it must carry the cell's own
    weight, because "excluded" and "unanswerable" are different findings.
    """
    scene = ow.WeightChoice(scenario="cafe_obstacle_crossing_v0.yaml",
                            weight=1000.0, basis=ow.RELIEVED,
                            permitted=(300.0, 1000.0, 3000.0),
                            measured_on="stock_mppi")
    cell = _interval(verdict=ri.RELIEF_FOUND, admissible=(3000.0,),
                     relieving=(3000.0,), baseline_admissible=True,
                     scenario="cafe_obstacle_crossing_v0.yaml")
    a = ow.audit_cell(scene, cell, controller="risk_mppi")
    assert a.verdict == ow.CELL_DIFFERS
    assert a.excluded is True
    assert a.cell_weight == 3000.0
    assert a.scene_weight == 1000.0


def test_the_measured_admissible_set_is_non_contiguous_on_the_weight_axis():
    """The live instance of `relief_interval`'s refusal to use intervals.

    Measured on `risk_mppi/cafe_obstacle_crossing_v0`, λ=3.2, 8 seeds — the
    median ESS walks 91.9 → 80.1 → 205.5 → 204.7 → 157.6 → 27.5 → 11.9 across
    w = 10 (baseline), 30, 100, 300, 1000, 3000, 10000, and the band admits only
    the **first and second-to-last**. So the set of tolerated weights is two
    islands, `{10, 3000}`, separated by five rungs that all fail.

    Interval arithmetic over `[min, max]` of that set would nominate 100, 300 and
    1000 — every one of them inadmissible on the very cell the interval came
    from. That is precisely the unsoundness the module preamble declined to
    assume away, and until now it existed only as a synthetic mid-ladder hole.
    """
    cell = _interval(verdict=ri.RELIEF_FOUND, admissible=(3000.0,),
                     relieving=(3000.0,), baseline_admissible=True)
    tolerated = sorted({SHIPPED, *cell.admissible})
    assert tolerated == [10.0, 3000.0]
    # The span implied by an interval reading, and what it would wrongly admit.
    for wrongly_admitted in (100.0, 300.0, 1000.0):
        assert min(tolerated) < wrongly_admitted < max(tolerated)
        assert ow.admits(cell, wrongly_admitted) is False


def test_single_rung_admissible_set_reports_knife_edge():
    """One tolerated rung is a measurement, not a robust operating point."""
    edge = _interval(verdict=ri.RELIEF_FOUND, admissible=(3000.0,),
                     relieving=(3000.0,))
    wide = _interval(verdict=ri.RELIEF_FOUND, admissible=(300.0, 1000.0, 3000.0),
                     relieving=(300.0, 1000.0, 3000.0))
    scene = ow.WeightChoice(scenario="s.yaml", weight=1000.0, basis=ow.RELIEVED)
    assert ow.audit_cell(scene, edge, controller="risk_mppi").knife_edge is True
    assert ow.audit_cell(scene, wide, controller="risk_mppi").knife_edge is False


def test_cell_agreeing_with_its_scene_weight_is_not_excluded():
    cell = _interval(verdict=ri.RELIEF_FOUND, admissible=(300.0, 1000.0),
                     relieving=(1000.0,))
    scene = ow.WeightChoice(scenario="s.yaml", weight=1000.0, basis=ow.RELIEVED)
    a = ow.audit_cell(scene, cell, controller="risk_mppi")
    assert a.verdict == ow.CELL_AGREES
    assert a.excluded is False
    assert a.cell_weight == a.scene_weight


def test_cell_tolerating_nothing_is_unserved_not_silently_shipped():
    """`resolve` falls back to the shipped weight; if the cell fails there too,
    that fallback is not an operating point and must not be reported as one."""
    cell = _interval(verdict=ri.UNRELIEVED, admissible=(),
                     baseline_admissible=False)
    scene = ow.WeightChoice(scenario="s.yaml", weight=1000.0, basis=ow.RELIEVED)
    a = ow.audit_cell(scene, cell, controller="risk_mppi")
    assert a.verdict == ow.CELL_UNSERVED
    assert a.cell_weight is None
    assert a.excluded is True


def test_cell_tolerating_only_the_shipped_weight_still_has_somewhere_to_run():
    """`CELL_UNSERVED` is about having no operating point, not about having a
    boring one — a cell that tolerates only the un-laddered shipped value is
    `CELL_DIFFERS`, and this is the case rung membership alone would misgrade."""
    cell = _interval(verdict=ri.UNRELIEVED, admissible=(),
                     baseline_admissible=True)
    scene = ow.WeightChoice(scenario="s.yaml", weight=1000.0, basis=ow.RELIEVED)
    a = ow.audit_cell(scene, cell, controller="risk_mppi")
    assert a.verdict == ow.CELL_DIFFERS
    assert a.cell_weight == SHIPPED


def test_render_audits_names_the_excluded_cells():
    cells = [
        ow.audit_cell(
            ow.WeightChoice(scenario="a.yaml", weight=1000.0, basis=ow.RELIEVED),
            _interval(verdict=ri.RELIEF_FOUND, admissible=(3000.0,),
                      relieving=(3000.0,), scenario="a.yaml"),
            controller="risk_mppi"),
        ow.audit_cell(
            ow.WeightChoice(scenario="b.yaml", weight=1000.0, basis=ow.RELIEVED),
            _interval(verdict=ri.RELIEF_FOUND, admissible=(1000.0,),
                      relieving=(1000.0,), scenario="b.yaml"),
            controller="risk_mppi"),
    ]
    out = ow.render_audits(cells)
    assert "excluded from the scene-keyed headline: 1/2" in out
    assert "risk_mppi/a.yaml" in out
    assert "KNIFE_EDGE" in out

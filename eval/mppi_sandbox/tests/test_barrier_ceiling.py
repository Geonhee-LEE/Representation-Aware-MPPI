# SPDX-License-Identifier: BSD-3-Clause
"""Q-110's sweep: what counts as the barrier winning, and what only looks like it."""

from __future__ import annotations

import math

import pytest

from eval.mppi_sandbox import barrier_ceiling as bc
from eval.mppi_sandbox.scenario import load_scenario

#: Every rung in this file is built at the temperature the D-123/D-124 cycles
#: matched on. Named rather than defaulted: `MPPIParams.lam` ships at 0.1, where
#: this scene's median ESS is ~1 of 256 and no additive term is audible, so a
#: test that silently inherited it would be asserting about the sampler.
LAM = 0.8

HEAD_ON = "eval/scenarios/cafe_head_on_v0.yaml"


def rung(value=10.0, unsafe=1.0, *, reached=True, band=True, mean_clr=0.01,
         cte=0.10, declared=0.30) -> bc.Rung:
    return bc.Rung(
        knob=bc.WEIGHT_KNOB, value=value, n=8, unsafe_rate=unsafe,
        mean_clearance=mean_clr, min_clearance=mean_clr / 2.0,
        all_reached=reached, median_ess=64.0, ess_in_band=band,
        cte_rms_worst=cte, declared_cte_rms_max=declared,
    )


# --------------------------------------------------------------------------
# Admissibility — the two filters that make a rung evidence about the term.
# --------------------------------------------------------------------------

def test_a_frozen_rung_is_not_evidence():
    """`ab.assert_all_reached` exists because freeze buys clearance. A rung
    that stopped finishing has bought its safety number, not measured it."""
    assert not rung(reached=False).admissible
    assert "froze" in rung(reached=False).inadmissible_because


def test_a_rung_outside_the_ess_band_is_not_evidence():
    """D-027's failure mode: a weight big enough to collapse the softmax
    changed the *sampler*, so the arm's behaviour is not the term's doing."""
    assert not rung(band=False).admissible
    assert "ess_out_of_band" in rung(band=False).inadmissible_because


def test_unknown_band_is_not_a_pass():
    """`SweepStats.ess_in_band` is `None` when any seed was unmeasurable.
    Unknown must not read as compliant — the sticky-`None` rule from `ab`."""
    r = rung(band=None)
    assert not r.admissible
    assert "ess_unknown" in r.inadmissible_because


def test_an_admissible_rung_names_no_reason():
    assert rung().admissible
    assert rung().inadmissible_because == ()


# --------------------------------------------------------------------------
# The verdicts, and the distinction between the two negatives.
# --------------------------------------------------------------------------

def test_no_rung_improves_is_saturated():
    base = rung(unsafe=1.0)
    assert bc.classify(base, [rung(value=v, unsafe=1.0)
                              for v in (30.0, 100.0, 300.0)]) == bc.SATURATED


def test_an_admissible_improvement_is_relieved():
    base = rung(unsafe=1.0)
    rungs = [rung(value=100.0, unsafe=1.0), rung(value=300.0, unsafe=0.0)]
    assert bc.classify(base, rungs) == bc.RELIEVED


def test_an_improvement_only_at_inadmissible_rungs_is_not_relieved():
    """The distinction the two negative verdicts exist for: the barrier does
    move the verdict, and the price is that it stops being a cost-term change."""
    base = rung(unsafe=1.0)
    rungs = [rung(value=300.0, unsafe=0.0, reached=False),
             rung(value=1000.0, unsafe=0.0, band=False)]
    assert bc.classify(base, rungs) == bc.BOUGHT_INADMISSIBLY


def test_saturated_and_bought_inadmissibly_are_distinct_strings():
    """Both are 'no' to Q-110 and they license different next moves, so a
    caller must not be able to collapse them with a truthiness check."""
    assert bc.SATURATED != bc.BOUGHT_INADMISSIBLY
    assert bc.RELIEVED not in (bc.SATURATED, bc.BOUGHT_INADMISSIBLY)


def test_improvement_under_half_a_seed_does_not_count():
    """On n = 8 one seed is 0.125; anything smaller is a rung failing to
    distinguish itself from its neighbour, not a relief."""
    base = rung(unsafe=1.0)
    assert bc.classify(base, [rung(value=300.0, unsafe=1.0 - 0.03)]) == bc.SATURATED
    assert bc.classify(base, [rung(value=300.0, unsafe=1.0 - 0.125)]) == bc.RELIEVED


# --------------------------------------------------------------------------
# Tracking is reported on its own axis, not folded into admissibility.
# --------------------------------------------------------------------------

def test_tracking_is_not_part_of_admissibility():
    """D-116 / D-119's lesson. 'Is this number evidence?' and 'is this
    controller acceptable?' are different questions; a rung may be a clean
    measurement of a controller the scene would still reject."""
    broken = rung(cte=0.9, declared=0.30)
    assert broken.admissible
    assert broken.tracking_ok is False


def test_tracking_is_unknown_when_the_scene_declares_no_bound():
    assert rung(declared=None).tracking_ok is None


def test_tracking_boundary_is_closed_on_the_compliant_side():
    assert rung(cte=0.30, declared=0.30).tracking_ok is True
    assert rung(cte=0.30 + 1e-9, declared=0.30).tracking_ok is False


# --------------------------------------------------------------------------
# Result accessors.
# --------------------------------------------------------------------------

def result(*rungs) -> bc.SweepResult:
    base = rung(unsafe=1.0, mean_clr=0.0056)
    return bc.SweepResult(
        scenario=HEAD_ON, knob=bc.WEIGHT_KNOB, lam=LAM, margin=0.40,
        baseline=base, rungs=tuple(rungs),
        verdict=bc.classify(base, rungs),
    )


def test_ceiling_is_the_largest_admissible_rung_not_the_best_one():
    """`ceiling` answers 'how far can this knob go before it stops being a
    cost-term change', which is a different rung from the best-scoring one."""
    res = result(rung(value=300.0, unsafe=0.0),
                 rung(value=1000.0, unsafe=0.0),
                 rung(value=3000.0, unsafe=0.0, band=False))
    assert res.ceiling.value == 1000.0


def test_no_admissible_rung_leaves_ceiling_and_best_none():
    res = result(rung(value=300.0, unsafe=0.0, reached=False))
    assert res.ceiling is None and res.best_admissible is None
    assert math.isnan(res.clearance_gain)


def test_clearance_gain_is_a_multiple_of_the_baseline():
    """The number D-119 (32x) and D-124 (1.7x) both reported without moving a
    verdict — computed the same way so the three are comparable."""
    res = result(rung(value=300.0, unsafe=0.0, mean_clr=0.056))
    assert res.clearance_gain == pytest.approx(10.0)


# --------------------------------------------------------------------------
# Refusals.
# --------------------------------------------------------------------------

def test_an_unsweepable_knob_is_refused_by_name():
    scen = load_scenario(HEAD_ON)
    with pytest.raises(ValueError, match="w_path"):
        bc.sweep(scen, "w_path", [1.0], lam=LAM)


def test_a_scene_with_no_declared_margin_is_refused_not_defaulted():
    """D-120's `unscored_margin` rule: an undeclared bar must not become a
    convenient 0.0, which would score every run clean for free."""
    scen = load_scenario("eval/scenarios/cafe_freezing_v0.yaml")
    with pytest.raises(ValueError, match="no scorable margin"):
        bc.sweep(scen, bc.WEIGHT_KNOB, [300.0], lam=LAM)


# --------------------------------------------------------------------------
# The measured answer. Slow: closed-loop runs.
# --------------------------------------------------------------------------

@pytest.mark.slow
def test_head_on_is_relieved_by_the_gain_knob():
    """Q-110's answer. The shipped `w_obs_soft = 10` leaves `cafe_head_on_v0`
    unsafe on every seed; 300 clears the scene's 0.40 m on every seed, with
    the arm still finishing and the softmax still in band."""
    scen = load_scenario(HEAD_ON)
    res = bc.sweep(scen, bc.WEIGHT_KNOB, [300.0], lam=LAM,
                   scenario_name=HEAD_ON, seeds=range(4),
                   measure_spread=False)
    assert res.baseline.unsafe_rate == 1.0
    assert res.verdict == bc.RELIEVED
    best = res.best_admissible
    assert best is not None and best.unsafe_rate == 0.0
    # The win is not paid for on the scene's other declared key.
    assert best.tracking_ok is True


@pytest.mark.slow
def test_the_decay_length_knob_saturates_where_the_gain_knob_relieves():
    """The two knobs are swept separately because they answer differently:
    8x on `obs_soft_scale` moves no verdict at all. Sweeping a single
    'barrier strength' axis would have averaged these into one wrong story."""
    scen = load_scenario(HEAD_ON)
    res = bc.sweep(scen, bc.SCALE_KNOB, [1.2], lam=LAM,
                   scenario_name=HEAD_ON, seeds=range(4),
                   measure_spread=False)
    assert res.verdict == bc.SATURATED

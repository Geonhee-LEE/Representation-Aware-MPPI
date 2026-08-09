"""The threshold-free comparison and, above all, the reading that makes it worth
having: the rungs the margin censuses had to drop are the ones that separate
most (STATE #1, arxiv 2605.18045)."""

from __future__ import annotations

import math

import pytest

from eval.mppi_sandbox import derived_margin as dm
from eval.mppi_sandbox import margin_free as mf
from eval.mppi_sandbox.scene_transplant import (
    MARGIN_DECIDES_VERDICT,
    NO_TWO_SIDED_TO_SPREAD,
)


def _rung(census, scenario_fragment, weight):
    (hit,) = [r for r in census.rungs
              if scenario_fragment in r.scenario and r.weight == weight]
    return hit


# --------------------------------------------------------------------------
# The statistic itself
# --------------------------------------------------------------------------

def test_superiority_is_half_when_the_samples_are_identical():
    assert mf.superiority((1.0, 2.0, 3.0), (1.0, 2.0, 3.0)) == 0.5


def test_superiority_counts_ties_as_half_a_win():
    # One pair, exactly tied: the whole statistic is that pair's half-win.
    assert mf.superiority((1.0,), (1.0,)) == 0.5
    # Two of four cross pairs tied, one won, one lost.
    assert mf.superiority((0.0, 1.0), (1.0, 0.0)) == 0.5


def test_superiority_saturates_on_disjoint_samples():
    assert mf.superiority((0.0, 0.1), (1.0, 1.1)) == 1.0
    assert mf.superiority((1.0, 1.1), (0.0, 0.1)) == 0.0


def test_superiority_refuses_an_empty_arm():
    with pytest.raises(ValueError, match="non-empty"):
        mf.superiority((), (1.0,))


def test_superiority_is_invariant_under_a_monotone_re_choice_of_scale():
    """The margin-freeness claim, proved structurally rather than by example.

    The module docstring says `A` is fixed under any monotone re-choice of
    threshold because it is a rank statistic. If that is true, then rescaling
    both arms by *any* strictly increasing map must leave it exactly alone —
    which is a far stronger test than checking one number, and it is the
    property the whole cycle rests on.
    """
    census = mf.census()
    for rung in census.rungs:
        plain = rung.superiority
        for warp in (lambda v: v ** 3,
                     lambda v: math.log(v + 1.0),
                     lambda v: 7.0 * v - 2.5,
                     lambda v: math.tanh(v)):
            warped = mf.superiority(tuple(warp(x) for x in rung.stock),
                                    tuple(warp(y) for y in rung.risk))
            assert warped == plain, f"{rung.scenario} w={rung.weight:g}"


def test_pairing_is_by_seed_index_and_unequal_arms_are_refused():
    with pytest.raises(ValueError, match="paired by seed index"):
        mf.RungComparison(scenario="s", weight=1.0, declared_margin=0.3,
                          censoring=NO_TWO_SIDED_TO_SPREAD,
                          stock=(1.0, 2.0), risk=(1.0,))


# --------------------------------------------------------------------------
# Coverage — the contrast with the two threshold censuses
# --------------------------------------------------------------------------

def test_every_walked_rung_and_every_eligible_scene_has_a_reading():
    assert mf.census().coverage == (6, 6, 3, 3)


def test_coverage_beats_the_derived_margin_route_on_the_same_population():
    """Same denominator, different numerator — that is the whole claim.

    :func:`margin_free.comparisons` is built off `walked_rungs()`, so if the
    population ever changes both censuses move together and this comparison
    stays honest.
    """
    free = mf.census()
    derived = dm.census()
    assert derived.rung_coverage == (2, 6)
    assert derived.scene_coverage == (1, 3)
    free_rungs, total_rungs, free_scenes, total_scenes = free.coverage
    assert (total_rungs, total_scenes) == (derived.rung_coverage[1],
                                           derived.scene_coverage[1])
    assert free_rungs > derived.rung_coverage[0]
    assert free_scenes > derived.scene_coverage[0]


# --------------------------------------------------------------------------
# The finding
# --------------------------------------------------------------------------

def test_the_censored_rungs_are_the_ones_that_separate_most():
    census = mf.census()
    assert census.verdict == mf.CENSORING_ANTI_INFORMATIVE
    assert len(census.censored) == 3 and len(census.scoreable) == 3
    # Strict group separation, not an overlap that happens to average right.
    assert (min(r.effect for r in census.censored)
            > max(r.effect for r in census.scoreable))


def test_the_docstring_magnitudes_are_the_measured_ones():
    """D-158's lesson: prose magnitudes are inside the verification surface.

    Every number the module docstring quotes is pinned here, so a re-walk that
    moves the data cannot leave the explanation standing.
    """
    census = mf.census()
    assert _rung(census, "convoy", 75).superiority == pytest.approx(1.0, abs=5e-5)
    assert _rung(census, "head_on", 75).superiority == pytest.approx(0.9980, abs=5e-5)
    assert _rung(census, "head_on", 100).superiority == pytest.approx(0.9980, abs=5e-5)
    assert _rung(census, "head_on", 150).superiority == pytest.approx(0.9473, abs=5e-5)
    assert _rung(census, "head_on", 250).superiority == pytest.approx(0.8457, abs=5e-5)
    assert _rung(census, "crossing", 250).superiority == pytest.approx(0.4980, abs=5e-5)
    assert min(r.effect for r in census.censored) == pytest.approx(0.4980, abs=5e-5)
    assert max(r.effect for r in census.scoreable) == pytest.approx(0.4473, abs=5e-5)


def test_convoy_separates_perfectly_and_is_the_rung_no_threshold_can_score():
    """The single sharpest instance: the arms' clearance ranges are disjoint —
    which is *why* no threshold has both interior."""
    convoy = _rung(mf.census(), "convoy", 75)
    assert convoy.censoring == NO_TWO_SIDED_TO_SPREAD
    assert convoy.superiority == 1.0
    assert max(convoy.stock) < min(convoy.risk)


def test_the_rung_the_threshold_decides_is_the_measured_tie():
    """D-164 read `MARGIN_DECIDES_VERDICT` as the threshold picking the answer.

    Margin-free it is a coin flip whose CI contains zero, so there is no answer
    for a threshold to pick — the two readings are one fact.
    """
    census = mf.census()
    (decided,) = census.decided_by_margin
    assert decided.censoring == MARGIN_DECIDES_VERDICT
    assert decided.superiority == pytest.approx(0.5, abs=0.01)
    lo, hi = decided.bootstrap_ci()
    assert lo < 0.0 < hi
    assert census.ties == (decided,)


def test_five_of_six_rungs_favour_the_risk_arm_and_none_favour_stock():
    census = mf.census()
    assert len(census.favouring_risk) == 5
    assert all(r.superiority >= 0.4980 for r in census.rungs)


# --------------------------------------------------------------------------
# The bootstrap / TOST layer
# --------------------------------------------------------------------------

def test_the_bootstrap_is_reproducible_and_seed_sensitive():
    rung = _rung(mf.census(), "head_on", 250)
    assert rung.bootstrap_ci(seed=3) == rung.bootstrap_ci(seed=3)
    assert rung.bootstrap_ci(seed=3) != rung.bootstrap_ci(seed=4)


def test_bootstrap_refuses_zero_replicates():
    rung = _rung(mf.census(), "head_on", 250)
    with pytest.raises(ValueError, match="at least one replicate"):
        rung.bootstrap_ci(reps=0)


def test_equivalence_refuses_a_non_positive_effect_size():
    rung = _rung(mf.census(), "head_on", 250)
    with pytest.raises(ValueError, match="positive effect size"):
        rung.equivalence(0.0)


def test_the_tie_reads_equivalent_at_an_effect_size_the_separated_rungs_do_not():
    """The verdict censoring cannot reach, reached.

    A censored rung has no threshold at which both arms are interior, so the
    threshold route cannot report *agreement* either — only silence. At
    ε = 0.05 m the crossing rung says the arms agree and convoy says they do
    not, which is two different answers where the census had one absence.
    """
    census = mf.census()
    crossing = _rung(census, "crossing", 250)
    convoy = _rung(census, "convoy", 75)
    assert crossing.equivalence(0.05) == mf.EQUIVALENT
    assert convoy.equivalence(0.05) == mf.SUPERIOR


def test_equivalence_margin_is_the_smallest_eps_that_reads_equivalent():
    rung = _rung(mf.census(), "crossing", 250)
    eps = rung.equivalence_margin()
    assert rung.equivalence(eps * 1.001) == mf.EQUIVALENT
    assert rung.equivalence(eps * 0.999) != mf.EQUIVALENT


def test_indeterminate_is_distinct_from_equivalent():
    """A tolerance tighter than the CI cannot conclude agreement — and must not
    be allowed to report it."""
    rung = _rung(mf.census(), "crossing", 250)
    assert rung.equivalence(0.0001) == mf.INDETERMINATE


def test_inferior_has_no_shipped_witness_so_it_is_proved_synthetically():
    """`INFERIOR` is unreachable from the recorded runs (no rung favours stock).

    Proved on a constructed rung rather than deleted, because a one-sided
    instrument and a two-sided one with nothing on one side read identically on
    this population, and only the synthetic case separates them.
    """
    worse = mf.RungComparison(
        scenario="synthetic", weight=1.0, declared_margin=0.3,
        censoring=NO_TWO_SIDED_TO_SPREAD,
        stock=tuple(1.0 + 0.01 * i for i in range(16)),
        risk=tuple(0.5 + 0.01 * i for i in range(16)))
    assert worse.superiority == 0.0
    assert worse.equivalence(0.05) == mf.INFERIOR


# --------------------------------------------------------------------------
# The alignment reading's other branches — D-107's empty-population shape
# --------------------------------------------------------------------------

def _synthetic(censoring, stock, risk):
    return mf.RungComparison(scenario="synthetic", weight=1.0,
                             declared_margin=0.3, censoring=censoring,
                             stock=stock, risk=risk)


_TIED = ((1.0, 1.0, 1.0), (1.0, 1.0, 1.0))
_SPLIT = ((0.0, 0.0, 0.0), (1.0, 1.0, 1.0))
_HALF = ((0.0, 0.0, 1.0), (1.0, 1.0, 1.0))


def test_censoring_aligned_is_reachable():
    """The mirror verdict: censoring drops only the rungs with little to say.
    If this were unreachable, `CENSORING_ANTI_INFORMATIVE` would be the only
    thing the property can print and would mean nothing."""
    census = mf.MarginFreeCensus(rungs=(
        _synthetic(NO_TWO_SIDED_TO_SPREAD, *_TIED),
        _synthetic(MARGIN_DECIDES_VERDICT, *_SPLIT)))
    assert census.censoring_alignment == mf.CENSORING_ALIGNED


def test_censoring_mixed_when_the_groups_interleave():
    census = mf.MarginFreeCensus(rungs=(
        _synthetic(NO_TWO_SIDED_TO_SPREAD, *_SPLIT),
        _synthetic(NO_TWO_SIDED_TO_SPREAD, *_TIED),
        _synthetic(MARGIN_DECIDES_VERDICT, *_HALF)))
    assert census.censoring_alignment == mf.CENSORING_MIXED


@pytest.mark.parametrize("censoring", [NO_TWO_SIDED_TO_SPREAD,
                                       MARGIN_DECIDES_VERDICT])
def test_one_sided_populations_report_uncomparable_not_a_verdict(censoring):
    """D-107's shape: with nothing on one side of the split there is no
    comparison, and a group-separation test on an empty group is vacuously
    true. It must not print as a finding."""
    census = mf.MarginFreeCensus(rungs=(_synthetic(censoring, *_SPLIT),))
    assert census.censoring_alignment == mf.CENSORING_UNCOMPARABLE


def test_an_empty_census_is_uncomparable_too():
    assert mf.MarginFreeCensus(rungs=()).censoring_alignment == \
        mf.CENSORING_UNCOMPARABLE

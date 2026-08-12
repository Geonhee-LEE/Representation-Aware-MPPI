# SPDX-License-Identifier: BSD-3-Clause
"""The seed-widened off-family 2x2, and what the two estimands do to it.

D-223 published `+0.0486 / -0.0085 m` on 6 seeds and called the pattern the
mirror image of the cafe family. Seeds 0..5 of :data:`paired_step.WALK_20` are
*those* seeds, so this file can check the reproduction and the widening on one
population — and the first two tests below are the reason the cycle was worth
running: the reproduction is exact, and the sign does not survive either
widening the ensemble **or** pairing the same six runs.

Nothing here asserts that `w_ped` must be inert off-family, or that the mirror
must be false. What is pinned is the arithmetic, the pairing contract, and the
one place the resampler is defined (D-047).
"""

from __future__ import annotations

import pytest

from eval.mppi_sandbox.margin_free import RungComparison
from eval.mppi_sandbox.paired_step import (
    MIN_IS_N_DEPENDENT,
    NOT_SEPARATED,
    SEPARATED_NEGATIVE,
    SEPARATED_POSITIVE,
    WALK_20,
    WALK_20_REACHED,
    PairedStep,
    estimand_drift,
    min_step_is_n_dependent,
    nested_worst_steps,
    paired_step,
    sign_test_p,
    steps,
)
from eval.mppi_sandbox.three_arm import W_PED_COLS, W_RISK_ROWS


def test_the_six_seed_prefix_reproduces_the_published_worst_case_steps():
    """D-223's table, recomputed from the first 6 seeds of this walk.

    If this drifts, the 20-seed reading is being compared against a 6-seed one
    it does not contain, and every statement below about widening is about two
    different walks instead of one.
    """
    assert nested_worst_steps(0.0)[6] == pytest.approx(+0.0486, abs=5e-4)
    assert nested_worst_steps(40.0)[6] == pytest.approx(-0.0085, abs=5e-4)


def test_the_published_sign_does_not_survive_either_widening_or_pairing():
    """The `w_risk = 0` row read three ways on runs that overlap completely.

    - worst-case at n=6:  **+0.0486** (published, "standalone helps")
    - worst-case at n=20: negative
    - paired mean at n=6: negative — *the same six runs*

    The third line is the one that matters. Widening an ensemble is expected to
    move a minimum; a sign that reverses without adding a single run is a
    property of the statistic chosen, not of the sample size, and that is what
    `worst_step` being a difference of two unpaired minima buys.
    """
    six = PairedStep(scene="x", w_risk=0.0,
                     base=WALK_20[(0.0, 0.0)][:6], arm=WALK_20[(0.0, 50.0)][:6])
    assert six.worst_step > 0.0
    assert six.mean_step < 0.0
    assert nested_worst_steps(0.0)[20] < 0.0


def test_neither_row_separates_from_zero_at_twenty_seeds():
    """The reading STATE asked for, stated as the verdict rather than prose."""
    read = steps()
    assert read[0.0].verdict == NOT_SEPARATED
    assert read[40.0].verdict == NOT_SEPARATED
    for w in W_RISK_ROWS:
        lo, hi = read[w].ci()
        assert lo < 0.0 < hi


def test_the_sign_test_agrees_that_neither_row_resolves_a_direction():
    """The claim D-222/D-223 made is about a sign, so it is tested as one.

    9+/11- in both rows is what a fair coin does. Pinned loosely (p > 0.5)
    because the point is that it is nowhere near a resolution, not that it is
    0.8238.
    """
    for w in W_RISK_ROWS:
        pos, neg, tie = steps()[w].sign_counts
        assert pos + neg + tie == 20
        assert steps()[w].sign_p > 0.5


def test_no_cell_bought_its_reading_by_freezing():
    """`three_arm.step_bought_with_freeze`'s question, asked of this walk.

    A clearance table with a frozen robot in it is unreadable regardless of
    which estimand it is read in, so this precondition is checked before any
    of the above means anything.
    """
    for w_risk in W_RISK_ROWS:
        for w_ped in W_PED_COLS:
            assert WALK_20_REACHED[(w_risk, w_ped)] == 20
            assert len(WALK_20[(w_risk, w_ped)]) == 20


def test_the_minimum_can_only_fall_as_seeds_are_added():
    """The theorem :func:`min_step_is_n_dependent` returns, checked on the
    walk as an implementation guard on the prefix logic — the prefixes must be
    nested and seed-ordered, or `nested_worst_steps` is comparing two samples
    rather than a sample and its extension."""
    for cell, clearances in WALK_20.items():
        assert min(clearances) <= min(clearances[:6]), cell


def test_the_direction_verdict_consults_no_data():
    """`seed_count_licence.licence_direction`'s precedent: a property of `min`
    is not a finding about these arms and must not need a population to
    state."""
    assert min_step_is_n_dependent() == MIN_IS_N_DEPENDENT


def test_the_drift_is_reported_and_is_not_the_same_in_both_rows():
    """Both rows' worst-case step moved between the prefixes, and by different
    amounts — which is why the drift of a *difference* of minima carries no
    known sign even though each minimum's does."""
    drift = estimand_drift()
    assert set(drift) == set(W_RISK_ROWS)
    assert all(d != 0.0 for d in drift.values())
    assert drift[0.0] != drift[40.0]


def test_the_bootstrap_is_the_one_the_branch_already_had():
    """`PairedStep.ci` must *be* `RungComparison.bootstrap_ci`, not a second
    implementation of it (D-047: two statements of a rule eventually differ).
    Pinned by equality on the same data at the same seed."""
    s = paired_step(0.0)
    mirror = RungComparison(scenario=s.scene, weight=s.w_risk,
                            declared_margin=0.0, censoring="",
                            stock=s.base, risk=s.arm)
    assert s.ci(reps=500, seed=3) == mirror.bootstrap_ci(reps=500, seed=3)
    assert s.mean_step == mirror.paired_delta


def test_unequal_cells_are_refused_rather_than_zipped():
    """`zip` truncates silently; an unpaired step is not a shorter one."""
    with pytest.raises(ValueError, match="paired by seed index"):
        PairedStep(scene="x", w_risk=0.0, base=(0.1, 0.2), arm=(0.1,))
    with pytest.raises(ValueError, match="at least one seed"):
        PairedStep(scene="x", w_risk=0.0, base=(), arm=())


def test_the_sign_test_is_exact_and_drops_ties():
    """Boundary behaviour of the p-value, checked against hand arithmetic."""
    assert sign_test_p([1.0] * 5) == pytest.approx(2 * (1 / 32))
    assert sign_test_p([0.0] * 9) == 1.0
    # Ties dropped: three effective pairs, all one way -> 2 * (1/8).
    assert sign_test_p([1.0, 1.0, 1.0, 0.0, 0.0]) == pytest.approx(0.25)
    assert sign_test_p([1.0, -1.0]) == 1.0


def test_the_separation_verdicts_read_off_the_interval():
    """Both separated verdicts are reachable — a verdict vocabulary that only
    ever returns one token is not grading anything (D-107's shape)."""
    up = PairedStep(scene="x", w_risk=0.0,
                    base=tuple(0.10 for _ in range(12)),
                    arm=tuple(0.30 + 0.001 * i for i in range(12)))
    down = PairedStep(scene="x", w_risk=0.0, base=up.arm, arm=up.base)
    assert up.verdict == SEPARATED_POSITIVE
    assert down.verdict == SEPARATED_NEGATIVE

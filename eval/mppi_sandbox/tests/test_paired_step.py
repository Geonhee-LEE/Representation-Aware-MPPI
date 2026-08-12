# SPDX-License-Identifier: BSD-3-Clause
"""The seed-widened off-family 2x2, and what the two estimands do to it.

D-223 published `+0.0486 / -0.0085 m` on 6 seeds and called the pattern the
mirror image of the cafe family. Seeds 0..5 of :data:`paired_step.WALK_20` are
*those* seeds, so this file can check the reproduction and the widening on one
population — and the first two tests below are the reason the cycle was worth
running: the reproduction is exact, and the sign does not survive either
widening the ensemble **or** pairing the same six runs.

The second half applies the identical pair of estimands to the **cafe** scene
the branch's headline was taken on (Q-135). It is the control the retraction
needs: there both rows separate, unanimously and with opposite signs, so
pairing is not an acid that dissolves every step on this branch — it dissolved
those arms.

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
    WALK_CAFE_6,
    WALK_CAFE_6_REACHED,
    PairedStep,
    cafe_steps,
    estimand_drift,
    min_step_is_n_dependent,
    nested_worst_steps,
    paired_step,
    sign_test_p,
    steps,
    walk_cells,
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


# --- Q-135: the same two estimands, applied to the cafe family -------------
#
# The off-family tests above are a retraction. These are the control that
# makes it one: if pairing dissolved every step on this branch, the honest
# reading of D-224 would be "the statistic is broken everywhere" rather than
# "those arms were noise". The cafe row is where the branch's headline lives,
# and it is read here with the identical class, walk shape and resampler.


def test_the_cafe_walk_reproduces_the_published_d218_pair():
    """`worst_step` on the cafe walk is D-218's published `+0.3755 / -0.0192`.

    The reproduction is what licenses calling this a *re-reading*: the runs
    behind `WALK_CAFE_6` give back the exact pair the branch published in the
    old estimand, so any difference the paired estimand shows below is the
    estimand's doing and not a different measurement's.
    """
    rows = cafe_steps()
    assert rows[W_RISK_ROWS[0]].worst_step == pytest.approx(+0.3755, abs=5e-5)
    assert rows[W_RISK_ROWS[1]].worst_step == pytest.approx(-0.0192, abs=5e-5)


def test_the_cafe_sign_flip_survives_the_paired_estimand():
    """Q-135's question, answered on the scene its lean named.

    Off-family, pairing took both rows to `NOT_SEPARATED` (the tests above).
    On the cafe scene both rows separate from zero **and keep the opposite
    signs** `interaction_sign_flip` was built on, so the D-217 -> D-219 line
    rests on a paired result rather than on a difference of ensemble minima.
    """
    rows = cafe_steps()
    top, bottom = rows[W_RISK_ROWS[0]], rows[W_RISK_ROWS[1]]

    assert top.verdict == SEPARATED_POSITIVE
    assert bottom.verdict == SEPARATED_NEGATIVE
    assert top.mean_step > 0.0 > bottom.mean_step

    # ...and the intervals are on opposite sides of zero, which is the sign
    # flip stated in the paired estimand rather than inferred from two minima.
    assert top.ci()[0] > 0.0
    assert bottom.ci()[1] < 0.0


def test_both_cafe_rows_are_unanimous_and_that_is_the_p_floor():
    """6/6 in both rows — and the reason `p` is reported next to `n`.

    At `n = 6` the smallest attainable two-sided sign-test p is
    `2 / 2**6 = 0.03125`, so unanimity is the *strongest* statement six seeds
    can make and `p = 0.031` is a floor, not a margin. Pinning the floor keeps
    a later reader from mistaking it for a comfortable distance below 0.05.
    """
    rows = cafe_steps()
    assert rows[W_RISK_ROWS[0]].sign_counts == (6, 0, 0)
    assert rows[W_RISK_ROWS[1]].sign_counts == (0, 6, 0)
    for row in rows.values():
        assert row.sign_p == pytest.approx(2 / 2 ** 6)
    assert sign_test_p((1.0,) * 6) == pytest.approx(2 / 2 ** 6)


def test_pairing_moves_the_cafe_rows_it_does_not_only_confirm_them():
    """The paired mean is not a rounding of `worst_step`.

    Top row `+0.3755 -> +0.3501` (smaller), bottom row `-0.0192 -> -0.0339`
    (larger in magnitude). The two estimands disagree in *both* directions on
    the same walk, which is why the module reports both instead of quietly
    substituting one — the same reason it does off-family.
    """
    rows = cafe_steps()
    top, bottom = rows[W_RISK_ROWS[0]], rows[W_RISK_ROWS[1]]
    assert top.mean_step == pytest.approx(+0.3501, abs=5e-4)
    assert bottom.mean_step == pytest.approx(-0.0339, abs=5e-4)
    assert abs(top.mean_step) < abs(top.worst_step)
    assert abs(bottom.mean_step) > abs(bottom.worst_step)


def test_no_cafe_cell_bought_its_reading_by_freezing():
    """The precondition, asked of the cafe walk exactly as of the off-family
    one: a step taken by a robot that stopped moving is not a clearance win."""
    for w_risk in W_RISK_ROWS:
        for w_ped in W_PED_COLS:
            assert WALK_CAFE_6_REACHED[(w_risk, w_ped)] == 6
            assert len(WALK_CAFE_6[(w_risk, w_ped)]) == 6


def test_the_recorded_cafe_walk_is_re_derivable():
    """`walk_cells` regenerates the recorded table, checked on seed 0.

    `WALK_CAFE_6` is a pasted population like `WALK_20` before it, and a pasted
    population is only as good as its path back to the sim. One seed is walked
    live (4 runs, ~11 s) and matched against the recorded column, so a future
    edit that silently changes an arm, the temperature or the scene fails here
    instead of being absorbed into a constant nobody can re-derive.
    """
    clearances, reached = walk_cells(seeds=(0,))

    assert set(clearances) == set(WALK_CAFE_6)
    for cell, live in clearances.items():
        assert len(live) == 1
        assert live[0] == pytest.approx(WALK_CAFE_6[cell][0], abs=5e-5), cell
        assert reached[cell] == 1


def test_the_cafe_reading_uses_the_off_family_class_unchanged():
    """One estimand, not two wearing one name (D-047 applied to a statistic).

    If the cafe rows were read by a bespoke class, "cafe separates and
    off-family does not" would be uninterpretable — the difference could live
    in the reader. Both go through `PairedStep`, and the cafe rows carry the
    cafe scene so the object says which walk it came from.
    """
    for row in cafe_steps().values():
        assert isinstance(row, PairedStep)
        assert row.scene.endswith("cafe_obstacle_crossing_v0.yaml")
        assert row.n == 6
    assert set(cafe_steps()) == set(steps())

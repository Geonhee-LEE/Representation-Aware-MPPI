# SPDX-License-Identifier: BSD-3-Clause
"""`comparison_headroom.certify` — the λ guard's first enforcing consumer.

D-134→D-143 built the guard bottom-up: `lookup` grades a table,
`lam_window_index.resolve` picks the table from the weight. What it never had
was a caller that could *refuse*. Every published `Headroom` recorded its `lam`
and its `weight` as free fields and nothing checked they belonged together, so
the guard was available rather than load-bearing (STATE 2026-08-08 21:00).

Two things are pinned here and they pull in opposite directions:

  * the certification **refuses** the operating points the project actually
    published at — otherwise it is decoration; and
  * it **accepts** at least one — otherwise it is `guard_vacuity`'s complaint
    with the sign flipped, which is the failure this module shipped with (see
    `test_the_stem_fix_was_load_bearing`).

Analytic throughout: the clearances are arbitrary because a certification is a
function of `(scenario, controller, weight, λ)` and the calibration tables, not
of the runs. The arms' numbers are only there to make a legal `Headroom`.
"""

from __future__ import annotations

import pytest

from eval.mppi_sandbox import comparison_headroom as ch
from eval.mppi_sandbox import lam_window_index as lwi
from eval.mppi_sandbox import lam_window_key as lwk

MARGIN = 0.40
HEADON = "cafe_head_on_v0"
CROSSING = "cafe_obstacle_crossing_v0"

INDEX = lwi.build_index()
UNCAL = INDEX.uncalibrated_probe   # a weight no table is keyed at, derived


def _hr(scenario: str, weight: float, lam: float, a: str, b: str) -> ch.Headroom:
    """A `Headroom` that straddles the margin, so its own verdict is SEPARATED
    and cannot be confused with the certification's."""
    return ch.Headroom(
        scenario=scenario, weight=weight, lam=lam,
        a=ch.ArmSafety(arm=a, clearances=(0.10, 0.50), margin=MARGIN),
        b=ch.ArmSafety(arm=b, clearances=(0.50, 0.60), margin=MARGIN),
    )


# --------------------------------------------------------------------------
# It accepts, and it refuses. Both directions, or it is not a guard.
# --------------------------------------------------------------------------

def test_head_on_at_its_own_weight_and_rung_certifies():
    """`w = 10`, λ = 0.8 — D-132's operating point on the scene its band was
    measured on. Both arms record `[0.2, 0.4, 0.8]` (D-141), so the project's
    one significant claim sits at a temperature both arms were calibrated for.
    If this refused, the guard would be unusable rather than strict."""
    cert = ch.certify(_hr(HEADON, 10.0, 0.8, "stock_mppi", "risk_mppi"), INDEX)
    assert cert.verdict == ch.CERTIFIED
    assert cert.certified
    assert cert.uncertified == ()
    assert cert.sole_uncertified is None


def test_a_rung_outside_a_measured_window_is_off_window_not_missing():
    """λ = 3.2 on head_on: both arms have windows and neither contains it.
    `OFF_WINDOW` rather than `EMPTY_WINDOW` because the action differs — there
    *is* an admissible rung here, the comparison just was not run at one."""
    cert = ch.certify(_hr(HEADON, 10.0, 3.2, "stock_mppi", "risk_mppi"), INDEX)
    assert cert.verdict == ch.OFF_WINDOW
    assert not cert.certified
    assert set(cert.uncertified) == {"stock_mppi", "risk_mppi"}
    assert cert.sole_uncertified is None, "both arms refuse; nobody is sole"


def test_d133s_crossing_rung_names_the_arm_that_was_inadmissible():
    """The cell that cost something. D-133 walked `crossing`/risk at λ = 3.2,
    which **is** in that arm's recorded `[1.6, 3.2]` — while `stock_mppi`'s
    window is `[0.4, 0.8]` and excludes it. So the refusal belongs to exactly
    one arm, and it is the *baseline*: the comparison was taken at a
    temperature only the mechanism was calibrated for.

    A single boolean would print this identically to the both-arms case above,
    which is why `sole_uncertified` exists (the `scorable_band.sole_refuser`
    argument, one axis over)."""
    cert = ch.certify(_hr(CROSSING, 10.0, 3.2, "stock_mppi", "risk_mppi"), INDEX)
    assert cert.verdict == ch.OFF_WINDOW
    assert cert.sole_uncertified == "stock_mppi"
    assert cert.arms["risk_mppi"].usable == (1.6, 3.2), "the mechanism was in band"
    assert cert.arms["stock_mppi"].usable == (0.4, 0.8)


# --------------------------------------------------------------------------
# What it says about the two claims the project has actually published
# --------------------------------------------------------------------------

def test_the_gap_gates_operating_point_certifies_now_that_its_arm_is_measured():
    """D-124 published a `mean_clearance` delta for `gap_gated_mppi` on
    head_on, and until D-146 that controller appeared in **no** calibration
    table at any weight — the refusal was `NO_CELL` and it named the arm.

    D-146 paid it: 8 scenes × 8 rungs × 8 seeds at `--w-obs-soft 10`, the
    weight the claim was taken at, merged into the `w = 10` table as a third
    controller column. `gap_gated_mppi` on head_on is admissible at
    `[0.2, 0.4, 0.8]` — the same window as both other arms — so λ = 0.8 was a
    measured-admissible temperature for it and the A/B ran at an operating
    point both its arms were calibrated for.

    This does **not** make D-124's claim scorable. `sub_margin` still says the
    delta sits below the margin, and that is a different complaint from the one
    cleared here: this one was about the temperature being unmeasured, that one
    is about the effect being too small to report. The claim now fails for
    exactly one reason instead of two."""
    cert = ch.certify(_hr(HEADON, 10.0, 0.8, "stock_mppi", "gap_gated_mppi"), INDEX)
    assert cert.verdict == ch.CERTIFIED
    assert cert.uncertified == ()
    assert cert.arms["gap_gated_mppi"].usable == (0.2, 0.4, 0.8)


def test_the_risk_channels_separating_rung_now_certifies_at_its_own_weight():
    """`comparison_headroom`'s own docstring reports the project's first
    genuinely scorable mechanism result at `w = 100`, and until D-145 no table
    existed at that weight — the certification graded `NO_TABLE_AT_WEIGHT` and
    this test asserted the refusal as the standing price of STATE's "re-key
    `w = 100`" item.

    D-145 paid it: 8 scenes × 2 controllers × 8 rungs × 8 seeds at
    `--w-obs-soft 100`. Both head_on arms are admissible at `[0.2, 0.4, 0.8]`,
    so λ = 0.8 — the temperature the claim was actually walked at — is inside
    both windows **at the weight the claim was taken at**. The project's only
    scorable mechanism result certifies for the first time.

    The load-bearing part is that this could have gone the other way. D-142
    moved 6 of 14 arm-cells between `w = 10` and `w = 75`; had head_on/risk
    been one of them at 100, this test would now be recording a retraction."""
    cert = ch.certify(_hr(HEADON, 100.0, 0.8, "stock_mppi", "risk_mppi"), INDEX)
    assert cert.verdict == ch.CERTIFIED, str(cert)
    assert cert.certified
    assert cert.uncertified == ()
    assert cert.arms["stock_mppi"].usable == (0.2, 0.4, 0.8)
    assert cert.arms["risk_mppi"].usable == (0.2, 0.4, 0.8)


def test_an_uncalibrated_weight_still_refuses_by_name():
    """The guard must keep refusing somewhere, or paying for a weight bought a
    certification by making the check vacuous. It names every weight that now
    exists (D-044) — five, after this cycle bought `w = 250`.

    The probe weight is now **derived** (`INDEX.uncalibrated_probe`) rather than
    named. This assertion walked 100 → 150 → 250 as D-145, D-149 and this cycle
    bought the tables under it, going red and being hand-migrated each time;
    the previous version of this docstring called that "the intended shape".
    It was not — the invariant asserted here is *whatever is still uncalibrated
    refuses by name*, which is a claim about the complement of the index's
    domain, and a literal is only ever a snapshot of that complement. Buying a
    weight can no longer redden this test or quietly empty it."""
    cert = ch.certify(_hr(HEADON, UNCAL, 0.8, "stock_mppi", "risk_mppi"), INDEX)
    assert cert.verdict == lwi.NO_TABLE_AT_WEIGHT
    assert cert.available == INDEX.weights == (10.0, 75.0, 100.0, 150.0, 250.0)
    assert "calibrated_at=10, 75, 100, 150, 250" in str(cert)


def test_an_empty_window_is_not_reported_as_a_wrong_rung():
    """`cut_in` is admissible at no temperature at all (Q-035). That must not
    grade `OFF_WINDOW`, which would tell the caller to go find a better λ that
    does not exist."""
    cert = ch.certify(_hr("cafe_cut_in_v0", 10.0, 0.8, "stock_mppi", "risk_mppi"), INDEX)
    assert cert.verdict == lwk.EMPTY_WINDOW
    assert cert.verdict != ch.OFF_WINDOW


# --------------------------------------------------------------------------
# The enforcing entry point
# --------------------------------------------------------------------------

def test_assert_certified_returns_on_a_good_point_and_raises_on_a_bad_one():
    good = _hr(HEADON, 10.0, 0.8, "stock_mppi", "risk_mppi")
    assert ch.assert_certified(good, INDEX).certified

    with pytest.raises(ch.UncertifiedOperatingPoint) as exc:
        ch.assert_certified(_hr(HEADON, UNCAL, 0.8, "stock_mppi", "risk_mppi"), INDEX)
    # the exception carries the actionable half, not just the word
    assert "NO_TABLE_AT_WEIGHT" in str(exc.value)
    assert "calibrated_at=10, 75, 100, 150, 250" in str(exc.value)


def test_certification_is_orthogonal_to_the_headroom_verdict():
    """A comparison can be scorable-but-uncertified, and the two verdicts must
    not be collapsed: one asks whether the margin could have moved, the other
    whether the temperature was ever measured. The `w = 250` row is `SEPARATED`
    on its clearances and refused on its calibration."""
    row = _hr(HEADON, UNCAL, 0.8, "stock_mppi", "risk_mppi")
    assert row.verdict == ch.SEPARATED and row.scorable
    assert not ch.certify(row, INDEX).certified


# --------------------------------------------------------------------------
# Non-vacuity — the bug this module shipped with
# --------------------------------------------------------------------------

def test_the_stem_fix_was_load_bearing():
    """`Headroom.scenario` records `cafe_head_on_v0`; the tables key on
    `cafe_head_on_v0.yaml`. Under the old basename-only match the guard's first
    real consumer graded **every** row `NO_CELL` — refusing everything, which
    reads as maximal strictness and checks nothing.

    Pinned as an equivalence rather than as "the extensionless form works", so
    a future normalisation that drops one spelling breaks here."""
    spellings = ("cafe_head_on_v0", "cafe_head_on_v0.yaml",
                 "eval/scenarios/cafe_head_on_v0.yaml")
    verdicts = {ch.certify(_hr(s, 10.0, 0.8, "stock_mppi", "risk_mppi"),
                           INDEX).verdict for s in spellings}
    assert verdicts == {ch.CERTIFIED}


def test_every_verdict_is_reachable_over_the_shipped_tables():
    """All five, from real rows. A verdict no artifact can produce is prose."""
    cases = [
        (_hr(HEADON, 10.0, 0.8, "stock_mppi", "risk_mppi"), ch.CERTIFIED),
        (_hr(HEADON, 10.0, 3.2, "stock_mppi", "risk_mppi"), ch.OFF_WINDOW),
        (_hr(HEADON, UNCAL, 0.8, "stock_mppi", "risk_mppi"), lwi.NO_TABLE_AT_WEIGHT),
        (_hr(HEADON, 10.0, 0.8, "stock_mppi", "cbf_mppi"), lwk.NO_CELL),
        (_hr("cafe_cut_in_v0", 10.0, 0.8, "stock_mppi", "risk_mppi"), lwk.EMPTY_WINDOW),
    ]
    seen = {ch.certify(row, INDEX).verdict for row, _ in cases}
    assert seen == {v for _, v in cases}
    assert seen == ch.UNCERTIFIED | {ch.CERTIFIED}, \
        "the reachable set and the declared set must be the same set"


def test_a_refusal_outranks_a_wrong_rung_when_the_arms_disagree_in_kind():
    """One arm off-window, the other with no cell: the verdict must be the one
    naming the larger missing thing, since `NO_CELL` needs a calibration run
    and `OFF_WINDOW` only needs a different λ.

    `cbf_mppi` carries the no-cell side since D-146 calibrated `gap_gated_mppi`
    — it is registered in `controllers.REGISTRY` and measured in no table at
    any weight, which is the same standing `gap_gated_mppi` had until this
    cycle paid for it."""
    cert = ch.certify(_hr(HEADON, 10.0, 3.2, "stock_mppi", "cbf_mppi"), INDEX)
    assert cert.verdict == lwk.NO_CELL

# SPDX-License-Identifier: BSD-3-Clause
"""`headline_rescope` — the two refusals, the reproduction clause, the verdict.

Synthetic cells throughout, for `test_freeze_weight`'s stated reason: whether a
published headline survives a scope change is arithmetic over cells, and the
one measured fact this module rests on — that the `lam = 0.1` ablation does not
exceed pre-arrival — is a `freeze_weight.sweep` result, pinned there and quoted
in D-253 rather than re-simulated here at 120 runs per suite.

The transcription tests are the exception and they are cheap: they read
`CLAIMS` against `freeze_weight`'s own constants, so a claim recorded at a
temperature the module does not define fails at collection rather than in a
cycle's prose six weeks later.
"""

from __future__ import annotations

import pytest

from eval.mppi_sandbox import freeze_weight as fw
from eval.mppi_sandbox import headline_rescope as hr

LIMIT = 2.0


def cell(w: float, before, whole, clearance=None, reached=None):
    """A `WeightCell` carrying **both** scopes explicitly.

    `freeze_weight`'s own helper defaults `longest_before` to `longest`, which
    is exactly the identity these tests must be able to break.
    """
    before = tuple(float(x) for x in before)
    whole = tuple(float(x) for x in whole)
    n = len(whole)
    return fw.WeightCell(
        w_freeze=float(w),
        longest=whole,
        clearance=tuple(float(c) for c in (clearance if clearance is not None
                                           else [0.9] * n)),
        reached=tuple(reached if reached is not None else [True] * n),
        limit=LIMIT,
        longest_before=before,
        arrival=tuple([1.0] * n),
    )


#: The measured shape at `lam = 0.1`: whole-scope exceedance reproduces D-243's
#: published column, arrival-scoped exceedance is zero everywhere below 1e5.
CONTAMINATED = (
    cell(0.0, [0.3, 0.3, 0.3], [3.0, 3.0, 0.5]),   # whole 2/3, before 0/3
    cell(1e2, [0.4, 0.4, 0.4], [3.0, 3.0, 3.0]),   # whole 3/3, before 0/3
    cell(1e3, [0.3, 0.3, 0.3], [3.0, 0.5, 0.5]),   # whole 1/3, before 0/3
    cell(1e4, [0.4, 0.4, 0.4], [0.5, 0.5, 0.5]),   # whole 0/3, before 0/3
    cell(1e5, [2.4, 2.4, 0.3], [3.0, 3.0, 3.0],
         clearance=[0.84, 0.84, 0.84]),            # whole 3/3, before 2/3
)

D243 = hr.CLAIMS[0]


# --- the refusals, which are the point of the module ------------------------

def test_a_different_temperature_is_refused_not_graded():
    """D-250's error, mechanised: a lam=0.8 reading cannot grade a lam=0.1 claim."""
    assert hr.regrade(D243, CONTAMINATED,
                      lam=fw.PAIRED_LAM, n=3) == hr.NOT_COMPARABLE_LAM


def test_the_refusal_outranks_the_verdict_it_would_have_returned():
    """The cells say VOID; the temperature says the cells are not evidence.

    This is what makes the refusal load-bearing rather than cosmetic — it fires
    on cells that would otherwise have produced the *same* answer D-250 reached,
    so the module declines even when declining costs it the right conclusion.
    """
    assert hr.regrade(D243, CONTAMINATED, lam=fw.D243_LAM,
                      n=3) == hr.VOID_POST_ARRIVAL
    assert hr.regrade(D243, CONTAMINATED, lam=fw.PAIRED_LAM,
                      n=3) == hr.NOT_COMPARABLE_LAM


def test_a_different_seed_count_is_refused():
    assert hr.regrade(D243, CONTAMINATED,
                      lam=fw.D243_LAM, n=12) == hr.NOT_COMPARABLE_N


def test_lam_is_checked_before_n():
    """Both wrong reports the temperature — the axis D-244 convicted."""
    assert hr.regrade(D243, CONTAMINATED,
                      lam=fw.PAIRED_LAM, n=99) == hr.NOT_COMPARABLE_LAM


# --- the reproduction clause ------------------------------------------------

def test_cells_off_the_claims_curve_cannot_grade_it():
    """A `before` column is only readable if `whole` still matches the record."""
    drifted = (cell(0.0, [0.3], [0.5]),) + CONTAMINATED[1:]
    assert hr.regrade(D243, drifted,
                      lam=fw.D243_LAM, n=3) == hr.NOT_REPRODUCED


def test_reproduction_reads_the_whole_scope_not_the_graded_one():
    """The published column is whole-scope; grading it on `before` inverts it."""
    assert hr.reproduces(D243, CONTAMINATED)
    assert not all(c.n_exceed_in(fw.SCOPE_BEFORE) == q
                   for c, q in zip(CONTAMINATED, D243.quoted) if q is not None)


def exceeding(w: float, k: int, n: int = 12):
    """A cell whose **whole** column exceeds on exactly `k` of `n` seeds.

    `before` is clean throughout — these fixtures exist to exercise the
    reproduction clause, which reads only the whole scope.
    """
    whole = [3.0] * k + [0.5] * (n - k)
    return cell(w, [0.3] * n, whole)


def test_an_unpublished_grid_point_is_a_hole_not_a_failure():
    """D-244 printed 3e3 and 1e4 but not 1e3 — the hole must not convict."""
    d244 = hr.CLAIMS[1]
    assert d244.quoted[2] is None
    cells = (exceeding(0.0, 6), exceeding(1e2, 6),
             exceeding(1e3, 3),           # never published; must not convict
             exceeding(3e3, 0), exceeding(1e4, 0))
    assert hr.reproduces(d244, cells)


def test_the_hole_is_the_only_point_exempt():
    """Same fixture, one published cell moved — that one still convicts."""
    d244 = hr.CLAIMS[1]
    cells = (exceeding(0.0, 5), exceeding(1e2, 6),   # ablation 6 -> 5
             exceeding(1e3, 3), exceeding(3e3, 0), exceeding(1e4, 0))
    assert not hr.reproduces(d244, cells)


def test_a_weight_absent_from_the_re_read_is_skipped():
    """A narrower sweep grades the points it took, not the ones it did not."""
    assert hr.reproduces(D243, CONTAMINATED[:4])


# --- the verdict ------------------------------------------------------------

def test_a_headline_survives_when_the_ablation_still_fails_pre_arrival():
    """The other direction, so VOID is a reading and not a constant."""
    genuine = (
        cell(0.0, [3.0, 3.0, 3.0], [3.0, 3.0, 0.5]),   # before 3/3 — real freeze
        cell(1e2, [3.0, 3.0, 3.0], [3.0, 3.0, 3.0]),
        cell(1e3, [3.0, 3.0, 0.5], [3.0, 0.5, 0.5]),
        cell(1e4, [0.5, 0.5, 0.5], [0.5, 0.5, 0.5],
             clearance=[0.95, 0.95, 0.95]),
        cell(1e5, [3.0, 3.0, 3.0], [3.0, 3.0, 3.0]),
    )
    assert hr.reproduces(D243, genuine)
    assert hr.regrade(D243, genuine, lam=fw.D243_LAM, n=3) == hr.SURVIVES


def test_void_is_decided_on_the_ablation_not_on_the_optimum():
    """All four headlines presume the ablation fails; that is the graded clause."""
    assert fw.verdict(CONTAMINATED, scope=fw.SCOPE_BEFORE) == "NO_FREEZE_TO_PRICE"
    assert hr.regrade(D243, CONTAMINATED,
                      lam=fw.D243_LAM, n=3) == hr.VOID_POST_ARRIVAL


# --- the transcription ------------------------------------------------------

def test_every_claim_sits_at_a_temperature_the_module_names():
    """A claim at an unnamed lam is untraceable to the sweep that took it."""
    for h in hr.CLAIMS:
        assert h.lam in (fw.D243_LAM, fw.PAIRED_LAM), h.decision


def test_the_claims_split_across_the_two_temperatures():
    """If they did not, the refusal would never fire and would rot untested."""
    lams = {h.lam for h in hr.CLAIMS}
    assert lams == {fw.D243_LAM, fw.PAIRED_LAM}


def test_claims_at_selects_only_the_gradeable_headlines():
    """The lam=0.1 re-read this cycle took is entitled to D-243 and D-244 only."""
    assert tuple(h.decision for h in hr.claims_at(fw.D243_LAM, 3)) == ("D-243",)
    assert tuple(h.decision for h in hr.claims_at(fw.D243_LAM, 12)) == ("D-244",)
    assert tuple(h.decision
                 for h in hr.claims_at(fw.PAIRED_LAM, 12)) == ("D-245", "D-246")


def test_every_published_column_is_denominated_against_its_ablation():
    with pytest.raises(ValueError, match="must be the ablation"):
        hr.Headline(decision="D-000", claim="x", lam=fw.D243_LAM, n=3,
                    weights=(1e4,), quoted=(0,))


def test_a_column_must_align_to_its_grid():
    with pytest.raises(ValueError, match="must align to the grid"):
        hr.Headline(decision="D-000", claim="x", lam=fw.D243_LAM, n=3,
                    weights=(0.0, 1e4), quoted=(0,))


def test_all_four_headlines_are_recorded_in_the_whole_scope():
    """The arrival-scoped reading did not exist until D-250 — none can be `before`."""
    assert {h.scope for h in hr.CLAIMS} == {fw.SCOPE_WHOLE}

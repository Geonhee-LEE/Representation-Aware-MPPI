"""Was the published band's censoring the margin's fault, or the arms'?

Two of these tests carry the module's weight rather than checking a field.
`test_breakpoints_are_exhaustive` is the one that entitles the two
`NO_TWO_SIDED_MARGIN` answers: "no margin makes this rung two-sided" is a claim
over an uncountable set, and the module answers it by enumerating 64 recorded
clearances, so the step-function argument gets probed against a dense grid
instead of believed. `test_two_sided_margins_are_contiguous` does the same for
:attr:`MarginSweep.window`, which is reported as a span and would be a lie if
the set had holes.
"""

import pytest

from eval.mppi_sandbox.comparison_headroom import ArmSafety, Headroom
from eval.mppi_sandbox.margin_sweep import (
    MULTI_RUNG_REACHABLE,
    NO_RECORDED_SEPARATION,
    NO_TWO_SIDED_MARGIN,
    NO_TWO_SIDED_RUNG,
    SINGLE_RUNG_CEILING,
    TWO_SIDED_AND_HELD,
    TWO_SIDED_BUT_LOST,
    BandSweep,
    MarginSweep,
    breakpoints,
    published_sweep,
    regrade,
)
from eval.mppi_sandbox.separation_reproduction import (
    NO_SEPARATION_TO_REPRODUCE,
    REPRODUCED,
    SIGN_REVERSED,
    UNCENSORED,
    Reproduction,
    SeedBlock,
    w75_reproduction,
    w100_reproduction,
    w150_reproduction,
    w250_reproduction,
)
from eval.mppi_sandbox.scorable_band import (
    PUBLISHED_ARMS,
    PUBLISHED_LAM,
    PUBLISHED_MARGIN,
    PUBLISHED_SCENARIO,
)


def _sweep(reproduction):
    return MarginSweep(reproduction=reproduction)


# --- the measurement -----------------------------------------------------


def test_published_margin_makes_no_rung_two_sided():
    """The starting point: D-157's 0/4, restated as a coverage at one margin."""
    assert published_sweep().coverage(PUBLISHED_MARGIN) == ()


@pytest.mark.parametrize("reproduction,expected", [
    (w75_reproduction(), NO_TWO_SIDED_MARGIN),
    (w100_reproduction(), NO_TWO_SIDED_MARGIN),
    (w150_reproduction(), TWO_SIDED_AND_HELD),
    (w250_reproduction(), TWO_SIDED_BUT_LOST),
])
def test_per_rung_verdicts(reproduction, expected):
    """Three of the four verdicts are reachable over shipped rungs.

    Non-vacuity that costs nothing to state and would have caught a
    one-constant implementation: a `verdict` hard-coded to any single value
    fails at least two of these four rows.
    """
    assert _sweep(reproduction).verdict == expected


def test_the_two_censored_rungs_are_the_ones_whose_arms_barely_overlap():
    """*Why* two rungs admit no margin — and that the reason is not sufficient.

    The pooled arm-range overlap at `w ∈ {75, 100}` is under a centimetre while
    the two-sided rungs clear 20 cm. But a positive overlap does not buy a
    two-sided margin — two-sidedness is required in each block of 16, not
    pooled over 32 — so the assertion is an ordering, not a threshold.
    """
    narrow = [_sweep(r) for r in (w75_reproduction(), w100_reproduction())]
    wide = [_sweep(r) for r in (w150_reproduction(), w250_reproduction())]

    for s in narrow:
        assert 0.0 < s.arm_overlap < 0.01, s
        assert s.two_sided == ()
    for s in wide:
        assert s.arm_overlap > 0.2, s
        assert s.two_sided

    assert max(s.arm_overlap for s in narrow) < min(s.arm_overlap for s in wide)


def test_w250_reversal_does_not_survive_a_two_sided_reading():
    """The finding: `SIGN_REVERSED` at 0.40 m, `REPRODUCED` at all 23 others.

    Both halves are asserted. That the recorded verdict is lost is the weak
    claim — a rung could lose `SIGN_REVERSED` by going `NOT_REPRODUCED`, which
    would say only that the margin was load-bearing. The strong claim is *what
    replaces it*: every two-sided margin reads `REPRODUCED`, so the 32 runs
    agree in the mechanism's direction once both arms have room.
    """
    sweep = _sweep(w250_reproduction())

    assert sweep.recorded_verdict == SIGN_REVERSED
    assert sweep.held == ()
    assert len(sweep.lost) == 23
    assert set(sweep.regraded_verdicts) == {REPRODUCED}


def test_w250_reversal_at_the_published_margin_rests_on_one_run_per_block():
    """Why that rung was the fragile one — the sign is two runs out of 32.

    Guards the interpretation, not the arithmetic: without this, "the reversal
    is a tail artifact" is an assertion in a docstring. With it, the claim is
    that each block's separation is a single run wide, so the *sign* of the
    pooled comparison is decided by two runs.
    """
    reproduction = w250_reproduction()
    stock, risk = PUBLISHED_ARMS

    for block in (reproduction.reference, reproduction.replication):
        rates = {block.headroom.a.arm: block.headroom.a.unsafe_rate,
                 block.headroom.b.arm: block.headroom.b.unsafe_rate}
        assert abs(rates[stock] - rates[risk]) == pytest.approx(1 / 16), block

    assert reproduction.reference.headroom.a.unsafe_rate == 0.0  # stock: FLOOR


# --- the claims the answers rest on --------------------------------------


@pytest.mark.parametrize("reproduction", [
    w75_reproduction(), w100_reproduction(),
    w150_reproduction(), w250_reproduction(),
])
def test_breakpoints_are_exhaustive(reproduction):
    """No two-sided margin hides between the recorded clearances.

    `two_sided` enumerates 62–64 recorded clearances and, at two rungs, returns
    nothing — a claim about every positive real, made from a finite list. The
    justification is that the unsafe count `#{c : c < m}` only changes as `m`
    crosses a recorded clearance, so each interval between consecutive ones is
    represented by its upper endpoint. This walks a dense grid across the full
    clearance range and asserts every uncensored margin it finds was already in
    the enumerated set — which is what the argument predicts and what the two
    `NO_TWO_SIDED_MARGIN` verdicts require.
    """
    enumerated = set(MarginSweep(reproduction=reproduction).two_sided)
    bps = breakpoints(reproduction)
    lo, hi = bps[0], bps[-1]

    steps = 2000
    found_off_grid = []
    for i in range(steps + 1):
        m = lo + (hi - lo) * i / steps
        if m <= 0.0:
            continue
        if regrade(reproduction, m).censoring == UNCENSORED:
            if m not in enumerated:
                # Legal only if it shares an interval with an enumerated
                # breakpoint — i.e. the next recorded clearance at or above m.
                nxt = min((c for c in bps if c >= m), default=None)
                if nxt not in enumerated:
                    found_off_grid.append(m)

    assert not found_off_grid, (
        f"w={reproduction.reference.headroom.weight:g}: dense probe found "
        f"{len(found_off_grid)} uncensored margins outside the enumerated set, "
        f"first {found_off_grid[0]:.6f} — the breakpoint enumeration is not "
        "exhaustive and every 'no two-sided margin' answer is unfounded"
    )


@pytest.mark.parametrize("reproduction", [
    w150_reproduction(), w250_reproduction(),
])
def test_two_sided_margins_are_contiguous(reproduction):
    """`window` is the whole set, not just its extremes.

    An arm's unsafe rate is monotone in the margin, so the margins where it is
    interior form one run and the four-way intersection is a run too. If this
    ever fails, `window` is reporting a span with holes in it and the honest
    field would be `two_sided` alone.
    """
    sweep = MarginSweep(reproduction=reproduction)
    bps = breakpoints(reproduction)
    idx = [i for i, m in enumerate(bps) if m in set(sweep.two_sided)]

    assert idx == list(range(idx[0], idx[-1] + 1))
    assert sweep.window == (bps[idx[0]], bps[idx[-1]])


def test_arm_unsafe_rate_is_monotone_in_the_margin():
    """The property both claims above are built on, asserted directly."""
    arm = w150_reproduction().reference.headroom.a
    rates = [
        ArmSafety(arm=arm.arm, clearances=arm.clearances, margin=m).unsafe_rate
        for m in sorted(set(arm.clearances))
    ]
    assert rates == sorted(rates)


# --- the band-level reading ----------------------------------------------


def test_band_ceiling_is_one_rung():
    """Arm coverage over the published band is capped at 1/4 by the data.

    Not "we measured 0/4" — that is a fact about the margin that was used. This
    is the stronger, and worse, statement: `Headroom` refuses two arms graded
    against different margins, so the band is scored at one threshold, and no
    threshold makes two of these four rungs two-sided at once.
    """
    band = published_sweep()

    assert band.verdict == SINGLE_RUNG_CEILING
    assert band.ceiling == 1
    assert band.best_margins
    for m in band.best_margins:
        assert len(band.coverage(m)) == 1


def test_the_two_windows_are_disjoint():
    """Why the ceiling is 1 and not 2 — the only two candidates do not meet."""
    w150 = MarginSweep(reproduction=w150_reproduction()).window
    w250 = MarginSweep(reproduction=w250_reproduction()).window

    assert w150[1] < w250[0]


def test_band_refuses_a_repeated_weight():
    """Two readings of one rung would double-count its coverage."""
    with pytest.raises(ValueError, match="repeated weights"):
        BandSweep(sweeps=(
            MarginSweep(reproduction=w150_reproduction()),
            MarginSweep(reproduction=w150_reproduction()),
        ))


# --- the corners the shipped rungs do not reach --------------------------


def _synthetic(stock_ref, risk_ref, stock_rep, risk_rep, margin=PUBLISHED_MARGIN):
    stock, risk = PUBLISHED_ARMS

    def block(lo, s, r):
        return SeedBlock(
            seeds=tuple(range(lo, lo + len(s))),
            headroom=Headroom(
                scenario=PUBLISHED_SCENARIO, weight=999.0, lam=PUBLISHED_LAM,
                a=ArmSafety(arm=stock, clearances=tuple(s), margin=margin),
                b=ArmSafety(arm=risk, clearances=tuple(r), margin=margin),
            ),
        )

    return Reproduction(reference=block(0, stock_ref, risk_ref),
                        replication=block(len(stock_ref), stock_rep, risk_rep))


def test_no_recorded_separation_is_reachable():
    """A tied reference block has no verdict for a re-grading to preserve.

    The empty-denominator corner, and the reason it is keyed on
    `NO_SEPARATION_TO_REPRODUCE` rather than on "not `REPRODUCED`":
    `SIGN_REVERSED` must *not* land here, or `w = 250` — the one rung where the
    margin question changes the answer — would have been routed away from it.
    """
    tied = _synthetic([0.5, 0.3], [0.5, 0.3], [0.5, 0.3], [0.5, 0.3])

    assert tied.verdict == NO_SEPARATION_TO_REPRODUCE
    assert MarginSweep(reproduction=tied).verdict == NO_RECORDED_SEPARATION
    assert MarginSweep(reproduction=w250_reproduction()).verdict != \
        NO_RECORDED_SEPARATION


def test_no_two_sided_rung_is_reachable():
    """A band all of whose rungs are unreachable reads `NO_TWO_SIDED_RUNG`."""
    band = BandSweep(sweeps=(
        MarginSweep(reproduction=w75_reproduction()),
        MarginSweep(reproduction=w100_reproduction()),
    ))

    assert band.verdict == NO_TWO_SIDED_RUNG
    assert band.ceiling == 0
    assert band.best_margins == ()


def test_multi_rung_reachable_is_reachable():
    """Two rungs sharing a two-sided margin — the state the band is *not* in.

    Without this, `SINGLE_RUNG_CEILING` could be returned by an implementation
    that never counts past one, and the band's ceiling would look like a
    measurement when it was a bug.
    """
    overlapping = BandSweep(sweeps=(
        MarginSweep(reproduction=w150_reproduction()),
        MarginSweep(reproduction=_synthetic(
            [0.41, 0.44], [0.43, 0.45], [0.42, 0.45], [0.43, 0.46])),
    ))

    assert overlapping.verdict == MULTI_RUNG_REACHABLE
    assert overlapping.ceiling == 2


# --- re-grading preserves the runs ---------------------------------------


def test_regrade_changes_only_the_margin():
    """A sweep that re-simulated, or dropped runs, would be a different study."""
    original = w150_reproduction()
    moved = regrade(original, 0.55)

    assert moved.seeds == original.seeds
    for before, after in ((original.reference, moved.reference),
                          (original.replication, moved.replication)):
        assert after.headroom.a.clearances == before.headroom.a.clearances
        assert after.headroom.b.clearances == before.headroom.b.clearances
    assert moved.reference.headroom.margin == 0.55


def test_regrade_refuses_an_unscorable_margin():
    """`Headroom` validates at construction; the sweep must not reach past it."""
    with pytest.raises(ValueError, match="not scorable"):
        regrade(w150_reproduction(), 0.0)

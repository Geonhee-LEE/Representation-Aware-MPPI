"""Does a threshold derived from the recorded clearances host the comparison?

Three tests carry this module rather than checking a field.
`test_no_threshold_is_shared_by_two_rungs` is the cross-scene claim and the one
that closes the successor question — it is proved by pairwise disjointness of
the three windows, not by trusting the intersection helper that reports it.
`test_windowless_rungs_do_not_widen_the_shared_window` pins the one modelling
choice in `shared_window` that could silently invert the headline. And
`test_inert_windows_lie_above_the_declared_margin` is the caveat test: the two
positive rungs are the only good news in the file, and they are only good news
about clearance ordering.
"""

import pytest

from eval.mppi_sandbox.derived_margin import (
    ABOVE_WINDOW,
    BELOW_WINDOW,
    INSIDE_WINDOW,
    MULTI_SCENE_STABLE,
    NO_STABLE_RUNG,
    NO_WINDOW,
    SINGLE_SCENE_STABLE,
    DerivedMarginCensus,
    RungDerivation,
    census,
    walked_rungs,
)
from eval.mppi_sandbox.margin_sweep import MarginSweep
from eval.mppi_sandbox.scene_transplant import (
    MARGIN_DECIDES_VERDICT,
    MARGIN_INERT,
    NO_TWO_SIDED_TO_SPREAD,
)
from eval.mppi_sandbox.separation_reproduction import REPRODUCED, reproduction_at

ARMS = ("stock_mppi", "risk_mppi")


def _sweep(stock, risk, margin, scenario="synthetic.yaml"):
    return MarginSweep(reproduction=reproduction_at(
        scenario, 0.8, margin, 250.0, ARMS,
        {"stock_mppi": tuple(stock), "risk_mppi": tuple(risk)}, 16))


def test_the_population_is_the_three_eligible_scenes():
    """D-159 screened the 8-scene matrix down to 3 eligible scenes; the census
    must cover all three, or its denominator is a different question's."""
    c = census()
    assert set(c.scenes) == {
        "cafe_head_on_v0.yaml",
        "cafe_convoy_v0.yaml",
        "cafe_obstacle_crossing_v0.yaml",
    }
    assert len(c.rungs) == 6


@pytest.mark.parametrize("scenario,weight,decides", [
    ("cafe_head_on_v0.yaml", 75.0, NO_TWO_SIDED_TO_SPREAD),
    ("cafe_head_on_v0.yaml", 100.0, NO_TWO_SIDED_TO_SPREAD),
    ("cafe_head_on_v0.yaml", 150.0, MARGIN_INERT),
    ("cafe_head_on_v0.yaml", 250.0, MARGIN_INERT),
    ("cafe_convoy_v0.yaml", 75.0, NO_TWO_SIDED_TO_SPREAD),
    ("cafe_obstacle_crossing_v0.yaml", 250.0, MARGIN_DECIDES_VERDICT),
])
def test_each_rung_keeps_its_measured_verdict(scenario, weight, decides):
    (rung,) = [r for r in walked_rungs()
               if r.scenario == scenario and r.weight == weight]
    assert rung.decides == decides


def test_scene_coverage_is_one_of_three_and_it_is_the_published_scene():
    """The headline. Two scenes were walked specifically to widen the evidence
    base past the published band; between them they contribute zero rungs with
    a margin-independent verdict, at any threshold their own runs express."""
    c = census()
    assert c.verdict == SINGLE_SCENE_STABLE
    assert c.scene_coverage == (1, 3)
    assert c.rung_coverage == (2, 6)
    assert c.stable_scenes == ("cafe_head_on_v0.yaml",)


def test_the_two_stable_rungs_both_read_reproduced():
    """Both margin-independent verdicts point in the mechanism's direction.
    Pinned because `MARGIN_INERT` only says the verdict does not move — a rung
    could be stably `NOT_REPRODUCED` and the flag would read the same."""
    c = census()
    assert [r.stable_verdict for r in c.stable] == [REPRODUCED, REPRODUCED]
    assert all(r.stable_verdict is None for r in c.deciding + c.windowless)


def test_no_threshold_is_shared_by_two_rungs():
    """The cross-scene ceiling, proved by pairwise disjointness rather than by
    the helper that reports it.

    `Headroom` grades one margin at a time, so a result quoted over the
    population needs a threshold the population shares. There is none, and the
    reason is structural: a margin is a length in metres and clearance scale is
    a scene property, so `head_on`'s windows (~0.42-0.59 m) cannot meet
    `crossing`'s (~1.0 m).
    """
    windows = [r.window for r in walked_rungs() if r.window is not None]
    assert len(windows) == 3
    for i, a in enumerate(windows):
        for b in windows[i + 1:]:
            assert a[1] < b[0] or b[1] < a[0], (a, b)
    assert census().shared_window is None


def test_windowless_rungs_do_not_widen_the_shared_window():
    """The one modelling choice in `shared_window`, pinned in the direction
    that would invert the headline.

    A rung with no two-sided margin is the *strongest* evidence against a
    shared threshold. If it were folded into the intersection as vacuously
    compatible, a population of one windowed rung plus five windowless ones
    would report a shared window — i.e. the more scenes that admit no
    threshold at all, the more confidently the census would name one.
    """
    windowed = RungDerivation("a.yaml", _sweep(
        [0.30 + 0.01 * (i % 16) for i in range(32)],
        [0.32 + 0.01 * (i % 16) for i in range(32)], 0.35))
    assert windowed.window is not None

    disjoint = RungDerivation("b.yaml", _sweep(
        [0.10 + 0.001 * (i % 16) for i in range(32)],
        [0.90 + 0.001 * (i % 16) for i in range(32)], 0.35))
    assert disjoint.window is None

    assert DerivedMarginCensus((windowed,)).shared_window == windowed.window
    # Adding a rung that admits no threshold must not leave the window intact.
    assert DerivedMarginCensus((windowed, disjoint)).shared_window is None


def test_every_declared_margin_with_a_window_sits_below_it():
    """One direction, no exceptions: the declared thresholds are not
    mis-centred inside their own two-sided spans, they are all outside and all
    on the permissive side."""
    c = census()
    assert c.declared_placements == {NO_WINDOW: 3, BELOW_WINDOW: 3}
    assert INSIDE_WINDOW not in c.declared_placements
    assert ABOVE_WINDOW not in c.declared_placements


def test_inert_windows_are_asymmetric_not_majority_unsafe():
    """Why the two positive rungs are not a safety result — and why D-158's
    stated reason for the same caveat is wrong on its own numbers.

    `margin_sweep`'s docstring says that at `w = 250`'s window "most runs of
    *both* arms count as unsafe". Measured, the arms are sharply asymmetric and
    the risk arm is nowhere near a majority at either rung. Two-sidedness needs
    both arms merely *interior*, which is much weaker. The caveat survives —
    the threshold is stricter than the scene's declared requirement and so
    means nothing about safety — but it rests on the threshold being
    undeclared, not on the runs being mostly unsafe.
    """
    seen = {}
    for r in census().stable:
        lo, _ = r.window
        assert lo > r.declared_margin, "window must sit above the declared margin"
        pooled = r.sweep.reproduction.pooled
        counts = {arm.arm: sum(1 for c in arm.clearances if c < lo)
                  for arm in (pooled.a, pooled.b)}
        assert all(0 < n < 32 for n in counts.values()), counts  # interior
        seen[r.weight] = counts

    assert seen == {150.0: {"stock_mppi": 19, "risk_mppi": 2},
                    250.0: {"stock_mppi": 11, "risk_mppi": 3}}
    # The claim D-158 makes, stated as the falsehood it is.
    assert all(c["risk_mppi"] * 2 < 32 for c in seen.values())


def test_placement_and_verdict_constants_are_all_reachable():
    """`INSIDE_WINDOW`, `ABOVE_WINDOW`, `MULTI_SCENE_STABLE` and
    `NO_STABLE_RUNG` are unreached by the shipped population, so they are
    proved reachable synthetically. A constant nothing can return is a branch
    that reads as measured-absent when it is actually dead (D-107)."""
    stock = [0.30 + 0.01 * (i % 16) for i in range(32)]
    risk = [0.32 + 0.01 * (i % 16) for i in range(32)]

    inside = RungDerivation("a.yaml", _sweep(stock, risk, 0.35))
    assert inside.declared_placement == INSIDE_WINDOW
    above = RungDerivation("a.yaml", _sweep(stock, risk, 5.0))
    assert above.declared_placement == ABOVE_WINDOW

    other = RungDerivation("b.yaml", _sweep(stock, risk, 0.35))
    assert DerivedMarginCensus((inside, other)).verdict == MULTI_SCENE_STABLE
    assert DerivedMarginCensus(()).verdict == NO_STABLE_RUNG


def test_the_shipped_inert_witness_is_no_longer_synthetic():
    """`test_margin_decides_covers_its_vacuous_and_inert_corners` proves
    `MARGIN_INERT` with a hand-built sweep, on the stated grounds that no
    shipped scene produces it. Scoped to `scene_transplant`'s two scenes that
    was true; over the eligible population it is not — `head_on`'s two rungs
    are shipped, measured witnesses. Pinned so the synthetic one is known to be
    a convenience rather than the only reachable instance."""
    assert [(r.scenario, r.weight) for r in census().stable] == [
        ("cafe_head_on_v0.yaml", 150.0),
        ("cafe_head_on_v0.yaml", 250.0),
    ]

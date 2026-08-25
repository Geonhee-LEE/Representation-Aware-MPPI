"""Does the band's protocol move to a second scene, and what does it find?

Two tests carry the module's weight. `test_no_threshold_is_two_sided_anywhere`
entitles the strongest claim here — that convoy admits no two-sided margin at
*any* value — by probing a dense grid over the recorded range rather than
trusting the disjointness arithmetic. `test_both_scenes_are_none_two_sided_from
_opposite_boundaries` is the finding itself, and it is written as a comparison
of two scenes so that a future change collapsing `censoring_direction` back
into `SeedBlock.censoring` fails here rather than silently merging two
different failure modes.

Nothing in this file runs a simulation; the clearances are constants.
"""

import pytest

from eval.mppi_sandbox.comparison_headroom import (
    NO_HEADROOM_SAFE,
    NO_HEADROOM_UNSAFE,
    ArmSafety,
    Headroom,
)
from eval.mppi_sandbox.margin_sweep import NO_RECORDED_SEPARATION
from eval.mppi_sandbox.scene_transplant import (
    LAM_NOT_ADMISSIBLE,
    NO_ADMISSIBLE_LAM,
    NO_RUNG_TRANSPLANTS,
    PARTIAL_TRANSPLANT,
    UNCALIBRATED,
    CONVOY_WEIGHT,
    convoy_screen,
    crossing_screen,
    CEILING_CENSORED,
    CONVOY_LAM,
    CONVOY_MARGIN,
    CONVOY_SCENARIO,
    CONVOY_W75_CLEARANCES,
    FLOOR_CENSORED,
    FULL_TRANSPLANT,
    LAM_NOT_ADMISSIBLE,
    MIXED_CENSORING,
    NOT_CENSORED,
    NO_RUNG_TRANSPLANTS,
    PARTIAL_TRANSPLANT,
    REFERENCE_WEIGHTS,
    TRANSPLANTS,
    UNCALIBRATED,
    RungTransplant,
    TransplantScreen,
    censoring_direction,
    convoy_screen,
    convoy_w75_sweep,
    convoy_w75_walk,
    disjoint_arms,
)
from eval.mppi_sandbox.separation_reproduction import (
    BOTH_ARMS_CENSORED,
    FLOOR,
    w75_reproduction,
)


# --- the screen: the protocol moves to exactly one rung ----------------------

def test_only_w75_transplants_to_convoy():
    screen = convoy_screen()
    assert screen.walkable == (75.0,)
    assert screen.coverage == (1, 4)
    assert screen.verdict == PARTIAL_TRANSPLANT


def test_blocked_rungs_keep_their_distinct_reasons():
    """`LAM_NOT_ADMISSIBLE` and `UNCALIBRATED` are different debts — one is a
    calibration run away from screenable, the other is a measured refusal."""
    assert dict(convoy_screen().blocked) == {
        100.0: LAM_NOT_ADMISSIBLE,
        150.0: UNCALIBRATED,
        250.0: UNCALIBRATED,
    }


def test_w100_is_blocked_by_a_measured_window_not_a_missing_one():
    """The rung most likely to be walked by mistake: convoy *is* calibrated at
    `w = 100`, and its window simply does not contain the band's λ."""
    rung = next(r for r in convoy_screen().rungs if r.weight == 100.0)
    windows = dict(rung.windows)
    assert all(w is not None and w for w in windows.values())
    assert all(CONVOY_LAM not in w for w in windows.values())


def test_screen_verdict_is_independent_of_its_coverage_count():
    """Both non-partial corners are reachable, so `PARTIAL_TRANSPLANT` is a
    reading and not a constant."""
    def screen(weights):
        return TransplantScreen(
            scenario=CONVOY_SCENARIO,
            rungs=tuple(RungTransplant(scenario=CONVOY_SCENARIO, weight=w,
                                       lam=CONVOY_LAM,
                                       arms=("stock_mppi", "risk_mppi"))
                        for w in weights),
        )

    assert screen((75.0,)).verdict == FULL_TRANSPLANT
    assert screen((150.0, 250.0)).verdict == NO_RUNG_TRANSPLANTS


def test_empty_screen_is_refused_by_name():
    with pytest.raises(ValueError, match="no rungs"):
        TransplantScreen(scenario=CONVOY_SCENARIO, rungs=())


def test_reference_weights_are_the_bands_four_rungs():
    assert REFERENCE_WEIGHTS == (75.0, 100.0, 150.0, 250.0)


# --- the walk ----------------------------------------------------------------

def test_convoy_walk_is_graded_at_its_own_margin_not_the_bands():
    """D-159's cross-scope error, pinned: 0.30 is convoy's, 0.40 is head_on's."""
    from eval.mppi_sandbox.scorable_band import PUBLISHED_MARGIN

    walk = convoy_w75_walk()
    assert CONVOY_MARGIN == 0.30
    assert PUBLISHED_MARGIN != CONVOY_MARGIN
    assert walk.reference.headroom.margin == CONVOY_MARGIN
    assert walk.pooled.scenario == CONVOY_SCENARIO


def test_every_convoy_run_clears_the_margin():
    clear = [c for arm in CONVOY_W75_CLEARANCES.values() for c in arm]
    assert len(clear) == 64
    assert min(clear) >= CONVOY_MARGIN
    assert convoy_w75_walk().pooled.verdict == NO_HEADROOM_SAFE


def test_both_arms_sit_at_the_floor_in_both_blocks():
    walk = convoy_w75_walk()
    for block in (walk.reference, walk.replication):
        assert block.censoring == BOTH_ARMS_CENSORED
        assert {b for _, b in block.censored} == {FLOOR}


def test_the_safety_headline_is_zero_on_both_arms():
    """What makes this unscorable rather than a clean win: the statistic the
    band reports cannot move, so there is no delta to attribute."""
    pooled = convoy_w75_walk().pooled
    assert pooled.a.unsafe_rate == 0.0
    assert pooled.b.unsafe_rate == 0.0


def test_arms_are_disjoint_and_risk_is_the_safer_one():
    """A complete clearance separation — 32 against 32 — that is a mechanism
    reading and not a safety one (D-124, in the mirror direction)."""
    stock = CONVOY_W75_CLEARANCES["stock_mppi"]
    risk = CONVOY_W75_CLEARANCES["risk_mppi"]
    assert max(stock) < min(risk)
    assert disjoint_arms(convoy_w75_sweep())
    assert convoy_w75_sweep().arm_overlap == pytest.approx(-0.0198, abs=5e-5)
    # ...and the trap it would be mistaken for reads False, because both means
    # are *above* the margin rather than below it.
    assert convoy_w75_walk().pooled.sub_margin is False


def test_sweep_returns_its_vacuity_verdict_not_a_two_sided_refusal():
    """`margin_sweep` grades whether a *recorded* separation survives; convoy
    recorded none, so the verdict is the vacuity one and the substantive answer
    is the empty `two_sided`."""
    sweep = convoy_w75_sweep()
    assert sweep.verdict == NO_RECORDED_SEPARATION
    assert sweep.two_sided == ()
    assert sweep.window is None


def test_no_threshold_is_two_sided_anywhere():
    """The claim is over the reals, so probe it densely rather than argue it.

    A threshold is two-sided only if it is interior to *both* arms' ranges;
    the arms are disjoint, so no value in the pooled span qualifies. 2000
    points, matching `margin_sweep`'s own exhaustiveness probe.
    """
    stock = CONVOY_W75_CLEARANCES["stock_mppi"]
    risk = CONVOY_W75_CLEARANCES["risk_mppi"]
    lo = min(min(stock), min(risk))
    hi = max(max(stock), max(risk))
    for i in range(2001):
        m = lo + (hi - lo) * i / 2000.0
        interior_stock = min(stock) < m <= max(stock)
        interior_risk = min(risk) < m <= max(risk)
        assert not (interior_stock and interior_risk), m


# --- the finding: one verdict, two boundaries --------------------------------

def test_both_scenes_are_none_two_sided_from_opposite_boundaries():
    """`cafe_head_on_v0` at `w = 75` and `cafe_convoy_v0` at `w = 75` are both
    `BOTH_ARMS_CENSORED`-adjacent dead ends, and the direction is the whole
    difference between them: head_on's margin is too hard for the scene,
    convoy's is too easy."""
    convoy = convoy_w75_walk().reference.headroom
    head_on = w75_reproduction().reference.headroom

    assert convoy.verdict == NO_HEADROOM_SAFE
    assert censoring_direction(convoy) == FLOOR_CENSORED

    # head_on's stock arm is pinned at the ceiling — nothing it does clears
    # 0.40 m — while its risk arm is free, so the scene is censored the other
    # way and is not even a `NO_HEADROOM_*` case.
    assert head_on.a.unsafe_rate == 1.0
    assert censoring_direction(head_on) == CEILING_CENSORED
    assert censoring_direction(convoy) != censoring_direction(head_on)


@pytest.mark.parametrize("rates,expected", [
    ((0.0, 0.0), FLOOR_CENSORED),
    ((1.0, 1.0), CEILING_CENSORED),
    ((0.0, 1.0), MIXED_CENSORING),
    ((0.5, 0.25), NOT_CENSORED),
    ((0.0, 0.5), FLOOR_CENSORED),
])
def test_censoring_direction_covers_every_corner(rates, expected):
    """Constructed rather than measured, because three of these five corners
    have never occurred and a reading only exercised on its one real input is
    not characterised."""
    def arm(name, rate):
        n = 4
        k = round(rate * n)
        # k runs under the margin, the rest above it.
        clearances = tuple([CONVOY_MARGIN - 0.1] * k
                           + [CONVOY_MARGIN + 0.1] * (n - k))
        return ArmSafety(arm=name, clearances=clearances, margin=CONVOY_MARGIN)

    h = Headroom(scenario=CONVOY_SCENARIO, weight=75.0, lam=CONVOY_LAM,
                 a=arm("stock_mppi", rates[0]), b=arm("risk_mppi", rates[1]))
    assert censoring_direction(h) == expected
    # Only when *both* arms sit at the same boundary is the pair unscorable;
    # `MIXED_CENSORING` and the one-arm cases are `SEPARATED` and do have a
    # headline. This is why the direction is reported beside `censoring` and
    # not instead of it.
    unscorable = rates in ((0.0, 0.0), (1.0, 1.0))
    assert (h.verdict in (NO_HEADROOM_SAFE, NO_HEADROOM_UNSAFE)) is unscorable


def test_the_last_eligible_scene_is_walkable_at_exactly_one_rung():
    """D-163 corrects D-161: the population is **3**, not 2.

    D-161 read this screen as `NO_RUNG_TRANSPLANTS` 0/4 and concluded that the
    third eligible scene could never host the successor question. Two of those
    four refusals were `UNCALIBRATED` — *unmeasured*, not empty, which the
    verdict's own docstring says is "not refused … unscreenable until someone
    runs `calibrate_lam` there". This cycle ran it, and one of the two came
    back walkable: at `w = 250` both arms admit λ = 0.8, the band's own.

    So the scene is 1/4 like convoy, and the walkable-scene population closes
    at 3. The reading that has to be kept apart from that: a rung's being
    *walkable* is a statement about admissible temperature, not about the
    two-sidedness the successor question wants — it buys the right to spend 64
    runs here, nothing more.
    """
    s = crossing_screen()
    assert s.verdict == PARTIAL_TRANSPLANT
    assert s.coverage == (1, 4)
    assert s.walkable == (250.0,)
    # The rung that moved was one of the two that had never been measured.
    assert 250.0 not in dict(s.blocked)


def test_crossing_is_blocked_for_a_reason_convoy_never_was():
    """0/4 and 1/4 are not the same shortfall, and `blocked` must say so.

    Convoy's blocked rung has a non-empty window — λ = 1.1314 is admissible
    there, so the rung is refused at the *reference* λ and buying it back
    costs only cross-scene comparability. Crossing's `w = 75` has an arm with
    **no** admissible λ at all: there is nothing to trade away, and the repair
    is a different weight rather than a different λ. Collapsing the two into
    "blocked" loses exactly the half that says which rungs are recoverable.
    """
    crossing = dict(crossing_screen().blocked)
    convoy = dict(convoy_screen().blocked)

    assert crossing[75.0] == NO_ADMISSIBLE_LAM
    assert crossing[100.0] == NO_ADMISSIBLE_LAM
    assert convoy[100.0] == LAM_NOT_ADMISSIBLE
    assert NO_ADMISSIBLE_LAM not in convoy.values()

    # D-163 spent the `calibrate_lam` run the `UNCALIBRATED` verdict asks for,
    # on crossing only. Its `w = 150` resolved to a *third* kind of refusal —
    # the stock arm has a cell there and no admissible λ in it, while the risk
    # arm has `[0.4, 0.8]` — so measuring an unmeasured rung is not a coin
    # flip between "walkable" and "unchanged": it can also convert an unknown
    # into a refusal that is now known to have no repair at this weight.
    assert crossing[150.0] == NO_ADMISSIBLE_LAM
    assert 250.0 not in crossing            # the one that came back walkable

    # Convoy was never calibrated at either weight, so `UNCALIBRATED` stays
    # reachable over the shipped tables — buying crossing's two cells must not
    # quietly turn the verdict into prose (`guard_vacuity`'s complaint).
    assert convoy[150.0] == convoy[250.0] == UNCALIBRATED


def test_the_new_verdict_does_not_move_the_recorded_convoy_screen():
    """D-160's 1/4 was recorded before `NO_ADMISSIBLE_LAM` existed.

    Adding a verdict that sits *ahead* of `LAM_NOT_ADMISSIBLE` in the same
    branch could silently re-grade a published screen, which is how a
    refinement becomes a retraction nobody announced.
    """
    s = convoy_screen()
    assert s.verdict == PARTIAL_TRANSPLANT
    assert s.coverage == (1, 4)
    assert s.walkable == (CONVOY_WEIGHT,)


# --- the third scene: the population closes, and the repair is asked ---------

def _crossing():
    from eval.mppi_sandbox.scene_transplant import crossing_w250_walk
    return crossing_w250_walk()


def _crossing_sweep():
    from eval.mppi_sandbox.scene_transplant import crossing_w250_sweep
    return crossing_w250_sweep()


def test_the_crossing_walk_ran_at_the_rung_its_own_screen_licensed():
    """The walk is only admissible because `crossing_screen` grades `w = 250`
    `TRANSPLANTS` — pinned together so a recalibration that moves the screen
    cannot leave this walk quoting an operating point nothing licenses."""
    from eval.mppi_sandbox.scene_transplant import (
        CROSSING_LAM, CROSSING_MARGIN, CROSSING_SCENARIO, CROSSING_WEIGHT,
    )
    from eval.mppi_sandbox.scorable_band import PUBLISHED_LAM, PUBLISHED_MARGIN

    screen = crossing_screen()
    assert screen.walkable == (CROSSING_WEIGHT,)
    assert CROSSING_LAM == PUBLISHED_LAM
    # ...but the margin is the scene's own, not the band's (D-159).
    assert CROSSING_MARGIN == 0.30 != PUBLISHED_MARGIN
    walk = _crossing()
    assert walk.pooled.scenario == CROSSING_SCENARIO
    assert walk.reference.headroom.margin == CROSSING_MARGIN


def test_the_third_scene_is_a_third_dead_end_at_its_declared_margin():
    """3/3 eligible scenes measured, 0/3 two-sided — the census closes."""
    from eval.mppi_sandbox.scene_transplant import CROSSING_W250_CLEARANCES

    walk = _crossing()
    assert walk.pooled.verdict == NO_HEADROOM_SAFE
    assert walk.pooled.a.unsafe_rate == 0.0
    assert walk.pooled.b.unsafe_rate == 0.0
    for block in (walk.reference, walk.replication):
        assert block.censoring == BOTH_ARMS_CENSORED
        assert censoring_direction(block.headroom) == FLOOR_CENSORED
    clear = [c for arm in CROSSING_W250_CLEARANCES.values() for c in arm]
    assert len(clear) == 64
    assert min(clear) >= 0.30


def test_crossing_is_the_first_scene_whose_arms_overlap_enough_to_regrade():
    """The three scenes' dead ends are not the same dead end. Convoy's arms are
    disjoint and the band's tightest rungs nearly so, which is what makes those
    unrepairable; crossing's overlap by two orders more, so a two-sided test
    exists to be asked."""
    sweep = _crossing_sweep()
    assert not disjoint_arms(sweep)
    assert sweep.arm_overlap == pytest.approx(0.1866, abs=5e-5)
    # convoy, for contrast — the same property, opposite sign
    assert disjoint_arms(convoy_w75_sweep())
    assert convoy_w75_sweep().two_sided == ()
    # ...and crossing's window is the first non-empty one outside the band
    assert len(sweep.two_sided) == 46
    assert sweep.window == pytest.approx((0.9712, 1.0906), abs=5e-5)


def test_the_regrade_has_no_margin_independent_verdict():
    """The finding. Four verdicts over 46 thresholds with no majority, and the
    mechanism's own direction the rarest — so which margin is declared decides
    what the rung is found to be."""
    from eval.mppi_sandbox.scene_transplant import (
        MARGIN_DECIDES_VERDICT, margin_decides, margin_verdict_counts,
    )
    from eval.mppi_sandbox.separation_reproduction import (
        NOT_REPRODUCED, NO_SEPARATION_TO_REPRODUCE, REPRODUCED, SIGN_REVERSED,
    )

    sweep = _crossing_sweep()
    assert margin_decides(sweep) == MARGIN_DECIDES_VERDICT
    counts = margin_verdict_counts(sweep)
    assert counts == {
        SIGN_REVERSED: 15,
        NO_SEPARATION_TO_REPRODUCE: 14,
        NOT_REPRODUCED: 10,
        REPRODUCED: 7,
    }
    assert sum(counts.values()) == len(sweep.two_sided)
    # no majority, and the modal outcome is the two blocks reversing sign
    assert max(counts.values()) < len(sweep.two_sided) / 2
    assert max(counts, key=counts.get) == SIGN_REVERSED
    assert counts[REPRODUCED] == min(counts.values())


def test_held_counts_agreement_with_a_vacuity_verdict_not_stability():
    """Why `margin_decides` is not a rename of `MarginSweep.held`. The recorded
    verdict here *is* the vacuity one, so `held` counts the margins that agree
    there was nothing to reproduce — 14 of 46 — while the other 32 disagree
    with each other too. `held` alone would read as a stability fraction."""
    from eval.mppi_sandbox.scene_transplant import margin_verdict_counts
    from eval.mppi_sandbox.separation_reproduction import (
        NO_SEPARATION_TO_REPRODUCE,
    )

    sweep = _crossing_sweep()
    assert sweep.recorded_verdict == NO_SEPARATION_TO_REPRODUCE
    assert len(sweep.held) == margin_verdict_counts(sweep)[
        NO_SEPARATION_TO_REPRODUCE]
    assert len(sweep.lost) == 32


def test_margin_decides_covers_its_vacuous_and_inert_corners():
    """`margin_decides` must not be a constant. Convoy supplies the vacuity
    corner from a shipped artifact; `MARGIN_INERT` is reachable and is proved
    so by a synthetic sweep, since no shipped scene produces it today."""
    from eval.mppi_sandbox.margin_sweep import MarginSweep
    from eval.mppi_sandbox.scene_transplant import (
        MARGIN_INERT, NO_TWO_SIDED_TO_SPREAD, margin_decides,
    )
    from eval.mppi_sandbox.separation_reproduction import reproduction_at

    assert margin_decides(convoy_w75_sweep()) == NO_TWO_SIDED_TO_SPREAD

    # Both blocks identical and both arms straddling one another: every
    # two-sided threshold grades the rung the same way.
    # `i % 16` so the two seed blocks span the *same* range — a sweep needs a
    # threshold interior to both arms in both blocks, which a monotone 0..31
    # ramp can never supply (its blocks do not overlap each other at all).
    stock = tuple(0.30 + 0.01 * (i % 16) for i in range(32))
    risk = tuple(0.32 + 0.01 * (i % 16) for i in range(32))
    inert = MarginSweep(reproduction=reproduction_at(
        "synthetic.yaml", 0.8, 0.35, 250.0, ("stock_mppi", "risk_mppi"),
        {"stock_mppi": stock, "risk_mppi": risk}, 16))
    assert inert.two_sided
    assert margin_decides(inert) == MARGIN_INERT


def test_the_convoy_clearance_separation_does_not_reproduce_on_crossing():
    """Convoy's 32-against-32 arm separation is the repo's widest; on the third
    scene the same two arms are tied, with the risk arm marginally worse. A
    mechanism reading, like convoy's — and it does not carry."""
    from eval.mppi_sandbox.scene_transplant import CROSSING_W250_CLEARANCES

    stock = CROSSING_W250_CLEARANCES["stock_mppi"]
    risk = CROSSING_W250_CLEARANCES["risk_mppi"]
    stock_mean = sum(stock) / len(stock)
    risk_mean = sum(risk) / len(risk)
    assert stock_mean == pytest.approx(1.0229, abs=5e-5)
    assert risk_mean == pytest.approx(1.0211, abs=5e-5)
    assert risk_mean < stock_mean          # the risk arm is *not* the safer one
    assert abs(risk_mean - stock_mean) < 0.01
    # convoy, where it did carry
    c_stock = CONVOY_W75_CLEARANCES["stock_mppi"]
    c_risk = CONVOY_W75_CLEARANCES["risk_mppi"]
    assert max(c_stock) < min(c_risk)

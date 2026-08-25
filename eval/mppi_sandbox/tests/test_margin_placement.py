"""Is the declared margin the instrument at fault?

`test_states_hypothesis_holds_for_convoy_and_fails_for_head_on` is the finding
and is written as a two-scene comparison on purpose: the claim under test is a
*census-wide* one ("neither scene's margin sits inside its own distribution")
and it can only be refuted by reading the scenes together.

`test_pooling_manufactures_interiority_the_blocks_do_not_have` pins the reason
the two answers differ, and computes **both** scopes side by side rather than
asserting the preferred one — the same shape D-157 used for union-vs-
intersection, and for the same reason: the pooled scope is the flattering one.

Nothing here runs a simulation; the clearances are constants.
"""

import pytest

from eval.mppi_sandbox.margin_placement import (
    ABOVE_ALL,
    BELOW_ALL,
    INTERIOR,
    MISPLACED,
    ONE_ARM_ONLY,
    SOME_MISPLACED,
    WELL_PLACED,
    ArmPlacement,
    census,
)
from eval.mppi_sandbox.scene_transplant import CONVOY_SCENARIO
from eval.mppi_sandbox.scorable_band import PUBLISHED_SCENARIO


def _by_scene(c, scenario):
    return [r for r in c.rungs if r.scenario == scenario]


def test_states_hypothesis_holds_for_convoy_and_fails_for_head_on():
    """STATE read `NONE_TWO_SIDED` as a mis-declared margin in **both** scenes.

    It is true of convoy and false of head_on, so the diagnosis is scene-local
    and the census verdict must not be readable as a blanket one.
    """
    c = census()

    convoy = _by_scene(c, CONVOY_SCENARIO)
    assert len(convoy) == 1
    assert convoy[0].verdict == MISPLACED
    # Every convoy run clears the margin — the arms are pinned at a floor, so
    # no re-grading of *this* walk reaches a two-sided test.
    assert [a.verdict for a in convoy[0].arms] == [ABOVE_ALL, ABOVE_ALL]

    head_on = {r.weight: r for r in _by_scene(c, PUBLISHED_SCENARIO)}
    assert set(head_on) == {75.0, 100.0, 150.0, 250.0}
    # Half the band's rungs have a margin interior to both arms: the blanket
    # reading is refuted by these two rows alone.
    assert head_on[150.0].verdict == WELL_PLACED
    assert head_on[250.0].verdict == WELL_PLACED
    # The other half is one-sided in a *specific* direction — the stock arm
    # never clears 0.40 m (D-158's ceiling), which is not a mis-declaration.
    for w in (75.0, 100.0):
        assert head_on[w].verdict == ONE_ARM_ONLY
        stock, risk = head_on[w].arms
        assert stock.verdict == BELOW_ALL
        assert risk.verdict == INTERIOR

    # The census-level verdict is driven by convoy alone.
    assert c.verdict == SOME_MISPLACED
    assert c.misplaced == ((CONVOY_SCENARIO, 75.0),)
    assert c.coverage == (2, 5)


def test_pooling_manufactures_interiority_the_blocks_do_not_have():
    """The two well-placed rungs are censored at the scope D-157 grades.

    Both scopes are computed here so the disagreement is the assertion. If a
    future change makes `verdict` read per block, this fails rather than
    quietly turning 2/5 into 0/5 with no record of which scope moved.
    """
    c = census()
    pooled = {(r.scenario, r.weight) for r in c.rungs
              if r.verdict == WELL_PLACED}
    per_block = {(r.scenario, r.weight) for r in c.rungs if r.block_interior}

    assert pooled == {(PUBLISHED_SCENARIO, 150.0), (PUBLISHED_SCENARIO, 250.0)}
    # Not one walked rung has a margin interior to every arm of every block —
    # this is the 2/5-vs-0/5 delta, and it is entirely a scope artefact.
    assert per_block == set()
    assert set(c.scope_disagreement) == pooled


def test_a_margin_on_the_boundary_is_not_interior():
    """Interiority is strict at both ends.

    A run whose clearance *equals* the margin is not evidence that the margin
    discriminates — it is the single value at which the safe/unsafe split is
    undefined, and rounding it inward would let a degenerate range read as
    two-sided.
    """
    assert ArmPlacement(arm="a", clearances=(0.30, 0.50),
                        margin=0.30).verdict == ABOVE_ALL
    assert ArmPlacement(arm="a", clearances=(0.10, 0.30),
                        margin=0.30).verdict == BELOW_ALL
    assert ArmPlacement(arm="a", clearances=(0.30, 0.30),
                        margin=0.30).verdict == ABOVE_ALL
    assert ArmPlacement(arm="a", clearances=(0.29, 0.31),
                        margin=0.30).verdict == INTERIOR


def test_an_arm_with_no_clearances_is_refused_not_scored():
    """An empty range is not "not interior" — it is unmeasured (D-107)."""
    with pytest.raises(ValueError, match="no recorded clearances"):
        ArmPlacement(arm="a", clearances=(), margin=0.30)

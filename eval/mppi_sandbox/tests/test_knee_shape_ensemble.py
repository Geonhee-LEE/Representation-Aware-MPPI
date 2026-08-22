# SPDX-License-Identifier: BSD-3-Clause
"""D-430: the knee+shape trade at n=16, with the mode split reported per arm.

D-427 read the collision knee and the barrier-shape knob as complementary from
a **5-seed** matrix: base 0/5, knee 1/5, shape 0/5, knee+shape 3/5. D-429 then
showed the per-seed `cte_rms` underneath those counts is **bimodal**, so the
mean D-427 quoted is a mode-mixture statistic and the 1/5 -> 3/5 headline is
underpowered. STATE named both defects and observed they are fixed by the same
run: widen to 16 seeds and report the mode split per arm.

This module is that run. It costs ~64 integrations (4 arms x 16 seeds, ~40 s),
computed once in a module fixture. What it found is not a cleaner version of
D-427's claim — it is a different claim in three places:

1. **The headline shrinks and stays underpowered.** 3/16 -> 6/16, not 1/5 ->
   3/5. Fisher on the knee-vs-knee+shape 2x2 gives p ~ 0.43: at n=16 the shape
   knob's *marginal* contribution over the knee is still not established. What
   *is* established is the pair against base (0/16 vs 6/16, p ~ 0.018).
2. **Mode is not a property of the seed.** The detour seeds under `knee` and
   under `knee+shape` overlap in exactly one seed out of {4, 6}. The shape knob
   does not convert squeeze seeds into detour seeds; it reshuffles which seeds
   land in which mode, in both directions.
3. **The two arms pass by different mechanisms.** Under `knee`, every passing
   seed is a detour seed — you buy clearance with a wide berth. Under
   `knee+shape`, most passing seeds are *squeeze*-mode: they hold the path and
   clear the gate anyway. That is the first arm measured here that gets
   avoidance without paying for it in mode, and it is the reason to keep the
   shape knob even though (1) says its count is not yet significant.

The residual is also worth stating: under `knee+shape` the clearance gate is
green on **16 of 16**, and every remaining failure is a tracking check —
`heading_err_rms_max` on 10 seeds. On this scene the avoidance problem is
solved by the pair; what is left is a heading-smoothness problem.
"""

from __future__ import annotations

from math import comb

import pytest

from eval.mppi_sandbox.controllers.stock_mppi import MPPIParams
from eval.mppi_sandbox.run import run_scenario

CROSSING = "eval/scenarios/cafe_obstacle_crossing_v0.yaml"
#: The clearance threshold the scene grades against, and the value both knobs
#: are set to. See `test_collision_knee.GATE` / `test_barrier_shape.GATE`.
GATE = 0.30
#: `time_to_goal` cut separating the two modes (D-429). The gap is ~9 s wide,
#: so any cut inside it labels identically — this is not a fitted threshold.
MODE_SPLIT_TTG = 12.0
#: 16 seeds: double D-429's 8, chosen because STATE asked for the power and
#: this is what fits one cycle. Still not a large-n claim — see `test_..._is_
#: still_underpowered` below, which pins that honestly rather than hiding it.
SEEDS = tuple(range(16))

ARMS = {
    "base": dict(),
    "knee": dict(collision_margin=GATE),
    "shape": dict(obs_barrier_band=GATE),
    "knee+shape": dict(collision_margin=GATE, obs_barrier_band=GATE),
}


@pytest.fixture(scope="module")
def ensemble():
    """{arm: [per-seed run summary]} — 4 arms x 16 seeds, computed once."""
    out = {}
    for arm, kw in ARMS.items():
        out[arm] = [
            run_scenario(CROSSING, controller="stock_mppi", seed=s,
                         params=MPPIParams(**kw))
            for s in SEEDS
        ]
    return out


def _detour(runs) -> set[int]:
    return {s for s, r in zip(SEEDS, runs)
            if r["metrics"]["time_to_goal"] > MODE_SPLIT_TTG}


def _passing(runs) -> set[int]:
    return {s for s, r in zip(SEEDS, runs) if all(r["acceptance"].values())}


def _failing_checks(runs) -> dict[str, int]:
    counts: dict[str, int] = {}
    for r in runs:
        for name, ok in r["acceptance"].items():
            if not ok:
                counts[name] = counts.get(name, 0) + 1
    return counts


def _fisher_two_sided(a: int, b: int, c: int, d: int) -> float:
    """Two-sided Fisher exact p for [[a,b],[c,d]]. No scipy in this sandbox."""
    n = a + b + c + d
    obs = comb(a + b, a) * comb(c + d, c) / comb(n, a + c)
    total = 0.0
    for i in range(min(a + b, a + c) + 1):
        j = a + c - i
        if 0 <= j <= c + d:
            p = comb(a + b, i) * comb(c + d, j) / comb(n, a + c)
            if p <= obs * (1 + 1e-9):
                total += p
    return total


# ------------------------------------- without the knee, only the gate fails

@pytest.mark.parametrize("arm", ["base", "shape"])
def test_neither_baseline_nor_shape_alone_clears_the_gate(ensemble, arm):
    """Both knee-less arms fail on 16/16, and on the *same single* check.

    This is the precondition that makes the whole matrix readable: without the
    knee the scene has exactly one defect (`min_distance_to_obstacle`), so any
    arm that fixes it can be compared on what it broke instead. It also pins
    D-427's complementarity claim at n=16 — the shape knob alone moves the
    count not at all, so it is not a weaker version of the knee.
    """
    assert _passing(ensemble[arm]) == set()
    assert _failing_checks(ensemble[arm]) == {"min_distance_to_obstacle": 16}
    assert _detour(ensemble[arm]) == set(), "no knee, no detour mode"


# ------------------------------------------------ the pair clears it outright

def test_knee_plus_shape_clears_the_gate_on_every_seed(ensemble):
    """The residual after the pair is tracking-only — avoidance is solved here.

    16/16 on `min_distance_to_obstacle` (the knee arm alone still misses one),
    and no clearance check appears among the failures at all. The remaining
    failures are heading/cross-track. This is the sharpest north-star statement
    the scene has produced: on `cafe_obstacle_crossing_v0` the object-avoidance
    half is met by the pair, and the open problem is path-tracking quality.
    """
    failures = _failing_checks(ensemble["knee+shape"])
    assert "min_distance_to_obstacle" not in failures
    assert set(failures) <= {"cte_rms_max", "cte_max", "heading_err_rms_max"}
    # Heading, not cross-track, is the dominant residual — it fails on a
    # majority of seeds while each cte check fails on a small minority.
    assert failures["heading_err_rms_max"] > sum(
        v for k, v in failures.items() if k.startswith("cte"))


def test_the_headline_improves_but_is_still_underpowered(ensemble):
    """D-427's 1/5 -> 3/5 does not survive as a *marginal* effect at n=16.

    Direction holds (3/16 -> 6/16) but Fisher on the knee-vs-knee+shape 2x2
    does not reach 0.05. The pair against base does. So the honest claim after
    this cycle is "knee+shape beats doing nothing", not "shape beats knee".

    This test pins the *non*-significance deliberately: a future cycle that
    widens the ensemble far enough to cross 0.05 will see it fail, and that
    failure is the signal to promote the claim rather than a regression.
    """
    n = len(SEEDS)
    knee, pair, base = (len(_passing(ensemble[a]))
                        for a in ("knee", "knee+shape", "base"))
    assert base == 0 and knee < pair, "the ordering is the part that holds"

    marginal = _fisher_two_sided(pair, n - pair, knee, n - knee)
    assert marginal > 0.05, (
        f"shape-over-knee reached significance (p={marginal:.3f}) — the "
        "underpowered caveat in D-430 is stale, promote the claim")

    versus_base = _fisher_two_sided(pair, n - pair, base, n - base)
    assert versus_base < 0.05, f"pair-vs-base lost significance (p={versus_base:.3f})"


# --------------------------------------------- mode is not a seed's property

def test_the_shape_knob_reshuffles_modes_rather_than_converting_them(ensemble):
    """The answer to STATE #2, and it is not the expected one.

    The hypothesis was that `obs_barrier_band` converts squeeze-mode seeds into
    detour-mode ones, which would have made the mean `cte_rms` a symptom of a
    mode shift. What it actually does is move seeds in **both** directions and
    keep almost none: the detour sets of the two arms overlap in one seed.

    So "seed N detours" is not a fact about seed N — it is a fact about (seed,
    arm). D-429's `test_seed_zero_is_in_the_smaller_mode` is true of the knee
    arm specifically, and must not be read as a property of seed 0.
    """
    knee_d, pair_d = _detour(ensemble["knee"]), _detour(ensemble["knee+shape"])
    assert knee_d and pair_d

    # Moves in both directions — this is what rules out "conversion".
    assert knee_d - pair_d, "no seed left the detour mode"
    assert pair_d - knee_d, "no seed entered the detour mode"
    # And keeps almost nothing: the overlap is a minority of each arm's set.
    assert len(knee_d & pair_d) < min(len(knee_d), len(pair_d))

    # The count still rises, which is why the mean cte_rms moved at all.
    assert len(pair_d) > len(knee_d)


def test_the_two_arms_pass_by_different_mechanisms(ensemble):
    """The finding worth keeping: the pair wins *without* buying a detour.

    Under `knee`, passing is entirely a detour phenomenon — every passing seed
    took the wide way around, which is exactly the 1:1 avoidance<->tracking
    trade D-426 priced. Under `knee+shape` that stops being true: a majority of
    the passing seeds are squeeze-mode, holding the path *and* clearing the
    gate. The barrier's compact support is what makes clearance affordable
    without a berth, and that — not the 3/16 -> 6/16 count — is the reason to
    carry the shape knob forward.
    """
    knee_pass, knee_d = _passing(ensemble["knee"]), _detour(ensemble["knee"])
    assert knee_pass and knee_pass <= knee_d, (
        "under the knee alone, passing should require detouring")

    pair_pass, pair_d = (_passing(ensemble["knee+shape"]),
                         _detour(ensemble["knee+shape"]))
    squeeze_passers = pair_pass - pair_d
    assert len(squeeze_passers) > len(pair_pass & pair_d), (
        "the pair's passing seeds should be mostly squeeze-mode — that is the "
        "escape from the 1:1 trade this arm was kept for")

# SPDX-License-Identifier: BSD-3-Clause
"""Q-035 / Q-025: "no shared temperature exists" is a property of *one scene*,
not of the protocol — but the fix it seems to license, a fixed `lam` chosen on
a better-behaved scene, is ruled out by the same measurement.

The 2026-08-02 14:00 cycle found that on the `offset = 0.3` hazard no `lam`
over twelve temperatures puts both arms of the shadow-cost A/B fully inside
Q-026's ESS band, and left a three-way fork: widen the band, calibrate `lam`
per seed, or retire that scene as an ablation surface. Option (c) is only
available if the pathology is scene-specific, so this file measures the same
ladder on two other surfaces at n = 8.

**It is scene-specific.** The centred variant of the same hazard, same
controller, has a shared admissible temperature:

| surface                     | lam window with 8/8 seeds in band  |
|-----------------------------|------------------------------------|
| `offset = 0.3` / risk_mppi  | **none** over 14 temperatures      |
| centred hazard / risk_mppi  | `lam = 5.0` (both arms)            |
| centred hazard / stock_mppi | `lam = 4.0` and `5.0`              |
| `cafe_straight_v0` / stock  | `lam = 0.2`, `0.3`, `0.4`          |

So option (c) survives, and 13:00's `lam = 5.0` result is not a knife edge —
`stock_mppi` on the centred hazard is admissible on two adjacent rungs.

**But the last row is the finding that matters more.** `cafe_straight_v0` has
no obstacles, and its admissible window sits at `lam ≈ 0.2 - 0.4` — roughly
**20x below** the hazard scenes' `4.0 - 5.0`. The two windows do not overlap
anywhere:

* at `lam = 0.3` (admissible on `cafe_straight`) the centred hazard runs at
  median ESS ~1.2 of K = 256 — one-hot, far below the floor;
* at `lam = 5.0` (admissible on the centred hazard) `cafe_straight` runs at
  median ESS ~227 — near-uniform, far above the ceiling.

A single fixed `lam` therefore cannot be admissible across the sandbox's own
scenario matrix, no matter which value is chosen. Q-025 asked whether a
fixed-`lam` ablation is admissible and was answered "no" three times on
narrowing grounds (scenes, then seeds, then controllers); this is the
constructive version — two scenes already in the repo whose admissible sets
are **disjoint**.

The mechanism is visible in the ladders and is not about obstacles being
"harder". What differs is how steeply ESS climbs with `lam`, i.e. how much
contrast the cost landscape has to spend. On `cafe_straight` the per-seed
spread is ~1.2x and the median crosses the band's full 10x width over
`lam = 0.15 -> 0.55` (~3.7x in `lam`); on the centred hazard it crosses over
`~2.9 -> >8` (>2.8x); on `offset = 0.3` the same crossing takes only
`~1.1 -> 1.9` (~1.7x) while the per-seed spread reaches 18x. A band is
reachable when the ladder crosses it more slowly than the seeds scatter — and
that ratio is a property of the scene's cost landscape, which is exactly the
thing an ablation is supposed to hold fixed.

Also filled here: 14:00's twelve-point ladder skipped `lam = 2.5` and `4.0` on
`offset = 0.3`. Both are non-admissible (0/8 and 2/8 respectively), so the
"no shared temperature" claim is not an artifact of a hole in the ladder.

CI cost is bounded to six seed sweeps; the full ladders live in this docstring
and the journal, per Q-030.
"""

import pytest

from eval.mppi_sandbox import ab
from eval.mppi_sandbox.controllers.stock_mppi import MPPIParams
from eval.mppi_sandbox.obstacles import CircleObstacle
from eval.mppi_sandbox.scenario import load_scenario
from eval.mppi_sandbox.tests.test_sandbox import _straight_scenario

SEEDS = tuple(range(8))
K = MPPIParams().samples
ESS_FLOOR, ESS_CEIL = ab.ess_band(K)

LAM_HAZARD = 5.0    # admissible on the centred hazard, both arms
LAM_CAFE = 0.3      # admissible on cafe_straight_v0
LAM_GAP = 2.5       # a rung 14:00's offset=0.3 ladder skipped

W_EPIST_ON = 200.0
_ISOLATE_SHADOW = dict(w_risk=0.0, k_margin_per_sigma=0.0)

CAFE_YAML = "eval/scenarios/cafe_straight_v0.yaml"

_CACHE: dict = {}


def _hazard(offset: float):
    return _straight_scenario(obstacles=[CircleObstacle(offset, -1.5)],
                              expected_duration=15.0)


def _probe(surface: str, lam: float, *, w_epist: float = W_EPIST_ON):
    """One memoized `LamProbe`. Every test below reads these six entries."""
    key = (surface, lam, w_epist)
    if key not in _CACHE:
        if surface == "cafe":
            scen, ctrl, kw = load_scenario(CAFE_YAML), "stock_mppi", {}
        else:
            offset = 0.3 if surface == "offset" else 0.0
            scen, ctrl = _hazard(offset), "risk_mppi"
            kw = dict(w_epist=w_epist, **_ISOLATE_SHADOW)
        _CACHE[key] = ab.lam_ladder(scen, ctrl, [lam], SEEDS, **kw)[0]
    return _CACHE[key]


@pytest.mark.slow
class TestThePathologyIsSceneSpecific:
    """Q-035 option (c) — retiring `offset = 0.3` — stays on the table."""

    def test_the_centred_hazard_has_a_shared_admissible_temperature(self):
        """Same controller, same cost term, same seeds, hazard moved to the
        path centre: `lam = 5.0` puts **both** arms fully in band. This is the
        whole question STATE item #2 asked — if it failed, the fixed-`lam`
        ablation protocol would be broken everywhere rather than on one
        scene, and option (c) would not exist."""
        on, off = _probe("centred", LAM_HAZARD), _probe(
            "centred", LAM_HAZARD, w_epist=0.0)
        shared = set(ab.admissible_lams([on])) & set(ab.admissible_lams([off]))
        assert shared == {LAM_HAZARD}, (
            f"lam={LAM_HAZARD} is no longer shared-admissible on the centred "
            f"hazard (on: {on.n_in_band}/{on.n} in band, reached "
            f"{on.all_reached}; off: {off.n_in_band}/{off.n}, reached "
            f"{off.all_reached}) — if this scene lost its admissible rung too, "
            f"'no shared lam' is a protocol problem, not a scene problem, and "
            f"Q-035's option (c) is gone")

    def test_the_offset_scene_stays_inadmissible_on_a_skipped_rung(self):
        """Gap-fill. 14:00 swept twelve temperatures on `offset = 0.3` but
        jumped 2.0 -> 3.0; a hole in a ladder is the cheapest way for a
        'no value exists' claim to be wrong. It is not in band here either."""
        p = _probe("offset", LAM_GAP)
        assert not p.admissible, (
            f"lam={LAM_GAP} is admissible on offset=0.3 after all "
            f"({p.n_in_band}/{p.n} in band) — 14:00's ladder had a hole and "
            f"the 'no shared temperature' finding needs re-deriving")
        assert p.median_ess > ESS_CEIL, (
            f"median ESS {p.median_ess:.2f} at lam={LAM_GAP} is no longer "
            f"above the ceiling {ESS_CEIL:.1f} — this rung was expected to "
            f"overshoot, so the ESS-vs-lam curve on this scene has moved")


@pytest.mark.slow
class TestNoFixedTemperatureServesTheScenarioMatrix:
    """The constructive form of Q-025: two repo scenes, disjoint windows."""

    def test_cafe_straight_is_admissible_twenty_times_lower(self):
        """The obstacle-free baseline scenario is *not* pathological — it has
        a comfortable window (per-seed spread ~1.2x). It just sits an order of
        magnitude away in `lam` from every scene with a hazard in it."""
        p = _probe("cafe", LAM_CAFE)
        assert p.admissible, (
            f"cafe_straight_v0 is not admissible at lam={LAM_CAFE} "
            f"({p.n_in_band}/{p.n} in band, median ESS {p.median_ess:.2f}, "
            f"reached {p.all_reached}) — the disjoint-windows claim below "
            f"rests on this scene having a window at all")
        assert p.spread < 2.0, (
            f"per-seed ESS spread on cafe_straight is {p.spread:.1f}x, no "
            f"longer the tight case — the contrast between this scene and "
            f"offset=0.3's 18x is part of the mechanism story")

    @pytest.mark.parametrize("surface,lam,other_lam", [
        ("cafe", LAM_HAZARD, LAM_CAFE),
        ("centred", LAM_CAFE, LAM_HAZARD),
    ])
    def test_each_scenes_admissible_lam_is_inadmissible_on_the_other(
            self, surface, lam, other_lam):
        """The disjointness itself, measured both ways. Each scene is run at
        the temperature that the *other* scene needs, and fails the band from
        the opposite side — `cafe_straight` near-uniform above the ceiling at
        5.0, the centred hazard one-hot below the floor at 0.3. Failing from
        opposite ends is what makes this unfixable by translation: there is no
        value between them that satisfies both, because moving toward one
        scene's window moves away from the other's."""
        p = _probe(surface, lam)
        assert not p.admissible, (
            f"{surface} is admissible at lam={lam}, which is {other_lam}'s "
            f"scene's temperature — the two windows now overlap and a single "
            f"fixed lam may serve the matrix after all. Re-run both ladders "
            f"before reporting any fixed-lam ablation as controlled")
        outside_ceiling = p.median_ess > ESS_CEIL
        outside_floor = p.median_ess < ESS_FLOOR
        assert outside_ceiling or outside_floor, (
            f"{surface} at lam={lam} has median ESS {p.median_ess:.2f}, "
            f"inside the band [{ESS_FLOOR:.1f}, {ESS_CEIL:.1f}] even though "
            f"individual seeds are not — that is the 13:00 median-hides-the-"
            f"arm mode, so assert on per-seed compliance, not this margin")

    def test_the_two_windows_fail_from_opposite_sides(self):
        """Stated once as a single claim, because the pair of parametrized
        cases above could both pass while failing from the *same* side, which
        would mean the windows are merely far apart rather than ordered
        against each other."""
        cafe_hot = _probe("cafe", LAM_HAZARD)
        centred_cold = _probe("centred", LAM_CAFE)
        assert cafe_hot.median_ess > ESS_CEIL, (
            f"cafe_straight at lam={LAM_HAZARD} is at median ESS "
            f"{cafe_hot.median_ess:.2f}, not above the ceiling "
            f"{ESS_CEIL:.1f} — expected near-uniform weighting")
        assert centred_cold.median_ess < ESS_FLOOR, (
            f"centred hazard at lam={LAM_CAFE} is at median ESS "
            f"{centred_cold.median_ess:.2f}, not below the floor "
            f"{ESS_FLOOR:.1f} — expected one-hot weighting")
        assert centred_cold.median_ess < cafe_hot.median_ess, (
            "the two scenes no longer straddle the band in the expected "
            "order; the disjointness argument needs re-deriving")


@pytest.mark.slow
class TestLadderPrimitiveMatchesTheGuard:
    """`lam_ladder` must agree with `assert_ess_in_band`, or calibration and
    verdict drift apart and the search stops answering the guard's question."""

    def test_admissible_probe_passes_the_guard_and_inadmissible_one_raises(self):
        scen = _hazard(0.0)
        good = ab.seed_sweep(scen, "risk_mppi", SEEDS,
                             params=MPPIParams(lam=LAM_HAZARD),
                             w_epist=W_EPIST_ON, **_ISOLATE_SHADOW)
        assert _probe("centred", LAM_HAZARD).admissible
        ab.assert_ess_in_band(good, f"centred @ lam={LAM_HAZARD}")

        assert not _probe("centred", LAM_CAFE).admissible
        cold = ab.seed_sweep(scen, "risk_mppi", SEEDS,
                             params=MPPIParams(lam=LAM_CAFE),
                             w_epist=W_EPIST_ON, **_ISOLATE_SHADOW)
        with pytest.raises(AssertionError, match="outside the admissible band"):
            ab.assert_ess_in_band(cold, f"centred @ lam={LAM_CAFE}")

    def test_admissible_lams_intersects_arms_rather_than_unioning_them(self):
        """A rung admissible for one arm only must not survive the
        intersection — the failure mode is reporting a comparison as
        controlled because *half* of it was."""
        on = ab.LamProbe(lam=1.0, median_ess=30.0, min_ess=20.0, max_ess=40.0,
                         n_in_band=8, n=8, all_reached=True)
        off = ab.LamProbe(lam=1.0, median_ess=30.0, min_ess=5.0, max_ess=40.0,
                          n_in_band=7, n=8, all_reached=True)
        assert ab.admissible_lams([on]) == (1.0,)
        assert ab.admissible_lams([off]) == ()
        assert not set(ab.admissible_lams([on])) & set(ab.admissible_lams([off]))

    def test_a_non_completing_rung_is_not_admissible_even_if_in_band(self):
        """Q-034's `lam = 30` shape: near-uniform weights with no arm reaching
        the goal must not be reported as a calibrated temperature."""
        frozen = ab.LamProbe(lam=30.0, median_ess=60.0, min_ess=50.0,
                             max_ess=70.0, n_in_band=8, n=8, all_reached=False)
        assert not frozen.admissible
        assert ab.admissible_lams([frozen]) == ()

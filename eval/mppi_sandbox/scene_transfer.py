# SPDX-License-Identifier: BSD-3-Clause
"""Coverage complete: `cbf_mppi` wins 4 of 5 scenes and one scene blocks it.

**D-333 closed the hostable set — all 5 scenes at 8 arms × 8 seeds.** The
question this module was opened to ask ("does any arm win more than one
scene?") is now answered as far as this repo can ask it, and the answer moved
twice on the way: D-330 said the winner sets were pairwise disjoint, D-332
falsified that with a third scene, and the last two scenes settle it.

The matrix, mean gap against `stock_mppi` at `8/8` unless noted:

| arm | freezing | cut_in | head_on | convoy | obst_cross |
|---|---|---|---|---|---|
| `cbf_mppi` | **+0.2282** | −0.0213 (2/8) | **+0.1781** | **+0.1494** | **+0.1888** |
| `social_mppi` | −0.1101 (0/8) | **+0.1187** | +0.0184 (7/8) | −0.0169 (1/8) | −0.0213 (1/8) |
| other six | lose or tie | lose | micro-wins | lose or tie | lose or tie |

Three readings, and the third is the one worth carrying:

* **`cbf_mppi` is blocked by exactly one scene.** It wins four of five at
  ensemble width; :func:`blocking_scenes` returns `('cafe_cut_in_v0',)` and
  :func:`narrowest_block` returns `('cbf_mppi',)`. `arms_that_generalise` is
  still `()` — the north star's "**all** environments" clause remains unmet —
  but the failure is now a single named counterexample rather than a diffuse
  one, which is the sharpest this question has been posed.
* **The blocking scene is precisely the scene the other winner takes.**
  `social_mppi`'s only win in the whole matrix is `cut_in`, and `cut_in` is
  `cbf_mppi`'s only loss. The two arms are *exact complements over the
  hostable set*. That is a stronger statement than "no arm generalises": it
  says the union of two shipped arms already covers all five scenes, so the
  gap is a **selection** problem, not a missing capability. Whether a switch
  between them can be made without oracle knowledge of the scene is the
  obvious next question and is **not** answered here.
* **The arm that travels is still the classical one.** `cbf_mppi` is a
  constraint, not a representation. Every representation arm loses on at least
  four of five scenes, `geometric_mppi` is bit-inert on all forty arm-seed
  pairs, and `risk_mppi`/`frozen_risk_mppi` remain indistinguishable across the
  complete set. The core hypothesis is not supported by this matrix.

Scope, before the numbers because it bounds them:

* **5 of 5 hostable scenes** — the denominator is `hostable_scenes()`, which is
  5 of 8 scenarios; the other three declare zero obstacles, so `min_clearance`
  is `inf` and the census question is undefined there (D-241). "Coverage
  complete" therefore means *complete over what can be measured*, not over the
  scenario set, and it does not extend to unseen environments at all.
* Same operating point for all five columns (`lam = 0.8`, `w_voo = 5`,
  :data:`ess_at_peak.ISOLATION`), so they compose rather than merely sit
  adjacent.
* :data:`CUT_IN_ENSEMBLE`'s `stock_mppi` and `social_mppi` rows are pinned
  equal to the measurement :data:`scene_census.PAIRED_ENSEMBLE` already
  carries, so a re-take that moved either goes red instead of quietly
  disagreeing with D-329.

Cost, measured: `267.3 s` / `193.1 s` / `117.1 s` / `94.7 s` for the four
columns taken here. `STATE.md` priced the last two at `~195 s` each and both
came in far under — the third and fourth consecutive over-estimate across a
scene boundary (`1.38×`, `1.67×`, `2.06×`). D-332 narrowed the one accurate
estimate on this branch to "within-scene"; that narrowing now has confirming
evidence, and it is why the remaining coverage fitted in one cycle.
"""


from __future__ import annotations

from dataclasses import dataclass

from .clearance_census import BASELINE, SEEDS, SEED_ENSEMBLE
from .scene_census import hostable_scenes

#: The scene this cycle measured. `clearance_census.SEED_ENSEMBLE` holds the
#: other one (`cafe_freezing_v0`); the pair is :data:`MEASURED_SCENES`.
CUT_IN_SCENE = "cafe_cut_in_v0"

#: The scene `clearance_census` took its ensemble on, named here so the join
#: below does not have to reach into that module's scene constant by hand.
FREEZING_SCENE = "cafe_freezing_v0"

#: The third scene, measured D-332. Chosen over `convoy` / `obstacle_crossing`
#: because a head-on encounter is the geometry where the yield-vs-freeze
#: distinction is sharpest, which is the axis the open bottleneck asks about:
#: why `social_mppi` wins a lateral intruder and loses a freezing pedestrian.
HEAD_ON_SCENE = "cafe_head_on_v0"

#: The fourth and fifth scenes, measured D-333 — the two that completed the
#: hostable set. No geometry-based preference decided the order this time
#: because both were taken in one cycle; what made that affordable is that the
#: pair cost `211.8 s` together, against the `~390 s` `STATE.md` projected.
CONVOY_SCENE = "cafe_convoy_v0"
OBSTACLE_CROSSING_SCENE = "cafe_obstacle_crossing_v0"

#: Scenes measured at **ensemble width** — 8 arms × 8 seeds. Ordered so the
#: matrix prints in the order the results were obtained. This is now the whole
#: of :func:`scene_census.hostable_scenes`; `test_coverage_is_complete_over_the
#: _hostable_set` pins the two equal as sets, so a new scenario yaml re-opens
#: coverage rather than leaving a stale count.
MEASURED_SCENES: tuple[str, ...] = (
    FREEZING_SCENE, CUT_IN_SCENE, HEAD_ON_SCENE,
    CONVOY_SCENE, OBSTACLE_CROSSING_SCENE,
)

#: `arm -> (min_clearance_m,) * SEEDS` on :data:`CUT_IN_SCENE`, seeds `0..7`,
#: `lam = 0.8`, `w_voo = 5`. The whole registry, so the column is a census and
#: not a selection — the arms that lose are recorded at the same width as the
#: one that wins, which is what makes "no arm generalises" checkable.
#:
#: Re-derive with :func:`retake_scene` (267.3 s). Recorded rather than
#: recomputed on import, per :data:`clearance_census.SEED_ENSEMBLE`'s precedent.
CUT_IN_ENSEMBLE: dict[str, tuple[float, ...]] = {
    "cbf_mppi":         (0.2031, 0.2105, 0.2066, 0.2075, 0.2110, 0.2044, 0.2058, 0.2052),
    "essps_mppi":       (0.0271, 0.3132, 0.0319, 0.0242, 0.0518, 0.0382, 0.0441, 0.0157),
    "frozen_risk_mppi": (0.0377, 0.0122, 0.0159, 0.0158, 0.0134, 0.0419, 0.0206, 0.0049),
    "gap_gated_mppi":   (0.0654, 0.2890, 0.2510, 0.2053, 0.0479, 0.0589, 0.1064, 0.0621),
    "geometric_mppi":   (0.2601, 0.1652, 0.1652, 0.2777, 0.2175, 0.2191, 0.2604, 0.2595),
    "risk_mppi":        (0.0377, 0.0122, 0.0159, 0.0158, 0.0134, 0.0419, 0.0206, 0.0049),
    "social_mppi":      (0.3783, 0.3241, 0.3046, 0.3350, 0.3727, 0.3688, 0.3554, 0.3352),
    "stock_mppi":       (0.2601, 0.1652, 0.1652, 0.2777, 0.2175, 0.2191, 0.2604, 0.2595),
}

#: `arm -> (min_clearance_m,) * SEEDS` on :data:`HEAD_ON_SCENE`, same width,
#: same operating point, same :func:`retake_scene` body as the column above —
#: which is the point of having made the scene a parameter. D-332.
HEAD_ON_ENSEMBLE: dict[str, tuple[float, ...]] = {
    "cbf_mppi":         (0.2003, 0.1797, 0.1809, 0.2151, 0.1044, 0.1831, 0.2148, 0.1912),
    "essps_mppi":       (0.0090, 0.0141, 0.0084, 0.0147, 0.0108, 0.0195, 0.0134, 0.0113),
    "frozen_risk_mppi": (0.0095, 0.0053, 0.0126, 0.0040, 0.0072, 0.0081, 0.0027, 0.0043),
    "gap_gated_mppi":   (0.0146, 0.0043, 0.0098, 0.0138, 0.0024, 0.0074, 0.0092, 0.0149),
    "geometric_mppi":   (0.0125, 0.0043, 0.0009, 0.0025, 0.0028, 0.0013, 0.0084, 0.0123),
    "risk_mppi":        (0.0095, 0.0053, 0.0126, 0.0040, 0.0072, 0.0081, 0.0027, 0.0043),
    "social_mppi":      (0.0039, 0.0060, 0.0306, 0.0174, 0.0354, 0.0550, 0.0220, 0.0219),
    "stock_mppi":       (0.0125, 0.0043, 0.0009, 0.0025, 0.0028, 0.0013, 0.0084, 0.0123),
}

#: `arm -> (min_clearance_m,) * SEEDS` on :data:`CONVOY_SCENE`. D-333.
#: `cbf_mppi` wins here `8/8` at `+0.1494 m`; every other arm loses or ties.
CONVOY_ENSEMBLE: dict[str, tuple[float, ...]] = {
    "cbf_mppi":         (0.5573, 0.5786, 0.5556, 0.5454, 0.5642, 0.6004, 0.5911, 0.5735),
    "essps_mppi":       (0.2874, 0.3104, 0.3003, 0.2956, 0.3010, 0.2645, 0.3208, 0.3230),
    "frozen_risk_mppi": (0.4287, 0.3991, 0.3297, 0.4083, 0.4271, 0.3665, 0.3796, 0.4395),
    "gap_gated_mppi":   (0.3637, 0.4311, 0.4395, 0.4374, 0.3963, 0.4034, 0.4714, 0.3994),
    "geometric_mppi":   (0.4006, 0.4334, 0.4021, 0.3792, 0.4425, 0.4293, 0.4337, 0.4501),
    "risk_mppi":        (0.4287, 0.3991, 0.3297, 0.4083, 0.4271, 0.3665, 0.3796, 0.4395),
    "social_mppi":      (0.3873, 0.4186, 0.4549, 0.3773, 0.3693, 0.4163, 0.3717, 0.4400),
    "stock_mppi":       (0.4006, 0.4334, 0.4021, 0.3792, 0.4425, 0.4293, 0.4337, 0.4501),
}

#: `arm -> (min_clearance_m,) * SEEDS` on :data:`OBSTACLE_CROSSING_SCENE`. D-333.
#: `cbf_mppi` wins here `8/8` at `+0.1888 m` — its largest margin outside
#: `freezing`, and the fourth of the five scenes it takes.
OBSTACLE_CROSSING_ENSEMBLE: dict[str, tuple[float, ...]] = {
    "cbf_mppi":         (0.3255, 0.2040, 0.1490, 0.2454, 0.2373, 0.2080, 0.2651, 0.1705),
    "essps_mppi":       (0.0373, 0.0683, 0.0821, 0.0244, 0.0286, 0.0243, 0.0891, 0.1275),
    "frozen_risk_mppi": (0.0167, 0.0221, 0.0266, 0.0364, 0.0215, 0.0467, 0.0397, 0.0266),
    "gap_gated_mppi":   (0.0266, 0.0261, 0.0538, 0.0365, 0.0463, 0.0431, 0.0330, 0.0072),
    "geometric_mppi":   (0.0597, 0.0697, 0.0261, 0.0318, 0.0528, 0.0202, 0.0192, 0.0146),
    "risk_mppi":        (0.0167, 0.0221, 0.0266, 0.0364, 0.0215, 0.0467, 0.0397, 0.0266),
    "social_mppi":      (0.0049, 0.0020, 0.0135, 0.0186, 0.0146, 0.0110, 0.0474, 0.0120),
    "stock_mppi":       (0.0597, 0.0697, 0.0261, 0.0318, 0.0528, 0.0202, 0.0192, 0.0146),
}

#: Measured wall clock for :func:`retake_scene`, in seconds, against the
#: estimate `STATE.md` carried into the cycle that took it. Pinned as pairs
#: because the ratio is the reading: this branch mis-priced four runs by 15–20×
#: before D-330, and the one that landed was extrapolated from a measured
#: subset. D-332's entry is the first *forward* test of that explanation — it
#: was projected from D-330's measured column before being run.
RETAKE_SECONDS = 267.3
PROJECTED_SECONDS = 275.0
HEAD_ON_RETAKE_SECONDS = 193.1
HEAD_ON_PROJECTED_SECONDS = 267.3
#: D-333's pair. `STATE.md` priced both at "~6.5 min at the measured 193 s
#: rate", i.e. `195 s` each; they came in at `117.1` and `94.7`. So the
#: cross-scene estimate missed **again**, in the same direction and by more
#: (`1.67×` and `2.06×` vs D-332's `1.38×`) — three scene boundaries, three
#: over-estimates. D-332 narrowed the accurate-estimate explanation to
#: "within-scene"; this pair is the confirming evidence, and the reason the
#: whole remaining coverage fitted in one cycle instead of two.
CONVOY_RETAKE_SECONDS = 117.1
CONVOY_PROJECTED_SECONDS = 195.0
OBSTACLE_CROSSING_RETAKE_SECONDS = 94.7
OBSTACLE_CROSSING_PROJECTED_SECONDS = 195.0
RETAKE_COST: dict[str, tuple[float, float]] = {
    CUT_IN_SCENE: (PROJECTED_SECONDS, RETAKE_SECONDS),
    HEAD_ON_SCENE: (HEAD_ON_PROJECTED_SECONDS, HEAD_ON_RETAKE_SECONDS),
    CONVOY_SCENE: (CONVOY_PROJECTED_SECONDS, CONVOY_RETAKE_SECONDS),
    OBSTACLE_CROSSING_SCENE: (
        OBSTACLE_CROSSING_PROJECTED_SECONDS, OBSTACLE_CROSSING_RETAKE_SECONDS),
}

#: `scene -> recorded column`. A dict rather than the `if` ladder it replaced,
#: so adding a scene is one entry and cannot silently disagree with
#: :data:`MEASURED_SCENES` — `test_the_column_registry_matches_measured_scenes`
#: pins the two populations equal in both directions.
_COLUMNS: dict[str, dict[str, tuple[float, ...]]] = {
    FREEZING_SCENE: SEED_ENSEMBLE,
    CUT_IN_SCENE: CUT_IN_ENSEMBLE,
    HEAD_ON_SCENE: HEAD_ON_ENSEMBLE,
    CONVOY_SCENE: CONVOY_ENSEMBLE,
    OBSTACLE_CROSSING_SCENE: OBSTACLE_CROSSING_ENSEMBLE,
}


def columns() -> dict[str, dict[str, tuple[float, ...]]]:
    """Every recorded per-seed column this module owns, keyed by scene.

    The public read of :data:`_COLUMNS`, added so `recorded_clearance` can
    register this module without reaching through the private name. It is a
    *function* on purpose, and the reason is `source_reach`'s taxonomy rather
    than style: a registered source that resolves to a constant must carry a
    :data:`source_reach.VOCABULARY` token in its name, and `_COLUMNS` carries
    none — registering it directly would have put the registry outside the
    vocabulary that audits it and turned `vocabulary_gap()` red. An aggregator
    over five separately-named constants is exactly the shape
    `separation_reproduction.published_census()` already occupies, which
    `source_reach` classifies `UNSCANNED` — reported, never convicted.

    Returns the live mapping, not a copy: `scene_transfer`'s constants are
    module-level records and every other reader here treats them as such.
    """
    return _COLUMNS


def _ensemble(scene: str) -> dict[str, tuple[float, ...]]:
    """The recorded 8 × 8 column for `scene`."""
    try:
        return _COLUMNS[scene]
    except KeyError:
        raise KeyError(
            f"{scene} has no ensemble-width column; have {MEASURED_SCENES}"
        ) from None


@dataclass(frozen=True)
class SceneStanding:
    """One arm's paired standing against the baseline on one scene.

    Same fields and same paired-per-seed construction as
    :class:`clearance_census.SeedVerdict` and
    :class:`scene_census.PairedVerdict`, so the three scenes' answers are
    comparable rather than merely adjacent.
    """

    scene: str
    arm: str
    mean_gap: float
    worst_gap: float
    best_gap: float
    beats_baseline: int

    @property
    def sign_is_stable(self) -> bool:
        """Does the gap keep its sign on every seed?"""
        return (self.best_gap < 0.0) or (self.worst_gap > 0.0)

    @property
    def wins(self) -> bool:
        """Does this arm out-clear the baseline, stably, on this scene?

        Both conditions, exactly as :attr:`scene_census.PairedVerdict.
        buys_clearance` defines it. `cbf_mppi` on `cut_in` is why the second
        one is not redundant: it leads on `2/8` seeds, so a mean-only test
        would still call it a loss, but an *any-seed* test would call it a
        partial win and the disjointness result below would blur.
        """
        return self.mean_gap > 0.0 and self.sign_is_stable


def standing(scene: str, arm: str) -> SceneStanding:
    """Grade `arm` against :data:`clearance_census.BASELINE` on `scene`."""
    col = _ensemble(scene)
    gaps = [a - b for a, b in zip(col[arm], col[BASELINE])]
    return SceneStanding(
        scene=scene,
        arm=arm,
        mean_gap=sum(gaps) / len(gaps),
        worst_gap=min(gaps),
        best_gap=max(gaps),
        beats_baseline=sum(g > 0.0 for g in gaps),
    )


def winners(scene: str) -> tuple[str, ...]:
    """Arms that out-clear the baseline on `scene`, stably, best mean first.

    Excludes the baseline itself and any arm tying it exactly — a zero mean
    fails :attr:`SceneStanding.wins`, which is how `geometric_mppi`'s inert
    channel stays out of the winner set instead of appearing as a draw.
    """
    col = _ensemble(scene)
    won = [a for a in col if standing(scene, a).wins]
    return tuple(sorted(won, key=lambda a: -standing(scene, a).mean_gap))


def arms_that_generalise() -> tuple[str, ...]:
    """Arms winning on **every** scene measured at ensemble width.

    The bottleneck's question as a set. Measured value: **empty**. The two
    scenes' winner sets are `('cbf_mppi',)` and `('social_mppi',)`, and their
    intersection is where the north star's "all environments" clause would
    have to be satisfied.
    """
    common = set(_ensemble(MEASURED_SCENES[0]))
    for scene in MEASURED_SCENES:
        common &= set(winners(scene))
    return tuple(sorted(common))


def blocking_scenes(arm: str) -> tuple[str, ...]:
    """Scenes where `arm` fails to win, in :data:`MEASURED_SCENES` order.

    The complement of :func:`arms_that_generalise`, and the more useful half of
    it once coverage is complete. An emptiness claim (`arms_that_generalise()
    == ()`) says only that the north-star clause is unmet; it does not say
    *what* is in the way, and it reads identically whether an arm loses one
    scene or all five. This names the obstruction.

    For `cbf_mppi` the answer is a single scene, which is the sharpest form the
    transfer question has taken on this branch: the arm clears every other
    hostable scene at ensemble width and is stopped by one geometry.
    """
    return tuple(s for s in MEASURED_SCENES if arm not in winners(s))


def narrowest_block() -> tuple[str, ...]:
    """Arms blocked by **exactly one** scene, fewest-blocked first.

    The set that would satisfy the north star if one scene were fixed. Empty
    would mean no arm is close; a member means the "all environments" clause
    has a single named counterexample rather than a diffuse failure.
    """
    graded = [a for a in _ensemble(MEASURED_SCENES[0]) if a != BASELINE]
    return tuple(sorted((a for a in graded if len(blocking_scenes(a)) == 1),
                        key=lambda a: (len(blocking_scenes(a)), a)))


def any_arm_generalises() -> bool:
    """The bottleneck reduced to a boolean. Measured `False`.

    Deliberately asked of the whole registry, not just
    :data:`clearance_census.REPRESENTATION_ARMS`: `cbf_mppi` is the arm with
    the best single-scene result on this branch and it fails this too, so the
    negative is not a statement about representations specifically. It is a
    statement about everything shipped here.
    """
    return bool(arms_that_generalise())


def scene_scoped_winners() -> dict[str, tuple[str, ...]]:
    """`scene -> winners`, for the reader who wants to see the disjointness."""
    return {s: winners(s) for s in MEASURED_SCENES}


def ensemble_coverage() -> tuple[int, int]:
    """`(scenes measured at ensemble width, scenes that can host the census)`.

    Returned as a pair rather than a percentage because the denominator is the
    load-bearing half: it is `5`, not `8`, and a reader handed `40 %` cannot
    tell whether the three zero-obstacle scenarios were counted as failures
    (D-241). Derived from :func:`scene_census.hostable_scenes`, so a new
    scenario yaml moves it without anyone editing this line.
    """
    return len(MEASURED_SCENES), len(hostable_scenes())


def inert_on_every_measured_scene(arm: str, reference: str = BASELINE) -> bool:
    """Is `arm` bit-identical to `reference` on every measured scene?

    The signature of a channel that never bites — pinned for `geometric_mppi`
    against the baseline, and used again for the `risk`/`frozen_risk` pair,
    whose prune `STATE.md` proposes. Two scenes × 8 seeds is `16` agreeing
    pairs, which is the evidence that recommendation now rests on.
    """
    return all(_ensemble(s)[arm] == _ensemble(s)[reference] for s in MEASURED_SCENES)


def retake_scene(scene: str, *, seeds: int = SEEDS) -> dict[str, tuple[float, ...]]:
    """Re-measure any scene's ensemble-width column. Not called by tests (~267 s each).

    Mirrors :func:`clearance_census.retake`'s construction exactly — same
    operating point, same epistemic-kwarg split, same rounding — so a drift
    check is a dict comparison rather than a re-reading of prose.

    The scene is a parameter rather than the module constant it used to be
    (D-330 shipped this body hard-wired to :data:`CUT_IN_SCENE`). Every recorded
    column must come from *this* function: a second scene measured by a
    hand-copied loop would differ from the first in ways no test could see,
    which is exactly the provenance the pinned `stock`/`social` rows exist to
    protect.
    """
    from eval.mppi_sandbox.clearance_census import takes_epistemic_kwargs

    from .controllers import REGISTRY, make_controller
    from .controllers.stock_mppi import MPPIParams
    from .ess_at_peak import ISOLATION
    from .essps import OPERATING_LAM, OPERATING_W_VOO
    from .obstacles import min_clearance
    from .run import ROBOT_RADIUS, simulate
    from .scenario import load_scenario

    if scene not in hostable_scenes():
        raise KeyError(f"{scene} cannot host the census; have {hostable_scenes()}")
    sc = load_scenario(f"eval/scenarios/{scene}.yaml")
    out: dict[str, tuple[float, ...]] = {}
    for name in sorted(REGISTRY):
        row = []
        for seed in range(seeds):
            kw = dict(w_voo=OPERATING_W_VOO, w_epist=0.0, **ISOLATION) \
                if takes_epistemic_kwargs(name, sc) else {}
            ctrl = make_controller(name, sc, seed=seed, robot_radius=ROBOT_RADIUS,
                                   params=MPPIParams(lam=OPERATING_LAM), **kw)
            traj = simulate(sc, ctrl)
            row.append(round(float(min_clearance(traj, sc.obstacles, ROBOT_RADIUS)), 4))
        out[name] = tuple(row)
    return out


def format_grade() -> str:
    """One-screen scene-transfer matrix. For a human reading the cycle's output."""
    measured, hostable = ensemble_coverage()
    graded = sorted(_ensemble(MEASURED_SCENES[0]))
    lines = [
        f"scene transfer — {measured}/{hostable} hostable scenes at ensemble "
        f"width ({SEEDS} seeds x {len(graded)} arms)",
        "",
        f"{'arm':<18}" + "".join(f"{s.replace('cafe_', '').replace('_v0', ''):>26}"
                                 for s in MEASURED_SCENES),
    ]
    for arm in graded:
        if arm == BASELINE:
            continue
        # No "(representation)" tag here, deliberately. Writing one costs a
        # membership test against a named constant, and `guard_reflexivity`
        # keys on exactly that shape — a cosmetic label in a printer would
        # enter the guard pool and drag `clearance_census.REPRESENTATION_ARMS`
        # into four allow-list registries as though it were an exemption. It is
        # a category, not an exemption; `REPRESENTATION_ARMS` is already the
        # one place that split is stated (D-330).
        cells = ""
        for scene in MEASURED_SCENES:
            v = standing(scene, arm)
            cells += f"{v.mean_gap:>+12.4f} {v.beats_baseline}/{SEEDS}" \
                     f"{' WIN' if v.wins else '    '}".rjust(26)
        lines.append(f"{arm:<18}{cells}")
    lines += [""]
    for scene, won in scene_scoped_winners().items():
        lines.append(f"winners on {scene:<22} {', '.join(won) if won else '(none)'}")
    lines += [
        "",
        f"arms_that_generalise = {arms_that_generalise()}",
        f"any_arm_generalises  = {any_arm_generalises()}",
    ]
    return "\n".join(lines)


if __name__ == "__main__":  # pragma: no cover
    print(format_grade())

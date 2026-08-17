# SPDX-License-Identifier: BSD-3-Clause
"""Does any arm win on more than one scene? Measured: no. (STATE #1)

D-329 filled one cell of the scene × arm matrix and overturned the branch's
negative result with it: `social_mppi` out-clears plain `stock_mppi` on
`cafe_cut_in_v0` by `+0.1187 m` at `8/8` seeds, where D-328 had measured the
same arm at `0/8` on `cafe_freezing_v0`. That left `STATE.md` with two cells
pointing at *different* arms and an explicit question: does the matrix say
"each channel bites on the situation it encodes" (the representation
hypothesis, confirmed) or "no arm generalises" (nothing built yet)?

This module fills the `cafe_cut_in_v0` column to the same width the `freezing`
column already had — **all eight registry arms at all eight seeds** — and the
matrix answers the second way:

* **`social_mppi` wins `cut_in` `8/8` and loses `freezing` `0/8`.**
* **`cbf_mppi` wins `freezing` `8/8` and loses `cut_in` `2/8`** (mean
  `-0.0213 m`, sign mixed).
* **The two winner sets are disjoint** — :func:`arms_that_generalise` is
  empty, and :func:`any_arm_generalises` is `False`.

So the win that D-329 recorded is real and it does not travel. Every arm this
repo ships, including the constraint arm that is not a representation at all,
out-clears the baseline on at most one of the two scenes measured at ensemble
width. Against the north star's "**all** environments" clause that is the
sharpest negative the branch has: the failure is not that the arms are weak on
average — `social_mppi` beats plain MPPI by `+0.1187 m` on every seed of
`cut_in`, which is a large, stable win — but that **no arm holds its win when
the scene changes**.

Two readings survive the scene change, and both are about the instrument:

* **`geometric_mppi` reproduces `stock_mppi` bit-for-bit on all 8 seeds here
  too.** D-327 pinned that on one seed of `freezing` and D-329 on seed 0 of
  four scenes; it is now pinned across `2 scenes × 8 seeds`. An inert channel
  is the one thing in this registry that is genuinely scene-independent.
* **`risk_mppi` and `frozen_risk_mppi` are identical on all 8 seeds here too.**
  The duplicate pair `STATE.md` proposed pruning now has ensemble-width
  evidence on a second scene: `16` of `16` arm-seed pairs agree to 4 dp.

Scope, before the numbers because it bounds them:

* **Two scenes of the five that can host the census** (`scene_census`'s
  `hostable_scenes()` is 5 of 8; three scenarios declare zero obstacles and the
  question is undefined there). :func:`ensemble_coverage` reports `2/5` rather
  than letting the reader infer it. "No arm generalises" is therefore a
  statement about `cut_in` vs `freezing`, not about the whole scenario set —
  an arm winning on both of the *unmeasured* three is not excluded by anything
  here.
* Same operating point as both prior columns (`lam = 0.8`, `w_voo = 5`,
  :data:`ess_at_peak.ISOLATION`), so the three constants compose rather than
  merely sit next to each other.
* :data:`CUT_IN_ENSEMBLE`'s `stock_mppi` and `social_mppi` rows are the same
  measurement `scene_census.PAIRED_ENSEMBLE` already carries. They are pinned
  equal rather than re-stated — a re-take that moved either goes red here
  instead of quietly disagreeing with D-329's published pair.

Cost, measured 2026-08-17: **267.3 s** for the full `8 × 8`, against the
`~275 s` `STATE.md` projected from the two-arm column. That is the first
inherited estimate on this branch to land inside 3 % — the four before it ran
15–20× long (D-326, Q-159, D-329). The estimate was accurate because it was
extrapolated from a *measured* two-arm run rather than guessed.
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

#: Scenes measured at **ensemble width** — 8 arms × 8 seeds. Ordered so the
#: matrix prints in the order the results were obtained.
MEASURED_SCENES: tuple[str, ...] = (FREEZING_SCENE, CUT_IN_SCENE, HEAD_ON_SCENE)

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
RETAKE_COST: dict[str, tuple[float, float]] = {
    CUT_IN_SCENE: (PROJECTED_SECONDS, RETAKE_SECONDS),
    HEAD_ON_SCENE: (HEAD_ON_PROJECTED_SECONDS, HEAD_ON_RETAKE_SECONDS),
}

#: `scene -> recorded column`. A dict rather than the `if` ladder it replaced,
#: so adding a scene is one entry and cannot silently disagree with
#: :data:`MEASURED_SCENES` — `test_the_column_registry_matches_measured_scenes`
#: pins the two populations equal in both directions.
_COLUMNS: dict[str, dict[str, tuple[float, ...]]] = {
    FREEZING_SCENE: SEED_ENSEMBLE,
    CUT_IN_SCENE: CUT_IN_ENSEMBLE,
    HEAD_ON_SCENE: HEAD_ON_ENSEMBLE,
}


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

# SPDX-License-Identifier: BSD-3-Clause
"""Is `cafe_cut_in_v0` separable from the other four by plan-time observables? (Q-162)

D-333 measured that `cbf_mppi` and `social_mppi` are **exact complements** over
the hostable set: `cut_in` is `cbf`'s only loss and `social`'s only win, so the
union of two shipped arms covers all five scenes. Running that union needs a
switch, and the switch needs to know *at plan time* which scene it is in. Q-162
asks whether that is possible without reading the scene label.

This module measures **separability**, not a classifier. Five scenes is far too
small a sample to fit a discriminant on, and Q-162 said so; what is checkable is
whether any plan-time observable puts `cut_in`'s eight seeds entirely outside
the other thirty-two.

**The answer is yes, and the yes is an oracle.** `cut_in` separates — on
exactly one observable, `obstacle_speed`, and that observable has **zero
within-scene spread**: it takes one value per scene across all eight seeds
(`1.25 / 0.0 / 1.0 / 0.8333 / 0.75`). It is a number copied out of the scenario
yaml, not a reading taken off a rollout. Separating on it is reading the scene
label with extra steps, which is precisely Q-162's option **(C)**.

Strip the constants — :func:`informative_separators` — and `cut_in`'s row
empties. The sole surviving separation in the whole matrix is `min_ttc` on
`cafe_head_on_v0`: a different scene from the one the question is about, and
one the switch does not need, because `cbf_mppi` already wins it. **The scene
D-333 named as the switch's decision point is the one scene these observables
cannot see.**

Two controls ran, and they did not agree — which is why both are recorded:

* **The scene-level control fired only partially.** With five scenes an
  observable that varies by scene puts *some* scene at an extremum, so a
  per-scene separation is cheap and the honest check is to run it on all five
  (:func:`separation_table`). Three of five separate, not five, so
  :func:`separation_is_distinctive` is **True** — `cut_in` separating is not,
  by itself, a vacuous statement. Had the analysis stopped here it would have
  reported qualified support for Q-162's option (A). It stopped one control too
  early.
* **The zero-spread control is the one that produced the verdict.** An
  observable that never moves across eight seeds of the same scene cannot be
  responding to anything the rollout did; it is a scenario parameter wearing an
  observable's clothes. `cut_in`'s only separator is such a parameter, and
  `freezing`'s is the same one. Any future observable must clear this bar
  before its separation counts.
* Even the one informative separation (`min_ttc` / `head_on`) is a threshold
  fitted by eye to five scenes, and says nothing about an **unseen** scene
  falling on the correct side of it.

**Consequence for D-333.** The complement result stands as measured, but its
reading must be downgraded: the union of `cbf_mppi` and `social_mppi` covers
the hostable set *only if someone tells the planner which scene it is in*. On
the evidence here that someone is the yaml file. D-333's "5/5 coverage" is
therefore an upper bound conditioned on an oracle, and the north star's unseen-
distribution clause is untouched by it.

Scope, before the numbers:

* **Baseline arm only** (`stock_mppi`). The switch has to run *before* an arm
  is chosen, so an observable read off `cbf_mppi`'s or `social_mppi`'s rollout
  would presuppose its own answer.
* Same operating point as :func:`scene_transfer.retake_scene` (`lam = 0.8`),
  so the rollouts these observables are read from are the same rollouts the
  `stock_mppi` row of every recorded column came from.
* **Plan-time** means computable online from the robot state and the perceived
  obstacle set at one instant — bearing, closing speed, bearing rate, obstacle
  speed, time-to-collision. Nothing here reads the scenario file's name, its
  acceptance block, or any quantity that needs the episode to have finished.
  The one concession is that each observable is reported at the episode's
  *critical* index (global minimum clearance), which a planner cannot know in
  advance; see the caveat on :data:`OBSERVABLES`.

Re-take with :func:`retake` — 40 baseline rollouts.
"""


from __future__ import annotations

import numpy as np

from .clearance_census import BASELINE, SEEDS
from .scene_transfer import MEASURED_SCENES

#: The scene Q-162 asks about. Named rather than indexed so a reordering of
#: :data:`scene_transfer.MEASURED_SCENES` cannot silently re-aim this module.
QUESTION_SCENE = "cafe_cut_in_v0"

#: Plan-time observables, each reduced to one scalar per (scene, seed) rollout.
#:
#: All five are functions of quantities a planner has online: the robot pose,
#: the obstacle positions and their velocities. None reads the scenario name.
#:
#: **The caveat that bounds them**: each is evaluated at the index of the
#: episode's global minimum clearance, which is only knowable in hindsight. A
#: real switch would have to decide earlier, so these are an *upper bound* on
#: what a plan-time switch could see — if `cut_in` were not separable even here
#: it certainly would not be online. It is separable here, which is why the
#: null (below) rather than this caveat is what settles Q-162.
OBSERVABLES: tuple[str, ...] = (
    "lateralness",     # |sin| of obstacle bearing in the robot frame: 0 head-on, 1 abeam
    "closing_speed",   # -d(clearance)/dt, m/s
    "bearing_rate",    # |d(bearing)/dt|, rad/s — the lateral-crossing signature
    "obstacle_speed",  # |v_obs|, m/s
    "min_ttc",         # min over the episode of clearance / closing speed, s
)

_EPS = 1e-6


def _critical_observables(traj: np.ndarray, obstacles, robot_radius: float) -> dict:
    """The five observables at the episode's minimum-clearance instant.

    `traj` is the (T, 6) array :func:`run.simulate` returns; columns are
    `t, x, y, yaw, v, omega`.
    """
    t, xy, yaw = traj[:, 0], traj[:, 1:3], traj[:, 3]
    # (n_obs, T) surface-to-surface clearance
    clear = np.stack([
        np.linalg.norm(xy - ob.position(t), axis=1) - ob.radius - robot_radius
        for ob in obstacles
    ])
    j, k = np.unravel_index(int(np.argmin(clear)), clear.shape)
    ob = obstacles[j]

    rel = ob.position(t) - xy                      # (T, 2) obstacle in world frame
    bearing = np.arctan2(rel[:, 1], rel[:, 0]) - yaw
    bearing = np.arctan2(np.sin(bearing), np.cos(bearing))   # wrap to (-pi, pi]

    dt = np.gradient(t)
    closing = -np.gradient(clear[j]) / np.maximum(dt, _EPS)
    brate = np.abs(np.gradient(np.unwrap(bearing)) / np.maximum(dt, _EPS))
    ttc = np.where(closing > _EPS, clear[j] / np.maximum(closing, _EPS), np.inf)

    return {
        "lateralness": float(abs(np.sin(bearing[k]))),
        "closing_speed": float(closing[k]),
        "bearing_rate": float(brate[k]),
        "obstacle_speed": float(np.linalg.norm(ob.velocity(float(t[k])))),
        "min_ttc": float(np.min(ttc)),
    }


def retake(*, seeds: int = SEEDS) -> dict[str, dict[str, tuple[float, ...]]]:
    """Re-derive :data:`OBSERVED`. `scene -> observable -> (value,) * seeds`.

    Mirrors :func:`scene_transfer.retake_scene`'s construction — same arm, same
    operating point, same rounding — so the rollouts these observables come off
    are the ones the recorded `stock_mppi` rows came off. Not called by tests.
    """
    from .controllers import make_controller
    from .controllers.stock_mppi import MPPIParams
    from .essps import OPERATING_LAM
    from .run import ROBOT_RADIUS, simulate
    from .scenario import load_scenario

    out: dict[str, dict[str, tuple[float, ...]]] = {}
    for scene in MEASURED_SCENES:
        sc = load_scenario(f"eval/scenarios/{scene}.yaml")
        rows: dict[str, list[float]] = {o: [] for o in OBSERVABLES}
        for seed in range(seeds):
            ctrl = make_controller(BASELINE, sc, seed=seed, robot_radius=ROBOT_RADIUS,
                                   params=MPPIParams(lam=OPERATING_LAM))
            obs = _critical_observables(simulate(sc, ctrl), sc.obstacles, ROBOT_RADIUS)
            for key, value in obs.items():
                rows[key].append(round(value, 4))
        out[scene] = {o: tuple(rows[o]) for o in OBSERVABLES}
    return out


#: `scene -> observable -> (value,) * SEEDS` on the baseline arm, `lam = 0.8`,
#: seeds 0..7. Recorded rather than recomputed on import, per
#: :data:`scene_transfer.CUT_IN_ENSEMBLE`. Re-derive with :func:`retake`
#: (**76.2 s** measured 2026-08-18 — 40 rollouts, one arm).
OBSERVED: dict[str, dict[str, tuple[float, ...]]] = {
    "cafe_freezing_v0": {
        "lateralness":    (0.5584, 0.5316, 0.3987, 0.5026, 0.6218, 0.4184, 0.5351, 0.4690),
        "closing_speed":  (0.0298, -0.0121, 0.0859, -0.0510, -0.0399, 0.0350, 0.0184, 0.0409),
        "bearing_rate":   (1.3707, 1.2787, 1.0811, 1.3322, 1.2975, 1.5826, 1.3777, 1.4132),
        "obstacle_speed": (1.25,) * 8,
        "min_ttc":        (1.3012, 1.4264, 1.3354, 1.2149, 1.2850, 1.1357, 1.0676, 1.2004),
    },
    "cafe_cut_in_v0": {
        "lateralness":    (0.9990, 0.9960, 0.9999, 1.0000, 0.5314, 0.9944, 0.9417, 0.9995),
        "closing_speed":  (0.0025, 0.0048, -0.0542, -0.0275, 0.0424, 0.0104, 0.0171, 0.0018),
        "bearing_rate":   (1.1104, 1.7840, 2.1999, 1.6464, 0.3242, 1.6804, 1.4545, 0.1882),
        "obstacle_speed": (0.0,) * 8,
        "min_ttc":        (1.3645, 1.6842, 1.4138, 1.4867, 1.2716, 1.3770, 1.3365, 1.4094),
    },
    "cafe_head_on_v0": {
        "lateralness":    (0.9836, 0.9825, 0.9982, 0.9943, 0.9896, 0.9957, 0.9993, 0.9980),
        "closing_speed":  (-0.1205, -0.0911, -0.0298, 0.1280, -0.2006, 0.1414, -0.0704, 0.1549),
        "bearing_rate":   (1.3612, 1.3669, 1.3970, 1.5067, 1.8549, 1.9463, 1.8283, 1.5128),
        "obstacle_speed": (1.0,) * 8,
        "min_ttc":        (0.0744, 0.0522, 0.0494, 0.0198, 0.0168, 0.0092, 0.0708, 0.0795),
    },
    "cafe_convoy_v0": {
        "lateralness":    (0.7338, 0.6435, 0.7218, 0.6740, 0.7042, 0.6940, 0.6628, 0.7111),
        "closing_speed":  (-0.0350, 0.0745, -0.0004, 0.0249, 0.0751, -0.0120, 0.0477, -0.0905),
        "bearing_rate":   (0.9437, 0.5920, 1.0841, 0.9037, 0.9597, 0.9907, 1.0037, 1.1057),
        "obstacle_speed": (0.8333,) * 8,
        "min_ttc":        (1.0311, 1.1375, 1.1470, 0.9698, 1.3741, 1.1379, 1.4539, 1.2512),
    },
    "cafe_obstacle_crossing_v0": {
        "lateralness":    (0.7070, 0.6644, 0.7418, 0.7999, 0.7628, 0.7566, 0.7886, 0.7511),
        "closing_speed":  (0.0089, -0.0340, -0.0593, 0.0017, 0.0598, 0.0328, 0.0125, 0.0161),
        "bearing_rate":   (1.2871, 1.6683, 1.2598, 1.2760, 1.1724, 0.9886, 1.6091, 1.0946),
        "obstacle_speed": (0.75,) * 8,
        "min_ttc":        (0.3298, 0.2984, 0.1809, 0.2220, 0.2858, 0.1547, 0.1449, 0.1454),
    },
}

#: The recorded verdict of :func:`separation_table` — every scene separates,
#: and every one of them on the same constant. Pinned so a re-take that changes
#: any row goes red rather than quietly re-answering Q-162.
SEPARATION: dict[str, tuple[str, ...]] = {
    "cafe_freezing_v0": ("obstacle_speed",),
    "cafe_cut_in_v0": ("obstacle_speed",),
    "cafe_head_on_v0": ("min_ttc",),
    "cafe_convoy_v0": (),
    "cafe_obstacle_crossing_v0": (),
}

#: The separators that survive :func:`constant_observables` — the whole
#: informative content of the matrix. One entry, and it is not `cut_in`'s.
INFORMATIVE_SEPARATION: dict[str, tuple[str, ...]] = {
    "cafe_freezing_v0": (),
    "cafe_cut_in_v0": (),
    "cafe_head_on_v0": ("min_ttc",),
    "cafe_convoy_v0": (),
    "cafe_obstacle_crossing_v0": (),
}


def separates(scene: str, observable: str) -> bool:
    """True iff `scene`'s seeds lie entirely outside the other scenes' range.

    A strict, gap-free reading: no overlap at all, in either direction. This is
    the most generous test a threshold switch could ask for — it is exactly the
    condition under which *some* constant separates that scene from the rest of
    the measured set.
    """
    mine = np.asarray(OBSERVED[scene][observable], dtype=float)
    rest = np.concatenate([np.asarray(OBSERVED[s][observable], dtype=float)
                           for s in MEASURED_SCENES if s != scene])
    finite = np.isfinite(mine).all() and np.isfinite(rest).all()
    if not finite:                      # an infinite TTC separates nothing usefully
        return False
    return bool(mine.max() < rest.min() or mine.min() > rest.max())


def separating_observables(scene: str) -> tuple[str, ...]:
    """The observables that separate `scene` from the other four, in registry order."""
    return tuple(o for o in OBSERVABLES if separates(scene, o))


def separation_table() -> dict[str, tuple[str, ...]]:
    """`scene -> separating observables`, for all five. **This is the control.**

    Reading only the `QUESTION_SCENE` row answers "is `cut_in` separable" with a
    yes and stops there. The other four rows are what say whether that yes
    carries information: if every scene is separable, the separation is a
    property of *having five different scenarios*, not of `cut_in`.
    """
    return {s: separating_observables(s) for s in MEASURED_SCENES}


def scenes_that_separate() -> tuple[str, ...]:
    """Scenes separated by at least one observable. Empty ⇒ no switch is possible."""
    return tuple(s for s in MEASURED_SCENES if separating_observables(s))


def constant_observables() -> tuple[str, ...]:
    """Observables with **zero within-scene spread** in every measured scene.

    These are scenario parameters wearing an observable's clothes: eight seeds
    of the same scene produce eight identical values, so the number cannot be
    responding to anything the rollout did. A separation carried by one of
    these is an oracle read — Q-162's option (C) — and the whole point of
    naming the population is that the verdict below can subtract it.
    """
    out = []
    for observable in OBSERVABLES:
        spreads = [max(OBSERVED[s][observable]) - min(OBSERVED[s][observable])
                   for s in MEASURED_SCENES]
        if all(spread == 0.0 for spread in spreads):
            out.append(observable)
    return tuple(out)


def informative_separators(scene: str) -> tuple[str, ...]:
    """:func:`separating_observables` minus :func:`constant_observables`."""
    constants = set(constant_observables())
    return tuple(o for o in separating_observables(scene) if o not in constants)


def scenes_that_separate_informatively() -> tuple[str, ...]:
    """Scenes a *rollout-derived* observable separates. The honest table."""
    return tuple(s for s in MEASURED_SCENES if informative_separators(s))


def separation_is_distinctive() -> bool:
    """Is `cut_in`'s separability evidence *about `cut_in`*?

    True only if `cut_in` separates and at least one other scene does **not**.
    False when every scene separates — the separation is then a restatement of
    "the scenes differ" and cannot support Q-162's option (A).
    """
    return bool(separating_observables(QUESTION_SCENE)
                and len(scenes_that_separate()) < len(MEASURED_SCENES))


def question_scene_is_informatively_separable() -> bool:
    """**The Q-162 verdict.** False ⇒ option (C): the switch needs the label.

    Deliberately named for the scene rather than for the answer, so a later
    cycle that makes some channel bite reads this as a question it can flip
    rather than as a settled negative.
    """
    return bool(informative_separators(QUESTION_SCENE))


def format_grade() -> str:
    """One-screen separation table. For a human reading the cycle's output."""
    constants = constant_observables()
    lines = ["scene                      separating / informative"]
    for scene in MEASURED_SCENES:
        mark = " <- Q-162" if scene == QUESTION_SCENE else ""
        lines.append(f"  {scene:<24} "
                     f"{', '.join(separating_observables(scene)) or '(none)':<30}"
                     f"{', '.join(informative_separators(scene)) or '(none)'}{mark}")
    lines.append(f"constant_observables (oracle reads) = {constants}")
    lines.append(f"scenes_that_separate                = "
                 f"{len(scenes_that_separate())}/{len(MEASURED_SCENES)}")
    lines.append(f"scenes_that_separate_informatively  = "
                 f"{scenes_that_separate_informatively()}")
    lines.append(f"separation_is_distinctive           = {separation_is_distinctive()}")
    lines.append(f"question_scene_is_informatively_separable = "
                 f"{question_scene_is_informatively_separable()}")
    return "\n".join(lines)


if __name__ == "__main__":  # pragma: no cover - measurement entry point
    import json
    import sys
    if "--retake" in sys.argv:
        print(json.dumps(retake(), indent=1))
    else:
        print(format_grade())

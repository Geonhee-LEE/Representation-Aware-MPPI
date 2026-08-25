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

**D-335 — the reading survives the index.** The caveat above was the one
objection that could have overturned the negative: read at the critical
instant, `cut_in`'s invisibility might have been an artefact of reading *late*.
It is not. :data:`CAUSAL_OBSERVED` holds the same five observables read at two
**causally available** indices off the same 40 rollouts — `first_detection`
(the instant an obstacle enters :data:`DETECTION_RADIUS`, which is when a
switch would actually have to fire) and `fixed_time` (1 s in, the dumb
control) — and `cut_in`'s row is empty at both:
:func:`policies_that_separate_question_scene` is `()`.

Two things sharpen rather than merely repeat D-334:

* **The causal rows are empty *before* the constant filter runs.** At the
  critical instant `cut_in` did separate, on `obstacle_speed = 0.0`, and the
  verdict needed :func:`constant_observables` to strike it out. At both causal
  indices there is nothing to strike out. The reason is worth stating plainly:
  at the critical instant the nearest obstacle is a *static* one, so the
  constant read `0.0` and was unique; at first detection the nearest obstacle
  is the moving one at `0.75`, a value `cafe_obstacle_crossing_v0` also
  carries. D-334 called the separator a scenario parameter — it was a
  parameter of an obstacle the switch would not even have been looking at.
* **The policy control fires red, and is kept red.**
  :func:`causal_policies_agree` is **False**: the two indices disagree about
  `freezing` and about `head_on`. So the table as a whole *is*
  index-dependent, and no row of it may be quoted without naming its index.
  What survives is the narrow claim — :func:`policies_agree_on_question_scene`
  — that all three indices agree about `cut_in` specifically. The two are
  pinned separately so the narrow agreement cannot be read as a general one.

The consequence for D-333 is therefore not softened but hardened: the switch
its complement result needs cannot be built from this observable set at any
index measured, and the remaining question is about the *observables*, not
about when they are read.

**D-336 — the observable set was asked the question, and the answer generalises
past the one channel.** D-335 left a named next move: add a `cut_in`-specific
channel. The obvious candidate is `path_lateral_speed`, the obstacle's velocity
component *across* the reference path — the quantity a lateral cut-in is
supposed to be made of, and one with a route to non-zero spread that
`obstacle_speed` lacked, since `cut_in`'s pedestrian is **piecewise** (2 s
perpendicular, then a turn to travel along the robot's line).

Measured on the same 40 rollouts, it fails on **both** counts:

* it **never separates** `cut_in` at any index — at the causal indices it reads
  `0.75`, exactly the value `cafe_obstacle_crossing_v0` carries, and at the
  critical index it reads `0.0`, exactly `cafe_head_on_v0`'s;
* and where it *does* separate (`freezing` at all three indices, `head_on` at
  the causal ones) it has **zero within-scene spread**, so
  :func:`constant_observables` strikes it out and the informative tables are
  bit-identical to D-335's.

The general statement is the part worth carrying, and it is pinned as
:data:`OBSTACLE_SIDE_OBSERVABLES`: **every observable built from the obstacle's
scripted velocity and the reference path is a yaml constant in this suite, by
construction.** The obstacle schedules are piecewise-linear and the paths are
fixed polylines, so whichever segment the read index falls in supplies a
literal; seed moves the index but not the segment. A third channel of the same
shape would inherit the same defect, so the remaining route to a `cut_in`
separator must read something the **robot** did — and the robot-side channels
already in the set (`lateralness`, `closing_speed`, `bearing_rate`) are the ones
measured not to separate it.

Re-take with :func:`retake_observables` — 40 baseline rollouts, all three
policies and all six observables in one pass (**76.1 s** measured 2026-08-18).
The 15 pre-existing (scene, policy) columns reproduced **exactly**, so D-336 is
a widening of the table and not a re-measurement of it.
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
    "path_lateral_speed",  # |v_obs . n_path|, m/s — D-336's cut-in-specific channel
    "min_ttc",         # min over the episode of clearance / closing speed, s
)

#: The index policies the observables are read at. `critical` is the hindsight
#: reading D-334 measured; the other two are **causally available** — an online
#: switch could compute them at the instant they name.
#:
#: * `critical` — the episode's global minimum-clearance instant, over all
#:   obstacles. Hindsight twice over: it needs the episode to have finished to
#:   know *when*, and to know *which obstacle*.
#: * `first_detection` — the first index at which any obstacle's surface
#:   clearance falls within :data:`DETECTION_RADIUS`. This is the instant a
#:   switch would actually have to fire at: the obstacle has just become
#:   visible and no arm has been committed to yet.
#: * `fixed_time` — the index nearest :data:`FIXED_TIME` seconds. The dumbest
#:   possible causal policy, included as the control on `first_detection`: if
#:   the two disagree, the reading is a property of the *policy* rather than of
#:   the scene.
INDEX_POLICIES: tuple[str, ...] = ("critical", "first_detection", "fixed_time")

#: Surface-to-surface clearance, metres, at which `first_detection` fires.
#: Chosen as a plausible short-range sensing horizon, not fitted — see the
#: sensitivity note on :data:`CAUSAL_OBSERVED`.
DETECTION_RADIUS = 2.0

#: Seconds into the episode that `fixed_time` reads at.
FIXED_TIME = 1.0

#: The causal counterpart of :data:`OBSERVABLES`. Four names are identical and
#: differ only in the index they are read at; `min_ttc` has **no** causal
#: counterpart — an episode-wide minimum is hindsight by construction — so
#: `ttc`, the instantaneous time-to-collision at the read index, replaces it.
#: Renamed rather than reused so no later cycle can line the two tables up by
#: column name and compare quantities that are not the same quantity.
CAUSAL_OBSERVABLES: tuple[str, ...] = (
    "lateralness",
    "closing_speed",
    "bearing_rate",
    "obstacle_speed",
    "path_lateral_speed",
    "ttc",
)

_EPS = 1e-6


def _path_normal(waypoints: np.ndarray, xy: np.ndarray) -> np.ndarray:
    """(2,) unit normal to the reference path at the point nearest `xy`.

    The path is the scenario's polyline, so the tangent is taken from the
    segment whose endpoint is nearest the robot and the normal is that tangent
    rotated a quarter turn. Both signs are equally correct — the observable
    takes an absolute value — so no orientation convention is fixed here.

    Plan-time by the same standard as everything else in :data:`OBSERVABLES`:
    the reference path is an *input* to the planner, not a property of the
    episode, so reading its local direction needs nothing the robot does not
    already hold at `t = 0`.
    """
    pts = np.asarray(waypoints, dtype=float)[:, :2]
    if len(pts) < 2:                       # degenerate path: no direction to read
        return np.zeros(2)
    i = int(np.argmin(np.linalg.norm(pts - xy, axis=1)))
    j = i + 1 if i + 1 < len(pts) else i - 1
    seg = pts[max(i, j)] - pts[min(i, j)]
    norm = float(np.linalg.norm(seg))
    if norm < _EPS:                        # duplicated waypoints
        return np.zeros(2)
    tangent = seg / norm
    return np.array([-tangent[1], tangent[0]])


def _path_lateral_speed(ob, t: float, waypoints: np.ndarray,
                        xy: np.ndarray) -> float:
    """|component of `ob`'s velocity across the reference path| at time `t`.

    **Why this channel and not `obstacle_speed`.** D-334 killed `obstacle_speed`
    because it is a yaml scalar: one value per scene across all eight seeds. The
    projection here is not automatically free of that defect — for an obstacle on
    a straight schedule crossing a straight path, `|v . n|` is just as constant.
    What makes it a different question is that `cafe_cut_in_v0`'s pedestrian is
    **piecewise**: it walks perpendicular to the robot's line for 2 s and then
    turns to travel *along* it, so its cross-path component collapses from ~0.75
    to ~0 partway through the episode. Whether the reading catches that depends
    on *when* the read index falls, which varies seed to seed — so unlike
    `obstacle_speed` this observable has a route to non-zero within-scene spread.
    It is graded by the same :func:`is_constant` bar regardless; the point is that
    the bar can now come out either way rather than being decided by construction.
    """
    n = _path_normal(waypoints, xy)
    return float(abs(np.dot(ob.velocity(t), n)))


def _critical_observables(traj: np.ndarray, obstacles, robot_radius: float,
                          waypoints: np.ndarray) -> dict:
    """The six observables at the episode's minimum-clearance instant.

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
        "path_lateral_speed": _path_lateral_speed(ob, float(t[k]), waypoints, xy[k]),
        "min_ttc": float(np.min(ttc)),
    }


def _clearance(traj: np.ndarray, obstacles, robot_radius: float) -> np.ndarray:
    """(n_obs, T) surface-to-surface clearance. The one geometry both readers share."""
    t, xy = traj[:, 0], traj[:, 1:3]
    return np.stack([
        np.linalg.norm(xy - ob.position(t), axis=1) - ob.radius - robot_radius
        for ob in obstacles
    ])


def _causal_index(clear: np.ndarray, t: np.ndarray, policy: str) -> int:
    """The index `policy` reads at, using only information available *by* that index.

    Both policies are prefix-determined: whether index `k` fires depends on
    `clear[:, :k+1]` and `t[:k+1]` alone, never on the future. That is the
    whole content of the word "causal" here, and it is what the hindsight
    `critical` reader violates.

    Falls back to the last index when the condition never fires, so every
    rollout yields a reading and no scene silently drops seeds — a missing seed
    would change the separation ranges without any test noticing.
    """
    if policy == "first_detection":
        hit = np.flatnonzero(clear.min(axis=0) <= DETECTION_RADIUS)
        return int(hit[0]) if hit.size else int(len(t) - 1)
    if policy == "fixed_time":
        return int(np.argmin(np.abs(t - FIXED_TIME)))
    raise ValueError(f"not a causal policy: {policy!r}")


def _observables_at(traj: np.ndarray, obstacles, robot_radius: float, k: int,
                    waypoints: np.ndarray) -> dict:
    """The six causal observables at index `k`.

    Two differences from :func:`_critical_observables`, both required for the
    reading to be causal rather than merely re-indexed:

    * the obstacle is the nearest one **at `k`**, not the one that turns out to
      be nearest eventually;
    * the derivatives are **backward** differences. `np.gradient` is centred,
      so it reads `k + 1` — a one-step look into the future that would smuggle
      hindsight back in through the closing speed and the bearing rate.
    """
    t, xy, yaw = traj[:, 0], traj[:, 1:3], traj[:, 3]
    clear = _clearance(traj, obstacles, robot_radius)
    j = int(np.argmin(clear[:, k]))
    ob = obstacles[j]

    rel = ob.position(t) - xy
    bearing = np.arctan2(rel[:, 1], rel[:, 0]) - yaw
    bearing = np.arctan2(np.sin(bearing), np.cos(bearing))

    p = max(k - 1, 0)                      # backward step; forward-degenerate at k=0
    dt = max(float(t[k] - t[p]), _EPS)
    closing = float(-(clear[j][k] - clear[j][p]) / dt)
    unwrapped = np.unwrap(bearing)
    brate = float(abs((unwrapped[k] - unwrapped[p]) / dt))
    ttc = float(clear[j][k] / closing) if closing > _EPS else float("inf")

    return {
        "lateralness": float(abs(np.sin(bearing[k]))),
        "closing_speed": closing,
        "bearing_rate": brate,
        "obstacle_speed": float(np.linalg.norm(ob.velocity(float(t[k])))),
        "path_lateral_speed": _path_lateral_speed(ob, float(t[k]), waypoints, xy[k]),
        "ttc": ttc,
    }


def retake_observables(*, seeds: int = SEEDS) -> dict[str, dict]:
    """Re-derive :data:`OBSERVED` **and** :data:`CAUSAL_OBSERVED` in one pass.

    Returns `policy -> scene -> observable -> (value,) * seeds`, keyed by
    :data:`INDEX_POLICIES`. All three policies are read off the *same* 40
    rollouts, which is what makes the comparison between them a comparison of
    read indices and not of two separate measurements.

    Mirrors :func:`scene_transfer.retake_scene`'s construction — same arm, same
    operating point, same rounding — so the rollouts these observables come off
    are the ones the recorded `stock_mppi` rows came off. Not called by tests.
    """
    from .controllers import make_controller
    from .controllers.stock_mppi import MPPIParams
    from .essps import OPERATING_LAM
    from .run import ROBOT_RADIUS, simulate
    from .scenario import load_scenario

    out: dict[str, dict] = {p: {} for p in INDEX_POLICIES}
    for scene in MEASURED_SCENES:
        sc = load_scenario(f"eval/scenarios/{scene}.yaml")
        rows: dict[str, dict[str, list[float]]] = {
            p: {o: [] for o in (OBSERVABLES if p == "critical" else CAUSAL_OBSERVABLES)}
            for p in INDEX_POLICIES
        }
        for seed in range(seeds):
            ctrl = make_controller(BASELINE, sc, seed=seed, robot_radius=ROBOT_RADIUS,
                                   params=MPPIParams(lam=OPERATING_LAM))
            traj = simulate(sc, ctrl)
            clear = _clearance(traj, sc.obstacles, ROBOT_RADIUS)
            for policy in INDEX_POLICIES:
                if policy == "critical":
                    obs = _critical_observables(traj, sc.obstacles, ROBOT_RADIUS,
                                                sc.waypoints)
                else:
                    k = _causal_index(clear, traj[:, 0], policy)
                    obs = _observables_at(traj, sc.obstacles, ROBOT_RADIUS, k,
                                          sc.waypoints)
                for key, value in obs.items():
                    rows[policy][key].append(round(value, 4))
        for policy in INDEX_POLICIES:
            out[policy][scene] = {o: tuple(v) for o, v in rows[policy].items()}
    return out


#: `scene -> observable -> (value,) * SEEDS` on the baseline arm, `lam = 0.8`,
#: seeds 0..7. Recorded rather than recomputed on import, per
#: :data:`scene_transfer.CUT_IN_ENSEMBLE`. Re-derive with :func:`retake_observables`
#: (**76.2 s** measured 2026-08-18 — 40 rollouts, one arm).
OBSERVED: dict[str, dict[str, tuple[float, ...]]] = {
    "cafe_freezing_v0": {
        "lateralness":    (0.5584, 0.5316, 0.3987, 0.5026, 0.6218, 0.4184, 0.5351, 0.4690),
        "closing_speed":  (0.0298, -0.0121, 0.0859, -0.0510, -0.0399, 0.0350, 0.0184, 0.0409),
        "bearing_rate":   (1.3707, 1.2787, 1.0811, 1.3322, 1.2975, 1.5826, 1.3777, 1.4132),
        "obstacle_speed": (1.25,) * 8,
        "path_lateral_speed": (1.25,) * 8,
        "min_ttc":        (1.3012, 1.4264, 1.3354, 1.2149, 1.2850, 1.1357, 1.0676, 1.2004),
    },
    "cafe_cut_in_v0": {
        "lateralness":    (0.9990, 0.9960, 0.9999, 1.0000, 0.5314, 0.9944, 0.9417, 0.9995),
        "closing_speed":  (0.0025, 0.0048, -0.0542, -0.0275, 0.0424, 0.0104, 0.0171, 0.0018),
        "bearing_rate":   (1.1104, 1.7840, 2.1999, 1.6464, 0.3242, 1.6804, 1.4545, 0.1882),
        "obstacle_speed": (0.0,) * 8,
        "path_lateral_speed": (0.0,) * 8,
        "min_ttc":        (1.3645, 1.6842, 1.4138, 1.4867, 1.2716, 1.3770, 1.3365, 1.4094),
    },
    "cafe_head_on_v0": {
        "lateralness":    (0.9836, 0.9825, 0.9982, 0.9943, 0.9896, 0.9957, 0.9993, 0.9980),
        "closing_speed":  (-0.1205, -0.0911, -0.0298, 0.1280, -0.2006, 0.1414, -0.0704, 0.1549),
        "bearing_rate":   (1.3612, 1.3669, 1.3970, 1.5067, 1.8549, 1.9463, 1.8283, 1.5128),
        "obstacle_speed": (1.0,) * 8,
        "path_lateral_speed": (0.0,) * 8,
        "min_ttc":        (0.0744, 0.0522, 0.0494, 0.0198, 0.0168, 0.0092, 0.0708, 0.0795),
    },
    "cafe_convoy_v0": {
        "lateralness":    (0.7338, 0.6435, 0.7218, 0.6740, 0.7042, 0.6940, 0.6628, 0.7111),
        "closing_speed":  (-0.0350, 0.0745, -0.0004, 0.0249, 0.0751, -0.0120, 0.0477, -0.0905),
        "bearing_rate":   (0.9437, 0.5920, 1.0841, 0.9037, 0.9597, 0.9907, 1.0037, 1.1057),
        "obstacle_speed": (0.8333,) * 8,
        "path_lateral_speed": (0.8333,) * 8,
        "min_ttc":        (1.0311, 1.1375, 1.1470, 0.9698, 1.3741, 1.1379, 1.4539, 1.2512),
    },
    "cafe_obstacle_crossing_v0": {
        "lateralness":    (0.7070, 0.6644, 0.7418, 0.7999, 0.7628, 0.7566, 0.7886, 0.7511),
        "closing_speed":  (0.0089, -0.0340, -0.0593, 0.0017, 0.0598, 0.0328, 0.0125, 0.0161),
        "bearing_rate":   (1.2871, 1.6683, 1.2598, 1.2760, 1.1724, 0.9886, 1.6091, 1.0946),
        "obstacle_speed": (0.75,) * 8,
        "path_lateral_speed": (0.75,) * 8,
        "min_ttc":        (0.3298, 0.2984, 0.1809, 0.2220, 0.2858, 0.1547, 0.1449, 0.1454),
    },
}

#: `policy -> scene -> observable -> (value,) * SEEDS` at the two **causal**
#: index policies, read off the same 40 rollouts as :data:`OBSERVED` in one
#: pass of :func:`retake_observables`. Recorded rather than recomputed on
#: import, per :data:`OBSERVED`.
#:
#: The `critical` policy is deliberately **absent** from this dict: its table is
#: :data:`OBSERVED`, and duplicating it here would let a re-take move one copy
#: and not the other.
CAUSAL_OBSERVED: dict[str, dict[str, dict[str, tuple[float, ...]]]] = {
    "first_detection": {
        "cafe_freezing_v0": {
            "lateralness": (0.67, 0.7167, 0.7305, 0.7081, 0.7053, 0.6972, 0.7011, 0.7605),
            "closing_speed": (1.1576, 1.0872, 1.0031, 1.2458, 1.1995, 1.0053, 1.0675, 1.2665),
            "bearing_rate": (0.6848, 0.361, 0.2309, 0.5145, 0.3647, 0.1029, 0.0652, 0.1807),
            "obstacle_speed": (1.25,) * 8,
            "path_lateral_speed": (1.25,) * 8,
            "ttc": (1.6587, 1.7825, 1.9317, 1.5252, 1.5979, 1.9512, 1.7997, 1.4973),
        },
        "cafe_cut_in_v0": {
            "lateralness": (0.6265, 0.6574, 0.611, 0.6519, 0.6601, 0.6777, 0.6313, 0.6326),
            "closing_speed": (0.6412, 0.6361, 0.6436, 0.637, 0.6356, 0.6325, 0.6405, 0.6402),
            "bearing_rate": (0.1708, 0.1684, 0.4174, 0.005, 0.0494, 0.1689, 0.3401, 0.2229),
            "obstacle_speed": (0.75,) * 8,
            "path_lateral_speed": (0.75,) * 8,
            "ttc": (3.0713, 3.0971, 3.0594, 3.0923, 3.0994, 3.1154, 3.0752, 3.0763),
        },
        "cafe_head_on_v0": {
            "lateralness": (0.3904, 0.3538, 0.4211, 0.4648, 0.4574, 0.3476, 0.5838, 0.3694),
            "closing_speed": (1.4895, 1.45, 1.3646, 1.4175, 1.4067, 1.4919, 1.2874, 1.3572),
            "bearing_rate": (0.7137, 0.7085, 0.5518, 0.9052, 0.4214, 0.5214, 0.3404, 0.3685),
            "obstacle_speed": (1.0,) * 8,
            "path_lateral_speed": (0.0,) * 8,
            "ttc": (1.296, 1.2994, 1.4342, 1.3513, 1.3768, 1.3131, 1.4989, 1.466),
        },
        "cafe_convoy_v0": {
            "lateralness": (0.6632, 0.6122, 0.5932, 0.8258, 0.7632, 0.5146, 0.7658, 0.6431),
            "closing_speed": (0.7213, 0.5733, 0.7641, 0.7456, 0.7854, 0.691, 0.8574, 0.5941),
            "bearing_rate": (0.6533, 0.3208, 0.2629, 0.2174, 0.0869, 0.9157, 0.3033, 0.0201),
            "obstacle_speed": (0.8333,) * 8,
            "path_lateral_speed": (0.8333,) * 8,
            "ttc": (2.6914, 3.4714, 2.5795, 2.6698, 2.477, 2.7983, 2.2738, 3.2671),
        },
        "cafe_obstacle_crossing_v0": {
            "lateralness": (0.8944, 0.909, 0.9088, 0.8395, 0.8974, 0.816, 0.8799, 0.8254),
            "closing_speed": (0.9384, 0.9275, 0.861, 0.9415, 0.869, 1.0189, 0.9814, 1.0488),
            "bearing_rate": (0.4163, 0.0659, 0.0962, 0.4422, 0.3878, 0.3464, 0.1457, 0.0512),
            "obstacle_speed": (0.75,) * 8,
            "path_lateral_speed": (0.75,) * 8,
            "ttc": (2.0907, 2.1128, 2.3225, 2.0405, 2.2966, 1.8686, 2.012, 1.8869),
        },
    },
    "fixed_time": {
        "cafe_freezing_v0": {
            "lateralness": (0.4776, 0.6608, 0.5468, 0.6003, 0.4483, 0.5575, 0.5018, 0.6373),
            "closing_speed": (1.0773, 0.9199, 1.0473, 1.0663, 0.9093, 0.9407, 0.9516, 0.9995),
            "bearing_rate": (0.6463, 0.0073, 0.2411, 0.4869, 0.3841, 0.4211, 0.8184, 0.5481),
            "obstacle_speed": (1.25,) * 8,
            "path_lateral_speed": (1.25,) * 8,
            "ttc": (1.2365, 1.5208, 1.3726, 1.286, 1.5755, 1.5586, 1.4813, 1.3365),
        },
        "cafe_cut_in_v0": {
            "lateralness": (0.5479, 0.5451, 0.5119, 0.4362, 0.5163, 0.5527, 0.5788, 0.5896),
            "closing_speed": (0.6968, 0.8004, 0.784, 0.661, 0.7622, 0.6179, 0.6003, 0.7329),
            "bearing_rate": (0.5908, 0.3654, 0.2104, 0.1086, 0.2097, 0.2646, 0.138, 0.0797),
            "obstacle_speed": (0.75,) * 8,
            "path_lateral_speed": (0.75,) * 8,
            "ttc": (2.0275, 1.6939, 1.7024, 2.0595, 1.855, 2.2806, 2.3677, 1.8265),
        },
        "cafe_head_on_v0": {
            "lateralness": (0.0405, 0.0939, 0.0703, 0.106, 0.064, 0.1379, 0.0585, 0.0201),
            "closing_speed": (1.3023, 1.5134, 1.3087, 1.1989, 1.4962, 1.2503, 1.3935, 1.2695),
            "bearing_rate": (0.0244, 0.4434, 0.0818, 0.0064, 0.2763, 0.0509, 0.2402, 0.0013),
            "obstacle_speed": (1.0,) * 8,
            "path_lateral_speed": (0.0,) * 8,
            "ttc": (2.7866, 2.3134, 2.7044, 2.9623, 2.3339, 2.9183, 2.5558, 2.8279),
        },
        "cafe_convoy_v0": {
            "lateralness": (0.7428, 0.6951, 0.6142, 0.8133, 0.7688, 0.7127, 0.7849, 0.6527),
            "closing_speed": (0.7275, 0.5694, 0.6928, 0.816, 0.8543, 0.6313, 0.8484, 0.7678),
            "bearing_rate": (0.6303, 0.5053, 0.4754, 0.4525, 0.0484, 0.7019, 0.0974, 0.3114),
            "obstacle_speed": (0.8333,) * 8,
            "path_lateral_speed": (0.8333,) * 8,
            "ttc": (2.8576, 3.8229, 2.9552, 2.531, 2.3692, 3.3807, 2.399, 2.6941),
        },
        "cafe_obstacle_crossing_v0": {
            "lateralness": (0.8632, 0.8964, 0.8934, 0.7909, 0.8692, 0.7457, 0.8553, 0.8439),
            "closing_speed": (1.0048, 0.9402, 0.8779, 0.979, 0.9952, 0.8805, 0.9739, 1.0223),
            "bearing_rate": (0.4192, 0.0539, 0.4898, 0.16, 0.4386, 0.045, 0.5107, 0.0541),
            "obstacle_speed": (0.75,) * 8,
            "path_lateral_speed": (0.75,) * 8,
            "ttc": (2.1463, 2.2771, 2.4695, 2.1627, 2.1867, 2.4952, 2.2318, 2.1348),
        },
    },
}


#: The recorded verdict of :func:`separation_table` — every scene separates,
#: and every one of them on the same constant. Pinned so a re-take that changes
#: any row goes red rather than quietly re-answering Q-162.
SEPARATION: dict[str, tuple[str, ...]] = {
    "cafe_freezing_v0": ("obstacle_speed", "path_lateral_speed"),
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


def _table(table: dict | None) -> dict:
    """`table` or :data:`OBSERVED`, resolved at call time.

    Resolved here rather than in a default argument so `monkeypatch.setattr(sep,
    "OBSERVED", ...)` still reaches every operator — the synthetic-table tests
    are what say *what the no-overlap rule means*, and a default bound at
    import would have quietly detached them from the code they document.
    """
    return OBSERVED if table is None else table


def separates(scene: str, observable: str, table: dict | None = None) -> bool:
    """True iff `scene`'s seeds lie entirely outside the other scenes' range.

    A strict, gap-free reading: no overlap at all, in either direction. This is
    the most generous test a threshold switch could ask for — it is exactly the
    condition under which *some* constant separates that scene from the rest of
    the measured set.

    `table` selects which reading to apply the rule to: the default hindsight
    :data:`OBSERVED`, or one of :data:`CAUSAL_OBSERVED`'s causal tables. The
    *rule* is identical across all three — only the index the numbers were read
    at differs, which is the whole design of the comparison.
    """
    tbl = _table(table)
    mine = np.asarray(tbl[scene][observable], dtype=float)
    rest = np.concatenate([np.asarray(tbl[s][observable], dtype=float)
                           for s in MEASURED_SCENES if s != scene])
    finite = np.isfinite(mine).all() and np.isfinite(rest).all()
    if not finite:                      # an infinite TTC separates nothing usefully
        return False
    return bool(mine.max() < rest.min() or mine.min() > rest.max())


def _observables_of(table: dict | None) -> tuple[str, ...]:
    """The registry the columns of `table` are drawn from.

    Read off the table rather than passed in, because the two registries differ
    by one column (`min_ttc` vs `ttc`) and a caller that named the wrong one
    would get a silent `KeyError`-free empty row — a separation of `()` that
    reads exactly like a measured negative.
    """
    if table is None:
        return OBSERVABLES
    present = table[MEASURED_SCENES[0]]
    seen: dict[str, None] = {}          # dedupe: the two registries share four names
    for o in OBSERVABLES + CAUSAL_OBSERVABLES:
        if o in present:
            seen[o] = None
    return tuple(seen)


def _table_carries(observable: str, table: dict | None) -> bool:
    """Does `table` actually have a column for `observable`?

    The half of the old `observable in _observables_of(t)` filter that genuinely
    depends on the table, split out so the *registry* half can be named at the
    call site (see :func:`constant_at_every_index`). The split is what keeps the
    exemption `TYPED`: this predicate returns a bool, so it is not set-valued
    and is not read as an exemption at all, while the registry it used to hide
    is now a bare module constant both scans resolve.

    `None` means the critical table, whose columns are :data:`OBSERVABLES` by
    construction — so every observable the caller can legally pass is carried,
    and the one real exclusion is `min_ttc`, which the causal tables spell
    `ttc`.
    """
    if table is None:
        return True
    return observable in table[MEASURED_SCENES[0]]


def separating_observables(scene: str, table: dict | None = None) -> tuple[str, ...]:
    """The observables that separate `scene` from the other four, in registry order."""
    return tuple(o for o in _observables_of(table) if separates(scene, o, table))


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


def is_constant(observable: str, table: dict | None = None) -> bool:
    """Does `observable` have **zero within-scene spread** in every measured scene?

    True ⇒ it is a scenario parameter wearing an observable's clothes: eight
    seeds of the same scene produce eight identical values, so the number
    cannot be responding to anything the rollout did. A separation carried by
    such an observable is an oracle read — Q-162's option (C).

    A predicate rather than a set, matching :func:`separates` one level up, so
    every filter in this module narrows the same way. The alternative shape —
    materialising `set(constant_observables())` and excluding against it —
    classifies as a `DIFFERENCE` guard under `guard_reflexivity`, and D-334
    took that route first: it costs a hand-written `guard_direction.PROBES`
    entry with a repo fixture and a permit/offend pair. The check that entry
    would buy (the excluded population cannot silently go empty) is already
    carried here by data, not by shape — :data:`INFORMATIVE_SEPARATION` is
    pinned as a whole-table equality and :func:`constant_observables` is pinned
    to its exact membership, so an emptied population is two red tests either
    way. Recorded because the restructure was prompted by the probe's price,
    and a reader should be able to see that and check the reasoning rather than
    read it as taste.
    """
    tbl = _table(table)
    return all(max(tbl[s][observable]) == min(tbl[s][observable])
               for s in MEASURED_SCENES)


def constant_observables() -> tuple[str, ...]:
    """The observables :func:`is_constant` holds of, in registry order.

    The census accessor for the predicate above — kept because the *population*
    is what the verdict subtracts and what the tests pin, and a predicate alone
    would leave that population unnamed.
    """
    return tuple(o for o in OBSERVABLES if is_constant(o))


def informative_separators(scene: str, table: dict | None = None) -> tuple[str, ...]:
    """:func:`separating_observables`, minus the observables that never move."""
    return tuple(o for o in separating_observables(scene, table)
                 if not is_constant(o, table))


def scenes_that_separate_informatively() -> tuple[str, ...]:
    """Scenes a *rollout-derived* observable separates. The honest table."""
    return tuple(s for s in MEASURED_SCENES if informative_separators(s))


def constant_at_every_index(observable: str) -> bool:
    """Is `observable` zero-spread under **all three** index policies?

    :func:`is_constant` grades one table. This grades the observable, and the
    distinction is what D-336 turns on: `obstacle_speed` is constant at every
    index because it is literally a yaml scalar, whereas a projection of the
    obstacle velocity *could* in principle move with the read index, since the
    schedules are piecewise. Measured, it does not — see
    :func:`obstacle_side_observables`.

    **Why the registry is named here rather than fetched (Q-164 → D-338).** The
    first draft filtered against `_observables_of(t)`, which reads correctly and
    was wrong for a reason no reviewer would see: that call is a same-module
    frame down to a hand-typed registry, so `_is_set_valued` follows it and
    admits this guard while `_provenance` stops at it and labels the exemption
    `DERIVED`. A `DERIVED` exemption is skipped by **every** `TYPED` screen
    (`Guard.typed_exemptions`, `guard_reflexivity.bite`, `unwatched_exemptions`,
    and the whole of `exemption_masking`), so the guard would have been admitted
    and then silently unwatched. That is exactly the shape
    :func:`predicate_depth.provenance_depth_exposure` was shipped to count, and
    D-336 wrote its first instance. The repair is the one D-052 (b) prescribed
    at the time: **name the registry at the call site**, and let a separate
    predicate carry the part that genuinely depends on the table.
    """
    tables = [None if p == "critical" else CAUSAL_OBSERVED[p] for p in INDEX_POLICIES]
    return all(is_constant(observable, t) for t in tables
               if observable in OBSERVABLES and _table_carries(observable, t))


#: The observables that are functions of the obstacle's scripted velocity and
#: the reference path **alone** — nothing about what the robot actually did.
#:
#: D-336's population. Both members are measured zero-spread at all three
#: indices, and the reason is structural rather than incidental: every obstacle
#: in the suite follows a piecewise-linear yaml schedule and every reference
#: path is a fixed polyline, so any quantity built from those two is a yaml
#: constant on whichever segment the read index lands in. Seed only moves
#: *which* index that is, and the segments are long enough that all eight seeds
#: land on the same one.
OBSTACLE_SIDE_OBSERVABLES: tuple[str, ...] = ("obstacle_speed", "path_lateral_speed")


def obstacle_side_observables() -> tuple[str, ...]:
    """:data:`OBSTACLE_SIDE_OBSERVABLES`, re-derived as the always-constant set.

    Returned as a census rather than asserted as a literal so the claim "these
    are exactly the obstacle-side channels" is checkable against the measurement
    instead of against the comment above it.
    """
    return tuple(o for o in OBSERVABLES if constant_at_every_index(o))


def causal_separation_table(policy: str) -> dict[str, tuple[str, ...]]:
    """:func:`separation_table`, read at a causally-available index."""
    return {s: separating_observables(s, CAUSAL_OBSERVED[policy])
            for s in MEASURED_SCENES}


def causal_informative_table(policy: str) -> dict[str, tuple[str, ...]]:
    """:func:`causal_separation_table`, minus the observables that never move."""
    return {s: informative_separators(s, CAUSAL_OBSERVED[policy])
            for s in MEASURED_SCENES}


def question_scene_is_causally_separable(policy: str) -> bool:
    """Does `cut_in` have a *rollout-derived* separator at `policy`'s index?

    The D-335 question in one call. :func:`question_scene_is_informatively_separable`
    asks it of the hindsight reading and answers False; this asks it of a reading
    a switch could actually take.
    """
    return bool(informative_separators(QUESTION_SCENE, CAUSAL_OBSERVED[policy]))


def policies_that_separate_question_scene() -> tuple[str, ...]:
    """The index policies under which `cut_in` has an informative separator.

    Empty ⇒ the invisibility D-334 found at the hindsight index is **not** an
    artefact of reading late: the scene is invisible to this observable set at
    every index measured, which is the stronger of the two readings D-335 could
    have produced.
    """
    return tuple(p for p in INDEX_POLICIES[1:]
                 if question_scene_is_causally_separable(p))


def causal_policies_agree() -> bool:
    """Do the two causal policies produce the same informative table, in full?

    **This is the control on the policy axis**, and it is measured **False**:
    the two policies disagree about `freezing` (`ttc` separates it at a fixed
    1 s, nothing does at first detection) and about `head_on` (one separator
    versus two). So the *table* is policy-dependent, and no row of it may be
    quoted without naming the index it was read at.

    Kept as a whole-table comparison, and kept red, rather than weakened to the
    one row D-335 needs. :func:`policies_agree_on_question_scene` is the narrow
    claim the verdict actually rests on; separating them is what stops a later
    cycle reading the narrow agreement as a general one.
    """
    return (causal_informative_table("first_detection")
            == causal_informative_table("fixed_time"))


def policies_agree_on_question_scene() -> bool:
    """Do **all three** index policies agree about `cut_in`'s row?

    True, and empty in all three — which is the claim D-335 makes. It is
    strictly narrower than :func:`causal_policies_agree`: the policies disagree
    elsewhere in the table, so what is being asserted is that `cut_in`'s
    invisibility survives every index measured, not that the index does not
    matter in general. It plainly does matter; it just does not matter *here*.
    """
    rows = [informative_separators(QUESTION_SCENE,
                                   None if p == "critical" else CAUSAL_OBSERVED[p])
            for p in INDEX_POLICIES]
    return all(row == rows[0] for row in rows)


def robust_causal_separators(scene: str) -> tuple[str, ...]:
    """The informative separators `scene` has at **every** causal index.

    An intersection, not a union, and that is the whole point: a separator that
    appears at one causal index and not the other is a property of the index
    policy, which :func:`causal_policies_agree` already measures **False** for
    the table as a whole. Only the intersection survives the control, so only
    the intersection is quotable without naming an index.
    """
    rows = [set(informative_separators(scene, CAUSAL_OBSERVED[p]))
            for p in INDEX_POLICIES[1:]]
    common = set.intersection(*rows) if rows else set()
    return tuple(o for o in CAUSAL_OBSERVABLES if o in common)


def scene_visibility(scene: str) -> str:
    """`robust` | `index_fragile` | `invisible` — how a switch could see `scene`.

    The three-way split the `cut_in` null could not produce on its own, because
    with one scene the only available answers are "separable" and "not". Read
    over all five it separates into:

    * **`robust`** — an informative separator at *both* causal indices. A switch
      could fire on it without knowing when to look.
    * **`index_fragile`** — informative somewhere, but not at every causal index.
      The reading is about the policy, not the scene; a switch built on it is
      fitted to the instant it was measured at.
    * **`invisible`** — no informative separator at any of the three measured
      indices, hindsight included. :data:`QUESTION_SCENE` is here.
    """
    if robust_causal_separators(scene):
        return "robust"
    seen = [informative_separators(scene, None if p == "critical"
                                   else CAUSAL_OBSERVED[p])
            for p in INDEX_POLICIES]
    return "index_fragile" if any(seen) else "invisible"


def visibility_census() -> dict[str, tuple[str, ...]]:
    """`class -> scenes`, over all five. The answer to the four-scene question.

    `cut_in`'s invisibility was never the whole finding — the question STATE.md
    carried was whether *any* scene separates at plan time on something that
    moves. One does (`head_on`, on `closing_speed`, at both causal indices), and
    it is the one scene D-333 says a switch is not needed for, because
    `cbf_mppi` already wins it. The scenes a switch would have to arbitrate are
    exactly the invisible ones.
    """
    out: dict[str, tuple[str, ...]] = {}
    for scene in MEASURED_SCENES:
        out.setdefault(scene_visibility(scene), ())
        out[scene_visibility(scene)] += (scene,)
    return out


def format_visibility_grade() -> str:
    """One-screen visibility census. For a human reading the cycle's output."""
    lines = ["scene                      class          robust separators"]
    for scene in MEASURED_SCENES:
        mark = " <- Q-162" if scene == QUESTION_SCENE else ""
        lines.append(f"  {scene:<24} {scene_visibility(scene):<15}"
                     f"{', '.join(robust_causal_separators(scene)) or '(none)'}{mark}")
    lines.append(f"visibility_census = {visibility_census()}")
    return "\n".join(lines)


def separation_margin(scene: str, observable: str,
                      table: dict | None = None) -> float:
    """The gap :func:`separates` thresholds at zero, in units of total spread.

    Positive ⇒ disjoint by that fraction of the combined range; negative ⇒ the
    distributions overlap by it. :func:`separates` is exactly `margin > 0`, so
    this is the continuous quantity underneath a boolean the census reads as a
    scene property.

    `nan` when the column is not finite, matching :func:`separates`'s refusal to
    grade an infinite TTC rather than inventing an ordering for it.
    """
    tbl = _table(table)
    mine = np.asarray(tbl[scene][observable], dtype=float)
    rest = np.concatenate([np.asarray(tbl[s][observable], dtype=float)
                           for s in MEASURED_SCENES if s != scene])
    if not (np.isfinite(mine).all() and np.isfinite(rest).all()):
        return float("nan")
    gap = max(mine.min() - rest.max(), rest.min() - mine.max())
    span = max(float(np.concatenate([mine, rest]).ptp()), 1e-12)
    return float(gap / span)


def separation_survives_seed_deletion(scene: str, observable: str,
                                      table: dict | None = None) -> bool:
    """Does the separation hold after deleting **any one** seed, either side?

    The resampling question the margin cannot answer. :func:`separation_margin`
    reports distance in units of the *combined* spread, which is set by whichever
    scene is furthest away — so a gap can read as a thin fraction of the total
    range while still being wide compared to the seed-to-seed scatter that
    actually decides it. This deletes one observation at a time and re-applies
    the rule, which is the same question asked in the units that matter.

    Measured, the two disagree, and that is why both are here: `head_on`'s
    `closing_speed` margin is `+0.023` at first detection — thin enough to read
    as a knife edge — and survives all 40 single-seed deletions. Read the
    margin alone and the one robust separator in the suite looks like a
    threshold artefact; it is not.

    **On this table the predicate coincides with :func:`separates` exactly**, and
    that is a measurement, not a redundancy: *no* separating pair anywhere in the
    suite is one seed from failing. The deletion sensitivity that does exist runs
    the other way — see :func:`deletion_fragile_negatives` — so this function is
    the half that reports a clean bill and that one is the half that bites.
    """
    tbl = _table(table)
    mine = np.asarray(tbl[scene][observable], dtype=float)
    rest = np.concatenate([np.asarray(tbl[s][observable], dtype=float)
                           for s in MEASURED_SCENES if s != scene])
    if not (np.isfinite(mine).all() and np.isfinite(rest).all()):
        return False

    def disjoint(a: np.ndarray, b: np.ndarray) -> bool:
        return bool(a.max() < b.min() or a.min() > b.max())

    if not disjoint(mine, rest):
        return False
    return (all(disjoint(np.delete(mine, i), rest) for i in range(mine.size))
            and all(disjoint(mine, np.delete(rest, j)) for j in range(rest.size)))


def separation_flips_under_seed_deletion(scene: str, observable: str,
                                         table: dict | None = None) -> bool:
    """Would deleting one seed turn this **non**-separation into a separation?

    The direction that actually discriminates on this suite. The invisibility
    verdicts are negatives — "no observable separates this scene" — and a
    negative earned by a 1.7%-of-spread overlap is a different claim from one
    earned by a 23% overlap. This asks the resampling question of the negatives.
    """
    tbl = _table(table)
    mine = np.asarray(tbl[scene][observable], dtype=float)
    rest = np.concatenate([np.asarray(tbl[s][observable], dtype=float)
                           for s in MEASURED_SCENES if s != scene])
    if not (np.isfinite(mine).all() and np.isfinite(rest).all()):
        return False

    def disjoint(a: np.ndarray, b: np.ndarray) -> bool:
        return bool(a.max() < b.min() or a.min() > b.max())

    if disjoint(mine, rest):
        return False                    # already separating: not this question
    return (any(disjoint(np.delete(mine, i), rest) for i in range(mine.size))
            or any(disjoint(mine, np.delete(rest, j)) for j in range(rest.size)))


def deletion_fragile_negatives() -> tuple[tuple[str, str, str], ...]:
    """`(scene, observable, policy)` for every negative one deletion could flip.

    **The honest caveat on D-341's census.** Four of them, and one lands inside
    the invisible class: `obstacle_crossing`/`lateralness` at first detection.
    So `no_gap_anywhere` for that scene is a verdict at eight seeds, not a
    structural statement — with one fewer seed at one index it would have read
    as a separation. `convoy` has no entry here, which is what makes its
    negative the sturdier of the two.

    Reported as the population rather than a count, because a count would go
    green on a re-take that swapped one entry for another.
    """
    out: list[tuple[str, str, str]] = []
    for policy in INDEX_POLICIES:
        table = None if policy == "critical" else CAUSAL_OBSERVED[policy]
        for scene in MEASURED_SCENES:
            for obs in _observables_of(table):
                if separation_flips_under_seed_deletion(scene, obs, table):
                    out.append((scene, obs, policy))
    return tuple(out)


def robust_separators_survive_deletion(scene: str) -> bool:
    """Do all of `scene`'s robust separators survive deletion at both indices?

    The census-level version of the check above: :func:`scene_visibility` grades
    `robust` off a boolean at two indices, and this asks whether that grade is
    resampling-stable rather than a pair of lucky reads. Vacuously True for a
    scene with no robust separators — the claim is about the ones it has.
    """
    return all(separation_survives_seed_deletion(scene, o, CAUSAL_OBSERVED[p])
               for o in robust_causal_separators(scene)
               for p in INDEX_POLICIES[1:])


def invisibility_reason(scene: str) -> str:
    """**Why** `scene` is invisible — the partition of D-341's largest class.

    `scene_visibility` says three of five scenes have no informative separator
    at any index, and stops there. Three scenes sharing a verdict is not three
    scenes sharing a cause, and the difference decides what would fix them:

    * **`oracle_only`** — something *does* separate the scene, but every such
      observable is zero-spread, i.e. a yaml scenario parameter read back out.
      The scene is distinguishable; it is just not distinguishable by anything
      the rollout produced. A richer *representation* could reach it.
    * **`no_gap_anywhere`** — no observable separates it at any index, constant
      ones included. Not even an oracle read of the scenario file gates this
      scene against the other four under the no-overlap rule. A richer
      representation is not obviously enough; the scene may simply not be
      distinct in these terms.
    * **`not_invisible`** — total by construction, so the function can be
      applied to the whole census without the caller pre-filtering and
      accidentally scoping the reason to a class it did not check.

    Measured: `cut_in` is `oracle_only` (`obstacle_speed` separates it at the
    hindsight index and is a yaml constant), while `convoy` and
    `obstacle_crossing` are `no_gap_anywhere`. So the invisible class is **two**
    reasons, not one and not three.
    """
    if scene_visibility(scene) != "invisible":
        return "not_invisible"
    tables = [None if p == "critical" else CAUSAL_OBSERVED[p] for p in INDEX_POLICIES]
    return ("oracle_only"
            if any(separating_observables(scene, t) for t in tables)
            else "no_gap_anywhere")


def invisibility_census() -> dict[str, tuple[str, ...]]:
    """`reason -> scenes`, over the invisible class only.

    The companion to :func:`visibility_census` one level down. That one says how
    many scenes a switch cannot see; this says how many of those a better
    representation could still rescue.
    """
    out: dict[str, tuple[str, ...]] = {}
    for scene in MEASURED_SCENES:
        reason = invisibility_reason(scene)
        if reason != "not_invisible":
            out[reason] = out.get(reason, ()) + (scene,)
    return out


def format_invisibility_grade() -> str:
    """One-screen reason partition + the margin/deletion disagreement."""
    lines = ["scene                      reason           best non-constant margin"]
    for scene in MEASURED_SCENES:
        best, where = float("-inf"), "(none)"
        for policy in INDEX_POLICIES[1:]:
            table = CAUSAL_OBSERVED[policy]
            for obs in _observables_of(table):
                if is_constant(obs, table):
                    continue
                margin = separation_margin(scene, obs, table)
                if margin == margin and margin > best:   # nan-safe
                    best, where = margin, f"{obs}@{policy}"
        lines.append(f"  {scene:<24} {invisibility_reason(scene):<16}"
                     f"{best:+.3f}  {where}")
    lines.append(f"invisibility_census = {invisibility_census()}")
    lines.append(f"robust separators survive single-seed deletion: "
                 f"{all(robust_separators_survive_deletion(s) for s in MEASURED_SCENES)}")
    return "\n".join(lines)


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


def format_causal_grade() -> str:
    """The D-335 table: the same rule at three read indices, side by side."""
    lines = [f"policy            scene                      informative separators"]
    for policy in INDEX_POLICIES:
        table = None if policy == "critical" else CAUSAL_OBSERVED[policy]
        for scene in MEASURED_SCENES:
            mark = " <- D-335" if scene == QUESTION_SCENE else ""
            got = ", ".join(informative_separators(scene, table)) or "(none)"
            lines.append(f"  {policy:<16} {scene:<26} {got}{mark}")
    lines.append(f"policies_that_separate_question_scene = "
                 f"{policies_that_separate_question_scene()}")
    lines.append(f"policies_agree_on_question_scene      = "
                 f"{policies_agree_on_question_scene()}")
    lines.append(f"causal_policies_agree (whole table)   = {causal_policies_agree()}")
    return "\n".join(lines)


if __name__ == "__main__":  # pragma: no cover - measurement entry point
    import json
    import sys
    if "--retake" in sys.argv:
        print(json.dumps(retake_observables(), indent=1))
    elif "--causal" in sys.argv:
        print(format_causal_grade())
    else:
        print(format_grade())


# --------------------------------------------------------------------------
# The re-take at sixteen seeds (D-344)
# --------------------------------------------------------------------------
#
# :func:`deletion_fragile_negatives` measured four negatives one seed deletion
# would flip, and one — `obstacle_crossing` / `lateralness` at first detection
# — sits inside the invisible class D-341's conclusion rests on. That made
# `no_gap_anywhere` for that scene a verdict at eight seeds rather than a
# structural statement.
#
# Deletion asks what happens with *fewer* seeds, and it is one-directional:
# removing a seed can only shrink a range, so it can only ever manufacture
# separations. Doubling the count is the reading that can go either way, and it
# is the one recorded below.

#: :data:`OBSERVED`, re-taken at **16** seeds (0..15) on the same baseline arm.
#: Recorded rather than recomputed on import for the same reason as the
#: eight-seed tables, and a stronger one: the re-take is **153 s**
#: of rollouts (80 per arm, measured 2026-08-18), which no test can afford.
OBSERVED_16: dict[str, dict[str, tuple[float, ...]]] = {
    "cafe_freezing_v0": {
        "lateralness": (0.5584, 0.5316, 0.3987, 0.5026, 0.6218, 0.4184, 0.5351, 0.469,
            0.5277, 0.5043, 0.5525, 0.4902, 0.3817, 0.5399, 0.5706, 0.3982),
        "closing_speed": (0.0298, -0.0121, 0.0859, -0.051, -0.0399, 0.035, 0.0184, 0.0409,
            -0.0574, -0.0223, -0.0342, 0.032, 0.0705, 0.0387, -0.1062, -0.0093),
        "bearing_rate": (1.3707, 1.2787, 1.0811, 1.3322, 1.2975, 1.5826, 1.3777, 1.4132,
            1.2505, 1.3348, 1.4609, 1.5371, 1.6048, 1.2626, 1.2142, 1.236),
        "obstacle_speed": (1.25,) * 16,
        "path_lateral_speed": (1.25,) * 16,
        "min_ttc": (1.3012, 1.4264, 1.3354, 1.2149, 1.285, 1.1357, 1.0676, 1.2004, 1.2874,
            1.0663, 1.5002, 1.1816, 1.1838, 1.1664, 1.2711, 1.0258),
    },
    "cafe_cut_in_v0": {
        "lateralness": (0.999, 0.996, 0.9999, 1, 0.5314, 0.9944, 0.9417, 0.9995, 0.9972,
            0.9995, 1, 1, 0.993, 0.9998, 0.9987, 0.9965),
        "closing_speed": (0.0025, 0.0048, -0.0542, -0.0275, 0.0424, 0.0104, 0.0171, 0.0018,
            0.004, 0.004, 0.0002, -0.0268, 0.0033, -0.0239, 0.001, 0.0045),
        "bearing_rate": (1.1104, 1.784, 2.1999, 1.6464, 0.3242, 1.6804, 1.4545, 0.1882,
            0.6124, 0.3739, 0.7207, 1.7235, 0.5194, 1.9027, 0.457, 0.6335),
        "obstacle_speed": (0.0,) * 16,
        "path_lateral_speed": (0.0,) * 16,
        "min_ttc": (1.3645, 1.6842, 1.4138, 1.4867, 1.2716, 1.377, 1.3365, 1.4094, 1.6784,
            0.9827, 1.2803, 1.1593, 1.612, 1.2006, 1.2526, 1.3987),
    },
    "cafe_head_on_v0": {
        "lateralness": (0.9836, 0.9825, 0.9982, 0.9943, 0.9896, 0.9957, 0.9993, 0.998,
            0.9889, 0.9844, 0.9945, 0.9918, 0.9995, 0.9634, 0.993, 0.9739),
        "closing_speed": (-0.1205, -0.0911, -0.0298, 0.128, -0.2006, 0.1414, -0.0704,
            0.1549, -0.071, 0.0563, -0.115, -0.002, 0.203, -0.176, -0.152, -0.1485),
        "bearing_rate": (1.3612, 1.3669, 1.397, 1.5067, 1.8549, 1.9463, 1.8283, 1.5128,
            1.6107, 1.5058, 1.4421, 1.6781, 2.0423, 1.6661, 1.474, 1.3397),
        "obstacle_speed": (1.0,) * 16,
        "path_lateral_speed": (0.0,) * 16,
        "min_ttc": (0.0744, 0.0522, 0.0494, 0.0198, 0.0168, 0.0092, 0.0708, 0.0795, 0.0557,
            0.1658, 0.1211, 0.0652, 0.0775, 0.0657, 0.0476, 0.0753),
    },
    "cafe_convoy_v0": {
        "lateralness": (0.7338, 0.6435, 0.7218, 0.674, 0.7042, 0.694, 0.6628, 0.7111,
            0.6821, 0.6708, 0.7027, 0.5724, 0.4959, 0.6843, 0.6959, 0.6579),
        "closing_speed": (-0.035, 0.0745, -0.0004, 0.0249, 0.0751, -0.012, 0.0477, -0.0905,
            0.0213, -0.0179, -0.0317, 0.0818, 0.0121, 0.0263, 0.0391, 0.0403),
        "bearing_rate": (0.9437, 0.592, 1.0841, 0.9037, 0.9597, 0.9907, 1.0037, 1.1057,
            0.6724, 0.7876, 0.6583, 0.89, 0.8448, 1.1021, 1.0851, 0.5587),
        "obstacle_speed": (0.8333,) * 16,
        "path_lateral_speed": (0.8333,) * 16,
        "min_ttc": (1.0311, 1.1375, 1.147, 0.9698, 1.3741, 1.1379, 1.4539, 1.2512, 0.9421,
            1.1584, 1.3317, 1.2147, 0.7961, 1.1204, 1.1952, 0.9821),
    },
    "cafe_obstacle_crossing_v0": {
        "lateralness": (0.707, 0.6644, 0.7418, 0.7999, 0.7628, 0.7566, 0.7886, 0.7511,
            0.7033, 0.772, 0.6304, 0.7417, 0.7347, 0.6611, 0.7033, 0.7845),
        "closing_speed": (0.0089, -0.034, -0.0593, 0.0017, 0.0598, 0.0328, 0.0125, 0.0161,
            0.0324, 0.0507, -0.0981, -0.0631, -0.0911, -0.0278, -0.0259, 0.0631),
        "bearing_rate": (1.2871, 1.6683, 1.2598, 1.276, 1.1724, 0.9886, 1.6091, 1.0946,
            1.4216, 1.25, 1.212, 1.1671, 1.8386, 1.1918, 1.3672, 1.2617),
        "obstacle_speed": (0.75,) * 16,
        "path_lateral_speed": (0.75,) * 16,
        "min_ttc": (0.3298, 0.2984, 0.1809, 0.222, 0.2858, 0.1547, 0.1449, 0.1454, 0.1712,
            0.3102, 0.2104, 0.3655, 0.2884, 0.2279, 0.1614, 0.1702),
    },
}

#: :data:`CAUSAL_OBSERVED`, re-taken at the same 16 seeds and read off the same
#: rollouts as :data:`OBSERVED_16` in one pass. `critical` is absent here for
#: the reason it is absent there — its table is :data:`OBSERVED_16`, and a
#: second copy is a second thing to move.
CAUSAL_OBSERVED_16: dict[str, dict[str, dict[str, tuple[float, ...]]]] = {
    "first_detection": {
        "cafe_freezing_v0": {
            "lateralness": (0.67, 0.7167, 0.7305, 0.7081, 0.7053, 0.6972, 0.7011, 0.7605,
                0.732, 0.7121, 0.7235, 0.7711, 0.7518, 0.7277, 0.6503, 0.6987),
            "closing_speed": (1.1576, 1.0872, 1.0031, 1.2458, 1.1995, 1.0053, 1.0675,
                1.2665, 1.1432, 1.1537, 1.1958, 1.0841, 1.1333, 1.1351, 1.0248, 1.0359),
            "bearing_rate": (0.6848, 0.361, 0.2309, 0.5145, 0.3647, 0.1029, 0.0652, 0.1807,
                0.2702, 0.323, 0.4173, 0.182, 0.1865, 0.0702, 0.2971, 0.1683),
            "obstacle_speed": (1.25,) * 16,
            "path_lateral_speed": (1.25,) * 16,
            "ttc": (1.6587, 1.7825, 1.9317, 1.5252, 1.5979, 1.9512, 1.7997, 1.4973, 1.6716,
                1.6651, 1.6067, 1.771, 1.6976, 1.6893, 1.8837, 1.8718),
        },
        "cafe_cut_in_v0": {
            "lateralness": (0.6265, 0.6574, 0.611, 0.6519, 0.6601, 0.6777, 0.6313, 0.6326,
                0.6265, 0.6399, 0.6717, 0.6223, 0.6574, 0.6574, 0.6635, 0.6574),
            "closing_speed": (0.6412, 0.6361, 0.6436, 0.637, 0.6356, 0.6325, 0.6405, 0.6402,
                0.6412, 0.6391, 0.6336, 0.6419, 0.6361, 0.6361, 0.6351, 0.6361),
            "bearing_rate": (0.1708, 0.1684, 0.4174, 0.005, 0.0494, 0.1689, 0.3401, 0.2229,
                0.1708, 0.284, 0.0225, 0.3414, 0.1684, 0.1684, 0.0877, 0.1684),
            "obstacle_speed": (0.75,) * 16,
            "path_lateral_speed": (0.75,) * 16,
            "ttc": (3.0713, 3.0971, 3.0594, 3.0923, 3.0994, 3.1154, 3.0752, 3.0763, 3.0713,
                3.0822, 3.1098, 3.068, 3.0971, 3.0971, 3.1024, 3.0971),
        },
        "cafe_head_on_v0": {
            "lateralness": (0.3904, 0.3538, 0.4211, 0.4648, 0.4574, 0.3476, 0.5838, 0.3694,
                0.4759, 0.3392, 0.5914, 0.3934, 0.5953, 0.3356, 0.323, 0.3283),
            "closing_speed": (1.4895, 1.45, 1.3646, 1.4175, 1.4067, 1.4919, 1.2874, 1.3572,
                1.4501, 1.4359, 1.365, 1.64, 1.5267, 1.3097, 1.5549, 1.6297),
            "bearing_rate": (0.7137, 0.7085, 0.5518, 0.9052, 0.4214, 0.5214, 0.3404, 0.3685,
                0.684, 0.5295, 0.4349, 0.4678, 0.3697, 0.4836, 0.5943, 0.748),
            "obstacle_speed": (1.0,) * 16,
            "path_lateral_speed": (0.0,) * 16,
            "ttc": (1.296, 1.2994, 1.4342, 1.3513, 1.3768, 1.3131, 1.4989, 1.466, 1.2846,
                1.3792, 1.4293, 1.1507, 1.213, 1.4316, 1.2627, 1.1563),
        },
        "cafe_convoy_v0": {
            "lateralness": (0.6632, 0.6122, 0.5932, 0.8258, 0.7632, 0.5146, 0.7658, 0.6431,
                0.6453, 0.7389, 0.6716, 0.6693, 0.7008, 0.6684, 0.6398, 0.7848),
            "closing_speed": (0.7213, 0.5733, 0.7641, 0.7456, 0.7854, 0.691, 0.8574, 0.5941,
                0.6974, 0.7506, 0.6728, 0.7972, 0.7983, 0.6519, 0.7134, 0.6868),
            "bearing_rate": (0.6533, 0.3208, 0.2629, 0.2174, 0.0869, 0.9157, 0.3033, 0.0201,
                0.3703, 0.2036, 0.2749, 0.3088, 0.4056, 0.1265, 0.0768, 0.217),
            "obstacle_speed": (0.8333,) * 16,
            "path_lateral_speed": (0.8333,) * 16,
            "ttc": (2.6914, 3.4714, 2.5795, 2.6698, 2.477, 2.7983, 2.2738, 3.2671, 2.794,
                2.5886, 2.9592, 2.4465, 2.4663, 3.0251, 2.7296, 2.8584),
        },
        "cafe_obstacle_crossing_v0": {
            "lateralness": (0.8944, 0.909, 0.9088, 0.8395, 0.8974, 0.816, 0.8799, 0.8254,
                0.9257, 0.846, 0.8649, 0.8574, 0.9734, 0.8909, 0.8969, 0.8674),
            "closing_speed": (0.9384, 0.9275, 0.861, 0.9415, 0.869, 1.0189, 0.9814, 1.0488,
                0.903, 1.0498, 0.961, 0.9292, 0.7998, 0.9647, 0.8738, 1.002),
            "bearing_rate": (0.4163, 0.0659, 0.0962, 0.4422, 0.3878, 0.3464, 0.1457, 0.0512,
                0.1721, 0.3723, 0.0576, 0.0479, 0.5057, 0.1568, 0.3045, 0.0911),
            "obstacle_speed": (0.75,) * 16,
            "path_lateral_speed": (0.75,) * 16,
            "ttc": (2.0907, 2.1128, 2.3225, 2.0405, 2.2966, 1.8686, 2.012, 1.8869, 2.1818,
                1.8243, 2.0575, 2.1118, 2.4889, 2.0666, 2.2709, 1.955),
        },
    },
    "fixed_time": {
        "cafe_freezing_v0": {
            "lateralness": (0.4776, 0.6608, 0.5468, 0.6003, 0.4483, 0.5575, 0.5018, 0.6373,
                0.6205, 0.6757, 0.5618, 0.565, 0.5449, 0.467, 0.524, 0.6681),
            "closing_speed": (1.0773, 0.9199, 1.0473, 1.0663, 0.9093, 0.9407, 0.9516,
                0.9995, 1.1197, 0.7987, 0.8816, 1.0711, 0.9593, 0.8345, 1.1484, 1.119),
            "bearing_rate": (0.6463, 0.0073, 0.2411, 0.4869, 0.3841, 0.4211, 0.8184, 0.5481,
                0.1101, 0.2841, 0.4442, 0.6102, 0.5745, 0.6896, 0.3089, 0.0088),
            "obstacle_speed": (1.25,) * 16,
            "path_lateral_speed": (1.25,) * 16,
            "ttc": (1.2365, 1.5208, 1.3726, 1.286, 1.5755, 1.5586, 1.4813, 1.3365, 1.2144,
                1.7923, 1.5973, 1.2863, 1.462, 1.6866, 1.188, 1.258),
        },
        "cafe_cut_in_v0": {
            "lateralness": (0.5479, 0.5451, 0.5119, 0.4362, 0.5163, 0.5527, 0.5788, 0.5896,
                0.6464, 0.6364, 0.5889, 0.5951, 0.5508, 0.6255, 0.6088, 0.6127),
            "closing_speed": (0.6968, 0.8004, 0.784, 0.661, 0.7622, 0.6179, 0.6003, 0.7329,
                0.7099, 0.7256, 0.6303, 0.7124, 0.7307, 0.6116, 0.6788, 0.6754),
            "bearing_rate": (0.5908, 0.3654, 0.2104, 0.1086, 0.2097, 0.2646, 0.138, 0.0797,
                0.278, 0.1004, 0.4357, 0.2732, 0.2042, 0.2328, 0.3857, 0.1233),
            "obstacle_speed": (0.75,) * 16,
            "path_lateral_speed": (0.75,) * 16,
            "ttc": (2.0275, 1.6939, 1.7024, 2.0595, 1.855, 2.2806, 2.3677, 1.8265, 1.9061,
                1.8339, 2.2571, 1.8743, 1.8871, 2.2234, 1.9781, 2.0759),
        },
        "cafe_head_on_v0": {
            "lateralness": (0.0405, 0.0939, 0.0703, 0.106, 0.064, 0.1379, 0.0585, 0.0201,
                0.0878, 0.0632, 0.0272, 0.0469, 0.0087, 0.0346, 0.1002, 0.0346),
            "closing_speed": (1.3023, 1.5134, 1.3087, 1.1989, 1.4962, 1.2503, 1.3935,
                1.2695, 1.1992, 1.2367, 1.3443, 1.2594, 1.3024, 1.2668, 1.2641, 1.3656),
            "bearing_rate": (0.0244, 0.4434, 0.0818, 0.0064, 0.2763, 0.0509, 0.2402, 0.0013,
                0.0246, 0.1203, 0.1737, 0.3044, 0.2207, 0.4515, 0.0816, 0.1636),
            "obstacle_speed": (1.0,) * 16,
            "path_lateral_speed": (0.0,) * 16,
            "ttc": (2.7866, 2.3134, 2.7044, 2.9623, 2.3339, 2.9183, 2.5558, 2.8279, 3.0105,
                2.9052, 2.6765, 2.9492, 2.7326, 2.8337, 2.8281, 2.6069),
        },
        "cafe_convoy_v0": {
            "lateralness": (0.7428, 0.6951, 0.6142, 0.8133, 0.7688, 0.7127, 0.7849, 0.6527,
                0.6867, 0.7761, 0.6917, 0.7288, 0.7291, 0.6999, 0.6641, 0.7967),
            "closing_speed": (0.7275, 0.5694, 0.6928, 0.816, 0.8543, 0.6313, 0.8484, 0.7678,
                0.7137, 0.7552, 0.7527, 0.6633, 0.7306, 0.6734, 0.7296, 0.7022),
            "bearing_rate": (0.6303, 0.5053, 0.4754, 0.4525, 0.0484, 0.7019, 0.0974, 0.3114,
                0.0498, 0.1852, 0.1301, 0.3402, 0.2222, 0.4693, 0.4577, 0.1841),
            "obstacle_speed": (0.8333,) * 16,
            "path_lateral_speed": (0.8333,) * 16,
            "ttc": (2.8576, 3.8229, 2.9552, 2.531, 2.3692, 3.3807, 2.399, 2.6941, 2.9166,
                2.7813, 2.7343, 3.17, 2.8041, 3.113, 2.8765, 3.0009),
        },
        "cafe_obstacle_crossing_v0": {
            "lateralness": (0.8632, 0.8964, 0.8934, 0.7909, 0.8692, 0.7457, 0.8553, 0.8439,
                0.9043, 0.8182, 0.8473, 0.8504, 0.9376, 0.8875, 0.9128, 0.8487),
            "closing_speed": (1.0048, 0.9402, 0.8779, 0.979, 0.9952, 0.8805, 0.9739, 1.0223,
                0.967, 1.0762, 0.9745, 0.9318, 0.8945, 0.8889, 0.9337, 1.0357),
            "bearing_rate": (0.4192, 0.0539, 0.4898, 0.16, 0.4386, 0.045, 0.5107, 0.0541,
                0.1833, 0.0461, 0.4458, 0.1333, 0.5052, 0.0976, 0.0929, 0.4856),
            "obstacle_speed": (0.75,) * 16,
            "path_lateral_speed": (0.75,) * 16,
            "ttc": (2.1463, 2.2771, 2.4695, 2.1627, 2.1867, 2.4952, 2.2318, 2.1348, 2.2243,
                1.9714, 2.2316, 2.3105, 2.4108, 2.4552, 2.3151, 2.0831),
        },
    },
}


def eight_seed_tables() -> dict[str, dict]:
    """`policy -> table` at 8 seeds, for all three measured indices.

    `critical` resolves to :data:`OBSERVED` rather than to `None`. The two are
    equivalent through :func:`_table` and :func:`_observables_of` — the latter
    reads the columns off the table it is handed, and `OBSERVED` carries
    exactly :data:`OBSERVABLES` — but naming it explicitly is what lets the
    same walk run over either seed count.
    """
    return {p: (OBSERVED if p == "critical" else CAUSAL_OBSERVED[p])
            for p in INDEX_POLICIES}


def doubled_tables() -> dict[str, dict]:
    """`policy -> table` at 16 seeds. The counterpart of :func:`eight_seed_tables`."""
    return {p: (OBSERVED_16 if p == "critical" else CAUSAL_OBSERVED_16[p])
            for p in INDEX_POLICIES}


def _robust_separators_from(scene: str, tables: dict[str, dict]) -> tuple[str, ...]:
    """:func:`robust_causal_separators`, over a supplied set of tables."""
    rows = [set(informative_separators(scene, tables[p])) for p in INDEX_POLICIES[1:]]
    common = set.intersection(*rows) if rows else set()
    return tuple(o for o in CAUSAL_OBSERVABLES if o in common)


def _visibility_from(scene: str, tables: dict[str, dict]) -> str:
    """:func:`scene_visibility`, over a supplied set of tables."""
    if _robust_separators_from(scene, tables):
        return "robust"
    seen = [informative_separators(scene, tables[p]) for p in INDEX_POLICIES]
    return "index_fragile" if any(seen) else "invisible"


def _invisibility_reason_from(scene: str, tables: dict[str, dict]) -> str:
    """:func:`invisibility_reason`, over a supplied set of tables.

    A parallel implementation rather than a refactor of the eight-seed
    functions, and the choice is deliberate: those three are what every pin in
    this module reads, and rewriting them to reach a new seed count would put
    the control and the treatment on the same code. The equivalence is
    asserted instead — `test_the_seed_count_walk_reproduces_the_recorded_grade`
    runs this walk over :func:`eight_seed_tables` and requires it to agree with
    :func:`invisibility_reason` on all five scenes. If the two ever drift, that
    test goes red before any 16-seed claim can be quoted.
    """
    if _visibility_from(scene, tables) != "invisible":
        return "not_invisible"
    return ("oracle_only"
            if any(separating_observables(scene, tables[p]) for p in INDEX_POLICIES)
            else "no_gap_anywhere")


def visibility_at_16(scene: str) -> str:
    """:func:`scene_visibility`, re-read at 16 seeds."""
    return _visibility_from(scene, doubled_tables())


def invisibility_reason_at_16(scene: str) -> str:
    """:func:`invisibility_reason`, re-read at 16 seeds."""
    return _invisibility_reason_from(scene, doubled_tables())


def invisibility_survives_doubling(scene: str) -> bool:
    """Does `scene`'s eight-seed grade still hold when the seeds are doubled?

    The question STATE.md carried into this cycle, in one call. False means the
    grade was a property of the sample, not of the scene.
    """
    return invisibility_reason(scene) == invisibility_reason_at_16(scene)


def doubling_disagreements() -> tuple[tuple[str, str, str], ...]:
    """`(scene, reason_at_8, reason_at_16)` for every scene the doubling moved.

    Measured: exactly one, and **not** the scene the re-take was run for.
    `obstacle_crossing` — the fragile negative that motivated it — holds
    `no_gap_anywhere`, as does `convoy` and as does `cut_in`'s `oracle_only`.
    What moves is `freezing`, which was `index_fragile` at eight seeds (a
    separator at one causal index, not the other) and is `invisible` at
    sixteen. That is the class D-341 called the least interesting one, and it
    turns out to be the only unstable grade in the census.

    Reported as the population rather than a count, per
    :func:`deletion_fragile_negatives`.
    """
    return tuple((s, invisibility_reason(s), invisibility_reason_at_16(s))
                 for s in MEASURED_SCENES
                 if invisibility_reason(s) != invisibility_reason_at_16(s))


def fragile_negatives_at_16() -> tuple[tuple[str, str, str], ...]:
    """:func:`deletion_fragile_negatives`, re-measured on the 16-seed tables.

    The second half of the reading, and the half that does not resolve. The
    population is **still four**, and half its membership is new — so doubling
    the seeds did not shrink the deletion-fragile class, it churned it. Read
    together with :func:`doubling_disagreements` that is the honest shape of
    the answer: the *verdicts* are stable under doubling while the *near-miss
    population* is not, which means deletion fragility is a standing property
    of samples this size rather than a specific near-miss more data would
    settle.

    The one entry that appears at both counts is `obstacle_crossing` /
    `lateralness` at first detection — the very entry the re-take was run to
    settle. Persisting across a doubling is the opposite of sampling noise.

    There is deliberately **no** `persistently_fragile_negatives` accessor for
    that intersection. It was written, and `census_preempt` named it at the
    stage as guard entrant 123: a comprehension narrowing by membership of
    another census is `DIFFERENCE`-shaped, and D-334 measured that shape's real
    price as a hand-written `guard_direction.PROBES` entry with a repo fixture
    and a permit/offend pair — thirteen red pins, discovered after the tally was
    repaired. D-334's own resolution applies unchanged here: both populations
    are pinned by value, so the intersection is a reader's subtraction rather
    than a census needing its own liveness watch. Recorded because the shape was
    chosen after the price was known, and a later cycle should be able to
    disagree with that rather than re-derive it.
    """
    out: list[tuple[str, str, str]] = []
    for policy, table in doubled_tables().items():
        for scene in MEASURED_SCENES:
            for obs in _observables_of(table):
                if separation_flips_under_seed_deletion(scene, obs, table):
                    out.append((scene, obs, policy))
    return tuple(out)


def format_doubling_grade() -> str:
    """One-screen 8-vs-16 comparison. A formatter, so it gets a test (D-342).

    Reports the two fragile-population *counts* and not their intersection. The
    intersection was here for one revision and made this formatter guard
    entrant 123 — a comprehension narrowing by membership of another census is
    `DIFFERENCE`-shaped wherever it is written, so moving it out of the dropped
    accessor and into the readout moved the obligation with it rather than
    shedding it. The shared entry is asserted in
    `test_the_motivating_near_miss_persists_across_the_doubling`, which is a
    test and therefore not in the pool at all.
    """
    lines = ["scene                      reason@8         reason@16"]
    for scene in MEASURED_SCENES:
        mark = " <-" if not invisibility_survives_doubling(scene) else ""
        lines.append(f"  {scene:<24} {invisibility_reason(scene):<16} "
                     f"{invisibility_reason_at_16(scene)}{mark}")
    lines.append(f"doubling_disagreements = {doubling_disagreements()}")
    lines.append(f"fragile negatives: {len(deletion_fragile_negatives())} at 8 seeds, "
                 f"{len(fragile_negatives_at_16())} at 16")
    return "\n".join(lines)


def nonconstant_cell_margins(tables: dict[str, dict]
                             ) -> tuple[tuple[str, str, str, float], ...]:
    """`(scene, observable, policy, margin)` for every informative cell, thinnest first.

    The **evidence base** underneath the visibility census, as one population.
    :func:`scene_visibility` reduces this to a per-scene word and
    :func:`doubling_disagreements` reduces it further to the scenes whose word
    moved; both reductions throw away the thing that turns out to explain the
    movement, which is *how many cells a scene's grade rests on*.

    Derived from the supplied tables and nothing else. It is deliberately **not**
    narrowed by membership of the other seed count's population — the cells this
    doubling removed are a reader's subtraction of two value-pinned tuples, per
    :func:`fragile_negatives_at_16`'s account of what a `DIFFERENCE`-shaped
    accessor costs (guard entrant, `guard_direction.PROBES` fixture, thirteen
    red pins). Sorted ascending by margin so the rank claim below is readable
    off the return value rather than recomputed by every caller.
    """
    out: list[tuple[str, str, str, float]] = []
    for policy in INDEX_POLICIES:
        table = tables[policy]
        for scene in MEASURED_SCENES:
            for obs in informative_separators(scene, table):
                out.append((scene, obs, policy,
                            separation_margin(scene, obs, table)))
    return tuple(sorted(out, key=lambda cell: cell[3]))


def evidence_width(scene: str, tables: dict[str, dict]) -> int:
    """How many informative cells `scene`'s grade rests on. A groupby, not a filter.

    The number the census could not show. Measured at eight seeds it is `1` for
    `freezing`, `4` for `head_on`, and `0` for the other three — and that single
    column answers the question STATE.md carried three cycles: **`freezing` is
    not the fragile scene, it is the scene with a width-1 evidence base.**

    The doubling deleted one cell from `freezing` and one from `head_on`. Equal
    losses; only the width-1 grade moved. The other three scenes did not move
    because they have nothing to lose — their stability under doubling is
    vacuous, not earned, and reading the 4/5-stable census without this column
    reports four scenes agreeing when only one of them was ever at risk.
    """
    return sum(1 for cell in nonconstant_cell_margins(tables) if cell[0] == scene)


def evidence_widths(tables: dict[str, dict]) -> dict[str, int]:
    """:func:`evidence_width` over all five scenes. Total, so a caller cannot
    scope the reading to the scenes it already suspects."""
    return {scene: evidence_width(scene, tables) for scene in MEASURED_SCENES}


#: The two time-to-collision columns, named once so the family split below is a
#: constant rather than a literal re-typed at each call site. `min_ttc` is the
#: hindsight table's episode-wide minimum; `ttc` its causal counterpart at the
#: read index (see :data:`CAUSAL_OBSERVABLES`). Both are `clearance / closing
#: speed` — a ratio whose denominator crosses zero, which is the property under
#: test.
TTC_FAMILY: tuple[str, ...] = ("min_ttc", "ttc")


def is_ttc_family(observable: str) -> bool:
    """Is this column one of the two time-to-collision readings?

    Predicate-shaped rather than set-shaped, and the shape was chosen after
    the price was known (D-349) — recorded that way so a later cycle can
    disagree. The set-shaped spelling, `tuple(o for o in
    tail_extensions_by_observable() if o in TTC_FAMILY)`, grades
    ``DIFFERENCE``/``COLLECTION`` and is therefore a *revocable collection*,
    which owes a hand-written `guard_direction.PROBES` entry with a repo
    fixture and a permit/offend pair — the obligation D-334 discovered behind
    the two literals it had already paid for, whose cost is a fixture rather
    than a line. This spelling matches the three siblings in this module that
    were never guards (`is_constant` and its neighbours), for the same reason
    D-334 chose it there.

    The family's membership is still watched, and by the thing that should
    watch it: `exemption_control`'s tamper shrinks :data:`TTC_FAMILY` and reads
    the count of columns this predicate admits, so the registry cannot be
    narrowed without a reading moving.
    """
    return observable in TTC_FAMILY


def tail_extension(scene: str, observable: str, policy: str) -> float:
    """How far this column's own extremes moved **outward** under the doubling.

    In units of the eight-seed pooled span for that `(observable, policy)`, so
    columns measured in different units are comparable. The sixteen-seed tuples
    begin with the eight-seed ones verbatim, so the movement can only be
    outward: this is exactly *how much tail the second eight seeds revealed*.

    D-346 left the fragility coordinate as an open reading — margin rank does
    not order survival, and since :func:`separates` is pure min/max, what must
    order it is the tail. This is that reading made into a number, and it is
    **not** the tautology of measuring only the cells that died: it runs over
    every scene × observable, most of which separate nothing.

    `nan` when either count's column is non-finite, matching
    :func:`separation_margin`'s refusal to grade an infinite TTC.
    """
    at8, at16 = eight_seed_tables()[policy], doubled_tables()[policy]
    mine8 = np.asarray(at8[scene][observable], dtype=float)
    mine16 = np.asarray(at16[scene][observable], dtype=float)
    if not (np.isfinite(mine8).all() and np.isfinite(mine16).all()):
        return float("nan")
    pooled = np.concatenate([np.asarray(at8[s][observable], dtype=float)
                             for s in MEASURED_SCENES])
    if not np.isfinite(pooled).all():
        return float("nan")
    span = max(float(pooled.ptp()), _EPS)
    out = max(mine8.min() - mine16.min(), mine16.max() - mine8.max(), 0.0)
    return float(out / span)


def tail_extensions_by_observable() -> dict[str, tuple[float, ...]]:
    """:func:`tail_extension` over every scene × policy, grouped by column.

    Total over the measured surface, so a caller cannot scope the reading to
    the columns it already suspects — the same reason :func:`evidence_widths`
    walks all five scenes. `nan` cells are dropped here rather than at the
    reader, since a column that is non-finite at one index is still a column.
    """
    out: dict[str, list[float]] = {}
    for policy in INDEX_POLICIES:
        table = eight_seed_tables()[policy]
        for observable in _observables_of(table):
            for scene in MEASURED_SCENES:
                value = tail_extension(scene, observable, policy)
                if np.isfinite(value):
                    out.setdefault(observable, []).append(value)
    return {k: tuple(v) for k, v in out.items()}


def worst_tail_extension(observable: str) -> float:
    """The largest outward movement `observable` showed on any scene × policy.

    The *max*, not the mean: :func:`separates` reads one end of one column, so
    a family's exposure is set by its worst cell and an average would let four
    quiet scenes hide the one that moved. `nan` if the column never graded.
    """
    values = tail_extensions_by_observable().get(observable, ())
    return max(values) if values else float("nan")


def ttc_family_has_the_heavier_tail() -> bool:
    """Does every TTC column move further than every bounded column does?

    The D-346 hypothesis as a single boolean, kept as the **refuted control**:
    it reads `False`, and the column that moves furthest is `lateralness` —
    bounded to `[0, 1]` by construction and therefore the one column that
    *cannot* have a heavy tail in the ratio sense the hypothesis meant. So the
    TTC coincidence D-346 pinned is not explained by tail weight, and the
    fragility coordinate is not a property of the column at all.

    Stated as a strict all-vs-all comparison because a mean-vs-mean version
    would have passed on one outlier and reported a mechanism that is not there.
    """
    ttc = [worst_tail_extension(o) for o in TTC_FAMILY]
    rest = [worst_tail_extension(o) for o in sorted(
        set(OBSERVABLES + CAUSAL_OBSERVABLES) - set(TTC_FAMILY))]
    ttc = [v for v in ttc if np.isfinite(v)]
    rest = [v for v in rest if np.isfinite(v)]
    if not ttc or not rest:
        return False
    return min(ttc) > max(rest)


def facing_extension(scene: str, observable: str, policy: str) -> float:
    """:func:`tail_extension` restricted to the end of the column that faces the gap.

    The correction the two-ended reading needs, and the reason that reading
    fails. :func:`separates` compares **one** end of `scene`'s column against
    **one** end of the pooled rest; movement at the other end is invisible to
    it. :func:`tail_extension` takes the max over both ends, so it counts
    movement that cannot cost anything — and the whole ranked table turns on
    exactly that distinction, since the thinnest cell in the suite has the
    largest two-ended extension of any cell and the smallest facing one (zero).

    Both sides are summed: the gap closes when `scene`'s facing extreme moves
    outward *or* when the rest's facing extreme moves toward it, and the two
    are the same event to a min/max rule.

    Sign convention: positive ⇒ the gap-facing ends moved together, i.e. the
    doubling ate this much of the eight-seed span out of the gap. `nan` when
    either column is non-finite, and `nan` when the cell does not separate at
    eight seeds — there is no facing end to name when there is no gap.
    """
    at8, at16 = eight_seed_tables()[policy], doubled_tables()[policy]

    def sides(table):
        mine = np.asarray(table[scene][observable], dtype=float)
        rest = np.concatenate([np.asarray(table[s][observable], dtype=float)
                               for s in MEASURED_SCENES if s != scene])
        return mine, rest

    mine8, rest8 = sides(at8)
    mine16, rest16 = sides(at16)
    if not all(np.isfinite(a).all() for a in (mine8, rest8, mine16, rest16)):
        return float("nan")
    span = max(float(np.concatenate([mine8, rest8]).ptp()), _EPS)
    if mine8.min() > rest8.max():                    # mine sits above the rest
        moved = (mine8.min() - mine16.min()) + (rest16.max() - rest8.max())
    elif mine8.max() < rest8.min():                  # mine sits below the rest
        moved = (mine16.max() - mine8.max()) + (rest8.min() - rest16.min())
    else:
        return float("nan")                          # no gap ⇒ no facing end
    return float(moved / span)


def facing_extension_exceeds_margin(scene: str, observable: str,
                                    policy: str) -> bool:
    """Did the facing ends eat more than the whole eight-seed gap?

    The predicted-deletion test. It is a *prediction* and not a restatement of
    the sixteen-seed margin: both quantities are computed from the eight-seed
    gap and the movement of two extremes, with no reference to whether the cell
    still separates. On this suite it is exactly right five times out of five —
    ratios `0.00, 1.32, 1.83, 0.58, 0.00` against a threshold of `1`, with the
    two cells above it the two the doubling deleted.
    """
    face = facing_extension(scene, observable, policy)
    margin = separation_margin(scene, observable, eight_seed_tables()[policy])
    if not (np.isfinite(face) and np.isfinite(margin)) or margin <= 0:
        return False
    return face > margin


def format_tail_grade() -> str:
    """One-screen tail reading, per column and then per cell. A formatter, so it
    gets a test (D-342) rather than a residue-list slot."""
    worst = {o: worst_tail_extension(o)
             for o in tail_extensions_by_observable()}
    lines = ["column                  family    worst-ext  cells  (units of 8-seed span)"]
    for observable, value in sorted(worst.items(), key=lambda kv: -kv[1]):
        family = "ttc" if observable in TTC_FAMILY else "bounded"
        cells = len(tail_extensions_by_observable()[observable])
        lines.append(f"  {observable:<22} {family:<9} {value:8.4f}  {cells:^5}")
    lines.append(f"every TTC column above every bounded one: "
                 f"{ttc_family_has_the_heavier_tail()}  (D-346 hypothesis)")
    lines.append("cells at 8 seeds: margin, facing extension, predicted vs actual")
    for scene, obs, policy, margin in nonconstant_cell_margins(eight_seed_tables()):
        face = facing_extension(scene, obs, policy)
        died = separation_margin(scene, obs, doubled_tables()[policy]) <= 0
        lines.append(
            f"  {margin:+.4f}  face {face:+.4f}  ratio {face / margin:5.2f}  "
            f"predict {'die ' if facing_extension_exceeds_margin(scene, obs, policy) else 'live'}"
            f"  actual {'die ' if died else 'live'}  {scene}/{obs}@{policy}")
    return "\n".join(lines)


def format_evidence_grade() -> str:
    """One-screen evidence base at both seed counts. A formatter, so it gets a
    test (D-342) rather than a residue-list slot."""
    lines = ["scene                      width@8  width@16  grade@8 -> grade@16"]
    w8, w16 = evidence_widths(eight_seed_tables()), evidence_widths(doubled_tables())
    for scene in MEASURED_SCENES:
        mark = " <-" if not invisibility_survives_doubling(scene) else ""
        lines.append(f"  {scene:<24} {w8[scene]:^7}  {w16[scene]:^8}  "
                     f"{invisibility_reason(scene)} -> "
                     f"{invisibility_reason_at_16(scene)}{mark}")
    lines.append("cells at 8 seeds, thinnest first:")
    for scene, obs, policy, margin in nonconstant_cell_margins(eight_seed_tables()):
        lines.append(f"  {margin:+.4f}  {scene}/{obs}@{policy}")
    lines.append("cells at 16 seeds, thinnest first:")
    for scene, obs, policy, margin in nonconstant_cell_margins(doubled_tables()):
        lines.append(f"  {margin:+.4f}  {scene}/{obs}@{policy}")
    return "\n".join(lines)

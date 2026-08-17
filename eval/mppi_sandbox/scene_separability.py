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
    """
    tables = [None if p == "critical" else CAUSAL_OBSERVED[p] for p in INDEX_POLICIES]
    return all(is_constant(observable, t) for t in tables
               if observable in _observables_of(t))


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

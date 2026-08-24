# SPDX-License-Identifier: BSD-3-Clause
"""Is the cross-track vacuity ordered by path curvature? — STATE #1, and the answer is **no**.

D-360 swept the `cte_max` (peak) column and found it grades **exactly** the
partition `cte_rms_max` already graded — 1 `DISCRIMINATING`, 3 `VACUOUS_PASS`,
`RMS_BLIND = ()`. So the five vacuous cross-track cells are not an artefact of
which statistic is read off the trajectory. Its finding #2 offered the surviving
explanation, borrowed from the `2026-08-19 08:00` research feed entry (Nav2
issue #5925): the dominant cross-track failure mode of a horizon-based sampler
is **excited by path curvature**, so a straight scene cannot fail a cross-track
bar at any value. That reframes the vacuity as a **scene-geometry** gap rather
than a threshold gap, which is why it escapes the threshold-shopping refusal
that killed D-356/357/358 alternative (c).

D-360 was explicit that this was **three points read off scene names** with no
radius computed, and pinned the silence as `CURVATURE_UNMEASURED`. This module
computes it. Zero rollouts — reference paths are static yaml.

**Finding #1, and it refutes the hypothesis as stated: the one scene whose
cross-track bar grades is perfectly straight.** Six of the eight scenes have a
minimum curvature radius of **infinity** — their `reference_path.waypoints` are
exactly collinear (all six run down `x = 0` with evenly spaced points, turn
angle `0.000°` at every interior vertex; this is not a degenerate-waypoint
artefact, it is checked segment by segment). `cafe_obstacle_crossing_v0` is one
of those six — and it is the **sole `DISCRIMINATING` scene on both cross-track
bars** (D-358, D-360). A perfectly straight path grades a cross-track bar, so
curvature is **not** what makes such a bar gradeable in this suite. What excites
the excursion there is the **obstacle**: `cbf_mppi` swerves to a `1.0272 m` peak
around the crossing pedestrian on a path with no curvature at all. Path
curvature and obstacle avoidance are two independent excitation channels, and
the only one this registry's graded cell uses is the second.

**Finding #2 — D-360's ordering survives, but only inside the vacuous three.**
Among the scenes that declare a cross-track bar *and* grade `VACUOUS_PASS`, the
excitation ratio orders them exactly as headroom did:

=====================  ==========  ==========  ================  ==============
scene                  `R_min`     reach       reach / `R_min`   peak headroom
=====================  ==========  ==========  ================  ==============
`city_curved_v0`       2.4556 m    1.800 m     **0.733**         **2.18x**
`city_figure8_v0`      2.4992 m    1.500 m     0.600             9.25x
`cafe_straight_v0`     inf         1.200 m     0.000             23.26x
=====================  ==========  ==========  ================  ==============

Monotone, and in the direction the feed predicts — more curvature relative to
reach, nearer to grading. So the mechanism is *visible*; it is simply not the
one operating in the graded cell. The honest statement is narrower than D-360's:
curvature orders the **ungraded** scenes among themselves, and says nothing
about the boundary between graded and ungraded.

**Finding #3 — no scene in the registry reaches the excitation ratio at all.**
Nav2 #5925 reports the mode on a `0.6 m` U-turn radius against a `80 x 0.1 s`
horizon, i.e. a reach several metres long: a ratio well above **1**, where the
rollout endpoints land past the turn and reference-point selection goes
ambiguous. This suite's *largest* ratio is `0.733` and its horizon is
`30 x 0.1 s = 3.0 s` — every scene is below 1. This matters for the repair: the
cheap reading of D-360 finding #2 is "add a curved scene", and at these radii
that would **not** excite the mode either. `EXCITATION_UNREACHED` names it. A
scene authored to test the mechanism needs `R_min` small *relative to reach*,
which is a scenario-authoring decision (the user-blocked question), not a
threshold change.

Scope, stated before the numbers:

* Curvature is the **circumradius of consecutive waypoint triples** on the
  declared `reference_path`, minimised over interior vertices. That is the
  path *as authored*, not the path *as driven* — the executed trajectory is
  smoother, so `R_min` here is a **lower bound** on the radius the controller
  actually experiences, and the ratio is an **upper** bound. Both bounds point
  the same way as finding #3 (the true ratio is even further below 1).
* Reach is `horizon x dt x target_speed` from :class:`MPPIParams` defaults
  (`30 x 0.1 s`) and the scene's `target_speed_mps`. Arms that override the
  horizon are not modelled; :data:`REACH_USES_DEFAULT_HORIZON` carries that.
* A polyline has curvature only at its vertices, so `R_min` is a property of
  the **discretisation** as much as the shape. `city_figure8_v0` traverses its
  loop **twice** (17 waypoints = 8 segments x 2 + 1, exactly repeated), which
  changes path length but not `R_min`.

CLI:
    python -m eval.mppi_sandbox.path_curvature   # rc=1 on drift from CENSUS
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

from .scenario import load_scenario

#: Scenario directory the sweep reads. Same population as `cte_peak_vacuity`
#: and `cte_vacuity` — the eight `*_v0.yaml` scenes.
SCENARIO_DIR = Path(__file__).resolve().parents[1] / "scenarios"

#: Sampler reach uses the :class:`MPPIParams` default horizon, not any arm's
#: override. Arms that lengthen the horizon would raise their own ratio; none
#: in the current registry does, but nothing here checks that.
REACH_USES_DEFAULT_HORIZON = ("horizon", 30, "dt", 0.1)

#: `scene -> minimum curvature radius (m)` over interior waypoint triples;
#: `inf` means every interior vertex is collinear, i.e. the authored path is a
#: straight line. Seven of nine.
R_MIN: dict[str, float] = {
    "cafe_convoy_v0": float("inf"),
    "cafe_cut_in_v0": float("inf"),
    "cafe_freezing_v0": float("inf"),
    "cafe_head_on_v0": float("inf"),
    "cafe_obstacle_contested_v0": float("inf"),
    "cafe_obstacle_crossing_v0": float("inf"),
    "cafe_straight_v0": float("inf"),
    "city_curved_v0": 2.4556,
    "city_figure8_v0": 2.4992,
}

#: `scene -> horizon x dt x target_speed` (m). The along-path distance one
#: rollout spans at the scene's nominal speed.
REACH: dict[str, float] = {
    "cafe_convoy_v0": 1.500,
    "cafe_cut_in_v0": 1.500,
    "cafe_freezing_v0": 1.500,
    "cafe_head_on_v0": 1.500,
    "cafe_obstacle_contested_v0": 0.900,
    "cafe_obstacle_crossing_v0": 0.900,
    "cafe_straight_v0": 1.200,
    "city_curved_v0": 1.800,
    "city_figure8_v0": 1.500,
}

#: The six scenes whose authored reference path is exactly straight. Finding #1
#: is that this tuple contains the suite's only `DISCRIMINATING` cross-track
#: scene.
STRAIGHT_SCENES: tuple[str, ...] = (
    "cafe_convoy_v0",
    "cafe_cut_in_v0",
    "cafe_freezing_v0",
    "cafe_head_on_v0",
    "cafe_obstacle_contested_v0",
    "cafe_obstacle_crossing_v0",
    "cafe_straight_v0",
)

#: The scene that grades `DISCRIMINATING` on both `cte_rms_max` (D-358) and
#: `cte_max` (D-360). Named here so the test that it is *straight* — the whole
#: of finding #1 — cannot silently stop referring to the graded cell.
DISCRIMINATING_SCENE = "cafe_obstacle_crossing_v0"

#: Nav2 #5925's mode needs rollout endpoints to land past the turn, i.e. a
#: reach/radius ratio above this. No scene in the registry reaches it; the
#: largest is `city_curved_v0` at 0.733.
EXCITATION_RATIO_THRESHOLD = 1.0

#: The silence D-360 left as `CURVATURE_UNMEASURED` is discharged by this
#: module; this is the one that replaces it. Adding a curved scene at the
#: registry's current radii would not excite #5925's mode either — the ratio,
#: not the presence of curvature, is what is short.
EXCITATION_UNREACHED = (
    "max ratio 0.733 (city_curved_v0) < 1.0; Nav2 #5925 reports the mode "
    "at a ratio well above 1 (0.6 m radius against an 8 s horizon)"
)

#: Drift census: `scene -> (R_min, reach, ratio)` rounded to 4 dp, with `inf`
#: radius mapped to ratio `0.0`. Derived from the yaml on every call, so an
#: edit to any `reference_path` moves this and `drift()` goes red.
CENSUS: dict[str, tuple[float, float, float]] = {
    "cafe_convoy_v0": (float("inf"), 1.5, 0.0),
    "cafe_cut_in_v0": (float("inf"), 1.5, 0.0),
    "cafe_freezing_v0": (float("inf"), 1.5, 0.0),
    "cafe_head_on_v0": (float("inf"), 1.5, 0.0),
    "cafe_obstacle_contested_v0": (float("inf"), 0.9, 0.0),
    "cafe_obstacle_crossing_v0": (float("inf"), 0.9, 0.0),
    "cafe_straight_v0": (float("inf"), 1.2, 0.0),
    "city_curved_v0": (2.4556, 1.8, 0.733),
    "city_figure8_v0": (2.4992, 1.5, 0.6002),
}


def min_curvature_radius(waypoints: np.ndarray) -> float:
    """Smallest circumradius over consecutive interior waypoint triples.

    `inf` when every interior vertex is collinear. Coincident points give a
    zero-area triple and are treated as collinear rather than as a zero radius
    — a repeated waypoint is a discretisation accident, not a hairpin.
    """
    w = np.asarray(waypoints, dtype=float)[:, :2]
    best = float("inf")
    for i in range(1, len(w) - 1):
        a, b, c = w[i - 1], w[i], w[i + 1]
        ab = float(np.linalg.norm(b - a))
        bc = float(np.linalg.norm(c - b))
        ca = float(np.linalg.norm(a - c))
        area = abs(float(np.cross(b - a, c - a))) / 2.0
        if area < 1e-12:
            continue
        best = min(best, ab * bc * ca / (4.0 * area))
    return best


def reach(target_speed: float,
          horizon: int = REACH_USES_DEFAULT_HORIZON[1],
          dt: float = REACH_USES_DEFAULT_HORIZON[3]) -> float:
    """Along-path distance one rollout spans at the scene's nominal speed."""
    return horizon * dt * target_speed


def excitation_ratio(r_min: float, reach_m: float) -> float:
    """`reach / R_min`, with a straight path (`inf` radius) mapping to 0.0."""
    if not np.isfinite(r_min):
        return 0.0
    return reach_m / r_min


def measure() -> dict[str, tuple[float, float, float]]:
    """Re-derive `scene -> (R_min, reach, ratio)` from the scenario yaml."""
    out: dict[str, tuple[float, float, float]] = {}
    for path in sorted(SCENARIO_DIR.glob("*_v0.yaml")):
        sc = load_scenario(path)
        key = path.stem
        r_min = min_curvature_radius(sc.waypoints)
        rch = reach(sc.target_speed)
        out[key] = (
            r_min if not np.isfinite(r_min) else round(r_min, 4),
            round(rch, 4),
            round(excitation_ratio(r_min, rch), 4),
        )
    return out


def straight_scenes() -> tuple[str, ...]:
    """Scenes whose authored reference path has no curvature at all."""
    return tuple(k for k, (r, _, _) in sorted(measure().items())
                 if not np.isfinite(r))


def unreached() -> tuple[str, ...]:
    """Scenes below :data:`EXCITATION_RATIO_THRESHOLD` — currently all eight."""
    return tuple(k for k, (_, _, ratio) in sorted(measure().items())
                 if ratio < EXCITATION_RATIO_THRESHOLD)


def drift() -> list[str]:
    """Lines describing every disagreement between :data:`CENSUS` and the yaml."""
    live = measure()
    lines: list[str] = []
    for key in sorted(set(CENSUS) | set(live)):
        want = CENSUS.get(key)
        got = live.get(key)
        if want is None:
            lines.append(f"{key}: new scene {got}")
        elif got is None:
            lines.append(f"{key}: scene gone (census {want})")
        elif want != got:
            lines.append(f"{key}: census {want} != derived {got}")
    if tuple(straight_scenes()) != STRAIGHT_SCENES:
        lines.append(
            f"STRAIGHT_SCENES {STRAIGHT_SCENES} != derived {straight_scenes()}")
    return lines


def main() -> int:
    live = measure()
    print(f"path_curvature — {len(live)} scenes, "
          f"{len(straight_scenes())} exactly straight")
    for key, (r_min, rch, ratio) in sorted(live.items()):
        mark = " <- DISCRIMINATING" if key == DISCRIMINATING_SCENE else ""
        r_txt = "inf" if not np.isfinite(r_min) else f"{r_min:.4f}"
        print(f"  {key:28s} R_min={r_txt:>8s}  reach={rch:.3f}  "
              f"ratio={ratio:.4f}{mark}")
    print(f"EXCITATION_UNREACHED: {EXCITATION_UNREACHED}")
    lines = drift()
    for line in lines:
        print(f"DRIFT: {line}")
    return 1 if lines else 0


if __name__ == "__main__":
    sys.exit(main())

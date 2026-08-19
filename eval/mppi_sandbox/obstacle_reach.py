# SPDX-License-Identifier: BSD-3-Clause
"""The other excitation channel: does an obstacle stand in the path when the robot arrives?

D-361 measured the **curvature** channel and refuted it as the mechanism behind
the cross-track partition: six of eight scenes are exactly straight, and
`cafe_obstacle_crossing_v0` — the **sole** `DISCRIMINATING` scene on both
`cte_rms_max` (D-358) and `cte_max` (D-360) — is one of the six. Its finding #1
named the surviving channel without measuring it: *"What excites the excursion
there is the **obstacle** … Path curvature and obstacle avoidance are two
independent excitation channels, and the only one this registry's graded cell
uses is the second."* This module measures the second one, the way
:mod:`path_curvature` measured the first. Zero rollouts — obstacle schedules
and reference paths are both static yaml.

**Finding #1 — the obstacle channel separates the cross-track partition
exactly, which curvature never did.** Four scenes declare a `cte_max` bar. Of
those four, **one** has any obstacle at all, and it is the graded one:

=========================  =========  ==========  ===========  ==============
scene                      obstacles  `d_enc`     forced       cte_max verdict
=========================  =========  ==========  ===========  ==============
`cafe_obstacle_crossing_v0`  5        0.0930 m    **0.5070 m**  DISCRIMINATING
`cafe_straight_v0`           0        inf         0.0000        VACUOUS_PASS
`city_curved_v0`             0        inf         0.0000        VACUOUS_PASS
`city_figure8_v0`            0        inf         0.0000        VACUOUS_PASS
=========================  =========  ==========  ===========  ==============

The three vacuous scenes are not *weakly* excited on this channel — they carry
**no obstacle whatsoever**, so the forced excursion is identically zero and no
bar value could be failed by avoidance. Against D-361's curvature table, which
ordered the losers among themselves (0.733 / 0.600 / 0.000) but put the winner
at the *bottom* of its own ordering, this channel is `1 → 0, 0, 0`: a clean
partition, in the right direction, with the graded cell on the excited side.
:data:`CHANNEL_SEPARATES` pins that.

**Finding #2 — the two scenes that force *more* excursion than the graded one
declare no `cte_max` bar at all.** Ranked by forced excursion:

    cafe_cut_in_v0     0.6000 m   (no cte_max declared)
    cafe_head_on_v0    0.5900 m   (no cte_max declared)
    cafe_obstacle_crossing_v0  0.5070 m   cte_max = 1.0  <- the only graded one
    cafe_convoy_v0     0.4798 m   (no cte_max declared)
    cafe_freezing_v0   0.0000 m   (no cte_max declared)

So the cross-track column is not short of excitation — it is short of **bars on
the scenes that have it**. STATE's standing user-blocked item ("4 scenes declare
no `cte_max`") has been a bookkeeping observation; this gives it a magnitude and
a direction. `cut_in` forces `0.6000 m` of lateral deviation — 18% more than the
graded scene — and contributes nothing to the column. :data:`UNBARRED_EXCITED`
names the two that clear the graded scene's own forced excursion; `convoy`'s
`0.4798 m` falls just under it and `freezing` is at zero, so the unbarred four
are **not** uniformly excited and declaring a bar on all four would re-create
the vacuity somewhere else. Declaring a bar there is still scene-authoring (what the bar
should *be* is not measured here), so it stays user-blocked — but unlike the
curved-scene proposal D-361 priced at ratio 0.733, this one needs **no new
scene and no new rollouts**, only a constant in a yaml that already earns it.

**Finding #3 — the excitation is real but sub-unity, on this channel too.**
`cafe_obstacle_crossing_v0`'s forced `0.5070 m` sits against a declared
`cte_max` of `1.0`, i.e. a ratio of `0.5070`. The scene grades anyway (D-360:
`cbf_mppi` peaks at `1.0272`), so the *attained* excursion exceeds the
geometrically forced one by roughly 2x — the controller swerves wider than it
has to. That gap is the honest reason this ratio must not be read as a
gradeability predictor the way D-361's threshold was: a ratio of `0.5` here
grades, so the channel's threshold is **not** 1.0 and this module does not
claim one. :data:`RATIO_NOT_A_THRESHOLD` carries that.

Scope, stated before the numbers:

* `d_enc` is a **space-time** closest approach: the robot is placed at the
  station it would occupy at time `t` if it tracked the reference path exactly
  at `target_speed_mps` from `t = 0`, and the obstacle at `ob.position(t)`. The
  time-blind alternative — obstacle track versus the path polyline, ignoring
  when each is there — is computed too (:func:`measure` returns it as
  `d_static`) and it **disagrees**: `cafe_freezing_v0` reads `0.3000 m`
  time-blind and `0.7428 m` on the encounter, because its two actors have swept
  past before the robot arrives. Reporting the time-blind number would have
  invented an excitation that does not happen.
* The robot is assumed to track the reference **exactly**. A controller that
  has already begun to deviate meets the obstacle elsewhere, so `forced` is the
  excursion demanded of a *perfect* tracker — a lower bound on what avoidance
  costs, not a prediction of the attained CTE. Finding #3 is the measured size
  of that gap on the one scene where both numbers exist.
* `forced` is `max(0, (ROBOT_RADIUS + ob.radius) - d_enc)`: the lateral shift
  that brings the two circles to touching, no safety margin added. Adding
  D-356's `d_safe` would raise every non-zero entry by the same constant and
  change no verdict here, since the vacuous three are at exactly zero.

CLI:
    python -m eval.mppi_sandbox.obstacle_reach   # rc=1 on drift from CENSUS
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

from .run import ROBOT_RADIUS
from .scenario import load_scenario

#: Scenario directory the sweep reads. Same population as :mod:`path_curvature`,
#: :mod:`cte_vacuity` and :mod:`cte_peak_vacuity` — the eight `*_v0.yaml` scenes.
SCENARIO_DIR = Path(__file__).resolve().parents[1] / "scenarios"

#: Time step of the nominal traversal, seconds. Fine enough that the reported
#: `d_enc` is insensitive to it at 4 dp for every scene in the registry.
NOMINAL_DT = 0.02

#: `scene -> (d_enc, forced, d_static)` in metres, 4 dp; `inf` `d_enc` means
#: the scene declares no obstacles at all, and then `forced` is `0.0`.
CENSUS: dict[str, tuple[float, float, float]] = {
    "cafe_convoy_v0": (0.1202, 0.4798, 0.0),
    "cafe_cut_in_v0": (0.0, 0.6, 0.2),
    "cafe_freezing_v0": (0.7428, 0.0, 0.3),
    "cafe_head_on_v0": (0.01, 0.59, 0.0),
    "cafe_obstacle_crossing_v0": (0.093, 0.507, 0.0),
    "cafe_straight_v0": (float("inf"), 0.0, float("inf")),
    "city_curved_v0": (float("inf"), 0.0, float("inf")),
    "city_figure8_v0": (float("inf"), 0.0, float("inf")),
}

#: Scenes carrying no `dynamic_obstacles:` block. Finding #1 is that this tuple
#: contains **exactly** the cross-track column's three `VACUOUS_PASS` scenes.
OBSTACLE_FREE_SCENES: tuple[str, ...] = (
    "cafe_straight_v0",
    "city_curved_v0",
    "city_figure8_v0",
)

#: The scene that grades `DISCRIMINATING` on both cross-track bars (D-358,
#: D-360), carried here so finding #1 cannot silently stop referring to it.
DISCRIMINATING_SCENE = "cafe_obstacle_crossing_v0"

#: Finding #1 in one assertion: among scenes that declare a `cte_max`, having an
#: obstacle and grading `DISCRIMINATING` are the same set. `path_curvature` had
#: no such statement to make — its channel put the graded scene at ratio 0.0.
CHANNEL_SEPARATES = (
    "of the 4 scenes declaring cte_max, exactly 1 has any obstacle "
    "(cafe_obstacle_crossing_v0, forced 0.5070 m) and it is exactly the 1 "
    "that grades DISCRIMINATING; the other 3 are obstacle-free, so their "
    "forced excursion is identically 0 at any bar value"
)

#: Finding #2: scenes whose forced excursion exceeds the graded scene's yet
#: declare no `cte_max`. Ordered by forced excursion, descending.
UNBARRED_EXCITED: tuple[str, ...] = (
    "cafe_cut_in_v0",
    "cafe_head_on_v0",
)

#: Finding #3. The graded scene's ratio is `0.5070` and it grades anyway, so
#: unlike `path_curvature.EXCITATION_RATIO_THRESHOLD` there is no 1.0 line to
#: draw on this channel — one data point above zero cannot locate one.
RATIO_NOT_A_THRESHOLD = (
    "forced/cte_max = 0.5070 on the one graded scene, which grades; so this "
    "channel's gradeability threshold is below 0.5 and is not located by a "
    "single non-zero point — do not read the ratio as a predictor"
)


def nominal_traversal(waypoints: np.ndarray, speed: float,
                      dt: float = NOMINAL_DT) -> tuple[np.ndarray, np.ndarray]:
    """`(t, xy)` of a perfect tracker running the polyline at constant `speed`."""
    w = np.asarray(waypoints, dtype=float)[:, :2]
    seg = np.linalg.norm(np.diff(w, axis=0), axis=1)
    station = np.concatenate([[0.0], np.cumsum(seg)])
    t = np.arange(0.0, station[-1] / speed + dt, dt)
    s = np.clip(t * speed, 0.0, station[-1])
    xy = np.stack([np.interp(s, station, w[:, 0]),
                   np.interp(s, station, w[:, 1])], axis=1)
    return t, xy


def scene_reach(scenario) -> tuple[float, float, float]:
    """`(d_enc, forced, d_static)` for one scenario.

    `d_enc` is the space-time closest approach of any obstacle *centre* to the
    nominal robot position; `forced` the lateral shift that would restore
    circle-to-circle contact; `d_static` the time-blind distance from the
    obstacle track to the reference polyline's vertices. An obstacle-free
    scene gives `(inf, 0.0, inf)`.
    """
    if not scenario.obstacles:
        return float("inf"), 0.0, float("inf")
    t, xy = nominal_traversal(scenario.waypoints, scenario.target_speed)
    w = np.asarray(scenario.waypoints, dtype=float)[:, :2]
    d_enc, forced, d_static = float("inf"), 0.0, float("inf")
    for ob in scenario.obstacles:
        pos = ob.position(t)
        d = float(np.min(np.linalg.norm(pos - xy, axis=1)))
        if d < d_enc:
            d_enc = d
            forced = max(0.0, (ROBOT_RADIUS + ob.radius) - d)
        blind = np.linalg.norm(pos[:, None, :] - w[None, :, :], axis=2)
        d_static = min(d_static, float(blind.min()))
    return d_enc, forced, d_static


def measure() -> dict[str, tuple[float, float, float]]:
    """Re-derive `scene -> (d_enc, forced, d_static)` from the scenario yaml."""
    out: dict[str, tuple[float, float, float]] = {}
    for path in sorted(SCENARIO_DIR.glob("*_v0.yaml")):
        d_enc, forced, d_static = scene_reach(load_scenario(path))
        out[path.stem] = (
            d_enc if not np.isfinite(d_enc) else round(d_enc, 4),
            round(forced, 4),
            d_static if not np.isfinite(d_static) else round(d_static, 4),
        )
    return out


def obstacle_free() -> tuple[str, ...]:
    """Scenes declaring no obstacles — the excitation-free side of finding #1."""
    return tuple(k for k, (d, _, _) in sorted(measure().items())
                 if not np.isfinite(d))


def declared_bars() -> dict[str, float]:
    """`scene -> cte_max` for the scenes that declare one. Four of eight."""
    out: dict[str, float] = {}
    for path in sorted(SCENARIO_DIR.glob("*_v0.yaml")):
        bar = load_scenario(path).acceptance.get("cte_max")
        if bar is not None:
            out[path.stem] = float(bar)
    return out


def unbarred_excited(floor: float = 0.5070) -> tuple[str, ...]:
    """Scenes forcing at least `floor` metres of excursion with no `cte_max`.

    Default `floor` is the graded scene's own forced excursion, so the result
    is "excited at least as much as the one cell that grades, and unbarred".
    """
    bars = declared_bars()
    return tuple(k for k, (_, forced, _) in sorted(measure().items())
                 if k not in bars and forced >= floor)


def drift() -> list[str]:
    """Lines describing every disagreement between :data:`CENSUS` and the yaml."""
    live = measure()
    lines: list[str] = []
    for key in sorted(set(CENSUS) | set(live)):
        want, got = CENSUS.get(key), live.get(key)
        if want is None:
            lines.append(f"{key}: new scene {got}")
        elif got is None:
            lines.append(f"{key}: scene gone (census {want})")
        elif want != got:
            lines.append(f"{key}: census {want} != derived {got}")
    if tuple(obstacle_free()) != OBSTACLE_FREE_SCENES:
        lines.append(f"OBSTACLE_FREE_SCENES {OBSTACLE_FREE_SCENES} "
                     f"!= derived {obstacle_free()}")
    if tuple(unbarred_excited()) != UNBARRED_EXCITED:
        lines.append(f"UNBARRED_EXCITED {UNBARRED_EXCITED} "
                     f"!= derived {unbarred_excited()}")
    return lines


def main() -> int:
    live = measure()
    bars = declared_bars()
    print(f"obstacle_reach — {len(live)} scenes, "
          f"{len(obstacle_free())} obstacle-free, {len(bars)} declare cte_max")
    for key, (d_enc, forced, d_static) in sorted(live.items()):
        bar = bars.get(key)
        ratio = f"{forced / bar:.4f}" if bar else "  (no bar)"
        d_txt = "inf" if not np.isfinite(d_enc) else f"{d_enc:.4f}"
        mark = " <- DISCRIMINATING" if key == DISCRIMINATING_SCENE else ""
        print(f"  {key:28s} d_enc={d_txt:>8s}  forced={forced:.4f}  "
              f"ratio={ratio}{mark}")
    print(f"CHANNEL_SEPARATES: {CHANNEL_SEPARATES}")
    print(f"UNBARRED_EXCITED: {UNBARRED_EXCITED}")
    print(f"RATIO_NOT_A_THRESHOLD: {RATIO_NOT_A_THRESHOLD}")
    lines = drift()
    for line in lines:
        print(f"DRIFT: {line}")
    return 1 if lines else 0


if __name__ == "__main__":
    sys.exit(main())

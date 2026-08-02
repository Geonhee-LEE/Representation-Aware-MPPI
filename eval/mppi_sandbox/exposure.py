# SPDX-License-Identifier: BSD-3-Clause
"""Static hazard-*exposure* screen — a simulation-free predictor of Q-040.

Measured 2026-08-02 18:00, adding five actors to `cafe_obstacle_crossing_v0`
split its two controllers' admissible `lam` windows (`stock_mppi` [0.4, 0.8]
vs `risk_mppi` [1.6, 3.2]) where they had overlapped completely while the
scene was empty. It is the **only** `per_arm` cell in the eight-scene matrix —
and `cafe_convoy_v0` carries the *same five actors* at the *same* footprint
without the effect. So obstacle **count** cannot be what predicts separation.

Q-040 asks what does. The mechanism 18:00 established is cost *magnitude*: the
arm carrying the extra cost term moved 8x, the arm without it 2x, so windows
separate when the two arms' cost landscapes scale differently. A collision
term's contribution is a **time-integral**, which is why this module measures
time-in-contest rather than obstacle count:

    a scene's hazard exposure is the fraction of its nominal traversal
    during which the reference-following robot is within `contest_radius`
    of at least one obstacle.

"Nominal" means the reference path walked at `target_speed_mps` with **no
controller in the loop**. That is deliberate, and it is what makes this a
*screen* in feasibility.py's sense rather than another measurement: it costs
milliseconds, it cannot depend on which controller you were going to run, and
it therefore predicts a property of the (scene, pair) cell from the scenario
yaml alone. The price is that it ignores the detour the planner would actually
take — so treat a verdict as a *prediction to be falsified by calibration*,
never as a substitute for `lam_windows.yaml`.

Correlation over eight scenes with one positive is not evidence — any
statistic that happens to rank the crossing scene first would "separate" it.
The claim is only worth making because it is checked by a **controlled
intervention** in `eval/scenarios/variants/`: hold obstacle count, footprint,
speed and geometry fixed, change *only* the schedule, and see whether the
windows follow the exposure. See `tests/test_hazard_exposure.py`.

----

**The timing model is falsified, and this module carries the error bar (Q-044,
D-023).** D-022 showed the closed loop does not traverse at `target_speed_mps`:
across the obstacle-carrying scenes the realized / nominal duration ratio spans
`TIMING_RATIO_BAND`. Since a hazard is a *rendezvous in time*, that error
propagates straight into `contested_fraction` — and `nominal_traversal` is the
only timing model a simulation-free screen has.

Q-044 asked what such a screen is then allowed to assume. The answer taken here
is **(b): keep the declared nominal, but never report a bare point estimate.**
`exposure_band` re-walks the same geometry under every duration ratio in the
measured band and returns the resulting `[lo, hi]` interval; `separates` and
`rank_with_band` refuse to order two scenes whose intervals overlap. What that
buys is not precision — it is the *refusal to over-read*, which is the specific
failure this cycle was cleaning up after.

Two consequences worth stating up front, because they bound what the screen is
still good for:

* **Static-obstacle scenes are exempt, exactly.** Rescaling the traversal speed
  rescales `contested_s` and `traversal_s` by the same factor when nothing
  moves, so a static scene's band has width **0** and its point estimate keeps
  full authority. The screen degrades in proportion to actor motion, not
  uniformly.
* **On the current matrix, the moving-obstacle bands very nearly all overlap.**
  Exactly one of the ten scene pairs separates, and it involves
  `cafe_cut_in_v0`, which is unreportable for an unrelated reason (it never
  completes). So D-018's headline reading — contested fraction **74 %**
  (crossing) vs **43 %** (convoy) — is **not citable**: those are `[0.22, 0.83]`
  and `[0.15, 0.66]`. D-018's *refutation* of exposure-as-predictor is
  untouched and if anything strengthened; what dies is the point-ranking.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Iterable, Sequence

import numpy as np

from .obstacles import CircleObstacle
from .scenario import Scenario, load_scenario

#: Surface-to-surface distance under which the robot is "in contest" with an
#: obstacle. Not a collision threshold — scenes set `min_distance_to_obstacle`
#: around 0.30 m, so 1.0 m is comfortably the band where a collision cost term
#: is *active but not yet dominant*, which is the regime that sets how far the
#: two arms' cost magnitudes diverge.
CONTEST_RADIUS = 1.0

#: Matches `ab.run_arm` / the sandbox diff-drive footprint.
ROBOT_RADIUS = 0.3

#: Nominal-traversal sampling step. 0.1 s over a ~20 s scene is 200 samples x
#: 5 obstacles — microseconds, and fine enough that a 0.75 m/s actor moves
#: 7.5 cm between samples.
DT = 0.1

#: Measured closed-loop / `nominal_traversal` duration ratio across the five
#: obstacle-carrying scenes, `risk_mppi` seed 0, 2026-08-03 01:00 (D-023):
#: crossing **0.557**, convoy 1.633, freezing 1.700, head_on 2.038 — and
#: `cafe_cut_in_v0` **15.0**, which is not a timing error but the scene's known
#: non-completion (it runs out the 120 s cap; Q-037 ruled that a scene defect
#: and it is excluded from every reportable matrix). Folding that outlier in
#: would widen the band 27x on the strength of a scene nobody may cite, so the
#: band is taken over the *reportable* scenes and the outlier is kept beside it.
#: Obstacle-free scenes contribute nothing — exposure is undefined there.
#: Pinned against re-measurement by `tests/test_exposure_timing_band.py`.
TIMING_RATIO_BAND = (0.557, 2.038)

#: The same statistic with the non-completing scene folded back in — what
#: D-022 quoted as "0.56x to 15x". Kept so the exclusion above stays visible
#: rather than being silently baked into one number.
TIMING_RATIO_BAND_WITH_DEFECT = (0.557, 15.0)

#: Duration ratios sampled across the band. Geometric because the quantity is a
#: ratio; 41 points resolve `contested_fraction`'s interior structure (it is
#: **not** monotone in the ratio — the crossing scene peaks near 0.8, inside the
#: band, so evaluating only the endpoints understates the interval).
BAND_GRID = 41


@dataclass(frozen=True)
class HazardExposure:
    """One scene's nominal-traversal exposure profile."""

    scenario: str
    n_obstacles: int
    traversal_s: float
    #: Seconds of the traversal spent within `CONTEST_RADIUS` of >= 1 obstacle.
    contested_s: float
    #: Largest number of obstacles simultaneously inside `CONTEST_RADIUS`.
    peak_contesting: int
    #: Closest surface-to-surface approach along the *nominal* path. Negative
    #: means the reference path itself passes through an obstacle — expected,
    #: since the nominal robot does not dodge.
    min_clearance: float

    @property
    def contested_fraction(self) -> float:
        """`contested_s / traversal_s` — the scale-free form, since scenes
        differ in both length and speed (`cafe_obstacle_crossing_v0` runs at
        0.3 m/s, `cafe_convoy_v0` at the 0.5 m/s default)."""
        return self.contested_s / self.traversal_s if self.traversal_s > 0 else 0.0

    def __str__(self) -> str:  # pragma: no cover - reporting sugar
        return (f"{self.scenario}: {self.n_obstacles} obs, "
                f"contested {self.contested_s:.1f}/{self.traversal_s:.1f} s "
                f"({self.contested_fraction:.0%}), peak {self.peak_contesting}, "
                f"min clearance {self.min_clearance:+.2f} m")


def nominal_traversal(scenario: Scenario, dt: float = DT,
                      duration_ratio: float = 1.0) -> np.ndarray:
    """(T, 3) `[t, x, y]` of the reference path walked at `target_speed`.

    Arc-length parameterised over the waypoint polyline, so a scene's own
    `target_speed_mps` sets both the duration and — crucially for a moving
    obstacle — *when* the robot is at each point. Two scenes with identical
    actor schedules and different speeds have different exposure, which is
    the correct behaviour: the hazard is a rendezvous, not a place.

    `duration_ratio` walks the *same* polyline in `ratio x` the nominal time —
    the one-parameter perturbation D-022's measurement licenses. The geometry
    is untouched and the obstacle schedules keep their own absolute clock, so
    varying it moves exactly the rendezvous and nothing else. `1.0` is the
    declared nominal and leaves every existing caller bit-identical.
    """
    xy = np.asarray(scenario.waypoints, dtype=float)[:, :2]
    seg = np.linalg.norm(np.diff(xy, axis=0), axis=1)
    s_wp = np.concatenate([[0.0], np.cumsum(seg)])
    total = float(s_wp[-1])
    speed = max(float(scenario.target_speed), 1e-6) / max(duration_ratio, 1e-6)
    duration = total / speed
    t = np.arange(0.0, duration + dt, dt)
    s = np.minimum(t * speed, total)
    return np.stack([t,
                     np.interp(s, s_wp, xy[:, 0]),
                     np.interp(s, s_wp, xy[:, 1])], axis=1)


def clearance_matrix(traj: np.ndarray, obstacles: Sequence[CircleObstacle],
                     robot_radius: float = ROBOT_RADIUS) -> np.ndarray:
    """(T, N) surface-to-surface clearance per sample per obstacle.

    Empty `(T, 0)` when the scene has no obstacles — callers must handle that
    rather than get a silent `+inf`, because "no obstacles" is exactly the
    defect 17:00's screen found in four of eight scenes.
    """
    t, xy = traj[:, 0], traj[:, 1:3]
    if not obstacles:
        return np.empty((len(t), 0))
    return np.stack([
        np.linalg.norm(xy - ob.position(t), axis=1) - ob.radius - robot_radius
        for ob in obstacles
    ], axis=1)


def hazard_exposure(path: str, *, contest_radius: float = CONTEST_RADIUS,
                    dt: float = DT,
                    duration_ratio: float = 1.0) -> HazardExposure:
    """Screen one scenario yaml. Simulates nothing."""
    scen = load_scenario(path)
    traj = nominal_traversal(scen, dt=dt, duration_ratio=duration_ratio)
    clear = clearance_matrix(traj, scen.obstacles)
    duration = float(traj[-1, 0])
    if clear.shape[1] == 0:
        return HazardExposure(scenario=os.path.basename(path), n_obstacles=0,
                              traversal_s=duration, contested_s=0.0,
                              peak_contesting=0, min_clearance=float("inf"))
    contesting = clear < contest_radius                      # (T, N) bool
    return HazardExposure(
        scenario=os.path.basename(path),
        n_obstacles=clear.shape[1],
        traversal_s=duration,
        contested_s=float(contesting.any(axis=1).sum()) * dt,
        peak_contesting=int(contesting.sum(axis=1).max()),
        min_clearance=float(clear.min()),
    )


def screen_scenarios(paths: Iterable[str], **kw) -> list[HazardExposure]:
    """Screen many, sorted by descending exposure — the ranking Q-040 asks
    about is the whole output, so return it ordered rather than making every
    caller re-sort."""
    return sorted((hazard_exposure(p, **kw) for p in paths),
                  key=lambda e: e.contested_fraction, reverse=True)


@dataclass(frozen=True)
class ExposureBand:
    """One scene's `contested_fraction` as an interval, not a number.

    `point` is what `hazard_exposure` reports at the declared nominal, kept so
    the artifact shows both what was previously cited and how much of the band
    it occupies.
    """

    scenario: str
    n_obstacles: int
    point: float
    lo: float
    hi: float
    #: The (min, max) duration ratios the interval was taken over.
    ratio_band: tuple[float, float]

    @property
    def width(self) -> float:
        return self.hi - self.lo

    @property
    def is_timing_sensitive(self) -> bool:
        """False exactly when nothing in the scene moves — see the module
        docstring's exemption. A zero-width band means the point estimate is
        the whole truth and may be ranked freely."""
        return self.width > 1e-9

    def separates(self, other: "ExposureBand") -> bool:
        """Do the two intervals fail to overlap? Only then is a claim that one
        scene is more contested than the other supported by this screen.

        Touching intervals do **not** separate: the band is a coarse
        one-parameter sweep, so an exactly-shared endpoint is far inside its
        own resolution.
        """
        return self.lo > other.hi or other.lo > self.hi

    def __str__(self) -> str:  # pragma: no cover - reporting sugar
        tag = "" if self.is_timing_sensitive else "  (static — exact)"
        return (f"{self.scenario}: {self.n_obstacles} obs, contested "
                f"[{self.lo:.0%}, {self.hi:.0%}] (nominal {self.point:.0%}) "
                f"over duration ratio "
                f"{self.ratio_band[0]:.2f}-{self.ratio_band[1]:.2f}{tag}")


def exposure_band(path: str, *,
                  ratio_band: tuple[float, float] = TIMING_RATIO_BAND,
                  n_grid: int = BAND_GRID, **kw) -> ExposureBand:
    """`hazard_exposure` re-walked across the measured timing band.

    Simulates nothing — the band constant is what carries the (already paid
    for) measurement, so this stays a millisecond screen. That was the point
    of answering Q-044 with (b) rather than (a).
    """
    lo_r, hi_r = ratio_band
    ratios = np.geomspace(lo_r, hi_r, n_grid) if hi_r > lo_r else np.array([lo_r])
    fracs = [hazard_exposure(path, duration_ratio=float(r), **kw).contested_fraction
             for r in ratios]
    nominal = hazard_exposure(path, **kw)
    return ExposureBand(scenario=nominal.scenario,
                        n_obstacles=nominal.n_obstacles,
                        point=nominal.contested_fraction,
                        lo=float(min(fracs)), hi=float(max(fracs)),
                        ratio_band=(float(lo_r), float(hi_r)))


def rank_with_band(paths: Iterable[str], **kw) -> tuple[list[ExposureBand],
                                                        list[tuple[str, str]]]:
    """`(bands sorted by midpoint, pairs the screen refuses to order)`.

    The second element is the load-bearing one. `screen_scenarios` returns a
    total order and says nothing about whether it earned one; this returns the
    order *plus* every pair for which the order is an artifact of reading a
    falsified point estimate. A caller that ignores the second element has
    reproduced D-018's over-reading.
    """
    bands = sorted((exposure_band(p, **kw) for p in paths),
                   key=lambda b: -(b.lo + b.hi))
    incomparable = [(a.scenario, b.scenario)
                    for i, a in enumerate(bands) for b in bands[i + 1:]
                    if not a.separates(b)]
    return bands, incomparable


def main(argv: Sequence[str] | None = None) -> int:  # pragma: no cover - CLI
    import argparse
    import glob

    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--scenarios", default="eval/scenarios/*.yaml")
    ap.add_argument("--contest-radius", type=float, default=CONTEST_RADIUS)
    ap.add_argument("--point-estimate", action="store_true",
                    help="report the bare nominal fraction (D-018's form). "
                         "Not citable for moving-obstacle scenes — see Q-044.")
    args = ap.parse_args(argv)

    from .calibrate_lam import is_scenario_yaml
    paths = [p for p in sorted(glob.glob(args.scenarios)) if is_scenario_yaml(p)]
    if args.point_estimate:
        for e in screen_scenarios(paths, contest_radius=args.contest_radius):
            print(e)
        return 0

    bands, incomparable = rank_with_band(paths, contest_radius=args.contest_radius)
    for b in bands:
        print(b)
    print(f"\nordered pairs the screen refuses: {len(incomparable)}")
    for a, b in incomparable:
        print(f"  {a} ~ {b}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())

# SPDX-License-Identifier: BSD-3-Clause
"""Q-189: the excursion's clearance yield saturates — where does the rest go?

D-445 measured, on `cafe_obstacle_crossing_v0`, that ``gain`` (the clearance an
excursion buys over standing on the reference path) is **uncorrelated with the
excursion's size**: r = -0.09 / +0.09 across two `w_heading` arms while
``deviation`` spans 4.6x, with `gain` penned into 0.07-0.19 m. `aim_efficiency`
(`gain / deviation`) therefore collapses against deviation, r = -0.81 / -0.89.
Something absorbs the extra metres. This module names what.

The identity the reading is built on
------------------------------------

At the closest-approach index, write `p` for the robot centre, `f` for its foot
on the reference polyline, `h` for the hazard centre. Radii cancel out of any
*difference* of surface clearances, so

    gain = |h - p| - |h - f|

exactly, and the deviation vector is `d = p - f` with `|d| = deviation`. Let
`u = (h - f) / |h - f|` be the unit bearing from the foot to the hazard. Then

    gain = -d . u + O(|d|^2 / |h - f|)

so the component of `d` along `-u` — call it **away** — is the only part that
buys clearance, and the orthogonal part — **slide** — buys nothing at first
order no matter how large it grows. `away**2 + slide**2 == deviation**2` is an
exact partition of the excursion, and it is reported as such: this is where the
metres went.

Why the *path*-frame split is reported but is not the answer
-----------------------------------------------------------

STATE framed Q-189 as a tangent/normal decomposition of the deviation vector.
Taken literally that reading is **vacuous, and vacuous by construction**:
:func:`avoidance_aim.foot_points` returns the *nearest* point on the polyline,
so `d` is orthogonal to the segment it projects onto whenever the foot is
interior to that segment — the tangential share is zero because of how a foot
point is defined, not because of anything the controller did. It is measured
anyway (`tangent_frac`), for exactly one reason: to pin that it stays ~0 and so
prove the framing was degenerate rather than leave a future cycle to re-derive
it. A reading that can only come out one way is not evidence.

The non-degenerate path-frame question is asked of the **hazard bearing**, not
of the deviation: :attr:`SeedBudget.bearing_tangent_frac` is `|u . t_hat|`,
how much of the direction-to-hazard lies along the path's own tangent. This is
free to be anything, and it is what separates STATE's two levers:

- **bearing along the tangent** (`bearing_tangent_frac` -> 1): the hazard sits
  essentially *on the path ahead*. A deviation that is constrained to be
  path-normal is then close to orthogonal to `u`, so it lands almost entirely
  in `slide` and cannot buy clearance **at any magnitude**. The lever is not
  where the path goes but *when the robot is there* — the reference's time
  parameterisation (P4 speed/timing), not its geometry.
- **bearing along the normal** (`bearing_tangent_frac` -> 0): the hazard is
  off to the side, the normal excursion points usefully, and a failure to
  clear is then a genuine aim/prediction failure — actor prediction (P4).

The two are distinguishable from the same 32 logged runs with no new sim,
which is the whole reason this reading is cheap.

What this deliberately does not do
----------------------------------

1. **It does not re-derive the closest-approach instant.** It reads the same
   index :mod:`avoidance_aim` reads, via the same helpers, so the numbers here
   and D-445's numbers describe the same instant. A second opinion about *when*
   would make the two readings incomparable for no gain.
2. **It does not report `slide` as waste.** `slide` is what the excursion spent
   without buying clearance *at this instant*; the same metres may be buying
   something at another one (D-444: the swerve is early). The claim made here
   is scoped to the instant at which clearing was decided, because that is the
   only instant D-445's saturation was measured at.
3. **It does not threshold `bearing_tangent_frac` behind a single constant.**
   :func:`lever_over_bands` sweeps the split the way D-444/D-445 swept theirs,
   for the same reason: a constant picked after seeing the answer manufactures
   the verdict.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from eval.mppi_sandbox.avoidance_aim import (
    ARMS,
    SCENE,
    SEEDS,
    foot_points,
)
from eval.mppi_sandbox.avoidance_timing import (
    clearance_series,
    closest_approach_index,
)

__all__ = [
    "ARMS",
    "BANDS",
    "SCENE",
    "SEEDS",
    "SeedBudget",
    "lever",
    "lever_over_bands",
    "measure_arm",
    "score_one_run",
    "shares",
]

#: Bands on `bearing_tangent_frac` at which the tangent/normal call is taken.
#: Swept rather than fixed; 0.707 is the isotropic split (45 degrees), the two
#: flanking rungs ask whether the verdict survives a stricter and a looser bar.
BANDS: tuple[float, ...] = (0.50, 0.707, 0.85)


@dataclass(frozen=True)
class SeedBudget:
    """One seed's excursion, partitioned at its own closest-approach instant.

    Lengths are metres; `*_frac` fields are dimensionless. `away` is signed —
    negative means the excursion moved the robot *toward* the hazard.
    """

    seed: int
    index: int
    t_s: float
    #: `|d|`, distance from the reference polyline at the deciding instant.
    deviation: float
    #: Component of `d` along `-u` (away from the hazard). Signed.
    away: float
    #: Component of `d` orthogonal to `u`. Non-negative by construction.
    slide: float
    #: `|u . t_hat|` — share of the hazard bearing lying along the path tangent.
    bearing_tangent_frac: float
    #: `|d . t_hat| / |d|` — degenerate, pinned ~0. See the module docstring.
    tangent_frac: float
    #: Exact `gain`, recomputed here so the linearisation can be checked.
    gain: float

    @property
    def away_frac(self) -> float:
        """Share of the excursion that pointed away from the hazard, in [-1, 1]."""
        if self.deviation <= 0.0:
            return float("nan")
        return self.away / self.deviation

    @property
    def slide_frac(self) -> float:
        """Share of the excursion orthogonal to the hazard bearing, in [0, 1]."""
        if self.deviation <= 0.0:
            return float("nan")
        return self.slide / self.deviation


def _unit(v: np.ndarray) -> np.ndarray:
    n = float(np.linalg.norm(v))
    return v / n if n > 0.0 else np.zeros_like(v)


def _tangent_at(waypoints: np.ndarray, point: np.ndarray) -> np.ndarray:
    """Unit tangent of the polyline segment nearest to `point`."""
    ref = np.asarray(waypoints, dtype=float)[:, :2]
    a, b = ref[:-1], ref[1:]
    seg = b - a
    denom = np.einsum("sk,sk->s", seg, seg)
    denom = np.where(denom > 0.0, denom, 1.0)
    u = np.clip(np.einsum("sk,sk->s", point[None, :] - a, seg) / denom, 0.0, 1.0)
    foot = a + u[:, None] * seg
    return _unit(seg[int(np.argmin(np.linalg.norm(point[None, :] - foot, axis=1)))])


def score_one_run(traj: np.ndarray, waypoints: np.ndarray, obstacles,
                  robot_radius: float, *, seed: int) -> SeedBudget:
    """Partition one logged trajectory's excursion. No band is applied here.

    The band enters only at :func:`lever`, so one integration is readable
    against the whole ladder — the same re-scoring discipline D-444/D-445 used.
    """
    if not obstacles:
        raise ValueError("the budget partition is undefined with no hazard")
    clr = clearance_series(traj, obstacles, robot_radius)
    i = closest_approach_index(clr)
    t = traj[i:i + 1, 0]

    p = traj[i, 1:3].astype(float)
    f = foot_points(traj, waypoints)[i].astype(float)
    # The hazard the clearance series is reporting at `i` — minimising over the
    # same set, so `gain` below matches `avoidance_aim` term for term.
    haz = min(obstacles,
              key=lambda ob: float(np.linalg.norm(p - ob.position(t)[0])) - ob.radius)
    h = haz.position(t)[0].astype(float)

    d = p - f
    deviation = float(np.linalg.norm(d))
    u = _unit(h - f)
    t_hat = _tangent_at(waypoints, f)

    away = float(-np.dot(d, u))
    # Exact orthogonal remainder; clipped only against float noise at |d| ~ 0.
    slide = float(np.sqrt(max(deviation ** 2 - away ** 2, 0.0)))
    gain = (float(np.linalg.norm(h - p)) - float(np.linalg.norm(h - f)))

    return SeedBudget(
        seed=seed,
        index=i,
        t_s=float(traj[i, 0]),
        deviation=deviation,
        away=away,
        slide=slide,
        bearing_tangent_frac=float(abs(np.dot(u, t_hat))),
        tangent_frac=(float(abs(np.dot(d, t_hat))) / deviation
                      if deviation > 0.0 else float("nan")),
        gain=gain,
    )


def shares(rows: tuple[SeedBudget, ...]) -> dict[str, float]:
    """Population means of the partition. Empty input -> all NaN, not an error."""
    keys = ("deviation", "away", "slide", "gain", "bearing_tangent_frac",
            "tangent_frac")
    if not rows:
        return {k: float("nan") for k in keys}
    return {k: float(np.mean([getattr(r, k) for r in rows])) for k in keys}


def lever(rows: tuple[SeedBudget, ...], band: float) -> str:
    """Which lever the geometry points at, at one band on the bearing split.

    Only seeds that actually left the path vote — a seed with `deviation == 0`
    has no excursion to partition, and counting it would let a controller that
    never swerved cast a vote about where its swerve went.
    """
    voting = tuple(r for r in rows if r.deviation > 0.0)
    if not voting:
        return "NO_EXCURSION: no seed left the reference path"
    tangential = sum(1 for r in voting if r.bearing_tangent_frac >= band)
    normal = len(voting) - tangential
    if tangential >= 2 * normal:
        return ("TIMING: the hazard sits along the path tangent, so a "
                "path-normal excursion cannot buy clearance at any size; "
                "the lever is the reference's time parameterisation")
    if normal >= 2 * tangential:
        return ("PREDICTION: the hazard sits off the path normal, so the "
                "excursion points usefully and failing to clear is an "
                "aim/prediction failure")
    return "MIXED: no majority; the scene holds both geometries"


def lever_over_bands(rows: tuple[SeedBudget, ...],
                     bands: tuple[float, ...] = BANDS) -> dict[float, str]:
    """The call at each rung. Stability across rungs is what a reader checks
    before believing any single one (D-445: a verdict that flips with its own
    threshold was never a verdict)."""
    return {b: lever(rows, b) for b in bands}


def measure_arm(scenario, w_heading: float,
                seeds: tuple[int, ...] = SEEDS) -> tuple[SeedBudget, ...]:
    """Run one arm and partition every seed. 16 integrations, no band applied."""
    from eval.mppi_sandbox import ab
    from eval.mppi_sandbox.controllers.stock_mppi import MPPIParams

    runs = ab.seed_sweep(scenario, "stock_mppi", seeds=list(seeds),
                         params=MPPIParams(w_heading=w_heading))
    # D-443's precondition, stated in the function whose output is undefined
    # without it: a truncated run's closest-approach index may sit before the
    # encounter ever happened, so its partition describes the wrong instant.
    stalled = [r.seed for r in runs if not r.reached_goal]
    if stalled:
        raise RuntimeError(
            f"w_heading={w_heading}: seed(s) {stalled} did not reach goal; "
            "the budget partition is not defined over a truncated run"
        )
    return tuple(
        score_one_run(r.traj, scenario.waypoints, scenario.obstacles,
                      ab.ROBOT_RADIUS, seed=r.seed)
        for r in runs
    )

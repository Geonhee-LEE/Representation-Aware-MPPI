# SPDX-License-Identifier: BSD-3-Clause
"""Occlusion metrics for blind-corner scenarios (Q-017 measurement surface).

The DYNAMIC-channel critic's north-star delta was measured with
`min_obstacle_clearance` (head-on: +>0.1 m). The EPISTEMIC channel needs its
own scalar — clearance is oracle-blind to occlusion, so it cannot score
"how blind was the approach." This module supplies two such scalars, both
computed from an executed (T, 6) trajectory plus the ground-truth occluder
set, via the same `GTBevProducer` occlusion model the critics consume:

- `sightline_reveal(traj, obstacles, target)` — at what arclength / distance
  does a hidden `target` point first enter line-of-sight? A cautious
  (epistemic-aware) approach reveals the pocket *earlier* / from *farther*,
  buying reaction distance. This is the headline blind-corner metric: it is
  non-zero and path-dependent even for a smooth trajectory.

- `occlusion_exposure(traj, obstacles, lookahead)` — mean epistemic σ of the
  pose the robot is about to enter (a `lookahead`-metre probe along the
  executed path), evaluated from the BEV rendered at the current pose. This
  is the quantity `ShadowCostCritic` charges directly. Empirically it is
  ~0 for a *smooth* oracle-baseline MPPI (the occluded region sits off to the
  side of the forward path, not on it — the generalisation of the Q-017
  redundancy finding), so it is reported mainly as a floor the shadow cost
  must not raise, not as a gain axis.

Both take the plain obstacle list so they work off any run without threading
a producer through — a fresh `GTBevProducer` is built with the same defaults
the sandbox controllers use.
"""

from __future__ import annotations

import numpy as np

from .representations import GTBevProducer, RiskChannel


def _producer(obstacles, sensing_range: float) -> GTBevProducer:
    return GTBevProducer(obstacles, sensing_range=sensing_range)


def _arclength(xy: np.ndarray) -> np.ndarray:
    """(T,) cumulative arclength of an (T, 2) path, starting at 0."""
    seg = np.linalg.norm(np.diff(xy, axis=0), axis=1)
    return np.concatenate([[0.0], np.cumsum(seg)])


def point_sigma(obstacles, robot_xy, t: float, point,
                sensing_range: float = 5.0) -> float:
    """Epistemic σ of a single world `point` as seen from `robot_xy` at t.

    σ=1 → occluded or beyond range (unknown); σ=0 → observed. Uses the
    pessimistic unobserved prior (D-012)."""
    bev = _producer(obstacles, sensing_range).render(np.asarray(robot_xy, float), t)
    return float(bev.sample(RiskChannel.EPISTEMIC, np.atleast_2d(point),
                            unobserved_value=1.0)[0])


def sightline_reveal(traj: np.ndarray, obstacles, target,
                     sensing_range: float = 5.0,
                     visible_sigma: float = 0.5) -> dict:
    """When does `target` first become visible along the executed path?

    Returns a dict:
      - visible_from_start: bool — target already in sight at pose 0
      - reveal_index:       int | None — first trajectory index with σ<thresh
      - reveal_arclength:   float | None — arclength travelled at reveal
      - reveal_distance:    float | None — robot→target distance at reveal
      - total_arclength:    float — full path length
      - reveal_fraction:    float | None — reveal_arclength / total_arclength

    A never-revealed target yields None for the reveal_* fields. A *cautious*
    approach should reveal the target at a smaller reveal_fraction and a
    larger reveal_distance (more reaction room)."""
    xy = traj[:, 1:3]
    ts = traj[:, 0]
    arc = _arclength(xy)
    tgt = np.asarray(target, float)
    prod = _producer(obstacles, sensing_range)

    reveal_index = None
    for i in range(len(xy)):
        bev = prod.render(xy[i], ts[i])
        sigma = float(bev.sample(RiskChannel.EPISTEMIC, tgt[None],
                                 unobserved_value=1.0)[0])
        if sigma < visible_sigma:
            reveal_index = i
            break

    out = {
        "visible_from_start": reveal_index == 0,
        "reveal_index": reveal_index,
        "total_arclength": float(arc[-1]),
        "reveal_arclength": None,
        "reveal_distance": None,
        "reveal_fraction": None,
    }
    if reveal_index is not None:
        out["reveal_arclength"] = float(arc[reveal_index])
        out["reveal_distance"] = float(np.linalg.norm(xy[reveal_index] - tgt))
        out["reveal_fraction"] = (float(arc[reveal_index] / arc[-1])
                                  if arc[-1] > 0 else 0.0)
    return out


def occlusion_exposure(traj: np.ndarray, obstacles, lookahead: float = 0.6,
                       sensing_range: float = 5.0) -> float:
    """Mean epistemic σ of the pose `lookahead` m ahead along the executed
    path, evaluated from the BEV at the current pose. Proxy for "driving
    blind." ≥ 0; ~0 for a smooth oracle-baseline path (see module docstring)."""
    xy = traj[:, 1:3]
    ts = traj[:, 0]
    prod = _producer(obstacles, sensing_range)
    n = len(xy)
    if n == 0:
        return 0.0
    total = 0.0
    for i in range(n):
        j = i
        while j < n - 1 and np.linalg.norm(xy[j] - xy[i]) < lookahead:
            j += 1
        bev = prod.render(xy[i], ts[i])
        total += float(bev.sample(RiskChannel.EPISTEMIC, xy[j:j + 1],
                                  unobserved_value=1.0)[0])
    return total / n

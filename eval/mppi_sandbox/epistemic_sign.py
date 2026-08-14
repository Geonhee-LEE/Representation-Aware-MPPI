# SPDX-License-Identifier: BSD-3-Clause
"""Read the **sign** of an epistemic critic off its own cost function.

The 2026-08-14 08:00 research feed entry on PA-MPPI (`2509.14978`, RA-L 2026)
names an axis this branch had not stated in prose: a soft epistemic cost in
MPPI can carry either sign, and the two are *not* reconcilable by tuning a
weight.

- **attract** — reward *observing* the unknown; the robot approaches a blind
  corner to resolve it (PA-MPPI's "perception cost", plan-to-see).
- **repel** — penalise *exposure to* the unknown; the robot backs off to buy
  margin (plan-against-the-unseen).

Same functional form, opposite gradient, opposite behaviour at a blind corner.
The feed's suggested TODO reads *"`p3-epistemic-shadow-cost-critic` has never
stated which of the two it is"*.

## The premise is false, and this module is how that is stated as a measurement

The branch has shipped **both signs**, in two critics, for eleven weeks:

- `ShadowCostCritic` (Q-017 answer (a)) — `cost = w_epist · Σ_h σ(x_kh)`.
  Charges σ **at the rollout point**: entering the shadow costs more. **Repel.**
- `ObservationValueCritic` (2404.07781 borrow, D-021) —
  `cost = w_voo · Σ_h (1 − V(x_kh))`, `V(q)` the fraction of shadowed cells
  revealed by standing at `q`. Charges the shadow you **fail to reveal**:
  standing where you can see into the shadow costs *less*. **Attract.**

So the sign question is not open here; it is *already answered twice*, and the
history is the interesting part. D-021 measured the **repel** arm signal-free
on `cafe_obstacle_crossing_v0` — byte-identical trajectories at `w_epist = 200`
vs `0` — and `ObservationValueCritic` was written as its **replacement**. This
branch reached PA-MPPI's sign by measurement rather than by citation.

## Three values, not two — and the third is the one this project measured

A sign read off a cost function is a statement about the **construction**. It is
not a statement about whether the term is *audible* on a scene: a critic can be
unambiguously repel-by-construction and still be exactly silent where the
rollouts actually go, which is precisely D-021's finding. Conflating the two is
what makes "which sign is it?" sound like an open question when the code has
answered it. So `sign()` returns one of:

    REPEL    — exposed points cost strictly more than observed ones
    ATTRACT  — exposed points cost strictly less
    SILENT   — the cost has no spread at all across the candidate set

`SILENT` is a first-class verdict, not a measurement failure, and it is
deliberately disjoint from the other two: a silent term has *no* sign, and
reporting it as "weakly repel" would be the D-241 silent-vacuity shape.

## Which statistic, said before dividing by it

`SIGN_STATISTIC = "mean_split"`. The sign is the difference of **mean cost over
exposed points minus mean cost over observed points**, exposure being
`σ > SHADOW_TAU` on the EPISTEMIC channel.

A Pearson correlation against σ is also returned (`corr`) but is explicitly
**not** what decides the sign, and the reason is structural rather than
stylistic. `ShadowCostCritic` is a pointwise function of σ, so its correlation
is exactly `+1.0`. `ObservationValueCritic` is **not a function of σ at the
point** — `V(q)` is an aggregate over rays from `q` to every shadowed cell — so
its correlation is weak (measured `-0.21`) even though its mean split is decisive
(measured `2.00` in shadow vs `5.59` outside, i.e. the shadow is ~2.8× cheaper).
Letting the correlation decide would report the aggregate-map construction as
nearly signless, which is the opposite of true. The mean split asks the question
the behaviour turns on — *does entering the shadow cost more or less* — and does
not presume the cost is pointwise in σ.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .critics import ObservationValueCritic, ShadowCostCritic
from .obstacles import CircleObstacle
from .representations import GTBevProducer, RiskChannel

REPEL = "REPEL"
ATTRACT = "ATTRACT"
SILENT = "SILENT"

SIGN_STATISTIC = "mean_split"
SHADOW_TAU = 0.5          # σ above this counts as an exposed (shadowed) point
SPREAD_EPS = 1e-12        # ptp at or below this is exact silence, not a sign


@dataclass(frozen=True)
class SignReading:
    """One critic's sign on one geometry, with the evidence that decided it."""

    critic: str
    sign: str
    mean_exposed: float
    mean_observed: float
    spread: float
    corr: float
    n_exposed: int
    n_observed: int

    @property
    def split(self) -> float:
        """Mean cost in shadow minus mean cost outside — the deciding number."""
        return self.mean_exposed - self.mean_observed


def classify(cost: np.ndarray, sigma: np.ndarray) -> SignReading:
    """Sign of `cost` with respect to shadow exposure `sigma`, both (K,).

    `critic` is left blank; `probe`/`probe_all` fill it in. Split out so the
    rule is testable on synthetic cost vectors without building a BEV.
    """
    cost = np.asarray(cost, dtype=float)
    sigma = np.asarray(sigma, dtype=float)
    if cost.shape != sigma.shape:
        raise ValueError(f"cost {cost.shape} and sigma {sigma.shape} differ")

    exposed = sigma > SHADOW_TAU
    spread = float(np.ptp(cost)) if len(cost) else 0.0

    if spread <= SPREAD_EPS:
        # No spread ⇒ the term cancels in the softmax ⇒ it has no sign.
        # Reported before the mean split is consulted, so a silent term can
        # never be dressed up as a weak preference.
        mean_e = float(cost[exposed].mean()) if exposed.any() else float("nan")
        mean_o = float(cost[~exposed].mean()) if (~exposed).any() else float("nan")
        return SignReading("", SILENT, mean_e, mean_o, spread, 0.0,
                           int(exposed.sum()), int((~exposed).sum()))

    if not exposed.any() or not (~exposed).any():
        raise ValueError(
            "candidate set has no exposed/observed split — the geometry does "
            "not pose the question (n_exposed="
            f"{int(exposed.sum())}, n_observed={int((~exposed).sum())})")

    mean_e = float(cost[exposed].mean())
    mean_o = float(cost[~exposed].mean())
    corr = float(np.corrcoef(sigma, cost)[0, 1]) if float(np.ptp(sigma)) > 0 else 0.0
    sign = REPEL if mean_e > mean_o else ATTRACT
    return SignReading("", sign, mean_e, mean_o, spread, corr,
                       int(exposed.sum()), int((~exposed).sum()))


def blind_corner(radius: float = 0.5, stride: int = 13):
    """The one-disc blind-corner geometry the signs are read on.

    A single disc ahead of the robot casts one occlusion shadow; candidate
    rollouts are single points sampled over the rendered BEV window, so a
    "rollout" here is an observation *location* and the reading is a pure
    statement about the cost field, with no planner in the loop.

    Returns `(producer, bev, robot_xy, points, sigma)`.
    """
    producer = GTBevProducer([CircleObstacle(2.0, 0.0, radius=radius)])
    robot_xy = np.array([0.0, 0.0])
    bev = producer.render(robot_xy, 0.0)

    n = bev.stack.shape[1]
    axis = bev.origin[0] + (np.arange(n) + 0.5) * bev.resolution
    ay = bev.origin[1] + (np.arange(n) + 0.5) * bev.resolution
    cx, cy = np.meshgrid(axis, ay)
    points = np.stack([cx.ravel(), cy.ravel()], axis=1)[::stride]
    sigma = bev.sample(RiskChannel.EPISTEMIC, points, unobserved_value=1.0)
    return producer, bev, robot_xy, points, sigma


def probe_all(w: float = 10.0, **geometry) -> dict[str, SignReading]:
    """Read both shipped epistemic critics on the same geometry.

    Same `w` for both by construction: the point of the reading is that the
    sign is a property of the *form*, not of the weight, so handing the two
    critics different weights would invite the reading to be explained away as
    a tuning difference.
    """
    producer, bev, robot_xy, points, sigma = blind_corner(**geometry)
    K = len(points)
    costs = {
        "ShadowCostCritic":
            ShadowCostCritic(w_epist=w).cost(bev, points, K),
        "ObservationValueCritic":
            ObservationValueCritic(w_voo=w).cost(
                producer, bev, robot_xy, 0.0, points, K),
    }
    out = {}
    for name, cost in costs.items():
        reading = classify(cost, sigma)
        out[name] = SignReading(name, reading.sign, reading.mean_exposed,
                                reading.mean_observed, reading.spread,
                                reading.corr, reading.n_exposed,
                                reading.n_observed)
    return out


def signs_are_opposed(readings: dict[str, SignReading]) -> bool:
    """True iff the readings contain both a REPEL and an ATTRACT arm.

    This is the claim the module exists to support: the branch holds both
    signs, so the sign question is answered by the code and not open.
    """
    got = {r.sign for r in readings.values()}
    return REPEL in got and ATTRACT in got


def format_readings(readings: dict[str, SignReading]) -> str:
    lines = [f"epistemic_sign — statistic={SIGN_STATISTIC} tau={SHADOW_TAU}"]
    for name, r in readings.items():
        lines.append(
            f"  {name:24s} {r.sign:8s} exposed={r.mean_exposed:8.3f} "
            f"observed={r.mean_observed:8.3f} split={r.split:+8.3f} "
            f"corr={r.corr:+.4f} n={r.n_exposed}/{r.n_observed}")
    lines.append(f"  opposed={signs_are_opposed(readings)}")
    return "\n".join(lines)


if __name__ == "__main__":     # pragma: no cover - manual read
    print(format_readings(probe_all()))

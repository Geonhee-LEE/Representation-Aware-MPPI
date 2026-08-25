# SPDX-License-Identifier: BSD-3-Clause
"""Is D-257's sampling band the **reader's** or the **planner's**? (Q-149)

D-257 swept the cancelling root over `radius x stride` and found that `stride` —
which changes no physical quantity — moves the root by 18-51 % of each band's
own mean, enough to confound 5 of 6 adjacent radius steps. It called that "the
sampler" and left the attribution there. This module splits it.

`stride` is not one knob. Subsampling a 64x64 lattice by `s` changes **two**
things at once:

- **count**: `K = ceil(4096 / s)`, spanning ~10x over the D-257 ensemble;
- **alignment**: *which* lattice offset survives, i.e. a structured, non-random
  choice of where in the window the candidates sit.

And both of them share a third property that neither `stride` nor `radius` can
vary: the **support**. Every D-257 candidate set is the whole 8x8 m BEV window,
uniformly. No planner visits that set. An MPPI rollout cloud is forward-biased,
robot-anchored, and covers maybe a quarter of the window.

So three supports at **matched K**, each banded over its own ensemble:

| support | ensemble | isolates |
|---|---|---|
| `GRID` | strides (D-257's own reader) | the baseline being explained |
| `UNIFORM` | seeds, K matched to the grid | count *without* alignment |
| `ROLLOUT` | seeds, K matched to the grid | what the planner actually scores |

The two questions this answers are different in kind, and only the second one
can produce a controller claim:

1. **Width.** If `UNIFORM`'s band at matched K is much narrower than `GRID`'s,
   D-257's spread was lattice alignment — an artifact of the reader, removable.
   If it is comparable, the spread is finite-sample noise in `V(q)` and the fix
   is more candidates, not a different lattice. Either way the *caveat* stays a
   caveat.
2. **Displacement.** If `ROLLOUT`'s band does not overlap `GRID`'s, then the
   root D-256 and D-257 quote is a number about a support the planner never
   scores, and the both-arms-on cell of Q-148 has been placed against the wrong
   one. That is not an instrument caveat; it moves where the experiment sits.

`separation()` is imported from `cancelling_stability` rather than re-derived —
disjointness is the same predicate whether the ensemble is strides or seeds, and
D-047 is exactly about not letting one number acquire two implementations.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .cancelling_stability import CONFOUNDED, SEPARATED, separation
from .critics import ObservationValueCritic, ShadowCostCritic
from .dynamics import Limits, step
from .epistemic_sign import classify
from .obstacles import CircleObstacle
from .representations import GTBevProducer, RiskChannel

GRID = "GRID"
UNIFORM = "UNIFORM"
ROLLOUT = "ROLLOUT"

# A radius at which the rollout support has no exposed/observed split at all, so
# the root is not merely displaced but undefined. See `displacement_sweep`.
UNPOSED = "UNPOSED"

# Seed ensemble for the two random supports. Fixed here rather than passed, for
# the same reason `DEFAULT_STRIDES` is: a band must not be quietly narrowed by
# choosing a friendlier ensemble.
DEFAULT_SEEDS = (0, 1, 2, 3, 4, 5, 6, 7)

# MPPI-like rollout parameters. Not tuned to any scenario -- they exist to make
# the cloud *shaped like* what a planner scores (robot-anchored, forward-biased,
# curvature-spread) rather than to reproduce a particular controller. The
# horizon is chosen so the far end of a nominal-speed rollout reaches past the
# disc at x=2.0 without leaving the +/-4 m window.
ROLLOUT_H = 30            # steps per rollout
ROLLOUT_DT = 0.15         # s
ROLLOUT_V_NOM = 0.8       # m/s mean commanded speed
ROLLOUT_V_STD = 0.25      # m/s
ROLLOUT_W_STD = 0.8       # rad/s, zero-mean -> symmetric fan


@dataclass(frozen=True)
class CloudBand:
    """The cancelling root at one geometry and support, banded over an ensemble.

    Deliberately *not* `cancelling_stability.RootBand`: that band's ensemble is
    `strides` and this one's is `seeds`, and storing seeds in a field named
    `strides` would be the kind of two-things-one-name conflation D-047 exists
    to catch. It carries the same `lo`/`hi` surface so `separation()` accepts it
    unchanged -- pinned by test, because duck-typing across modules is a
    contract nobody declared.
    """

    support: str
    radius: float
    k: int
    roots: tuple[float, ...]
    ensemble: tuple[int, ...]

    @property
    def lo(self) -> float:
        return min(self.roots)

    @property
    def hi(self) -> float:
        return max(self.roots)

    @property
    def mean(self) -> float:
        return float(np.mean(self.roots))

    @property
    def width(self) -> float:
        return self.hi - self.lo

    @property
    def relative_width(self) -> float:
        return self.width / self.mean if self.mean else float("nan")

    def contains(self, value: float) -> bool:
        return self.lo <= value <= self.hi


def scene(radius: float = 0.5):
    """The D-257 blind-corner scene, without any candidate set attached.

    `epistemic_sign.blind_corner` builds the scene *and* grids it in one call;
    the whole point here is to vary the second half, so the two are separated.
    Pinned against `blind_corner` by test so this is a re-use, not a fork.
    """
    producer = GTBevProducer([CircleObstacle(2.0, 0.0, radius=radius)])
    robot_xy = np.array([0.0, 0.0])
    return producer, producer.render(robot_xy, 0.0), robot_xy


def grid_points(bev, stride: int) -> np.ndarray:
    """D-257's candidate set: the window's cell centres, subsampled by stride."""
    n = bev.stack.shape[1]
    ax = bev.origin[0] + (np.arange(n) + 0.5) * bev.resolution
    ay = bev.origin[1] + (np.arange(n) + 0.5) * bev.resolution
    cx, cy = np.meshgrid(ax, ay)
    return np.stack([cx.ravel(), cy.ravel()], axis=1)[::stride]


def grid_k(bev, stride: int) -> int:
    """How many candidates a stride yields — the K the clouds must match."""
    n = bev.stack.shape[1]
    return len(range(0, n * n, stride))


def uniform_points(bev, k: int, seed: int) -> np.ndarray:
    """K i.i.d. uniform points over the same window — count without alignment."""
    n = bev.stack.shape[1]
    span = n * bev.resolution
    rng = np.random.default_rng(seed)
    return bev.origin + rng.random((k, 2)) * span


def rollout_points(bev, k: int, seed: int,
                   robot_xy=(0.0, 0.0), heading: float = 0.0) -> np.ndarray:
    """K points drawn from MPPI-like diff-drive rollouts out of the robot pose.

    Control sequences are i.i.d. Gaussian per step (`v` about a positive
    nominal, `omega` zero-mean), integrated through the sandbox's own
    `dynamics.step` under its own `Limits` — so the cloud obeys the same
    acceleration and speed clamps the planner's rollouts do, and is a subset of
    the state space a controller could actually reach in `ROLLOUT_H` steps.

    Points are returned in rollout-major order and truncated to exactly `k`, so
    a matched-K comparison against the grid is exact rather than approximate.
    Any point outside the window is left in place: `bev.sample` reports it
    `unobserved`, which is the physically right reading for a rollout that
    leaves the map, and censoring it would bias the cloud toward the centre.
    """
    rng = np.random.default_rng(seed)
    n_roll = int(np.ceil(k / ROLLOUT_H))
    state = np.zeros((n_roll, 5))
    state[:, 0] = robot_xy[0]
    state[:, 1] = robot_xy[1]
    state[:, 2] = heading
    lim = Limits()
    out = np.empty((n_roll, ROLLOUT_H, 2))
    for h in range(ROLLOUT_H):
        u = np.stack([
            rng.normal(ROLLOUT_V_NOM, ROLLOUT_V_STD, n_roll),
            rng.normal(0.0, ROLLOUT_W_STD, n_roll),
        ], axis=1)
        state = step(state, u, ROLLOUT_DT, lim)
        out[:, h, :] = state[:, :2]
    return out.reshape(-1, 2)[:k]


def root_on(producer, bev, robot_xy, points: np.ndarray) -> float:
    """The cancelling `w_epist : w_voo` root on an arbitrary candidate set.

    Same algebra as `cancelling_stability.root_at` (`-v1 / s1` from the two
    unit-weight splits), with the candidate set lifted out of the callee. Pinned
    equal to `root_at` on the grid set by test — that equality is what makes
    this a re-read of D-257's quantity rather than a new one wearing its name.
    """
    sigma = bev.sample(RiskChannel.EPISTEMIC, points, unobserved_value=1.0)
    K = len(points)
    s1 = classify(ShadowCostCritic(w_epist=1.0).cost(bev, points, K), sigma).split
    v1 = classify(
        ObservationValueCritic(w_voo=1.0).cost(
            producer, bev, robot_xy, 0.0, points, K), sigma).split
    if s1 <= 0.0:
        raise ValueError(
            f"repel arm is not repel at unit weight (split={s1}); the root is "
            "only defined against an opposed pair")
    return -v1 / s1


def band_on(support: str, radius: float, k: int,
            ensemble=DEFAULT_SEEDS) -> CloudBand:
    """The root's band at one geometry and support, over `ensemble`.

    For `GRID` the ensemble is strides and `k` is ignored (the stride *sets* K);
    for the two random supports the ensemble is seeds at the given fixed K.
    """
    producer, bev, robot_xy = scene(radius)
    if support == GRID:
        roots = tuple(root_on(producer, bev, robot_xy, grid_points(bev, s))
                      for s in ensemble)
        # The stride ensemble varies K by ~10x by construction, so no single K
        # describes it; the median is a summary, not the band's parameter. That
        # K and alignment move together is precisely what UNIFORM separates.
        k = int(np.median([grid_k(bev, s) for s in ensemble]))
    elif support == UNIFORM:
        roots = tuple(root_on(producer, bev, robot_xy, uniform_points(bev, k, s))
                      for s in ensemble)
    elif support == ROLLOUT:
        roots = tuple(root_on(producer, bev, robot_xy, rollout_points(bev, k, s))
                      for s in ensemble)
    else:
        raise ValueError(f"unknown support {support!r}")
    return CloudBand(support, radius, k, roots, tuple(ensemble))


def matched_k(radius: float = 0.5, stride: int = 13) -> int:
    """The K a given grid stride yields — the matching target for the clouds."""
    _, bev, _ = scene(radius)
    return grid_k(bev, stride)


def compare(radius: float = 0.5, stride: int = 13,
            grid_ensemble=(3, 5, 7, 11, 13, 17, 23, 31),
            seeds=DEFAULT_SEEDS) -> dict[str, CloudBand]:
    """All three supports at one geometry, clouds matched to `stride`'s K."""
    k = matched_k(radius, stride)
    return {
        GRID: band_on(GRID, radius, k, grid_ensemble),
        UNIFORM: band_on(UNIFORM, radius, k, seeds),
        ROLLOUT: band_on(ROLLOUT, radius, k, seeds),
    }


def width_attribution(bands: dict[str, CloudBand]) -> tuple[str, float]:
    """Is the grid's width alignment, or is it finite-sample noise?

    Returns `(verdict, ratio)` where `ratio = uniform.width / grid.width`:

    - `ALIGNMENT` (`< 0.5`) — the matched-K uniform cloud is materially tighter,
      so the grid's extra spread came from *which* lattice offsets it kept.
    - `SAMPLING` (`0.5 … 1.5`) — comparable; the spread is what any K-point
      estimate of `V(q)` carries, and the fix is more candidates.
    - `LATTICE_TIGHTER` (`> 1.5`) — the *random* cloud is the noisier one. Kept
      separate from `SAMPLING` rather than folded into it because it is a
      different statement: a regular lattice is a lower-variance estimator of a
      ray aggregate than i.i.d. draws at the same K, so D-257's stride ensemble
      was already the favourable reader and its width is a **lower** bound on
      what a K-point estimate costs.

    There is deliberately no verdict meaning "the reading is precise": all three
    outcomes leave D-257's caveat standing, they only say what it is about.
    """
    ratio = bands[UNIFORM].width / bands[GRID].width
    if ratio < 0.5:
        verdict = "ALIGNMENT"
    elif ratio <= 1.5:
        verdict = "SAMPLING"
    else:
        verdict = "LATTICE_TIGHTER"
    return verdict, ratio


def support_moves_the_root(bands: dict[str, CloudBand]) -> str:
    """`SEPARATED` iff the rollout cloud's band is disjoint from the grid's.

    This is the load-bearing verdict. `SEPARATED` says D-257's root is a
    property of a support no planner visits, and Q-148's both-arms-on cell must
    be re-placed against the rollout band. `CONFOUNDED` says the grid reading
    survives contact with a planner-shaped candidate set — which is a *licence*
    for the existing number, not a proof that the supports agree.
    """
    return separation(bands[GRID], bands[ROLLOUT])


def displacement_sweep(radii=(0.3, 0.4, 0.5, 0.6, 0.8, 1.0, 1.25),
                       stride: int = 13) -> list[tuple[float, str]]:
    """Per-radius `GRID` vs `ROLLOUT` verdict across D-257's own radius set.

    Returns `(radius, verdict)` with verdict in `{SEPARATED, CONFOUNDED,
    UNPOSED}`. One radius would leave this finding open to exactly the objection
    D-257 raised against D-256 — a single cell quoted as a property.

    `UNPOSED` is the interesting one and it is not an error path. `classify`
    refuses a candidate set with no exposed/observed split, and on the *rollout*
    support that refusal fires for real: at a large enough disc every point a
    forward rollout can reach in `ROLLOUT_H` steps is observed, so the planner
    never scores a shadowed candidate and the cancelling root does not exist for
    it. The grid, which samples the whole window including the region behind the
    disc, reports a finite root at that same radius regardless. A cell where one
    support has no question and the other has an answer is the strongest form of
    the displacement finding, so it is named rather than swallowed.
    """
    out = []
    for r in radii:
        try:
            out.append((r, support_moves_the_root(compare(r, stride))))
        except ValueError:
            out.append((r, UNPOSED))
    return out


def format_compare(bands: dict[str, CloudBand]) -> str:
    lines = [f"rollout_cloud — radius={bands[GRID].radius} "
             f"matched K={bands[UNIFORM].k}",
             f"  {'support':>8} {'n':>3} {'mean':>8} {'lo':>8} {'hi':>8} "
             f"{'width':>8} {'rel':>7}"]
    for name in (GRID, UNIFORM, ROLLOUT):
        b = bands[name]
        lines.append(f"  {name:>8} {len(b.roots):3d} {b.mean:8.4f} {b.lo:8.4f} "
                     f"{b.hi:8.4f} {b.width:8.4f} {b.relative_width:7.1%}")
    verdict, ratio = width_attribution(bands)
    lines.append(f"  width attribution: {verdict} (uniform/grid = {ratio:.2f})")
    lines.append(f"  GRID vs ROLLOUT: {support_moves_the_root(bands)}")
    return "\n".join(lines)


if __name__ == "__main__":     # pragma: no cover - manual read
    print(format_compare(compare()))

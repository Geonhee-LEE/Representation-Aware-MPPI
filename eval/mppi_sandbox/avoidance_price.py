# SPDX-License-Identifier: BSD-3-Clause
"""Q-185: how much of the obstacle scene's heading residual did **avoidance buy**?

D-440 added `w_heading` and measured it on two scenes. Obstacle-free it
converts cleanly (16/16 seeds, -38%). On `cafe_obstacle_crossing_v0` — the
scene the residual was actually *reported* on — the same 0 -> 32 swing reads
11 better / 5 worse, -13%, the per-seed spread **widens**, and cross-track gets
**worse** (+20%). D-440 read that last number as two cost terms competing for
one degree of freedom and filed Q-185 rather than guessing.

The question Q-185 asks is not "is the lever real" (D-440 answered that) but
**what the remaining residual is made of**:

- **(a) unpriced tracking error** — the term is right but too weak / wrong
  shape on this scene, so tune or reshape it; or
- **(b) definitional** — clearance is bought by *leaving the reference path*,
  and `heading_err_rms` is scored against that same path, so some of the
  residual is the price of avoidance and no cost term can remove it without
  un-buying the clearance. Then the thing to move is the **acceptance
  threshold or the metric's reference**, not the cost.

Q-185's stated discriminator, reproduced here rather than re-invented: take the
per-seed correlation between each seed's heading residual and how much
avoidance that seed bought, **in both arms**.

    rho stays tight at w_heading = 32  ->  (b): the term did not remove the
                                              avoidance-bought share, because
                                              that share is not tracking error
    rho loosens at w_heading = 32      ->  (a): the term collected the tracking
                                              share, leaving something else

The estimand and its two honest limits
--------------------------------------

The correlation is **cross-sectional across seeds within one arm**, not a
paired within-seed difference. That is deliberate — the question is about the
*composition* of one arm's residual, and a paired delta differences that
composition away. But it means two things that must be read with it:

1. **n = 16, and rho is a rank statistic on 16 points.** :func:`permutation_p`
   is exact-in-distribution under the null (it enumerates by shuffling, with a
   fixed generator so the number is reproducible), and it is still 16 points:
   a null rho of |0.4| is unremarkable here. The reading below therefore keys
   on **whether rho moves between arms**, and reports both arms' p so a reader
   can see when neither was distinguishable from noise to begin with.

2. **Correlation across seeds is not the causal decomposition.** Seeds differ
   in more than how much avoidance they bought; a seed that detours more may
   also be one that started worse. This is evidence about (a) vs (b), on the
   measurement Q-185 named, and it is not a variance decomposition. Stated so
   the next cycle does not quote it as one.

Two avoidance proxies, and why both
-----------------------------------

**Clearance** (`ArmRun.clearance`, min distance to any obstacle) is what the
acceptance set actually grades, so it is the one D-426's knee moved. But it is
a **minimum over the run** — one instant — while `heading_err_rms` is an
average over the whole trajectory, so a seed can hold a large clearance for one
step and track badly everywhere else.

**Detour** (driven path length / reference polyline length) is the whole-run
quantity, and it is the one Q-181 phrased the hypothesis in: "residual is the
price of *leaving the path*". Neither dominates, so both are reported and
:class:`ArmCorrelation` carries them side by side. Where they disagree, that
disagreement is the finding and must not be resolved by picking the one with
the smaller p.

Cost: 32 integrations (2 arms x 16 seeds) on one scene, ~60-90 s. No source
change to any controller — `w_heading` already exists and its default is 0.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

SCENE = "eval/scenarios/cafe_obstacle_crossing_v0.yaml"
SEEDS: tuple[int, ...] = tuple(range(16))
#: The two arms Q-185 names. `0.0` is the shipped default (D-440 keeps it 0).
ARMS: tuple[float, float] = (0.0, 32.0)
#: Shuffles behind :func:`permutation_p`. Fixed generator, so the p is a
#: reproducible number and not a fresh draw on every read.
N_PERM = 20_000


def _rank(x: np.ndarray) -> np.ndarray:
    """Average ranks, ties shared.

    Ties matter here: `clearance` on a scene where several seeds park on the
    same knee can repeat to float precision, and competition ranking would
    silently order those by seed index — i.e. by nothing.
    """
    x = np.asarray(x, dtype=float)
    order = np.argsort(x, kind="stable")
    ranks = np.empty(len(x), dtype=float)
    ranks[order] = np.arange(1, len(x) + 1, dtype=float)
    for v in np.unique(x):
        at = x == v
        if at.sum() > 1:
            ranks[at] = ranks[at].mean()
    return ranks


def spearman(x: np.ndarray, y: np.ndarray) -> float:
    """Spearman rank correlation. `nan` when either side is constant.

    Computed as Pearson on the average ranks rather than the `1 - 6*d^2/...`
    shortcut, which is only correct without ties.
    """
    rx, ry = _rank(x), _rank(y)
    sx, sy = rx.std(), ry.std()
    if sx == 0.0 or sy == 0.0:
        return float("nan")
    return float(((rx - rx.mean()) * (ry - ry.mean())).mean() / (sx * sy))


def permutation_p(x: np.ndarray, y: np.ndarray, *,
                  n_perm: int = N_PERM, seed: int = 0) -> float:
    """Two-sided p for `spearman(x, y)` under the label-shuffle null.

    No asymptotics: the t-approximation for rho is poor at n = 16, which is
    exactly the n this module runs at. The `+1`s are the standard
    add-one correction, so the p can never be reported as 0.
    """
    obs = spearman(x, y)
    if not np.isfinite(obs):
        return float("nan")
    rng = np.random.default_rng(seed)
    y = np.asarray(y, dtype=float)
    hits = 0
    for _ in range(n_perm):
        if abs(spearman(x, rng.permutation(y))) >= abs(obs) - 1e-12:
            hits += 1
    return (hits + 1) / (n_perm + 1)


@dataclass(frozen=True)
class PerSeed:
    """One seed's residual and the two proxies for what avoidance it bought."""

    seed: int
    heading_rms: float
    clearance: float
    detour: float
    reached_goal: bool


@dataclass(frozen=True)
class ArmCorrelation:
    """One arm's cross-seed composition reading. Both proxies, both p's."""

    w_heading: float
    n: int
    heading_mean: float
    rho_clearance: float
    p_clearance: float
    rho_detour: float
    p_detour: float

    @property
    def proxies_agree(self) -> bool:
        """Do clearance and detour point the same way?

        A property rather than a filter: when they disagree the pair *is* the
        result, and the module refuses to resolve it by dropping one.
        """
        a, b = self.rho_clearance, self.rho_detour
        if not (np.isfinite(a) and np.isfinite(b)):
            return False
        return (a >= 0) == (b >= 0)


def _detour(traj: np.ndarray, waypoints: np.ndarray) -> float:
    """Driven length / reference length. 1.0 = drove the polyline exactly.

    Scored on the same reference `heading_error` is scored against, so the two
    numbers being correlated are anchored to one path and not two.
    """
    driven = float(np.linalg.norm(np.diff(traj[:, 1:3], axis=0), axis=1).sum())
    ref = float(np.linalg.norm(np.diff(waypoints[:, :2], axis=0), axis=1).sum())
    return driven / ref if ref > 0 else float("nan")


def measure_arm(scenario, w_heading: float,
                seeds: tuple[int, ...] = SEEDS) -> tuple[PerSeed, ...]:
    """Run one arm and score every seed. 16 integrations."""
    from eval.mppi_sandbox import ab
    from eval.mppi_sandbox.controllers.stock_mppi import MPPIParams
    from eval.path_tracking_metrics import heading_error

    runs = ab.seed_sweep(scenario, "stock_mppi", seeds=list(seeds),
                         params=MPPIParams(w_heading=w_heading))
    out = []
    for r in runs:
        e = heading_error(r.traj, scenario.waypoints)
        out.append(PerSeed(
            seed=r.seed,
            heading_rms=float(np.sqrt(np.mean(e ** 2))),
            clearance=float(r.clearance),
            detour=_detour(r.traj, scenario.waypoints),
            reached_goal=bool(r.reached_goal),
        ))
    return tuple(out)


def correlate(rows: tuple[PerSeed, ...], w_heading: float,
              *, seed: int = 0, n_perm: int = N_PERM) -> ArmCorrelation:
    """Both proxies against the residual, for one arm."""
    h = np.array([r.heading_rms for r in rows])
    c = np.array([r.clearance for r in rows])
    d = np.array([r.detour for r in rows])
    return ArmCorrelation(
        w_heading=w_heading,
        n=len(rows),
        heading_mean=float(h.mean()),
        rho_clearance=spearman(h, c),
        p_clearance=permutation_p(h, c, n_perm=n_perm, seed=seed),
        rho_detour=spearman(h, d),
        p_detour=permutation_p(h, d, n_perm=n_perm, seed=seed),
    )


def loosened(off: ArmCorrelation, on: ArmCorrelation,
             *, proxy: str = "detour") -> bool:
    """Did pricing heading *weaken* the residual's tie to avoidance?

    `True` -> Q-185 branch (a): the term collected a tracking share and what
    is left is less avoidance-shaped than it was.
    `False` -> branch (b): the tie survived being priced against, which is what
    a definitional share does.

    Read on `|rho|`, not signed rho: the hypothesis is about how *strongly*
    the residual tracks avoidance, and a sign flip at low |rho| is noise
    wearing a direction.
    """
    a = abs(getattr(off, f"rho_{proxy}"))
    b = abs(getattr(on, f"rho_{proxy}"))
    if not (np.isfinite(a) and np.isfinite(b)):
        return False
    return b < a


def verdict(off: ArmCorrelation, on: ArmCorrelation) -> str:
    """One line, and it names the disagreement rather than hiding it."""
    parts = []
    for proxy in ("clearance", "detour"):
        parts.append(
            f"{proxy}: |rho| {abs(getattr(off, f'rho_{proxy}')):.3f} -> "
            f"{abs(getattr(on, f'rho_{proxy}')):.3f} "
            f"({'loosens' if loosened(off, on, proxy=proxy) else 'holds'}, "
            f"p {getattr(off, f'p_{proxy}'):.3f} -> "
            f"{getattr(on, f'p_{proxy}'):.3f})")
    agree = loosened(off, on, proxy="clearance") == loosened(
        off, on, proxy="detour")
    head = ("Q-185 (a): the term collected a tracking share"
            if loosened(off, on) else
            "Q-185 (b): the tie to avoidance survived being priced against")
    if not agree:
        head = "Q-185 SPLIT — the two proxies disagree; do not pick one"
    return f"{head}. " + "; ".join(parts)

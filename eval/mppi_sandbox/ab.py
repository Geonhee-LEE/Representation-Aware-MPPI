# SPDX-License-Identifier: BSD-3-Clause
"""Seed × scene × speed A/B harness for closed-loop sandbox comparisons.

Three primitives were hand-rolled independently in three consecutive cycles
(2026-08-02 05:00 / 07:00 / 08:00), each time because a P3 result had just
died on the nuisance axis that primitive controls:

  * **seed** — `test_shadow_cost_seed_robustness.py`. A single-seed assertion
    shipped green for 20 days encoding a *false* Q-017 finding: seed 0 sat in
    a coincidence basin where two arms converge, and CI's newer numpy moved it
    out. Single-seed assertions about closed-loop behaviour are claims about
    an RNG stream, not about the controller.
  * **speed** — `test_visibility_gated_mppi.py` (PR #69). An unhandicapped
    blind arm ran 1.58× the oracle's realized speed, so "it collides more" was
    confounded with "it drives faster". `v_max` handicapping removes it.
  * **completion** — the `_reached_goal` guard, same file. A 2026-08-02 sweep
    produced a +1.53 m "berth" at p = 1.19e-07 that was entirely *freeze*
    (oracle d_goal 5.42 m on a 7 m path). Zero collisions and a wide berth are
    both purchasable by giving up early.
  * **temperature** — `test_softmax_temperature_audibility.py`, the fourth
    hand-rolled probe (2026-08-02 12:00) and the reason ESS is scored here
    from 13:00 on. At the shipped `lam = 0.1` the softmax has a median
    effective sample size of **1.01 of K = 256**: `U += sum_k w_k * noise_k`
    degenerates to `U += noise[argmin]`, so an additive cost term is audible
    only when it flips the argmin. Q-017 was answered wrongly twice (once
    "nothing to redistribute", once "homotopy indifference") because both
    cycles read a *controller hyperparameter* as a property of the *scene*.
    An A/B that does not report the ESS it ran at cannot distinguish "this
    channel does nothing" from "the sampler never weighed it".

Q-030 proposes making the seed × scene × speed triple a hard precondition for
any reportable sandbox A/B; Q-026 adds the ESS band. A precondition only holds
if obeying it is cheap, which is what this module is for — `seed_sweep` +
`summarize` + `paired_delta` are the three calls a compliant comparison needs,
and `median_ess` / `ess_in_band` now ride along on the stats it already
returns rather than needing a fifth hand-rolled probe.

Deliberately *not* here: p-values. Fisher/sign tests were run ad hoc in the
cycles above and belong with the P5 aggregator, not in a test-support module
whose numbers are asserted in CI.

Typical use::

    scen = load_scenario("eval/scenarios/cafe_blind_approach_v0.yaml")
    oracle = seed_sweep(scen, "stock_mppi", range(8))
    blind = seed_sweep(scen, "vg_mppi", range(8), v_max=0.30,
                       sensing_range=1.0)
    assert_all_reached(oracle, "oracle"); assert_all_reached(blind, "blind")
    assert summarize(blind).collisions > summarize(oracle).collisions

Report `summarize(...).median_ess` alongside any such claim, and call
`assert_ess_in_band` when the claim is that a *cost term* changed behaviour.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import ceil
from typing import Callable, Iterable, Sequence

import numpy as np

from .controllers import make_controller
from .dynamics import Limits
from .obstacles import CircleObstacle, min_clearance
from .run import ROBOT_RADIUS, simulate
from .scenario import Scenario

# Trajectory column layout emitted by `simulate`: [t, x, y, yaw, v, omega].
COL_XY = slice(1, 3)
COL_V = 4

DEFAULT_SEEDS = range(8)

# Q-026's admissible effective-sample-size band, as fractions of K. Below the
# floor the softmax is effectively argmin over K draws (only argmin-flipping
# terms are audible); above the ceiling the weights are near-uniform, so
# `U += sum_k w_k * noise_k` averages to ~0 and the term is inert again. The
# window is *scene-dependent* (Q-025): one `lam` puts an off-centre hazard at
# ESS 46 and the same scene's centred variant at 5.4, so this band is a
# property of a (scenario, controller, lam) triple and has to be re-checked
# per arm — which is why it is scored on the run rather than assumed.
ESS_BAND_FRACTIONS = (0.05, 0.5)


def ess_band(n_samples: int) -> tuple[float, float]:
    """Admissible (floor, ceiling) ESS for a K-sample softmax."""
    lo, hi = ESS_BAND_FRACTIONS
    return (lo * n_samples, hi * n_samples)


def median_ess(controller) -> tuple[float, int]:
    """`(median ESS over the run, K)` for a controller that just ran.

    Reads the log the controller wrote while weighting (`StockMPPI.ess_log`),
    unwrapping the one composition in the registry — `CBFMPPI` keeps its MPPI
    in `.nominal` and filters its output through a QP. Returns `(nan, 0)` for
    a controller that reports no ESS at all; callers must treat that as
    *unknown*, not as *in band* (see `assert_ess_in_band`).
    """
    for c in (controller, getattr(controller, "nominal", None)):
        log = getattr(c, "ess_log", None)
        if log:
            return float(np.median(log)), int(getattr(c.p, "samples", 0))
    return float("nan"), 0


@dataclass(frozen=True)
class ArmRun:
    """One closed-loop run of one arm at one seed."""

    seed: int
    traj: np.ndarray
    clearance: float
    reached_goal: bool
    mean_speed: float
    median_ess: float = float("nan")
    n_samples: int = 0

    @property
    def collided(self) -> bool:
        return bool(self.clearance < 0.0)

    @property
    def ess_in_band(self) -> bool | None:
        """`None` when this arm reported no ESS — unknown, not compliant."""
        if not self.n_samples or not np.isfinite(self.median_ess):
            return None
        lo, hi = ess_band(self.n_samples)
        return bool(lo <= self.median_ess <= hi)


@dataclass(frozen=True)
class SweepStats:
    """Aggregate of a `seed_sweep`. `all_reached` is the admissibility flag.

    `median_ess` is a **report**; `ess_in_band` is the **verdict**, and they
    disagree often enough that reading the first as the second is a mistake.
    Measured 2026-08-02 13:00 on `stock_mppi`, one centred hazard, n = 8:

    | lam | arm median ESS | per-seed range | every seed in band? |
    |-----|----------------|----------------|---------------------|
    | 3.0 | 13.34 (in)     | 9.1 – 45.1     | **no** — 4/8 below  |
    | 5.0 | 33.09 (in)     | 23.1 – 92.7    | yes                 |
    | 8.0 | 77.65 (in)     | 58.1 – 223.6   | **no** — 2/8 above  |

    All three arm medians sit inside `[12.8, 128.0]`; only one arm is actually
    compliant. ESS varies ~5x across seeds at fixed `lam`, so `ess_in_band`
    requires *every* seed and is not derived from `median_ess`.
    """

    n: int
    collisions: int
    collision_rate: float
    mean_clearance: float
    median_clearance: float
    min_clearance: float
    mean_speed: float
    all_reached: bool
    median_ess: float = float("nan")
    n_samples: int = 0
    ess_in_band: bool | None = None


def reached_goal(traj: np.ndarray, scenario: Scenario) -> bool:
    """Completion guard: did this arm actually finish the path?

    A safety comparison whose arms are not both at the goal is not a safety
    comparison. Assert this on every arm of every comparison, on the same run
    that scores safety — not on a separate one.
    """
    tol = float(scenario.acceptance.get("goal_xy_tol", 0.2))
    return bool(np.linalg.norm(traj[-1, COL_XY] - scenario.goal[:2]) <= tol)


def mean_speed(traj: np.ndarray) -> float:
    """Mean |v| actually realized. The quantity a `v_max` handicap must move.

    Realized speed, not `target_speed_mps` — the two are decoupled (measured
    2026-08-02 02:00), so a scenario's declared target is not evidence that
    two arms drove at comparable speeds.
    """
    return float(np.abs(traj[:, COL_V]).mean())


def run_arm(scenario: Scenario, controller: str, seed: int, *,
            v_max: float | None = None,
            obstacles: Sequence[CircleObstacle] | None = None,
            robot_radius: float = ROBOT_RADIUS,
            **controller_kwargs) -> ArmRun:
    """Simulate one arm at one seed and score it.

    `v_max` handicaps this arm only (all other `Limits` keep their defaults) —
    that is the speed control. `obstacles` overrides which obstacles clearance
    is scored against; the default is **every** obstacle in the scenario. Pass
    an explicit subset when the claim is about one specific hazard, and say so
    at the call site, because "clearance to the hazard" and "clearance to the
    nearest of anything" are different numbers on a multi-obstacle scene.
    """
    ctrl = make_controller(controller, scenario, seed=seed,
                           robot_radius=robot_radius, **controller_kwargs)
    traj = simulate(scenario, ctrl,
                    limits=Limits(v_max=v_max) if v_max is not None else None)
    scored = list(scenario.obstacles if obstacles is None else obstacles)
    ess, k = median_ess(ctrl)
    return ArmRun(
        seed=seed,
        traj=traj,
        clearance=min_clearance(traj, scored, robot_radius),
        reached_goal=reached_goal(traj, scenario),
        mean_speed=mean_speed(traj),
        median_ess=ess,
        n_samples=k,
    )


def seed_sweep(scenario: Scenario, controller: str,
               seeds: Iterable[int] = DEFAULT_SEEDS,
               **arm_kwargs) -> list[ArmRun]:
    """`run_arm` over a seed ensemble. Results stay seed-ordered so two sweeps
    over the same `seeds` are positionally paired (see `paired_delta`)."""
    return [run_arm(scenario, controller, s, **arm_kwargs) for s in seeds]


def summarize(runs: Sequence[ArmRun]) -> SweepStats:
    clr = np.array([r.clearance for r in runs], dtype=float)
    collisions = int((clr < 0.0).sum())
    per_seed_band = [r.ess_in_band for r in runs]
    return SweepStats(
        n=len(runs),
        collisions=collisions,
        collision_rate=collisions / len(runs) if runs else float("nan"),
        mean_clearance=float(clr.mean()),
        median_clearance=float(np.median(clr)),
        min_clearance=float(clr.min()),
        mean_speed=float(np.mean([r.mean_speed for r in runs])),
        all_reached=all(r.reached_goal for r in runs),
        median_ess=float(np.median([r.median_ess for r in runs])),
        n_samples=max((r.n_samples for r in runs), default=0),
        # `None` (unknown) is sticky: one unmeasurable seed makes the arm's
        # band compliance unknown rather than quietly True.
        ess_in_band=(None if any(b is None for b in per_seed_band)
                     else all(per_seed_band)),
    )


def assert_all_reached(runs: Sequence[ArmRun], label: str) -> None:
    """Raise unless every seed of this arm finished. Call before scoring."""
    failed = [r.seed for r in runs if not r.reached_goal]
    if failed:
        raise AssertionError(
            f"{label}: seeds {failed} did not reach the goal — a safety score "
            f"from a non-completing arm is unusable (freeze buys clearance)")


def assert_ess_in_band(runs: Sequence[ArmRun], label: str) -> None:
    """Raise unless every seed of this arm weighted inside the ESS band.

    Deliberately **opt-in**, not folded into `summarize`. The shipped default
    `lam = 0.1` puts *every* arm this repo has ever measured below the floor,
    so making it automatic would turn the whole suite red for a re-baseline
    that Q-032 says must wait for the merge queue to drain. `summarize`
    therefore always *reports* `median_ess`; only a comparison whose claim is
    "this cost term changed behaviour" has to *assert* it, because that is the
    claim the band makes falsifiable.
    """
    unknown = [r.seed for r in runs if r.ess_in_band is None]
    if unknown:
        raise AssertionError(
            f"{label}: seeds {unknown} reported no ESS — band compliance is "
            f"unknown, and an unmeasurable ESS is not an in-band one")
    out = [(r.seed, r.median_ess) for r in runs if not r.ess_in_band]
    if out:
        k = runs[0].n_samples
        lo, hi = ess_band(k)
        detail = ", ".join(f"seed {s}: {e:.2f}" for s, e in out)
        raise AssertionError(
            f"{label}: median ESS outside the admissible band "
            f"[{lo:.1f}, {hi:.1f}] of K={k} ({detail}) — below the floor the "
            f"softmax is argmin over K draws and only argmin-flipping terms "
            f"are audible; above the ceiling the weights are near-uniform and "
            f"the update averages to ~0. Re-pick `lam` for this scene "
            f"(the band is scene-dependent) before reading this comparison")


def paired_delta(a: Sequence[ArmRun], b: Sequence[ArmRun]) -> np.ndarray:
    """Per-seed `a.clearance - b.clearance`. Requires identical seed order.

    Paired, not mean: a mean gap can be tail-driven by one seed (the #69
    finding was 15/24 paired at a mean gap that looked decisive).
    """
    if [r.seed for r in a] != [r.seed for r in b]:
        raise ValueError("arms were swept over different seeds — not pairable")
    return np.array([x.clearance - y.clearance for x, y in zip(a, b)])


def sign_counts(deltas: np.ndarray, tol: float = 1e-6) -> tuple[int, int, int]:
    """(favouring-a, favouring-b, tied) counts of a `paired_delta` vector.

    `tol` exists because bit-identical arms are a real and informative outcome
    here, not float noise — see the Q-017 seed-0 coincidence basin.
    """
    d = np.asarray(deltas, dtype=float)
    return (int((d > tol).sum()), int((d < -tol).sum()),
            int((np.abs(d) <= tol).sum()))


@dataclass(frozen=True)
class LamProbe:
    """One temperature's ESS profile for one arm, over a seed ensemble."""

    lam: float
    median_ess: float
    min_ess: float
    max_ess: float
    n_in_band: int
    n: int
    all_reached: bool
    #: How many seeds finished. `-1` marks "not recorded" — probes built before
    #: 2026-08-02 22:00 kept only the `all_reached` boolean, which is why the
    #: completion half of a verdict is **not** re-scorable on historical data
    #: (see `in_band_fraction` / `reached_fraction` below and Q-042).
    n_reached: int = -1

    @property
    def spread(self) -> float:
        """Per-seed ESS ratio `max/min` — the width the band has to contain."""
        return self.max_ess / self.min_ess if self.min_ess > 0 else float("inf")

    @property
    def admissible(self) -> bool:
        """Every seed in band *and* every seed finished. Both are required:
        `lam = 30` on the offset scene is near-uniform with no arm reaching
        the goal (Q-034), which is a completion failure wearing a temperature
        failure's clothes.

        This is criterion (a) of Q-042, kept as the default by D-019. It is a
        **conjunction over seeds**, so it can only tighten as `n` grows; every
        verdict it produces must be stamped with its `n`.
        """
        return self.n_in_band == self.n and self.all_reached

    @property
    def in_band_fraction(self) -> float:
        """`n_in_band / n` — the sufficient statistic for every Q-042 criterion.

        Seeds are exchangeable draws, so the per-seed in-band indicator is an
        unordered binary vector and `(n_in_band, n)` determines its whole
        distribution. That is why criteria (b) and (c) are computable from
        *stored* probes with **zero new simulation** — the per-seed ESS values
        `lam_ladder` discards were never needed for this half of the verdict.
        """
        return self.n_in_band / self.n if self.n else float("nan")

    @property
    def reached_fraction(self) -> float:
        """`n_reached / n`, or `nan` on a probe that predates the field.

        The asymmetry that answers Q-042's opening question: the in-band half
        of a verdict was always re-scorable, the completion half was not.
        `all_reached=False` is consistent with any `n_reached` in `[0, n)`, so
        collapsing it to a boolean threw away exactly the count the fractional
        criteria need — the same monotone-conjunction defect D-019 found in
        the in-band half, in a field that could not even be re-scored.
        """
        return self.n_reached / self.n if self.n and self.n_reached >= 0 \
            else float("nan")


def lam_ladder(scenario: Scenario, controller: str, lams: Iterable[float],
               seeds: Iterable[int] = DEFAULT_SEEDS,
               **arm_kwargs) -> list[LamProbe]:
    """Profile one arm's ESS across a temperature ladder — the calibration
    counterpart to `assert_ess_in_band`'s verdict.

    Four consecutive cycles hand-rolled this loop (2026-08-02 12:00 / 13:00 /
    14:00 / 15:00), which is the same signal that moved ESS itself into this
    module. The guard tells a comparison it ran at a bad temperature; it does
    not say which temperature to use, and "re-pick `lam` for this scene" is
    not actionable advice without a way to search.

    `params=MPPIParams(lam=...)` is injected per rung, so pass the arm's other
    knobs as `arm_kwargs` exactly as you would to `seed_sweep`.
    """
    from .controllers.stock_mppi import MPPIParams

    probes = []
    for lam in lams:
        runs = seed_sweep(scenario, controller, seeds,
                          params=MPPIParams(lam=float(lam)), **arm_kwargs)
        ess = [r.median_ess for r in runs if np.isfinite(r.median_ess)]
        stats = summarize(runs)
        probes.append(LamProbe(
            lam=float(lam),
            median_ess=stats.median_ess,
            min_ess=min(ess) if ess else float("nan"),
            max_ess=max(ess) if ess else float("nan"),
            n_in_band=sum(1 for r in runs if r.ess_in_band),
            n=len(runs),
            all_reached=stats.all_reached,
            n_reached=sum(1 for r in runs if r.reached_goal),
        ))
    return probes


# --- Q-042: what should window admissibility *be*? ---------------------------
#
# D-019 showed `LamProbe.admissible` is a conjunction over seeds, so a window
# only ever shrinks as `n` grows and any two arms separate eventually. Three
# criteria were on the table. Scored 2026-08-02 22:00 on the case that forced
# the question — `stock_mppi @ lam = 1.6` on `cafe_obstacle_crossing_v0`,
# where completion is perfect at both counts and only the band moves:
#
#   | criterion                        | n = 4 (4/4) | n = 8 (7/8) | stable? |
#   |----------------------------------|-------------|-------------|---------|
#   | (a) all seeds                    | admissible  | lost        | **no**  |
#   | (b) quantile >= ceil(0.9 n)      | admissible  | lost        | **no**  |
#   | (c) Wilson lower bound on p      | 0.510       | 0.529       | **yes** |
#
# (b) is not a near-miss, it is a **no-op**: `ceil(0.9 n) == n` for every
# `n <= 9`, so at the seed counts this repo actually runs (4 and 8) it is
# *identical to (a)*, tie included. It only becomes a distinct criterion at
# `n >= 10`. That is a zero-simulation refutation — arithmetic, not a run.
#
# (c) inverts the bias instead of softening it. At `k = n` the Wilson lower
# bound is `n / (n + z^2)`, strictly *increasing* in `n`: more seeds that all
# pass buy more confidence, so a window can **grow** with evidence. On the
# measured case the one lost seed at n = 8 is more than paid for by the four
# extra draws (0.510 -> 0.529), so the verdict does not flip for any threshold
# outside the sliver `(0.510, 0.529]`.

Z_95 = 1.959963984540054   #: two-sided 95% normal quantile


def wilson_lower(k: int, n: int, z: float = Z_95) -> float:
    """Lower end of the Wilson score interval for `k` successes in `n` draws.

    Closed form, no scipy, no RNG — and it is the limit a seed-bootstrap
    converges to. Resampling an exchangeable binary vector depends only on
    `(k, n)`, so the bootstrap adds Monte-Carlo noise to a quantity that has
    an exact expression; `test_lam_admissibility_criterion.py` measures that
    agreement rather than asserting it.

    Unlike the naive `k / n`, this is not monotone-decreasing in `n` at fixed
    quality: it rewards evidence, which is the whole point for Q-042.
    """
    if n <= 0:
        return float("nan")
    p = k / n
    centre = p + z * z / (2 * n)
    halfwidth = z * ((p * (1 - p) / n + z * z / (4 * n * n)) ** 0.5)
    return (centre - halfwidth) / (1 + z * z / n)


def all_seeds(probe: LamProbe) -> bool:
    """Criterion (a) — the D-019 default. Identical to `probe.admissible`."""
    return probe.admissible


def at_least_quantile(q: float) -> Callable[[LamProbe], bool]:
    """Criterion (b) — at least `ceil(q n)` seeds in band *and* reached.

    Kept despite being refuted at `n <= 9` (see the table above) because the
    refutation is only visible if the criterion is runnable: a reader who
    doubts "(b) is a no-op" can call it at n = 4, 8 and 10 and watch it
    coincide with (a) twice and diverge once.
    """
    def criterion(probe: LamProbe) -> bool:
        need = ceil(q * probe.n)
        return probe.n_in_band >= need and _n_reached(probe) >= need
    return criterion


def wilson_lower_at_least(threshold: float,
                          z: float = Z_95) -> Callable[[LamProbe], bool]:
    """Criterion (c) — 95%-confident that both per-seed pass rates exceed
    `threshold`. The only one of the three that is not biased by `n`."""
    def criterion(probe: LamProbe) -> bool:
        return (wilson_lower(probe.n_in_band, probe.n, z) >= threshold
                and wilson_lower(_n_reached(probe), probe.n, z) >= threshold)
    return criterion


def _n_reached(probe: LamProbe) -> int:
    """`probe.n_reached`, refusing to guess when the probe predates the field.

    A probe carrying only `all_reached` cannot be re-scored fractionally, and
    silently reading `all_reached=True` as `n_reached == n` would be right
    only half the time — `False` maps to anything in `[0, n)`. Raise, so the
    zero-new-runs claim stays honest about which half it covers.
    """
    if probe.n_reached < 0:
        raise ValueError(
            f"LamProbe(lam={probe.lam}) has no `n_reached` (pre-Q-042 probe); "
            "fractional criteria cannot re-score the completion half — "
            "re-run `lam_ladder`, or use `all_seeds`, which needs only the "
            "`all_reached` boolean.")
    return probe.n_reached


def admissible_lams(probes: Sequence[LamProbe],
                    criterion: Callable[[LamProbe], bool] = all_seeds,
                    ) -> tuple[float, ...]:
    """The rungs where *every* seed weighted in band and reached the goal.

    A pure function over probes so that the two arms of an A/B can be
    intersected — which is the quantity a paired comparison actually needs::

        on = lam_ladder(scen, "risk_mppi", LADDER, w_epist=200.0)
        off = lam_ladder(scen, "risk_mppi", LADDER, w_epist=0.0)
        shared = set(admissible_lams(on)) & set(admissible_lams(off))

    An empty intersection is a real and reportable outcome, not a search
    failure: measured 2026-08-02, the `offset = 0.3` scene has none over 14
    temperatures while its centred variant has one. Comparing a compliant arm
    against a non-compliant one is still an uncontrolled comparison.

    `criterion` selects the Q-042 rule. The default stays `all_seeds` per
    D-019, so every existing caller and every window in the repo is unchanged
    by this parameter's arrival — but the default is the one criterion known
    to be `n`-biased, so a window reported under it **must** carry its `n`::

        window = admissible_lams(probes, ab.wilson_lower_at_least(0.5))

    Whichever rule is used, both arms of a comparison must use the same one;
    intersecting a window scored under (a) with one scored under (c) is a
    protocol error the type system cannot catch.
    """
    return tuple(p.lam for p in probes if criterion(p))


# --- Q-039: the temperature protocol of a *two-arm* comparison ----------------
#
# Q-035 settled the per-cell question — a scene is an admissible ablation
# surface for a *controller* iff that cell's `admissible` window is non-empty.
# Measured 2026-08-02 18:00, that is not sufficient for an A/B:
# `cafe_obstacle_crossing_v0` calibrates fine for **both** arms and still has
# no temperature they can share (`stock_mppi` [0.4, 0.8], `risk_mppi`
# [1.6, 3.2]). So the pair-level rule is the same generalisation one level up:
#
#   a scene is an admissible **single-temperature** A/B surface for a
#   controller *pair* iff the intersection of their windows is non-empty.
#
# When it is empty there is no clean protocol, and the honest framing is that
# both remaining options are confounded — pick the lesser and *say which*:
#
#   * single `lam`  — at least one arm runs outside the band Q-026 exists to
#     enforce, i.e. it is not executing its intended update at all (below the
#     floor the softmax is argmin over K draws; above the ceiling it averages
#     to ~0). The confound is unbounded and silent.
#   * per-arm `lam` — every arm runs its intended update, but the measured
#     delta now carries a temperature difference alongside the controller
#     difference. The confound is real, *bounded by the gap*, and reportable.
#
# Hence `verdict="per_arm"` plus `lam_gap`, and `lam_for` minimising that gap
# in log-space rather than picking an arbitrary rung. Neither option makes the
# comparison a clean ablation; only one of them makes the impurity visible.

_VERDICTS = ("shared", "per_arm", "unreportable")


@dataclass(frozen=True)
class ABTemperature:
    """The temperature protocol available to one scene × controller-pair."""

    scenario: str
    per_arm: dict[str, tuple[float, ...]]
    shared: tuple[float, ...]
    verdict: str

    @property
    def arms(self) -> tuple[str, ...]:
        return tuple(self.per_arm)

    @property
    def single_lam_admissible(self) -> bool:
        """May this comparison be reported at one temperature for both arms?"""
        return self.verdict == "shared"

    def lam_for(self, arm: str) -> float:
        """The rung this arm should run at under the resolved protocol.

        `shared` → the shared rung nearest all arms' windows. `per_arm` → the
        arm's own rung minimising the log-distance to the other arms', because
        the confound a per-arm protocol introduces scales with the temperature
        *ratio*, so the defensible choice is the pair that minimises it.
        """
        if self.verdict == "unreportable":
            raise ValueError(
                f"{self.scenario}: arms "
                f"{[a for a, w in self.per_arm.items() if not w]} have an "
                f"empty admissible window — this scene is not a reportable "
                f"ablation surface for them at any tested temperature "
                f"(Q-035), so there is no rung to run at")
        if self.verdict == "shared":
            return _log_nearest(self.shared, self.shared)[0]
        others = [l for a, w in self.per_arm.items() if a != arm for l in w]
        return _log_nearest(self.per_arm[arm], others)[0]

    @property
    def lam_gap(self) -> float:
        """Largest per-arm temperature ratio the resolved protocol carries.

        `1.0` for a shared protocol — the quantity a `per_arm` report has to
        state, since it bounds the confound it is trading the band for.
        """
        lams = [self.lam_for(a) for a in self.arms]
        return max(lams) / min(lams) if min(lams) > 0 else float("inf")


def _log_nearest(candidates: Sequence[float],
                 targets: Sequence[float]) -> tuple[float, float]:
    """`(rung, distance)` from `candidates` closest to `targets` in log-space.

    Log-space because temperature acts multiplicatively: 0.8 → 1.6 and
    3.2 → 6.4 are the same intervention, and a linear metric would call the
    second one four times worse.
    """
    if not targets:
        return (float(min(candidates)), 0.0)
    scored = [
        (max(abs(np.log(c) - np.log(t)) for t in targets), float(c))
        for c in candidates
    ]
    dist, rung = min(scored)
    return (rung, float(dist))


def ab_temperature(scenario_file: str, arms: Sequence[str],
                   windows: dict | None = None) -> ABTemperature:
    """Resolve the temperature protocol for an A/B from the calibration table.

    `scenario_file` is the table's key — the yaml *basename*, e.g.
    `"cafe_obstacle_crossing_v0.yaml"` — not a loaded `Scenario`, because this
    is a precondition to be checked *before* paying for any run.
    """
    from .calibrate_lam import load_windows

    cells = load_windows() if windows is None else windows
    per_arm: dict[str, tuple[float, ...]] = {}
    for arm in arms:
        try:
            cell = cells[(scenario_file, arm)]
        except KeyError:
            raise KeyError(
                f"no calibration cell for ({scenario_file}, {arm}) — run "
                f"`python3 -m eval.mppi_sandbox.calibrate_lam` before "
                f"reporting an A/B on it; an uncalibrated arm's band "
                f"compliance is unknown, not assumed") from None
        per_arm[arm] = tuple(cell["admissible"])

    shared: set[float] | None = None
    for w in per_arm.values():
        shared = set(w) if shared is None else shared & set(w)
    shared_t = tuple(sorted(shared or ()))

    if any(not w for w in per_arm.values()):
        verdict = "unreportable"
    elif shared_t:
        verdict = "shared"
    else:
        verdict = "per_arm"
    return ABTemperature(scenario=scenario_file, per_arm=per_arm,
                         shared=shared_t, verdict=verdict)


def assert_single_lam_ab(scenario_file: str, arms: Sequence[str],
                         lam: float, windows: dict | None = None) -> None:
    """Raise unless running **every** arm at `lam` is admissible on this scene.

    The guard Q-039 asks for. `assert_ess_in_band` catches the same defect
    *after* paying for the sweep and only per arm; this catches it from the
    table, before any run, and names the pair-level alternative.
    """
    t = ab_temperature(scenario_file, arms, windows)
    if t.verdict == "unreportable":
        empty = [a for a, w in t.per_arm.items() if not w]
        raise AssertionError(
            f"{scenario_file}: arms {empty} have an empty admissible window "
            f"— not a reportable ablation surface at any tested temperature "
            f"(Q-035). No single-`lam` protocol exists because no protocol "
            f"does")
    if lam in t.shared:
        return
    if t.shared:
        raise AssertionError(
            f"{scenario_file}: lam={lam} is outside the shared admissible "
            f"window {t.shared} for arms {list(t.arms)} — a shared rung does "
            f"exist, so use one instead of running an arm out of band")
    detail = ", ".join(f"{a}: {w}" for a, w in t.per_arm.items())
    raise AssertionError(
        f"{scenario_file}: no shared admissible temperature for arms "
        f"{list(t.arms)} ({detail}) — the windows are disjoint, so running "
        f"both at lam={lam} puts at least one arm outside the Q-026 band, "
        f"where it is not executing its intended update. Run per-arm "
        f"temperatures ("
        + ", ".join(f"{a}={t.lam_for(a)}" for a in t.arms)
        + f", gap {t.lam_gap:.1f}x) and report the gap alongside the delta, "
        f"or drop this scene from the single-`lam` matrix (Q-039)")

# SPDX-License-Identifier: BSD-3-Clause
"""Has any arm on this branch ever bought clearance? (STATE #1)

D-326 priced one arm's slowdown in minimum clearance and found it bought
nothing. That reading was **pairwise** — `essps_mppi` against `risk_mppi` — and
a pairwise reading cannot answer the question the bottleneck actually asks,
which is about the *branch*: many cycles here have optimized ESS band
compliance, a property of the **sampler**, while the north star names obstacle
avoidance and path tracking. Whether that optimization ever moved a safety
number is a question about the whole registry, so this module takes the column
across all of it.

The answer is **no, and the baseline is the reason**. `stock_mppi` — plain MPPI,
no representation channel of any kind — clears `0.5152 m` on seed 0. All five
arms this branch built as representation work sit **below** it, by `0.10`–`0.18
m` there and by `0.11`–`0.23 m` in the eight-seed mean, and not one of them
out-clears it on **any** of the eight seeds. The one arm that clears more is
`cbf_mppi` (`0.7856 m` on seed 0, `+0.228 m` mean, ahead on `8/8`), and CBF is
a *constraint* method, not a representation: it is the control formulation
buying the clearance, not a richer input.

Scope of the claim, stated before the numbers because it bounds them:

* **One scene** — `PEAK_SCENE`, same operating point as
  :data:`essps.PER_ITERATION_ARMS` so the two rows that overlap can be checked
  against each other rather than assumed equal.
* **Eight seeds**, not one. :data:`SEED_ENSEMBLE` re-takes the whole registry
  at seeds 0–7; the seed-0 column of that constant *is*
  :data:`SHIPPED_ARM_CLEARANCE`, pinned equal. What this buys is the magnitude
  D-327 explicitly declined to claim: the per-arm deficit is `-0.11`–`-0.23 m`
  in the mean and **never crosses zero on any seed** (`beats_baseline = 0/8`
  for all five representation arms), so the ensemble that was supposed to be
  needed for the magnitude has been run and the magnitude is now claimable.
* The gaps here are `0.11`–`0.27 m`. D-326 declined to call `0.0128 m` a
  regression because D-019's per-seed spread is larger; these are **8–21×**
  that, and the per-seed spread is now measured directly rather than borrowed
  from D-019 — every arm's worst seed still loses to the baseline's best.
* **Episode length does not explain the ranking**, and the ensemble sharpens
  why. The arms split into a fast class (82–177 steps) and a slow one
  (813–1167), and the slow class holds the *higher* clearances — minimum-over-
  the-episode can only fall as an episode runs longer, so length works
  **against** the arms that win. The stronger reading is *within* the slow
  class, where length is not a difference at all: `gap_gated_mppi` runs the
  same class as the baseline and still loses (`-0.157 m` mean), and `cbf_mppi`
  runs it and wins (`+0.228 m`). Both results survive the confound because
  neither pair is separated by it.

One row is a reading about the instrument rather than the arm: `geometric_mppi`
reproduces `stock_mppi` in **all three** recorded columns, which is the
signature of an inert channel, not of two controllers that agree. It is pinned
as such (`test_geometric_arm_is_indistinguishable_from_the_baseline`) so that a
later cycle making the geometric channel bite finds out here.

Re-take with :func:`retake` — **10.6–14.2 s** for all eight arms, and
:data:`SEED_ENSEMBLE`'s full 8 × 8 in **98.8 s** (measured 2026-08-17). The
`~4 min` this line used to carry was never measured, and it was the third
inherited over-estimate on this branch in three cycles: D-326 priced a re-take
at `~26 s` against an actual `1.7 s` (15×), Q-159 priced this ensemble at
`~32 min` against the actual `1.6 min` (19×), and both times the estimate was
large enough to *change the plan* — Q-159 chose a two-arm pair over the full
ensemble on that number alone, and the full ensemble turned out to fit inside
a single cycle with room to spare. Price a run before scoping around its cost.
"""

from __future__ import annotations

from dataclasses import dataclass

from .controllers import REGISTRY
from .ess_at_peak import ISOLATION, PEAK_SCENE

#: The scene these rows were taken on, as a path. `PEAK_SCENE` is a bare name.
SCENE_PATH = f"eval/scenarios/{PEAK_SCENE}.yaml"

#: Plain MPPI — no risk channel, no epistemic channel, no CBF. The reference the
#: question "did the representation buy anything" has to be asked against; a
#: representation arm that does not beat *this* has not bought avoidance, no
#: matter how it compares to another representation arm.
BASELINE = "stock_mppi"

#: Arms whose constructor accepts the epistemic-channel kwargs (`w_voo`,
#: `w_epist`) and :data:`ess_at_peak.ISOLATION`. Measured, not asserted — see
#: :func:`takes_epistemic_kwargs`, which derives the split by construction so a
#: new controller cannot join the registry and silently pick the wrong branch.
#:
#: The split is recorded because it makes the census's population **two
#: configurations, not one**: the plain arms are run without those kwargs. That
#: is not a different operating point in substance — they have no such channels
#: to zero out, so `ISOLATION`'s `w_risk = 0` is their natural state — but a
#: census that hides the asymmetry is one whose reader cannot check it (D-047).
EPISTEMIC_ARMS: tuple[str, ...] = (
    "cbf_mppi", "essps_mppi", "frozen_risk_mppi", "risk_mppi", "social_mppi",
)

#: `arm -> (min_clearance_m, completion, steps)` for one closed-loop run of
#: every registry arm on :data:`SCENE_PATH`, seed 0, at the operating point
#: `lam = 0.8` (`w_voo = 5` for the arms that take it).
#:
#: Recorded rather than recomputed on import, per
#: :data:`essps.PER_ITERATION_ARMS`'s precedent. The `essps_mppi` and
#: `risk_mppi` rows are shared with that constant to 4 dp — `0.3319` and
#: `0.3447` — which is provenance, not duplication: `test_clearance_census`
#: pins the two equal, so a re-take that moved either would go red here rather
#: than quietly disagreeing with D-326's published pair.
SHIPPED_ARM_CLEARANCE: dict[str, tuple[float, float, int]] = {
    "cbf_mppi":         (0.7856, 0.9922,  985),
    "stock_mppi":       (0.5152, 0.9922,  932),
    "geometric_mppi":   (0.5152, 0.9922,  932),
    "gap_gated_mppi":   (0.4126, 0.9924, 1011),
    "social_mppi":      (0.4050, 0.9922,  110),
    "risk_mppi":        (0.3447, 0.9926,  116),
    "frozen_risk_mppi": (0.3447, 0.9926,  116),
    "essps_mppi":       (0.3319, 0.9931,  158),
}

#: Number of seeds in :data:`SEED_ENSEMBLE`. Named so the tests that walk the
#: ensemble cannot disagree with the constant about its own width.
SEEDS = 8

#: `arm -> (min_clearance_m,) * SEEDS` — the same closed-loop measurement as
#: :data:`SHIPPED_ARM_CLEARANCE`, re-taken at seeds `0 .. SEEDS - 1`.
#:
#: This is Q-159's answer. That item asked whether the baseline deficit D-327
#: measured was "an accident of one seed or a property of the arm", and priced
#: the ensemble that would settle it at `~32 min` — out of a cycle's reach, so
#: it leaned on a two-arm subset instead. The real cost is `98.8 s`, so the
#: subset was never necessary and the whole registry is recorded here.
#:
#: Only the clearance column is kept. The completion column is `0.992`–`0.993`
#: for every arm on every seed, which is a column that cannot separate anything
#: and would read as evidence if recorded beside ones that can; the step column
#: is summarised in the module docstring's class split rather than pinned,
#: because its per-seed value is not a claim anything here rests on.
SEED_ENSEMBLE: dict[str, tuple[float, ...]] = {
    "cbf_mppi":         (0.7856, 0.7732, 0.7809, 0.7713, 0.7871, 0.8318, 0.7831, 0.7785),
    "stock_mppi":       (0.5152, 0.5701, 0.6123, 0.5477, 0.5881, 0.5412, 0.5680, 0.5237),
    "geometric_mppi":   (0.5152, 0.5701, 0.6123, 0.5477, 0.5881, 0.5412, 0.5680, 0.5237),
    "social_mppi":      (0.4050, 0.4531, 0.4980, 0.4512, 0.4430, 0.4952, 0.4001, 0.4401),
    "gap_gated_mppi":   (0.4126, 0.4012, 0.3863, 0.4104, 0.3848, 0.4257, 0.3631, 0.4242),
    "risk_mppi":        (0.3447, 0.4485, 0.4206, 0.3924, 0.4057, 0.4813, 0.3549, 0.3441),
    "frozen_risk_mppi": (0.3447, 0.4485, 0.4206, 0.3924, 0.4057, 0.4813, 0.3549, 0.3441),
    "essps_mppi":       (0.3319, 0.3342, 0.3069, 0.3181, 0.3158, 0.3329, 0.3312, 0.3359),
}

#: Arms this branch built as *representation* work — the ones whose premise is
#: that a richer input improves the plan. `cbf_mppi` is deliberately absent: it
#: changes the control formulation, so crediting the representation hypothesis
#: with its clearance would be attributing a win to the wrong mechanism.
REPRESENTATION_ARMS: tuple[str, ...] = (
    "essps_mppi", "frozen_risk_mppi", "gap_gated_mppi", "risk_mppi",
    "social_mppi",
)


def takes_epistemic_kwargs(name: str, scenario) -> bool:
    """Does `name`'s constructor accept the epistemic-channel kwargs?

    Derived by construction — the arm is built once (cheap; no `simulate`) and
    a `TypeError` naming an unexpected keyword is the negative answer. Deriving
    it is the point: :data:`EPISTEMIC_ARMS` is a hand-written census of a
    population that grows every time someone adds a `REGISTRY` line, and a
    hand-written census of a growing population is the failure this repo keeps
    paying for. The test pins the two against each other.
    """
    from .controllers import make_controller
    from .controllers.stock_mppi import MPPIParams
    from .essps import OPERATING_LAM, OPERATING_W_VOO
    from .run import ROBOT_RADIUS

    try:
        make_controller(name, scenario, seed=0, robot_radius=ROBOT_RADIUS,
                        params=MPPIParams(lam=OPERATING_LAM),
                        w_voo=OPERATING_W_VOO, w_epist=0.0, **ISOLATION)
    except TypeError as exc:
        if "unexpected keyword argument" in str(exc):
            return False
        raise
    return True


@dataclass(frozen=True)
class Verdict:
    """The bottleneck's question, as a graded object."""

    baseline: float
    best_representation: str
    best_representation_clearance: float
    best_overall: str
    best_overall_clearance: float

    @property
    def representation_gain(self) -> float:
        """Best representation arm's clearance minus the baseline's, in metres.

        A **difference**, not a ratio, for the same reason
        :attr:`essps.Price.clearance_gain` is: clearance is a signed distance
        and a ratio across zero says nothing.
        """
        return self.best_representation_clearance - self.baseline

    @property
    def any_representation_buys_clearance(self) -> bool:
        """Did *any* representation arm out-clear plain MPPI?

        This is the bottleneck sentence reduced to a boolean. `False` is the
        measured answer, and it is the reading that matters: the branch's
        avoidance work has been priced against other representation arms, never
        against the arm with no representation at all.
        """
        return self.representation_gain > 0.0


def grade() -> Verdict:
    """Grade :data:`SHIPPED_ARM_CLEARANCE` — recorded numbers, no runs."""
    baseline = SHIPPED_ARM_CLEARANCE[BASELINE][0]
    best_rep = max(REPRESENTATION_ARMS,
                   key=lambda n: SHIPPED_ARM_CLEARANCE[n][0])
    best_all = max(SHIPPED_ARM_CLEARANCE,
                   key=lambda n: SHIPPED_ARM_CLEARANCE[n][0])
    return Verdict(
        baseline=baseline,
        best_representation=best_rep,
        best_representation_clearance=SHIPPED_ARM_CLEARANCE[best_rep][0],
        best_overall=best_all,
        best_overall_clearance=SHIPPED_ARM_CLEARANCE[best_all][0],
    )


@dataclass(frozen=True)
class SeedVerdict:
    """One arm's standing against the baseline across :data:`SEEDS` seeds."""

    arm: str
    mean_gap: float
    worst_gap: float
    best_gap: float
    beats_baseline: int

    @property
    def sign_is_stable(self) -> bool:
        """Does the gap keep its sign on every seed?

        This is the property D-327 could not check and therefore did not claim.
        A mean gap says the arm loses *on average*, which is compatible with it
        winning on some seeds; this says the comparison never changes direction,
        which is what "a property of the arm, not of the seed" actually means.
        """
        return (self.best_gap < 0.0) or (self.worst_gap > 0.0)


def seed_grade(arm: str) -> SeedVerdict:
    """Grade one arm's :data:`SEED_ENSEMBLE` row against the baseline's.

    Paired per seed rather than mean-against-mean: both arms saw the same
    scene and the same seed, so the per-seed difference removes the
    seed-to-seed variation that is common to them. The baseline's own spread
    is `0.5152`–`0.6123` — wider than several of the gaps — so an unpaired
    comparison would be noisier than the effect it is trying to read.
    """
    base = SEED_ENSEMBLE[BASELINE]
    gaps = [a - b for a, b in zip(SEED_ENSEMBLE[arm], base)]
    return SeedVerdict(
        arm=arm,
        mean_gap=sum(gaps) / len(gaps),
        worst_gap=min(gaps),
        best_gap=max(gaps),
        beats_baseline=sum(g > 0.0 for g in gaps),
    )


def any_representation_arm_wins_on_any_seed() -> bool:
    """The branch-level question, widened from one seed to :data:`SEEDS`.

    :attr:`Verdict.any_representation_buys_clearance` asks it of the best arm
    on seed 0. This asks it of *every* representation arm on *every* seed, so
    a single lucky seed anywhere in the ensemble would answer `True`. It does
    not: the measured value is `False`, with `0/8` for all five arms.
    """
    return any(seed_grade(a).beats_baseline > 0 for a in REPRESENTATION_ARMS)


def retake(scenario=None, *, seed: int = 0) -> dict[str, tuple[float, float, int]]:
    """Re-measure every registry arm. Not called by tests (~4 min).

    Returns the same 3-tuple per arm the constant records, so a drift check is
    a dict comparison rather than a re-reading of prose.
    """
    from eval.path_tracking_metrics import completion_percent

    from .controllers import make_controller
    from .controllers.stock_mppi import MPPIParams
    from .essps import OPERATING_LAM, OPERATING_W_VOO
    from .obstacles import min_clearance
    from .run import ROBOT_RADIUS, simulate
    from .scenario import load_scenario

    sc = load_scenario(SCENE_PATH) if scenario is None else scenario
    out: dict[str, tuple[float, float, int]] = {}
    for name in sorted(REGISTRY):
        kw = dict(w_voo=OPERATING_W_VOO, w_epist=0.0, **ISOLATION) \
            if takes_epistemic_kwargs(name, sc) else {}
        ctrl = make_controller(name, sc, seed=seed, robot_radius=ROBOT_RADIUS,
                               params=MPPIParams(lam=OPERATING_LAM), **kw)
        traj = simulate(sc, ctrl)
        out[name] = (
            round(float(min_clearance(traj, sc.obstacles, ROBOT_RADIUS)), 4),
            round(float(completion_percent(traj, sc.waypoints)[-1]), 4),
            int(traj.shape[0]),
        )
    return out


def format_grade() -> str:
    """One-screen census, ranked. For a human reading the cycle's output."""
    v = grade()
    lines = [
        f"clearance census — {PEAK_SCENE}, seed 0, lam=0.8 "
        f"({len(SHIPPED_ARM_CLEARANCE)}/{len(REGISTRY)} arms)",
        "",
        f"{'arm':<18}{'clearance':>11}{'vs base':>10}{'steps':>8}",
    ]
    for name, (clr, _comp, steps) in sorted(
            SHIPPED_ARM_CLEARANCE.items(), key=lambda kv: -kv[1][0]):
        tag = "  <- baseline" if name == BASELINE else ""
        lines.append(f"{name:<18}{clr:>11.4f}{clr - v.baseline:>+10.4f}"
                     f"{steps:>8}{tag}")
    lines += [
        "",
        f"best overall:        {v.best_overall} ({v.best_overall_clearance:.4f}) "
        f"— a constraint method, not a representation",
        f"best representation: {v.best_representation} "
        f"({v.best_representation_clearance:.4f}), "
        f"{v.representation_gain:+.4f} vs plain MPPI",
        f"any_representation_buys_clearance = "
        f"{v.any_representation_buys_clearance}",
    ]
    return "\n".join(lines)


if __name__ == "__main__":  # pragma: no cover
    print(format_grade())

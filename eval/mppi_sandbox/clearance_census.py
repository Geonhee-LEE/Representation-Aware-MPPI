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
no representation channel of any kind — clears `0.5152 m`. Every arm this
branch built (`risk_mppi`, `frozen_risk_mppi`, `essps_mppi`) sits **below** it,
by `0.17`–`0.18 m`. The one arm that clears more is `cbf_mppi` at `0.7856 m`,
and CBF is a *constraint* method, not a representation: it is the control
formulation buying the clearance, not a richer input.

Scope of the claim, stated before the numbers because it bounds them:

* **One scene, one seed** — `PEAK_SCENE` at seed 0, same operating point as
  :data:`essps.PER_ITERATION_ARMS` so the two rows that overlap can be checked
  against each other rather than assumed equal.
* The gaps here are `0.17`–`0.27 m`. D-326 declined to call `0.0128 m` a
  regression because D-019's per-seed spread is larger; these are **13–21×**
  that, which is why the *sign* is claimable here and was not there. The
  *magnitude* still is not — a seed ensemble would be needed for that, and this
  is the first result on the branch where one is worth running.
* **Episode length does not explain the ranking.** The arms split into a fast
  class (110–158 steps) and a slow one (932–1011), and the slow class holds the
  *higher* clearances. Minimum-over-the-episode can only fall as an episode
  runs longer, so length works **against** the arms that win here; the ranking
  survives the confound in the direction that matters.

One row is a reading about the instrument rather than the arm: `geometric_mppi`
reproduces `stock_mppi` in **all three** recorded columns, which is the
signature of an inert channel, not of two controllers that agree. It is pinned
as such (`test_geometric_arm_is_indistinguishable_from_the_baseline`) so that a
later cycle making the geometric channel bite finds out here.

Re-take with :func:`retake` (~4 min for all eight — the slow class dominates).
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

# SPDX-License-Identifier: BSD-3-Clause
"""The three-arm head-to-head: *neither* / *geometry now* / *geometry predicted*.

STATE #1. D-217 landed the third arm (`RiskMPPI(w_ped=...)`, PGIF's cost term)
and took a single-scene reading: worst-case clearance 0.007 -> 0.382 m at 6/6
completion on `cafe_obstacle_crossing_v0`. That reading is the *arm existing*,
not the comparison. This module is the comparison the branch was built for.

The three arms span one axis, which is why they are worth putting on the same
seeds:

| arm | knob | what it reads |
|---|---|---|
| `shadow` | `RiskMPPI(w_epist=...)` | neither geometry — an epistemic scalar |
| `geometric` | `GeometricMPPI(w_geom=...)` | geometry **now** — min clearance, no model |
| `predicted` | `RiskMPPI(w_ped=...)` | geometry **predicted** — speed-scaled anisotropic field |

Why the completion rate is not a footnote
-----------------------------------------

`research/feed.md`'s 2026-08-12 04:00 entry is the reason this module exists in
this shape rather than as another clearance table. It reports PGIF's own
headline — *"0% collisions"* — as a **metric-selection artifact**: on the Hard
level the method converts an 82 % collision rate into a **59 % timeout** rate.
The collisions did not go away, they changed which column they land in. An arm
that stops driving has perfect clearance.

So this module does not have a "clearance" verdict and a "completion" caveat.
It has **one** verdict, and clearance is unreadable unless completion is held:
:meth:`ArmReading.verdict` returns `BOUGHT_WITH_FREEZE` whenever an arm's
clearance improves while its completion falls, and the clearance number is
still reported beside it so the trade is visible rather than hidden. This is
the same discipline `ab.assert_all_reached` applies per-comparison, moved into
the verdict so a *reported* number cannot be a frozen one.

The arms are isolated, and that is what found the interaction
-------------------------------------------------------------

Every arm here carries `w_risk = 0.0`, so each knob is read *alone* against a
baseline with no cost term at all. D-217 did not do that: both its arms carried
the shipped `w_risk = 40.0` default, so its headline is the `w_ped` step taken
**on top of** the risk term. The two denominations disagree, and not by a
little — :func:`risk_interaction` walks the 2x2 that separates them (6 paired
seeds, `lam = 0.8`, `cafe_obstacle_crossing_v0`, worst-case clearance in m):

| | `w_ped = 0` | `w_ped = 50` | step |
|---|---|---|---|
| `w_risk = 40` | 0.0068 | 0.3823 | **+0.3755** |
| `w_risk = 0`  | 0.0202 | 0.0010 | **-0.0192** |

D-217's number is reproduced exactly in the top row. The bottom row is the same
term on the same seeds at the same temperature with the risk term removed, and
it changes **sign**. So `w_ped`'s effect is an *interaction*, not a main effect:
the predicted-geometry field does not buy clearance on its own here, it buys
clearance in the presence of the BEV risk term. The second row also says the
risk term alone *costs* worst-case clearance (0.0202 -> 0.0068) — the pair wins
where neither member does.

That is a claim about attribution, which is the question this branch's
`geometric_null` line exists to ask, and it is why `ARMS` is denominated
against an empty baseline rather than against D-217's. Neither denomination is
wrong; reporting one without the other is.

The 2x2 on all three scenes, and what the threshold was doing
--------------------------------------------------------------

The table above is **one** scene, which cannot tell a property of the term from
a property of `cafe_obstacle_crossing_v0`. :func:`risk_interaction_matrix`
walks all three (6 paired seeds, `lam = 0.8`, worst-case clearance in m, `w_ped`
step per row):

| scene | `w_risk = 40` step | `w_risk = 0` step | verdict |
|---|---|---|---|
| `cafe_obstacle_crossing_v0` | **+0.3756** | -0.0192 | `SIGN_FLIP` |
| `cafe_convoy_v0` | **+0.1968** | -0.0055 | `SIGN_FLIP` |
| `cafe_head_on_v0` | **+0.0806** | -0.0002 | `SIGN_FLIP` |

**This table's third column has since been narrowed and does not read as
current** (D-234). Re-read guard-free — materiality by paired-CI separation
instead of `EPS_CLEARANCE` — only `cafe_obstacle_crossing_v0` flips;
`cafe_convoy_v0` and `cafe_head_on_v0` are `PAIRED_CONDITIONAL`, their
`w_risk = 0` rows unable to resolve a direction at all. The `w_ped` steps above
are reproduced to four decimals by that walk, so what changed is the estimand
and not the runs. D-235 then doubled those two scenes to twelve seeds: still
`NOT_SEPARATED`, and the positive point estimates D-234 read at six seeds
(+0.0159, +0.0040) **cross to negative** (-0.0021, -0.0028), so no direction
should be attributed to either row at any `n` walked so far. Live verdicts:
:func:`paired_step.cafe_family_verdicts` (n=6, all three) and
:func:`paired_step.cafe_family_verdicts_12` (n=12, the two conditional ones).

Completion held **6/6 in all 24 cells**, so no cell's clearance was bought by
freezing and every number above is readable.

The interaction generalizes. The *sign flip* does not, and the difference is
the threshold. `EPS_CLEARANCE` is a float-noise guard, so a -0.0002 m step —
a fifth of a millimetre — counts as "the term harms alone". Re-read at 5 cm,
all three scenes are `CONDITIONAL` instead (:func:`verdict_ladder`), i.e. the
term is *silent* alone rather than harmful. What survives every threshold is
that no scene reads `MAIN_EFFECT` or `INERT`: :func:`is_interaction` is the
predicate for that conjunction, and it is the branch-level claim this walk
licenses. D-218's stronger reading — "the risk term alone costs clearance" —
holds only on the crossing scene, where the step is ~2 cm.

What this cannot settle
-----------------------

The weights are **not scale-matched** — `w_epist = 200`, `w_geom = 40`,
`w_ped = 50` are each the value its own cycle used, and they enter different
cost summands with different units (`weight_units` grades exactly this). The
coefficient caveat `geometric_null` states is therefore live in both
directions: an arm that *loses* here may merely be quieter. An arm that
**ties or wins** is not exposed to that objection, and neither is a
`BOUGHT_WITH_FREEZE` verdict — a freeze is not a volume setting.

`shadow` is additionally expected to read as **inert**: D-021 measured
`ShadowCostCritic` signal-free at `w_epist = 200` (byte-identical trajectories,
per-sample spread 0.00 at all 92 control steps). Its presence here is not an
oversight — it is the axis's *neither* cell, and an inert arm is the correct
null for "does spanning the geometry axis matter at all". :meth:`inert` reports
it rather than letting it masquerade as a tie.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .ab import ArmRun, SweepStats, seed_sweep, summarize
from .controllers.stock_mppi import MPPIParams
from .scenario import load_scenario

# Named, not inherited — D-118/D-124's rung discipline, and D-217's finding that
# the shipped `lam = 0.1` is a greedy argmin (median ESS ~1 of 256) where a
# claim about trajectory difference is satisfied by noise. Matched across all
# three arms: that is what makes the seeds paired in the sense that matters.
LAM = 0.8

# Six paired seeds — D-217's ensemble, kept so this comparison's `predicted`
# column is denominated against the same population its headline was.
SEEDS = (0, 1, 2, 3, 4, 5)

# The three eligible scenes, per `scene_eligibility` (the other five are
# GOAL_BALL_BLOCKED / NO_DECLARED_MARGIN / NO_OBSTACLES and cannot score a
# clearance comparison at all).
SCENES = (
    "eval/scenarios/cafe_obstacle_crossing_v0.yaml",
    "eval/scenarios/cafe_convoy_v0.yaml",
    "eval/scenarios/cafe_head_on_v0.yaml",
)

# (controller, kwargs) per arm. Each weight is the value its own cycle named;
# see the module docstring on why they are **not** scale-matched.
ARMS: dict[str, tuple[str, dict]] = {
    "baseline": ("risk_mppi", {"w_risk": 0.0}),
    "shadow": ("risk_mppi", {"w_risk": 0.0, "w_epist": 200.0}),
    "geometric": ("geometric_mppi", {"w_geom": 40.0}),
    "predicted": ("risk_mppi", {"w_risk": 0.0, "w_ped": 50.0}),
}

#: Clearance deltas below this are not called improvements (metres).
EPS_CLEARANCE = 1e-6


@dataclass(frozen=True)
class ArmReading:
    """One arm on one scene, scored jointly on clearance **and** completion."""

    scene: str
    arm: str
    stats: SweepStats
    base: SweepStats
    runs: tuple[ArmRun, ...]
    base_runs: tuple[ArmRun, ...]

    @property
    def d_worst_clearance(self) -> float:
        """Worst-case clearance moved, arm - baseline. D-217's headline metric."""
        return self.stats.min_clearance - self.base.min_clearance

    @property
    def d_median_clearance(self) -> float:
        return self.stats.median_clearance - self.base.median_clearance

    @property
    def d_reached(self) -> int:
        """Completion moved, arm - baseline. Negative is the freezing tax."""
        return self.stats.n_reached - self.base.n_reached

    @property
    def timeout_rate(self) -> float:
        """The column PGIF's headline moved its collisions into."""
        n = self.stats.n
        return (n - self.stats.n_reached) / n if n else float("nan")

    @property
    def base_timeout_rate(self) -> float:
        n = self.base.n
        return (n - self.base.n_reached) / n if n else float("nan")

    @property
    def inert(self) -> bool:
        """Did this arm execute the baseline's trajectories byte-for-byte?

        D-021's failure mode, checked rather than assumed. An inert arm ties on
        every metric, and a tie that is really an absence must not be reported
        as a tie — `verdict` returns `INERT` for it.
        """
        return all(np.array_equal(a.traj, b.traj)
                   for a, b in zip(self.runs, self.base_runs))

    @property
    def verdict(self) -> str:
        """One verdict over both columns. Clearance alone is never the answer.

        `BOUGHT_WITH_FREEZE` outranks `IMPROVED` deliberately: it is exactly the
        cell the feed's metric-selection critique names, and reporting it as an
        improvement with a completion footnote is the mistake being guarded.
        """
        if self.inert:
            return "INERT"
        if self.d_reached < 0:
            return ("BOUGHT_WITH_FREEZE"
                    if self.d_worst_clearance > EPS_CLEARANCE else "DEGRADED")
        if self.d_worst_clearance > EPS_CLEARANCE:
            return "IMPROVED"
        if self.d_worst_clearance < -EPS_CLEARANCE:
            return "WORSE"
        return "TIED"

    def __str__(self) -> str:  # pragma: no cover - formatting
        scene = self.scene.rsplit("/", 1)[-1].replace(".yaml", "")
        return (f"{scene:30s} {self.arm:10s} {self.verdict:18s} "
                f"worst {self.base.min_clearance:+.3f} -> "
                f"{self.stats.min_clearance:+.3f} m  "
                f"({self.d_worst_clearance:+.3f})  "
                f"reached {self.base.n_reached}/{self.base.n} -> "
                f"{self.stats.n_reached}/{self.stats.n}  "
                f"timeout {self.timeout_rate:.0%}")


def read_arm(scene: str, arm: str, seeds=SEEDS, lam: float = LAM) -> ArmReading:
    """Walk one arm and the baseline on the same seeds at the same temperature."""
    scen = load_scenario(scene)
    params = MPPIParams(lam=lam)

    # `params` is threaded explicitly rather than closed over: `default_lam_sites`
    # is a static detector and cannot see through a closure, so a call that omits
    # it reads as DEFAULTS — the census bills the temperature as unnamed even
    # though it is named one line up. Naming it at the call site is both the
    # truthful classification and the reason a reader can see the rung here.
    def walk(name: str, params: MPPIParams) -> list[ArmRun]:
        controller, kwargs = ARMS[name]
        return seed_sweep(scen, controller, seeds=seeds, params=params, **kwargs)

    base_runs, runs = walk("baseline", params=params), walk(arm, params=params)
    return ArmReading(scene=scene, arm=arm,
                      stats=summarize(runs), base=summarize(base_runs),
                      runs=tuple(runs), base_runs=tuple(base_runs))


def head_to_head(scenes=SCENES, seeds=SEEDS, lam: float = LAM
                 ) -> list[ArmReading]:
    """Every non-baseline arm on every scene, paired against a shared baseline."""
    arms = [a for a in ARMS if a != "baseline"]
    return [read_arm(scene, arm, seeds=seeds, lam=lam)
            for scene in scenes for arm in arms]


#: The scene D-217's headline was taken on — the 2x2's home.
INTERACTION_SCENE = SCENES[0]

#: The 2x2's axes, named once. `W_RISK_ROWS[0]` is the shipped default D-217
#: measured on top of; `W_RISK_ROWS[1]` is the same term read alone.
W_RISK_ROWS = (40.0, 0.0)
W_PED_COLS = (0.0, 50.0)


def risk_interaction(scene: str = INTERACTION_SCENE, seeds=SEEDS,
                     lam: float = LAM) -> dict[tuple[float, float], SweepStats]:
    """The 2x2 that separates D-217's denomination from this module's.

    Keyed `(w_risk, w_ped)`. The top row (`w_risk = 40`) is D-217's comparison;
    the bottom row (`w_risk = 0`) is the same term read alone. They disagree in
    sign, which is the finding — see the module docstring's table.
    """
    scen = load_scenario(scene)
    params = MPPIParams(lam=lam)
    return {
        (w_risk, w_ped): summarize(
            seed_sweep(scen, "risk_mppi", seeds=seeds, params=params,
                       w_risk=w_risk, w_ped=w_ped))
        for w_risk in W_RISK_ROWS for w_ped in W_PED_COLS
    }


def ped_step(cells, w_risk: float) -> float:
    """The `w_ped` step in one row of the 2x2, in worst-case clearance (m)."""
    return (cells[(w_risk, W_PED_COLS[1])].min_clearance
            - cells[(w_risk, W_PED_COLS[0])].min_clearance)


def interaction_sign_flip(cells) -> bool:
    """Does the `w_ped` step change sign between the two `w_risk` rows?

    True is the D-217-vs-this-module disagreement, stated as a predicate so a
    test can pin it rather than a docstring asserting it.
    """
    return ped_step(cells, W_RISK_ROWS[0]) * ped_step(cells, W_RISK_ROWS[1]) < 0.0


def step_bought_with_freeze(cells, w_risk: float) -> bool:
    """Did this row's `w_ped` step buy clearance by not finishing?

    The module's standing discipline (see the docstring): a clearance number is
    unreadable unless completion is held. Applied per *row*, because each row
    has its own baseline — the `w_ped = 0` cell at the same `w_risk`.
    """
    lo, hi = cells[(w_risk, W_PED_COLS[0])], cells[(w_risk, W_PED_COLS[1])]
    return (hi.min_clearance - lo.min_clearance) > EPS_CLEARANCE \
        and hi.n_reached < lo.n_reached


def interaction_verdict(cells, eps: float = EPS_CLEARANCE) -> str:
    """Grade one scene's 2x2. What kind of term is `w_ped` *here*?

    The vocabulary answers the question D-218 left open — it read one scene and
    could not say whether "interaction, not main effect" was a property of the
    term or of `cafe_obstacle_crossing_v0`:

    - `BOUGHT_WITH_FREEZE` — some row's gain came with lost completion, so the
      clearance comparison is unreadable and no other verdict may be returned.
      Checked **first**, for the same reason :meth:`ArmReading.verdict` checks
      it first: a frozen robot has excellent clearance.
    - `SIGN_FLIP` — the two rows disagree in sign and both steps are material.
      D-218's reading. The strongest form of "this is an interaction".
    - `CONDITIONAL` — one row moves materially, the other does not. Also an
      interaction, but a weaker claim than a flip: the term is silent alone
      rather than harmful alone.
    - `MAIN_EFFECT` — both rows move materially in the *same* direction, i.e.
      the term works with or without the risk term. This is the verdict that
      would narrow D-218 the way D-218 narrowed D-217.
    - `INERT` — neither row moves. The term does nothing on this scene at all.
    """
    if any(step_bought_with_freeze(cells, w) for w in W_RISK_ROWS):
        return "BOUGHT_WITH_FREEZE"
    top, bot = (ped_step(cells, w) for w in W_RISK_ROWS)
    material = [abs(top) > eps, abs(bot) > eps]
    if not any(material):
        return "INERT"
    if not all(material):
        return "CONDITIONAL"
    return "SIGN_FLIP" if top * bot < 0.0 else "MAIN_EFFECT"


def risk_interaction_matrix(scenes=SCENES, seeds=SEEDS, lam: float = LAM
                            ) -> dict[str, dict[tuple[float, float], SweepStats]]:
    """The 2x2 on every eligible scene, keyed by scene.

    D-218 measured the 2x2 on one scene and booked "PGIF is an interaction
    term" from it. One scene cannot separate a property of the *term* from a
    property of *that scene* — which is exactly the error D-218 itself caught
    D-217 making one denomination up. Three scenes is what makes the reading a
    branch-level claim, and it costs ~1m10 per scene.
    """
    return {scene: risk_interaction(scene=scene, seeds=seeds, lam=lam)
            for scene in scenes}


def interaction_verdicts(matrix) -> dict[str, str]:
    """:func:`interaction_verdict` per scene, keyed the same as the matrix."""
    return {scene: interaction_verdict(cells) for scene, cells in matrix.items()}


#: Thresholds the verdict is re-read at, spanning "any float difference counts"
#: to "5 cm or it did not happen". `EPS_CLEARANCE` is the module's float-noise
#: guard, not a physical scale; a clearance step of 0.2 mm is material to it and
#: to nothing else. Reading the verdict at one eps hides that.
EPS_LADDER = (EPS_CLEARANCE, 1e-3, 1e-2, 5e-2)

def verdict_ladder(cells, epsilons=EPS_LADDER) -> dict[float, str]:
    """:func:`interaction_verdict` re-read at each threshold in `epsilons`."""
    return {eps: interaction_verdict(cells, eps=eps) for eps in epsilons}


def verdict_is_threshold_robust(cells, epsilons=EPS_LADDER) -> bool:
    """Does the verdict survive being re-read at every threshold?

    False means the verdict names the threshold as much as the measurement —
    which is what the 3-scene walk found for `SIGN_FLIP`: it holds everywhere
    at `EPS_CLEARANCE` and nowhere at 5 cm, because the `w_risk = 0` steps are
    -0.0192 / -0.0055 / **-0.0002** m. The last is a fifth of a millimetre.
    """
    return len(set(verdict_ladder(cells, epsilons).values())) == 1


def is_interaction(cells, epsilons=EPS_LADDER) -> bool:
    """Is `w_ped` conditional on `w_risk` at *every* threshold?

    This is the claim that survived the 3-scene walk. `SIGN_FLIP` did not — it
    decays to `CONDITIONAL` as the threshold grows — but both of those verdicts
    agree that the term does not stand alone, so the question is only whether
    any eps reads `MAIN_EFFECT` or `INERT`. That conjunction is what makes
    "PGIF is an interaction term" a branch-level statement rather than a
    threshold artifact.

    Stated as the *complement* of the two non-interaction verdicts rather than
    as membership in an allow-list of the two interaction ones. The readings
    are equivalent, but a module-level allow-list is an unwatched population
    (`guard_reflexivity`), and this predicate does not need one: `MAIN_EFFECT`
    and `INERT` are the verdicts :func:`interaction_verdict` returns when the
    rows agree, which is the thing being ruled out.
    """
    return not any(v in ("MAIN_EFFECT", "INERT")
                   for v in verdict_ladder(cells, epsilons).values())


def flip_is_scene_dependent(matrix) -> bool:
    """Do the scenes disagree about what kind of term `w_ped` is?

    True means the single-scene reading cannot be promoted to the term — the
    same shape D-218 found for `ShadowCostCritic`'s inertness, which read
    `INERT` on one scene and moved on another. Stated as a predicate so the
    answer is pinned by a test rather than asserted in prose.
    """
    return len(set(interaction_verdicts(matrix).values())) > 1


def freezing_tax(readings) -> list[ArmReading]:
    """The readings whose clearance was bought by not finishing."""
    return [r for r in readings if r.verdict == "BOUGHT_WITH_FREEZE"]


def main() -> None:  # pragma: no cover - CLI
    readings = head_to_head()
    for r in readings:
        print(r)
    taxed = freezing_tax(readings)
    print(f"\n{len(readings)} readings · {len(taxed)} BOUGHT_WITH_FREEZE · "
          f"{sum(1 for r in readings if r.verdict == 'INERT')} INERT")

    # The 2x2 is printed here and not left as a library function nobody calls:
    # `consumer_reach` flagged exactly that (`three_arm.risk_interaction` with
    # zero callers), and it was right — the table in the module docstring is
    # this module's headline, so the CLI that reports the head-to-head must be
    # able to reproduce it rather than leaving it to prose.
    matrix = risk_interaction_matrix(lam=LAM)
    verdicts = interaction_verdicts(matrix)
    for scene, cells in matrix.items():
        print(f"\nrisk x ped 2x2 on {scene.rsplit('/', 1)[-1]} "
              f"(worst-case clearance, m):")
        for w_risk in W_RISK_ROWS:
            lo, hi = cells[(w_risk, W_PED_COLS[0])], cells[(w_risk, W_PED_COLS[1])]
            print(f"  w_risk={w_risk:5.1f}  w_ped=0 {lo.min_clearance:+.4f}  "
                  f"w_ped=50 {hi.min_clearance:+.4f}  "
                  f"step {ped_step(cells, w_risk):+.4f}  "
                  f"reached {lo.n_reached}/{lo.n} -> {hi.n_reached}/{hi.n}")
        print(f"  sign flip: {interaction_sign_flip(cells)}  "
              f"verdict: {verdicts[scene]}")
    print(f"\nverdicts: {verdicts}")
    print(f"scene-dependent: {flip_is_scene_dependent(matrix)}")


if __name__ == "__main__":  # pragma: no cover - CLI
    main()

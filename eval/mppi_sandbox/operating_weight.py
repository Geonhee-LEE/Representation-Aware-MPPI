# SPDX-License-Identifier: BSD-3-Clause
"""Which `w_obs_soft` each scene's matrix cells run at, given D-126's survey.

D-125 moved a shipped scene's safety verdict for the first time (`unsafe_rate`
1.0000 → 0.0000 on `cafe_head_on_v0` between the shipped weight and 300), and
D-126 then refused to turn that into a global repin: the three sweepable scenes'
permitted rung sets are **disjoint**, because `cafe_convoy_v0` needs no relief
and tolerates only up to 30. `relief_interval.reconcile` reports that as
`PER_SCENE_REQUIRED`. This module is what `PER_SCENE_REQUIRED` actually means
operationally — the map from one scene's `ReliefInterval` to the weight its
cells are run at — and it exists so the headline can be re-measured at operating
points the scenes admit, instead of at one rung two of them are known to fail.

**The rule is `pick_lam`'s, not a second copy of it.** Both knobs are
multiplicative and both ladders are log-spaced, so "which rung represents this
admissible set" has the same answer for both, and `pick_weight` delegates rather
than restating it (D-047). Picking the log-middle rather than the cheapest
relieving rung is the substantive choice here, and it is `pick_lam`'s argument
verbatim: the threshold is by construction one ladder step from *not* relieving,
so a cell reported there is one calibration refresh from silently falling back
into the failure region. The cheapest rung is the smaller intervention; the
middle rung is the one whose verdict survives the ladder being re-walked. This
picks the second and says so, and `basis` records which rule fired so a later
change to the policy shows up as a diff rather than as drifting numbers.

Three things this deliberately does **not** do:

  * It does not repin `MPPIParams`. The shipped default stays 10.0; this is an
    operating point for a measurement, not a change to the controller. A repin
    is D-126's `GLOBAL_REPIN` verdict, which the survey refused.
  * It does not invent a weight for a scene the survey could not sweep.
    `cafe_freezing_v0` (no declared margin) and `cafe_cut_in_v0` (empty
    admissible λ window) keep the shipped weight under `UNSWEPT`, named rather
    than dropped — the same discipline `relief_interval.refused` applies.
  * It does not let a scene that needed no relief be *moved* by one that did.
    That is the whole content of D-126's disjointness finding, and a resolver
    that quietly gave convoy head-on's 300 would re-create exactly the global
    repin the survey refuted, one layer down.

**Honest scope limit.** The survey behind these intervals is measured on
`stock_mppi` (`relief_interval.survey`'s default), so a table applied to every
arm of the matrix is the *scene's* rung extrapolated across the controller axis.
That is the right call for a cross-controller comparison — matching the arms'
operating point is the point — but it is an extrapolation, and `measured_on`
carries the controller it was measured on so a per-arm survey later shows up as
a different table rather than as the same one silently reinterpreted.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Mapping, Sequence

from . import relief_interval
from .baseline_matrix import pick_lam
from .relief_interval import ReliefInterval

#: Why a scene runs at the weight it does. `basis` is reported per scene, and
#: the two "kept the shipped weight" cases are **not** merged: one is a scene
#: that voted for the shipped rung, the other is a scene the survey never
#: reached. Collapsing them would let an unswept scene read as an endorsement.
RELIEVED = "RELIEVED"
SHIPPED = "SHIPPED"
REPAIRED = "REPAIRED"
UNSWEPT = "UNSWEPT"
UNRELIEVED = "UNRELIEVED"


def pick_weight(permitted: Sequence[float]) -> float:
    """The rung a scene runs at, given the rungs it permits.

    Delegates to `baseline_matrix.pick_lam`: the argument for the log-space
    middle is about multiplicative knobs on log-spaced ladders and does not
    mention temperature anywhere. One statement of the rule, two names for it
    (D-047) — a wrapper, not a copy.
    """
    return pick_lam(permitted)


@dataclass(frozen=True)
class WeightChoice:
    """One scene's operating weight, the rule that produced it, and its vote."""

    scenario: str
    weight: float
    basis: str
    #: The rung set this choice was drawn from — `ReliefInterval.permits`,
    #: which is `relieving` for a scene demanding relief and `admissible` for
    #: every other. Empty for `UNSWEPT` / `UNRELIEVED`.
    permitted: tuple[float, ...] = ()
    #: Controller the survey behind `permitted` was measured on. `None` when
    #: no survey reached this scene.
    measured_on: str | None = None

    @property
    def moved(self) -> bool:
        """Does this scene run anywhere other than the shipped weight?"""
        return self.weight != relief_interval.shipped_weight()

    def __str__(self) -> str:
        rungs = ",".join(f"{v:g}" for v in self.permitted) or "-"
        return (f"{self.scenario:<32} w_obs_soft={self.weight:<7g} "
                f"{self.basis:<11} permits={rungs}")


def resolve(interval: ReliefInterval | None, *,
            shipped: float | None = None,
            controller: str = "stock_mppi") -> WeightChoice:
    """One scene's weight from its interval. `None` ⇒ the survey never swept it.

    The ladder, worst-first, mirroring `relief_interval.classify_scene`'s own
    verdict order so the two cannot disagree about what a scene is:

      * no interval          → shipped, `UNSWEPT`
      * `UNRELIEVED`         → shipped, `UNRELIEVED`. No tested rung relieves
        the scene, so there is no operating point to move it to; running it
        somewhere else would change the number without justifying it.
      * demands relief       → `pick_weight(relieving)`, `RELIEVED`
      * baseline admissible  → shipped, `SHIPPED`. A scene that tolerates the
        shipped weight is not moved off it — the minimal intervention.
      * otherwise            → `pick_weight(permits)`, `REPAIRED`. The scene
        needed no *relief* yet fails at its own shipped weight (out of band or
        frozen); it must run somewhere, and its own permitted set is the only
        place that is not a guess.

    **The `SHIPPED` test reads `baseline_admissible`, never `shipped in
    permits`.** The first draft of this function used the membership test and a
    test caught it immediately: the ladder is `(30, 100, 300, 1000, 3000)` and
    the shipped weight is `10.0`, so the shipped value is *by construction*
    absent from every `permits` set, and the membership test is unconditionally
    false. Every no-relief scene would therefore have graded `REPAIRED` and been
    moved to the ladder's floor — `cafe_convoy_v0`, the scene whose veto is the
    entire content of D-126's disjointness finding, moved off the weight it
    voted for, by a branch whose docstring says it prevents exactly that. A
    scene's tolerance of a value that was never a rung is a *measurement*
    (`SweepResult.baseline.admissible`), and asking a rung set about it is a
    category error that happens to typecheck.
    """
    ship = relief_interval.shipped_weight() if shipped is None else float(shipped)
    if interval is None:
        return WeightChoice(scenario="?", weight=ship, basis=UNSWEPT)
    if interval.verdict == relief_interval.UNRELIEVED:
        return WeightChoice(scenario=interval.scenario, weight=ship,
                            basis=UNRELIEVED, measured_on=controller)
    permits = tuple(sorted(interval.permits))
    demands = interval.needs_relief and interval.resolvable
    if demands:
        # `permits` is already `relieving` in this branch — asking the interval
        # rather than re-deriving it keeps one statement of that rule.
        return WeightChoice(scenario=interval.scenario,
                            weight=pick_weight(permits), basis=RELIEVED,
                            permitted=permits, measured_on=controller)
    if interval.baseline_admissible:
        return WeightChoice(scenario=interval.scenario, weight=ship,
                            basis=SHIPPED, permitted=permits,
                            measured_on=controller)
    if not permits:
        return WeightChoice(scenario=interval.scenario, weight=ship,
                            basis=UNRELIEVED, measured_on=controller)
    return WeightChoice(scenario=interval.scenario, weight=pick_weight(permits),
                        basis=REPAIRED, permitted=permits,
                        measured_on=controller)


def table(survey: relief_interval.ReliefSurvey, *,
          scenarios: Iterable[str] = (),
          controller: str = "stock_mppi") -> dict[str, WeightChoice]:
    """scene-file → `WeightChoice`, covering every name in `scenarios`.

    Scenes the survey refused (and any name it simply never saw) get an
    `UNSWEPT` choice at the shipped weight rather than being absent, so a
    caller iterating the table sees the whole matrix and not just the part that
    could be measured — the empty-denominator failure D-107/D-120 both booked,
    arriving here as a silently short table.
    """
    by_scene = {i.scenario: i for i in survey.intervals}
    names = list(dict.fromkeys([*by_scene, *(survey.refused or {}), *scenarios]))
    out: dict[str, WeightChoice] = {}
    for name in names:
        choice = resolve(by_scene.get(name), controller=controller)
        if by_scene.get(name) is None:
            choice = WeightChoice(scenario=name, weight=choice.weight,
                                  basis=UNSWEPT)
        out[name] = choice
    return out


def weights(choices: Mapping[str, WeightChoice]) -> dict[str, float]:
    """The plain scene-file → float map `baseline_matrix.run_matrix` consumes."""
    return {name: c.weight for name, c in choices.items()}


def render(choices: Mapping[str, WeightChoice]) -> str:
    lines = [f"operating weights (shipped = {relief_interval.shipped_weight():g})"]
    lines += [f"   {choices[name]}" for name in sorted(choices)]
    moved = [n for n in sorted(choices) if choices[n].moved]
    lines.append(f"   moved off shipped: {len(moved)}/{len(choices)}"
                 + (f" — {', '.join(moved)}" if moved else ""))
    return "\n".join(lines)

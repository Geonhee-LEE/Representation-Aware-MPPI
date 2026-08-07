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


# --------------------------------------------------------------------------
# Q-113 — does the scene's weight survive on each *cell* of that scene's row?
# --------------------------------------------------------------------------
#
# The table above is keyed by scene, and the honest-scope-limit at the top of
# this module says why that is an extrapolation across the controller axis.
# D-127 then paid for it: `risk_mppi/cafe_obstacle_crossing_v0` was handed the
# scene's 1000, graded `ESS_OUT_OF_BAND`, and **left the near-miss denominator**
# (6 cells/48 seeds → 5/40) rather than being answered. Nothing in this module
# could have seen that coming — `weights()` hands over a float and the cell
# discovers its inadmissibility only afterwards, as a missing row.
#
# `audit_cell` closes that: given the scene's choice and the cell's *own*
# measured interval, it says whether the scene weight is admissible there and,
# if not, what the cell's own weight would be. The point is not to change the
# headline — Q-113's lean keeps the headline per-scene, because per-cell weights
# re-confound the cross-controller delta exactly as per-cell temperature did
# (D-123). The point is that an excluded cell should be **named before the
# matrix runs**, from a measurement, instead of inferred afterwards from a hole.

#: The scene's operating weight is admissible on this cell too. The cell stays
#: in the denominator and the arms are matched — nothing to report but the pass.
CELL_AGREES = "CELL_AGREES"
#: The scene's weight is inadmissible here, but the cell has an admissible
#: weight of its own. The cell is measurable, just not at the row's operating
#: point — so the headline may keep the row's weight and must name this cell.
CELL_DIFFERS = "CELL_DIFFERS"
#: No tested rung is admissible on this cell, and neither is the shipped
#: weight. There is no operating point on the weight axis for this cell at all,
#: which is a conclusion rather than a gap to be filled by a denser ladder.
CELL_UNSERVED = "CELL_UNSERVED"
#: No survey reached this cell, so its agreement with the scene weight is
#: **unknown** — not confirmed and not refuted. Kept apart from every verdict
#: above because those are measurements and this is their absence; `refusal`
#: carries `relief_interval.sweepable`'s reason. This is `UNSWEPT`'s shape one
#: layer out, and the reason it needs its own name is the same reason `table`
#: refuses to merge `SHIPPED` with `UNSWEPT`: a cell nobody asked, counted as a
#: cell that agreed, is the empty-denominator failure D-107 / D-120 / D-127 have
#: now booked three times.
CELL_UNSWEPT = "CELL_UNSWEPT"


def admits(interval: ReliefInterval, weight: float) -> bool:
    """Would this cell stay in the denominator if run at `weight`?

    **Admissibility, not relief.** A rung a cell tolerates but is still unsafe
    at yields a perfectly good number — an unsafe one. Testing `relieving` here
    would drop every cell whose safety problem the weight does not fix, which is
    the population the headline exists to count.

    The `weight not in admissible` case is **not** sufficient on its own, and the
    reason is the defect `resolve` books above: the ladder never contains the
    shipped weight, so a membership test against the rung set is unconditionally
    false for it. A cell asked about the shipped weight must be asked via
    `baseline_admissible`, which is a measurement of exactly that value. Same
    category error, one layer out — this is its second sighting, so it is one
    function with one test rather than an inline `in` at each call site (D-047).
    """
    if weight in interval.admissible:
        return True
    return (weight == relief_interval.shipped_weight()
            and interval.baseline_admissible)


@dataclass(frozen=True)
class CellAudit:
    """One (scene, controller) cell judged against its own scene's weight."""

    scenario: str
    controller: str
    #: The weight the scene-keyed table would run this cell at.
    scene_weight: float
    verdict: str
    #: Rungs admissible on this **cell** (not the scene). Empty ⇒ the cell
    #: tolerates nothing on the ladder — which does *not* mean it tolerates
    #: nothing, see `cell_baseline_admissible`.
    cell_admissible: tuple[float, ...] = ()
    #: Was the **shipped** weight measured admissible on this cell? Carried
    #: because it is not derivable from `cell_admissible` — the ladder never
    #: contains it — and `tolerated` / `knife_edge` need it.
    cell_baseline_admissible: bool = False
    #: Where this cell would run if the table were keyed by cell. `None` for
    #: `CELL_UNSERVED`, and equal to `scene_weight` under `CELL_AGREES`.
    cell_weight: float | None = None
    #: Why no survey reached this cell — `relief_interval.NO_DECLARED_MARGIN`
    #: or `NO_ADMISSIBLE_LAM`. Set only under `CELL_UNSWEPT`.
    refusal: str | None = None

    @property
    def measured(self) -> bool:
        """Was this cell's agreement actually measured, either way?"""
        return self.verdict != CELL_UNSWEPT

    @property
    def excluded(self) -> bool:
        """Does the scene-keyed headline lose this cell's seeds?

        **`not excluded` is not `agrees`.** An unswept cell is not excluded —
        nobody asked it — and it is not included either. Reading this property
        as a two-way split would put every unmeasured cell on the *safe* side of
        it by default, which is the exact asymmetry that let D-127's excluded
        cell be discovered afterwards as a hole. Consumers that need the third
        state read `measured`; `MatrixAudit` reports all three counts and never
        sums the last two into one.
        """
        return self.measured and self.verdict != CELL_AGREES

    @property
    def tolerated(self) -> tuple[float, ...]:
        """Every weight this cell is measured to tolerate — shipped included.

        `cell_admissible` is a **rung** set and the shipped weight is not a
        rung, so it can never appear there no matter how well the cell runs at
        it. A cell's tolerated set is the rungs *plus* the shipped value when
        `cell_baseline_admissible` says it was measured to hold there.
        """
        rungs = set(self.cell_admissible)
        if self.cell_baseline_admissible:
            rungs.add(relief_interval.shipped_weight())
        return tuple(sorted(rungs))

    @property
    def knife_edge(self) -> bool:
        """Is the cell's **own operating point** the only rung it tolerates?

        A lone rung is a measurement that happens to be reportable, not a robust
        operating point: the ladder neighbours on both sides fail, so the next
        calibration refresh can move the cell out of the band without the ladder
        changing. Worth printing next to the weight it qualifies — `cell_weight`
        alone reads far more solid than it is.

        **Both halves are tested, and the second one was missing.** D-128 wrote
        this docstring and implemented only `len(cell_admissible) == 1`, so a
        cell was flagged whenever *some* rung stood alone, whether or not that
        rung was where the cell runs. `risk_mppi/cafe_convoy_v0` is the live
        witness: it runs at the shipped 10 (via `baseline_admissible`) and its
        rung set is `{30}`, so the length test fired `KNIFE_EDGE` on a cell
        whose operating point was not in the set being counted — the third
        sighting of shipped-weight-is-never-a-rung, after `resolve` (D-127) and
        `admits` (D-128). Wrong in the alarming direction, which is the kind
        that gets designed around rather than noticed.
        """
        return (len(self.cell_admissible) == 1
                and self.cell_weight == self.cell_admissible[0])

    def __str__(self) -> str:
        rungs = ",".join(f"{v:g}" for v in self.cell_admissible) or "-"
        cw = "-" if self.cell_weight is None else f"{self.cell_weight:g}"
        tail = " KNIFE_EDGE" if self.knife_edge else ""
        if self.refusal:
            tail = f" ({self.refusal})"
        return (f"{self.controller}/{self.scenario:<32} "
                f"scene_w={self.scene_weight:<7g} cell_w={cw:<7} "
                f"admits={rungs:<12} {self.verdict}{tail}")


def audit_cell(choice: WeightChoice, cell: ReliefInterval, *,
               controller: str) -> CellAudit:
    """Grade the scene's operating weight against one cell's own measurement.

    `cell` must come from `relief_interval.survey(..., controller=controller)`
    on the same scene — the per-cell survey Q-113 asked for. The verdict order
    is agree → differs → unserved, and `CELL_UNSERVED` is decided by the cell
    having no admissible rung *and* no admissible baseline, so a cell that
    tolerates only the shipped weight grades `CELL_DIFFERS` (it has somewhere to
    run) rather than being written off.
    """
    scene_w = choice.weight
    admissible = tuple(sorted(cell.admissible))
    if admits(cell, scene_w):
        return CellAudit(scenario=cell.scenario, controller=controller,
                         scene_weight=scene_w, verdict=CELL_AGREES,
                         cell_admissible=admissible, cell_weight=scene_w,
                         cell_baseline_admissible=cell.baseline_admissible)
    own = resolve(cell, controller=controller)
    if not admits(cell, own.weight):
        # `resolve` falls back to the shipped weight for `UNRELIEVED` / no-rung
        # cells; if the cell does not tolerate that either, the fallback is not
        # an operating point and must not be reported as one.
        return CellAudit(scenario=cell.scenario, controller=controller,
                         scene_weight=scene_w, verdict=CELL_UNSERVED,
                         cell_admissible=admissible,
                         cell_baseline_admissible=cell.baseline_admissible)
    return CellAudit(scenario=cell.scenario, controller=controller,
                     scene_weight=scene_w, verdict=CELL_DIFFERS,
                     cell_admissible=admissible, cell_weight=own.weight,
                     cell_baseline_admissible=cell.baseline_admissible)


def unswept_cell(choice: WeightChoice, *, scenario: str, controller: str,
                 refusal: str) -> CellAudit:
    """The cell no survey reached, named rather than omitted.

    `audit_cell` takes a `ReliefInterval` and is right to demand one — it grades
    a weight against a *measurement*, and there is no honest verdict to return
    when the measurement does not exist. Making its `cell` argument optional
    would have put the absence of evidence through the same `admits` test as
    evidence, and the fallback would have been `CELL_AGREES`. So the missing
    case gets its own constructor and its own verdict instead.

    The cells that land here are real: `cafe_freezing_v0` declares no margin, so
    `relief_interval.sweepable` refuses it for **both** arms, and it is in the
    matrix regardless. Two of the eight cells therefore have no measured
    agreement with their scene weight and never will until the scene declares
    one — which is a fact about the scene file, not about the weight axis.
    """
    return CellAudit(scenario=scenario, controller=controller,
                     scene_weight=choice.weight, verdict=CELL_UNSWEPT,
                     refusal=refusal)


@dataclass(frozen=True)
class MatrixAudit:
    """Every cell of the matrix graded, with the three populations kept apart.

    `agrees + excluded + unswept == len(audits)` is the only sum that holds.
    There is deliberately no "included" count that folds `unswept` in on either
    side: the whole content of D-127 is that a cell missing from a denominator
    and a cell that was never asked are indistinguishable *after the fact*, and
    a summary that adds them is how they become indistinguishable again.
    """

    audits: tuple[CellAudit, ...] = ()

    @property
    def agrees(self) -> tuple[CellAudit, ...]:
        return tuple(a for a in self.audits if a.verdict == CELL_AGREES)

    @property
    def excluded(self) -> tuple[CellAudit, ...]:
        """Measured to be inadmissible at the scene weight — the footnotes."""
        return tuple(a for a in self.audits if a.excluded)

    @property
    def unswept(self) -> tuple[CellAudit, ...]:
        return tuple(a for a in self.audits if not a.measured)

    @property
    def keying_is_sound(self) -> bool:
        """Does scene-keying cost the headline nothing it could have measured?

        True iff **no** measured cell disagrees with its scene's weight. This is
        the question the audit exists to answer, and it is deliberately not a
        threshold on how many disagree: one `CELL_DIFFERS` is a caveat the
        headline can carry by name, but it is still a cell running somewhere its
        row does not, so the honest report is the count and the names — the
        boolean is only the "nothing to report" shortcut.
        """
        return not self.excluded


def audit_matrix(choices: Mapping[str, WeightChoice],
                 surveys: Mapping[str, relief_interval.ReliefSurvey],
                 *, scenarios: Sequence[str] = ()) -> MatrixAudit:
    """Grade every (scene, controller) cell against its scene's weight.

    `choices` is the scene-keyed table (`table(...)`); `surveys` maps a
    **controller** to that controller's own per-cell survey, i.e. the output of
    `relief_interval.survey(..., controller=c)`. Scenes default to the ones the
    choices cover, so the walk is the whole matrix and not the part that swept.

    A cell is looked up in its controller's survey by scene name. Found ⇒
    `audit_cell`. Refused ⇒ `unswept_cell` carrying the refusal reason. Absent
    from both ⇒ also `unswept_cell`, because a scene the survey neither swept
    nor refused is one it never saw, which is the same epistemic state under a
    less informative name.
    """
    names = list(scenarios) or sorted(choices)
    shipped = relief_interval.shipped_weight()
    out: list[CellAudit] = []
    for controller in sorted(surveys):
        survey = surveys[controller]
        by_scene = {i.scenario: i for i in survey.intervals}
        refused = dict(survey.refused or {})
        for name in names:
            choice = choices.get(name) or WeightChoice(
                scenario=name, weight=shipped, basis=UNSWEPT)
            interval = by_scene.get(name)
            if interval is None:
                out.append(unswept_cell(
                    choice, scenario=name, controller=controller,
                    refusal=refused.get(name, "not_surveyed")))
                continue
            out.append(audit_cell(choice, interval, controller=controller))
    return MatrixAudit(audits=tuple(out))


def render_audits(audits: Sequence[CellAudit]) -> str:
    lines = ["cell audit vs scene-keyed operating weights"]
    lines += [f"   {a}" for a in audits]
    excluded = [f"{a.controller}/{a.scenario}" for a in audits if a.excluded]
    unswept = [f"{a.controller}/{a.scenario}" for a in audits if not a.measured]
    lines.append(f"   excluded from the scene-keyed headline: "
                 f"{len(excluded)}/{len(audits)}"
                 + (f" — {', '.join(excluded)}" if excluded else ""))
    # Printed on its own line even when zero. A count that disappears when
    # empty is one a reader cannot distinguish from a count nobody took.
    lines.append(f"   never asked (no survey reached them): "
                 f"{len(unswept)}/{len(audits)}"
                 + (f" — {', '.join(unswept)}" if unswept else ""))
    return "\n".join(lines)

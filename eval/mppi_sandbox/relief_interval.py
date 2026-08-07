# SPDX-License-Identifier: BSD-3-Clause
"""Q-111 — is the relieving `w_obs_soft` the *same* across scenes, or per-scene?

Why this exists
---------------
D-125 showed a single weight (`w_obs_soft = 300`) takes both 8/8-unsafe scenes
to 0/8 at a matched temperature, every seed reaching and every seed's ESS in
band. That is one rung on two scenes, and Q-111 asks the question it cannot
answer: does *one* number serve the whole matrix, or does each scene want its
own? The stakes are not tuning convenience. D-125 already carries a
counter-example in its own result — `cafe_convoy_v0` was **already** 0/8 safe
at the shipped weight and leaves the ESS band at 300, so the rung that rescues
two scenes charges sampler compliance to a third that needed nothing. A global
repin is therefore not free, and Q-111's (a)/(b)/(c) turn on whether any rung
is simultaneously enough for the scenes that need relief and gentle enough for
the ones that do not.

The object is a witness set, not an interval
---------------------------------------------
The tempting formulation is per-scene intervals `[threshold, ceiling]` and an
interval intersection. That is unsound here, and the reason is worth stating
because the shape looks so natural: **admissibility is not known to be
contiguous in the weight.** `Rung.admissible` is `all_reached AND ess_in_band`,
and neither is monotone in `w_obs_soft` by any argument this repo has made — a
mid-ladder rung may freeze or leave the band while its neighbours on both sides
do not. An interval intersection would silently assume otherwise and could
nominate a rung that is inadmissible on the very scene it was derived from.

So `reconcile` intersects the actual **sets** of tested rung values that are
admissible on every scene *and* relieving on every scene that needs relief.
`threshold` and `ceiling` survive as per-scene **reports** — they are what a
reader wants to see — but no verdict is computed from them.

The two directions are not equally strong
------------------------------------------
`GLOBAL_REPIN` is a **witness**: a concrete rung was run on every scene and
passed both filters everywhere. That is a proof at the seed count used.

`PER_SCENE_REQUIRED` is a **claim at ladder resolution**: no *tested* rung
served everyone. A denser ladder could find one between two rungs that failed
for opposite reasons (too weak on head_on, too strong for convoy's band). The
asymmetry is reported rather than smoothed over, because the project has twice
shipped an empty-set result whose emptiness was structural and once where it
was density (`lam_windows.yaml`'s `min_spread` exists to tell those apart), and
the honest default is to say which kind this one is not yet known to be.

Scenes that refuse are named, not dropped
------------------------------------------
Q-111's action line says "all five obstacle-bearing scenes". Two of them cannot
be swept, for two different pre-existing reasons, and both refusals are the
repo working correctly:

* `cafe_freezing_v0` declares **no** `min_distance_to_obstacle`, so
  `barrier_ceiling.sweep` refuses it (D-120's `unscored_margin` rule — scoring
  it against a convenient default would hand it a free clean sheet).
* `cafe_cut_in_v0` has an **empty admissible temperature window** on
  `stock_mppi` (`completes_anywhere: false`) — it never finishes at any rung on
  the calibrated ladder, so there is no temperature at which a barrier sweep
  would be measuring the barrier.

A cross-scene verdict computed over "the scenes that happened to run" while
silently dropping two is exactly the empty-denominator failure D-107 and D-120
both booked, so `ReliefSurvey.refused` carries them by name and reason and
`str()` prints them alongside the verdict.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Sequence

from . import barrier_ceiling, near_miss
from .baseline_matrix import lam_for_cell
from .controllers.stock_mppi import MPPIParams
from .scenario import Scenario

#: Per-scene verdicts.
RELIEF_FOUND = "RELIEF_FOUND"
NO_RELIEF_NEEDED = "NO_RELIEF_NEEDED"
UNRELIEVED = "UNRELIEVED"
#: The scene is unsafe, but by *less* than one rung can distinguish itself at
#: this seed count — so no rung can be shown to relieve it, and that failure is
#: a property of the ensemble, not of the knob. Kept separate from `UNRELIEVED`
#: because conflating them lets a scene at 1/16 unsafe veto a global repin on
#: the strength of a difference the survey cannot measure.
SUBRESOLUTION = "SUBRESOLUTION"

#: Cross-scene verdicts.
GLOBAL_REPIN = "GLOBAL_REPIN"
PER_SCENE_REQUIRED = "PER_SCENE_REQUIRED"
UNRELIEVABLE = "UNRELIEVABLE"

#: Why a scene could not be swept at all.
NO_DECLARED_MARGIN = "no_declared_margin"
NO_ADMISSIBLE_LAM = "no_admissible_lam"

#: Geometric ladder around the shipped `w_obs_soft = 10` and D-125's relieving
#: 300. Geometric because the knob is a gain: 30 → 100 and 100 → 300 are the
#: same intervention, so a linear ladder would spend its density in the wrong
#: place (the same argument `pick_lam` makes for temperature).
DEFAULT_LADDER = (30.0, 100.0, 300.0, 1000.0, 3000.0)


@dataclass(frozen=True)
class ReliefInterval:
    """One scene's answer: which tested rungs relieve it, and which it tolerates.

    `relieving` and `admissible` are the sets `reconcile` intersects.
    `threshold` / `ceiling` are reports derived from them for the table.
    """

    scenario: str
    lam: float
    baseline_value: float
    baseline_unsafe: float
    needs_relief: bool
    #: Tested rung values that pass both pre-existing filters on this scene.
    admissible: tuple[float, ...] = ()
    #: Tested rung values that are admissible **and** beat the baseline's
    #: `unsafe_rate` by `barrier_ceiling.MIN_IMPROVEMENT`. One statement of
    #: "relieves" — the predicate is `barrier_ceiling.classify`'s, not a
    #: second copy of it (D-047).
    relieving: tuple[float, ...] = ()
    verdict: str = UNRELIEVED

    @property
    def threshold(self) -> float | None:
        """Cheapest rung that relieves this scene. `None` if none does."""
        return min(self.relieving) if self.relieving else None

    @property
    def ceiling(self) -> float | None:
        """Largest rung the scene still tolerates — where the knob stops being
        a cost-term change. `None` if no tested rung is admissible."""
        return max(self.admissible) if self.admissible else None

    @property
    def resolvable(self) -> bool:
        """Is this scene's safety gap big enough that relief could be *shown*?

        A baseline below `MIN_IMPROVEMENT` cannot be improved on by that much,
        so every rung — including a perfect one — fails the relief test for
        arithmetic reasons. The scene needs a larger ensemble, not a larger
        weight.
        """
        return self.baseline_unsafe >= barrier_ceiling.MIN_IMPROVEMENT

    @property
    def permits(self) -> frozenset[float]:
        """Rungs this scene permits a *global* repin to use.

        A scene needing demonstrable relief votes with `relieving`; every other
        scene votes with `admissible`. `SUBRESOLUTION` sits in the second group
        deliberately: it may not *demand* a relief the survey cannot measure,
        but it still gets to refuse a rung it would freeze or de-band on.
        """
        demands_relief = self.needs_relief and self.resolvable
        return frozenset(self.relieving if demands_relief else self.admissible)

    def __str__(self) -> str:
        thr = "-" if self.threshold is None else f"{self.threshold:g}"
        ceil = "-" if self.ceiling is None else f"{self.ceiling:g}"
        return (f"{self.scenario:<32} lam={self.lam:<5g} "
                f"base_unsafe={self.baseline_unsafe:.4f} "
                f"needs={'y' if self.needs_relief else 'n'} "
                f"threshold={thr:<7} ceiling={ceil:<7} {self.verdict}")


@dataclass(frozen=True)
class ReliefSurvey:
    """Every sweepable scene's interval, the refusals, and the joint verdict."""

    intervals: tuple[ReliefInterval, ...] = ()
    #: scene → reason, for scenes that could not be swept at all.
    refused: Mapping[str, str] = None  # type: ignore[assignment]
    #: Rungs admissible on every swept scene and relieving on every scene that
    #: needs relief. Non-empty ⇒ `GLOBAL_REPIN`, and its `min` is the witness.
    witnesses: tuple[float, ...] = ()
    verdict: str = PER_SCENE_REQUIRED

    @property
    def witness(self) -> float | None:
        """Cheapest rung serving every swept scene, or `None`."""
        return min(self.witnesses) if self.witnesses else None

    @property
    def unrelieved(self) -> tuple[str, ...]:
        return tuple(i.scenario for i in self.intervals
                     if i.verdict == UNRELIEVED)

    @property
    def subresolution(self) -> tuple[str, ...]:
        """Scenes unsafe by less than the ensemble can resolve. A `GLOBAL_REPIN`
        carrying any of these is a witness for the scenes that could be
        measured and silent about these — worth printing, not worth vetoing."""
        return tuple(i.scenario for i in self.intervals
                     if i.verdict == SUBRESOLUTION)

    def __str__(self) -> str:
        head = f"relief survey · {self.verdict}"
        if self.witness is not None:
            head += f" · witness w_obs_soft={self.witness:g}"
        lines = [head] + [f"   {i}" for i in self.intervals]
        for scene, why in sorted((self.refused or {}).items()):
            lines.append(f"   {scene:<32} REFUSED ({why})")
        return "\n".join(lines)


def classify_scene(result: barrier_ceiling.SweepResult) -> ReliefInterval:
    """Turn one `barrier_ceiling` walk into this scene's contribution.

    `needs_relief` is `baseline.unsafe_rate > 0` — *any* unsafe seed, not
    `MIN_IMPROVEMENT`. The two thresholds answer different questions and must
    not be shared: `MIN_IMPROVEMENT` asks whether one rung distinguishes itself
    from another (a resolution question about an 8-seed ensemble), while this
    asks whether the scene has a safety problem at all. A scene at 1/8 unsafe
    has one, and reusing the resolution bar here would declare it clean.
    """
    base = result.baseline
    admissible = tuple(r.value for r in result.rungs if r.admissible)
    relieving = tuple(
        r.value for r in result.rungs
        if r.admissible
        and base.unsafe_rate - r.unsafe_rate >= barrier_ceiling.MIN_IMPROVEMENT)
    needs = base.unsafe_rate > 0.0
    resolvable = base.unsafe_rate >= barrier_ceiling.MIN_IMPROVEMENT
    if not needs:
        verdict = NO_RELIEF_NEEDED
    elif relieving:
        verdict = RELIEF_FOUND
    elif not resolvable:
        verdict = SUBRESOLUTION
    else:
        verdict = UNRELIEVED
    return ReliefInterval(
        scenario=result.scenario,
        lam=result.lam,
        baseline_value=base.value,
        baseline_unsafe=base.unsafe_rate,
        needs_relief=needs,
        admissible=admissible,
        relieving=relieving,
        verdict=verdict,
    )


def reconcile(intervals: Sequence[ReliefInterval],
              refused: Mapping[str, str] | None = None) -> ReliefSurvey:
    """Intersect the per-scene permitted rung sets; classify what is left.

    Set intersection rather than interval arithmetic — see the module preamble.
    `UNRELIEVABLE` outranks an empty intersection because the two say different
    things: an empty intersection means no *shared* rung was found, while
    `UNRELIEVED` means a scene has no rung at all, which no per-scene policy
    fixes either. Reporting the weaker verdict there would suggest (b) solves
    something it does not.
    """
    intervals = tuple(intervals)
    if not intervals:
        return ReliefSurvey(intervals=(), refused=dict(refused or {}),
                            witnesses=(), verdict=PER_SCENE_REQUIRED)
    if any(i.verdict == UNRELIEVED for i in intervals):
        return ReliefSurvey(intervals=intervals, refused=dict(refused or {}),
                            witnesses=(), verdict=UNRELIEVABLE)
    shared: frozenset[float] = intervals[0].permits
    for i in intervals[1:]:
        shared &= i.permits
    witnesses = tuple(sorted(shared))
    return ReliefSurvey(
        intervals=intervals,
        refused=dict(refused or {}),
        witnesses=witnesses,
        verdict=GLOBAL_REPIN if witnesses else PER_SCENE_REQUIRED,
    )


def sweepable(scenario: Scenario, scenario_file: str,
              controller: str = "stock_mppi") -> str | None:
    """`None` if this scene can be swept, else the refusal reason.

    Both refusals delegate to the module that owns the rule — `near_miss` for
    the margin, the calibration table for the temperature — so neither is
    restated here (D-047).
    """
    if not near_miss.is_scorable_margin(near_miss.margin_for(scenario)):
        return NO_DECLARED_MARGIN
    lam, why = lam_for_cell(scenario_file, controller)
    if lam is None:
        return NO_ADMISSIBLE_LAM
    return None


def survey(scenarios: Mapping[str, Scenario], *,
           ladder: Sequence[float] = DEFAULT_LADDER,
           controller: str = "stock_mppi",
           seeds: Sequence[int] | None = None,
           measure_spread: bool = False) -> ReliefSurvey:
    """Sweep every sweepable scene at its own calibrated rung and reconcile.

    The temperature is **per scene**, from `lam_for_cell` — the shipped answer
    to "which rung does this cell run at". It is not matched across scenes and
    must not be: scenes have disjoint admissible windows (`shared_window: []`),
    so one temperature for the survey would run most cells out of band and the
    ESS filter this whole survey rests on would be measuring the temperature
    rather than the weight.
    """
    from . import ab

    seeds = tuple(ab.DEFAULT_SEEDS) if seeds is None else tuple(seeds)
    intervals: list[ReliefInterval] = []
    refused: dict[str, str] = {}
    for name, scen in scenarios.items():
        why = sweepable(scen, name, controller)
        if why is not None:
            refused[name] = why
            continue
        lam, _ = lam_for_cell(name, controller)
        assert lam is not None  # `sweepable` just checked
        result = barrier_ceiling.sweep(
            scen, barrier_ceiling.WEIGHT_KNOB, list(ladder), lam=lam,
            scenario_name=name, seeds=seeds, controller=controller,
            measure_spread=measure_spread)
        intervals.append(classify_scene(result))
    return reconcile(intervals, refused)


def shipped_weight() -> float:
    """The `w_obs_soft` a repin would move, read from the params dataclass."""
    return float(getattr(MPPIParams(), barrier_ceiling.WEIGHT_KNOB))


def _main(argv: Sequence[str] | None = None) -> int:
    import argparse
    from pathlib import Path

    from .scenario import load_scenario

    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("scenarios", nargs="+", help="scenario yaml paths")
    ap.add_argument("--ladder", type=float, nargs="+", default=list(DEFAULT_LADDER))
    ap.add_argument("--seeds", type=int, default=8)
    ap.add_argument("--controller", default="stock_mppi")
    args = ap.parse_args(argv)

    scens = {Path(p).name: load_scenario(p) for p in args.scenarios}
    res = survey(scens, ladder=args.ladder, controller=args.controller,
                 seeds=range(args.seeds))
    print(res)
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(_main())

# SPDX-License-Identifier: BSD-3-Clause
"""Which scenes can host a two-sided arm comparison *at all*?

`margin_sweep` closed the question one scene down: on `cafe_head_on_v0` arm
coverage is 0/4 and its **ceiling is 1/4**, because at `w ∈ {75, 100}` the two
arms' clearance distributions are so nearly disjoint that no threshold sits
interior to both (D-158). Neither more seeds nor re-grading repairs that. So
the successor question is about the *scene*, and STATE posed it as: which of
the **8 matrix scenes** have overlapping arm clearance distributions at the
published margin?

That phrasing carries two assumptions this module refutes before any overlap is
measured, both of them about the **population** rather than the answer:

- **The denominator is not 8, it is 3.** Five of the eight scenes cannot host
  the question. Three (`cafe_straight_v0`, `city_curved_v0`, `city_figure8_v0`)
  contain **no obstacles**, so there is no clearance to compare — the same
  empty-population-reads-as-clean shape D-107 named. `cafe_freezing_v0` carries
  two obstacles but **declares no margin**, so there is no threshold at which
  to grade a rung two-sided; `feasibility.declared_margin` returns `None` there
  precisely so this case cannot be folded into a number. And `cafe_cut_in_v0`
  is **provably infeasible** — its goal ball is permanently occupied, best
  achievable clearance **−0.20 m**, so no controller finishes it and no
  comparison on it means anything.
- **There is no such thing as "the" published margin.** The three eligible
  scenes do not share one: `cafe_head_on_v0` declares **0.40 m**,
  `cafe_convoy_v0` and `cafe_obstacle_crossing_v0` declare **0.30 m**. This is
  not news to the code — `feasibility.declared_margin` and `near_miss` both say
  so in as many words — but it *is* news to a cross-scene reading, because
  `Headroom` refuses to grade two arms against different margins, exactly as
  `BandSweep` found within one scene. A census that quotes
  `scorable_band.PUBLISHED_MARGIN` across scenes is quoting a **scene**
  constant as if it were a band one.

What is left after the screen is the finding, and it is smaller than the
question assumed: **3 of 8 scenes are eligible, and 2 of those 3 have never
been walked.** The only eligible scene with recorded per-seed clearances is
`cafe_head_on_v0` — the one already proved to cap out at 1/4. So every
remaining route to a two-sided rung runs through `cafe_convoy_v0` or
`cafe_obstacle_crossing_v0`, both at margin 0.30, neither ever measured. That
is a two-scene walk, not an eight-scene survey, and it is the whole of what the
successor question can still buy.

Exclusions are recorded as a **set, not a first match**. `cafe_straight_v0`
fails two ways at once (no obstacles *and* no declared margin) and both are
kept, because D-157's lesson was that collapsing a multi-reason judgement to
one reason produces a wrong population claim rather than a missing one. The
single-valued :attr:`SceneEligibility.verdict` is a precedence pick over that
set for display; the set is what the counts are computed from.

Reported, never thresholded (D-044). No test asserts the eligible count is
non-zero or that any scene is measured: today's honest 3-of-8 and 1-of-3 would
become a permanent red the moment a scene is retired, and the censoring lesson
of D-158 applies here too — a scene gets *less* eligible as its effect grows.

Nothing here runs a simulation. Every input is a scenario yaml plus the
already-owned readers in `feasibility`; the cost is milliseconds.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence

from .feasibility import declared_margin, goal_ball_clearance
from .scenario import Scenario, load_scenario
from .scorable_band import PUBLISHED_SCENARIO

#: A scene with no obstacles. Clearance to nothing is not a measurement, and an
#: empty near-miss population reads as a *clean* one (D-107).
NO_OBSTACLES = "NO_OBSTACLES"

#: Obstacles, but the acceptance block declares no `min_distance_to_obstacle`.
#: There is no threshold at which "two-sided" means anything, and substituting
#: one decides what the scene refused to say.
NO_DECLARED_MARGIN = "NO_DECLARED_MARGIN"

#: The goal ball is permanently occupied — `feasibility`'s screen proves no
#: controller completes the scene, so no arm comparison on it is meaningful.
GOAL_BALL_BLOCKED = "GOAL_BALL_BLOCKED"

#: Survives every screen: has obstacles, declares a margin, and is completable.
ELIGIBLE = "ELIGIBLE"

#: Precedence for collapsing an exclusion *set* to one displayed verdict, most
#: fundamental first. Order is load-bearing only for display; every count in
#: :class:`EligibilityCensus` reads the set.
_PRECEDENCE = (NO_OBSTACLES, NO_DECLARED_MARGIN, GOAL_BALL_BLOCKED)

#: Band-level verdicts.
NO_SCENE_ELIGIBLE = "NO_SCENE_ELIGIBLE"
NONE_MEASURED = "NONE_MEASURED"
PARTIALLY_MEASURED = "PARTIALLY_MEASURED"
FULLY_MEASURED = "FULLY_MEASURED"

#: Scenes for which per-seed clearance magnitudes are recorded in the repo.
#: `separation_reproduction`'s four rungs are all on `PUBLISHED_SCENARIO`; the
#: name is imported rather than spelled so the two cannot drift (D-047).
RECORDED_SCENES: frozenset[str] = frozenset({PUBLISHED_SCENARIO})


def _n_obstacles(scenario: Scenario) -> int:
    return len(getattr(scenario, "obstacles", ()) or ())


@dataclass(frozen=True)
class SceneEligibility:
    """Whether one scene can host a two-sided arm comparison."""

    scenario: str
    n_obstacles: int
    #: The scene's own declared margin, or `None`. Never defaulted — the
    #: absent case is a distinct exclusion, not a zero.
    declared_margin: float | None
    #: Best clearance attainable in the goal ball; negative ⇒ provably blocked.
    best_goal_clearance: float
    #: Every reason this scene is excluded. Empty ⇒ eligible. A set because a
    #: scene can fail more than one screen and both are facts about it.
    exclusions: frozenset[str]

    @property
    def eligible(self) -> bool:
        return not self.exclusions

    @property
    def verdict(self) -> str:
        """The exclusion to *display*, by `_PRECEDENCE`; `ELIGIBLE` if none."""
        for reason in _PRECEDENCE:
            if reason in self.exclusions:
                return reason
        return ELIGIBLE

    @property
    def measured(self) -> bool:
        """Are per-seed clearance magnitudes recorded for this scene?

        Only meaningful for an eligible scene — an ineligible one is not
        measured in the sense that matters, whatever data exists.
        """
        return self.eligible and self.scenario in RECORDED_SCENES

    def __str__(self) -> str:
        margin = "none" if self.declared_margin is None else f"{self.declared_margin:.2f}"
        tail = "measured" if self.measured else ("unmeasured" if self.eligible else "")
        extra = f" ({tail})" if tail else ""
        return (f"{self.scenario}: {self.verdict}{extra} — "
                f"obstacles {self.n_obstacles}, margin {margin}")


def screen(scenario: Scenario, name: str) -> SceneEligibility:
    """Apply every eligibility screen to one loaded scenario."""
    n_obs = _n_obstacles(scenario)
    margin = declared_margin(scenario)
    reach = goal_ball_clearance(scenario)

    exclusions: set[str] = set()
    if n_obs == 0:
        exclusions.add(NO_OBSTACLES)
    if margin is None:
        exclusions.add(NO_DECLARED_MARGIN)
    # An obstacle-free scene has `inf` clearance and cannot be blocked; the
    # screen only convicts on a strictly negative reading, matching
    # `feasibility`'s "a negative verdict is a proof" asymmetry.
    if reach.best_clearance < 0.0:
        exclusions.add(GOAL_BALL_BLOCKED)

    return SceneEligibility(
        scenario=name,
        n_obstacles=n_obs,
        declared_margin=margin,
        best_goal_clearance=float(reach.best_clearance),
        exclusions=frozenset(exclusions),
    )


@dataclass(frozen=True)
class EligibilityCensus:
    """Population-level reading over the shipped scene matrix.

    Two counts, deliberately not folded together, for `ReplicationCensus`'s
    reason: **eligibility** is the denominator of the successor question and
    **measurement** is its coverage. A reader who takes "3 eligible" for
    progress reads two unwalked scenes as two available results.
    """

    scenes: tuple[SceneEligibility, ...]

    @property
    def eligible(self) -> tuple[SceneEligibility, ...]:
        return tuple(s for s in self.scenes if s.eligible)

    @property
    def excluded(self) -> tuple[SceneEligibility, ...]:
        return tuple(s for s in self.scenes if not s.eligible)

    @property
    def measured(self) -> tuple[SceneEligibility, ...]:
        return tuple(s for s in self.eligible if s.measured)

    @property
    def unmeasured(self) -> tuple[SceneEligibility, ...]:
        return tuple(s for s in self.eligible if not s.measured)

    @property
    def declared_margins(self) -> tuple[float, ...]:
        """The distinct margins the *eligible* scenes declare, ascending.

        More than one entry is the reason a cross-scene overlap reading cannot
        quote a single `PUBLISHED_MARGIN`: `Headroom` grades one margin.
        """
        return tuple(sorted({s.declared_margin for s in self.eligible
                             if s.declared_margin is not None}))

    @property
    def margin_is_shared(self) -> bool:
        return len(self.declared_margins) <= 1

    @property
    def verdict(self) -> str:
        if not self.eligible:
            return NO_SCENE_ELIGIBLE
        if not self.measured:
            return NONE_MEASURED
        if self.unmeasured:
            return PARTIALLY_MEASURED
        return FULLY_MEASURED

    def count(self, reason: str) -> int:
        """How many scenes carry `reason` — over the exclusion *sets*, so a
        scene failing two screens is counted under both."""
        return sum(1 for s in self.scenes if reason in s.exclusions)

    def __str__(self) -> str:
        lines = [
            f"scene eligibility: {self.verdict} — "
            f"{len(self.eligible)}/{len(self.scenes)} eligible, "
            f"{len(self.measured)}/{len(self.eligible)} measured",
        ]
        if not self.margin_is_shared:
            margins = ", ".join(f"{m:.2f}" for m in self.declared_margins)
            lines.append(f"  eligible scenes declare {len(self.declared_margins)} "
                         f"distinct margins ({margins}) — not one band margin")
        for s in self.scenes:
            lines.append(f"  {s}")
        return "\n".join(lines)


def census(root: str | Path = "eval/scenarios",
           scenarios: Sequence[str | Path] | None = None) -> EligibilityCensus:
    """Screen every shipped scene. No simulation; yaml reads only."""
    paths: Iterable[Path]
    if scenarios is None:
        paths = sorted(Path(root).glob("*_v0.yaml"))
    else:
        paths = [Path(p) for p in scenarios]
    return EligibilityCensus(
        scenes=tuple(screen(load_scenario(p), p.stem) for p in paths))


def main(argv=None):
    import argparse

    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--root", default="eval/scenarios")
    args = ap.parse_args(argv)
    print(census(args.root))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())

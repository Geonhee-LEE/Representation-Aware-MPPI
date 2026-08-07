# SPDX-License-Identifier: BSD-3-Clause
"""P5's first quantitative harness: controller × scenario baseline matrix.

Eighty-one consecutive cycles reported "no north-star movement" while STATE
carried the reason: *every P5 deliverable needs main to absorb the P3/P4 work
first*. That premise was never measured. It is false — `origin/main` already
carries all three controllers and all eight scenarios, so the matrix needs
nothing off any branch. This module is that matrix.

Cost is **not** uniform, and the first estimate written here was wrong the same
way the premise was. Measured 2026-08-07, `stock_mppi`, one seed:

    cafe_straight   0.29 s      cafe_cut_in     2.56 s
    cafe_head_on    0.44 s      city_figure8   14.40 s

A 50× spread, so "one run is 0.3 s" (the `cafe_straight` reading, taken first
and generalised) understates the 8-seed matrix by more than an order of
magnitude. Budget per-scene, and keep `city_*` out of anything that runs in
the test suite.

What it is **not** is a fifth hand-rolled primitive. `ab.seed_sweep` /
`ab.summarize` already own the seed × speed × completion × ESS discipline, and
`ab`'s own docstring parks the aggregator here ("deliberately not here:
p-values … belong with the P5 aggregator"). `feasibility.is_avoidance_measurable`
already owns the avoidance denominator. This file adds exactly one thing: the
**admissibility ladder** that decides which cells may contribute to a headline,
and the headline itself.

Two axes, not one grade (D-116's precedent, and for its reason — the axes
disagree on real data). A scene with no obstacles is a perfectly good
path-tracking measurement and a vacuous avoidance measurement:

  * ``tracking_reportable``  — every seed finished. Nothing else is required;
    cross-track error on an empty scene is a real number about the controller.
  * ``avoidance_reportable`` — every seed finished **and** the scene contains
    obstacles **and** the sampler actually weighed the cost (`ess_in_band`).

Collapsing these to one flag is what makes 4-of-8 empty scenes read as an 8/8
clean avoidance record. Keeping them apart is why `headline()` prints two
denominators and names every excluded cell rather than quietly shrinking to
the cells that happened to work.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence

from .ab import ArmRun, SweepStats, seed_sweep, summarize
from .calibrate_lam import is_scenario_yaml
from .controllers import REGISTRY
from .controllers.stock_mppi import MPPIParams
from .feasibility import is_avoidance_measurable
from .scenario import load_scenario

#: Seeds for the shipped matrix. `ab.DEFAULT_SEEDS` is the same ensemble; named
#: here so a caller can shrink it without reaching into `ab`.
DEFAULT_SEEDS = range(8)

#: Cell verdicts, worst-first. `run_cell` returns the *first* that applies, so
#: the order is the ladder: a cell that never finished is not additionally
#: graded on its ESS, because an unfinished run's ESS says nothing.
NOT_REACHED = "NOT_REACHED"
ESS_UNKNOWN = "ESS_UNKNOWN"
ESS_OUT_OF_BAND = "ESS_OUT_OF_BAND"
NO_OBSTACLES = "NO_OBSTACLES"
OK = "OK"

#: Table-level verdicts, decided from `lam_windows.yaml` *before* any sweep is
#: paid for. They are not ladder rungs: a cell that no temperature makes
#: admissible cannot be graded by running it at one, so the sweep is skipped
#: rather than run and then discarded.
LAM_UNCALIBRATED = "LAM_UNCALIBRATED"
NO_ADMISSIBLE_LAM = "NO_ADMISSIBLE_LAM"

#: Statuses whose cell produced **no run**, so neither axis may count it.
#: `NOT_REACHED` is here because an unfinished run's tracking error is not a
#: statement about tracking; the two table verdicts are here because nothing
#: was executed at all. Keeping this as one named set is what stops a new
#: verdict from silently defaulting into a denominator.
UNRUN = frozenset({NOT_REACHED, LAM_UNCALIBRATED, NO_ADMISSIBLE_LAM})


def pick_lam(admissible: Sequence[float]) -> float:
    """The rung a cell runs at, given its admissible window.

    The **log-space middle** rung, for the reason `ab._closest` already gives:
    temperature acts multiplicatively, so 0.2 → 0.4 and 0.4 → 0.8 are the same
    intervention and a linear midpoint would not be a midpoint. On an
    even-length window this takes the upper of the two central rungs, which is
    a tie-break and not a claim — `test_baseline_matrix` pins it so a later
    change to it shows up as a diff rather than as drifting numbers.

    Picking the *middle* rather than an endpoint is the whole point: the
    endpoints of an admissible window are one ladder step from being
    inadmissible, so a cell reported at its boundary is one calibration
    refresh away from silently leaving the band.
    """
    rungs = sorted(admissible)
    if not rungs:
        raise ValueError("empty admissible window has no representative rung")
    return float(rungs[len(rungs) // 2])


def lam_for_cell(scenario_file: str, controller: str,
                 windows: dict | None = None) -> tuple[float | None, str | None]:
    """Resolve one cell's temperature from the calibration table.

    Returns `(lam, None)` when the cell is runnable, or `(None, verdict)` when
    the table already answers it. Reads `calibrate_lam.load_windows` — the
    reader that exists for this file — rather than re-parsing it here (D-047,
    and D-118 shipped that exact duplication one cycle ago).
    """
    from .calibrate_lam import load_windows

    cells = load_windows() if windows is None else windows
    cell = cells.get((scenario_file, controller))
    if cell is None:
        return (None, LAM_UNCALIBRATED)
    admissible = tuple(cell.get("admissible", ()))
    if not admissible:
        return (None, NO_ADMISSIBLE_LAM)
    return (pick_lam(admissible), None)


def default_scenarios(root: str | Path = "eval/scenarios") -> tuple[Path, ...]:
    """The shipped scene set, sorted.

    The glob matches `lam_windows.yaml` — the calibration table, not a scene —
    so it has to be screened out. This asks `calibrate_lam.is_scenario_yaml`
    rather than carrying a filename allow-list: that predicate already exists
    for exactly this glob and exactly this file, and a typed copy of it here
    would be a second statement of one rule (D-047), which is also what the
    census flagged the moment the copy was written.
    """
    return tuple(sorted(
        p for p in Path(root).glob("*.yaml") if is_scenario_yaml(str(p))
    ))


@dataclass(frozen=True)
class Cell:
    """One controller on one scenario across a seed ensemble.

    `status` is the ladder verdict; the two `*_reportable` flags are what the
    headline consumes. They are deliberately not derivable from each other:
    `NO_OBSTACLES` is tracking-reportable and avoidance-blind, `NOT_REACHED`
    is neither, and an out-of-band cell is tracking-reportable while its
    avoidance number is a statement about the sampler rather than the cost.
    """

    controller: str
    scenario: str
    status: str
    n_seeds: int
    successes: int
    stats: SweepStats | None = None
    lam: float | None = None

    @property
    def tracking_reportable(self) -> bool:
        return self.status not in UNRUN

    @property
    def avoidance_reportable(self) -> bool:
        return self.status == OK

    @property
    def success_rate(self) -> float:
        return self.successes / self.n_seeds if self.n_seeds else float("nan")


def _status(stats: SweepStats, measurable: bool) -> str:
    if not stats.all_reached:
        return NOT_REACHED
    if not measurable:
        return NO_OBSTACLES
    if stats.ess_in_band is None:
        return ESS_UNKNOWN
    if not stats.ess_in_band:
        return ESS_OUT_OF_BAND
    return OK


def run_cell(scenario_path: str | Path, controller: str,
             seeds: Iterable[int] = DEFAULT_SEEDS,
             lam: float | None = None, **arm_kwargs) -> Cell:
    """Sweep one (controller, scenario) pair and grade it.

    `successes` is the joint north-star event — reached the goal **and** never
    collided. Counting either alone is how a freeze buys a clean record.

    `lam` is forwarded to the controller. Left `None` the controller keeps its
    shipped default, which is what produced D-118's twelve `ESS_OUT_OF_BAND`
    cells: at `lam = 0.1` the median ESS is ~1.01 of 256, so the sampler is a
    greedy argmin and its avoidance behaviour describes the temperature rather
    than any cost term.
    """
    scenario = load_scenario(scenario_path)
    if lam is not None:
        # `params=MPPIParams(lam=...)` is the injection `ab.lam_probe` uses;
        # `lam` is not a controller kwarg (`StockMPPI.__init__` takes `params`).
        arm_kwargs = {**arm_kwargs, "params": MPPIParams(lam=float(lam))}
    runs: list[ArmRun] = seed_sweep(scenario, controller, seeds, **arm_kwargs)
    stats = summarize(runs)
    return Cell(
        controller=controller,
        scenario=Path(scenario_path).stem,
        status=_status(stats, is_avoidance_measurable(scenario)),
        n_seeds=len(runs),
        successes=sum(1 for r in runs if r.reached_goal and not r.collided),
        stats=stats,
        lam=lam,
    )


@dataclass(frozen=True)
class Headline:
    """Cross-cell aggregate. Every denominator carries its exclusions."""

    tracking_cells: int
    tracking_total: int
    avoidance_cells: int
    avoidance_total: int
    success_rate: float
    collision_rate: float
    min_clearance: float
    excluded: tuple[tuple[str, str], ...] = ()

    def as_dict(self) -> dict:
        return {
            "tracking_reportable": f"{self.tracking_cells}/{self.tracking_total}",
            "avoidance_reportable": f"{self.avoidance_cells}/{self.avoidance_total}",
            "success_rate": self.success_rate,
            "collision_rate": self.collision_rate,
            "min_clearance": self.min_clearance,
            "excluded": [{"cell": c, "why": w} for c, w in self.excluded],
        }


@dataclass(frozen=True)
class Matrix:
    """The full grid plus its headline."""

    cells: tuple[Cell, ...] = ()
    controllers: tuple[str, ...] = ()
    scenarios: tuple[str, ...] = ()

    def headline(self) -> Headline:
        """Aggregate over *reportable* cells, naming what was left out.

        `success_rate` is scoped to tracking-reportable cells and
        `collision_rate` / `min_clearance` to avoidance-reportable ones,
        because those are the populations on which each number means anything.
        An empty population yields `nan`, never a vacuous 1.0 — D-107's
        empty-population-reads-as-clean is the exact failure this avoids.
        """
        track = [c for c in self.cells if c.tracking_reportable]
        avoid = [c for c in self.cells if c.avoidance_reportable]
        excluded = tuple(
            (f"{c.controller}/{c.scenario}", c.status)
            for c in self.cells if not c.avoidance_reportable
        )
        seeds = sum(c.n_seeds for c in track)
        wins = sum(c.successes for c in track)
        collisions = sum(c.stats.collisions for c in avoid if c.stats)
        avoid_seeds = sum(c.n_seeds for c in avoid)
        clearances = [c.stats.min_clearance for c in avoid if c.stats]
        return Headline(
            tracking_cells=len(track),
            tracking_total=len(self.cells),
            avoidance_cells=len(avoid),
            avoidance_total=len(self.cells),
            success_rate=wins / seeds if seeds else float("nan"),
            collision_rate=(collisions / avoid_seeds
                            if avoid_seeds else float("nan")),
            min_clearance=min(clearances) if clearances else float("nan"),
            excluded=excluded,
        )


def run_matrix(scenarios: Sequence[str | Path] | None = None,
               controllers: Sequence[str] | None = None,
               seeds: Iterable[int] = DEFAULT_SEEDS,
               calibrated: bool = True,
               windows: dict | None = None) -> Matrix:
    """Every controller against every scenario. Cost is per-scene — see the
    module docstring's 50× spread, not "~0.3 s per seed".

    With `calibrated=True` (the default) each cell runs at its own admissible
    temperature from `lam_windows.yaml`, resolved **before** the sweep: a cell
    whose window is empty is `NO_ADMISSIBLE_LAM` and is never run, because
    Q-035 already settled that no tested temperature makes it a reportable
    surface and paying for eight seeds cannot change that answer. Passing
    `calibrated=False` reproduces D-118's shipped-default matrix.
    """
    scens = tuple(scenarios) if scenarios is not None else default_scenarios()
    ctrls = tuple(controllers) if controllers is not None else tuple(sorted(REGISTRY))
    seeds = tuple(seeds)
    if calibrated and windows is None:
        from .calibrate_lam import load_windows
        windows = load_windows()

    cells: list[Cell] = []
    for c in ctrls:
        for s in scens:
            lam, verdict = ((None, None) if not calibrated
                            else lam_for_cell(Path(s).name, c, windows))
            if verdict is not None:
                cells.append(Cell(controller=c, scenario=Path(s).stem,
                                  status=verdict, n_seeds=0, successes=0))
                continue
            cells.append(run_cell(s, c, seeds, lam=lam))
    return Matrix(cells=tuple(cells), controllers=ctrls,
                  scenarios=tuple(Path(s).stem for s in scens))


def render(matrix: Matrix) -> str:
    """Text table + headline. The excluded list is never elided."""
    lines = ["| controller | scenario | lam | status | success | collisions | min_clr |",
             "|---|---|---|---|---|---|---|"]
    for c in matrix.cells:
        st = c.stats
        collisions = str(st.collisions) if st else "-"
        min_clr = f"{st.min_clearance:.3f}" if st else "-"
        lam = f"{c.lam:g}" if c.lam is not None else "-"
        seeds = f"{c.successes}/{c.n_seeds}" if c.n_seeds else "-"
        lines.append(
            f"| {c.controller} | {c.scenario} | {lam} | {c.status} "
            f"| {seeds} | {collisions} | {min_clr} |"
        )
    h = matrix.headline()
    lines += [
        "",
        f"tracking-reportable cells : {h.tracking_cells}/{h.tracking_total}",
        f"avoidance-reportable cells: {h.avoidance_cells}/{h.avoidance_total}",
        f"success_rate  (tracking pop) : {h.success_rate:.4f}",
        f"collision_rate(avoidance pop): {h.collision_rate:.4f}",
        f"min_clearance (avoidance pop): {h.min_clearance:.4f}",
    ]
    if h.excluded:
        lines.append(f"excluded from avoidance ({len(h.excluded)}):")
        lines += [f"  - {cell}: {why}" for cell, why in h.excluded]
    return "\n".join(lines)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--controller", action="append", default=None)
    ap.add_argument("--scenario", action="append", default=None)
    ap.add_argument("--seeds", type=int, default=8)
    ap.add_argument("--json", default=None, help="write headline+cells here")
    ap.add_argument("--no-calibrated", dest="calibrated", action="store_false",
                    help="run every cell at the controller's shipped default "
                         "lam instead of its admissible rung (reproduces "
                         "D-118's 0/24 matrix)")
    args = ap.parse_args(argv)
    matrix = run_matrix(args.scenario, args.controller, range(args.seeds),
                        calibrated=args.calibrated)
    print(render(matrix))
    if args.json:
        Path(args.json).write_text(json.dumps({
            "headline": matrix.headline().as_dict(),
            "cells": [
                {"controller": c.controller, "scenario": c.scenario,
                 "status": c.status, "successes": c.successes,
                 "n_seeds": c.n_seeds, "lam": c.lam}
                for c in matrix.cells
            ],
        }, indent=2) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

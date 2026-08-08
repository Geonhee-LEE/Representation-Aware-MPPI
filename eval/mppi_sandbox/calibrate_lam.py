# SPDX-License-Identifier: BSD-3-Clause
"""Per-scene softmax-temperature calibration for the sandbox scenario matrix.

Why this exists
---------------
Four cycles (2026-08-02 12:00 → 15:00) narrowed the same defect. The shipped
`lam = 0.1` gives a median effective sample size of ~1 of K = 256, so the MPPI
update `U += sum_k w_k * noise_k` degenerates to `U += noise[argmin]` and an
additive cost term is audible only when it flips the argmin. Re-picking one
better `lam` does **not** repair it: `cafe_straight_v0` weights in band around
`lam ~ 0.3` while the hazard scenes need `~ 5.0`, and the two windows are
**disjoint** — each scene fails the Q-026 band from the *opposite* side at the
other's temperature. So the calibration unit is the **scene**, not the repo,
and this module is what makes "calibrate per scene" one call instead of one
cycle.

What it produces
----------------
`eval/scenarios/lam_windows.yaml` — a table keyed by `(scenario, controller)`
holding the rungs where **every** seed weighted inside the ESS band *and*
reached the goal (`ab.LamProbe.admissible`), plus the per-seed spread that
decides whether a window can exist at all. Regenerate with::

    python3 -m eval.mppi_sandbox.calibrate_lam --out eval/scenarios/lam_windows.yaml

The table is a *measurement record*, not a config the controllers read. Nothing
imports it to change behaviour; the re-baseline (Q-032) will, once the queue
drains and there is one branch allowed to re-score every arm at once.

The admissibility criterion this settles (Q-035)
------------------------------------------------
Q-035 asked whether a single `lam` per (scene, controller) is admissible at
all, given per-seed ESS spans ~5x at fixed temperature. 14:00 answered "no" for
`offset = 0.3`; 15:00 showed that is scene-specific. The fork's option (c) was
"retire `offset = 0.3`" — retiring one scene **by name**, which generalises
badly: the next scene with the same pathology gets found the same expensive
way. `scene_is_calibratable` below states the criterion instead: a scene is an
admissible ablation surface for a controller iff its admissible window is
non-empty. That is measurable ahead of any A/B, applies to scenes nobody has
looked at yet, and retires `offset = 0.3` as a *consequence* rather than as a
special case.

Cost note (STATE item #6)
-------------------------
A full matrix pass is ~500 closed-loop runs, ~5 min. That is a script, not a
test — the suite went 81 s -> 130 s in one cycle and two more ladder files
would break D-016's "seconds, no ROS needed". The committed pytest coverage
spot-checks the recorded table against a *narrow* re-measurement; the wide
ladder lives here and runs on demand.
"""

from __future__ import annotations

import argparse
import glob
import os
from dataclasses import dataclass, field
from typing import Iterable, Sequence

from . import ab
from .scenario import load_scenario

#: Factor-2 log ladder spanning the full disjoint range measured 2026-08-02:
#: `cafe_straight_v0`'s window (0.2-0.4) sits ~20x below the hazard scenes'
#: (4.0-5.0), so a linear ladder either misses one end or costs 10x as many
#: rungs. The floor matters as much as the ceiling — 15:00's first sweep
#: started at 0.8, read `cafe_straight` as 0/8 everywhere, and nearly recorded
#: "no temperature works" when the truth was "wrong decade".
DEFAULT_LADDER: tuple[float, ...] = (0.05, 0.1, 0.2, 0.4, 0.8, 1.6, 3.2, 6.4)

#: Controllers worth calibrating. `risk_mppi` inherits `StockMPPI.command`, so
#: its ESS is the stock softmax's; it is listed separately because its extra
#: cost terms change the *cost spread* the temperature divides, which is the
#: quantity that decides audibility.
DEFAULT_CONTROLLERS: tuple[str, ...] = ("stock_mppi", "risk_mppi")


def default_weight() -> float:
    """`MPPIParams`' own obstacle weight — the weight a ladder walks at when
    the caller names none.

    Derived rather than restated so this module and `lam_window_key`'s
    `CALIBRATION_WEIGHT` cannot drift apart the day the controller default
    moves (D-047). Imported lazily to match `ab.lam_ladder`'s own deferral of
    the controller import.
    """
    from .controllers.stock_mppi import MPPIParams

    return float(MPPIParams().w_obs_soft)


@dataclass(frozen=True)
class SceneCalibration:
    """One (scene, controller) cell of the calibration table."""

    scenario: str
    controller: str
    admissible: tuple[float, ...]
    probes: tuple[ab.LamProbe, ...] = field(repr=False, default=())
    #: Obstacle weight the whole ladder was walked at. Carried on the cell
    #: rather than passed alongside it so that a window and the weight it was
    #: measured at cannot be separated: `to_yaml` reads this, so there is no
    #: call path that emits a table whose `calibration_weight` is a caller's
    #: assertion instead of the run's own record. `None` is not permitted —
    #: `calibrate` resolves the default before constructing the cell, because
    #: "unspecified" and "10.0" are the same *measurement* and only differ in
    #: how the caller spelled it.
    w_obs_soft: float = field(default_factory=lambda: default_weight())

    @property
    def ladder(self) -> tuple[float, ...]:
        """Rungs actually measured for this cell — not necessarily
        `DEFAULT_LADDER`, since refined cells carry extra rungs."""
        return tuple(sorted(p.lam for p in self.probes))

    @property
    def is_calibratable(self) -> bool:
        """True iff some temperature exists at which this arm is reportable.

        The Q-035 criterion. An empty window is not a search failure to be
        fixed with more rungs — 14:00 measured 14 temperatures on
        `offset = 0.3` and found none, because the band spans 10x while the
        per-seed ESS spread reaches 18x. When the spread exceeds the band, no
        rung can contain every seed, and the ladder's density is irrelevant.
        """
        return bool(self.admissible)

    @property
    def completes_anywhere(self) -> bool:
        """True iff *some* rung had every seed reach the goal.

        Separates the two ways a window can be empty, which the first cut of
        this module conflated. `ab.LamProbe.admissible` requires band
        compliance **and** completion, so an arm that never finishes has an
        empty window at every temperature no matter how tightly its seeds
        agree — measured here on `cafe_cut_in_v0` (per-seed ESS spread 1.00x,
        i.e. perfectly reproducible, yet no admissible rung). Calling that a
        temperature pathology would be exactly the Q-034 error: a completion
        failure wearing a temperature failure's clothes. No ladder, however
        fine, fixes it.
        """
        return any(p.all_reached for p in self.probes)

    @property
    def min_spread(self) -> float:
        """Narrowest per-seed ESS ratio over the ladder — the structural test.

        A window is reachable iff the ESS-vs-`lam` curve crosses the band more
        slowly than the seeds scatter. `min_spread` above the band's width
        (10x, from `ab.ESS_BAND_FRACTIONS`) means *no* rung can qualify, which
        distinguishes "this ladder missed it" from "this scene cannot have
        one" without running a finer ladder.
        """
        spreads = [p.spread for p in self.probes]
        return min(spreads) if spreads else float("inf")


def band_width() -> float:
    """Ratio the ESS band spans, from its own constants — the number
    `min_spread` has to beat. Derived, not hard-coded, so widening the band
    (Q-035 option (a)) automatically moves this threshold too."""
    lo, hi = ab.ESS_BAND_FRACTIONS
    return hi / lo


def calibrate(scenario_path: str, controller: str,
              lams: Iterable[float] = DEFAULT_LADDER,
              seeds: Iterable[int] = ab.DEFAULT_SEEDS,
              w_obs_soft: float | None = None,
              **arm_kwargs) -> SceneCalibration:
    """Profile one arm across the ladder and record its admissible window.

    `w_obs_soft` selects the obstacle weight the whole ladder is walked at;
    `None` means `MPPIParams`' default. It is a named parameter rather than an
    `arm_kwargs` passthrough because the emitted table has to *record* it — see
    `to_yaml`'s `calibration_weight`.
    """
    scenario = load_scenario(scenario_path)
    probes = tuple(ab.lam_ladder(scenario, controller, lams, seeds=seeds,
                                 w_obs_soft=w_obs_soft, **arm_kwargs))
    return SceneCalibration(
        scenario=os.path.basename(scenario_path),
        controller=controller,
        admissible=ab.admissible_lams(probes),
        probes=probes,
        w_obs_soft=default_weight() if w_obs_soft is None else float(w_obs_soft),
    )


def scene_is_calibratable(scenario_path: str, controller: str,
                          lams: Iterable[float] = DEFAULT_LADDER,
                          **kwargs) -> bool:
    """Q-035's precondition as a single call, for use before an A/B.

    Prefer the recorded table (`load_windows`) when one exists — this re-runs
    the whole ladder and is priced accordingly.
    """
    return calibrate(scenario_path, controller, lams, **kwargs).is_calibratable


def _calibrate_cell(job) -> SceneCalibration:
    """One matrix cell, coarse pass + bounded refinement. Module-level and
    tuple-argued so it is picklable for `multiprocessing`."""
    path, controller, ladder, seeds, refine_passes, w_obs_soft = job
    cal = calibrate(path, controller, ladder, seeds, w_obs_soft=w_obs_soft)
    for _ in range(refine_passes):
        if not needs_refinement(cal):
            break
        before = cal.ladder
        cal = refine(cal, path, seeds, w_obs_soft=w_obs_soft)
        if cal.ladder == before:
            break
    return cal


def _describe(cal: SceneCalibration) -> str:
    mark = "ok  " if cal.is_calibratable else (
        "FINE" if needs_refinement(cal) else "none")
    return (f"  {mark} {cal.scenario:28s} {cal.controller:11s} "
            f"window={list(cal.admissible)} "
            f"min_spread={cal.min_spread:.2f}x rungs={len(cal.ladder)}")


def calibrate_matrix(scenario_paths: Sequence[str],
                     controllers: Sequence[str] = DEFAULT_CONTROLLERS,
                     lams: Iterable[float] = DEFAULT_LADDER,
                     seeds: Iterable[int] = ab.DEFAULT_SEEDS,
                     verbose: bool = False,
                     refine_passes: int = 1,
                     jobs: int = 1,
                     w_obs_soft: float | None = None,
                     on_cell=None) -> list[SceneCalibration]:
    """Calibrate every cell, then bisect the cells whose empty window is not
    yet structural. Refinement is bounded (`refine_passes`) so a scene whose
    spread hugs the band width cannot spin forever.

    Cells are independent — each simulates its own arm from its own seeds — so
    `jobs > 1` fans them across processes. This is not premature: a serial
    matrix pass is ~1000 closed-loop runs and measured >10 min, which is long
    enough that the table stops being regenerated and starts being trusted
    stale. The whole point of Q-032's re-baseline is that a stale calibration
    is what got us here.

    `on_cell(cells_so_far)` fires as each cell lands, so the caller can persist
    partial results. Measured 2026-08-02: `city_figure8_v0` costs more than the
    other seven scenes together, and a wall-clock timeout inside it discarded
    fifteen finished cells because the table was written only at the end. A
    measurement that is consumable only if it fully succeeds ends up being run
    at settings small enough to be useless.
    """
    ladder = tuple(lams)
    seeds = tuple(seeds)
    jobs_list = [(p, c, ladder, seeds, refine_passes, w_obs_soft)
                 for p in scenario_paths for c in controllers]
    order = {(os.path.basename(p), c): i
             for i, (p, c, *_) in enumerate(jobs_list)}

    def key(cal):
        return order.get((cal.scenario, cal.controller), len(order))

    out = []

    def record(cal):
        if verbose:
            print(_describe(cal), flush=True)
        out.append(cal)
        if on_cell is not None:
            # Sorted on every call so a partial table is still scene-ordered.
            on_cell(sorted(out, key=key))

    if jobs > 1:
        import multiprocessing as mp

        # Unordered: a single slow cell must not withhold every finished one,
        # which is exactly what made the timeout total rather than partial.
        with mp.Pool(min(jobs, len(jobs_list))) as pool:
            for cal in pool.imap_unordered(_calibrate_cell, jobs_list):
                record(cal)
    else:
        for job in jobs_list:
            record(_calibrate_cell(job))

    return sorted(out, key=key)


def needs_refinement(cal: SceneCalibration) -> bool:
    """True when an empty window is *not yet* a reportable negative.

    A rung qualifies only if every seed lands inside the band, so when the
    narrowest per-seed spread over the ladder already exceeds the band's
    width, no temperature can contain the ensemble and a finer ladder is
    wasted compute — that is a structural empty window (`offset = 0.3`,
    measured over 14 rungs at 14:00). When the spread *does* fit, the coarse
    ladder may simply have stepped over the crossing, and reporting "no
    admissible temperature" would repeat 15:00's near-miss where a ladder
    starting 2x above `cafe_straight`'s window read as a pathology.
    """
    return (not cal.admissible
            and cal.completes_anywhere
            and cal.min_spread <= band_width())


def refine_ladder(cal: SceneCalibration) -> tuple[float, ...]:
    """Geometric midpoints bracketing the rung that came closest to the band.

    Bisects in log space because the ladder is log-spaced and ESS moves
    roughly multiplicatively in `lam`. Returns only the *new* rungs.
    """
    if not cal.probes:
        return ()
    ordered = sorted(cal.probes, key=lambda p: p.lam)
    best = max(ordered, key=lambda p: (p.n_in_band, p.all_reached))
    i = ordered.index(best)
    neighbours = [ordered[j].lam for j in (i - 1, i + 1) if 0 <= j < len(ordered)]
    return tuple(round((best.lam * n) ** 0.5, 4) for n in neighbours)


def refine(cal: SceneCalibration, scenario_path: str,
           seeds: Iterable[int] = ab.DEFAULT_SEEDS,
           w_obs_soft: float | None = None,
           **arm_kwargs) -> SceneCalibration:
    """Re-measure one cell on a finer ladder and merge the new rungs in.

    `w_obs_soft` is named rather than left to `arm_kwargs` so the refinement
    pass cannot silently drop back to the default weight and merge rungs
    measured at *two* weights into one window.
    """
    weight = default_weight() if w_obs_soft is None else float(w_obs_soft)
    if weight != cal.w_obs_soft:
        raise ValueError(
            f"refine at w_obs_soft={weight:g} would merge rungs into a cell "
            f"measured at {cal.w_obs_soft:g} — one window cannot have two "
            f"weights behind it")
    extra = refine_ladder(cal)
    if not extra:
        return cal
    scenario = load_scenario(scenario_path)
    probes = tuple(ab.lam_ladder(scenario, cal.controller, extra, seeds=seeds,
                                 w_obs_soft=weight, **arm_kwargs))
    merged = tuple(sorted(cal.probes + probes, key=lambda p: p.lam))
    return SceneCalibration(
        scenario=cal.scenario,
        controller=cal.controller,
        admissible=ab.admissible_lams(merged),
        probes=merged,
        w_obs_soft=cal.w_obs_soft,   # asserted equal to `weight` above
    )


def shared_window(cals: Sequence[SceneCalibration]) -> tuple[float, ...]:
    """Temperatures admissible for **every** cell passed in.

    Call it over the two arms of one A/B to get the temperatures that
    comparison may legally run at; call it over the whole matrix to ask
    whether a fixed-`lam` protocol exists at all. Measured 2026-08-02 the
    second answer is the empty tuple, which is Q-025's constructive form.
    """
    if not cals:
        return ()
    shared = set(cals[0].admissible)
    for cal in cals[1:]:
        shared &= set(cal.admissible)
    return tuple(sorted(shared))


def to_yaml(cals: Sequence[SceneCalibration], ladder: Sequence[float]) -> str:
    """Serialize the table by hand — the repo's only yaml dependency is the
    scenario *loader*, and a calibration record that cannot be read without
    installing a writer is a record nobody reads.

    Emits `calibration_weight:`, which is what `lam_window_key._rows` has
    always read and nothing has ever written — the field existed on the reader
    side only, so the shipped table graded `UNKEYED` for every caller and the
    guard could not reach `ON_KEY`/`OFF_KEY` at all (Q-116 (a)). The value is
    taken from the cells rather than from a parameter: a weight passed
    alongside a measurement is an assertion, a weight carried on it is a
    record. Cells measured at different weights are refused outright, because
    one top-level key cannot describe them and silently writing the first
    cell's weight is exactly the false provenance D-107 booked.
    """
    weights = {c.w_obs_soft for c in cals}
    if len(weights) > 1:
        raise ValueError(
            f"cells span {len(weights)} obstacle weights ({sorted(weights)}) — "
            f"one table records one `calibration_weight`; write one file per "
            f"weight")
    weight = weights.pop() if weights else default_weight()
    lines = [
        "# Per-scene softmax-temperature (`lam`) calibration for the sandbox.",
        "# GENERATED by `python3 -m eval.mppi_sandbox.calibrate_lam` — do not",
        "# hand-edit; re-run it instead. See eval/mppi_sandbox/calibrate_lam.py",
        "# for why the calibration unit is the scene and not the repo.",
        "#",
        "# `admissible`: rungs where EVERY seed weighted inside the ESS band",
        "#   (ab.ess_band) and reached the goal. Empty => this (scene,",
        "#   controller) is not a reportable ablation surface at any tested",
        "#   temperature (Q-035).",
        "# `min_spread`: narrowest per-seed ESS max/min over the ladder. Above",
        f"#   the band width ({band_width():.0f}x) no rung can qualify, so an",
        "#   empty window is structural rather than a ladder-density artifact.",
        "# `calibration_weight`: the `w_obs_soft` every ladder above was walked",
        "#   at. A window means nothing away from the weight it was measured",
        "#   at (D-134: crossing/risk moves [1.6, 3.2] -> {0.8} between w=10",
        "#   and w=150), so `lam_window_key.lookup` grades OFF_KEY against it.",
        "",
        f"calibration_weight: {weight:g}",
        f"ladder: [{', '.join(str(x) for x in ladder)}]",
        f"seeds: {len(list(ab.DEFAULT_SEEDS))}",
        f"band_width: {band_width():.1f}",
        "",
        "cells:",
    ]
    for cal in cals:
        lines += [
            f"  - scenario: {cal.scenario}",
            f"    controller: {cal.controller}",
            f"    admissible: [{', '.join(str(x) for x in cal.admissible)}]",
            f"    ladder: [{', '.join(str(x) for x in cal.ladder)}]",
            f"    min_spread: {cal.min_spread:.2f}",
            f"    completes_anywhere: {str(cal.completes_anywhere).lower()}",
            f"    calibratable: {str(cal.is_calibratable).lower()}",
        ]
    shared = shared_window(cals)
    lines += [
        "",
        "# Intersection over every cell above. Empty is the reportable result:",
        "# no single temperature serves the matrix, so cross-scene aggregates",
        "# must be read per scene (Q-036).",
        f"shared_window: [{', '.join(str(x) for x in shared)}]",
        "",
    ]
    return "\n".join(lines)


def load_windows(path: str = "eval/scenarios/lam_windows.yaml") -> dict:
    """Read the generated table back as `{(scenario, controller): cell}`.

    Deliberately a tiny hand-parser over the known generated shape rather than
    a yaml import: this is read by a test that must stay fast, and the file is
    machine-written so its shape is fixed.
    """
    cells: dict[tuple[str, str], dict] = {}
    cur: dict = {}
    with open(path) as fh:
        for raw in fh:
            line = raw.split("#", 1)[0].strip()
            if not line:
                continue
            if line.startswith("- scenario:"):
                cur = {"scenario": line.split(":", 1)[1].strip()}
                continue
            if not cur or ":" not in line:
                continue
            key, _, val = line.partition(":")
            key, val = key.strip("- ").strip(), val.strip()
            if key == "controller":
                cur["controller"] = val
            elif key in ("admissible", "ladder"):
                inner = val.strip("[]").strip()
                cur[key] = tuple(
                    float(x) for x in inner.split(",") if x.strip())
            elif key == "min_spread":
                cur["min_spread"] = float(val)
            elif key == "completes_anywhere":
                cur["completes_anywhere"] = val == "true"
            elif key == "calibratable":
                cur["calibratable"] = val == "true"
                cells[(cur["scenario"], cur["controller"])] = cur
    return cells


#: Keys `scenario.load_scenario` cannot do without. Used to tell a scenario
#: yaml from the other yamls that share the directory.
_SCENARIO_KEYS = ("start", "goal", "reference_path")


def is_scenario_yaml(path: str) -> bool:
    """True if `path` parses as a scenario rather than some other yaml.

    Exists because the default `--scenarios` glob is `eval/scenarios/*.yaml`,
    which matches this module's **own output** (`lam_windows.yaml`) once it has
    been written. The first generation therefore succeeded and every re-run
    died with `KeyError: 'start'` inside a worker — so the table the header
    tells you to regenerate rather than hand-edit could not, in fact, be
    regenerated. Found 2026-08-02 18:00 while re-measuring a scene whose
    obstacle set had changed.
    """
    import yaml as _yaml
    try:
        raw = _yaml.safe_load(open(path))
    except Exception:
        return False
    return isinstance(raw, dict) and all(k in raw for k in _SCENARIO_KEYS)


def main(argv: Sequence[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--scenarios", default="eval/scenarios/*.yaml",
                    help="glob of scenario yamls to calibrate")
    ap.add_argument("--controllers", nargs="+", default=list(DEFAULT_CONTROLLERS))
    ap.add_argument("--lams", nargs="+", type=float, default=list(DEFAULT_LADDER))
    ap.add_argument("--seeds", type=int, default=len(list(ab.DEFAULT_SEEDS)))
    ap.add_argument("--out", default="eval/scenarios/lam_windows.yaml")
    ap.add_argument("--jobs", "-j", type=int, default=os.cpu_count() or 1,
                    help="cells to calibrate in parallel")
    ap.add_argument("--refine-passes", type=int, default=1,
                    help="bisection passes for non-structural empty windows")
    ap.add_argument("--w-obs-soft", type=float, default=None,
                    help="obstacle weight to walk every ladder at; recorded "
                         "as `calibration_weight` in the output. Default: "
                         "MPPIParams' own. Windows are weight-specific, so a "
                         "table written at one weight is refused (OFF_KEY) by "
                         "lam_window_key.lookup at any other — write one file "
                         "per weight via --out.")
    args = ap.parse_args(argv)

    matched = sorted(glob.glob(args.scenarios))
    paths = [p for p in matched if is_scenario_yaml(p)]
    skipped = [p for p in matched if p not in paths]
    if skipped:                      # never drop inputs silently
        print(f"skipping {len(skipped)} non-scenario yaml: "
              f"{', '.join(os.path.basename(p) for p in skipped)}", flush=True)
    if not paths:
        print(f"no scenarios matched {args.scenarios}")
        return 1
    weight = default_weight() if args.w_obs_soft is None else args.w_obs_soft
    print(f"calibrating {len(paths)} scenes x {len(args.controllers)} controllers "
          f"x {len(args.lams)} rungs x {args.seeds} seeds "
          f"at w_obs_soft={weight:g}", flush=True)
    def flush(cells):
        with open(args.out, "w") as fh:
            fh.write(to_yaml(cells, args.lams))

    cals = calibrate_matrix(paths, args.controllers, args.lams,
                            range(args.seeds), verbose=True,
                            refine_passes=args.refine_passes, jobs=args.jobs,
                            w_obs_soft=weight, on_cell=flush)
    flush(cals)
    dead = [c for c in cals if not c.is_calibratable]
    print(f"wrote {args.out}: {len(cals)} cells at w_obs_soft={weight:g}, "
          f"{len(dead)} not calibratable, shared window {shared_window(cals)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

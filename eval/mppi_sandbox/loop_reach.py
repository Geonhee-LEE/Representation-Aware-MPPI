"""How many times did a loop-body ``assert`` actually run?

:mod:`assert_reach` counted 174 loop-body ``assert``s across the corpus and
graded 15 of them as *population claims* — ``a <= b``, ``a == {literal}``,
``len(a) == n`` — and then stopped, because counting is not reading.  This
module reads them, and the reading is a **runtime** one, because the question is
not answerable statically.

The hazard a loop-body assertion carries is not the one :mod:`assert_reach`
describes.  There, a claim goes unevaluated because a *failure* stopped the run
before it.  Here the run is **green** and the claim is still unevaluated::

    for cell in registry_cells():        # returns () this month
        assert set(cell["admissible"]) <= set(cell["ladder"])

Nothing failed.  Nothing was checked either.  A green loop-body assertion
establishes its claim over exactly the elements the loop yielded, and the number
of elements it yielded is invisible in the source, in the pass count, and in the
CI log.  It is visible in precisely one place: the execution.

So: run the tests with :mod:`sys.monitoring` watching the 15 assert lines, and
count.  ``DISABLE`` is what makes this cheap — every line that is not a target
returns it on first hit and is never reported again, so the overhead decays to
approximately nothing rather than scaling with suite runtime.

**Zero is two different findings, and separating them is the whole design.**
A count of zero means either the loop yielded nothing (a vacuous claim — the
finding) or the test never ran at all (skipped, deselected, or filtered — not a
finding, just an absence).  Conflating them would publish every ``slow``-marked
test as a vacuity.  The discriminator is the ``for`` statement's own line: it is
watched alongside the assert, and

===============  ==============  ==================================
``for`` count    assert count    grade
===============  ==============  ==================================
0                0               ``NOT_RUN`` — the test never ran
≥ 1              0               ``EMPTY`` — the loop yielded nothing
≥ 1              1               ``SINGLETON`` — population of one
≥ 1              ≥ 2             ``SAMPLED`` — n elements checked
===============  ==============  ==================================

``SINGLETON`` is graded separately from ``SAMPLED`` on D-101's argument: a
containment asserted over one element is a claim about that element wearing the
grammar of a claim about a population, and the grammar is what a reader carries
away.

Usage::

    python3 -m eval.mppi_sandbox.loop_reach report
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

from . import assert_reach as ar

REPO_ROOT = Path(__file__).resolve().parents[2]

#: Env var naming the JSON file of watch targets, read by the plugin half.
TARGETS_ENV = "LOOP_REACH_TARGETS"

#: Env var naming the JSON file the plugin half writes counts to.
COUNTS_ENV = "LOOP_REACH_COUNTS"

NOT_RUN = "NOT_RUN"
EMPTY = "EMPTY"
SINGLETON = "SINGLETON"
SAMPLED = "SAMPLED"

GRADES: tuple[str, ...] = (NOT_RUN, EMPTY, SINGLETON, SAMPLED)


# --------------------------------------------------------------------------
# 1. Targets: an assert line, and the `for` line that decides whether it runs.
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class Target:
    """One loop-body assertion, plus the loop header that gates it."""

    test_id: str
    kind: str
    assert_line: int
    loop_line: int
    text: str

    @property
    def rel(self) -> str:
        return self.test_id.split("::")[0]

    @property
    def path(self) -> Path:
        return REPO_ROOT / self.rel


def _loop_header_of(path: Path, assert_line: int) -> int | None:
    """Line of the innermost ``for``/``while`` whose body holds ``assert_line``.

    Innermost, not outermost: a nested loop's inner header is what decides
    whether the body runs, and it is the one whose zero-iteration case the
    outer loop's non-zero count would otherwise mask.
    """
    import ast

    tree = ast.parse(path.read_text(encoding="utf-8"))
    best: int | None = None
    for node in ast.walk(tree):
        if not isinstance(node, (ast.For, ast.While, ast.AsyncFor)):
            continue
        for child in ast.walk(node):
            if isinstance(child, ast.Assert) and child.lineno == assert_line:
                if best is None or node.lineno > best:
                    best = node.lineno
                break
    return best


def targets(paths: tuple[Path, ...] | None = None) -> tuple[Target, ...]:
    """The population-claim loop-body assertions, with their loop headers.

    ``paths`` mirrors :func:`assert_reach.sampled` so the negative controls
    reach these targets through the production path rather than a parallel one.
    """
    out: list[Target] = []
    for a in ar.sampled(paths):
        if not a.is_population_claim:
            continue
        loop = _loop_header_of(REPO_ROOT / a.test_id.split("::")[0], a.lineno)
        if loop is None:  # pragma: no cover -- in_loop implies a header exists
            continue
        out.append(Target(
            test_id=a.test_id, kind=a.kind, assert_line=a.lineno,
            loop_line=loop, text=a.text,
        ))
    return tuple(out)


# --------------------------------------------------------------------------
# 2. The plugin half — runs inside the pytest subprocess.
# --------------------------------------------------------------------------

_COUNTS: dict[str, int] = {}
_WATCHED: set[tuple[str, int]] = set()
_TOOL_ID = 3  # sys.monitoring.PROFILER_ID


def _callback(code, line_number):  # pragma: no cover -- exercised in subprocess
    key = (code.co_filename, line_number)
    if key not in _WATCHED:
        return sys.monitoring.DISABLE
    _COUNTS[f"{key[0]}:{line_number}"] = _COUNTS.get(f"{key[0]}:{line_number}", 0) + 1
    return None


def pytest_configure(config):  # pragma: no cover -- subprocess entry point
    """Install the line monitor.  Loaded via ``-p eval.mppi_sandbox.loop_reach``."""
    spec = os.environ.get(TARGETS_ENV)
    if not spec:
        return
    for path, line in json.loads(Path(spec).read_text(encoding="utf-8")):
        _WATCHED.add((str(Path(path).resolve()), int(line)))
    mon = sys.monitoring
    mon.use_tool_id(_TOOL_ID, "loop_reach")
    mon.register_callback(_TOOL_ID, mon.events.LINE, _callback)
    mon.set_events(_TOOL_ID, mon.events.LINE)


def pytest_unconfigure(config):  # pragma: no cover -- subprocess entry point
    """Tear the monitor down and dump the counts."""
    out = os.environ.get(COUNTS_ENV)
    if not out:
        return
    mon = sys.monitoring
    try:
        mon.set_events(_TOOL_ID, 0)
        mon.register_callback(_TOOL_ID, mon.events.LINE, None)
        mon.free_tool_id(_TOOL_ID)
    except ValueError:  # never installed
        pass
    Path(out).write_text(json.dumps(_COUNTS), encoding="utf-8")


# --------------------------------------------------------------------------
# 3. The driver half — runs pytest in a subprocess and reads the counts back.
# --------------------------------------------------------------------------


def measure(
    files: tuple[str, ...],
    watch: tuple[tuple[str, int], ...],
    tmp: Path,
    extra: tuple[str, ...] = (),
) -> dict[str, int]:
    """Run pytest over ``files`` counting executions of each ``watch`` line.

    A subprocess rather than a nested :func:`pytest.main` so this is callable
    from inside a pytest run — which is what the negative controls do.
    """
    tgt = tmp / "targets.json"
    counts = tmp / "counts.json"
    tgt.write_text(json.dumps([[str(p), l] for p, l in watch]), encoding="utf-8")
    env = {**os.environ, TARGETS_ENV: str(tgt), COUNTS_ENV: str(counts)}
    subprocess.run(
        [sys.executable, "-m", "pytest", "-p", "eval.mppi_sandbox.loop_reach",
         "-q", "-p", "no:cacheprovider", *extra, *files],
        cwd=REPO_ROOT, env=env, capture_output=True, text=True, timeout=900,
    )
    if not counts.exists():
        return {}
    return json.loads(counts.read_text(encoding="utf-8"))


def grade(target: Target, counts: dict[str, int]) -> tuple[str, int]:
    """``(grade, iterations)`` for one target given a counts mapping."""
    resolved = str(target.path.resolve())
    hits = counts.get(f"{resolved}:{target.assert_line}", 0)
    loop = counts.get(f"{resolved}:{target.loop_line}", 0)
    if loop == 0 and hits == 0:
        return NOT_RUN, 0
    if hits == 0:
        return EMPTY, 0
    if hits == 1:
        return SINGLETON, 1
    return SAMPLED, hits


def unevaluated_grades() -> frozenset[str]:
    """Grades meaning the claim saw no element — **derived from** :func:`grade`.

    This was a typed literal (``frozenset({NOT_RUN, EMPTY})``) when D-103 shipped
    it, and `guard_reflexivity.unwatched_exemptions` went five-to-six within one
    test run of it being written: a ``TYPED`` allow-list with no module-level
    enumerator is D-047's state, and D-073 / D-080 / D-101 each paid for the same
    shape.  D-077's repair is the cheap one and it applies here — a narrowing
    computed by *calling* something is watched by whatever watches that
    something — because "saw no element" is not an opinion about which two names
    belong in a set.  It is exactly what :func:`grade` returns when the hit count
    is zero, so the set is recomputed from the grader rather than copied out of it
    and left to drift.
    """
    probe = Target("probe.py::probe", "PROBE", 2, 1, "assert x")
    resolved = str(probe.path.resolve())
    no_element = (
        {},                                        # nothing ran at all
        {f"{resolved}:{probe.loop_line}": 3},      # loop ran, body never did
    )
    return frozenset(grade(probe, counts)[0] for counts in no_element)


#: Grades that mean the claim was never evaluated on a single element.
#:
#: Kept as a name for readers, but **not** what :func:`report` narrows by — it
#: calls :func:`unevaluated_grades` at the site instead, and that is deliberate.
#: ``_provenance`` asks its question *at the call site* (Q-067 / D-052 option b),
#: so a module-level set constant reads ``TYPED`` no matter how it was computed:
#: with ``if r[1] in UNEVALUATED`` the exemption is a hand-typed registry as far
#: as the screen can tell, which is how D-103 shipped an unwatched allow-list one
#: test run after writing it.  Naming the derivation at the site reads ``DERIVED``
#: and the guard is watched by whatever watches :func:`grade`.
#:
#: The other spelling was measured too, as D-073 did rather than argued: bare
#: ``UNEVALUATED = unevaluated_grades()`` makes ``_is_set_valued`` say no, and
#: :func:`report` **leaves the pool entirely** — the pin reads 77-unchanged, so
#: deriving the constant would have deleted the guard from the census rather than
#: paying for it, and D-103's cost would have read as nil.
UNEVALUATED: frozenset[str] = frozenset(unevaluated_grades())


def run(
    tmp: Path | None = None,
    paths: tuple[Path, ...] | None = None,
    extra: tuple[str, ...] = (),
) -> tuple[tuple[Target, str, int], ...]:
    """Measure every target and grade it.  This is the reading."""
    import tempfile

    tg = targets(paths)
    files = tuple(sorted({str(t.path) for t in tg}))
    watch = tuple(
        (str(t.path.resolve()), line)
        for t in tg for line in (t.assert_line, t.loop_line)
    )
    if tmp is None:
        with tempfile.TemporaryDirectory() as d:
            counts = measure(files, watch, Path(d), extra)
    else:
        counts = measure(files, watch, tmp, extra)
    return tuple((t, *grade(t, counts)) for t in tg)


def census(rows: tuple[tuple[Target, str, int], ...]) -> dict[str, int]:
    out = {g: 0 for g in GRADES}
    for _, g, _n in rows:
        out[g] += 1
    return out


# --------------------------------------------------------------------------
# 4. The reading, recorded.
# --------------------------------------------------------------------------

#: What the measurement said on 2026-08-06, as ``test name -> (grade, n)``.
#:
#: **The answer is that there is nothing here.**  Every population claim in the
#: table is evaluated over 2–30 elements.  Not one is vacuous, and not one is a
#: population of one.  (The set grows as the corpus does — the row count is
#: whatever ``targets()`` finds today, which is what
#: ``test_recorded_reading_covers_exactly_todays_targets`` enforces; stating a
#: literal here is what made this sentence say "15" for three cycles after it
#: stopped being 15.)  The hazard that produced D-100 (a stale ``CARDINALITY``),
#: D-101 (an unsound ``SUBSET``) and D-102 (two claims no run reached) does
#: **not** extend to the loop-body population — the suspicion was reasonable and
#: the measurement refuses it.  Kept rather than deleted, per D-076/D-081: an
#: emptiness that was measured is a different object from one that was assumed,
#: and the next cycle that wonders about loop-body vacuity should find this
#: instead of re-deriving it.
#:
#: One caveat is load-bearing and is why ``grade`` reports ``NOT_RUN``
#: separately.  ``test_the_nominal_point_lies_inside_its_own_band`` is
#: ``slow``-marked, so the **fast** job never evaluates it; it reads ``NOT_RUN``
#: there and ``SAMPLED n=8`` under ``--slow``.  Recorded at its ``--slow``
#: value, because the ``slow`` job does select it (``-m slow``) — but that job
#: is the one carrying the D-033 dispatch drift, so "evaluated" here means
#: "evaluated by a job that is currently degraded", not "evaluated in CI green".
READING: dict[str, tuple[str, int]] = {
    # D-190.  The two constructors' agreement across every flag value, looped
    # over `(True, False, None)`.  `n=21` is the tuple-comparison arity the
    # sampler sees, not the flag count: the population being claimed is the
    # three-valued flag domain, and it is the *whole* domain rather than a
    # sample of one — `ess_in_band` has no fourth value.  The row exists
    # because the copy of this rule that D-190 deleted had agreed on two of
    # those three values, so "all flags" is exactly the claim that needed
    # pinning.
    "test_from_sweep_delegates_its_flag_tail_to_from_flag": (SAMPLED, 21),
    # D-104.  The position table's equality check, which is a loop over
    # `sa.located()` — 8 elements, the same eight the census pins.  Added here
    # rather than left to drift: a population claim whose row is missing is
    # indistinguishable from one nobody wrote.
    "test_the_position_table_is_derived_not_a_second_transcription": (SAMPLED, 8),
    # D-169.  The head_on `w_geom` ladder's admissibility, 5 rungs — the claim
    # that the spread of verdicts across the ladder cannot be waved off as bad
    # runs.  A population claim, so it owes a row like any other.
    "test_the_ladder_rungs_are_not_refusable_on_the_walks_grounds": (SAMPLED, 5),
    # D-171.  The circularity screen, looped over both walked rungs — 2
    # elements, which is the *whole* population of rungs carrying a recorded
    # `w_geom` ladder, not a sample of a wider one.  Exactly at the `n >= 2`
    # floor, and that is the honest width: a screen shown on one rung would be
    # D-101's grammar, and there is no third ladder on disk to widen it with.
    "test_gain_matching_is_circular_on_both_walked_rungs": (SAMPLED, 2),
    # D-173.  The structural rung's pairing claim, looped over the two recorded
    # arms — 2 elements, and again the *whole* population rather than a sample:
    # `versus_frozen` pairs the walk against exactly `stock_mppi` and
    # `risk_mppi`, so there is no third arm the loop could have widened to.
    # At the `n >= 2` floor for the same honest reason D-171's row is.
    "test_the_walk_pairs_with_the_recorded_arms_by_seed": (SAMPLED, 2),
    # D-174.  Q-124's screen, two rows.  The first loops over the ladder's
    # **refused** rungs to check each sits inside the admissible share span —
    # 2 elements, which is every refusal the 6-rung ladder has, not a sample.
    # It is the width that makes the row worth reading: this claim is the one
    # piece of the cycle's evidence that survives `SCREEN_UNDERPOWERED`, and a
    # reader owes it the knowledge that it rests on two refusals.
    "test_ladder_admissible_set_spans_the_refused_ones": (SAMPLED, 2),
    # D-174.  The second loops over all 6 ladder rungs, re-deriving each share
    # against the 16-seed truncated arms.  The whole ladder, so the pairing
    # claim is exactly as wide as the table it defends.
    "test_ladder_shares_are_paired_on_the_truncated_arms": (SAMPLED, 6),
    "test_excluded_surfaces_are_declared_and_load_bearing": (SAMPLED, 7),
    "test_instrument_tagged_citations_state_that_arm_s_reading": (SAMPLED, 30),
    "test_the_screen_undercounts_the_scalar_across_the_matrix": (SAMPLED, 24),
    "test_the_nominal_point_lies_inside_its_own_band": (SAMPLED, 8),  # --slow
    "test_monotone_approach_reports_no_interior_hit": (SAMPLED, 8),
    "test_the_working_guard_names_its_own_offence": (SAMPLED, 5),
    "test_suppressing_the_exemption_reveals_the_offence": (SAMPLED, 5),
    "test_unwitnessed_ignores_non_candidates": (SAMPLED, 2),
    # D-107.  The affordability claim, looped over `POST_RECEIPT_WRITES` — 4
    # elements, the whole population, so the loop is exactly as wide as the
    # thing it quantifies over.  Non-vacuous, and worth having measured rather
    # than assumed: this is the test that replaced a **cost estimate nobody had
    # measured**, and shipping it vacuous would have reproduced the defect in
    # the repair.
    "test_the_reprobe_is_affordable_where_the_full_probe_was_not": (SAMPLED, 4),
    "test_recorded_windows_are_rungs_of_the_recorded_ladder": (SAMPLED, 16),
    "test_every_cell_measured_at_least_the_default_ladder": (SAMPLED, 16),
    "test_site_takes_the_strongest_class_it_reaches": (SAMPLED, 5),
    "test_every_cell_shares_the_parents_robot_lanes_and_acceptance": (SAMPLED, 4),
    "test_ratios_do_not_collide_at_all": (SAMPLED, 6),
    "test_registered_probes_are_probeable_by_execution": (SAMPLED, 4),
    "test_record_carries_every_grader_field": (SAMPLED, 3),
    # D-158.  The margin sweep's two population claims, and they sit at opposite
    # ends of this table's width.  `test_band_ceiling_is_one_rung` loops over
    # all 32 margins that make *any* rung two-sided — the widest row here — and
    # asserts each covers exactly one rung, which is the whole "arm coverage is
    # capped at 1/4" claim; a loop that reached fewer margins would leave the
    # cap witnessed only where it was convenient.  The overlap test is `n = 2`
    # for the same reason D-135's rows are: the population *is* the two rungs
    # that admit no two-sided margin, so a wider loop would be a wider claim.
    "test_band_ceiling_is_one_rung": (SAMPLED, 32),
    "test_the_two_censored_rungs_are_the_ones_whose_arms_barely_overlap": (
        SAMPLED, 2),
    # D-184.  The seed-count claim's derivation: `CENSUS_LADDER_SEEDS = 16` is
    # read off the two recorded `w_geom` ladders rather than re-typed (D-047),
    # which makes it a population claim over every rung in both ladders — 12
    # elements, the whole population, not a sample.  The width matters here for
    # a specific reason: the row is what stops the derivation from passing on a
    # ladder that happens to be empty, and an empty ladder is exactly how "the
    # census grades at 16" would silently become a claim nobody measured.
    "test_ladder_seed_count_is_derived_not_retyped": (SAMPLED, 12),
    # D-135.  The head_on re-keying claims, each looped over the cell's two
    # arms.  `n = 2` is the narrowest row in this table and is the honest
    # width: the claim *is* about both arms of one cell, so a wider loop would
    # be a wider claim and not a better-supported one.  Recorded rather than
    # exempted, because "n = 2 because the population is 2" and "n = 2 because
    # the loop stopped early" are the two states this table exists to separate.
    "test_headon_w100_window_held_on_both_arms": (SAMPLED, 2),
    "test_d132_operating_point_is_admissible_for_both_arms": (SAMPLED, 2),
    "test_headon_window_held_exactly_with_nothing_to_spare": (SAMPLED, 2),
    # D-136.  The confound claim, looped over the two axes a re-measured cell
    # is keyed by.  `n = 2` is the population: `contrasts` accepts exactly
    # `SCENE` and `WEIGHT` and refuses anything else by name, so a third
    # element here would mean the factor set had grown and this row had not.
    "test_two_cells_differing_in_both_axes_isolate_neither": (SAMPLED, 2),
    # D-136, the other two.  `n = 4` is the only row in this table whose width
    # is a *product* — two arms x the two weights head_on has been measured at
    # — and it is the row that says so: the claim is that the window held at
    # both weights on both arms, so a loop of 2 would silently be the
    # one-weight claim wearing the two-weight claim's name.  The w150 rung row
    # is 2 for the same reason its D-135 neighbours are: one cell, both arms.
    "test_headon_holds_at_both_measured_weights": (SAMPLED, 4),
    "test_d132_w150_rung_was_walked_at_an_admissible_temperature": (SAMPLED, 2),
    # D-148.  The published band's arm-naming claim, looped over the rebuilt
    # walk's rungs.  `n = 8` is the whole ladder — every rung D-133 visited,
    # refused ones included — and that is the right width: certification
    # couples on the arm *name*, so a rung whose arms were renamed would grade
    # `NO_CELL` and read as calibrated-adjacent while testing nothing. A loop
    # narrowed to the 4 scorable rungs would leave the other 4 unchecked and
    # still print as a claim about the band.
    "test_arms_are_the_names_the_calibration_tables_key_on": (SAMPLED, 8),
    # D-160.  The convoy walk's censoring claim, looped over the two seed
    # blocks.  `n = 2` is the whole population — a `Reproduction` is exactly a
    # reference and a replication — and the loop is the point: both arms sit at
    # the floor in *each* block, which is a stronger statement than the pooled
    # one and the only version that rules out the two blocks censoring
    # different arms, the shape `w = 250` turned out to have (D-157).
    "test_both_arms_sit_at_the_floor_in_both_blocks": (SAMPLED, 2),
    # D-185.  The two seed counts a rung carries, looped over both walked
    # rungs — the whole population of rungs with a recorded `w_geom` ladder,
    # not a sample of a wider one, so `n = 2` is the honest width and not a
    # thin one.  Same population as the row above it, and for the same reason.
    "test_the_two_seed_counts_are_derived_from_the_rung_not_retyped": (SAMPLED, 2),
    # D-185.  The agreement between the derived per-rung reading and D-184's
    # two module constants.  A population claim about `seed_counts`, and the
    # row that makes the swap checkable: if a rung is ever walked at another
    # ensemble size the derived side moves, this loop sees it, and the
    # constants do not.
    "test_the_census_reading_matches_the_constant_pair_it_replaces": (SAMPLED, 6),
}

#: Tests whose row in :data:`READING` was taken under ``--slow`` rather than in
#: the fast job.  Named so the caveat above is machine-checkable, not prose.
SLOW_ONLY: frozenset[str] = frozenset({
    "test_the_nominal_point_lies_inside_its_own_band",
})


def report() -> str:
    rows = run()
    counts = census(rows)
    unevaluated = [r for r in rows if r[1] in unevaluated_grades()]
    lines = [
        "loop_reach — how many elements did each population claim see?",
        "",
        f"  population-claim loop assertions: {len(rows)}",
        f"  never evaluated on any element:   {len(unevaluated)}",
        "  by grade: " + ", ".join(f"{k}={v}" for k, v in counts.items()),
        "",
    ]
    for t, g, n in sorted(rows, key=lambda r: (GRADES.index(r[1]), r[0].test_id)):
        lines.append(
            f"  {g:<10} n={n:<5} {t.kind:<13} "
            f"{t.test_id.split('::')[-1]}:{t.assert_line}"
        )
        lines.append(f"      {t.text[:100]}")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if argv and argv[0] != "report":
        print("usage: python3 -m eval.mppi_sandbox.loop_reach report", file=sys.stderr)
        return 2
    print(report())
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())

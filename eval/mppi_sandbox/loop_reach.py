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
    # D-317.  The identity that licenses calling `membership_dethresholded_in_k`
    # a de-thresholding *of* the membership count — `#{margin >= 0}` recomputed
    # from the margins against the count the column reading reports, walked over
    # both measured ensembles.  The row is owed for the same reason D-301's is:
    # the claim is a **negative** one ("the identity never breaks"), and a
    # negative over a loop nobody registered is indistinguishable from a loop
    # that never ran — which for this particular claim would silently void every
    # count-vs-continuum comparison the function makes.
    # `n=2` is exhaustive over the ensembles walked at this cell (`n=16` and
    # `n=32`), not a sample of a wider set.  Measured with the D-305 scoping
    # (`run(paths=...)` over the one test file the same cycle wrote, ~5 s
    # against the ~90 s full-corpus pass) — third time that scoping has paid.
    "test_the_dethresholded_statistic_is_the_one_the_count_thresholds": (SAMPLED, 2),
    # D-319.  D-317's censoring caveat carried to the two functions that
    # actually publish the count.  Both rows are owed for the reason the row
    # above is: the claims are **negatives** walked over a loop — "all three
    # functions agree on which columns are blind", "every reported bound is an
    # edge of the censored region" — and a negative over an unregistered loop
    # reads identically to a loop that never ran.  Here that would be worse than
    # usual: the whole deliverable is a caveat, and a caveat that silently
    # covers zero columns is the failure it exists to prevent.
    # `n=2` is exhaustive over the ensembles walked at this cell (`n=16` and
    # `n=32`), not a sample.  `n=3` on the bracket row counts the run-bound
    # sides it reaches on top of the two grids.  Measured with the D-305
    # scoping (`run(paths=...)` over the one test file this cycle wrote) —
    # fourth time that scoping has paid, and this time `census_preempt` named
    # the two unrecorded rows in 2 s, before the suite rather than after it.
    "test_the_saturation_caveat_reaches_the_functions_that_publish_the_count":
        (SAMPLED, 2),
    "test_the_bracketed_run_is_the_censored_region": (SAMPLED, 3),
    # D-313.  D-312's two monotonicity claims about the extremum axis, each
    # walked over a three-element ladder of nested sets.  They are recorded
    # together because they are deliberately opposite-signed — one asserts a
    # span cannot shrink under extension, the other that a min-gap threshold
    # cannot grow under it — and a pair of loops that would both go vacuous the
    # same way is exactly what a single recorded row would hide.
    # `n=3` is a *sample*, not exhaustive: the ladder is three sets chosen to
    # bracket the property, and any longer one would do.  Measured with the
    # D-305 scoping (`measure` over the one new test file, ~5 s against the
    # ~90 s full-corpus pass), which is the second time that scoping has paid
    # for itself and the first time on a file the same cycle wrote.
    "test_span_is_monotone_non_decreasing_under_extension": (SAMPLED, 3),
    "test_min_gap_threshold_is_monotone_the_other_way": (SAMPLED, 3),
    # D-305.  The two ensemble sizes (16, 32) at the matched three-column grid,
    # each checked for `NOT_APPLICABLE` separability — D-304's (c) leg, which is
    # what makes "the grid cannot express the decomposition at *either* size" a
    # claim about a population rather than about the one size that was run.
    # `n=2` is exhaustive: the control and the re-read are the only two ensemble
    # sizes the matched grid has columns for.  Measured with `run(paths=...)`
    # scoped to the ladder test file — and that scoping is now *checked*, not
    # assumed: the same run reproduced all eight of this file's already-recorded
    # rows at their recorded grades and counts (D-305), so a new claim costs one
    # file's measurement rather than the full-corpus pass STATE budgeted 12 min
    # for.
    "test_the_matched_grid_cannot_re_read_the_span_consumers_only_the_boundary": (SAMPLED, 2),
    # D-301.  The `lam` window's two exit legs, each checked for zero *genuine*
    # (in-band) jackknife flips — the claim that D-300's `UNDECIDED` is
    # structure rather than 16-seed noise.  `n=2` is measured with
    # `run(paths=...)` scoped to the ladder test file, not typed from the leg
    # count (D-079), and it is the whole population: a window has exactly two
    # exits, so this is exhaustive rather than a sample.  The row is owed
    # precisely because the claim is a negative one — "nothing flipped" over a
    # loop nobody registered is indistinguishable from a loop that never ran.
    "test_lam_window_undecided_is_durable_not_a_sample_size_artifact": (SAMPLED, 2),
    # D-293.  The three `K = 128` temperature columns, each checked for the
    # census seed count, the shared `K`, and `reached_goal` — membership
    # readings taken on crashed runs would be measurements of nothing.  `n=3`
    # is every column walked at `K = 128`, so the claim is exhaustive over the
    # grid it names rather than a sample of a wider one.
    "test_every_k128_run_reached_goal": (SAMPLED, 3),
    # D-296.  The two bisection columns (`K = 80`, `K = 192`) walked to halve
    # D-294's open endpoint intervals, checked for the same three properties
    # as the `K = 128` claim above.  `n=2` is measured with `run(paths=...)`
    # scoped to the ladder test file, not typed from the column count (D-079).
    "test_every_bisection_run_reached_goal": (SAMPLED, 2),
    # D-290.  `unanimity_bracket`'s five `w = 5` temperature columns, checked
    # for the shared population (16 seeds) and the shared `K` (256) that make
    # a cross-temperature comparison legal at all.  `n=5` is every column the
    # branch has walked — a closed domain, so the claim is exhaustive over the
    # thing it names rather than a sample of a wider set.
    # 5 -> 7: D-291 walked `lam = 1.15` and `1.25` into `CENSUS_COLUMN_ROWS`.
    "test_the_new_columns_are_the_census_population_at_the_shared_rung": (SAMPLED, 7),
    # D-291: the three columns above the unanimous run, each asserted to miss
    # at the ceiling rather than the floor.
    "test_membership_does_not_recover_above_the_failing_neighbour": (SAMPLED, 3),
    # D-288.  `lam = 1.2`'s rise attribution walks each seed at *both*
    # interior rungs — the D-019 precondition that lets the two rungs be
    # compared at one seed count.  `n=3` is the whole walked ensemble
    # (seeds 0/1/2), a closed domain, not a sample of a wider one.
    "test_every_seed_is_walked_at_both_rungs": (SAMPLED, 3),
    # D-265.  The linear inversion's overstatement, looped over the five
    # rungs of `arm_audibility.MEASURED_CURVE`.  `SUBSET`, not a
    # cardinality claim: the assertion is "never understates" at every
    # rung plus a floor on the worst factor, so it reads each of the five
    # but claims nothing about ladders it did not walk.
    "test_linear_inversion_overstates_and_by_how_much": (SAMPLED, 5),
    # D-224.  The 20-seed off-family walk's two preconditions, each looped over
    # the 2x2's four cells: completion (`20/20` per cell, so no reading was
    # bought by freezing) and the nested-prefix monotonicity of `min`.  `n=4`
    # is the cell count both walk over and it is the *whole* population — the
    # 2x2 has no fifth cell — so these are cardinality/subset claims over a
    # closed domain rather than samples of a larger one.
    "test_no_cell_bought_its_reading_by_freezing": (SAMPLED, 4),
    "test_the_minimum_can_only_fall_as_seeds_are_added": (SAMPLED, 4),
    # D-225.  The cafe re-read's two preconditions, the same shape one scene
    # over: completion (`6/6` per cell) and the re-derivability of the pasted
    # `WALK_CAFE_6` table against a live seed-0 walk.  `n=4` is again the whole
    # 2x2 rather than a sample — `W_RISK_ROWS x W_PED_COLS` has no fifth cell.
    # Both rows are the off-family pair above transposed onto
    # `cafe_obstacle_crossing_v0`, which is the point: the cafe reading that
    # survived pairing owes exactly the preconditions the retracted one owed.
    "test_no_cafe_cell_bought_its_reading_by_freezing": (SAMPLED, 4),
    "test_the_recorded_cafe_walk_is_re_derivable": (SAMPLED, 4),
    # D-234.  The cafe family read as a family: the top-row loop walks all
    # three scenes (`CAFE_FAMILY_WALKS`) and the lean-positive loop walks the
    # two that did *not* flip.  Both are exhaustive over their stated set, not
    # samples of a larger one — the family has three members and the unflipped
    # pair has two — so the claim each makes is the whole population it names.
    "test_the_top_row_is_what_actually_generalizes_across_the_family": (SAMPLED, 3),
    "test_the_two_unflipped_rows_lean_positive_rather_than_merely_noisy": (SAMPLED, 2),
    # D-235.  The n=12 widening of the two scenes D-234 left unresolved.  The
    # loop walks `cafe_family_steps_12()`, whose two members are the *whole*
    # widened set — `cafe_convoy_v0` and `cafe_head_on_v0` — so `n=2` is the
    # population and not a sample of the three-scene family above.  It sits at
    # the `n >= 2` floor for the same reason the row above it does: the third
    # family member flipped and was never widened, so there is no third scene on
    # disk to read.  Registered here because D-235 *retracted* the row directly
    # above (`..._lean_positive_rather_than_merely_noisy`, whose recorded
    # `(4, 2, 0)` is the six-seed prefix) — a retraction that added a loop and
    # left it unregistered would have been the exact drift this table exists to
    # catch.
    "test_the_top_row_survives_the_widening_and_gets_sharper": (SAMPLED, 2),
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
    # D-206.  The premise a pin inherits includes what its readers import, and
    # this is the loop that walks those readers — `n = 5` is the mediating set
    # the static layer named, checked as a subset rather than an equality
    # because a reader that stops mediating is a weaker event than one that
    # appears.  The row exists because the claim is about *which* modules
    # mediate, and a claim keyed on a set is exactly the shape that goes stale
    # silently when the set grows.
    "test_the_mediating_modules_are_the_ones_the_static_layer_named": (SAMPLED, 5),
    # D-206.  The same five, read from the other end: whether a premise held is
    # not settled by how the pin was generated.  Two assertion sites share the
    # row (the sampler sees `:343` and `:344`), which is the normal shape for a
    # claim checked in both directions inside one loop.
    "test_generation_does_not_determine_whether_the_premise_held": (SAMPLED, 5),
    # D-214.  The `PARTIAL` withdrawal's one-way property, looped over the four
    # local tokens (`shard`, `slice`, `census`, `subset`).  `n = 4` is the whole
    # token set rather than a sample: the claim is that *no* token turns an
    # uncorroborated count into a corroborated one, and a claim of that shape is
    # worth exactly the width it was checked at.  The row is owed because the
    # audit it guards grades published counts — a token added later without a
    # re-measurement would widen the withdrawal branch silently.
    "test_a_token_can_never_manufacture_a_corroboration": (SAMPLED, 4),
    # D-251.  The arrival-scope census's construction claim: truncating a stall
    # to the pre-arrival window can only shorten it, so `before <= whole` holds
    # on every scene.  `n=8` is the whole shipped scene set rather than a sample
    # — `scene_paths()` is the closed domain — which is why it is asserted per
    # scene rather than on the one scene that motivated it.  The row is owed
    # because a scene added later would widen the claim silently.
    "test_before_never_exceeds_whole_on_any_scene": (SAMPLED, 8),
    # D-257.  The premise the whole `cancelling_stability` reading rests on:
    # the EPISTEMIC channel is exactly binary, which is what makes the repel
    # arm's unit split a constant 1.0 and the "ratio" a reading of one arm.
    # `n=3` is a sample of radii rather than a closed domain — radius is
    # continuous — so the row is owed: a geometry that blurred the shadow
    # would falsify the premise without moving this loop's count.
    "test_the_epistemic_channel_is_exactly_binary": (SAMPLED, 3),
    # D-257.  The band's internal consistency (`lo <= mean <= hi`, every root
    # contained).  `n=7` is the shipped `DEFAULT_RADII`, but that tuple is a
    # chosen sweep and not a closed domain, so a radius appended later would
    # widen the claim silently — hence a row rather than a derivation.
    "test_band_brackets_its_own_samples": (SAMPLED, 7),
    # D-258.  `rollout_cloud`'s matched-K precondition: the K a stride yields
    # must equal the number of points that stride actually produces, or the
    # three supports are not being compared at matched K and the displacement
    # finding measures count as well as support.  `n=3` is a sample of strides
    # (3, 13, 31 — the ends and the middle of the ensemble) and not a closed
    # domain, so the row is owed: a stride whose arithmetic disagreed would
    # falsify the premise without moving this loop's count.
    "test_grid_k_matches_the_grid_it_describes": (SAMPLED, 3),
    # D-263.  The arm freeze's rename guard: every frozen arm's config keys must
    # be weight fields the critics actually declare, or the config sets nothing
    # and all four arms silently become the control.  `n=4` is the whole arm
    # table rather than a sample — `ARM_NAMES` is the closed domain — but the
    # row is owed anyway, because a fifth arm is exactly the kind of thing a
    # later cycle adds, and the failure this guards is silent by construction.
    "test_as_config_keys_are_the_critics_real_weight_fields": (SAMPLED, 4),
    # D-281.  Q-153's two seed counts: the miss list is asserted to be a
    # superset going from `n = 8` to `n = 16`, and each count's census is
    # re-read inside the loop.  `n=2` is the whole domain — there are exactly
    # two readings and D-019(b) forbids a third being pooled in — so this is a
    # closed-domain claim, not a sample.  The row is owed regardless: a cycle
    # that adds `n = 32` would extend the loop, and the guard that must not go
    # quiet is precisely "a seed that failed at the smaller `n` cannot pass at
    # the larger one".
    "test_the_miss_list_can_only_grow_and_here_it_did_not": (SAMPLED, 2),
    # D-283.  The repair rung's 16 rows, each asserted in band, audible and
    # reaching — the per-seed evidence under the `UNANIMOUS_WINDOW` verdict.
    # `n=16` is the whole population at that cell, but graded `SUBSET` rather
    # than a cardinality claim because the assertion is a conjunction over the
    # rows recorded, and `seed_verdict` is where the `16/16` count is made.
    # A cycle that walks `lam = 1.2` adds a table, not rows to this one.
    "test_the_repair_rung_rows_clear_the_floor_the_operating_point_missed":
        (SAMPLED, 16),
    # D-287.  The three temperatures of `MEASURED_ALL_LAMS_UNIFORM`, each
    # asserted to walk the same four rungs across D-027's ceiling bracket.
    # `n=3` is the whole population and the claim is a set *equality* per
    # temperature — which is the point, since `resolution_uniform` is exactly
    # "the interior rungs are the same set at every `lam`".  A cycle that walks
    # a fourth temperature extends this loop and must re-take the reading.
    "test_the_spacing_is_now_uniform_across_all_three_temperatures":
        (SAMPLED, 3),
    # D-295.  The `SUBSET` claim that every `POST_RECEIPT_WRITES` candidate is
    # mediated by `inert_surface` — the fixed point that makes the five stale
    # pins self-blocking rather than merely expensive.  Taken scoped to the one
    # file (`run(paths=...)`), which is why it exists at all: the full corpus
    # reading did not finish inside the cycle budget, and a recorded `n` that
    # was predicted rather than measured is the shape D-079 calls decoration.
    # `n=10` and not the 5 candidates a reader expects: the grader counts
    # *assert-line hits*, and the tracer evaluates the file twice.  Recorded as
    # measured — a cycle that "corrects" this to 5 from the candidate count has
    # substituted arithmetic for the reading.
    "test_the_machinery_mediates_every_candidate": (SAMPLED, 10),
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

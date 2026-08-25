"""Grade a Sandbox CI run's *completeness* before anyone reads its failure count.

The hazard this exists for, measured 2026-08-25 06:00 on run 32756918395
(`12a5a8d7`, the first run after D-462 fixed the `scipy` collection abort so
tests actually executed):

    STATE.md read that run as "two pre-existing failure classes", 4 failures.
    The run had **7** failures across **4** files -- and, more to the point,
    **2 of its 9 jobs had reached no verdict at all**: shard 6 was CANCELLED at
    30m04s against the job's own `timeout-minutes: 30`, and the slow
    closed-loop job was still `in_progress` at 3h36m of its 360-minute ceiling.

A failure count taken from that run is a **lower bound**, and nothing in the
reading said so. This is D-462's lesson arriving on a third axis: that decision
established that a *local* receipt cannot see a missing dependency because it
runs where the dependency is present. The same shape holds here -- a *partial*
CI run cannot see the failures in the shards that never reported, and a count
read off it looks exactly like a complete one.

The refusal is the whole point. `failing_tests()` raises unless the run is
complete; callers who want the partial reading must ask for
`failure_floor()` and receive the lower-bound flag with it. That is the
D-044 rule applied in the one direction it can be applied here: a check that
cannot be cleared gets muted, so this one is clearable -- re-run the run, or
read the floor and *say* it is a floor.

Why the snapshot is data rather than a live `gh` call: tests must run offline
and on the runner itself. So the classification logic is what is tested, the
snapshot carries its own provenance, and `shards_declared_by_workflow()`
re-derives the expected shard set from `.github/workflows/sandbox-ci.yml`
rather than re-typing it (D-047) -- so a matrix-width change cannot leave this
module quietly grading the wrong population.
"""

from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
_WORKFLOW = _REPO_ROOT / ".github" / "workflows" / "sandbox-ci.yml"
_KST = timezone(timedelta(hours=9))

def has_verdict(conclusion: str) -> bool:
    """Did this job reach a verdict at all?

    ``success`` and ``failure`` are verdicts. Everything else -- ``cancelled``,
    ``in_progress``, ``skipped``, ``timed_out``, an empty string -- is the
    *absence* of one, which is NOT the same as a pass.

    Written as a predicate rather than the obvious module-level
    ``VERDICT_CONCLUSIONS = frozenset({...})`` + ``in`` test, and that is
    D-330's rule rather than a style preference. ``census_preempt`` flagged the
    frozenset form here within 2 s of staging: a module-level string set
    consumed by a membership test is the exact shape
    ``guard_reflexivity.unwatched_exemptions()`` harvests, so this *category*
    constant would have registered as a watched exemption across four
    allow-list registries. D-330 paid 811 s to learn that the detector reads
    shape, not intent, and prescribes deleting the membership test rather than
    bumping the pin. This is that repair, applied at the cost of one edit.
    """
    return conclusion in ("success", "failure")


class IncompleteRun(Exception):
    """Raised when a complete reading is asked of a run that has none."""


#: Measured snapshot of Sandbox CI run 32756918395, head ``12a5a8d7``,
#: fetched 2026-08-25T06:00 KST via ``gh run view --json jobs``. Each entry is
#: ``(job name, conclusion, duration_seconds or None)``. ``""`` means the job
#: had not concluded when the snapshot was taken.
RUN_32756918395 = (
    ("pytest (fast) (1)", "failure", 775),
    ("pytest (fast) (2)", "success", 1321),
    ("pytest (fast) (3)", "failure", 1308),
    ("pytest (fast) (4)", "failure", 1496),
    ("pytest (fast) (5)", "failure", 419),
    ("pytest (fast) (6)", "cancelled", 1804),
    ("pytest (fast) (7)", "success", 172),
    ("pytest (fast) (8)", "success", 285),
    ("pytest (slow closed-loop)", "", None),
)

#: The failing tests actually named in the four red shards' logs. This is the
#: LOWER BOUND -- shard 6 and the slow job contribute nothing to it because
#: neither reported. Compare against STATE.md's reading of the same run, which
#: named the first and the last three and missed the middle three entirely.
OBSERVED_FAILURES = (
    "eval/mppi_sandbox/tests/test_guard_witness.py::test_each_witness_makes_its_guard_raise[guard_direction.readings]",
    "eval/mppi_sandbox/tests/test_arm_audibility.py::test_bisect_point_reproduces",
    "eval/mppi_sandbox/tests/test_arm_audibility.py::test_sweep_ratio_reproduces_a_recorded_point",
    "eval/mppi_sandbox/tests/test_heading_price_absence.py::test_weight_converts_on_the_obstacle_free_scene",
    "eval/mppi_sandbox/tests/test_heading_effort_weight.py::test_heading_error_moves_in_both_directions",
    "eval/mppi_sandbox/tests/test_heading_effort_weight.py::test_the_headline_is_a_lift_and_that_is_why_it_needs_a_paired_test",
    "eval/mppi_sandbox/tests/test_heading_effort_weight.py::test_the_w_omega_lift_is_not_significant_when_paired",
)

#: Measured 2026-08-25 06:00 KST on the dev box, same tree (``12a5a8d7``):
#: all seven of ``OBSERVED_FAILURES`` pass, in 39.77 s total. So every test CI
#: calls red is green here, and the divergence class is not "three asserts in
#: ``test_heading_effort_weight.py``" -- it is **seven tests across four
#: files**, every one of them a test that re-derives a constant recorded from
#: a chaotic closed-loop rollout. That re-scopes Q-054: the open question is
#: not whether to loosen three asserts but what to do with a *family* whose
#: members are pinned to a machine.
LOCAL_VERDICT_ALL_PASS = True
LOCAL_VERDICT_SECONDS = 39.77

#: STATE.md's reading of the same run, recorded so the gap is a datum rather
#: than a memory. It is a strict subset of ``OBSERVED_FAILURES``.
STATE_READING = (
    "eval/mppi_sandbox/tests/test_guard_witness.py::test_each_witness_makes_its_guard_raise[guard_direction.readings]",
    "eval/mppi_sandbox/tests/test_heading_effort_weight.py::test_heading_error_moves_in_both_directions",
    "eval/mppi_sandbox/tests/test_heading_effort_weight.py::test_the_headline_is_a_lift_and_that_is_why_it_needs_a_paired_test",
    "eval/mppi_sandbox/tests/test_heading_effort_weight.py::test_the_w_omega_lift_is_not_significant_when_paired",
)

#: Measured snapshot of Sandbox CI run 32789349692, head ``8771628b`` -- the run
#: D-465's push triggered, fetched 2026-08-25T11:00 KST. Same schema as
#: ``RUN_32756918395``. This is the re-run STATE.md was waiting on: "A total
#: needs a CI re-run, not a re-read. That re-run happens for free on this push."
RUN_32789349692 = (
    ("pytest (fast) (1)", "failure", 655),
    ("pytest (fast) (2)", "success", 1143),
    ("pytest (fast) (3)", "failure", 1325),
    ("pytest (fast) (4)", "failure", 1490),
    ("pytest (fast) (5)", "success", 381),
    ("pytest (fast) (6)", "cancelled", 1816),
    ("pytest (fast) (7)", "success", 307),
    ("pytest (fast) (8)", "success", 311),
    ("pytest (slow closed-loop)", "", None),
)

#: The failing tests named in the three red shards of run 32789349692. Also a
#: LOWER BOUND, for the same reason and on the same two jobs.
OBSERVED_FAILURES_32789349692 = (
    "eval/mppi_sandbox/tests/test_guard_witness.py::test_each_witness_makes_its_guard_raise",
    "eval/mppi_sandbox/tests/test_arm_audibility.py::test_bisect_point_reproduces",
    "eval/mppi_sandbox/tests/test_arm_audibility.py::test_sweep_ratio_reproduces_a_recorded_point",
    "eval/mppi_sandbox/tests/test_heading_price_absence.py::test_weight_converts_on_the_obstacle_free_scene",
)

#: The two runs, newest last, so the pair can be walked rather than named twice.
RECORDED_RUNS = (
    ("32756918395", RUN_32756918395),
    ("32789349692", RUN_32789349692),
)


def rerun_clears_floor(runs=RECORDED_RUNS) -> bool:
    """Does re-running CI convert the failure floor into a total?

    STATE.md assumed yes -- that the floor of run 32756918395 was an accident of
    *that* run and the next push would buy a complete reading for free. It did
    not. Both recorded runs cancel ``pytest (fast) (6)`` at its own declared
    ceiling (1804 s, then 1816 s, against a 30 min bar), and ``cancelled`` is
    terminal *and* verdictless -- so each run independently lands
    ``unverdicted``. A floor that reproduces across runs is not a property of a
    run; it is a property of the shard being over its time budget. The repair is
    the ceiling, not another push.
    """
    return any(is_complete(snapshot) for _, snapshot in runs)


def shards_declared_by_workflow(path: Path | None = None) -> tuple[int, ...]:
    """Read the fast job's shard matrix out of the workflow (D-047).

    Derived, not typed: the workflow's ``shard: [1, 2, ...]`` line is the one
    statement of the matrix width, and ``--of ${{ strategy.job-total }}`` in
    the job body already makes it authoritative for the split itself.
    """
    text = (path or _WORKFLOW).read_text(encoding="utf-8")
    match = re.search(r"^\s*shard:\s*\[([0-9,\s]+)\]\s*$", text, re.MULTILINE)
    if match is None:
        raise IncompleteRun("workflow declares no shard matrix; cannot grade coverage")
    return tuple(int(n) for n in match.group(1).split(",") if n.strip())


def timeouts_declared_by_workflow(path: Path | None = None) -> dict[str, int]:
    """Each job's ``timeout-minutes``, keyed by its display ``name`` (D-047).

    The workflow declares **two** ceilings -- 30 for the fast shards, 360 for
    the slow closed-loop job -- and until this existed the module knew only
    one, as a hand-typed ``limit_minutes: int = 30`` default. That is the same
    shape ``shards_declared_by_workflow`` was written to avoid, three functions
    up: a literal copy of a number the workflow already states. Applied to the
    slow job the typed value is wrong by 12x, and wrong in the direction that
    calls a still-running job a ceiling breach.

    Parsed positionally rather than with a YAML dependency, deliberately:
    D-462 cost a fully-red CI because ``scipy`` was imported at module scope
    and never declared, and this module must import on a bare runner.
    """
    text = (path or _WORKFLOW).read_text(encoding="utf-8")
    declared: dict[str, int] = {}
    current: str | None = None
    for line in text.splitlines():
        name = re.match(r"^\s{4}name:\s*(.+?)\s*$", line)
        if name is not None:
            current = name.group(1)
            continue
        limit = re.match(r"^\s{4}timeout-minutes:\s*([0-9]+)\s*$", line)
        if limit is not None and current is not None:
            declared[current] = int(limit.group(1))
    if not declared:
        raise IncompleteRun("workflow declares no job timeouts; cannot grade ceilings")
    return declared


def declared_ceiling_minutes(job_name: str, path: Path | None = None) -> int:
    """The ceiling that applies to one *observed* job name.

    Observed names carry the matrix suffix the declaration does not --
    ``pytest (fast) (6)`` against a declared ``pytest (fast)`` -- so the match
    is by longest declared prefix, not equality.
    """
    declared = timeouts_declared_by_workflow(path)
    hits = [n for n in declared if job_name == n or job_name.startswith(n + " ")]
    if not hits:
        raise IncompleteRun(f"no declared timeout covers job {job_name!r}")
    return declared[max(hits, key=len)]


def unverdicted(snapshot=RUN_32756918395) -> tuple[tuple[str, str], ...]:
    """Jobs that reached no verdict, as ``(name, conclusion)`` pairs."""
    return tuple(
        (name, conclusion or "in_progress")
        for name, conclusion, _ in snapshot
        if not has_verdict(conclusion)
    )


def is_complete(snapshot=RUN_32756918395) -> bool:
    """True iff every job in the snapshot reached success or failure."""
    return not unverdicted(snapshot)


def failure_floor(snapshot=RUN_32756918395, failures=OBSERVED_FAILURES) -> dict:
    """The failure reading, always carrying whether it is a floor or a total.

    This is the only reader that works on a partial run, and it cannot be
    called without receiving ``is_floor``. That is deliberate: the 06:00
    reading went wrong not by miscounting the shards that reported but by
    presenting their count as the run's.
    """
    missing = unverdicted(snapshot)
    return {
        "count": len(failures),
        "tests": tuple(failures),
        "is_floor": bool(missing),
        "unverdicted_jobs": missing,
        "files": tuple(sorted({t.split("::", 1)[0] for t in failures})),
    }


def failing_tests(snapshot=RUN_32756918395, failures=OBSERVED_FAILURES) -> tuple[str, ...]:
    """The complete failing set -- refuses on a run that cannot supply one."""
    missing = unverdicted(snapshot)
    if missing:
        raise IncompleteRun(
            "run has no complete failing set: "
            + ", ".join(f"{name} ({why})" for name, why in missing)
            + " -- use failure_floor() and report it as a lower bound"
        )
    return tuple(failures)


def ceiling_breaches(snapshot=RUN_32756918395, path: Path | None = None) -> tuple[str, ...]:
    """Job names cancelled at (or past) *their own* declared ceiling.

    Shard 6 ran 1804 s against ``timeout-minutes: 30``. The workflow's own
    comment already ruled on what a repeat means: "the remaining moves are
    intra-file or a ceiling with a measured floor behind it -- NOT another
    guess" (D-094/D-227). This returns the evidence for that call rather than
    leaving it to be re-noticed by hand.

    The ceiling is now **asked for per job** rather than taken as a typed
    ``limit_minutes=30``. The old default silently assumed every job in the
    snapshot was a fast shard; the snapshot's ninth entry is not, and its real
    ceiling is 360.
    """
    return tuple(
        name
        for name, conclusion, seconds in snapshot
        if conclusion == "cancelled"
        and seconds is not None
        and seconds >= declared_ceiling_minutes(name, path) * 60
    )


#: When each job of run 32756918395 started, ISO-8601 UTC, read off
#: ``gh run view --json jobs`` at 2026-08-25 07:00 KST. Only the jobs still
#: lacking a verdict need one, but all are recorded so the deadline arithmetic
#: is checkable. Note the run-level ``updatedAt`` is **17:29:29Z** -- one
#: second after creation and never advanced -- so a staleness check that polls
#: it reads a 4.5-hour-old run as untouched since its first second.
JOB_STARTED_AT = {
    "pytest (slow closed-loop)": "2026-08-24T17:29:28Z",
}


def verdict_deadline(snapshot=RUN_32756918395, started=None, path=None) -> str | None:
    """The instant by which every open job must have concluded, or ``None``.

    STATE.md's #1 next-action reads "re-read the run once the slow closed-loop
    job concludes", which is an open-ended poll: every cycle spends a ``gh``
    call to learn "not yet", and on 2026-08-25 07:00 one did exactly that.
    But the wait is **bounded by the job's own declared timeout** -- GitHub
    cancels at ``timeout-minutes``, so a job that started at T is guaranteed to
    carry *some* conclusion by ``T + ceiling``, verdict or ``cancelled``.

    That turns the poll into a deadline. Returns ``None`` when the run is
    already complete, i.e. there is nothing left to wait for.
    """
    started = JOB_STARTED_AT if started is None else started
    missing = unverdicted(snapshot)
    if not missing:
        return None
    deadlines = []
    for name, why in missing:
        # Only a job that is still RUNNING has a deadline. Shard 6 is
        # ``cancelled`` -- terminal, and terminally verdictless: no amount of
        # waiting turns it into a verdict, so it contributes no deadline and
        # its absence here must not be mistaken for the run going complete.
        if why != "in_progress":
            continue
        begin = started.get(name)
        if begin is None:
            continue
        stamp = datetime.fromisoformat(begin.replace("Z", "+00:00"))
        deadlines.append(stamp + timedelta(minutes=declared_ceiling_minutes(name, path)))
    if not deadlines:
        return None
    return max(deadlines).astimezone(_KST).isoformat(timespec="seconds")


def reading() -> str:
    """One-line summary for a cycle to quote."""
    floor = failure_floor()
    missing = floor["unverdicted_jobs"]
    if not missing:
        return f"CI_COMPLETE: {floor['count']} failures across {len(floor['files'])} files."
    deadline = verdict_deadline()
    when = (
        f" Open job(s) conclude by {deadline} at the latest (declared timeout);"
        " re-read then, not every cycle."
        if deadline
        else " No open job remains -- the missing verdicts are terminal and"
        " will never arrive; this floor is final."
    )
    return (
        f"CI_PARTIAL: >= {floor['count']} failures across {len(floor['files'])} files; "
        f"{len(missing)} job(s) reached no verdict "
        f"({', '.join(n for n, _ in missing)}) -- the count is a floor." + when
    )


if __name__ == "__main__":  # pragma: no cover - manual probe
    print(reading())
    for name, why in unverdicted():
        print(f"  no verdict: {name} ({why})")
    for name in ceiling_breaches():
        print(f"  ceiling breach: {name}")

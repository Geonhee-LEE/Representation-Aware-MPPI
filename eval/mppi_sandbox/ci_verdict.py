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
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
_WORKFLOW = _REPO_ROOT / ".github" / "workflows" / "sandbox-ci.yml"

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


def ceiling_breaches(snapshot=RUN_32756918395, limit_minutes: int = 30) -> tuple[str, ...]:
    """Fast-job names that were cancelled at (or past) their declared ceiling.

    Shard 6 ran 1804 s against ``timeout-minutes: 30``. The workflow's own
    comment already ruled on what a repeat means: "the remaining moves are
    intra-file or a ceiling with a measured floor behind it -- NOT another
    guess" (D-094/D-227). This returns the evidence for that call rather than
    leaving it to be re-noticed by hand.
    """
    return tuple(
        name
        for name, conclusion, seconds in snapshot
        if conclusion == "cancelled"
        and seconds is not None
        and seconds >= limit_minutes * 60
    )


def reading() -> str:
    """One-line summary for a cycle to quote."""
    floor = failure_floor()
    missing = floor["unverdicted_jobs"]
    if not missing:
        return f"CI_COMPLETE: {floor['count']} failures across {len(floor['files'])} files."
    return (
        f"CI_PARTIAL: >= {floor['count']} failures across {len(floor['files'])} files; "
        f"{len(missing)} job(s) reached no verdict "
        f"({', '.join(n for n, _ in missing)}) -- the count is a floor."
    )


if __name__ == "__main__":  # pragma: no cover - manual probe
    print(reading())
    for name, why in unverdicted():
        print(f"  no verdict: {name} ({why})")
    for name in ceiling_breaches():
        print(f"  ceiling breach: {name}")

"""Read the CI authority **per job**, because the run does not know yet.

Carried on STATE's next-actionable list for four cycles, and each carry made the
case sharper.  What finally forced it was a reading taken while writing it.

At 2026-08-05T08:00Z run ``30981826577`` (head ``70e2863``) reported::

    run-level:  status=in_progress   conclusion=null   updated_at=06:34:39Z
    job  fast:  status=completed     conclusion=failure   completed_at=06:57:09Z
    job  slow:  status=in_progress   conclusion=null

The run says *no verdict yet*.  One of its two required jobs had failed
**sixty-three minutes earlier**.  Both records are accurate; only one of them
answers "is this branch red", and it is not the one every tool in this project
reads.  ``gh run list --json conclusion`` prints the empty one.

This is the fourth instance of the pattern :mod:`git_surface` tabulated, and it
runs in the opposite direction from the other three, which is why it survived
being named three times:

============================  ==========================  ====================
instrument                    silence was read as         verdict that fixes it
============================  ==========================  ====================
``push_preflight``            "didn't fail" = passed      ``VACUOUS``
``git_surface``               no refs = no commits        ``NO_REMOTE_BRANCHES``
``local_only_audit``          empty fold = nothing found  (the D-086 inversion)
**this module**               **not finished = not bad**  ``PENDING`` ≠ ``FAIL``
============================  ==========================  ====================

The first three turn absent evidence into a *false clean bill*.  This one hides a
verdict that **already exists** behind an aggregate that is merely late.  A
pending run is not evidence of health, and a run-level ``conclusion`` is not a
reading of the jobs — it is a summary that has not been written yet.  So the rule
is: **a failed job is a red branch the instant it completes**, regardless of what
its siblings are still doing.  :func:`read_run` ranks ``FAIL`` above ``PENDING``
for exactly this reason, and :func:`test_a_failed_job_outranks_a_pending_sibling`
pins the live record above as a fixture.

``cancelled`` is not ``failure`` — and not ``success`` either
-------------------------------------------------------------

D-084's finding, given a name here.  Between 2026-08-03T23:18Z and
2026-08-05T06:57Z **every** Sandbox CI run ended ``cancelled``: the jobs were
killed at their ``timeout-minutes`` ceiling, so no test verdict was ever
reached.  ``gh pr checks`` renders that as "fail", STATE.md read it as "green",
and both were guesses about a run that had not run.  :data:`UNRUN` is a verdict
of its own — *the question was not answered* — and it is neither pass nor fail.
Collapsing it into either direction is how twenty-seven consecutive pushes went
unexamined.

Why the ceiling needs metering, not just a bigger number
--------------------------------------------------------

D-084 raised the fast job 10 → 30 min and stopped, having read the streak as one
ceiling crossing.  Measured **per job** there were two, ~10 h apart: ``fast``
crossed 10 min at ``2be88f0a`` (08-03T23:18Z) and ``slow`` crossed 60 min at
``ed80d0bd`` (08-04T09:32Z).  Raising only ``fast`` left every run ``cancelled``
and the authority silent for another day, and it *looked* like a whole fix
because the run-level conclusion says ``cancelled`` either way.  D-085 then
raised ``slow`` 60 → 120.

:attr:`JobReading.headroom` is that diagnosis mechanised.  Each job is metered
against the ``timeout-minutes`` declared for it in the workflow, and the meter
reads in both tenses:

``at_ceiling``
    post-mortem — an ``UNRUN`` job that died *at* its cap, distinguished from
    one a human cancelled or that GitHub tore down when a sibling failed.  Both
    spell ``cancelled``; only the first means the cap is now the thing under
    test.

``approaching_ceiling``
    forward — a job **still running** at ≥98% of its cap, metered off elapsed
    time.  The first draft of this module had only the post-mortem, which would
    have reported D-085's breach exactly as late as the humans did.  A meter
    that speaks only after the kill is a description of the wreck.

The suite's cost is superlinear in instrument count — this file is one more
instrument — so the crossing recurs by construction, and the answer is a meter
rather than another hand-read streak.

Reading the record
------------------

Every function here takes **plain dicts** in the GitHub REST shape, so the tests
are hermetic and the live fixtures above are checked in verbatim.  :func:`fetch`
is the only thing that touches the network, and it is a thin ``gh api`` shell —
nothing in the ranking logic can be broken by an offline box.

Fast half: pure dict arithmetic plus one YAML parse.  No network, no simulation.
"""

from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

import yaml

from .tree_provenance import REPO_ROOT

#: The job completed and its steps succeeded.
PASS = "PASS"

#: The job completed and something in it failed.  A real verdict about the tree.
FAIL = "FAIL"

#: The job reached no verdict: ``cancelled``, ``timed_out``, ``skipped``,
#: ``stale``.  Not a pass and **not a fail** — the question went unanswered.
#: Distinct from :data:`PENDING` because this one is final: waiting will not
#: turn it into a verdict.
UNRUN = "UNRUN"

#: The job has not finished.  Says nothing about the tree yet, and in particular
#: is *not* evidence of health — see the module docstring.
PENDING = "PENDING"

#: The record could not be parsed into any of the above.  Fails closed: a caller
#: gating on green must treat this as not-green.
UNREADABLE = "UNREADABLE"

#: Run-level only: the run carries no jobs at all.  A run with zero jobs has
#: passed nothing, so it is never :data:`PASS`.
NO_JOBS = "NO_JOBS"

#: Precedence for folding job verdicts into a run verdict.  ``FAIL`` first is
#: the load-bearing claim of this module: a completed failure outranks a sibling
#: that is merely still running.
_PRECEDENCE = (FAIL, UNREADABLE, UNRUN, PENDING, PASS)

#: Terminal conclusions that mean "no verdict was reached".
_UNRUN_CONCLUSIONS = frozenset({"cancelled", "timed_out", "skipped", "stale"})

#: A job killed at its ceiling reads ``cancelled`` exactly like one a human
#: stopped.  Within this fraction of its declared cap, call it a ceiling breach.
CEILING_FRACTION = 0.98

#: Default workflow whose ``timeout-minutes`` declarations meter the jobs.
DEFAULT_WORKFLOW = Path(".github/workflows/sandbox-ci.yml")


@dataclass(frozen=True)
class JobReading:
    """One job's verdict, plus how close it ran to its declared ceiling."""

    name: str
    verdict: str
    conclusion: str | None = None
    status: str | None = None
    duration_s: float | None = None
    cap_s: float | None = None
    #: True when `duration_s` is *elapsed-so-far* on a job that has not finished,
    #: rather than a final runtime.  Kept explicit because the two are the same
    #: number in different tenses, and a caller quoting an in-flight elapsed time
    #: as a job's cost would be quoting a lower bound as a measurement.
    running: bool = False

    @property
    def headroom(self) -> float | None:
        """Fraction of the declared cap left unused, or ``None`` if unmetered.

        Negative is possible in principle (a job that overran its own cap before
        the runner noticed); it is reported rather than clamped, because a
        negative headroom is a fact about the ceiling and clamping it to zero
        would spell it the same as a job that landed exactly on the line.
        """
        if self.duration_s is None or not self.cap_s:
            return None
        return 1.0 - self.duration_s / self.cap_s

    @property
    def at_ceiling(self) -> bool:
        """Did this job die *at its cap* rather than for some other reason?

        The distinction D-084 needed and had to make by hand: ``cancelled``
        because the ceiling bit, versus ``cancelled`` because a human pressed
        the button or a sibling failed fast.  Only the first is a signal that
        the cap is now the thing under test.
        """
        h = self.headroom
        return (
            self.verdict == UNRUN
            and not self.running
            and h is not None
            and h <= 1.0 - CEILING_FRACTION
        )

    @property
    def approaching_ceiling(self) -> bool:
        """Is this job *still running* and already near its cap?

        :attr:`at_ceiling` is a post-mortem: it can only speak once the job has
        been killed, which is one full wasted run too late.  D-085's whole
        complaint was that the ceiling became the thing under test without
        anyone noticing for a day, and a meter that only reports after the kill
        would not have helped.  This is the same threshold read forward, off
        elapsed-so-far, so a job at 98% of its cap is visible while it is still
        alive.
        """
        h = self.headroom
        return self.running and h is not None and h <= 1.0 - CEILING_FRACTION

    def describe(self) -> str:
        parts = [f"{self.name}: {self.verdict}"]
        if self.conclusion:
            parts.append(f"({self.conclusion})")
        if self.duration_s is not None:
            parts.append(f"{self.duration_s / 60:.1f}m{'+' if self.running else ''}")
            if self.cap_s:
                parts.append(f"/ {self.cap_s / 60:.0f}m cap")
                parts.append(f"headroom {self.headroom:+.0%}")
        if self.at_ceiling:
            parts.append("⚠ AT CEILING")
        elif self.approaching_ceiling:
            parts.append("⚠ APPROACHING CEILING")
        return " ".join(parts)


@dataclass(frozen=True)
class RunReading:
    """A run's verdict, **derived from its jobs** and never read off the run."""

    run_id: int | None
    head_sha: str | None
    verdict: str
    jobs: tuple[JobReading, ...] = ()
    run_status: str | None = None
    run_conclusion: str | None = None

    @property
    def ok(self) -> bool:
        """Only :data:`PASS` licenses a green claim.  Everything else is not-green."""
        return self.verdict == PASS

    @property
    def disagrees_with_run_level(self) -> bool:
        """Does the aggregate GitHub publishes differ from what the jobs say?

        True for the live 08-05 record: ``conclusion=null`` while a job is
        ``failure``.  Worth surfacing explicitly — a caller that has been
        reading the run conclusion wants to know the moment it stops matching.
        """
        published = _verdict_of(self.run_status, self.run_conclusion)
        return published != self.verdict

    def failed_jobs(self) -> tuple[JobReading, ...]:
        return tuple(j for j in self.jobs if j.verdict == FAIL)

    def ceiling_breaches(self) -> tuple[JobReading, ...]:
        """Jobs that were killed *at* their cap — post-mortem."""
        return tuple(j for j in self.jobs if j.at_ceiling)

    def ceiling_warnings(self) -> tuple[JobReading, ...]:
        """Jobs still running that are already near their cap — early warning."""
        return tuple(j for j in self.jobs if j.approaching_ceiling)

    def describe(self) -> str:
        head = f"run {self.run_id} ({(self.head_sha or '?')[:8]}): {self.verdict}"
        if self.disagrees_with_run_level:
            head += (
                f"  [run-level says {self.run_conclusion or self.run_status!r} —"
                " the jobs disagree]"
            )
        return "\n".join([head, *(f"  - {j.describe()}" for j in self.jobs)])


def _verdict_of(status: str | None, conclusion: str | None) -> str:
    """Map one GitHub ``(status, conclusion)`` pair to a verdict.

    The whole point of the module lives in four lines.  ``status`` decides
    whether a verdict exists at all; ``conclusion`` decides what it is.  Reading
    ``conclusion`` alone conflates "no verdict yet" with "no verdict ever", and
    reading ``status`` alone conflates a pass with a failure.
    """
    if status is None and conclusion is None:
        return UNREADABLE
    if status != "completed":
        return PENDING if status in {"queued", "in_progress", "waiting", "requested", "pending"} else UNREADABLE
    if conclusion == "success":
        return PASS
    if conclusion == "failure":
        return FAIL
    if conclusion in _UNRUN_CONCLUSIONS:
        return UNRUN
    return UNREADABLE


def _parse_ts(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return None


def _duration_s(job: dict, now: datetime | None = None) -> tuple[float | None, bool]:
    """``(seconds, running)`` for one job.

    With `now` supplied, a started-but-unfinished job reports **elapsed so far**
    and flags itself ``running``; without one it reports ``None``, because a
    duration invented from the local clock would be a reading of this box rather
    than of the runner.  The caller decides whether it has a trustworthy clock;
    the default is to decline.
    """
    t0 = _parse_ts(job.get("started_at"))
    t1 = _parse_ts(job.get("completed_at"))
    if t0 is None:
        return None, False
    if t1 is not None:
        return (t1 - t0).total_seconds(), False
    if now is None:
        return None, False
    return max(0.0, (now - t0).total_seconds()), True


def job_caps(workflow: Path | None = None) -> dict[str, float]:
    """Declared ``timeout-minutes`` per job, keyed by the job's **display name**.

    Keyed by display name because that is what the jobs API returns; the
    workflow's own key (``fast``) never appears in a run record.  A job with no
    ``timeout-minutes`` is absent from the map rather than given GitHub's 360-min
    default — an undeclared ceiling is not a ceiling anybody chose, and metering
    against it would manufacture reassuring headroom out of nothing.

    .. warning::
       This reads the workflow **as it is now**, so a historical run is metered
       against today's ceilings rather than the ones in force when it ran.  The
       08-05T03:34Z ``cancelled`` run scores +50% headroom under D-085's raised
       120-min cap and was a breach of the 60-min cap it actually ran under.
       When re-reading a past run, pass the caps of its epoch explicitly — the
       tests here do.
    """
    path = workflow or (REPO_ROOT / DEFAULT_WORKFLOW)
    try:
        spec = yaml.safe_load(Path(path).read_text())
    except (OSError, yaml.YAMLError):
        return {}
    caps: dict[str, float] = {}
    for key, job in (spec or {}).get("jobs", {}).items():
        if not isinstance(job, dict):
            continue
        minutes = job.get("timeout-minutes")
        if isinstance(minutes, (int, float)):
            caps[str(job.get("name") or key)] = float(minutes) * 60.0
    return caps


def read_jobs(
    jobs: list[dict],
    caps: dict[str, float] | None = None,
    now: datetime | None = None,
) -> tuple[JobReading, ...]:
    """Turn raw job records into readings, metered against `caps` where declared.

    `now` enables forward metering of in-flight jobs — see :func:`_duration_s`.
    """
    caps = caps if caps is not None else job_caps()
    out = []
    for job in jobs:
        name = str(job.get("name") or "?")
        seconds, running = _duration_s(job, now)
        out.append(
            JobReading(
                name=name,
                verdict=_verdict_of(job.get("status"), job.get("conclusion")),
                conclusion=job.get("conclusion"),
                status=job.get("status"),
                duration_s=seconds,
                cap_s=caps.get(name),
                running=running,
            )
        )
    return tuple(out)


def read_run(
    run: dict,
    jobs: list[dict],
    caps: dict[str, float] | None = None,
    now: datetime | None = None,
) -> RunReading:
    """Derive a run's verdict from its jobs.

    `run` supplies identity only (id, sha) and its own published verdict for the
    disagreement check.  It is deliberately **not** consulted for the answer: on
    the record this module was written from, doing so returns ``null`` while a
    required job has already failed.
    """
    readings = read_jobs(jobs, caps, now)
    if not readings:
        verdict = NO_JOBS
    else:
        present = {r.verdict for r in readings}
        verdict = next(v for v in _PRECEDENCE if v in present)
    return RunReading(
        run_id=run.get("id"),
        head_sha=run.get("head_sha"),
        verdict=verdict,
        jobs=readings,
        run_status=run.get("status"),
        run_conclusion=run.get("conclusion"),
    )


def _utcnow() -> datetime:
    from datetime import timezone

    return datetime.now(timezone.utc)


def _gh(*args: str) -> object:
    proc = subprocess.run(
        ("gh", *args), capture_output=True, text=True, timeout=60, cwd=REPO_ROOT
    )
    if proc.returncode != 0:
        raise RuntimeError(f"gh {' '.join(args)} failed: {proc.stderr.strip()[:200]}")
    return json.loads(proc.stdout or "null")


def fetch(run_id: int, now: datetime | None = None) -> RunReading:
    """Read one run from the authority.  The only networked function here.

    `now` defaults to the wall clock in UTC so that in-flight jobs are metered
    against their caps.  That is a reading of *this* box's clock against the
    runner's timestamps — good to within clock skew, which is minutes at worst
    against ceilings measured in tens of minutes.
    """
    run = _gh("api", f"repos/{{owner}}/{{repo}}/actions/runs/{run_id}")
    payload = _gh("api", f"repos/{{owner}}/{{repo}}/actions/runs/{run_id}/jobs")
    return read_run(run, (payload or {}).get("jobs", []), None, now or _utcnow())


def fetch_latest(branch: str, workflow_name: str = "Sandbox CI") -> RunReading | None:
    """Most recent run of `workflow_name` on `branch`, read per job."""
    runs = _gh(
        "run", "list", "--branch", branch, "--limit", "20",
        "--json", "databaseId,workflowName,createdAt",
    )
    for entry in sorted(runs or [], key=lambda r: r.get("createdAt", ""), reverse=True):
        if entry.get("workflowName") == workflow_name:
            return fetch(int(entry["databaseId"]))
    return None


def _main(argv: list[str] | None = None) -> int:
    import argparse

    ap = argparse.ArgumentParser(
        prog="python3 -m eval.mppi_sandbox.ci_verdict",
        description="Read the CI authority per job (STATE #1). Exit 0 only on PASS.",
    )
    sub = ap.add_subparsers(dest="cmd", required=True)

    p_run = sub.add_parser("run", help="read one run by id")
    p_run.add_argument("run_id", type=int)

    p_latest = sub.add_parser("latest", help="read the newest run on a branch")
    p_latest.add_argument("branch")
    p_latest.add_argument("--workflow", default="Sandbox CI")

    sub.add_parser("caps", help="print the declared per-job ceilings")

    args = ap.parse_args(argv)

    if args.cmd == "caps":
        caps = job_caps()
        if not caps:
            print("no declared timeout-minutes found")
            return 1
        for name, cap in sorted(caps.items()):
            print(f"{name}: {cap / 60:.0f} min")
        return 0

    reading = fetch(args.run_id) if args.cmd == "run" else fetch_latest(args.branch, args.workflow)
    if reading is None:
        print(f"no {args.workflow!r} run found for {args.branch}")
        return 1
    print(reading.describe())
    for job in reading.ceiling_breaches():
        print(f"=> {job.name} died AT ITS CEILING — raise the cap, do not re-run.")
    for job in reading.ceiling_warnings():
        print(f"=> {job.name} is at {1 - (job.headroom or 0):.0%} of its cap and still running.")
    if reading.verdict == UNRUN:
        print("=> UNRUN: the authority answered nothing. Not green, not red.")
    return 0 if reading.ok else 1


if __name__ == "__main__":  # pragma: no cover - CLI
    raise SystemExit(_main())

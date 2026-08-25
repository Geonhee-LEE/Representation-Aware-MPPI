"""The ceiling is stated twice, and only one of the two is enforced.

D-089 measured why the ``slow`` job dies (a nested suite run outgrew the 900 s
timeout guarding it), D-092 measured the multiplier (**>=18** nested runs, **6**
declared runner classes), and D-093 shipped the memo that collapses them.  What
remains is the half D-092 proved mandatory: **6 x 1396 s = 8376 s against a
7200 s ceiling**, ``INSUFFICIENT`` by 1176 s.  This module does that raise, and
does it so that the next one is a red test rather than a fourth guess.

Three separate defects sit in the way, and each has bitten this branch already.

**1. The number lives in two files.**  ``timeout-minutes:`` is declared in
``.github/workflows/sandbox-ci.yml``, which is the only place it is *enforced*;
``nested_suite_cost.SLOW_CEILING_SECONDS`` is a hand-typed copy of it, and
every ``grade()`` reading in this package is taken against the copy.  Raise one
and not the other and the instruments report on a ceiling CI does not apply —
in whichever direction happens to read clean.  This is **D-047's defect class**
exactly (a hand-typed copy of a registry that had since grown, three of five
paths, and the two it missed were the two the rule existed to catch).  So
:func:`ceiling_seconds` reads the workflow, and :func:`agreement` grades the
copy against it.

**2. Three raises were set from the last reading, and each became the thing
under test.**  10 -> 30 (D-084), 60 -> 120 (D-085), and the workflow's own
comment already names the mechanism — *"setting this to the measured figure is
how the old job got a 10-minute ceiling that silently became the thing under
test"* — while the value beside it was set that way anyway.  So the requirement
here is **derived, not chosen**: :func:`required_seconds` is the measured
collapsed floor times :data:`HEADROOM_FACTOR`, and :func:`grade` refuses to
certify a declared ceiling below it *and names the minutes that would clear it*.
The factor is D-085's own stated rule ("the headroom is doubled rather than
trimmed to the last reading"), applied rather than quoted.

**3. There is a ceiling on ceilings, and the floor is already most of the way
to it.**  ``timeout-minutes`` is not a free variable: a GitHub-hosted job is
killed by the platform regardless of what the workflow declares.  Measured at
the documented cap, the runway is **one** more full-suite runner class — at 7
classes the requirement is 325.7 min and still declarable, at 8 it is 372.3 and
**no value works**.  This branch has been adding runner classes at roughly one
per three cycles, so that is not a distant bound.  Past it the only remaining
moves are co-installing the recorders into one run or cutting the census
subject.  :func:`runway` reports it and :data:`UNENFORCEABLE` is the verdict —
which is why D-094 declares the cap itself rather than the 280 the requirement
alone would justify: a fourth incremental raise would buy one cycle and nothing
else.

(I estimated this at two before running it.  The estimate was wrong by the
whole remaining margin, which is the reason it is a function.)

⚠️ **The cap is declared here, not measured here.**  :data:`PLATFORM_MAX_MINUTES`
is the documented GitHub-hosted job limit; this cycle had **no network access**
to fetch the page and no artifact in this repo records it, so it enters as an
*input* and never as a finding.  Every consumer takes it as an argument that may
be ``None``, :func:`runway` returns ``None`` rather than a number when it is,
and :func:`grade` reads :data:`CAP_UNVERIFIED` instead of :data:`UNENFORCEABLE`
so a conditional claim is never printed in the shape of a measured one.  The
five names this package has already needed for absence-as-result — ``UNRUN``,
``UNPOPULATED``, ``UNCOLLECTED``, ``UNIDENTIFIED``, ``UNREAD`` — are the same
lesson; this is the sixth, and the first about an input rather than an output.

To verify the cap and turn the runway into a measurement, fetch
https://docs.github.com/en/actions/reference/limits and pass ``cap_minutes``
explicitly.  Until then the runway is *conditional on 360* and says so.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml

from . import nested_suite_cost as nsc

PACKAGE = Path(__file__).resolve().parent
ROOT = PACKAGE.parent.parent

#: Where the ceiling is *enforced*.  Anything else is a copy.
WORKFLOW = ROOT / ".github" / "workflows" / "sandbox-ci.yml"

#: Multiplier from the measured collapsed floor to the ceiling we may declare.
#: D-085's rule, stated in the workflow and not applied there: the instrument
#: suite's cost is superlinear in instrument count, so the headroom is doubled
#: rather than trimmed to the last reading.  It also absorbs the `slow` job's
#: own non-nested work, which is **unmeasured** — the last verdict-reaching runs
#: (20.8 / 24.9 / 29.5 / 57.97 min) all *contain* nested runs, so none of them
#: isolates it.  Doubling covers both without claiming to have measured either.
HEADROOM_FACTOR = 2.0

#: The platform's own kill, in minutes.  **Declared, not measured here** — see
#: the module docstring.  Pass ``cap_minutes=None`` to any consumer to get the
#: unconditional answer, which is that the runway is unknown.
PLATFORM_MAX_MINUTES = 360

#: The job the collapsed floor is a measurement *of*.  The nested suite runs
#: live in ``slow``-marked tests, so :func:`collapsed_floor_seconds` is a
#: statement about this job and no other.  Grading ``fast`` against it would be
#: a bound computed for one purpose used for another — D-090's shape, which has
#: now inverted a verdict twice on this branch (D-092, D-091), so it gets a
#: verdict rather than a docstring warning.
FLOOR_JOB = "slow"

#: :func:`grade` verdicts.
SUFFICIENT = "SUFFICIENT"
INSUFFICIENT = "INSUFFICIENT"
UNENFORCEABLE = "UNENFORCEABLE"
CAP_UNVERIFIED = "CAP_UNVERIFIED"
UNDECLARED = "UNDECLARED"
UNREAD = "UNREAD"
WRONG_SUBJECT = "WRONG_SUBJECT"

#: :func:`agreement` verdicts.
AGREES = "AGREES"
DIVERGES = "DIVERGES"


def declared_ceilings(workflow: Path | None = None) -> dict[str, int | None] | None:
    """``{job: timeout-minutes}`` as the workflow declares it.

    ``None`` for a job means it declares no ``timeout-minutes`` — which is *not*
    "no ceiling": the platform default applies, and reading an absent key as an
    absent limit is the shape this package has now named six times.  ``None``
    for the whole result means the workflow could not be read, and callers must
    grade that :data:`UNREAD` rather than treating an empty mapping as a clean
    bill.
    """
    path = workflow or WORKFLOW
    try:
        doc = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError):
        return None
    if not isinstance(doc, dict) or not isinstance(doc.get("jobs"), dict):
        return None
    out: dict[str, int | None] = {}
    for job, body in doc["jobs"].items():
        if not isinstance(body, dict):
            return None
        value = body.get("timeout-minutes")
        out[str(job)] = int(value) if isinstance(value, int) else None
    return out


def ceiling_seconds(job: str = "slow",
                    workflow: Path | None = None,
                    cap_minutes: int | None = PLATFORM_MAX_MINUTES) -> int | None:
    """The ceiling this job actually runs under, in seconds.

    Read from the workflow, because that is where it is enforced.  A job that
    declares nothing runs under the platform default, so the answer is the cap
    when one is supplied and ``None`` when it is not — an undeclared ceiling
    under an unverified cap is genuinely unknown, and this refuses to guess it.
    """
    declared = declared_ceilings(workflow)
    if declared is None or job not in declared:
        return None
    minutes = declared[job]
    if minutes is None:
        return None if cap_minutes is None else cap_minutes * 60
    return minutes * 60


def required_seconds(floor_seconds: int,
                     factor: float = HEADROOM_FACTOR) -> int:
    """The smallest ceiling this package is willing to certify, in seconds.

    ``floor_seconds`` is the *collapsed upper bound* — what the nested runs cost
    after a perfect memo, from :func:`nested_run_ledger.grade`.  It is a floor
    on the job, not an estimate of it: the job also does its own non-nested work
    on top.  Hence the factor, and hence the fact that this number is derived
    from a measurement rather than read off one.
    """
    return int(-(-floor_seconds * factor // 1))


def collapsed_floor_seconds(suite_seconds: int = nsc.CI_FAST_HALF_SECONDS,
                            root: Path | None = None) -> int:
    """The measured collapsed floor: declared runner classes x one suite run.

    Deliberately routed through :func:`nested_run_ledger.declared_classes`, the
    **upper** bound over classes, because certifying sufficiency from a lower
    bound is what graded D-092's first draft ``SUFFICIENT`` on a population
    missing one name.
    """
    from . import nested_run_ledger as nrl
    return len(nrl.declared_classes(root)) * suite_seconds


@dataclass(frozen=True)
class CeilingReading:
    """What the job may run for, against what it needs to."""

    verdict: str
    job: str
    declared_seconds: int | None
    required_seconds: int
    floor_seconds: int
    cap_minutes: int | None

    @property
    def required_minutes(self) -> int:
        """Minutes a ``timeout-minutes:`` line would have to declare."""
        return int(-(-self.required_seconds // 60))

    @property
    def headroom_seconds(self) -> int | None:
        if self.declared_seconds is None:
            return None
        return self.declared_seconds - self.required_seconds


def grade(job: str = FLOOR_JOB,
          suite_seconds: int = nsc.CI_FAST_HALF_SECONDS,
          workflow: Path | None = None,
          cap_minutes: int | None = PLATFORM_MAX_MINUTES,
          root: Path | None = None,
          floor_seconds: int | None = None) -> CeilingReading:
    """Is the *enforced* ceiling above the *derived* requirement?

    Verdict precedence is chosen so that no unknown is ever folded into a pass:
    :data:`WRONG_SUBJECT` outranks everything (a reading about the wrong job is
    not a weak reading, it is a different question), then :data:`UNREAD` (the
    workflow did not parse) and :data:`UNDECLARED`, and only then the
    arithmetic.  :data:`CAP_UNVERIFIED` outranks :data:`UNENFORCEABLE` because
    "the requirement exceeds the platform cap" is a claim about a number this
    module was told rather than one it measured.

    ``floor_seconds`` may be passed for a job whose floor was measured
    elsewhere; left ``None`` it is the nested-run collapse, which is a
    :data:`FLOOR_JOB` quantity and refuses to be applied to another job.
    """
    if floor_seconds is None and job != FLOOR_JOB:
        return CeilingReading(verdict=WRONG_SUBJECT, job=job,
                              declared_seconds=None, required_seconds=0,
                              floor_seconds=0, cap_minutes=cap_minutes)
    floor = (collapsed_floor_seconds(suite_seconds, root)
             if floor_seconds is None else floor_seconds)
    need = required_seconds(floor)
    declared = declared_ceilings(workflow)
    reading = CeilingReading(verdict=UNREAD, job=job, declared_seconds=None,
                             required_seconds=need, floor_seconds=floor,
                             cap_minutes=cap_minutes)
    if declared is None or job not in declared:
        return reading
    if declared[job] is None:
        return CeilingReading(**{**reading.__dict__, "verdict": UNDECLARED})

    seconds = ceiling_seconds(job, workflow, cap_minutes)
    if cap_minutes is None:
        verdict = CAP_UNVERIFIED if need > (seconds or 0) else SUFFICIENT
    elif need > cap_minutes * 60:
        verdict = UNENFORCEABLE
    elif (seconds or 0) >= need:
        verdict = SUFFICIENT
    else:
        verdict = INSUFFICIENT
    return CeilingReading(**{**reading.__dict__,
                            "verdict": verdict, "declared_seconds": seconds})


def agreement(workflow: Path | None = None,
              copy_seconds: int = nsc.SLOW_CEILING_SECONDS,
              job: str = "slow",
              cap_minutes: int | None = PLATFORM_MAX_MINUTES) -> str:
    """Does the hand-typed copy still say what the enforced ceiling says?

    :data:`nested_suite_cost.SLOW_CEILING_SECONDS` is the number every ``grade``
    in this package is taken against, and the workflow is the number CI applies.
    They are two statements of one fact, which is the arrangement D-047 was
    written about.  Deriving the copy away entirely would be better; pinning
    this to :data:`AGREES` at least makes the divergence loud instead of silent.
    """
    enforced = ceiling_seconds(job, workflow, cap_minutes)
    if enforced is None:
        return UNREAD
    return AGREES if enforced == copy_seconds else DIVERGES


def runway(suite_seconds: int = nsc.CI_FAST_HALF_SECONDS,
           cap_minutes: int | None = PLATFORM_MAX_MINUTES,
           factor: float = HEADROOM_FACTOR,
           root: Path | None = None) -> int | None:
    """How many more full-suite runner classes fit under the platform cap.

    ``None`` when the cap is unverified — the honest answer, and the reason this
    is a function taking the cap rather than a constant folding it in.  ``0``
    means the next runner class added to this package makes the ``slow`` job
    unfixable by any ``timeout-minutes`` value, which is a different kind of
    fact from "the ceiling is too low" and deserves to be reported before it is
    true rather than after.
    """
    if cap_minutes is None:
        return None
    from . import nested_run_ledger as nrl
    classes = len(nrl.declared_classes(root))
    budget_seconds = cap_minutes * 60
    extra = 0
    while required_seconds((classes + extra + 1) * suite_seconds,
                           factor) <= budget_seconds:
        extra += 1
        if extra > 1000:  # pragma: no cover - runaway guard
            break
    return extra


def _main() -> None:  # pragma: no cover - CLI
    reading = grade()
    print(f"job {reading.job}: {reading.verdict}")
    print(f"  collapsed floor : {reading.floor_seconds} s "
          f"({reading.floor_seconds / 60:.1f} min)")
    print(f"  required        : {reading.required_seconds} s "
          f"(timeout-minutes: {reading.required_minutes})")
    print(f"  declared        : {reading.declared_seconds} s")
    print(f"  copy agreement  : {agreement()}")
    room = runway()
    print(f"  runway          : "
          f"{'unknown (cap unverified)' if room is None else room} "
          f"more runner classes (cap={reading.cap_minutes} min, declared)")


if __name__ == "__main__":  # pragma: no cover
    _main()

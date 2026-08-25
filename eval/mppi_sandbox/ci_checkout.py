"""How deep CI checks out the repository — because the suite reads it as a corpus.

Most test suites do not care what ``actions/checkout`` leaves on disk: they read
the *worktree*, and depth 1 gives them a correct one.  This suite is not most
suites.  A large part of it reads the repository's **history** as its subject —
``cycle_artifacts`` assigns rows by commit date, ``tsv_timestamp`` classifies a
typed stamp against the commit that carried it, ``assert_reach`` takes readings
at the run commit.  For those modules the commit graph *is* the input data, and
``actions/checkout@v4`` hands them a one-commit graph unless told otherwise.

The failure mode this makes possible is the expensive one: the same code, over
the same worktree, returns different answers locally and in CI, and **neither is
buggy**.  Measured 2026-08-13 against run 31618148485 — the first Sandbox CI run
in thirteen to reach a verdict at all (D-227 ended the cancellations) — 19 tests
failed there while the local suite on the identical tree was green 2699/2857.
18 of the 19 pass in a full-depth clone that is otherwise identical, receipt
store absent either way.  So the red was **checkout configuration**, not defect.

The reading is deliberately shaped like :mod:`declared_ceiling`, and repeats its
central lesson because this module is another instance of it: **a job that
declares no ``fetch-depth`` has not declined to specify one.**  It has specified
1.  Reading an absent key as an absent constraint is how a shallow checkout
stayed invisible while it was inverting verdicts.
"""

from __future__ import annotations

from pathlib import Path

import yaml

PACKAGE = Path(__file__).resolve().parent
ROOT = PACKAGE.parent.parent

#: Where checkout depth is *enforced*.  Anything else is a copy.
WORKFLOW = ROOT / ".github" / "workflows" / "sandbox-ci.yml"

#: ``actions/checkout``'s depth when the job says nothing.  Not "unspecified" —
#: this is the number the action uses, and the whole point of the module.
CHECKOUT_DEFAULT_DEPTH = 1

#: The depth that means "all of it", in ``actions/checkout``'s own encoding.
FULL = 0

#: Jobs whose steps run the suite, and therefore whose depth is load-bearing.
#: Derived, not typed: any job that invokes pytest reads the corpus.
SUITE_STEP_MARKER = "pytest"

#: :func:`grade` verdicts.
FULL_DEPTH = "FULL_DEPTH"
SHALLOW = "SHALLOW"
UNREAD = "UNREAD"
NO_SUITE_JOB = "NO_SUITE_JOB"


def _jobs(workflow: Path | None = None) -> dict | None:
    path = workflow or WORKFLOW
    try:
        doc = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError):
        return None
    if not isinstance(doc, dict) or not isinstance(doc.get("jobs"), dict):
        return None
    return doc["jobs"]


def _runs_suite(body: dict) -> bool:
    """Does this job actually run the suite?

    Checked by looking for pytest in the job's ``run:`` steps rather than by
    matching job names, so renaming a job cannot silently drop it out of the
    population this module grades.
    """
    steps = body.get("steps")
    if not isinstance(steps, list):
        return False
    for step in steps:
        if isinstance(step, dict) and SUITE_STEP_MARKER in str(step.get("run", "")):
            return True
    return False


def checkout_depths(workflow: Path | None = None) -> dict[str, int] | None:
    """``{job: fetch-depth}`` for every job that runs the suite.

    A job that checks out without a ``with.fetch-depth`` reports
    :data:`CHECKOUT_DEFAULT_DEPTH`, not ``None`` — see the module docstring.  A
    job that never checks out at all is absent from the mapping; it has no
    corpus to be wrong about.  ``None`` for the whole result means the workflow
    could not be read, which callers must grade :data:`UNREAD` rather than
    treating as a clean bill.
    """
    jobs = _jobs(workflow)
    if jobs is None:
        return None
    out: dict[str, int] = {}
    for job, body in jobs.items():
        if not isinstance(body, dict) or not _runs_suite(body):
            continue
        steps = body.get("steps")
        for step in steps if isinstance(steps, list) else []:
            if not isinstance(step, dict):
                continue
            if not str(step.get("uses", "")).startswith("actions/checkout"):
                continue
            with_ = step.get("with")
            depth = with_.get("fetch-depth") if isinstance(with_, dict) else None
            out[str(job)] = (int(depth) if isinstance(depth, int)
                             else CHECKOUT_DEFAULT_DEPTH)
            break
    return out


def shallow_jobs(workflow: Path | None = None) -> list[str] | None:
    """Suite-running jobs that would read a truncated commit graph."""
    depths = checkout_depths(workflow)
    if depths is None:
        return None
    return sorted(j for j, d in depths.items() if d != FULL)


def grade(workflow: Path | None = None) -> str:
    """One verdict over the whole workflow.

    :data:`NO_SUITE_JOB` is kept distinct from :data:`FULL_DEPTH` on purpose: a
    workflow with nothing to grade is not a workflow that passed.  That is the
    vacuity this package refuses everywhere else.
    """
    depths = checkout_depths(workflow)
    if depths is None:
        return UNREAD
    if not depths:
        return NO_SUITE_JOB
    return FULL_DEPTH if all(d == FULL for d in depths.values()) else SHALLOW


def report(workflow: Path | None = None) -> str:
    verdict = grade(workflow)
    depths = checkout_depths(workflow) or {}
    lines = [f"ci_checkout — {verdict}", ""]
    for job, depth in sorted(depths.items()):
        how = "full history" if depth == FULL else f"depth {depth}"
        flag = "" if depth == FULL else "   <- reads a truncated corpus"
        lines.append(f"  {job:<24} {how}{flag}")
    if verdict == SHALLOW:
        lines += [
            "",
            "  The suite reads history as data (cycle_artifacts, tsv_timestamp,",
            "  assert_reach).  A shallow job makes those modules disagree with",
            "  the same code run locally, and neither side is buggy (D-228).",
        ]
    return "\n".join(lines)


def _main() -> None:  # pragma: no cover - CLI
    import sys

    print(report())
    sys.exit(1 if grade() in (SHALLOW, UNREAD, NO_SUITE_JOB) else 0)


if __name__ == "__main__":  # pragma: no cover - CLI
    _main()

"""Does a guard's reading *move* when its rule is actually broken? (Q-065 (b))

D-049 left a gap it named but did not test.  :func:`guard_reflexivity.revocable`
asks whether a guard's population is a **difference between two observations** —
a structural property, computed from the AST.  It matched **two** guards.  The
failure D-047 found occurred in **one**.  The other,
:func:`local_only_audit.staged_declarations`, has the identical shape and is a
guard *working*: the forbidden act **fills** its population where it **empties**
the other's.  Shape twice, failure once.  Direction is not in the structure.

Q-065 asked whether the direction can be recovered statically — infer which term
of the difference the forbidden act moves — or whether it has to be executed.
Lean was (b), execute, because the population is small (2 of 28) and because the
one decisive experiment in D-049 was exactly this: stage a file in a scratch
repo and look.  This module is that, generalised and repeated per declared path.

What the probe does
-------------------

Per (guard, declared path), in a throwaway git repository standing in D-011's
situation — an ``origin/main``, an ``autoresearch/*`` branch, the five declared
local-only paths tracked and committed:

1. **Edit** the declared path in the worktree without staging it.  This is the
   *permitted* state; D-011 requires exactly this.  Read the guard → ``before``.
2. **Commit** it — ``git add`` then ``git commit``.  This is the offence the
   rule forbids.  Read the guard → ``after``.

The verdict is **membership, not cardinality**: does ``after`` name the path
that was just committed?  Cardinality was the obvious measure and it is the
wrong one — see :class:`Direction`.

Liveness, so ``SILENT`` means something
---------------------------------------

A guard that returns the empty tuple unconditionally would score ``SILENT``
without being blind to anything in particular; it would just be dead.  So every
probe also carries an act the guard *is* supposed to catch, run in the same
scratch repo, and a reading that stays empty through **that** raises rather than
scoring.  A blindness finding is worth what the liveness check is worth.

The probe table is typed; its completeness is not
-------------------------------------------------

:data:`PROBES` maps a guard qualname to how to call it and what act to commit —
knowledge that comes from the *rule* side, which is the objection Q-065 (a)
raised against the static route and which (b) does not escape.  What it does
escape is D-045's failure mode, where a hand-written registry silently omits a
member: :func:`unprobed_revocable` compares the table's key set against
:func:`guard_reflexivity.revocable` and is asserted empty in the tests, so a new
``DIFFERENCE``-shaped guard cannot appear without a probe.  The table may be
typed.  Its *population* is derived.
"""

from __future__ import annotations

import subprocess
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from pathlib import Path

from . import guard_reflexivity as gr
from .tree_provenance import DECLARED_LOCAL_ONLY

#: ``after`` names the path the offence just committed — the guard fires on the
#: act it exists to forbid.
VERDICT_NAMES = "NAMES_OFFENCE"
#: ``after`` does not name it.  The rule was broken and the instrument did not
#: say so — D-047's defect, stated as an executed reading rather than a shape.
VERDICT_SILENT = "SILENT"


class ProbeError(RuntimeError):
    """A probe could not be run, or its liveness check did not hold.

    Raised rather than defaulted, for the reason :mod:`local_only_audit` gives:
    an audit that degrades to "found nothing" reports a clean guard for an
    experiment it never performed.
    """


@dataclass(frozen=True)
class Probe:
    """How to read one guard in a scratch repo, and what it must be able to see.

    :param read: guard → the set of paths it currently names, given a repo root.
    :param liveness: an act that must make :attr:`read` name
        :attr:`liveness_subject`, so a ``SILENT`` verdict distinguishes *blind
        to this offence* from *dead*.
    :param liveness_subject: the path :attr:`liveness` acts on.  Declared rather
        than left implicit in the act's body, because it is what the check
        asserts — see :func:`check_liveness`.
    :param read_unexempted: the same guard with its registry filter suppressed —
        its population before the exemption removes anything.  This is what
        separates *blinded by the exemption* from *blinded by the collapse*
        (:class:`Mechanism`); both readings come from the guard's own code, not
        from a re-implementation.
    """

    read: Callable[[Path], frozenset[str]]
    liveness: Callable[[Path], None]
    liveness_note: str
    read_unexempted: Callable[[Path], frozenset[str]]
    liveness_subject: str = ""
    subjects: tuple[str, ...] = tuple(DECLARED_LOCAL_ONLY)
    """What this guard's rule is *about* — the offences to execute against it.

    Was the module-level ``DECLARED_LOCAL_ONLY`` for as long as every probed
    guard enforced D-011, and the generalisation was invisible because two
    guards enforcing one rule cannot distinguish "the paths this rule covers"
    from "the paths every rule covers".  The third guard is about journal files
    and the loop was still iterating snapshot paths, which would have committed
    ``STATE.md`` at :func:`cycle_artifacts.unsupported` and scored it blind to an
    offence that is not its.
    """
    build: Callable[[Path], None] | None = None
    """Fixture builder; ``None`` means D-011's :func:`build_scratch_repo`."""
    permit: Callable[[Path, str], None] | None = None
    """Put the repo in the *permitted* state for one subject, before the offence."""
    offend: Callable[[Path, str], None] | None = None
    """Commit the forbidden act for one subject.  ``None`` means ``git commit``."""


@dataclass(frozen=True)
class Direction:
    """One executed before/after reading of a guard across its own offence.

    :attr:`verdict` is decided by membership — is the committed path in
    ``after``.  Cardinality is recorded but deliberately not the test, and the
    reason is the point of the cycle: D-047's guard does not *shrink* when the
    rule breaks.  Its exemption has already emptied it, so it reads the same
    empty tuple on both sides.  A shrink test would score it ``INERT`` alongside
    every guard the offence is irrelevant to, and the one real blindness in the
    package would be indistinguishable from noise.  ``quieter`` is kept so that
    claim is a recorded reading rather than an assertion in prose.
    """

    guard: str
    path: str
    before: tuple[str, ...]
    after: tuple[str, ...]
    verdict: str

    @property
    def quieter(self) -> bool:
        """Did the reading strictly shrink — ``revocable``'s implied mechanism?"""
        return len(self.after) < len(self.before)

    @property
    def moved(self) -> bool:
        """Did the reading change at all across the offence?"""
        return self.before != self.after


# --------------------------------------------------------------------------
# scratch repository
# --------------------------------------------------------------------------


def _git(root: Path, *args: str, when: str | None = None) -> str:
    """Run git in *root*; ``when`` pins both dates so a fixture can be *dated*.

    :mod:`cycle_artifacts` reads a row's date from ``git blame`` and its
    subject's date from ``git show`` on the recorded sha, and the whole finding
    it publishes is a case where those two disagree.  A fixture that cannot set
    them cannot construct that case, so it could only be described in prose —
    which is what D-105 had to do.
    """
    env = None
    if when is not None:
        import os

        env = {**os.environ, "GIT_AUTHOR_DATE": when, "GIT_COMMITTER_DATE": when}
    try:
        out = subprocess.run(
            ("git", "-C", str(root), *args),
            capture_output=True, check=True, text=True, env=env,
        )
    except (OSError, subprocess.CalledProcessError) as exc:
        raise ProbeError(f"git {' '.join(args)} failed in {root}: {exc}") from exc
    return out.stdout


#: A tracked file that is *not* declared local-only, so an edit to it is a real
#: violation of the thing :func:`tree_provenance.undeclared_drift` reports.
CONTROL_PATH = "eval/control.txt"

#: The declared path :func:`_live_staged_declarations` stages.  Named once and
#: read by both the act and :func:`check_liveness`'s assertion about it — a
#: subject the check re-derives independently is a subject the two can disagree
#: about, which is the shape D-045/D-047 keep finding in hand-copied registries.
LIVE_DECLARED_PATH = next(iter(DECLARED_LOCAL_ONLY))


def build_scratch_repo(root: Path) -> None:
    """A minimal repo in D-011's situation, ready for an offence.

    Every declared local-only path exists and is tracked, plus one control file
    that is not declared.  ``origin/main`` is a real ref because
    :func:`local_only_audit.staged_declarations` reads ``origin/main...HEAD``,
    and the branch is named ``autoresearch/*`` because that is the scope D-011's
    rule is written about.
    """
    root.mkdir(parents=True, exist_ok=True)
    _git(root, "init", "-q", "-b", "main")
    _git(root, "config", "user.email", "probe@local")
    _git(root, "config", "user.name", "probe")
    for rel in (*DECLARED_LOCAL_ONLY, CONTROL_PATH):
        target = root / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(f"base {rel}\n", encoding="utf-8")
    _git(root, "add", "-A")
    _git(root, "commit", "-qm", "base")
    _git(root, "update-ref", "refs/remotes/origin/main", "HEAD")
    _git(root, "checkout", "-q", "-b", "autoresearch/probe")


def _commit_offence(root: Path, rel: str) -> None:
    _git(root, "add", rel)
    _git(root, "commit", "-qm", f"violation: commit {rel}")


def _permit_local_only(root: Path, rel: str) -> None:
    """D-011's permitted state: written in the worktree, deliberately unstaged."""
    (root / rel).write_text("local-only edit\n", encoding="utf-8")


# --------------------------------------------------------------------------
# the probes
# --------------------------------------------------------------------------


def _read_staged_declarations(root: Path) -> frozenset[str]:
    from . import local_only_audit as loa

    return frozenset(loa.staged_declarations(root=root))


def _live_staged_declarations(root: Path) -> None:
    """Staging a declared path is the act this guard is named for (D-049).

    The edit is load-bearing and is the probe's own first self-catch: ``git
    add`` on a file identical to ``HEAD`` moves nothing into the index, so the
    first draft of this act staged a *clean* path, read empty, and the liveness
    check refused it.  A probe whose "act" is a no-op measures nothing, which is
    the same defect as D-048's filter sites with no population.
    """
    (root / LIVE_DECLARED_PATH).write_text("liveness edit\n", encoding="utf-8")
    _git(root, "add", LIVE_DECLARED_PATH)


def _read_staged_changes(root: Path) -> frozenset[str]:
    """:func:`local_only_audit.staged_declarations` with its ``& registry`` gone."""
    from . import local_only_audit as loa

    return frozenset(loa.staged_changes(root=root))


def _read_undeclared_drift(root: Path) -> frozenset[str]:
    from . import tree_provenance as tp

    drift = tp.undeclared_drift(root=root)
    return frozenset((*drift.changed, *drift.added, *drift.removed))


def _read_raw_drift(root: Path) -> frozenset[str]:
    """:func:`tree_provenance.undeclared_drift` with an empty allow-list.

    The function already takes ``declared``, so suppressing the exemption needs
    no second implementation of the diff.
    """
    from . import tree_provenance as tp

    drift = tp.undeclared_drift(root=root, declared={})
    return frozenset((*drift.changed, *drift.added, *drift.removed))


def _live_undeclared_drift(root: Path) -> None:
    """An uncommitted edit to a path that is *not* declared local-only.

    This is precisely what D-043 caught and what the guard reports, so it is the
    right liveness act: if this does not register, the guard is dead rather than
    blind.
    """
    (root / CONTROL_PATH).write_text("liveness edit\n", encoding="utf-8")


# --------------------------------------------------------------------------
# the third guard's offence is not D-011's
# --------------------------------------------------------------------------

#: The branch the journal fixture describes; ``results/probe.tsv`` follows from
#: it the way :func:`cycle_artifacts.tsv_path` derives one from any branch.
CA_BRANCH = "autoresearch/probe"

#: A journal claiming a TSV row it never appended, with **no** row anywhere near
#: it.  Both dating keys agree, so this is the offence the guard must name.
CA_PLAIN = "journal/2026-08/01-11-c2.md"

#: The same claim, but a row appended *later* by another cycle records a sha
#: dated inside this one.  The ``records`` key reads it ``HONOURED``, the
#: ``appended`` key reads it ``UNSUPPORTED``, and the intersection therefore
#: publishes nothing.  D-105 argued this case in prose; here it is executed.
CA_MASKED = "journal/2026-08/01-12-c3.md"


def _ca_journal(stamp: str, claim: str) -> str:
    return (
        f"# probe cycle {stamp}\n\n"
        f"- **Cycle**: {stamp} KST\n"
        f"- **Branch**: `{CA_BRANCH}`\n"
        f"- **Status**: keep\n\n"
        "## Artifacts\n"
        f"- TSV row appended: {claim}\n"
    )


def build_cycle_artifacts_repo(root: Path) -> None:
    """Four dated cycles and a TSV, one row of which is **retroactive**.

    Cycle dates are pinned through ``git commit --date`` rather than left to the
    clock, because the two keys :mod:`cycle_artifacts` compares are both git
    dates: a fixture built "now" collapses them onto one minute and the case
    that separates them cannot occur.
    """
    root.mkdir(parents=True, exist_ok=True)
    _git(root, "init", "-q", "-b", "main")
    _git(root, "config", "user.email", "probe@local")
    _git(root, "config", "user.name", "probe")

    (root / "journal" / "2026-08").mkdir(parents=True, exist_ok=True)
    (root / "results").mkdir(parents=True, exist_ok=True)
    for rel, stamp in (
        ("journal/2026-08/01-10-c1.md", "2026-08-01 10:00"),
        (CA_PLAIN, "2026-08-01 11:00"),
        (CA_MASKED, "2026-08-01 12:00"),
        ("journal/2026-08/01-13-c4.md", "2026-08-01 13:00"),
    ):
        (root / rel).write_text(_ca_journal(stamp, "no"), encoding="utf-8")
    tsv = root / "results" / "probe.tsv"
    tsv.write_text("timestamp\tcommit\tmetric\tstatus\tdescription\n", encoding="utf-8")
    _git(root, "add", "-A")
    _git(root, "commit", "-qm", "cycles", when="2026-08-01T10:30:00+09:00")
    _git(root, "update-ref", "refs/remotes/origin/main", "HEAD")
    _git(root, "checkout", "-q", "-b", CA_BRANCH.split("/", 1)[1])

    # A commit dated inside the 12:00 cycle, so a row *recording* it dates there.
    (root / "results" / "work.txt").write_text("c3 work\n", encoding="utf-8")
    _git(root, "add", "-A")
    _git(root, "commit", "-qm", "c3 work", when="2026-08-01T12:05:00+09:00")
    sha = _git(root, "rev-parse", "--short", "HEAD").strip()

    # Appended at 13:10 — by the 13:00 cycle, three hours after the one whose
    # sha it carries.  ``appended`` says 13:00, ``records`` says 12:00.
    with tsv.open("a", encoding="utf-8") as fh:
        fh.write(f"2026-08-01T13:10:00+09:00\t{sha}\tqual:doc-only\tkeep\tretroactive row\n")
    _git(root, "add", "results/probe.tsv")
    _git(root, "commit", "-qm", "retroactive TSV row",
         when="2026-08-01T13:10:00+09:00")


def _ca_permit(root: Path, rel: str) -> None:
    """Assert the honest state rather than perform it — the build already set it.

    D-011's permitted state is an *act* (edit, leave unstaged); this one is a
    property of the fixture, so the corresponding step has nothing to do.  It is
    checked instead of skipped: a ``before`` reading taken from a state nobody
    verified is how a probe comes to measure the wrong thing, and the first
    draft of this function committed here and died on git's own "nothing to
    commit" — the empty-act self-catch the liveness check was written for,
    arriving one step earlier.
    """
    text = (root / rel).read_text(encoding="utf-8")
    if "TSV row appended: no" not in text:
        raise ProbeError(
            f"{rel} is not in the permitted state: expected a journal claiming "
            f"no TSV row, got {text!r}")


def _ca_offend(root: Path, rel: str) -> None:
    """The offence: flip the claim to ``yes`` without appending a row."""
    stamp = "2026-08-01 " + Path(rel).name.split("-")[1] + ":00"
    (root / rel).write_text(_ca_journal(stamp, "yes"), encoding="utf-8")
    _git(root, "add", rel)
    _git(root, "commit", "-qm", f"violation: unsupported claim in {rel}",
         when="2026-08-01T13:30:00+09:00")


def _read_unsupported(root: Path) -> frozenset[str]:
    from . import cycle_artifacts as ca

    return frozenset(c.path for c in ca.unsupported(CA_BRANCH, root=root))


def _read_unsupported_one_key(root: Path) -> frozenset[str]:
    """The same reading with the second key's agreement suppressed."""
    from . import cycle_artifacts as ca

    return frozenset(
        c.path for c in ca.unsupported_by(CA_BRANCH, "appended", root=root))


def _live_unsupported(root: Path) -> None:
    _ca_offend(root, CA_PLAIN)


# --------------------------------------------------------------------------
# cycle_artifacts.unwatched_strandings  (D-114)
# --------------------------------------------------------------------------
#
# D-112 added the guard and wired it into REVIEW; nothing registered a probe,
# so ``readings()`` raised ``ProbeError`` for six cycles and took five other
# tests down as collateral.  The bill is the same one D-108 paid and the same
# one this table exists to make unpayable-in-silence: a revocable guard with no
# probe is a rule nobody has watched fail.
#
# The offence is **not** a false claim — that is ``unsupported``'s.  It is a
# journal that exists locally and never reached ``origin``, which means the
# permitted state is the path's *absence*: ``_remote_has`` tests for the path in
# ``origin/<branch>``, so rewriting a published journal's content leaves it
# published and could never construct the case.

CS_BRANCH = "autoresearch/probe-strand"
#: Published baseline — keeps ``cycles()`` at ≥ 2 so ``unpublished``'s own
#: short-circuit is never what makes a reading empty.
CS_PUBLISHED = "journal/2026-08/02-10-s0.md"
#: Stranded **and** lying, so it lands in ``unsupported`` and the subtraction
#: that *is* this guard's exemption has something to remove.  Without it
#: ``read`` and ``read_unexempted`` coincide and :class:`Mechanism` cannot tell
#: the exemption apart from the collapse.
CS_LIAR = "journal/2026-08/02-11-s1.md"
#: The offences: journal paths that do not exist until ``offend`` writes them.
CS_SUBJECTS = ("journal/2026-08/02-14-s4.md", "journal/2026-08/02-15-s5.md")
CS_LIVE = "journal/2026-08/02-16-s6.md"


def _cs_journal(rel: str, claim: str) -> str:
    stamp = "2026-08-02 " + Path(rel).name.split("-")[1] + ":00"
    return (
        f"# strand probe cycle {stamp}\n\n"
        f"- **Cycle**: {stamp} KST\n"
        f"- **Branch**: `{CS_BRANCH}`\n"
        f"- **Status**: keep\n\n"
        "## Artifacts\n"
        f"- TSV row appended: {claim}\n"
    )


def build_stranding_repo(root: Path) -> None:
    """A branch whose ``origin`` ref lags: one published cycle, one stranded liar.

    ``origin/<branch>`` is set **mid-history** rather than at the tip, because a
    stranding is exactly the gap between the two and a fixture that pushes
    everything has no gap to read.
    """
    root.mkdir(parents=True, exist_ok=True)
    _git(root, "init", "-q", "-b", "main")
    _git(root, "config", "user.email", "probe@local")
    _git(root, "config", "user.name", "probe")

    (root / "journal" / "2026-08").mkdir(parents=True, exist_ok=True)
    (root / "results").mkdir(parents=True, exist_ok=True)
    tsv = root / "results" / f"{CS_BRANCH.split('/')[-1]}.tsv"
    tsv.write_text("timestamp\tcommit\tmetric\tstatus\tdescription\n", encoding="utf-8")
    _git(root, "add", "-A")
    _git(root, "commit", "-qm", "tsv header", when="2026-08-02T09:00:00+09:00")
    _git(root, "update-ref", "refs/remotes/origin/main", "HEAD")
    _git(root, "checkout", "-q", "-b", CS_BRANCH.split("/", 1)[1])

    # Published: committed, then the remote ref is moved up to include it.
    (root / CS_PUBLISHED).write_text(_cs_journal(CS_PUBLISHED, "no"), encoding="utf-8")
    _git(root, "add", CS_PUBLISHED)
    _git(root, "commit", "-qm", "s0", when="2026-08-02T10:05:00+09:00")
    _git(root, "update-ref", f"refs/remotes/origin/{CS_BRANCH}", "HEAD")

    # Stranded and lying: claims a TSV row over a file that has none.
    (root / CS_LIAR).write_text(_cs_journal(CS_LIAR, "yes"), encoding="utf-8")
    _git(root, "add", CS_LIAR)
    _git(root, "commit", "-qm", "s1", when="2026-08-02T11:05:00+09:00")


def _cs_permit(root: Path, rel: str) -> None:
    """Assert the subject is absent — the state the fixture already leaves.

    Checked rather than performed, for the reason :func:`_ca_permit` gives: a
    ``before`` reading taken from an unverified state is how a probe comes to
    measure something other than what it reports.
    """
    if (root / rel).exists():
        raise ProbeError(
            f"{rel} already exists in the strand fixture: the permitted state "
            "for this guard is the journal's absence, not its content")


def _cs_offend(root: Path, rel: str) -> None:
    """The offence: write an **honest** journal and never push it.

    Honest on purpose.  A lying stranded journal is caught by ``unsupported``
    and would be subtracted straight back out — the population this guard was
    named for is the difference, and the offence has to land inside it.
    """
    (root / rel).parent.mkdir(parents=True, exist_ok=True)
    (root / rel).write_text(_cs_journal(rel, "no"), encoding="utf-8")
    _git(root, "add", rel)
    _git(root, "commit", "-qm", f"stranded cycle {rel}",
         when="2026-08-02T14:05:00+09:00")


def _read_unwatched_strandings(root: Path) -> frozenset[str]:
    from . import cycle_artifacts as ca

    return frozenset(c.path for c in ca.unwatched_strandings(CS_BRANCH, root=root))


def _read_all_strandings(root: Path) -> frozenset[str]:
    """The population before the ``- unsupported`` subtraction removes anything."""
    from . import cycle_artifacts as ca

    return frozenset(c.path for c in ca.stranded(CS_BRANCH, root=root))


def _live_unwatched_strandings(root: Path) -> None:
    _cs_offend(root, CS_LIVE)


# --------------------------------------------------------------------------
# the fourth guard's offence is a *content* move, not a path
# --------------------------------------------------------------------------

#: The path :func:`inert_surface.carried_drift`'s readers are readers *of*.
#: Any string will do — the scan matches it as a substring of the repo-relative
#: path — but a TSV under ``results/`` is the shape the live pins actually hold.
CD_CANDIDATE = "results/cd.tsv"

CD_TESTS = "eval/mppi_sandbox/tests/"

#: Carried readers: present in the pin's ``readers_key``, so an entrance cannot
#: excuse them and the guard is obliged to notice their content moving.
CD_CARRIED = CD_TESTS + "test_cd_carried.py"
CD_CARRIED2 = CD_TESTS + "test_cd_second.py"

#: A reader **absent** from the pin's key, so :func:`inert_surface.entrants`
#: names it and the exemption removes it before any offence.  Not a subject:
#: it is the population difference :attr:`Probe.read_unexempted` exists to
#: expose, and it is what makes the ``exempt=()`` reading non-vacuous here.
CD_ENTRANT = CD_TESTS + "test_cd_entrant.py"

#: Liveness subject — carried, so the act must register.
CD_LIVE = CD_TESTS + "test_cd_live.py"

CD_SUBJECTS = (CD_CARRIED, CD_CARRIED2)

#: Where the fixture records its own base commit.  ``carried_drift`` reads the
#: base off a :class:`inert_surface.Pin`, and a scratch repo has no entry in the
#: live registry — so the fixture writes the sha it committed and the reader
#: builds the pin around it.  A ref rather than a file: a tracked file would
#: itself be a reader and change the very set under measurement.
CD_BASE_REF = "refs/cd/base"


def _cd_reader_src(rel: str, body: str) -> str:
    """A test file that reaches :data:`CD_CANDIDATE` by naming it directly."""
    return (
        f'"""Probe reader {Path(rel).name}."""\n\n\n'
        f"def test_reads_the_candidate():\n"
        f'    path = "{CD_CANDIDATE}"\n'
        f"    assert path\n"
        f"    # {body}\n"
    )


def build_carried_drift_repo(root: Path) -> None:
    """A repo with a pinned reader set, all of it byte-identical to the base.

    The permitted state is *no drift at all*: every carried reader is exactly
    what the base commit holds, so ``before`` is empty and any movement the
    probe reads is the offence it just committed rather than fixture noise.
    """
    root.mkdir(parents=True, exist_ok=True)
    _git(root, "init", "-q", "-b", "main")
    _git(root, "config", "user.email", "probe@local")
    _git(root, "config", "user.name", "probe")

    (root / CD_TESTS).mkdir(parents=True, exist_ok=True)
    (root / "results").mkdir(parents=True, exist_ok=True)
    (root / CD_CANDIDATE).write_text(
        "timestamp\tcommit\tmetric\tstatus\tdescription\n", encoding="utf-8")
    for rel in (CD_CARRIED, CD_CARRIED2, CD_LIVE, CD_ENTRANT):
        (root / rel).write_text(_cd_reader_src(rel, "base content"), encoding="utf-8")

    _git(root, "add", "-A")
    _git(root, "commit", "-qm", "base tree the pin was taken on",
         when="2026-08-03T09:00:00+09:00")
    _git(root, "update-ref", CD_BASE_REF, "HEAD")


def _cd_pin(root: Path) -> "ins.Pin":
    """The pin the fixture stands in for, base commit read back off the ref.

    ``readers_key`` deliberately omits :data:`CD_ENTRANT`: the pin was taken
    before that file existed, which is precisely the state that makes the
    entrant exempt and gives :attr:`Probe.read_unexempted` something to differ
    on.
    """
    from . import inert_surface as ins

    base = _git(root, "rev-parse", CD_BASE_REF).strip()
    return ins.Pin(
        verdict=ins.INERT,
        readers_key="|".join(sorted((CD_CARRIED, CD_CARRIED2, CD_LIVE))),
        taken="2026-08-03",
        note="guard_direction fixture pin",
        base_commit=base,
    )


def _cd_drift(root: Path, exempt: tuple[str, ...] | None = None) -> frozenset[str]:
    from . import inert_surface as ins

    drift = ins.carried_drift(
        CD_CANDIDATE,
        sources=ins._python_sources(root),
        root=root,
        pin=_cd_pin(root),
        exempt=exempt,
    )
    return frozenset((*drift.drifted, *drift.modules_drifted))


def _read_carried_drift(root: Path) -> frozenset[str]:
    return _cd_drift(root)


def _read_all_drift(root: Path) -> frozenset[str]:
    """The same reading with the entrant exemption suppressed.

    ``exempt=()`` rather than a re-implemented diff, for the reason
    :func:`_read_raw_drift` gives: the function already takes the seam, so the
    unexempted population comes from the guard's own code.
    """
    return _cd_drift(root, exempt=())


def _cd_permit(root: Path, rel: str) -> None:
    """Assert the subject has not moved — the state :func:`build_carried_drift_repo`
    leaves.  Checked rather than performed, per :func:`_cs_permit`."""
    if rel in _cd_drift(root):
        raise ProbeError(
            f"{rel} already reads as drifted in the carried-drift fixture: the "
            "permitted state for this guard is a reader identical to its base")


def _cd_offend(root: Path, rel: str) -> None:
    """The offence: move a carried reader's **content** and commit it.

    The pin's key is a set of *names*, and this act leaves every name in place —
    which is the whole premise :func:`inert_surface.carried_drift` was written
    to check.
    """
    (root / rel).write_text(_cd_reader_src(rel, "content moved after the pin"),
                            encoding="utf-8")
    _git(root, "add", rel)
    _git(root, "commit", "-qm", f"move carried reader {rel}",
         when="2026-08-03T14:05:00+09:00")


def _live_carried_drift(root: Path) -> None:
    _cd_offend(root, CD_LIVE)


PROBES: dict[str, Probe] = {
    "inert_surface.carried_drift": Probe(
        read=_read_carried_drift,
        liveness=_live_carried_drift,
        liveness_note="move a carried reader's content while its name stays put",
        read_unexempted=_read_all_drift,
        liveness_subject=CD_LIVE,
        subjects=CD_SUBJECTS,
        build=build_carried_drift_repo,
        permit=_cd_permit,
        offend=_cd_offend,
    ),
    "cycle_artifacts.unsupported": Probe(
        read=_read_unsupported,
        liveness=_live_unsupported,
        liveness_note="a journal claiming a TSV row that was never appended",
        read_unexempted=_read_unsupported_one_key,
        liveness_subject=CA_PLAIN,
        subjects=(CA_PLAIN, CA_MASKED),
        build=build_cycle_artifacts_repo,
        permit=_ca_permit,
        offend=_ca_offend,
    ),
    "cycle_artifacts.unwatched_strandings": Probe(
        read=_read_unwatched_strandings,
        liveness=_live_unwatched_strandings,
        liveness_note="commit a journal locally and leave origin behind it",
        read_unexempted=_read_all_strandings,
        liveness_subject=CS_LIVE,
        subjects=CS_SUBJECTS,
        build=build_stranding_repo,
        permit=_cs_permit,
        offend=_cs_offend,
    ),
    "local_only_audit.staged_declarations": Probe(
        read=_read_staged_declarations,
        liveness=_live_staged_declarations,
        liveness_note="stage a declared path (the INDEX read D-049 added)",
        read_unexempted=_read_staged_changes,
        liveness_subject=LIVE_DECLARED_PATH,
    ),
    "tree_provenance.undeclared_drift": Probe(
        read=_read_undeclared_drift,
        liveness=_live_undeclared_drift,
        liveness_note="edit an undeclared tracked path in the worktree",
        read_unexempted=_read_raw_drift,
        liveness_subject=CONTROL_PATH,
    ),
}


def unprobed_revocable(pool: Iterable[gr.Guard] | None = None) -> tuple[str, ...]:
    """``DIFFERENCE``-shaped guards **with a members-bearing reading** and no probe.

    The derived half of a typed table.  Non-empty means a guard whose direction
    nobody executed — which is the state D-049 shipped and Q-065 was filed
    about, so it must not be reachable silently.

    The obligation is derived from :func:`guard_reflexivity.revocable_collections`
    and not from ``revocable`` itself, which is this cycle's finding: the census
    pool is deliberately a count of visible *spellings* (D-072/D-073), so it
    contains renderers whose counts happen to come from a difference.  Demanding
    an executed "does the reading name the offence" of a function that returns a
    string is a category error, and the only way to satisfy it would be to
    recover the population by parsing the rendered text — a second statement of
    the rule, which is the defect D-045 and D-047 each are.  The exclusion is
    published by :func:`unprobeable_revocable` rather than left implicit.
    """
    have = set(PROBES)
    return tuple(sorted(g.qualname for g in gr.revocable_collections(pool)
                        if g.qualname not in have))


def unprobeable_revocable(pool: Iterable[gr.Guard] | None = None) -> tuple[str, ...]:
    """Revocable guards this module declines to probe, and why it can (D-038).

    Counted rather than silently subtracted.  An exclusion with no enumerator is
    the shape D-045/D-046/D-047 each found in a hand-written registry, and the
    fact that this one is computed does not exempt it from being readable.
    """
    scalar = {g.qualname for g in gr.scalar_readings(pool)}
    return tuple(sorted(g.qualname for g in gr.revocable(pool)
                        if g.qualname in scalar))


def own_fixture_probes() -> tuple[str, ...]:
    """Probes that build their **own** repository instead of D-011's scratch one.

    :mod:`probe_reach` measures whether one shared fixture can host an act for a
    guard, and its ground truth was "every entry in :data:`PROBES`" — sound while
    every probe used that fixture, and false the moment one supplies its own.  A
    guard whose rule is about journal files is not made unprobeable by a fixture
    that contains no journals; it is simply outside that reading.  Published here
    so the exclusion is derived from the table rather than re-typed next to it.
    """
    return tuple(sorted(q for q, p in PROBES.items() if p.build is not None))


def shared_fixture_probes() -> tuple[str, ...]:
    """The complement — the population :mod:`probe_reach`'s reading still covers."""
    return tuple(sorted(q for q, p in PROBES.items() if p.build is None))


def stale_probes(pool: Iterable[gr.Guard] | None = None) -> tuple[str, ...]:
    """Probe entries naming a guard the scan no longer reports as revocable.

    The mirror of :func:`unprobed_revocable`, for :mod:`tree_provenance`'s
    :func:`stale_declarations` reason: an entry for a guard that has changed
    shape is an entry nobody will notice went dead.
    """
    live = {g.qualname for g in gr.revocable_collections(pool)}
    return tuple(sorted(name for name in PROBES if name not in live))


# --------------------------------------------------------------------------
# running one
# --------------------------------------------------------------------------


def check_liveness(qualname: str, workdir: Path) -> frozenset[str]:
    """Perform the guard's own catchable act; the reading must **name its subject**.

    This asserted only ``reading != frozenset()`` for the twenty-odd cycles that
    the probe table had two entries, and on those two it happened to be
    equivalent: the base fixture reads empty for both guards before their act.
    It is not equivalent in general, and
    :func:`liveness_derivation.validate` found the counterexample the moment a
    third guard was measured on a fixture that copies real surfaces in —
    ``unregistered_local_only`` reads non-empty *before* any act and scored live
    on somebody else's population.  A non-emptiness bar tests the fixture; a
    membership bar tests the act.
    """
    probe = PROBES[qualname]
    repo = workdir / "liveness"
    (probe.build or build_scratch_repo)(repo)
    before = probe.read(repo)
    probe.liveness(repo)
    reading = probe.read(repo)
    subject = probe.liveness_subject
    if subject not in reading or subject in before:
        raise ProbeError(
            f"{qualname}: liveness act ({probe.liveness_note}) did not put "
            f"{subject!r} into the reading — before={sorted(before)}, "
            f"after={sorted(reading)}. A SILENT verdict from this probe would "
            "be meaningless")
    return reading


def probe_path(qualname: str, rel: str, workdir: Path) -> Direction:
    """Execute the offence for one (guard, declared path) and read both sides."""
    probe = PROBES[qualname]
    repo = workdir / f"{qualname.replace('.', '_')}__{rel.replace('/', '_')}"
    (probe.build or build_scratch_repo)(repo)

    (probe.permit or _permit_local_only)(repo, rel)
    before = probe.read(repo)

    (probe.offend or _commit_offence)(repo, rel)
    after = probe.read(repo)

    verdict = VERDICT_NAMES if rel in after else VERDICT_SILENT
    return Direction(guard=qualname, path=rel, before=tuple(sorted(before)),
                     after=tuple(sorted(after)), verdict=verdict)


@dataclass(frozen=True)
class Mechanism:
    """Which of two sufficient causes actually blinds a guard to its own offence.

    ``revocable`` models exactly one: the offending act **collapses** the
    difference the population is built from.  There is a second, and it is not
    in the shape — the **exemption** can have removed the offending path from
    the reading *before the act happens at all*.  Both are sufficient, so when
    both hold the collapse is **masked**: it can never be the observed
    mechanism, which is why :attr:`Direction.quieter` reads ``no`` on the one
    guard the shape predicate was built to describe.
    """

    guard: str
    path: str
    exempt_before: tuple[str, ...]
    exempt_after: tuple[str, ...]
    raw_before: tuple[str, ...]
    raw_after: tuple[str, ...]

    @property
    def blinded_by_exemption(self) -> bool:
        """The path is in the population but filtered out — before any offence."""
        return self.path in self.raw_before and self.path not in self.exempt_before

    @property
    def blinded_by_collapse(self) -> bool:
        """The act removes the path from the population itself (revocable's model)."""
        return self.path in self.raw_before and self.path not in self.raw_after

    @property
    def masked(self) -> bool:
        """Both hold ⇒ the shape predicate names a cause that cannot be observed."""
        return self.blinded_by_exemption and self.blinded_by_collapse

    @property
    def exempted_away(self) -> bool:
        """The offence lands *in* the raw reading and the exemption removes it.

        :attr:`blinded_by_exemption` asks the same question one moment earlier —
        was the subject already in the population before the act — and that is
        the right moment only when the permitted state already carries the
        subject, which is true of an unstaged edit and false of a journal that
        has not yet made a false claim.  Adding the moment rather than moving it:
        the two are different readings and D-102's rule is that a repair which
        rewrites the earlier one deletes its own evidence.
        """
        return self.path in self.raw_after and self.path not in self.exempt_after


def mechanism(qualname: str, rel: str, workdir: Path) -> Mechanism:
    """Read one guard four ways across its offence: {exempt, raw} × {before, after}."""
    probe = PROBES[qualname]
    repo = workdir / f"mech__{qualname.replace('.', '_')}__{rel.replace('/', '_')}"
    (probe.build or build_scratch_repo)(repo)

    (probe.permit or _permit_local_only)(repo, rel)
    exempt_before, raw_before = probe.read(repo), probe.read_unexempted(repo)

    (probe.offend or _commit_offence)(repo, rel)
    exempt_after, raw_after = probe.read(repo), probe.read_unexempted(repo)

    return Mechanism(
        guard=qualname, path=rel,
        exempt_before=tuple(sorted(exempt_before)),
        exempt_after=tuple(sorted(exempt_after)),
        raw_before=tuple(sorted(raw_before)),
        raw_after=tuple(sorted(raw_after)),
    )


def mechanisms(workdir: Path) -> tuple[Mechanism, ...]:
    return tuple(mechanism(q, rel, workdir)
                 for q in sorted(PROBES) for rel in PROBES[q].subjects)


def readings(workdir: Path, pool: Iterable[gr.Guard] | None = None) -> tuple[Direction, ...]:
    """Every (revocable guard × declared path) probe, liveness-checked first."""
    missing = unprobed_revocable(pool)
    if missing:
        raise ProbeError(f"no probe for revocable guard(s): {', '.join(missing)}")
    out: list[Direction] = []
    for qualname in sorted(PROBES):
        check_liveness(qualname, workdir / "live" / qualname.replace(".", "_"))
        for rel in PROBES[qualname].subjects:
            out.append(probe_path(qualname, rel, workdir))
    return tuple(out)


def fails_quietly(workdir: Path,
                  pool: Iterable[gr.Guard] | None = None) -> tuple[Direction, ...]:
    """Q-065's answer set: guards live enough to see, silent on their own offence.

    Deliberately **not** an argument on :func:`guard_reflexivity.revocable`, per
    Q-065's stated next action.  ``revocable`` reports a shape and is honest
    about reporting a shape; conflating it with an executed direction would make
    a cheap static reading look like an experiment.
    """
    return tuple(d for d in readings(workdir, pool) if d.verdict == VERDICT_SILENT)


def report(workdir: Path) -> str:
    lines = ["# guard direction (Q-065 (b) — executed, not inferred)", ""]
    obs = readings(workdir)
    lines.append(f"revocable guards probed: {len(PROBES)} · subjects: "
                 + ", ".join(f"{q}={len(PROBES[q].subjects)}" for q in sorted(PROBES))
                 + f" · readings: {len(obs)}")
    skipped = unprobeable_revocable()
    lines.append(f"revocable but not probeable (scalar reading): "
                 f"{', '.join(skipped) if skipped else '(none)'}")
    lines.append("")
    lines.append("| guard | path | before | after | verdict | moved | quieter |")
    lines.append("|---|---|---|---|---|---|---|")
    for d in obs:
        lines.append(
            f"| `{d.guard}` | `{d.path}` | {len(d.before)} | {len(d.after)} | "
            f"{d.verdict} | {'yes' if d.moved else 'no'} | "
            f"{'yes' if d.quieter else 'no'} |")
    quiet = [d for d in obs if d.verdict == VERDICT_SILENT]
    lines.append("")
    lines.append(f"SILENT: {len(quiet)} of {len(obs)} readings, "
                 f"{len({d.guard for d in quiet})} of {len(PROBES)} guards")
    shrank = [d for d in obs if d.quieter]
    lines.append(f"quieter (revocable's implied mechanism): {len(shrank)} of {len(obs)}")

    lines += ["", "## why — the sufficient causes", "",
              "| guard | path | exemption | collapse | masked | exempted away |",
              "|---|---|---|---|---|---|"]
    mechs = mechanisms(workdir)
    for m in mechs:
        lines.append(
            f"| `{m.guard}` | `{m.path}` | {'yes' if m.blinded_by_exemption else 'no'} "
            f"| {'yes' if m.blinded_by_collapse else 'no'} "
            f"| {'yes' if m.masked else 'no'} "
            f"| {'yes' if m.exempted_away else 'no'} |")
    lines.append("")
    lines.append(f"masked (collapse unobservable behind the exemption): "
                 f"{sum(m.masked for m in mechs)} of {len(mechs)}")
    lines.append(f"exempted away (offence enters the raw reading, exemption drops it): "
                 f"{sum(m.exempted_away for m in mechs)} of {len(mechs)}")
    return "\n".join(lines)


def main() -> int:  # pragma: no cover - CLI
    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        print(report(Path(tmp)))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())

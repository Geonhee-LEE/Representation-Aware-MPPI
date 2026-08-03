"""Derive the local-only population from its writers (STATE #1, after D-046).

:data:`tree_provenance.DECLARED_LOCAL_ONLY` is the last hand-typed registry
named in three consecutive findings.  D-044 wrote it by *reading* the prose rule
in ``scripts/prompts/auto_research.md``, which named three files; running
:func:`tree_provenance.undeclared_drift` on the tree immediately found two more
(``TODO.md``, ``research/feed.md``), so the list shipped with five entries and
the honest note that the prose figure had been an undercount for as long as both
writing scripts had existed.  D-045 and D-046 then found the same shape twice
more, in the module list and in the citation list, and the lesson each time was
the same one: a registry maintained by memory is short at whichever element
nobody remembered.  So this module stops maintaining the list and derives it.

What "derive" means here
------------------------

A local-only path is not a property of the path.  It is a property of **who
writes it and whether the writing lands**, which is two independent questions
and needs two independent instruments:

``overwrite_sites``
    Who writes it, and in what mode.  Scans the *writer surface* — the cron
    scripts and their prompt files, globbed rather than typed, per D-045 — for
    a tracked path stated inside a unit of text that also states a
    full-overwrite verb.  A file rewritten wholesale or prepended-to every cycle
    cannot be reconstructed from a branch diff, which is the property D-011
    actually cared about.

``branch_committed``
    Whether the writing lands.  A path that ``autoresearch/*`` branches commit
    is part of the durable record, however it is written; a path they never
    commit is local-only whether or not anyone declared it.  This is read from
    git, not from prose, and it is what separates ``docs/decisions.md`` — also
    prepended every cycle, also never reconstructible from a diff, and
    emphatically committed — from the five.

Neither alone is sound.  The overwrite scan cannot tell the two classes apart:
the 🚫 paragraph that states the rule names *both* in the same breath, the
never-staged three and the durable-record four, because that paragraph's whole
job is to contrast them.  The git test cannot tell a local-only file from a file
nobody happens to have touched lately.  Intersected, each covers the other's
failure, and both are auditable.

The epoch is load-bearing
-------------------------

``branch_committed`` asked over all history says the three snapshot files *are*
committed on live branches — and it is right.  Four ``p2-*`` branches carry
them, two of which are still in the review queue, and every such commit is dated
the day D-011 was accepted or earlier.  The rule has held since without
exception.  So the window opens at :func:`rule_epoch`, parsed out of D-011's own
heading in ``docs/decisions.md`` rather than typed here, and the pre-epoch
commits are reported separately by :func:`pre_epoch_commits` instead of being
dropped: they are the mechanism D-011 was written about, still sitting in the
queue, and a filter that hid them would be hiding the evidence for its own
epoch.

What running it found
---------------------

The derived population and the declared one agree — the first registry in four
cycles that was not short.  The finding is one level over, in the *executable*
guard rather than the list: the Phase 3 push check is a hand-typed alternation
matching three of the five declared paths.  ``TODO.md`` and ``research/feed.md``
are declared local-only by the module the same executor wrote, and staging
either passes the guard silently — which is exactly D-011's conflict mechanism,
re-admitted through the check written to prevent it.  See
:func:`unguarded_declarations`; the guard's pattern is read out of the prompt
file, so the test tracks the guard rather than a copy of it.

The second finding is that :func:`tree_provenance.undeclared_drift` cannot see a
violation of the rule it enforces.  It diffs the worktree against ``HEAD``, so
staging ``STATE.md`` makes the two *agree* and the drift goes quiet: the
instrument reads cleanest at the moment the rule is broken.  Committing is
D-011's actual failure mode and it needs a different comparison —
:func:`staged_declarations` diffs against ``origin/main`` instead.

Fast half: this module globs, reads text, and shells out to ``git``.  Nothing
simulates.
"""

from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass
from pathlib import Path

from .tree_provenance import DECLARED_LOCAL_ONLY, REPO_ROOT, tracked_paths

#: The writer surface, globbed.  Every cron entry point and every prompt file
#: those entry points hand to Claude.  Globs rather than a file list for
#: D-045's reason: a writer added next month is in the surface the moment it
#: exists, including one added by an executor that never read this module.
WRITER_GLOBS: tuple[str, ...] = ("scripts/*.sh", "scripts/prompts/*.md")

#: Verbs that mark a **full-overwrite** write — one whose result is not a
#: function of the branch's diff.  Rewriting, regenerating and prepending all
#: qualify; plain ``append`` deliberately does not, because ``results/*.tsv``
#: is append-only *and* committed, and the point of the vocabulary is to
#: separate write modes, not to catch every mention of writing.
#:
#: This is a hand-typed list, which is the failure mode this module exists to
#: fix, so it does not stand alone: :func:`underived_declarations` re-derives
#: every already-declared path and goes red if the vocabulary missed one.  A
#: short vocabulary is then a failing test rather than a quiet undercount.
OVERWRITE_VOCABULARY: tuple[tuple[str, str], ...] = (
    (r"rewrit\w*", "rewrite"),
    (r"regenerat\w*", "regenerate"),
    (r"overwrit\w*", "overwrite"),
    (r"prepend\w*", "prepend"),
    (r"append-at-top", "append-at-top"),
    (r"snapshot", "snapshot"),
    (r"write_text", "write_text"),
    (r"덮어\w*", "overwrite-ko"),
)

_VERB = re.compile("|".join(pat for pat, _ in OVERWRITE_VOCABULARY), re.IGNORECASE)
_LABEL = tuple((re.compile(pat, re.IGNORECASE), label) for pat, label in OVERWRITE_VOCABULARY)

#: A backticked path in prose.  Prose in this repo spells paths in backticks
#: without exception; a bare-word fallback was tried and matched prose nouns
#: that happen to end in ``.md`` inside sentences about files in general.
_BACKTICKED = re.compile(r"`([^`\n]{1,120}?)`")

#: An ordered-list row.  Not an ornament: the REVIEW phase's read order is a
#: numbered list whose rows name ``CLAUDE.md`` and ``STATE.md`` one after the
#: other, and grouping them into one prose block attributed ``STATE.md``'s
#: "previous cycle's snapshot" to ``CLAUDE.md`` — a derived sixth entry that was
#: an artifact of the scope, not a finding.  Rows are rows in both list styles.
_ORDERED_ROW = re.compile(r"\d+[.)]\s")

#: Shell write targets whose destination is a literal.  ``>>`` is excluded by
#: the lookahead: appending is not the write mode in question.
_REDIRECT = re.compile(r"(?<![>&\d])>(?!>)\s*\"?([A-Za-z0-9_./-]+)")
_TEE = re.compile(r"\btee\s+(?!-a\b)(?:--\s+)?\"?([A-Za-z0-9_./-]+)")

#: Shell writes whose destination is a variable or a positional argument, so no
#: literal path can be attributed.  Declared rather than dropped, per D-042: an
#: instrument that can only clear work must name what it could not look at.
#: ``aggregate_results.sh`` writes ``RESULTS.md`` through ``sys.argv``, and is
#: the reason this field is not empty — the prose route catches that path
#: anyway, which is why two routes exist.
UNRESOLVED_TARGETS: tuple[tuple[str, str], ...] = (
    ("scripts/aggregate_results.sh",
     "writes via out_path.write_text(sys.argv[2]) — destination is passed in by "
     "the caller, so the literal never appears in the script"),
    ("scripts/telegram_poll.sh",
     "writes ${STATE_FILE}, a path under ~/.cache — outside the repo and "
     "therefore outside every fingerprint by construction"),
)

#: Heading that dates the rule :func:`branch_committed` is scoped to.  Parsed
#: out of the decision record so the epoch cannot drift from the decision.
RULE_ANCHOR = "## D-011"

#: Where the push-time guard lives, and the shape it is written in.  Read
#: rather than copied: a test against a copy of the guard passes forever after
#: someone edits the guard.
GUARD_FILE = "scripts/prompts/auto_research.md"
_GUARD_LINE = re.compile(r"git diff --name-only origin/main\.\.\.HEAD.*?grep -E '([^']+)'")


class WriterSurfaceError(RuntimeError):
    """The writer surface or the rule epoch could not be enumerated.

    Raised rather than defaulted, for :func:`tree_provenance._git`'s reason: an
    audit that degrades to "found nothing" reports a clean registry for a
    surface it never read.
    """


@dataclass(frozen=True)
class Site:
    """One statement, in one writer, that a path is written under overwrite."""

    path: str
    writer: str
    line: int
    verb: str
    quote: str

    def __str__(self) -> str:  # pragma: no cover - display only
        return f"{self.writer}:{self.line} [{self.verb}] {self.path}"


def _git(*args: str, root: Path | None = None) -> str:
    try:
        out = subprocess.run(
            ("git", *args),
            cwd=str(root or REPO_ROOT),
            capture_output=True,
            check=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError) as exc:
        raise WriterSurfaceError(f"git {' '.join(args)} failed: {exc}") from exc
    return out.stdout


def writer_surface(root: Path | None = None) -> tuple[str, ...]:
    """Repo-relative paths of every cron entry point and prompt file."""
    base = root or REPO_ROOT
    found: set[str] = set()
    for pattern in WRITER_GLOBS:
        found.update(str(p.relative_to(base)) for p in base.glob(pattern))
    if not found:
        raise WriterSurfaceError(f"no writers matched {WRITER_GLOBS} under {base}")
    return tuple(sorted(found))


def _units(text: str, is_markdown: bool):
    """Yield ``(line_no, body)`` for the smallest unit a claim can be read in.

    Markdown gets list rows and table rows one at a time, prose gets contiguous
    blocks, and the enclosing heading is prefixed to each because headings in
    these prompts routinely carry the target (``### 4c) Rewrite `STATE.md```,
    ``## Phase 3 — Append to `research/feed.md```).

    The unit size is the whole difficulty.  Section-wide scope attributes a
    verb to every path in a bullet list that merely *inventories* files, which
    made ``CLAUDE.md`` and ``README.md`` read as full-overwrite artifacts off
    the repo-layout section.  Line-wide scope drops ``research/feed.md``, whose
    heading names it and whose body states the verb two lines down.  Rows alone
    plus heading-prefixed blocks is the scope that holds both ends.
    """
    if not is_markdown:
        yield (1, text)
        return
    heading, buf, buf_start = "", [], 0
    for lineno, line in enumerate(text.splitlines(), 1):
        stripped = line.strip()
        if line.startswith("#"):
            if buf:
                yield (buf_start, heading + "\n" + "\n".join(buf))
                buf = []
            heading = stripped
            yield (lineno, heading)
        elif stripped.startswith(("-", "*", "|")) or _ORDERED_ROW.match(stripped):
            if buf:
                yield (buf_start, heading + "\n" + "\n".join(buf))
                buf = []
            yield (lineno, heading + "\n" + line)
        elif stripped:
            if not buf:
                buf_start = lineno
            buf.append(line)
        elif buf:
            yield (buf_start, heading + "\n" + "\n".join(buf))
            buf = []
    if buf:
        yield (buf_start, heading + "\n" + "\n".join(buf))


def _verb_of(body: str) -> str | None:
    for pattern, label in _LABEL:
        if pattern.search(body):
            return label
    return None


def _shell_targets(text: str) -> set[str]:
    """Literal destinations of shell writes — redirects and non-append tee."""
    out: set[str] = set()
    for pattern in (_REDIRECT, _TEE):
        out.update(m.group(1) for m in pattern.finditer(text))
    return out


def overwrite_sites(root: Path | None = None) -> list[Site]:
    """Every statement, anywhere in the writer surface, that a **tracked** path
    is written under a full-overwrite verb.

    Two routes, because the writers are two languages.  Prose (``.md``) is
    scanned lexically against :data:`OVERWRITE_VOCABULARY`; shell is scanned
    structurally, since a redirect *is* the overwrite and needs no verb.  The
    tracked-ness filter is the same one :func:`citation_audit.tracked_files`
    applies and for the same reason: an untracked path cannot reach the pushed
    tree, so it cannot be the subject of a claim about that tree.
    """
    base = root or REPO_ROOT
    tracked = set(tracked_paths(root))
    sites: list[Site] = []
    for writer in writer_surface(root):
        try:
            text = (base / writer).read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):  # pragma: no cover - defensive
            continue
        if writer.endswith(".md"):
            for lineno, body in _units(text, True):
                verb = _verb_of(body)
                if verb is None:
                    continue
                for match in _BACKTICKED.finditer(body):
                    raw = match.group(1).strip()
                    for cand in (raw, raw.replace("<repo>/", "")):
                        if cand in tracked:
                            sites.append(Site(cand, writer, lineno, verb,
                                              " ".join(body.split())[:120]))
        else:
            for target in _shell_targets(text):
                if target in tracked:
                    sites.append(Site(target, writer, 1, "redirect", target))
    return sorted(set(sites), key=lambda s: (s.path, s.writer, s.line))


def rule_epoch(root: Path | None = None) -> str:
    """The date D-011 was accepted, parsed out of the decision record.

    Typed here it would be a second copy of a fact the record already holds,
    and copies of dates are how an epoch outlives the rule it belongs to.
    """
    base = root or REPO_ROOT
    text = (base / "docs" / "decisions.md").read_text(encoding="utf-8")
    for line in text.splitlines():
        if line.startswith(RULE_ANCHOR):
            match = re.search(r"(\d{4}-\d{2}-\d{2})", line)
            if match:
                return match.group(1)
    raise WriterSurfaceError(f"no dated {RULE_ANCHOR} heading in docs/decisions.md")


def _branch_refs(root: Path | None = None) -> tuple[str, ...]:
    raw = _git("for-each-ref", "--format=%(refname)",
               "refs/remotes/origin/autoresearch", root=root)
    return tuple(sorted(r for r in raw.split("\n") if r.strip()))


def _committed_on_branches(since: str | None, root: Path | None = None) -> set[str]:
    out: set[str] = set()
    for ref in _branch_refs(root):
        args = ["log", "--name-only", "--pretty=", f"origin/main..{ref}"]
        if since:
            args.insert(1, f"--since={since}")
        for path in _git(*args, root=root).split("\n"):
            if path.strip():
                out.add(path.strip())
    return out


def branch_committed(root: Path | None = None) -> frozenset[str]:
    """Paths ``autoresearch/*`` branches commit **in the D-011 era**.

    The window opens the day after :func:`rule_epoch`: D-011's own cycle
    committed snapshot files while writing the rule against them, so including
    its date would classify the three files the rule is *about* as durable
    record.  Everything earlier is reported by :func:`pre_epoch_commits`.
    """
    epoch = rule_epoch(root)
    year, month, day = (int(p) for p in epoch.split("-"))
    day += 1  # git parses an over-range day; no calendar arithmetic needed
    return frozenset(_committed_on_branches(f"{year:04d}-{month:02d}-{day:02d}", root))


def derived_local_only(root: Path | None = None) -> dict[str, list[Site]]:
    """Tracked, full-overwrite-written, never committed by a branch this era.

    The population :data:`tree_provenance.DECLARED_LOCAL_ONLY` is a hand-typed
    statement of.
    """
    committed = branch_committed(root)
    out: dict[str, list[Site]] = {}
    for site in overwrite_sites(root):
        if site.path not in committed:
            out.setdefault(site.path, []).append(site)
    return dict(sorted(out.items()))


def unregistered_local_only(root: Path | None = None) -> list[str]:
    """Derived local-only paths nobody declared — D-046's direction."""
    return sorted(set(derived_local_only(root)) - set(DECLARED_LOCAL_ONLY))


def underived_declarations(root: Path | None = None) -> list[str]:
    """Declared paths the derivation did **not** re-find.

    The mirror of :func:`unregistered_local_only`, and the reason a hand-typed
    :data:`OVERWRITE_VOCABULARY` is tolerable: a verb the vocabulary lacks makes
    this non-empty, so the scan's blindness is a red test rather than a shorter
    answer.  D-046's ``derived_citations`` had no such mirror and needed four
    drafts before its scan stopped under-counting.
    """
    derived = set(derived_local_only(root))
    return sorted(p for p in DECLARED_LOCAL_ONLY if p not in derived)


def push_guard_pattern(root: Path | None = None) -> str | None:
    """The alternation the Phase 3 push check greps for, read from the prompt.

    ``None`` once the guard stops being a literal — see
    :func:`unguarded_declarations`.
    """
    base = root or REPO_ROOT
    text = (base / GUARD_FILE).read_text(encoding="utf-8")
    match = _GUARD_LINE.search(text)
    return match.group(1) if match else None


def guard_is_derived(root: Path | None = None) -> bool:
    """Does the push check call this module instead of restating the list?"""
    base = root or REPO_ROOT
    text = (base / GUARD_FILE).read_text(encoding="utf-8")
    return f"{__name__.rsplit('.', 1)[0]}.local_only_audit staged" in text \
        or "eval.mppi_sandbox.local_only_audit staged" in text


def unguarded_declarations(root: Path | None = None) -> list[str]:
    """Declared local-only paths the push-time guard does not match.

    D-011's rule has two halves — write it locally, never stage it — and for
    thirty-odd cycles only the first half had a mechanism.  The second was a
    grep whose alternation was typed when the list had three entries and never
    revisited when :data:`tree_provenance.DECLARED_LOCAL_ONLY` grew to five, so
    ``TODO.md`` and ``research/feed.md`` were paths the executor is told never
    to commit and was not stopped from committing.  That is the finding this
    module was written to produce and it is now fixed at the source: the guard
    calls :func:`staged_declarations`, so the registry has exactly one
    statement of itself.

    Empty when the guard is derived — there is nothing left for a copy to be
    short of.  Non-empty means someone put a literal back.
    """
    if guard_is_derived(root):
        return []
    pattern = push_guard_pattern(root)
    if pattern is None:
        raise WriterSurfaceError(
            f"{GUARD_FILE} has neither a derived nor a literal push guard")
    compiled = re.compile(pattern)
    return sorted(p for p in DECLARED_LOCAL_ONLY if not compiled.search(p))


def staged_declarations(ref: str = "HEAD", root: Path | None = None) -> list[str]:
    """Declared local-only paths this branch actually commits, vs ``origin/main``.

    :func:`tree_provenance.undeclared_drift` compares the worktree against
    ``HEAD`` and exempts these five, so it is silent in both directions here:
    staging a snapshot file removes the drift it looks for *and* the path is on
    its allow-list.  The violation is only visible against the merge base, which
    is what this reads.
    """
    raw = _git("diff", "--name-only", f"origin/main...{ref}", root=root)
    changed = {p.strip() for p in raw.split("\n") if p.strip()}
    return sorted(changed & set(DECLARED_LOCAL_ONLY))


def pre_epoch_commits(root: Path | None = None) -> dict[str, list[str]]:
    """``{path: [branch, ...]}`` for declared paths committed **before** D-011.

    Kept visible rather than filtered away.  These are live branches in the
    review queue carrying the exact commits D-011 was written to stop, and they
    are the evidence that :func:`branch_committed`'s window needs an epoch at
    all — a filter that erased them would be erasing its own justification.
    """
    epoch = rule_epoch(root)
    out: dict[str, list[str]] = {}
    for ref in _branch_refs(root):
        branch = ref.split("refs/remotes/origin/", 1)[-1]
        raw = _git("log", "--name-only", "--pretty=", f"--until={epoch}",
                   f"origin/main..{ref}", root=root)
        for path in {p.strip() for p in raw.split("\n") if p.strip()}:
            if path in DECLARED_LOCAL_ONLY:
                out.setdefault(path, []).append(branch)
    return {k: sorted(v) for k, v in sorted(out.items())}


def report() -> str:  # pragma: no cover - display only
    lines = [f"writers: {len(writer_surface())}  epoch: {rule_epoch()}"]
    derived = derived_local_only()
    lines.append(f"derived local-only: {len(derived)}  declared: {len(DECLARED_LOCAL_ONLY)}")
    for path, sites in derived.items():
        mark = " " if path in DECLARED_LOCAL_ONLY else "!"
        lines.append(f" {mark} {path:<24} {len(sites):>2} site(s)  "
                     f"{', '.join(sorted({s.verb for s in sites}))}")
    for label, rows in (
        ("unregistered (derived, not declared)", unregistered_local_only()),
        ("underived (declared, not found)", underived_declarations()),
        ("unguarded by the push check", unguarded_declarations()),
        ("staged on this branch", staged_declarations()),
    ):
        lines.append(f"{label}: {', '.join(rows) if rows else 'none'}")
    lines.append(f"push guard: {'derived' if guard_is_derived() else push_guard_pattern()}")
    for path, branches in pre_epoch_commits().items():
        lines.append(f"pre-epoch: {path} on {len(branches)} branch(es)")
    return "\n".join(lines)


def _main(argv: list[str] | None = None) -> int:  # pragma: no cover - CLI
    import argparse

    ap = argparse.ArgumentParser(
        prog="python3 -m eval.mppi_sandbox.local_only_audit",
        description="Derive the local-only population from its writers.",
    )
    sub = ap.add_subparsers(dest="cmd")
    sub.add_parser("report", help="full audit (default)")
    p_staged = sub.add_parser(
        "staged", help="D-011's push guard: fail if a declared local-only path "
                       "is committed on this branch")
    p_staged.add_argument("--ref", default="HEAD")
    args = ap.parse_args(argv)

    if args.cmd != "staged":
        print(report())
        return 0

    staged = staged_declarations(args.ref)
    if not staged:
        print(f"OK: no declared local-only path staged on {args.ref} "
              f"({len(DECLARED_LOCAL_ONLY)} declared, none committed)")
        return 0
    print(f"ERROR: snapshot file staged on branch — unstage before push: "
          f"{', '.join(staged)}")
    print("=> D-011: full-overwrite artifacts committed on a branch re-dirty "
          "every other open PR on merge.")
    return 1


if __name__ == "__main__":  # pragma: no cover - CLI
    raise SystemExit(_main())

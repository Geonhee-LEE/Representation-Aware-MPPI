"""The declared full-suite target list, stated once.

D-402 counted this tuple **seven times** in the repo — four machine-readable
copies (:mod:`predicate_vacuity`, :mod:`guard_vacuity`,
``tests/test_receipt_scope.py``, ``tests/test_suite_coverage.py``) and three in
the constitution (``scripts/prompts/auto_research.md``).  The comment above one
of them confessed the shape outright: *"Deliberately the same tuple*
:mod:`guard_vacuity` *uses, so the two censuses describe the same suite."*  That
is a registry admitting it is not one — D-047's exact failure form, where a
hand-typed ``grep`` fell behind the five-path registry it was copying and left
``TODO.md`` and ``research/feed.md`` unguarded.

This module is the single statement.  The four machine-readable copies derive
from it, so "the two censuses describe the same suite" becomes a fact about
imports rather than a promise in a docstring.

**Why this list does not go stale the way a census does.**  D-401 priced a
declared-suite *test count* (``4119``) and found it moves on every added test —
the ``+1`` shape behind an 8-cycle RED streak (D-399).  This is not that: it is
three **target paths**, and adding a test does not move it.  Only adding a test
*directory* does, which is rare and is exactly the event a registry should force
someone to notice.

The constitution's three prose copies are deliberately left alone: prose cannot
import, and rewriting the loop's own instructions to point at a Python symbol
would make the runbook unreadable to the human who maintains it.  What this
module buys is that the four copies a *test* can reach now have one source.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

#: The declared full-suite target list, relative to the repo root.
#:
#: Fast half only — the slow half costs ~8 min (see ``eval/conftest.py``), so a
#: guard that only fires under ``--slow`` scores ``NEVER_FIRED`` against this
#: suite.  That is a known bound on every reading taken from it, reported by
#: the censuses rather than left silent.
DECLARED_SUITE = (
    "eval/mppi_sandbox/tests/",
    "eval/tests/test_path_tracking_metrics.py",
    "eval/tests/test_run_metrics.py",
)


@dataclass(frozen=True)
class SuiteScope:
    """How much of :data:`DECLARED_SUITE` an invocation actually named.

    The population here is the receipt's **argv**, which is a different
    question from :mod:`suite_coverage`'s and has to be, because that module
    cannot reach it.  ``suite_coverage`` subtracts ``skipped``/``deselected``
    from what pytest *collected*, and pytest only collects what it was pointed
    at — so a target that was never named appears in no count at all and the
    coverage reading comes back clean.  D-400 measured exactly that inversion:
    a nine-test one-file receipt graded ``none left out`` while the 3954-test
    receipt on the same tree graded ``96.0%; 164 uncovered``.  **Narrowing the
    invocation made it read cleaner.**
    """

    #: Declared targets the command named (directly or via a parent directory).
    named: tuple[str, ...]
    #: Declared targets it did not.  Empty ⇒ the invocation was full.
    missing: tuple[str, ...]
    #: Was there an argv to read at all?  ``False`` on receipts written before
    #: :attr:`push_preflight.Receipt.command` existed.
    asked: bool

    @property
    def full(self) -> bool:
        """Did the invocation name every declared target?

        ``False`` when the command is unrecorded: an unanswerable question is
        not a pass.  That is :attr:`push_preflight.Receipt.worktree`'s rule for
        missing per-path digests, applied to the other missing field, and it
        fails in the closed direction — the only direction this gate may fail.
        """
        return self.asked and not self.missing

    def describe(self) -> str:
        if not self.asked:
            return "the receipt records no command, so which targets ran cannot be asked"
        if not self.missing:
            return f"all {len(self.named)} declared targets named"
        return (
            f"{len(self.named)}/{len(DECLARED_SUITE)} declared targets named; "
            f"never invoked: {', '.join(self.missing)}"
        )


def _covers(token: str, target: str) -> bool:
    """Does argv *token* point pytest at *target*?

    Equality, or *token* being a parent directory of it — ``eval/`` is a
    legitimate way to run all three, and refusing it would push cycles toward
    typing the list a fifth time to satisfy the guard.
    """
    tok = token.lstrip("./").rstrip("/")
    tgt = target.rstrip("/")
    return tok == tgt or tgt.startswith(tok + "/")


def scope_of(command: Sequence[str]) -> SuiteScope:
    """Grade an invocation's argv against the registry.

    Option flags and their values are not filtered out: a flag cannot equal a
    declared path and cannot be a parent directory of one, so it never matches,
    and a filter would need its own list of which flags take arguments — a
    second hand-typed census to keep in step with pytest (D-047's shape, which
    this module exists to stop reproducing).
    """
    tokens = tuple(command)
    if not tokens:
        return SuiteScope(named=(), missing=DECLARED_SUITE, asked=False)
    named = tuple(t for t in DECLARED_SUITE if any(_covers(k, t) for k in tokens))
    missing = tuple(t for t in DECLARED_SUITE if t not in named)
    return SuiteScope(named=named, missing=missing, asked=True)

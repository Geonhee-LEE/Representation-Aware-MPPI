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

"""The declared suite is stated once, and the copies that cannot import agree.

D-402 counted seven copies of the same three strings and stopped there — it
measured their *existence*, not their *equality*.  Its own limitation section
named that gap and said the consolidation cycle's first test must close it.
This is that test.

The four machine-readable copies are now derivations (``DEFAULT_SUITE =
DECLARED_SUITE``), so their agreement is enforced by the import system and the
tests below only have to prove the hand copies are *gone* — a source scan, not a
value comparison, because two names bound to one object cannot disagree.

The three constitution copies are the interesting half.  Prose cannot import, so
those are exactly the copies that can still drift, and they are the ones D-047's
failure form actually bit: a hand-typed ``grep`` fell behind a five-path
registry and left two files unguarded for thirty-odd cycles.  The scan below
gives that drift a place to go red.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from eval.mppi_sandbox.declared_suite import DECLARED_SUITE

REPO = Path(__file__).resolve().parents[3]

#: The modules that used to hand-type the tuple (D-402's four machine-readable
#: copies).  Each must now reference the registry instead.
DERIVED_SITES = (
    "eval/mppi_sandbox/predicate_vacuity.py",
    "eval/mppi_sandbox/guard_vacuity.py",
    "eval/mppi_sandbox/tests/test_receipt_scope.py",
    "eval/mppi_sandbox/tests/test_suite_coverage.py",
)

#: The constitution's prose copies — the loop's own runbook.  These cannot
#: import, so they are checked textually.
CONSTITUTION = "scripts/prompts/auto_research.md"


class TestTheRegistryIsTheOnlyStatement:
    """No module still writes the three strings out by hand."""

    @pytest.mark.parametrize("relpath", DERIVED_SITES)
    def test_site_references_the_registry(self, relpath):
        src = (REPO / relpath).read_text()
        assert "DECLARED_SUITE" in src, (
            f"{relpath} no longer references the registry — if the derivation "
            f"was removed, the hand copy is back and D-402 has regressed."
        )

    @pytest.mark.parametrize("relpath", DERIVED_SITES)
    def test_site_does_not_rehand_type_the_tuple(self, relpath):
        """The literal three-string run must not reappear as a group.

        Individual paths still occur legitimately (an ``--ignore`` entry, a
        docstring).  What must not recur is all three adjacent, which is the
        copy shape itself.
        """
        src = (REPO / relpath).read_text()
        pattern = re.compile(
            r'"eval/mppi_sandbox/tests/"\s*,\s*'
            r'"eval/tests/test_path_tracking_metrics\.py"\s*,\s*'
            r'"eval/tests/test_run_metrics\.py"'
        )
        assert not pattern.search(src), (
            f"{relpath} hand-types the declared suite again; import "
            f"DECLARED_SUITE from eval.mppi_sandbox.declared_suite instead."
        )


class TestTheCopiesThatCannotImportStillAgree:
    """The constitution's prose copies are checked textually or not at all."""

    def test_every_constitution_invocation_names_the_declared_targets(self):
        text = (REPO / CONSTITUTION).read_text()

        # Each pytest invocation in the runbook that runs the receipt suite.
        # They span lines (one is a shell continuation), so normalise first.
        flat = re.sub(r"\\\s*\n\s*", " ", text)
        invocations = [
            line
            for line in flat.splitlines()
            if "pytest" in line and "test_run_metrics.py" in line
        ]
        assert invocations, (
            "the constitution no longer contains a recognisable suite "
            "invocation — if the runbook moved, this guard is describing "
            "nothing (D-091)."
        )

        for inv in invocations:
            for target in DECLARED_SUITE:
                assert target in inv, (
                    f"constitution invocation drifted from the registry: "
                    f"{target!r} missing from {inv.strip()!r}"
                )

    def test_the_registry_has_not_silently_grown_past_the_prose(self):
        """A new target added in Python but not in the runbook goes red here.

        This is the direction D-047 actually failed in: the registry grew to
        five paths, the hand-typed copy stayed at three, and nothing said so.
        """
        text = (REPO / CONSTITUTION).read_text()
        missing = [t for t in DECLARED_SUITE if t not in text]
        assert not missing, (
            f"DECLARED_SUITE names {missing} but the constitution's suite "
            f"invocations do not — the runbook a human follows would run a "
            f"narrower suite than the censuses declare."
        )

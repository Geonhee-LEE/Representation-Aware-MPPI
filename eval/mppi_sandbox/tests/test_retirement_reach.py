"""Q-194's backward half: a retired entry must name the entry that retired it.

The gate is :func:`retirement_reach.unbacked_retirements` and its population is
currently empty — which is the point.  D-449 repaired D-430 / D-433 / D-440 by
hand; these tests are what makes the *next* retirement unable to be written
without its back-reference.

The advisory census is pinned as an inequality rather than a literal, because
it is over-reporting by construction and a literal would go red every time
somebody writes the word 은퇴 in a decision.  What is pinned is the property
the module claims: the advisory strictly over-reports relative to the gate.
"""

from __future__ import annotations

from eval.mppi_sandbox import retirement_reach as rr


def test_every_retired_entry_names_its_retirer():
    """The gate.  Empty population; a bare ``Status: retired`` turns it red."""
    unbacked = rr.unbacked_retirements()
    assert unbacked == (), (
        "retired entries whose Status line names no other decision — the "
        "correction is stated but unreachable: "
        + ", ".join(f"{e.name} ({e.doc}:{e.line})" for e in unbacked)
    )


def test_the_gate_has_a_nonempty_population_to_be_about():
    """A gate over an empty *input* is vacuous, not clean (cf. D-043's lesson).

    ``unbacked_retirements`` returning ``()`` is only meaningful if
    ``retired_entries`` found something to check.  Eleven entries carry a
    retirement verb in their own Status line as of D-450; pinned as a lower
    bound so future retirements do not have to touch this test.
    """
    retired = rr.retired_entries()
    assert len(retired) >= 11, f"only {len(retired)} retired entries found — parser regression?"
    assert all(rr.names_a_retirement_verb(e.status_line) for e in retired)


def test_d449_three_entries_are_in_the_retired_population_and_backed():
    """The three entries that motivated Q-194, read through the instrument."""
    by_name = {e.name: e for e in rr.retired_entries()}
    for name, retirer in (("D-430", "D-446"), ("D-433", "D-446"), ("D-440", "D-446")):
        assert name in by_name, f"{name} is not read as retired — D-449's repair regressed"
        refs = by_name[name].referenced_decisions(by_name[name].status_line)
        assert retirer in refs, f"{name}'s Status line no longer names {retirer}: {sorted(refs)}"


def test_entry_parser_covers_both_scanned_docs():
    """449 entries as of D-450; both docs contribute, so neither is silently dropped."""
    docs = {e.doc for e in rr.entries()}
    assert docs == {"docs/decisions.md"} or "docs/decisions.md" in docs
    assert len(rr.entries()) >= 449


def test_advisory_strictly_over_reports_relative_to_the_gate():
    """The measured refutation of Q-194's "오탐이 없다" lean, held as a property.

    If the line-level scan ever *stopped* over-reporting the module docstring's
    central claim would be wrong, and the reader should be told.
    """
    advisory = rr.retirement_statements()
    assert len(advisory) > len(rr.retired_entries()) * 4, (
        f"advisory census is {len(advisory)}; the docstring claims it over-reports "
        "by a wide margin — re-read the docstring if this is now false"
    )
    assert all(r.source != r.target for r in advisory), "self-reference must be dropped"

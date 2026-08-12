"""The quoted-count audit, and the one property that keeps it from acquitting.

The reading this branch banks is in
:func:`test_no_quoted_count_inside_the_reach_is_unmeasured` — STATE carried
"audit the last month's quoted counts" as its top actionable for three cycles on
the suspicion that D-212's broken summary line had been quoted into a journal.
It had not been, and this file is where that answer stops being prose.
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta

import pytest

from eval.mppi_sandbox import push_preflight as pp
from eval.mppi_sandbox import quoted_counts as qc
from eval.mppi_sandbox import receipt_store as rs


def _journal(root, name: str, body: str) -> None:
    month = root / qc.JOURNAL_DIR / "2026-08"
    month.mkdir(parents=True, exist_ok=True)
    (month / name).write_text(body)


def _receipt(passed: int, head: str = "deadbeef") -> pp.Receipt:
    return pp.Receipt(
        head=head,
        worktree_fingerprint=f"{passed:064d}",
        committed_fingerprint=f"{passed:064d}",
        returncode=0,
        counts={"passed": passed, "skipped": 0},
    )


def _archive(root, receipt: pp.Receipt) -> None:
    path = rs.path_for(receipt.worktree_fingerprint, root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(receipt.to_json())


@pytest.fixture
def pinned_reach(monkeypatch):
    """A store whose evidence begins before every fixture journal below.

    The real :func:`quoted_counts.reach` dates receipts by ``git show`` on their
    ``head``; a tmp_path fixture has no git object for that sha, so without this
    every fixture quote would grade ``OUT_OF_REACH`` and the verdict branches
    under test would never be reached.  Pinned rather than faked into git: the
    dating logic has its own test below.
    """
    boundary = datetime(2026, 8, 1, tzinfo=qc.KST)
    monkeypatch.setattr(qc, "reach", lambda root=None: boundary)
    return boundary


def test_cycle_of_reads_the_name_not_the_mtime(tmp_path):
    month = tmp_path / "journal" / "2026-08"
    month.mkdir(parents=True)
    path = month / "12-09-the-missing-piece.md"
    path.write_text("x")
    assert qc.cycle_of(path) == datetime(2026, 8, 12, 9, tzinfo=qc.KST)


def test_a_path_that_names_no_cycle_is_not_one(tmp_path):
    month = tmp_path / "journal" / "2026-08"
    month.mkdir(parents=True)
    for name in ("README.md", "notes.md", "9-9-short.md"):
        assert qc.cycle_of(month / name) is None


def test_the_scan_ignores_counts_too_small_to_be_the_suite(tmp_path):
    _journal(tmp_path, "12-09-a.md", "ran 2573 passed here\nand 12 passed there\n")
    values = [q.value for q in qc.quotes(tmp_path)]
    assert values == [2573]


def test_a_value_quoted_again_later_is_restated_not_reread(tmp_path, pinned_reach):
    _journal(tmp_path, "12-08-first.md", "green: 2556 passed\n")
    _journal(tmp_path, "12-09-second.md", "as 08:00 reported, 2556 passed\n")
    _archive(tmp_path, _receipt(2556))
    verdicts = [(f.quote.path[-14:], f.verdict) for f in qc.audit(tmp_path)]
    assert verdicts == [
        ("12-08-first.md", qc.CORROBORATED),
        ("2-09-second.md", qc.RESTATED),
    ]


def test_a_count_no_receipt_carries_is_the_finding(tmp_path, pinned_reach):
    _journal(tmp_path, "12-09-a.md", "green: 2573 passed\n")
    _archive(tmp_path, _receipt(2556))
    findings = qc.audit(tmp_path)
    assert [f.verdict for f in findings] == [qc.UNCORROBORATED]
    assert findings[0].is_defect
    assert qc.defects(tmp_path) == findings


def test_a_partial_run_token_withdraws_the_conviction(tmp_path, pinned_reach):
    _journal(tmp_path, "12-09-a.md", "census slice green (319 passed, 4 skipped)\n")
    _archive(tmp_path, _receipt(2556))
    findings = qc.audit(tmp_path)
    assert [f.verdict for f in findings] == [qc.PARTIAL]
    assert not findings[0].is_defect


def test_a_token_can_never_manufacture_a_corroboration(tmp_path, pinned_reach):
    """The load-bearing asymmetry: ``PARTIAL`` is reachable only from the branch
    that would otherwise convict, so no token turns an unmeasured number into a
    measured one.  Asserted over every token rather than over one example."""
    _archive(tmp_path, _receipt(2556))
    for index, token in enumerate(qc.PARTIAL_TOKENS):
        root = tmp_path / f"case{index}"
        (root / "results").mkdir(parents=True)
        _archive(root, _receipt(2556))
        _journal(root, "12-09-a.md", f"the {token} ran and 2556 passed\n")
        verdicts = {f.verdict for f in qc.audit(root)}
        assert verdicts == {qc.CORROBORATED}, token


def test_a_quote_older_than_the_evidence_is_not_graded_unsupported(tmp_path):
    """Absence of evidence is reported as absence of evidence.

    ``reach`` is empty here (no datable receipt), which is exactly the state the
    branch was in before the store existed — and the whole month of quotes that
    predates it must not read as findings."""
    _journal(tmp_path, "12-09-a.md", "green: 2573 passed\n")
    findings = qc.audit(tmp_path)
    assert [f.verdict for f in findings] == [qc.OUT_OF_REACH]
    assert qc.defects(tmp_path) == ()


def test_an_undatable_receipt_does_not_extend_the_reach(tmp_path):
    """A head no git object backs cannot date its receipt, and the conservative
    direction is to let it grade nothing rather than to invent a boundary."""
    _archive(tmp_path, _receipt(2556, head="0" * 40))
    assert qc.reach(tmp_path) is None


def test_an_unreadable_archive_is_no_evidence_rather_than_an_error(tmp_path):
    _archive(tmp_path, _receipt(2556))
    (rs.store_dir(tmp_path) / "garbage.json").write_text("{not json")
    assert [r.counts["passed"] for r in qc.archived(tmp_path)] == [2556]


def test_a_misfiled_receipt_still_counts_as_evidence_of_its_own_counts(tmp_path):
    """Deliberately weaker than :func:`receipt_store.recall`, which refuses a
    receipt whose filename does not match its fingerprint.  That refusal
    protects a *push*; this pass only asks whether a number was ever measured,
    and a misfiled receipt is still a record that it was."""
    receipt = _receipt(2556)
    path = rs.store_dir(tmp_path) / "misfiled.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(receipt.to_json())
    assert json.loads(path.read_text())["counts"]["passed"] == 2556
    assert [r.counts["passed"] for r in qc.archived(tmp_path)] == [2556]


def test_no_quoted_count_inside_the_reach_is_unmeasured():
    """The banked answer to STATE #1, taken over the real repo.

    D-212's broken summary line printed one shard's count as the run's between
    2026-08-12 07:00 and 08:00.  The question this audit was carried three
    cycles to answer is what that line was quoted into, and the answer is
    **nothing**: every count quoted inside the store's reach is either carried
    by an archived receipt or says on its own line that it is a partial run.

    This test goes red if a future cycle quotes a full-suite count that no
    receipt supports — which is the failure the audit exists for, and the only
    direction it can detect."""
    unsupported = qc.defects()
    assert unsupported == (), "\n".join(
        f"{f.quote.value} passed at {f.quote.path}:{f.quote.line}" for f in unsupported
    )


def test_the_reach_is_a_boundary_the_receipts_derive_not_a_constant():
    """The store began on 2026-08-11 22:04 (D-200), so the reach must land at or
    after it and at or before now — a hard-coded date would go stale silently as
    receipts age out, which is D-047's shape."""
    boundary = qc.reach()
    assert boundary is not None, "the real store holds no datable receipt"
    assert boundary >= datetime(2026, 8, 11, 21, tzinfo=qc.KST)
    assert boundary <= datetime.now(qc.KST) + timedelta(hours=1)

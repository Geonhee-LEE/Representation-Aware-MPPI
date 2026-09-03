"""The receipt store keeps a measurement past the cycle that paid for it.

The pins that matter here are not "does a dict round-trip".  They are the two
properties that decide whether the store is worth having at all:

1. archiving must not move the fingerprint the receipt is keyed by (otherwise
   every entry invalidates itself and the store can never hit), and
2. the key must stay *derived* — a file that does not contain the fingerprint
   its name claims is not a weaker receipt, it is not evidence.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from eval.mppi_sandbox import push_preflight as pp
from eval.mppi_sandbox import receipt_store as rs
from eval.mppi_sandbox import tree_provenance as tp


#: The sentinel `worktree` payload every fixture receipt here carries.  It is
#: what makes a leaked entry identifiable in the production store.
_FIXTURE_WORKTREE = {"eval/x.py": "d1"}


def _receipt(fingerprint: str = "f" * 40, **kw) -> pp.Receipt:
    base = dict(
        head="abc1234",
        worktree_fingerprint=fingerprint,
        committed_fingerprint="c" * 40,
        returncode=0,
        counts={"passed": 2496},
        command=("python3", "-m", "pytest"),
        worktree={"eval/x.py": "d1"},
        failed_nodes=(),
        duration_seconds=1220.5,
    )
    base.update(kw)
    return pp.Receipt(**base)


def test_archive_then_recall_returns_the_same_receipt(tmp_path: Path) -> None:
    receipt = _receipt()
    rs.archive(receipt, root=tmp_path)
    got = rs.recall(receipt.worktree_fingerprint, root=tmp_path)
    assert got is not None
    assert got.counts == {"passed": 2496}
    assert got.duration_seconds == pytest.approx(1220.5)


def test_the_file_is_named_by_the_tree_not_by_the_cycle(tmp_path: Path) -> None:
    """Two trees ⇒ two entries; the same tree twice ⇒ one.

    This is the property that makes recall a lookup rather than a search: no
    hour, branch, or ordinal appears in the key, so nothing can be "close".
    """
    rs.archive(_receipt("a" * 40), root=tmp_path)
    rs.archive(_receipt("b" * 40), root=tmp_path)
    rs.archive(_receipt("a" * 40, counts={"passed": 9}), root=tmp_path)

    assert len(rs.entries(root=tmp_path)) == 2
    again = rs.recall("a" * 40, root=tmp_path)
    assert again is not None and again.counts == {"passed": 9}, (
        "a re-archive of the same tree must win: both receipts describe that "
        "tree, so keeping the older one is the wrong direction"
    )


def test_recall_misses_on_a_tree_nobody_measured(tmp_path: Path) -> None:
    rs.archive(_receipt("a" * 40), root=tmp_path)
    assert rs.recall("b" * 40, root=tmp_path) is None


def test_a_misfiled_receipt_is_not_evidence(tmp_path: Path) -> None:
    """The key is derived from the contents; break that link and it is gone.

    Reached by writing a well-formed, green receipt under the *wrong* name —
    the shape a rename or a hand-edit produces.  A store that answered here
    would license a push using a measurement of a different tree, which is the
    exact defect `push_preflight` exists to refuse.
    """
    path = rs.path_for("a" * 40, root=tmp_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(_receipt("b" * 40).to_json())

    assert rs.recall("a" * 40, root=tmp_path) is None


def test_a_truncated_write_is_not_evidence(tmp_path: Path) -> None:
    path = rs.path_for("a" * 40, root=tmp_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(_receipt("a" * 40).to_json()[:40])

    assert rs.recall("a" * 40, root=tmp_path) is None


def test_archiving_does_not_move_the_fingerprint_it_keys_on() -> None:
    """The load-bearing one: the store must be invisible to the tree stamp.

    `push_preflight.check` compares `worktree_fingerprint`, which covers
    tracked files.  If archiving changed that value, the receipt would be stale
    against its own key the instant it was written and the store could never
    hit.  Measured against the live repo rather than a `tmp_path` fixture,
    because the claim is about *this* repository's ignore rules.
    """
    before = tp.stamp().worktree_fingerprint
    receipt = _receipt(before)
    # D-497: `before` is the *live* tree's fingerprint, which is exactly the
    # fingerprint a real `push_preflight record` run for this same tree
    # archives under. When this test runs as part of such a run (any full
    # suite invocation on an unchanged tree — the normal case), a genuine
    # receipt may already occupy this path. `rs.archive` overwrites by design
    # (see its docstring), but the unconditional `unlink()` this test used to
    # do in `finally` went further and *deleted* that genuine receipt outright
    # — observed 2026-09-03: it made `quoted_counts`'s corroboration check
    # flap red mid-run, because the real archived count vanished the instant
    # this test executed in a concurrent shard. Snapshot whatever was there
    # (or wasn't) and restore it exactly, rather than assuming the path was
    # empty.
    path = rs.path_for(before)
    prior = path.read_bytes() if path.exists() else None
    archived = rs.archive(receipt)
    try:
        after = tp.stamp().worktree_fingerprint

        assert after == before
        assert rs.recall(before) is not None
    finally:
        # This test is the one that *must* write to the production store — the
        # claim is about this repo's ignore rules, so a `tmp_path` store would
        # assert nothing. Restore whatever occupied this path before the test
        # ran: a real receipt for this tree if one existed, otherwise nothing.
        if prior is None:
            archived.unlink(missing_ok=True)
        else:
            archived.write_bytes(prior)


def test_the_store_is_untracked_in_this_repo() -> None:
    """A committed store is not slower — it is a cache that never hits.

    The failure is silent (writes succeed, reads miss, nothing errors), so it
    gets asserted here rather than left for a future cycle to rediscover.
    """
    assert rs.tracked_conflict() == (), (
        "results/readings/ is tracked — every archive would now change the "
        "tracked tree and invalidate the receipt it just stored"
    )


def test_no_fixture_receipt_survives_in_the_production_store() -> None:
    """The store `push_licence` reads must hold measurements, not fixtures.

    Q-180 filed this as harmless on the reasoning that the leaked entries carry
    synthetic fingerprints and so can never be recalled.  That reasoning was
    wrong in the one place it mattered: the two leakers keyed on
    ``tp.stamp().worktree_fingerprint`` — the **live** tree — so
    ``recall_current()`` hit and ``licence_path()`` pointed straight at a
    fixture.  What actually held the gate was a second, unrelated check: the
    fixture's ``command`` names none of the declared targets, so ``check``
    returns ``SCOPED``.  One fixture that spelled the real command would have
    licensed a push of an unmeasured tree (D-082, D-434).

    Pinned on the payload rather than the count because leakage is what has to
    stay impossible, not any particular number of entries.
    """
    leaked = [p.name for p in rs.entries() if json.loads(p.read_text()).get("worktree") == _FIXTURE_WORKTREE]
    assert leaked == [], (
        f"{len(leaked)} fixture receipt(s) in the production store — a test is "
        f"writing to the real STORE_DIR instead of a tmp_path: {leaked[:5]}"
    )


def test_recall_current_reads_the_tree_in_hand(tmp_path: Path, monkeypatch) -> None:
    fingerprint = "e" * 40
    monkeypatch.setattr(
        rs.tp,
        "stamp",
        lambda root=None, ref="HEAD": tp.Stamp(
            head="h",
            worktree_fingerprint=fingerprint,
            committed_fingerprint="c" * 40,
            untracked_digest="u",
            n_tracked=1,
            n_untracked=0,
            worktree={},
            committed={},
        ),
    )
    assert rs.recall_current(root=tmp_path) is None
    rs.archive(_receipt(fingerprint), root=tmp_path)
    assert rs.recall_current(root=tmp_path) is not None


def test_cli_recall_reports_miss_then_hit(tmp_path: Path, capsys, monkeypatch) -> None:
    # `STORE_DIR` is joined onto the repo root, so an *absolute* override wins
    # and redirects the CLI's default-root writes into `tmp_path`.  Without it
    # this test archived a green receipt keyed on the live tree straight into
    # the production store (D-434); the fingerprint may stay real, it is only
    # the store that has to be private.
    monkeypatch.setattr(rs, "STORE_DIR", tmp_path)
    fingerprint = tp.stamp().worktree_fingerprint
    assert rs._main(["list"]) == 0

    rs.archive(_receipt(fingerprint))
    assert rs._main(["recall"]) == 0
    assert "HIT" in capsys.readouterr().out


def test_cli_archive_refuses_a_missing_receipt(tmp_path: Path, capsys) -> None:
    assert rs._main(["archive", str(tmp_path / "nope.json")]) == 1
    assert "nothing readable" in capsys.readouterr().out


def test_archived_receipt_is_the_json_push_preflight_reads(tmp_path: Path) -> None:
    """The store holds `push_preflight`'s own format, not a private one.

    Pinned because the moment the store needed a schema of its own, a receipt
    would have two statements of itself (D-047) and they would drift.
    """
    path = rs.archive(_receipt("a" * 40), root=tmp_path)
    blob = json.loads(path.read_text())
    assert pp.Receipt.from_json(json.dumps(blob)).worktree_fingerprint == "a" * 40

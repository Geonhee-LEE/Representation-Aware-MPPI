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
    rs.archive(receipt)
    after = tp.stamp().worktree_fingerprint

    assert after == before
    assert rs.recall(before) is not None


def test_the_store_is_untracked_in_this_repo() -> None:
    """A committed store is not slower — it is a cache that never hits.

    The failure is silent (writes succeed, reads miss, nothing errors), so it
    gets asserted here rather than left for a future cycle to rediscover.
    """
    assert rs.tracked_conflict() == (), (
        "results/readings/ is tracked — every archive would now change the "
        "tracked tree and invalidate the receipt it just stored"
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

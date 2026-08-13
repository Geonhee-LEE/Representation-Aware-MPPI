"""Recall and gate must admit the same receipt (D-237).

The gap this file pins is not that the gate was wrong — it was right on every
tree it was handed.  It is that the *hand-off* could not name the receipt the
gate would have accepted.  ``push_preflight.check`` admits a tree that moved
only on paths ``inert_surface`` has measured to be unreadable by the suite;
``push_licence.licence_path`` derived the receipt's filename from an exact
worktree fingerprint.  Since the protocol mandates writes *after* the receipt
(the post-receipt population), the fingerprint has always moved by push time, so
the exact key always missed and the hook always read ``NO_RECEIPT`` — including
on 2026-08-13 12:00, which held four live pins, saw ``check`` go GREEN, was
refused by the hook anyway, and paid a second 513 s suite.

Note on hygiene, learned the expensive way while writing this file: a test that
*spells* a pinned path is a direct reader of it, so the pin's ``readers_key``
moves and the exemption is withdrawn — by the test that asserts the exemption
works.  Every path below is therefore obtained from
:data:`inert_surface.POST_RECEIPT_WRITES` at run time, never typed.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from eval.mppi_sandbox import inert_surface as ins
from eval.mppi_sandbox import push_licence as pl
from eval.mppi_sandbox import push_preflight as pp
from eval.mppi_sandbox import receipt_store as rs
from eval.mppi_sandbox import tree_provenance as tp

#: A source file that no pin exempts — drift here is material by construction.
CARRIER = "eval/mppi_sandbox/push_licence.py"


def _live_inert_path() -> str:
    """A concrete path covered by a pin that currently holds.

    Read from the module rather than typed, per this file's docstring.  Skips
    rather than fails when every pin happens to be withdrawn: the exemption
    machinery having no live pin is a real state of the repository (it is the
    state 2026-08-13 10:00 left behind), and it is not this file's claim.
    """
    for candidate in ins.POST_RECEIPT_WRITES:
        if not ins.inert(candidate):
            continue
        return candidate + "x.tsv" if candidate.endswith("/") else candidate
    pytest.skip("no inert pin currently holds — nothing to exempt")


def _stamp(worktree: dict[str, str], fingerprint: str) -> tp.Stamp:
    return tp.Stamp(
        head="0" * 40,
        worktree_fingerprint=fingerprint,
        committed_fingerprint="c" * 16,
        untracked_digest="u" * 16,
        n_tracked=len(worktree),
        n_untracked=0,
        worktree=dict(worktree),
    )


def _receipt(worktree: dict[str, str], fingerprint: str, rc: int = 0) -> pp.Receipt:
    return pp.Receipt(
        head="0" * 40,
        worktree_fingerprint=fingerprint,
        committed_fingerprint="c" * 16,
        returncode=rc,
        counts={"passed": 10, "failed": 0},
        worktree=dict(worktree),
    )


class TestTreeMatch:
    """The one implementation of "close enough to license this tree"."""

    def test_the_same_tree_is_the_trivial_hit(self):
        wt = {CARRIER: "aaa"}
        assert pp.tree_match(_receipt(wt, "f1"), _stamp(wt, "f1")).ok

    def test_a_move_on_a_pinned_path_is_admitted_and_named(self):
        inert_path = _live_inert_path()
        before = {CARRIER: "aaa", inert_path: "111"}
        after = {CARRIER: "aaa", inert_path: "222"}
        match = pp.tree_match(_receipt(before, "f1"), _stamp(after, "f2"))
        assert match.ok
        # Named, not merely tolerated: the verdict's detail prints these.
        assert inert_path in match.ignored

    def test_a_move_a_test_can_read_is_refused(self):
        before = {CARRIER: "aaa"}
        after = {CARRIER: "bbb"}
        match = pp.tree_match(_receipt(before, "f1"), _stamp(after, "f2"))
        assert not match.ok
        assert not match.blind
        assert CARRIER in match.material.paths

    def test_a_receipt_without_digests_cannot_be_shown_harmless(self):
        # Absent per-path digests the question is unanswerable, and an
        # unanswerable question is not a pass.
        receipt = pp.Receipt(
            head="0" * 40,
            worktree_fingerprint="f1",
            committed_fingerprint="c" * 16,
            returncode=0,
            counts={"passed": 1},
        )
        match = pp.tree_match(receipt, _stamp({CARRIER: "aaa"}, "f2"))
        assert not match.ok
        assert match.blind

    @pytest.mark.parametrize(
        "moved_path_is_pinned, expected_ok",
        [(True, True), (False, False)],
    )
    def test_the_gate_reaches_tree_match_s_verdict_not_its_own(
        self, tmp_path, monkeypatch, moved_path_is_pinned, expected_ok
    ):
        # check() must not re-implement the rule.  Both directions, so the
        # agreement is not the vacuous one where both always say yes.
        moved = _live_inert_path() if moved_path_is_pinned else CARRIER
        before = {CARRIER: "aaa", _live_inert_path(): "111"}
        after = dict(before, **{moved: "222"})
        receipt = _receipt(before, "f" * 16)
        path = tmp_path / "r.json"
        path.write_text(receipt.to_json())
        stamp = _stamp(after, "g" * 16)
        monkeypatch.setattr(tp, "stamp", lambda root=None: stamp)

        assert pp.tree_match(receipt, stamp, path).ok is expected_ok
        verdict = pp.check(path, root=tmp_path, declared={}, frontier=())
        assert (verdict.verdict != pp.STALE) is expected_ok


class TestLicenceRecall:
    """What ``licence_path`` hands the gate, and what it refuses to."""

    def _store(self, tmp_path: Path) -> Path:
        d = rs.store_dir(tmp_path)
        d.mkdir(parents=True, exist_ok=True)
        return d

    def _archive(self, tmp_path: Path, receipt: pp.Receipt) -> Path:
        self._store(tmp_path)
        return rs.archive(receipt, tmp_path)

    def test_the_exact_fingerprint_still_wins(self, tmp_path, monkeypatch):
        wt = {CARRIER: "aaa"}
        exact = self._archive(tmp_path, _receipt(wt, "f" * 16))
        monkeypatch.setattr(tp, "stamp", lambda root=None: _stamp(wt, "f" * 16))
        assert pl.licence_path(tmp_path) == exact

    def test_a_post_receipt_write_no_longer_hides_the_receipt(
        self, tmp_path, monkeypatch
    ):
        # The D-237 regression, stated as the cycle experienced it: the suite
        # ran, then the mandated post-receipt writes moved the tree, and the
        # hook could not find the receipt it had just archived.
        inert_path = _live_inert_path()
        measured = {CARRIER: "aaa", inert_path: "111"}
        pushed = {CARRIER: "aaa", inert_path: "222"}
        archived = self._archive(tmp_path, _receipt(measured, "a" * 16))
        monkeypatch.setattr(tp, "stamp", lambda root=None: _stamp(pushed, "b" * 16))

        found = pl.licence_path(tmp_path)

        assert found == archived
        assert found.exists()

    def test_a_receipt_for_a_materially_different_tree_is_not_a_licence(
        self, tmp_path, monkeypatch
    ):
        # Fails closed: the returned path is the exact key, which does not
        # exist, so the gate reports NO_RECEIPT on a tree nobody measured.
        measured = {CARRIER: "aaa"}
        pushed = {CARRIER: "bbb"}
        self._archive(tmp_path, _receipt(measured, "a" * 16))
        monkeypatch.setattr(tp, "stamp", lambda root=None: _stamp(pushed, "b" * 16))

        found = pl.licence_path(tmp_path)

        assert not found.exists()
        assert found == rs.path_for("b" * 16, tmp_path)
        assert pp.check(found, root=tmp_path).verdict == pp.NO_RECEIPT

    def test_an_empty_store_fails_closed(self, tmp_path, monkeypatch):
        self._store(tmp_path)
        monkeypatch.setattr(tp, "stamp", lambda root=None: _stamp({CARRIER: "a"}, "b" * 16))
        assert not pl.licence_path(tmp_path).exists()

    def test_the_search_is_deterministic_and_prefers_the_newest(
        self, tmp_path, monkeypatch
    ):
        # Two admissible receipts are both licences for this tree; the newest is
        # the one whose measurement is closest to what is about to be pushed,
        # and two runs of the hook on one tree must reach the same file.
        inert_path = _live_inert_path()
        older = self._archive(
            tmp_path, _receipt({CARRIER: "aaa", inert_path: "1"}, "a" * 16)
        )
        newer = self._archive(
            tmp_path, _receipt({CARRIER: "aaa", inert_path: "2"}, "c" * 16)
        )
        import os

        os.utime(older, (1_600_000_000, 1_600_000_000))
        os.utime(newer, (1_700_000_000, 1_700_000_000))
        monkeypatch.setattr(
            tp, "stamp", lambda root=None: _stamp({CARRIER: "aaa", inert_path: "3"}, "d" * 16)
        )

        assert pl.licence_path(tmp_path) == newer
        assert pl.licence_path(tmp_path) == newer

    def test_recall_cannot_beat_the_gate(self, tmp_path, monkeypatch):
        # The search's whole safety argument: a receipt it admits still faces
        # every other condition check() applies.  A red suite whose tree drifted
        # only on a pinned path is findable — and still refused.
        inert_path = _live_inert_path()
        measured = {CARRIER: "aaa", inert_path: "111"}
        pushed = {CARRIER: "aaa", inert_path: "222"}
        archived = self._archive(tmp_path, _receipt(measured, "a" * 16, rc=1))
        monkeypatch.setattr(tp, "stamp", lambda root=None: _stamp(pushed, "b" * 16))

        found = pl.licence_path(tmp_path)
        assert found == archived

        verdict = pp.check(found, root=tmp_path, declared={}, frontier=())
        assert verdict.verdict == pp.RED
        assert not verdict.ok

    def test_no_argument_can_aim_the_hook_at_a_friendlier_receipt(self):
        # The property the one-line version had, preserved: licence_path takes
        # no receipt argument, so the caller composes nothing.
        import inspect

        params = list(inspect.signature(pl.licence_path).parameters)
        assert params == ["root"]

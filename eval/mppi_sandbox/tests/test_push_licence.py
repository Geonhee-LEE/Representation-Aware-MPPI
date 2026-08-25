"""The push gate, re-run where the caller's shell cannot reach it (D-221)."""

from __future__ import annotations

import os
import stat
from dataclasses import dataclass
from pathlib import Path

import pytest

from eval.mppi_sandbox import push_licence as pl

ROOT = Path(__file__).resolve().parents[3]


@dataclass(frozen=True)
class _StubVerdict:
    """Enough of :class:`push_preflight.Verdict` for the decision to be read."""

    verdict: str
    detail: str

    @property
    def ok(self) -> bool:
        return self.verdict == "GREEN"


def _line(remote_ref: str, local_sha: str = "a" * 40) -> str:
    return f"refs/heads/topic {local_sha} {remote_ref} {'b' * 40}"


class TestGuardedRefs:
    def test_autoresearch_ref_is_guarded(self):
        text = _line("refs/heads/autoresearch/p3-thing")
        assert pl.guarded_refs(text) == ("refs/heads/autoresearch/p3-thing",)

    def test_main_is_not_this_hooks_business(self):
        assert pl.guarded_refs(_line("refs/heads/main")) == ()

    def test_membership_follows_the_remote_name_not_the_local_one(self):
        # A local branch called anything, landing under autoresearch/, is
        # judged by where it lands — that is what the review queue counts.
        text = "refs/heads/scratch " + "a" * 40 + " refs/heads/autoresearch/x " + "b" * 40
        assert pl.guarded_refs(text) == ("refs/heads/autoresearch/x",)

    def test_deletion_ships_no_tree_so_it_is_not_gated(self):
        assert pl.guarded_refs(_line("refs/heads/autoresearch/x", "0" * 40)) == ()

    def test_malformed_and_blank_lines_are_skipped(self):
        text = "\n".join(["", "garbage", _line("refs/heads/autoresearch/y")])
        assert pl.guarded_refs(text) == ("refs/heads/autoresearch/y",)

    def test_multiple_refs_in_one_push(self):
        text = "\n".join(
            [
                _line("refs/heads/autoresearch/a"),
                _line("refs/heads/main"),
                _line("refs/heads/autoresearch/b"),
            ]
        )
        assert pl.guarded_refs(text) == (
            "refs/heads/autoresearch/a",
            "refs/heads/autoresearch/b",
        )


class TestDecide:
    def test_unguarded_push_never_consults_a_receipt(self):
        # The short-circuit is the property: a human pushing main must not be
        # blocked by, or even pay for, the executor's suite bookkeeping.
        def _explode(*a, **k):  # pragma: no cover - must not run
            raise AssertionError("checker consulted for an unguarded push")

        decision = pl.decide(_line("refs/heads/main"), checker=_explode)
        assert decision.ok
        assert decision.refs == ()

    def test_green_gate_allows(self):
        decision = pl.decide(
            _line("refs/heads/autoresearch/x"),
            receipt_path=Path("/nonexistent"),
            checker=lambda p, root=None: _StubVerdict("GREEN", "all good"),
        )
        assert decision.outcome == pl.ALLOW
        assert "GREEN" in decision.detail

    def test_refusal_reaches_the_decision(self):
        decision = pl.decide(
            _line("refs/heads/autoresearch/x"),
            receipt_path=Path("/nonexistent"),
            checker=lambda p, root=None: _StubVerdict("STALE", "tree moved"),
        )
        assert decision.outcome == pl.REFUSE
        assert not decision.ok
        assert "STALE" in decision.detail

    def test_missing_receipt_fails_closed_through_the_real_gate(self, tmp_path):
        # No stub: this is push_preflight's own NO_RECEIPT path, which is the
        # verdict a crashed cycle leaves behind.
        decision = pl.decide(
            _line("refs/heads/autoresearch/x"),
            receipt_path=tmp_path / "absent.json",
            root=ROOT,
        )
        assert decision.outcome == pl.REFUSE
        assert "NO_RECEIPT" in decision.detail


class TestLicencePath:
    def test_path_is_derived_from_the_tree_not_from_an_argument(self):
        # Two calls on one tree agree, and the name carries the fingerprint —
        # so there is no argument by which a caller could aim the hook at a
        # friendlier receipt.
        first = pl.licence_path(ROOT)
        second = pl.licence_path(ROOT)
        assert first == second
        assert first.parent == ROOT / "results" / "receipts"


class TestHookScript:
    def test_hook_exists_where_the_module_says_it_does(self):
        assert (ROOT / pl.HOOKS_DIR / pl.HOOK_NAME).is_file()

    def test_hook_is_executable(self):
        # git silently ignores a non-executable hook, which would make this
        # whole guard a no-op that reads as installed.
        mode = (ROOT / pl.HOOKS_DIR / pl.HOOK_NAME).stat().st_mode
        assert mode & stat.S_IXUSR

    def test_hook_delegates_to_this_module(self):
        text = (ROOT / pl.HOOKS_DIR / pl.HOOK_NAME).read_text()
        assert "eval.mppi_sandbox.push_licence hook" in text

    def test_hook_execs_so_its_status_is_the_modules(self):
        # Without exec the shell's own exit status is what git reads, which is
        # the same class of bug this hook exists to close.
        text = (ROOT / pl.HOOKS_DIR / pl.HOOK_NAME).read_text()
        assert "exec python3" in text


class TestWiring:
    def test_wiring_reports_a_string(self):
        assert isinstance(pl.wiring(ROOT), str)

    def test_wired_agrees_with_the_configured_path(self):
        assert pl.wired(ROOT) == (pl.wiring(ROOT) == str(pl.HOOKS_DIR))

    def test_status_fails_closed_when_unwired(self, tmp_path, monkeypatch):
        # A clone that has the hook file but not the config is ungated, and the
        # honest reading of that is rc=1 — no commit can carry core.hooksPath.
        monkeypatch.setattr(pl, "wired", lambda root=None: False)
        monkeypatch.setattr(pl, "wiring", lambda root=None: "")
        assert pl._main(["status"]) == 1

    def test_status_passes_when_wired(self, monkeypatch):
        monkeypatch.setattr(pl, "wired", lambda root=None: True)
        monkeypatch.setattr(pl, "wiring", lambda root=None: str(pl.HOOKS_DIR))
        assert pl._main(["status"]) == 0

    def test_unknown_command_is_distinguishable_from_a_refusal(self):
        # rc=2 vs rc=1: a typo must not read as a gate refusal, and a refusal
        # must not read as a typo.
        assert pl._main(["nonsense"]) == 2


class TestHookCli:
    def test_hook_rc_is_one_on_refusal(self, monkeypatch, capsys):
        monkeypatch.setattr(
            pl, "decide", lambda text: pl.Decision(pl.REFUSE, "tree moved")
        )
        monkeypatch.setattr("sys.stdin", _FakeStdin(_line("refs/heads/autoresearch/x")))
        assert pl._main(["hook"]) == 1
        assert "REFUSE" in capsys.readouterr().out

    def test_hook_rc_is_zero_on_allow(self, monkeypatch, capsys):
        monkeypatch.setattr(
            pl, "decide", lambda text: pl.Decision(pl.ALLOW, "green")
        )
        monkeypatch.setattr("sys.stdin", _FakeStdin(""))
        assert pl._main(["hook"]) == 0
        assert "ALLOW" in capsys.readouterr().out


class _FakeStdin:
    def __init__(self, text: str) -> None:
        self._text = text

    def read(self) -> str:
        return self._text

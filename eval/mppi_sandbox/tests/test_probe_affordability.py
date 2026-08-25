"""A probe that cannot afford to finish must return a reading, not a traceback.

On 2026-08-13 the executor spent 15 minutes earning a full re-take of the
largest pin in :data:`inert_surface.POST_RECEIPT_WRITES` and got a
``subprocess.TimeoutExpired`` stack trace for it: the *un-mutated* pass alone
exceeded the 900 s ceiling, and a probe needs two.  The measurement — "this pin
is not re-takable by :func:`probe` at any cycle length" — is the single most
decision-relevant fact the module can report about a pin sitting at
:data:`COMPOSITION_CAP`, and it was thrown away as an exception (D-238).

These tests name the *population* (``POST_RECEIPT_WRITES``, the registry) and
never respell its members.  That is not style: a docstring that spells a pinned
path makes this module a reader of it and withdraws the pin between two
readings, which is exactly what the 13:00 cycle did to itself one hour before
this file was written (D-237).
"""

from __future__ import annotations

import subprocess

import pytest

from eval.mppi_sandbox import inert_surface as ins


TIMEOUT_SENTINEL = subprocess.TimeoutExpired(cmd=("python3", "-m", "pytest"), timeout=1)


@pytest.fixture
def target(tmp_path):
    """A one-file tree standing in for a probe candidate."""
    path = tmp_path / "artifact.md"
    path.write_text("original\n")
    return path


def _always_timeout(*_a, **_k):
    raise TIMEOUT_SENTINEL


# --------------------------------------------------------------------------
# the verdict exists and is distinct
# --------------------------------------------------------------------------


def test_unaffordable_is_not_any_other_verdict():
    """The whole point is that it is not folded into VACUOUS."""
    others = {ins.INERT, ins.INERT_COMPOSED, ins.CONTENT_READ, ins.VACUOUS}
    assert ins.UNAFFORDABLE not in others


def test_unaffordable_does_not_license_an_exemption():
    """A verdict nobody measured cannot be the one that admits a write."""
    assert ins.UNAFFORDABLE not in (ins.INERT, ins.INERT_COMPOSED)


# --------------------------------------------------------------------------
# _run: a timeout is a return value, not an exception
# --------------------------------------------------------------------------


def test_run_returns_none_on_timeout(monkeypatch):
    monkeypatch.setattr(ins.subprocess, "run", _always_timeout)
    assert ins._run(("t.py",)) is None


def test_run_does_not_raise_on_timeout(monkeypatch):
    """The regression: the CLI died on this and the cycle got no verdict."""
    monkeypatch.setattr(ins.subprocess, "run", _always_timeout)
    try:
        ins._run(("t.py",))
    except subprocess.TimeoutExpired:  # pragma: no cover - the defect
        pytest.fail("_run raised instead of grading the timeout")


def test_run_still_parses_a_pass_that_finishes(monkeypatch):
    """The other direction — the timeout path must not swallow a real run."""

    class _Proc:
        stdout = "3 passed\n"
        stderr = ""

    monkeypatch.setattr(ins.subprocess, "run", lambda *a, **k: _Proc())
    assert ins._run(("t.py",)) == {"passed": 3}


def test_run_passes_its_timeout_through(monkeypatch):
    seen = {}

    def _capture(*_a, **kw):
        seen.update(kw)
        raise TIMEOUT_SENTINEL

    monkeypatch.setattr(ins.subprocess, "run", _capture)
    ins._run(("t.py",), None, 12.5)
    assert seen["timeout"] == 12.5


# --------------------------------------------------------------------------
# probe: graded, and the tree is left alone
# --------------------------------------------------------------------------


def test_probe_grades_unaffordable_when_the_first_pass_times_out(monkeypatch, target):
    monkeypatch.setattr(ins, "_run", lambda *a, **k: None)
    monkeypatch.setattr(ins, "readers", lambda *a, **k: ins.Readers(("t.py",), ()))
    monkeypatch.setattr(ins, "_probe_target", lambda *a, **k: target)
    p = ins.probe("artifact.md", sources={}, tracked=None)
    assert p.verdict == ins.UNAFFORDABLE


def test_first_pass_timeout_never_writes_the_mutation(monkeypatch, target):
    """Paying for the second pass when the first priced out is pure waste."""
    monkeypatch.setattr(ins, "_run", lambda *a, **k: None)
    monkeypatch.setattr(ins, "readers", lambda *a, **k: ins.Readers(("t.py",), ()))
    monkeypatch.setattr(ins, "_probe_target", lambda *a, **k: target)
    ins.probe("artifact.md", sources={}, tracked=None)
    assert target.read_text() == "original\n"


def test_second_pass_timeout_still_restores_the_target(monkeypatch, target):
    """The mutation is written here, so the finally: clause is load-bearing."""
    calls = []

    def _first_ok_then_timeout(*_a, **_k):
        calls.append(1)
        return {"passed": 1, "failed": 0} if len(calls) == 1 else None

    monkeypatch.setattr(ins, "_run", _first_ok_then_timeout)
    monkeypatch.setattr(ins, "readers", lambda *a, **k: ins.Readers(("t.py",), ()))
    monkeypatch.setattr(ins, "_probe_target", lambda *a, **k: target)
    p = ins.probe("artifact.md", sources={}, tracked=None)
    assert p.verdict == ins.UNAFFORDABLE
    assert target.read_text() == "original\n"


# --------------------------------------------------------------------------
# compose: the reason survives the composition
# --------------------------------------------------------------------------


def test_compose_propagates_unaffordable_from_the_entrant_half():
    assert ins.compose(ins.INERT, ins.UNAFFORDABLE, True) == ins.UNAFFORDABLE


def test_compose_does_not_launder_unaffordable_into_inert():
    assert ins.compose(ins.INERT_COMPOSED, ins.UNAFFORDABLE, True) != ins.INERT_COMPOSED


def test_compose_still_grades_a_measured_entrant_inert():
    """Both directions — the new branch must not shadow the ordinary one."""
    assert ins.compose(ins.INERT, ins.INERT, True) == ins.INERT_COMPOSED

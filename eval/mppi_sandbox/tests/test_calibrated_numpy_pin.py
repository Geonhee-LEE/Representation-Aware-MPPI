"""The numpy pin is load-bearing evidence, so it gets a test (D-032).

Five slow closed-loop tests -- the evidence for D-029 and D-030 -- pass under
numpy 1.26.4 and fail under 2.5.1 on one box with identical code and seeds.
That makes the pinned version part of the *claim*, not part of the toolchain.

Two ways that fact could silently rot, one test each:

* someone bumps ``eval/requirements-ci.txt`` and the conftest header keeps
  announcing the old version as "calibrated" -- the header would then lie in
  exactly the situation it exists to flag;
* someone drops the pin back to a bare ``numpy``, restoring the unpinned
  install that put the runner on 2.x for 24 hours without anyone noticing.

These are free (no simulation), so they stay in the fast half deliberately: a
guard that only runs in the 24-minute job is a guard nobody sees fail.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from eval.conftest import (
    CALIBRATED_NUMPY,
    CALIBRATED_SIMD,
    _dispatch_line,
    _numpy_line,
    simd_found,
)

REQUIREMENTS = Path(__file__).resolve().parents[2] / "requirements-ci.txt"


def _pinned_numpy() -> str:
    for raw in REQUIREMENTS.read_text().splitlines():
        line = raw.split("#", 1)[0].strip()
        if not line:
            continue
        m = re.fullmatch(r"numpy==([0-9][0-9A-Za-z.]*)", line)
        if m:
            return m.group(1)
        if re.match(r"numpy\b", line):
            pytest.fail(
                f"numpy is present but not pinned with '==' in {REQUIREMENTS.name}: "
                f"{line!r}. An unpinned numpy is what put CI on 2.x while every "
                f"D-029/D-030 constant was derived on {CALIBRATED_NUMPY} (D-032)."
            )
    pytest.fail(f"no numpy requirement found in {REQUIREMENTS}")


def test_pin_matches_header():
    """The advertised 'calibrated' version must be the one CI installs."""
    assert _pinned_numpy() == CALIBRATED_NUMPY, (
        "eval/requirements-ci.txt and eval/conftest.py:CALIBRATED_NUMPY "
        "disagree. Bumping the pin is allowed, but it means re-deriving the "
        "D-029 / D-030 constants on the new version -- not just editing one "
        "of these two files until CI is green."
    )


def test_header_flags_an_uncalibrated_numpy(monkeypatch):
    """The mismatch branch must actually say something, not degrade to silence.

    Asserted through the real hook rather than by reading the source, so that
    deleting the warning breaks this test.
    """
    import numpy

    monkeypatch.setattr(numpy, "__version__", "0.0.0-not-a-real-numpy")
    line = _numpy_line()
    assert "0.0.0-not-a-real-numpy" in line, "the actual version must be named"
    assert CALIBRATED_NUMPY in line, "the expected version must be named too"
    assert "requirements-ci.txt" in line, "the reader needs somewhere to go"


def test_header_is_quiet_on_the_calibrated_version(monkeypatch):
    import numpy

    monkeypatch.setattr(numpy, "__version__", CALIBRATED_NUMPY)
    assert _numpy_line() == f"eval numpy: {CALIBRATED_NUMPY} (calibrated)"


# --------------------------------------------------------------------------
# D-033: the pin was honoured and the verdict flipped anyway, so the version is
# not the discriminating coordinate -- the SIMD dispatch is. These guards are
# the same shape as the ones above, one axis over, and live in the fast half for
# the same reason: a guard that only runs in the 24-minute job is one nobody
# watches fail.
# --------------------------------------------------------------------------


def test_dispatch_is_reported_at_all():
    """The header must name the dispatch, not just the version.

    The concrete failure this prevents: CI printed 'numpy 1.26.4 (calibrated)'
    while measuring a different machine, and that line was read as evidence the
    environment matched. It did not.
    """
    line = _dispatch_line()
    assert line.startswith("eval simd:"), line
    assert CALIBRATED_SIMD in line or "unknown" in line, line


def test_dispatch_line_flags_a_missing_calibrated_extension(monkeypatch):
    """The AVX2-runner branch must say something, asserted through the hook."""
    monkeypatch.setattr(
        "eval.conftest.simd_found", lambda: ("SSE2", "AVX", "FMA3", "AVX2")
    )
    line = _dispatch_line()
    assert "AVX2" in line, "the actual top extension must be named"
    assert CALIBRATED_SIMD in line, "the expected extension must be named too"
    assert "D-033" in line, "the reader needs somewhere to go"


def test_dispatch_line_is_quiet_when_calibrated(monkeypatch):
    monkeypatch.setattr(
        "eval.conftest.simd_found", lambda: ("AVX2", CALIBRATED_SIMD)
    )
    assert _dispatch_line() == (
        f"eval simd: {CALIBRATED_SIMD} (calibrated: {CALIBRATED_SIMD} present)"
    )


def test_dispatch_line_degrades_to_unknown_not_to_a_crash(monkeypatch):
    """A future numpy that drops the config dict must not take the suite down."""
    monkeypatch.setattr("eval.conftest.simd_found", tuple)
    assert "unknown" in _dispatch_line()


def test_simd_found_reads_the_live_interpreter():
    """Sanity: the helper reports something plausible on whatever runs it.

    Deliberately not asserting AVX-512 is present -- that is exactly the
    machine-dependence under study, and asserting it here would make the suite
    un-runnable on the runner it is meant to diagnose.
    """
    found = simd_found()
    assert isinstance(found, tuple)
    if found:
        assert all(isinstance(x, str) for x in found)

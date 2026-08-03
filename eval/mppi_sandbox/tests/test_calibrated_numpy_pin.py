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

from eval.conftest import CALIBRATED_NUMPY, _numpy_line

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

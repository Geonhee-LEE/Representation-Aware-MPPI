"""Fast-by-default test selection for the ``eval/`` suite.

D-016 made ``eval/`` the primary verification surface, and the suite has grown
from 145 s to ~636 s as cycles piled on closed-loop evidence.  The bulk of that
is not slack: the expensive assertions are runs deliberately derailed (D-029's
naive-weight arm) or frozen (D-030's ``H >= 35`` rungs), which cost ~100x a unit
test and *are* the evidence for those decisions.  Shortening their caps would
weaken the claims to save time nobody is waiting on (Q-051).

So the fix is a split, not a trim.  Tests marked ``@pytest.mark.slow`` are
deselected by default and run under ``--slow``.  Sandbox CI runs both halves as
separate jobs, so total coverage is unchanged -- only the default local /
executor invocation gets cheaper.

Two anti-silence guards, because a marker that quietly stops running tests is
worse than a slow suite:

* the header states which mode is active, and
* the terminal summary names the count deselected and how to get it back.
"""

from __future__ import annotations

import pytest

_SLOW_HELP = (
    "run tests marked @pytest.mark.slow (closed-loop sandbox runs; ~8 min)"
)

#: The numpy the D-029 / D-030 closed-loop constants were measured on. Keep in
#: lockstep with ``eval/requirements-ci.txt``; :func:`test_pin_matches_header`
#: fails if the two drift apart.
CALIBRATED_NUMPY = "1.26.4"


def pytest_addoption(parser):
    parser.addoption(
        "--slow", action="store_true", default=False, help=_SLOW_HELP
    )


def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "slow: closed-loop sandbox run costing >2 s; deselected unless --slow. "
        "Reserved for tests whose runtime IS the evidence (derailed / frozen "
        "arms), not for tests that are merely unoptimised.",
    )


def pytest_report_header(config):
    mode = ("FULL (--slow given; closed-loop runs included)"
            if config.getoption("--slow")
            else "FAST (slow closed-loop runs deselected; pass --slow for all)")
    return [f"eval suite: {mode}", _numpy_line()]


def _numpy_line():
    """State the numpy version, and shout if it is not the calibrated one.

    D-032: five slow tests pass on 1.26.4 and fail on 2.5.1 with identical code
    and seeds -- FP drift in a chaotic closed loop, not an RNG change. A run on
    the wrong numpy is not a weaker signal, it is a different measurement, so
    the version belongs in the header next to the mode rather than in a comment
    nobody reads at 3am. Reporting only; enforcing is Q-054's call, not this
    hook's -- a hard failure here would block bisecting the very drift it warns
    about.
    """
    import numpy

    got = numpy.__version__
    if got == CALIBRATED_NUMPY:
        return f"eval numpy: {got} (calibrated)"
    return (f"eval numpy: {got} != {CALIBRATED_NUMPY} (calibrated) -- "
            f"D-029/D-030 constants were derived on {CALIBRATED_NUMPY}; "
            f"a failure here may be FP drift, not a regression (see "
            f"eval/requirements-ci.txt)")


def pytest_collection_modifyitems(config, items):
    if config.getoption("--slow"):
        return
    skip_slow = pytest.mark.skip(reason="slow: pass --slow to run")
    deselected = 0
    for item in items:
        if item.get_closest_marker("slow") is not None:
            item.add_marker(skip_slow)
            deselected += 1
    config.stash[_DESELECTED] = deselected


_DESELECTED = pytest.StashKey[int]()


def pytest_terminal_summary(terminalreporter, exitstatus, config):
    n = config.stash.get(_DESELECTED, 0)
    if n:
        terminalreporter.write_sep(
            "-", f"{n} slow test(s) not run -- rerun with --slow for the full suite"
        )

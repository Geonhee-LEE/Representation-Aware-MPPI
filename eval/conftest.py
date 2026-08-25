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

#: The SIMD dispatch the same constants were measured under (D-033).  numpy
#: selects its kernels from the *host CPU* at import time, so this is a property
#: of the machine, not of the pin -- and it is the coordinate that actually
#: discriminates.  Measured: with numpy held at 1.26.4 and AVX-512 masked off via
#: ``NPY_DISABLE_CPU_FEATURES``, this box reproduces the GH runner's failure
#: value to all 17 digits (0.17901180719252627).  See :func:`_dispatch_line`.
CALIBRATED_SIMD = "AVX512_SKX"


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
    return [f"eval suite: {mode}", _numpy_line(), _dispatch_line(), _drift_line()]


def _numpy_line():
    """State the numpy version, and shout if it is not the calibrated one.

    D-032: five slow tests pass on 1.26.4 and fail on 2.5.1 with identical code
    and seeds -- FP drift in a chaotic closed loop, not an RNG change. A run on
    the wrong numpy is not a weaker signal, it is a different measurement, so
    the version belongs in the header next to the mode rather than in a comment
    nobody reads at 3am. Reporting only; enforcing is Q-054's call, not this
    hook's -- a hard failure here would block bisecting the very drift it warns
    about.

    D-033 downgraded this line's importance without removing it: the version is
    a real perturbation but *not* the discriminating one -- see
    :func:`_dispatch_line`.  It stays because a bump is still a re-measurement.
    """
    import numpy

    got = numpy.__version__
    if got == CALIBRATED_NUMPY:
        return f"eval numpy: {got} (calibrated)"
    return (f"eval numpy: {got} != {CALIBRATED_NUMPY} (calibrated) -- "
            f"D-029/D-030 constants were derived on {CALIBRATED_NUMPY}; "
            f"a failure here may be FP drift, not a regression (see "
            f"eval/requirements-ci.txt)")


def simd_found():
    """The SIMD extensions numpy actually dispatches on, this process.

    Runtime CPU detection, so it varies by *machine* even with the pin honoured.
    Returns ``()`` if numpy stops exposing the config dict rather than guessing.
    """
    import numpy

    try:
        cfg = numpy.__config__.show(mode="dicts")
    except Exception:                                  # pragma: no cover
        return ()
    return tuple(cfg.get("SIMD Extensions", {}).get("found", ()))


def _dispatch_line():
    """State the SIMD dispatch, and shout when it is not the calibrated one.

    D-033.  D-032 announced ``eval numpy: 1.26.4 (calibrated)`` on the GH runner
    and the same five slow tests failed anyway -- so the pin was honoured and the
    verdict still flipped, which falsifies "the evidence is conditional on the
    numpy version" as a *causal* claim.  Holding version and build fixed and
    masking AVX-512 off with ``NPY_DISABLE_CPU_FEATURES`` reproduces the runner's
    number to all 17 digits, which localises the real variable to kernel
    selection: AVX-512 (dev box) vs AVX2 (runner) reduce in a different order.

    Why report the whole found-set rather than a bool: the next divergence will
    not be AVX-512 again, and a fingerprint that only answers last time's
    question is how D-032 got written.  Reporting only, for D-032's reason -- a
    hard failure here would block bisecting the drift it exists to flag.
    """
    found = simd_found()
    if not found:
        return "eval simd: unknown (numpy exposed no SIMD config)"
    top = found[-1]
    if CALIBRATED_SIMD in found:
        return f"eval simd: {top} (calibrated: {CALIBRATED_SIMD} present)"
    return (f"eval simd: {top} -- {CALIBRATED_SIMD} ABSENT; D-029/D-030 "
            f"constants were measured with it. A closed-loop failure here is "
            f"most likely dispatch drift, not a regression (D-033)")


def drift_xfail_ids():
    """Node ids that route (a) marks on a non-calibrated dispatch (D-099).

    Derived from :func:`eval.mppi_sandbox.drift_repair.markable`, which derives
    it in turn from D-098's *per-test* native/masked readings.  It is deliberately
    not a list here: a hand-typed marker set would drift from the measurement
    that licenses it, and a set keyed on the dispatch alone would xfail rows whose
    failure on the runner has nothing to do with dispatch -- including Q-092's two
    unread ``exclusion_scope`` rows, which ``markable`` refuses.

    An import failure returns ``()`` **and is announced** by
    :func:`_drift_line`; silently marking nothing would look identical to a
    dispatch that needs no marks.
    """
    try:
        from eval.mppi_sandbox.drift_repair import markable
    except Exception:                                  # pragma: no cover
        return ()
    return tuple(sorted(markable()))


def _drift_line():
    """State what route (a) will do to this session, before it does it.

    Same anti-silence rule as the ``--slow`` summary: a marker that converts
    failures into expected-failures must never be inferable only by noticing
    that the count went down.
    """
    if CALIBRATED_SIMD in simd_found():
        return (f"eval drift-xfail: inactive ({CALIBRATED_SIMD} present; the "
                f"D-098 rows assert normally and a regression still fails)")
    ids = drift_xfail_ids()
    if not ids:
        return ("eval drift-xfail: ACTIVE but marked 0 tests -- drift_repair "
                "did not import or measured nothing; the D-098 rows will fail "
                "as before (this line is the only notice)")
    return (f"eval drift-xfail: ACTIVE, {len(ids)} test(s) xfail(strict=True) "
            f"as measured dispatch drift (D-098/D-099); a PASS is a failure")


def pytest_collection_modifyitems(config, items):
    _mark_drift_xfails(config, items)
    if config.getoption("--slow"):
        return
    skip_slow = pytest.mark.skip(reason="slow: pass --slow to run")
    deselected = 0
    for item in items:
        if item.get_closest_marker("slow") is not None:
            item.add_marker(skip_slow)
            deselected += 1
    config.stash[_DESELECTED] = deselected


def _mark_drift_xfails(config, items):
    """Route (a): xfail the measured-drift rows, and only on a machine that lacks
    the dispatch they were calibrated on.

    ``strict=True`` is the load-bearing argument.  A non-strict xfail absorbs a
    pass silently, so the day the numbers stop diverging -- a numpy bump, a
    runner change, or a genuine fix -- the marker would keep the row green and
    nobody would learn.  Strict makes an XPASS a failure, which is the loud
    signal that the marker's own premise expired.
    """
    config.stash[_DRIFT_MARKED] = 0
    if CALIBRATED_SIMD in simd_found():
        return
    wanted = set(drift_xfail_ids())
    if not wanted:
        return
    marked = 0
    for item in items:
        if item.nodeid in wanted:
            item.add_marker(
                pytest.mark.xfail(
                    reason=(
                        f"measured dispatch drift (D-098): passes on "
                        f"{CALIBRATED_SIMD}, fails with it masked. strict, so an "
                        f"unexpected pass fails and re-opens the attribution."
                    ),
                    strict=True,
                )
            )
            marked += 1
    config.stash[_DRIFT_MARKED] = marked


_DESELECTED = pytest.StashKey[int]()
_DRIFT_MARKED = pytest.StashKey[int]()


def pytest_terminal_summary(terminalreporter, exitstatus, config):
    n = config.stash.get(_DESELECTED, 0)
    if n:
        terminalreporter.write_sep(
            "-", f"{n} slow test(s) not run -- rerun with --slow for the full suite"
        )
    d = config.stash.get(_DRIFT_MARKED, 0)
    if d:
        terminalreporter.write_sep(
            "-",
            f"{d} test(s) xfail(strict) as measured dispatch drift (D-099); "
            f"2 attributable CI rows are NOT covered -- see Q-092",
        )

"""Why the five withdrawn exemptions have stayed withdrawn (D-295).

``carried_drift`` prices a re-take; it does not say what made it expensive.
Seventeen consecutive cycles read its ``PREMISE_DRIFTED`` line, re-derived the
cause by hand from the module list, and deferred on the strength of it.  These
tests fix the derivation so the eighteenth does not have to repeat it.

The measured fact under all of it: :mod:`inert_surface` mediates **every**
candidate and is the module the pin machinery lives in, so every cycle that
maintains the exemption mechanism withdraws every exemption it grants.
"""

import pytest

from eval.mppi_sandbox import inert_surface as ins


@pytest.fixture(scope="module")
def sources():
    return ins._python_sources()


def test_the_machinery_mediates_every_candidate(sources):
    """The fixed point, stated as a measurement rather than as prose.

    This is what makes the block structural instead of incidental churn: the
    module is not merely *a* dependency of the pins, it is a dependency of all
    of them at once, so no pin can outlive an edit to it.
    """
    for candidate in ins.POST_RECEIPT_WRITES:
        mods = ins.readers(candidate, sources).modules
        assert set(ins.SELF_MEDIATING) <= set(mods), (
            f"{candidate} is not mediated by {ins.SELF_MEDIATING} — if this "
            "fails the self-blocking argument has stopped applying to it, and "
            "D-295's premise needs re-reading rather than patching"
        )


def test_self_blocked_names_the_owning_module_not_just_a_count():
    """A count spells self-inflicted drift and foreign drift identically.

    The whole value of the reading is the *name*, which is why the verdict is
    derived from membership and the describe line quotes the module.
    """
    drift = ins.PremiseDrift(
        "STATE.md",
        ins.PREMISE_DRIFTED,
        modules_drifted=("citation_audit", "inert_surface"),
        base="deadbee",
    )
    block = ins.reprobe_block("STATE.md", drift=drift)

    assert block.verdict == ins.REPROBE_SELF_BLOCKED
    assert block.self_modules == ("inert_surface",)
    assert block.foreign_modules == ("citation_audit",)
    assert "inert_surface" in block.describe()


def test_foreign_drift_alone_is_not_self_blocked():
    """The distinction has to cut both ways or it is not a distinction.

    Foreign churn is ordinary maintenance debt and a re-take against it buys a
    pin that survives; grading it ``SELF_BLOCKED`` would licence deferring a
    re-take that is actually worth paying for.
    """
    drift = ins.PremiseDrift(
        "STATE.md",
        ins.PREMISE_DRIFTED,
        modules_drifted=("citation_audit", "push_preflight"),
        base="deadbee",
    )
    block = ins.reprobe_block("STATE.md", drift=drift)

    assert block.verdict == ins.REPROBE_FULL
    assert block.self_modules == ()
    assert not block.self_blocked


def test_nothing_is_dropped_from_the_reported_module_set():
    """``modules_drifted`` is carried through unfiltered.

    The ownership split is a property of the reading, not a subtraction inside
    the function — the shape that keeps this a pricing reading rather than a
    revocable guard with an unmet probe obligation (see ``reprobe_block``).
    A regression here would re-incur that obligation silently.
    """
    mods = ("citation_audit", "inert_surface", "tree_provenance")
    drift = ins.PremiseDrift(
        "JOURNAL.md", ins.PREMISE_DRIFTED, modules_drifted=mods, base="deadbee"
    )
    block = ins.reprobe_block("JOURNAL.md", drift=drift)

    assert block.modules_drifted == mods
    assert set(block.self_modules) | set(block.foreign_modules) == set(mods)


def test_an_intact_premise_prices_the_cheap_path():
    drift = ins.PremiseDrift(
        "JOURNAL.md",
        ins.PREMISE_INTACT,
        entrants=("eval/mppi_sandbox/tests/test_licence_recall.py",),
        intact=("eval/mppi_sandbox/tests/test_inert_surface.py",),
        base="deadbee",
    )
    block = ins.reprobe_block("JOURNAL.md", drift=drift)

    assert block.verdict == ins.REPROBE_CHEAP
    assert block.rerun == drift.rerun


def test_an_uncheckable_premise_does_not_read_as_a_priced_one():
    """``DRIFT_UNKNOWN`` fails closed, same rule ``carried_drift`` applies.

    A pin whose base commit is unresolvable has not been shown cheap *or*
    expensive, and reporting a cost for it would be a number with no
    measurement behind it.
    """
    drift = ins.PremiseDrift("results/", ins.DRIFT_UNKNOWN)
    block = ins.reprobe_block("results/", drift=drift)

    assert block.verdict == ins.REPROBE_UNKNOWN
    assert block.rerun == ()
    assert "cannot be priced" in block.describe()


def test_cli_blocker_is_advisory():
    """rc=0 on every verdict, for D-044's reason.

    No edit clears a self-blocked pin — the drift is a fact about history — so
    a red here would be permanent, and a permanent red gets muted.
    """
    assert ins._main(["blocker"]) == 0

"""STATE #2: how far does the dynamic probe actually reach? (D-053).

Each test states a fact that would have to change for the module's conclusion
to change, rather than pinning today's counts.  The counts live in the journal;
what lives here is the structure that produced them.
"""

from __future__ import annotations

import inspect
import subprocess
from pathlib import Path

import pytest

from eval.mppi_sandbox import guard_direction as gd
from eval.mppi_sandbox import guard_reflexivity as gr
from eval.mppi_sandbox import probe_reach as pr


@pytest.fixture(scope="module")
def pool():
    return gr.guards()


@pytest.fixture(scope="module")
def base_fixture(tmp_path_factory):
    root = tmp_path_factory.mktemp("base") / "repo"
    gd.build_scratch_repo(root)
    return root


@pytest.fixture(scope="module")
def enriched_fixture(tmp_path_factory):
    root = tmp_path_factory.mktemp("rich") / "repo"
    pr.build_enriched_repo(root)
    return root


# --------------------------------------------------------------------------
# population — a partition, pinned as an equality
# --------------------------------------------------------------------------


def test_substrates_partition_the_whole_guard_pool(pool):
    """Every guard lands in exactly one substrate, and nothing is dropped.

    D-052's equality pin, same reason: a reach number is a claim about a
    population, and a rule that stops matching would shrink the population
    silently instead of reporting an omission.
    """
    parts = pr.substrates(pool)
    named = [q for members in parts.values() for q in members]
    assert sorted(named) == sorted(g.qualname for g in pool)
    assert len(named) == len(set(named)), "a guard was counted under two substrates"
    assert set(parts) <= {
        pr.SUBSTRATE_REPO_ROOT, pr.SUBSTRATE_PACKAGE_SOURCE,
        pr.SUBSTRATE_SCANNED_POOL, pr.SUBSTRATE_DOMAIN,
    }


def test_root_addressable_agrees_with_the_signatures_it_claims_to_read(pool):
    """The substrate rule is checked against ``inspect`` in both directions."""
    claimed = {g.qualname for g in pr.root_addressable(pool)}
    actual = set()
    for g in pool:
        params = inspect.signature(pr._callable_of(g)).parameters
        if any(p in params for p in pr.ROOT_PARAMS):
            actual.add(g.qualname)
    assert claimed == actual


def test_root_addressable_is_a_strict_subset_of_the_pool(pool):
    """If every guard were root-addressable the substrate split would be idle."""
    assert 0 < len(pr.root_addressable(pool)) < len(pool)


# --------------------------------------------------------------------------
# normalise — the NOT_A_READING / empty conflation
# --------------------------------------------------------------------------


def test_a_string_return_is_not_an_empty_reading():
    """``len("")`` and ``len(())`` are both 0 and mean different things.

    Folding them would score ``lam_dependence.report`` as ``UNDECIDABLE`` — a
    measurement reported where none was possible, which is the failure mode
    every mirror in this package exists to prevent.
    """
    assert pr.normalise("some report text") is None
    assert pr.normalise("") is None
    assert pr.normalise(7) is None
    assert pr.normalise(()) == frozenset()


def test_normalise_flattens_all_three_drift_fields():
    """D-052's own defect, pinned here rather than rediscovered.

    ``Drift`` is a dataclass; reading only one field (or its ``repr``) hides
    movement in the other two, which is exactly how D-050's proven mask first
    came out ``DIVERGES``.
    """

    class FakeDrift:
        changed = ("a",)
        added = ("b",)
        removed = ("c",)

    assert pr.normalise(FakeDrift()) == frozenset({"a", "b", "c"})


def test_normalise_reads_dict_keys_not_values():
    assert pr.normalise({"x": [1, 2], "y": []}) == frozenset({"x", "y"})


# --------------------------------------------------------------------------
# the fixtures, and the liveness discipline on the enriched one
# --------------------------------------------------------------------------


def test_enriched_fixture_refuses_to_be_identical_to_the_base_one(tmp_path):
    """A fixture that copied nothing would make the whole comparison vacuous.

    D-050's rule: a probe whose act is a no-op measures nothing.  Here the
    "act" is the copy, so an empty copy raises instead of quietly reporting
    that enrichment changed no verdicts.
    """
    empty_source = tmp_path / "nothing"
    empty_source.mkdir()
    with pytest.raises(pr.ReachError):
        pr.build_enriched_repo(tmp_path / "repo", source=empty_source)


def test_enriched_fixture_carries_the_surfaces_and_commits_them(enriched_fixture):
    for rel in pr.READ_SURFACES:
        assert (enriched_fixture / rel).is_dir()
    status = subprocess.run(
        ("git", "-C", str(enriched_fixture), "status", "--porcelain"),
        capture_output=True, text=True, check=True).stdout
    assert status.strip() == "", "read surfaces left uncommitted — the fixture is " \
                                 "not in the committed state the guards read"


def test_base_fixture_still_holds_every_declared_local_only_path(base_fixture):
    """The comparison is only meaningful if enrichment *adds* rather than replaces."""
    from eval.mppi_sandbox.tree_provenance import DECLARED_LOCAL_ONLY

    for rel in DECLARED_LOCAL_ONLY:
        assert (base_fixture / rel).exists()


# --------------------------------------------------------------------------
# the findings
# --------------------------------------------------------------------------


def test_enrichment_strictly_widens_the_reach(pool, base_fixture, enriched_fixture):
    """The measured price of the fixture coincidence.

    Guards excluded from the probe's reach because ``build_scratch_repo``
    happens not to write ``docs/`` or ``scripts/`` — a property of the fixture,
    not of the guard or of the probe.  If this ever goes empty the fixture has
    caught up with the guards and the finding has been fixed.
    """
    base = pr.reach(pool, fixture=base_fixture)
    rich = pr.reach(pool, fixture=enriched_fixture)
    gap = pr.fixture_gap(base, rich)
    assert gap, "no guard is fixture-bound — D-053's finding no longer holds"
    base_errors = [r for r in base if r.verdict == pr.VERDICT_FIXTURE_ERROR]
    rich_errors = [r for r in rich if r.verdict == pr.VERDICT_FIXTURE_ERROR]
    assert len(rich_errors) < len(base_errors)
    assert sum(r.act_addressable for r in rich) > sum(r.act_addressable for r in base)


def test_both_registered_probes_read_empty_in_both_fixtures(pool, base_fixture,
                                                            enriched_fixture):
    """The sharpest finding, and the answer to STATE #2.

    Neither guard in :data:`guard_direction.PROBES` is readable from a fixture
    alone — both read **empty in the scratch repo**, base and enriched alike.
    What makes them probeable is the hand-written
    :attr:`guard_direction.Probe.liveness` act, of which there are exactly two.
    So the probe's reach is bounded by a **typed** table after all, one layer
    below the table :func:`guard_direction.unprobed_revocable` checks — D-052's
    finding in the instrument that was supposed to answer it.

    The assertion is on ``fixture_size``, **not** on the verdict, and the first
    draft got that wrong: it pinned ``UNDECIDABLE``, which also asserts the
    reading at the *real root* is empty.  That is a fact about whatever is in the
    working tree at the moment the suite runs — ``undeclared_drift`` reports
    every file this very cycle created — so the test failed on the cycle that
    wrote it, for a reason that has nothing to do with the probe.
    ``MUTE_FIXTURE`` and ``UNDECIDABLE`` differ only in the real-root half; the
    finding lives entirely in the fixture half.

    The dropped line is the point of D-056.  This test also asserted ``not
    scored[qualname].probeable`` — three lines under a docstring calling the two
    guards probeable.  Both statements were about the same two guards and only
    one of them could be true; the name carried the contradiction across, so it
    read as consistent for three cycles.  Silence at rest is now asserted as what
    it is — a *precondition* these two satisfy — and probeability is asserted
    against ground truth in
    :func:`test_registered_probes_are_probeable_by_execution`.
    """
    for fixture in (base_fixture, enriched_fixture):
        scored = {r.guard: r for r in pr.reach(pool, fixture=fixture)}
        for qualname in gd.PROBES:
            assert qualname in scored, f"{qualname} is not even root-addressable"
            assert scored[qualname].fixture_size == 0, (
                f"{qualname} now reads non-empty in the fixture — it no longer "
                "depends on its typed liveness act and D-053 needs re-deriving")
            assert not scored[qualname].reads_at_rest
            assert scored[qualname].verdict in (pr.VERDICT_UNDECIDABLE,
                                                pr.VERDICT_MUTE_FIXTURE)


def test_registered_probes_are_probeable_by_execution(pool, base_fixture,
                                                      enriched_fixture):
    """D-056's ground truth: the bar must pass the guards that demonstrably work.

    Every entry in ``PROBES`` has a hand-written liveness act, runs each cycle,
    and was re-confirmed under D-055's membership bar.  Whatever predicate this
    module uses to decide probeability must therefore score all of them
    probeable — no new fixture required, and no argument.

    Under the old ``probeable = READABLE`` bar this failed **2 of 2**, in both
    fixtures.  It is the check that turns "the bar looks one-sided" into a red
    test, which is the standard D-055 set for this class of finding.
    """
    for fixture in (base_fixture, enriched_fixture):
        scored = pr.reach(pool, fixture=fixture)
        assert pr.misscored_probes(scored) == (), (
            "the reach bar refuses a guard that has a working before/after "
            "probe — it is not measuring probeability")
        by_name = {r.guard: r for r in scored}
        for qualname in gd.PROBES:
            assert by_name[qualname].act_addressable


def test_act_gap_is_the_honest_denominator_reach_gap_stood_in_for(
        pool, enriched_fixture):
    """``reach_gap`` selects on loudness, which D-055 measured as adverse.

    Two things are asserted together because the second is what makes the first
    a defect: the act gap strictly contains the reach gap (so the smaller number
    was never the population), and the reach gap excludes guards the act gap
    keeps — among them both registered probes, which is exactly backwards.
    """
    scored = pr.reach(pool, fixture=enriched_fixture)
    loud = set(pr.reach_gap(scored))
    addressable = set(pr.act_gap(scored))
    assert loud < addressable, "the two gaps no longer differ — re-derive D-056"
    silent_but_workable = addressable - loud
    assert silent_but_workable, (
        "no guard is silent at rest yet act-addressable — the state both "
        "registered probes are in")
    assert not (addressable & set(gd.PROBES))


def test_reach_gap_is_the_mirror_unprobed_revocable_could_not_be(pool,
                                                                enriched_fixture):
    """``unprobed_revocable`` clears the probe table against ``revocable()``.

    That population has 2 members and every guard in the reach gap is outside
    it, so the existing mirror cannot report these no matter how many there
    are.  The two facts are asserted together because the second is what makes
    the first a defect rather than a coincidence.
    """
    assert gd.unprobed_revocable(pool) == ()
    gap = pr.reach_gap(pr.reach(pool, fixture=enriched_fixture))
    assert gap, "nothing readable is unprobed — the gap has closed"
    revocable = {g.qualname for g in gr.revocable(pool)}
    assert not (set(gap) & revocable), \
        "a revocable guard is in the reach gap — unprobed_revocable should have " \
        "caught it and the two mirrors are no longer independent"
    assert not (set(gap) & set(gd.PROBES))


def test_scored_guards_partition_into_addressable_and_unreachable(pool,
                                                                  enriched_fixture):
    """A reach number is a measurement only if the excluded set is stated.

    The partition held under the old bar too — it was a partition into the wrong
    two sets, which is why a structural pin did not catch D-056.  The added
    assertion is the one with content: no registered probe may land on the
    excluded side.
    """
    scored = pr.reach(pool, fixture=enriched_fixture)
    addressable = {r.guard for r in scored if r.act_addressable}
    excluded = {line.split(":")[0] for line in pr.unreachable(scored)}
    assert addressable | excluded == {r.guard for r in scored}
    assert not (addressable & excluded)
    assert not (excluded & set(gd.PROBES)), (
        "unreachable() names a guard with a working probe — the mirror that "
        "states what a reach number excluded is excluding the ground truth")


def test_a_guard_that_raises_is_not_scored_as_reading_nothing(pool, base_fixture):
    """``FIXTURE_ERROR`` must stay distinct from ``UNDECIDABLE``.

    The eight base-fixture failures raise rather than returning empty — which
    is :mod:`local_only_audit`'s stated discipline working.  Had they degraded
    to "found nothing" they would have scored ``UNDECIDABLE`` and the fixture
    gap would have been invisible, so the distinction is load-bearing for the
    finding and not merely tidy.
    """
    scored = pr.reach(pool, fixture=base_fixture)
    errors = [r for r in scored if r.verdict == pr.VERDICT_FIXTURE_ERROR]
    assert errors, "the base fixture now carries every guard — re-derive D-053"
    for r in errors:
        assert r.note, "an error verdict with no cause recorded"
        assert r.fixture_size is None


def test_measure_reports_a_readable_guard_with_both_sizes(pool, enriched_fixture):
    """Both readings are recorded, so an inversion is visible rather than lost.

    ``citation_audit.missing_sites`` reads non-empty in the fixture and empty at
    HEAD: the fixture is not a faithful copy of the repository and the module
    must not present it as one.
    """
    scored = [r for r in pr.reach(pool, fixture=enriched_fixture) if r.reads_at_rest]
    assert scored
    for r in scored:
        assert r.fixture_size is not None and r.fixture_size > 0
        assert r.real_size is not None

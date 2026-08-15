"""Tests for :mod:`census_subset` — Q-159's pricing instrument.

The tests that matter here are not the arithmetic ones.  They are the two
soundness properties the module claims in its docstring: that its population is
*derived* from the census registry rather than copied out of it, and that its
output cannot be mistaken for a push receipt.  Both are properties this package
has been burned by before (D-047, and the ``--fast`` subset receipt that
:mod:`suite_shard` exists instead of).
"""

from __future__ import annotations

import dataclasses

import pytest

from eval.mppi_sandbox import census_subset as cs
from eval.mppi_sandbox import push_preflight as pp
from eval.mppi_sandbox import suite_shard as ss
from eval.mppi_sandbox import tree_provenance as tp
from eval.mppi_sandbox.exemption_control import REGISTRIES


def test_modules_are_derived_from_the_registry_not_typed():
    """The population must move when ``REGISTRIES`` moves.

    D-047's rule: a hand-copied registry is a registry with two statements of
    itself.  This asserts the *derivation*, so adding a registry to a new module
    grows the census subset with no edit here.
    """
    assert set(cs.modules()) == {module for module, _ in REGISTRIES}


def test_modules_collapse_duplicate_owners():
    """11 registries, 9 owners — the collapse D-280's "11 files" missed.

    Pinned as a relation, not as the literals ``11`` and ``9``, so this stays
    true as the census grows and still fails if the collapse stops happening.
    """
    assert len(cs.modules()) < len(REGISTRIES)
    assert len(cs.modules()) == len(set(cs.modules()))


def test_files_are_real_paths_under_the_test_dir():
    found = cs.files()
    assert found, "census subset is empty — the derivation is broken"
    for rel in found:
        assert rel.startswith(cs.TEST_DIR + "/")
        assert (tp.REPO_ROOT / rel).is_file()


def test_files_are_sorted_and_unique():
    """Determinism: the split is only reproducible if its input is."""
    found = cs.files()
    assert list(found) == sorted(found)
    assert len(set(found)) == len(found)


def test_files_tolerate_a_module_with_no_test_file(tmp_path):
    """A missing ``test_<module>.py`` is an absence, not an error.

    The census covers registries; whether an owner happens to have a same-named
    test file is a fact about the test layout, and coupling the pricing
    instrument to that convention would make it raise on a layout change it has
    no stake in.
    """
    (tmp_path / cs.TEST_DIR).mkdir(parents=True)
    assert cs.files(root=tmp_path) == ()


def test_files_is_a_subset_of_what_the_full_suite_expands_to():
    """The subset must be a genuine subset of the control it is compared to.

    If a census file were outside the full suite's target expansion, the two
    numbers would again be measuring different populations — which is the exact
    defect in D-280's serial-vs-sharded reading that this module corrects.
    """
    full = set(ss.expand_targets([cs.TEST_DIR], tp.REPO_ROOT))
    assert set(cs.files()) <= full


def test_price_is_not_a_receipt():
    """Structural, not advisory: no subset run can license a push.

    ``push_preflight.check`` grades a :class:`Receipt`.  :class:`Price` is a
    different type with no tree fingerprint, so there is no accidental path from
    "I timed the subset" to "I may push".
    """
    assert not issubclass(cs.Price, pp.Receipt)
    fields = {f.name for f in dataclasses.fields(cs.Price)}
    receipt_fields = {f.name for f in dataclasses.fields(pp.Receipt)}
    # The tree-pinning fields are exactly what a receipt has and a price must
    # not: without them there is nothing for `check` to verify against.
    assert "worktree" not in fields
    assert "worktree" in receipt_fields
    assert "counts" not in fields


def test_verdict_thresholds_are_q159s_own():
    assert cs.verdict(10.0, 660.0) == cs.SUBSET_CHEAP
    assert cs.verdict(300.0, 1200.0) == cs.SUBSET_MARGINAL
    assert cs.verdict(400.0, 660.0) == cs.SUBSET_NOT_CHEAP


def test_near_full_beats_cheap_on_a_tie():
    """A subset under 3 min that is still half the suite buys nothing.

    The reading in that case is "the full suite is cheap", not "the subset is a
    bargain" — so ``SUBSET_NOT_CHEAP`` must win, or the verdict would recommend
    a targeted runner precisely when there is no tax to avoid.
    """
    assert cs.verdict(100.0, 200.0) == cs.SUBSET_NOT_CHEAP


def test_verdict_survives_an_unknown_full_price():
    """``suite_price`` falls back rather than failing; the verdict must too."""
    assert cs.verdict(10.0, 0.0) == cs.SUBSET_CHEAP


@pytest.mark.parametrize("jobs", [1, 2, 14])
def test_plan_partitions_the_census_at_any_job_count(jobs):
    """Same partition obligation :func:`suite_shard.plan` carries for the suite."""
    targets = cs.files()
    shards = ss.plan(targets, jobs)
    flat = [f for s in shards for f in s]
    assert sorted(flat) == sorted(targets)
    assert len(flat) == len(set(flat))

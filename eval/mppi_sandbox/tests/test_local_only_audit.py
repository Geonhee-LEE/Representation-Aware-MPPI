"""Contract tests for the derived local-only population (D-047).

The registry under test is :data:`tree_provenance.DECLARED_LOCAL_ONLY`, and the
thing being asserted is not that it has five entries — that would be a second
hand-typed copy, which is the defect.  It is that the list agrees with a
population derived from the writers, in **both** directions, and that the rule
it states has a mechanism at every point it is enforced.
"""

from __future__ import annotations

import re

import pytest

from eval.mppi_sandbox import git_surface, local_only_audit as loa
from eval.mppi_sandbox.tree_provenance import DECLARED_LOCAL_ONLY

#: Every history-derived assertion below is split on this.  It is deliberately
#: **not** a ``skipif``: a clone that cannot answer must make these tests assert
#: something *else* and still assert it, or the CI half of the suite goes quiet
#: and the module's own vacuity finding is reproduced inside its tests.  The two
#: branches are written as `if _DECIDABLE: <real claim> else: <probe fired>`, so
#: neither surface has a path through that asserts nothing.
_SURFACE = git_surface.reading()
_DECIDABLE = _SURFACE.decidable


def _assert_undecidable(fn, *args, **kwargs):
    """The CI-side claim: the call refuses, and names *why* it refused.

    Asserting on ``.verdict`` rather than on the exception type is the point.
    "It raised" is compatible with a typo raising ``NameError``; only the
    verdict distinguishes a probe that fired from an instrument that broke.
    """
    with pytest.raises(git_surface.UndecidableSurface) as excinfo:
        fn(*args, **kwargs)
    assert excinfo.value.verdict in (
        git_surface.NO_REMOTE_BRANCHES,
        git_surface.NO_MERGE_BASE,
        git_surface.NOT_A_REPO,
    ), f"raised with an unnamed verdict: {excinfo.value.verdict}"
    return excinfo.value.verdict


def test_writer_surface_is_globbed_not_typed():
    """Every cron entry point and prompt file, discovered.

    D-045's lesson applied one registry over: a writer added next month is in
    the surface without anyone editing this package.
    """
    surface = loa.writer_surface()
    assert surface, "writer surface is empty — the audit read nothing"
    assert all(w.startswith("scripts/") for w in surface)
    assert "scripts/prompts/auto_research.md" in surface
    assert "scripts/prompts/mirror_todos.md" in surface, \
        "TODO.md's writer must be in the surface or its declaration is underived"
    assert "scripts/prompts/researcher.md" in surface


def test_no_unregistered_local_only():
    """Derived − declared.  D-046's direction: what the list is short of."""
    if not _DECIDABLE:
        _assert_undecidable(loa.unregistered_local_only)
        return
    unregistered = loa.unregistered_local_only()
    assert not unregistered, (
        "paths are written under full overwrite by a cron writer and committed "
        "by no branch this era, yet are absent from "
        f"tree_provenance.DECLARED_LOCAL_ONLY: {unregistered}"
    )


def test_no_underived_declarations():
    """Declared − derived.  The mirror, and the reason a typed vocabulary is OK.

    Without this the audit could pass by scanning nothing at all — D-042's
    asymmetry, which is why the clearing direction is never trusted alone.  A
    verb missing from :data:`local_only_audit.OVERWRITE_VOCABULARY` fails here
    instead of quietly shortening the derived population.
    """
    underived = loa.underived_declarations()
    assert not underived, (
        "declared local-only, but no writer states a full-overwrite write of "
        f"them — the scan is short or the declaration is wrong: {underived}"
    )


def test_derivation_and_declaration_are_the_same_set():
    """Stated once, as the conjunction of the two directions above."""
    if not _DECIDABLE:
        _assert_undecidable(loa.derived_local_only)
        return
    assert set(loa.derived_local_only()) == set(DECLARED_LOCAL_ONLY)


def test_every_declared_path_has_a_reason():
    """A declaration without a reason is the hole D-038 named, not an exemption."""
    for path, reason in DECLARED_LOCAL_ONLY.items():
        assert reason.strip(), f"{path} is exempt for no stated reason"


def test_durable_record_is_not_derived_as_local_only():
    """The committed-every-cycle prepend targets must fall out of the population.

    ``docs/decisions.md`` is prepended to every cycle and is not reconstructible
    from a branch diff either, so the overwrite scan alone cannot separate it
    from the five.  If this fails, ``branch_committed`` stopped doing its half
    of the work and the audit is running on the lexical route only.
    """
    if not _DECIDABLE:
        # This is the test that inverted on CI, and the inversion is the whole
        # reason git_surface exists: with no refs the fold was empty, so the two
        # durable-record paths fell *into* the local-only population.  Pin the
        # refusal here specifically, so a future clone-blindness regression
        # fails at the probe rather than by re-classifying the contrast case.
        _assert_undecidable(loa.derived_local_only)
        _assert_undecidable(loa.branch_committed)
        return
    derived = loa.derived_local_only()
    for path in ("docs/decisions.md", "docs/deliberations.md"):
        assert path not in derived, \
            f"{path} is committed by branches every cycle; it is durable record"
    assert {"docs/decisions.md", "docs/deliberations.md"} <= loa.branch_committed()


def test_repo_layout_inventory_is_not_read_as_a_write():
    """Bullet and numbered rows are scoped one row at a time.

    ``CLAUDE.md`` sits one line above ``STATE.md`` in the REVIEW read order, and
    a block-wide scope lent it ``STATE.md``'s "snapshot" — a sixth derived entry
    that was an artifact of the scope.  Regression guard for the scope, not for
    the path.
    """
    assert "CLAUDE.md" not in loa.derived_local_only()
    assert "README.md" not in loa.derived_local_only()


def test_push_guard_covers_every_declared_path():
    """D-011's second half — never stage it — has a mechanism, at full width.

    This is D-047's finding.  The guard was a literal alternation naming three
    of the five declared paths, so the two the executor added later were
    forbidden by prose and permitted by the check.  Passing now because the
    guard calls the registry; it fails again the moment someone re-types a list.
    """
    assert not loa.unguarded_declarations(), (
        "the Phase 3 push guard does not stop these declared local-only paths "
        f"from being committed: {loa.unguarded_declarations()}"
    )


def test_guard_is_derived_rather_than_copied():
    """Stronger than the above: no literal list may stand in for the registry."""
    assert loa.guard_is_derived(), (
        "scripts/prompts/auto_research.md must invoke "
        "`local_only_audit staged`; a grep alternation is a copy of "
        "DECLARED_LOCAL_ONLY and goes stale silently"
    )
    assert loa.push_guard_pattern() is None or \
        not re.search(r"STATE\|JOURNAL\|RESULTS", loa.push_guard_pattern() or "")


def test_this_branch_stages_no_local_only_file():
    """The guard, run as a test as well as at push time.

    ``tree_provenance.undeclared_drift`` cannot express this: it compares the
    worktree to ``HEAD`` and exempts these paths, so committing one both removes
    the drift and is on the allow-list.  The violation is visible only against
    the merge base.
    """
    if not _SURFACE.has_main:
        # `git diff origin/main...HEAD` exited 128 here before the probe.  That
        # one at least crashed rather than inverting, which is why it was the
        # less dangerous of the two — but a bare crash names no reason.
        _assert_undecidable(loa.staged_declarations)
        return
    staged = loa.staged_declarations()
    assert not staged, f"D-011 violation on this branch: {staged}"


def test_rule_epoch_is_read_from_the_decision_record():
    """The epoch is D-011's date, not a copy of it."""
    epoch = loa.rule_epoch()
    assert re.fullmatch(r"\d{4}-\d{2}-\d{2}", epoch)
    text = (loa.REPO_ROOT / "docs" / "decisions.md").read_text(encoding="utf-8")
    assert f"{loa.RULE_ANCHOR} — {epoch}" in text


def test_pre_epoch_violations_are_reported_not_hidden():
    """The evidence that ``branch_committed`` needs an epoch at all.

    Four ``p2-*`` branches carry snapshot-file commits dated on or before
    D-011's acceptance, two of them still in the review queue.  An empty result
    here would mean either that they were merged or deleted — in which case the
    epoch has lost its justification and should be re-argued — or that the
    ``--until`` window silently stopped matching.
    """
    if not _DECIDABLE:
        _assert_undecidable(loa.pre_epoch_commits)
        return
    pre = loa.pre_epoch_commits()
    assert pre, (
        "no pre-D-011 snapshot commits found on any live autoresearch branch; "
        "branch_committed's epoch no longer has evidence behind it"
    )
    assert set(pre) <= set(DECLARED_LOCAL_ONLY)
    for path, branches in pre.items():
        assert branches, f"{path} listed with no branch"


def test_unresolved_shell_targets_are_declared():
    """What the structural route cannot attribute gets a field, per D-042."""
    assert loa.UNRESOLVED_TARGETS, (
        "the shell route resolves only literal destinations; if nothing is "
        "declared unresolved, the declaration went stale rather than the "
        "scripts becoming literal"
    )
    surface = set(loa.writer_surface())
    for path, reason in loa.UNRESOLVED_TARGETS:
        assert path in surface, f"{path} declared unresolved but is not a writer"
        assert reason.strip()


def test_declared_local_only_paths_are_tracked():
    """An exemption for an untracked path is an exemption nobody will notice died."""
    from eval.mppi_sandbox.tree_provenance import stale_declarations

    assert not stale_declarations()


@pytest.mark.parametrize("path", sorted(DECLARED_LOCAL_ONLY))
def test_each_declaration_names_a_writer(path):
    """Per-path, so a failure says which declaration lost its writer."""
    sites = loa.derived_local_only().get(path)
    assert sites, f"{path} is declared local-only but no writer writes it"
    assert all(s.writer.startswith("scripts/") for s in sites)

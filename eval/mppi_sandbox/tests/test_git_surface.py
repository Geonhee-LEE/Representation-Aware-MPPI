"""Contract tests for the clone-capability probe.

The module exists because an empty fold over zero refs is spelled exactly like a
fold that found nothing.  So the load-bearing tests here are the ones that build
a clone *with* the blindness and check the probe names it — asserting against the
dev box alone would only ever exercise the ``DECIDABLE`` branch, which is the
half that was never broken.

Fast half: builds throwaway repos in ``tmp_path``.  No simulation.
"""

from __future__ import annotations

import subprocess

import pytest

from eval.mppi_sandbox import git_surface as gs
from eval.mppi_sandbox import local_only_audit as loa


def _run(root, *args):
    subprocess.run(("git", *args), cwd=str(root), check=True,
                   capture_output=True, text=True)


@pytest.fixture
def bare_clone(tmp_path):
    """A git repo with one commit, no remotes, no branches — CI's checkout.

    This is the fixture the whole module is about.  ``actions/checkout@v4``
    produces this shape, and every history-derived instrument read it as
    evidence of absence rather than absence of evidence.
    """
    root = tmp_path / "clone"
    root.mkdir()
    _run(root, "init", "-q", "-b", "main")
    _run(root, "config", "user.email", "t@t")
    _run(root, "config", "user.name", "t")
    (root / "f.txt").write_text("x\n", encoding="utf-8")
    _run(root, "add", "f.txt")
    _run(root, "commit", "-qm", "c")
    return root


@pytest.fixture
def full_clone(bare_clone):
    """A clone holding both halves: ``origin/main`` and an autoresearch ref.

    The positive control, and it is *constructed* rather than read off the dev
    box.  The first draft asserted ``gs.reading() == DECIDABLE`` against the real
    repo, which is true here and false on CI — so the DECIDABLE branch would have
    been exercised on exactly the surface that never had the bug, and gone
    unexercised on the one that did.  A control that only runs where the defect
    is absent is D-079's finding restated.
    """
    _run(bare_clone, "update-ref", "refs/remotes/origin/main", "HEAD")
    _run(bare_clone, "update-ref",
         "refs/remotes/origin/autoresearch/p3-fixture", "HEAD")
    return bare_clone


def test_a_clone_with_both_halves_is_decidable(full_clone):
    """The positive control, exercised on every surface this suite runs on."""
    r = gs.reading(full_clone)
    assert r.verdict == gs.DECIDABLE
    assert r.has_main and r.branch_refs == 1 and not r.shallow
    assert r.decidable
    # And the guards let it through — a probe that refused everything would
    # pass every negative test above and be useless.
    assert gs.require_branches(full_clone).decidable
    assert gs.require_main(full_clone).decidable
    assert gs.require_history(full_clone).decidable


def test_the_dev_box_reading_is_reported_not_asserted():
    """Informational: what *this* clone can answer.

    Deliberately not an assertion that the dev box is DECIDABLE. That claim is
    false on CI by construction, and making it a hard assertion is what turned
    the positive control into a second copy of the environment dependence the
    module exists to name.  What is asserted is only internal consistency —
    the verdict must follow from the three measured fields.
    """
    r = gs.reading()
    assert r.verdict in gs.VERDICTS
    if r.branch_refs == 0:
        assert r.verdict in (gs.NO_REMOTE_BRANCHES, gs.NOT_A_REPO)
    elif not r.has_main:
        assert r.verdict == gs.NO_MERGE_BASE
    elif r.shallow:
        assert r.verdict == gs.SHALLOW
    else:
        assert r.verdict == gs.DECIDABLE


def test_a_refless_clone_is_named_not_answered(bare_clone):
    """The negative control, and the defect stated as a test.

    Before the probe, this clone made ``branch_committed`` return an empty
    frozenset — indistinguishable from "the branches exist and commit nothing".
    """
    r = gs.reading(bare_clone)
    assert r.verdict == gs.NO_REMOTE_BRANCHES
    assert r.branch_refs == 0
    assert not r.decidable


def test_the_inversion_is_refused_at_its_two_call_sites(bare_clone):
    """Both blind readers now raise, with a verdict, instead of inverting.

    ``branch_committed`` is the one that inverted; ``staged_changes`` is the one
    that exited 128.  Pinning them together is deliberate — they failed
    differently and were repaired by one probe, and a later edit that fixes only
    the loud one would pass a test written about the loud one alone.
    """
    with pytest.raises(gs.UndecidableSurface) as branch_exc:
        loa.branch_committed(bare_clone)
    assert branch_exc.value.verdict == gs.NO_REMOTE_BRANCHES

    # The narrow-guard regression, pinned as its own case. Branch refs present,
    # `origin/main` absent: `require_branches` alone let this through and the
    # fold died at exit 128 six frames down. Only a --depth 1 clone of this repo
    # surfaced it; no dev-box run can, since both halves are always there.
    _run(bare_clone, "update-ref",
         "refs/remotes/origin/autoresearch/p3-narrow", "HEAD")
    with pytest.raises(gs.UndecidableSurface) as narrow_exc:
        loa.branch_committed(bare_clone)
    assert narrow_exc.value.verdict == gs.NO_MERGE_BASE
    _run(bare_clone, "update-ref", "-d",
         "refs/remotes/origin/autoresearch/p3-narrow")

    with pytest.raises(gs.UndecidableSurface) as staged_exc:
        loa.staged_changes(root=bare_clone)
    assert staged_exc.value.verdict == gs.NO_MERGE_BASE


def test_derived_population_refuses_rather_than_reclassifying(bare_clone):
    """The specific wrong answer, pinned as unreachable.

    On CI this call returned a dict containing ``docs/decisions.md`` — the path
    the module's docstring holds up as the *contrast* case.  A regression that
    removed the probe would make this test fail by returning a value, which is
    the shape of the original bug.
    """
    with pytest.raises(gs.UndecidableSurface):
        loa.derived_local_only(bare_clone)


def test_not_a_repo_is_distinct_from_a_refless_one(tmp_path):
    """Two different blindnesses must not collapse into one verdict.

    A vendored copy with no ``.git`` and a fresh CI checkout are both
    undecidable and want different fixes (ship the history vs fetch the refs),
    so a single ``UNKNOWN`` would be the vocabulary-poverty failure this package
    keeps finding one layer up.
    """
    plain = tmp_path / "tarball"
    plain.mkdir()
    (plain / "f.txt").write_text("x\n", encoding="utf-8")
    r = gs.reading(plain)
    assert r.verdict == gs.NOT_A_REPO
    assert not r.has_main and r.branch_refs == 0


def test_no_merge_base_is_reachable_and_distinct(bare_clone):
    """A clone with autoresearch refs but no ``origin/main``.

    Constructed rather than assumed: without this the ``NO_MERGE_BASE`` branch
    of :func:`git_surface.reading` would be dead code that no test enters, which
    is exactly how D-081's ``STALE`` verdict came to be unreachable inside the
    test written to prove the verdicts exist.
    """
    _run(bare_clone, "update-ref",
         "refs/remotes/origin/autoresearch/p3-fake", "HEAD")
    r = gs.reading(bare_clone)
    assert r.verdict == gs.NO_MERGE_BASE
    assert r.branch_refs == 1
    assert not r.has_main

    # ...and a branch-only fold IS answerable here, so require_branches must not
    # refuse.  An over-broad guard is a different defect, not a safer one.
    assert gs.require_branches(bare_clone).verdict == gs.NO_MERGE_BASE
    with pytest.raises(gs.UndecidableSurface):
        gs.require_main(bare_clone)


def test_every_verdict_is_reachable():
    """No verdict may be unreachable — D-081's fixture accident, pinned.

    ``SHALLOW`` is the one this cannot construct cheaply (it needs a real
    ``clone --depth``), so it is named here as knowingly unexercised rather than
    silently absent.  Naming it is the difference between a gap and a hole.
    """
    exercised = {gs.DECIDABLE, gs.NO_REMOTE_BRANCHES, gs.NO_MERGE_BASE,
                 gs.NOT_A_REPO}
    unexercised = set(gs.VERDICTS) - exercised
    assert unexercised == {gs.SHALLOW}, (
        f"verdict reachability changed: {unexercised} are unexercised. Add a "
        "fixture or state why the verdict cannot be constructed here."
    )


def test_worst_folds_by_declared_order():
    """The precedence is the tuple, not a second table.

    Ordering by ``VERDICTS.index`` means adding a verdict orders it here with no
    edit — one statement of the registry, per D-047.
    """
    decidable = gs.SurfaceReading(gs.DECIDABLE, True, 3, False)
    refless = gs.SurfaceReading(gs.NO_REMOTE_BRANCHES, True, 0, False)
    shallow = gs.SurfaceReading(gs.SHALLOW, True, 3, True)
    assert gs.worst(decidable, shallow) == gs.SHALLOW
    assert gs.worst(decidable, shallow, refless) == gs.NO_REMOTE_BRANCHES
    assert gs.worst(decidable) == gs.DECIDABLE
    assert gs.worst() == gs.DECIDABLE, "no readings is not a failure to read"


def test_the_probe_is_uncached(bare_clone):
    """A reading must not outlive the condition it described.

    Gaining a ref mid-run is ordinary (a fixture fetches, a test branches), and
    a memoised ``NO_REMOTE_BRANCHES`` would then be a stale verdict presented as
    a measurement — this module's own defect, one level in.
    """
    assert gs.reading(bare_clone).verdict == gs.NO_REMOTE_BRANCHES
    _run(bare_clone, "update-ref",
         "refs/remotes/origin/autoresearch/p3-late", "HEAD")
    assert gs.reading(bare_clone).verdict == gs.NO_MERGE_BASE

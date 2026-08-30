"""A pass count must be attributable to one tree (D-043).

Fast tests only: file hashing plus ``git`` on throwaway repos.  Nothing
simulates.

Two things these tests deliberately do **not** assert.

1. **That the real repo has no undeclared drift.**  Between an edit and its
   commit, the working copy legitimately differs from ``HEAD`` on the file being
   written — including this one.  A test asserting emptiness there would be red
   for the whole of every EXECUTE phase, and D-042's asymmetry lesson cuts both
   ways: a check whose default state is alarm gets muted, which leaves the same
   hole as no check.  Reporting live drift is
   :func:`~eval.mppi_sandbox.tree_provenance.undeclared_drift`'s job, invoked by
   the executor at one specific moment (after the doc writes, before the push).
   What the suite pins is the *mechanism* and the *declaration*.
2. **A specific fingerprint value.**  It is a hash of the whole repo; banking it
   would make every commit a test failure.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from eval.mppi_sandbox import tree_provenance as tp

# D-011 named these three explicitly in the Phase 3 push rule.  They are pinned
# separately from the rest of the declaration so a future edit cannot quietly
# drop one: losing an entry here re-admits a file to the policed surface, which
# reads as a finding rather than as a deletion.
D011_SNAPSHOT_FILES = ("STATE.md", "JOURNAL.md", "RESULTS.md")


def _run(*args: str, cwd: Path) -> None:
    subprocess.run(args, cwd=str(cwd), check=True, capture_output=True)


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    """A one-commit git repo with two files, for mechanism tests."""
    _run("git", "init", "-q", "-b", "main", cwd=tmp_path)
    (tmp_path / "claim.md").write_text("the speedup is 7.777x\n")
    (tmp_path / "code.py").write_text("VALUE = 1\n")
    _run("git", "add", "-A", cwd=tmp_path)
    _run(
        "git",
        "-c",
        "user.email=t@t",
        "-c",
        "user.name=t",
        "commit",
        "-qm",
        "init",
        cwd=tmp_path,
    )
    return tmp_path


# --- the declaration (D-038: an excluded surface is only auditable if written) ---


def test_every_declared_local_only_path_is_tracked():
    """A dead exemption is an exemption nobody notices went dead."""
    assert tp.stale_declarations() == ()


def test_every_declaration_carries_a_reason():
    for path, why in tp.DECLARED_LOCAL_ONLY.items():
        assert why.strip(), path


def test_d011_snapshot_files_stay_declared():
    for path in D011_SNAPSHOT_FILES:
        assert path in tp.DECLARED_LOCAL_ONLY, path


def test_declaration_is_wider_than_d011_named():
    """The finding this module was written on: D-011 declares 3, the tree drifts 5.

    ``TODO.md`` and ``research/feed.md`` are the same full-overwrite class and no
    branch commits either, but neither is named in the rule they obey.  If a
    later cycle proves one of them *is* committed, this assertion is the place
    that should go red rather than the exemption silently widening.
    """
    extra = set(tp.DECLARED_LOCAL_ONLY) - set(D011_SNAPSHOT_FILES)
    assert extra == {"TODO.md", "research/feed.md"}


# --- the two fingerprints have to be comparable at all ---


def test_clean_tree_has_equal_worktree_and_committed_fingerprints(repo: Path):
    """Guards the blob-header trap.

    git's own blob sha is taken over a ``blob <len>\\0`` header, so reusing it
    for one side and a bare content hash for the other would make every clean
    tree look like a finding.
    """
    st = tp.stamp(root=repo)
    assert st.worktree_fingerprint == st.committed_fingerprint
    assert st.worktree == st.committed


def test_unmodified_real_repo_file_hashes_identically_on_both_sides():
    """Same trap, checked against this repo rather than a fixture."""
    st = tp.stamp()
    shared = {
        p
        for p in st.worktree.keys() & st.committed.keys()
        if p not in tp.DECLARED_LOCAL_ONLY
    }
    agreeing = {p for p in shared if st.worktree[p] == st.committed[p]}
    # Uncommitted work in progress is expected; wholesale disagreement is the
    # header bug.  Any single agreeing path proves the hashes are comparable.
    assert agreeing, "no tracked path agrees — the two digests are incommensurable"


# --- D-043's rule: the tree that was measured must be the tree in hand ---


def test_verify_is_clean_when_nothing_moves(repo: Path):
    assert not tp.verify(tp.stamp(root=repo), root=repo)


def test_verify_catches_a_doc_write_after_the_measurement(repo: Path):
    """D-043 verbatim: measure, then prepend prose, then ship.

    The count taken at ``before`` is true of a tree that stops existing on the
    next line.
    """
    before = tp.stamp(root=repo)
    with (repo / "claim.md").open("a") as fh:
        fh.write("\n## D-041 — restates 7.777x\n")
    drift = tp.verify(before, root=repo)
    assert drift
    assert drift.changed == ("claim.md",)
    assert "claim.md" in drift.describe()


def test_local_only_files_are_not_exempt_from_verify(repo: Path):
    """The guard reads ``docs/``, so a *local-only* write still invalidates a count.

    :func:`verify` and :func:`undeclared_drift` answer different questions, and
    this is where they diverge — the declared set exempts a path from the
    worktree-vs-``HEAD`` comparison, never from before-vs-after.
    """
    (repo / "STATE.md").write_text("snapshot\n")
    _run("git", "add", "-A", cwd=repo)
    _run(
        "git", "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-qm", "s", cwd=repo
    )
    before = tp.stamp(root=repo)
    (repo / "STATE.md").write_text("snapshot rewritten mid-cycle\n")
    drift = tp.verify(before, root=repo)
    assert drift.changed == ("STATE.md",)
    assert not tp.undeclared_drift(root=repo)


def test_added_and_removed_are_reported_separately(repo: Path):
    before = tp.stamp(root=repo)
    (repo / "extra.py").write_text("X = 2\n")
    _run("git", "add", "extra.py", cwd=repo)
    (repo / "code.py").unlink()
    drift = tp.verify(before, root=repo)
    assert drift.added == ("extra.py",)
    # Tracked-but-deleted keeps its key and takes the sentinel, so it lands in
    # `changed`; `removed` is for a path leaving the index entirely.
    assert drift.changed == ("code.py",)


def test_deleted_tracked_file_is_distinguishable_from_an_empty_one(repo: Path):
    (repo / "code.py").write_text("")
    empty = tp.worktree_digests(root=repo)["code.py"]
    (repo / "code.py").unlink()
    gone = tp.worktree_digests(root=repo)["code.py"]
    assert gone == tp.MISSING
    assert empty != gone


def test_rename_is_drift_even_when_contents_are_identical(repo: Path):
    """The path is hashed alongside its content, so a move is a change."""
    before = tp.stamp(root=repo)
    _run("git", "mv", "code.py", "moved.py", cwd=repo)
    drift = tp.verify(before, root=repo)
    assert drift.added == ("moved.py",)
    assert drift.removed == ("code.py",)
    assert tp.stamp(root=repo).worktree_fingerprint != before.worktree_fingerprint


# --- the named fail-open: untracked files ---


def test_untracked_files_are_outside_the_fingerprints_but_still_counted(repo: Path):
    """They cannot reach the pushed tree, so folding them in would be a false
    mismatch — but they can change a test outcome, so they get a field."""
    before = tp.stamp(root=repo)
    (repo / "stray.py").write_text("SIDE_EFFECT = True\n")
    after = tp.stamp(root=repo)
    assert after.worktree_fingerprint == before.worktree_fingerprint
    assert not tp.verify(before, root=repo)
    assert after.n_untracked == before.n_untracked + 1
    assert after.untracked_digest != before.untracked_digest
    assert "stray.py" in after.untracked


# --- undeclared_drift: measured tree vs shipped tree ---


def test_undeclared_drift_reports_paths_outside_the_declared_set(repo: Path):
    (repo / "code.py").write_text("VALUE = 99\n")
    drift = tp.undeclared_drift(root=repo, declared={"claim.md": "test exemption"})
    assert drift.changed == ("code.py",)


def test_undeclared_drift_honours_the_exemption(repo: Path):
    (repo / "claim.md").write_text("rewritten\n")
    assert not tp.undeclared_drift(root=repo, declared={"claim.md": "test exemption"})


# --- plumbing ---


def test_stamp_survives_a_json_round_trip(repo: Path):
    st = tp.stamp(root=repo)
    back = tp.Stamp.from_json(st.to_json())
    assert back == st
    assert not tp.verify(back, root=repo)


def test_drift_is_falsy_when_empty_and_describes_itself():
    assert not tp.Drift()
    assert tp.Drift().describe() == "no drift"
    d = tp.Drift(changed=("a",), added=("b",), removed=("c",))
    assert d
    assert d.paths == ("a", "b", "c")
    assert "changed: a" in d.describe()


def test_tracked_paths_survives_an_awkward_filename(repo: Path):
    """This repo already carries ``2026-07-17"`` from a misquoted ``date``; NUL
    delimiting is what keeps enumeration correct rather than lucky."""
    weird = repo / 'odd"name.md'
    weird.write_text("x\n")
    _run("git", "add", "-A", cwd=repo)
    assert 'odd"name.md' in tp.tracked_paths(root=repo)


def test_repo_root_is_resolved_from_the_module_not_the_cwd():
    assert (tp.REPO_ROOT / "CLAUDE.md").is_file()
    assert (tp.REPO_ROOT / "eval" / "mppi_sandbox" / "tree_provenance.py").is_file()


class TestLoopWiring:
    """D-495: `declared` had three callers and none of them was REVIEW.

    Phase 3 stamps, Phase 4a-ter verifies — both *after* a suite has been
    bought. So an undeclared-drift refusal was structurally undiscoverable
    until the expensive part of the cycle was already spent, which is what
    D-494 paid three cycles to learn. These pin the cheap early call.

    Note the shape difference from `test_bottleneck_scope.py::TestLoopWiring`:
    that module has one call site, so a whole-file substring test is a real
    pin. This one has three, so the pin must be section-scoped or it passes
    vacuously off the 4a-ter block.
    """

    def test_review_section_invokes_declared(self):
        assert tp.wired_into_review(), (
            f"{tp.LOOP_PROMPT} Phase 1 REVIEW does not contain "
            f"{tp.DECLARED_INVOCATION!r} — the reading has no early caller, "
            "which is the defect D-495 was opened for."
        )

    def test_invocation_is_derived_from_the_module_name(self):
        """A typed spelling would keep matching a renamed module — D-047."""
        assert tp.DECLARED_INVOCATION == f"python3 -m {tp.__name__} declared"
        assert tp.__name__.endswith("tree_provenance")

    def test_prompt_path_exists(self):
        """`review_section` returns "" on a missing prompt rather than
        raising, so the pin above could pass vacuously if the path were
        wrong. This is the discriminator."""
        assert tp.LOOP_PROMPT.is_file()

    def test_the_pin_is_section_scoped_not_whole_file(self, tmp_path):
        """The regression this class exists to prevent.

        A prompt carrying the 4a-ter call but *no* REVIEW call must read as
        not-wired. An unscoped `in text` test would call this green.
        """
        p = tmp_path / "prompt.md"
        p.write_text(
            f"## Phase 1 — REVIEW\nread STATE.md.\n\n"
            f"## Phase 4 — REPORT\n{tp.DECLARED_INVOCATION}\n",
            encoding="utf-8",
        )
        assert tp.wired_into_review(p) is False

    def test_call_inside_review_is_wired(self, tmp_path):
        p = tmp_path / "prompt.md"
        p.write_text(
            f"## Phase 1 — REVIEW\n{tp.DECLARED_INVOCATION}\n\n"
            "## Phase 2 — PLAN\n",
            encoding="utf-8",
        )
        assert tp.wired_into_review(p) is True

    def test_absent_prompt_is_not_wired_and_does_not_raise(self, tmp_path):
        assert tp.wired_into_review(tmp_path / "nope.md") is False
        assert tp.review_section(tmp_path / "nope.md") == ""

    def test_missing_review_heading_is_not_wired(self, tmp_path):
        p = tmp_path / "prompt.md"
        p.write_text(f"## Phase 2 — PLAN\n{tp.DECLARED_INVOCATION}\n",
                     encoding="utf-8")
        assert tp.review_section(p) == ""
        assert tp.wired_into_review(p) is False

    def test_unterminated_review_section_reads_to_end_of_file(self, tmp_path):
        """REVIEW is the last section only in a truncated prompt, but the
        slice must not silently drop the body when no next heading follows."""
        p = tmp_path / "prompt.md"
        p.write_text(f"## Phase 1 — REVIEW\n{tp.DECLARED_INVOCATION}\n",
                     encoding="utf-8")
        assert tp.wired_into_review(p) is True

    def test_prose_naming_the_module_is_not_a_call(self, tmp_path):
        p = tmp_path / "prompt.md"
        p.write_text("## Phase 1 — REVIEW\nsee `tree_provenance` for drift.\n",
                     encoding="utf-8")
        assert tp.wired_into_review(p) is False

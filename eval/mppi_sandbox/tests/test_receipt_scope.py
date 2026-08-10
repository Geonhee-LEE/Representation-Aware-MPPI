"""D-177's diff-conditional receipt scope.

The exemption these tests police is the only one in the package that *widens*
what a cycle may skip, so the assertions are written from the refusal side:
the interesting cases are the ones where the scope must come back full, not
the ones where it may come back narrow.

Placement note (D-178, applied not re-learned): this is a **new** module rather
than a class inside `test_receipt_cost.py`, and that is deliberate the other
way round from 17:00's lesson.  It imports `receipt_cost` only — not
`guard_reflexivity`, not `citation_audit` — so it joins no pin's reader set,
and `guard_meta_suite()` therefore does not sweep it up.  A test that named the
pool enumerator here would put itself in the very set it is testing the
derivation of, and the derivation would then be true by self-reference.
"""

from __future__ import annotations

from eval.mppi_sandbox import receipt_cost as rc


class TestGuardMetaSuite:
    """The exempted set is derived from the tree, never typed."""

    def test_derives_a_nonempty_set(self):
        meta = rc.guard_meta_suite()
        assert meta, "no guard meta-suite derived — the exemption would be vacuous"

    def test_contains_the_four_modules_that_dominate_the_wall_clock(self):
        # D-176 priced these at 390.5s / 163.4s / 103.9s / 74.7s — 51.5% of the
        # suite between the top two alone.  If the derivation stops catching
        # them the exemption saves nothing, and it will do so *silently*, so
        # the price is what gets pinned rather than the mechanism.
        meta = set(rc.guard_meta_suite())
        for name in (
            "test_exemption_masking",
            "test_guard_reflexivity",
            "test_exemption_control",
            "test_probe_reach",
        ):
            assert f"eval/mppi_sandbox/tests/{name}.py" in meta, name

    def test_paths_are_repo_relative_and_exist(self):
        from pathlib import Path

        root = Path(__file__).resolve().parents[3]
        for rel in rc.guard_meta_suite():
            assert not rel.startswith("/"), rel
            assert (root / rel).is_file(), rel

    def test_this_module_is_not_in_its_own_subject(self):
        """The derivation must not be true by self-reference.

        If this file ever mentions the pool enumerator it enters the set it
        exists to check, and every assertion above becomes a statement about
        itself.  Pinned rather than left to care.
        """
        assert (
            "eval/mppi_sandbox/tests/test_receipt_scope.py"
            not in rc.guard_meta_suite()
        )


class TestScope:
    """`scope` fails closed: full suite unless the diff proves it need not be."""

    def test_untouched_diff_activates_the_exemption(self):
        # The second path is deliberately *not* one of the three snapshot
        # files, and it may not be named even in a comment.  The first cut used
        # one; spelling it anywhere in this file puts the module into that
        # pin's reader set and stales it (Q-128/D-179's mechanism, arriving one
        # cycle after it was written down).  The comment explaining the fix
        # re-created the failure for the same reason — a reader scan cannot
        # tell a use from a mention.  A fixture path costs nothing and
        # re-measures no pin (D-178).
        s = rc.scope(("docs/decisions.md", "README.md"))
        assert s.verdict == rc.EXEMPTION_ACTIVE
        assert s.dropped == rc.guard_meta_suite()
        assert s.triggers == ()
        assert not s.is_full

    def test_a_guard_source_voids_it(self):
        s = rc.scope(("docs/decisions.md", "eval/mppi_sandbox/guard_reflexivity.py"))
        assert s.verdict == rc.EXEMPTION_VOID
        assert s.dropped == ()
        assert s.triggers == ("eval/mppi_sandbox/guard_reflexivity.py",)
        assert s.is_full

    def test_a_meta_test_edit_voids_it_too(self):
        """Beyond D-177's letter, and the widening is the point.

        The exemption's premise is that the *claims* about the pool have not
        moved.  Editing an assertion moves them as surely as editing the code
        the assertion reads, and D-177's stated trigger (`eval/mppi_sandbox/*.py`)
        does not reach `tests/`.  Widening a void condition can only cost a
        full suite, which is the status quo.
        """
        target = rc.guard_meta_suite()[0]
        s = rc.scope((target,))
        assert s.verdict == rc.EXEMPTION_VOID
        assert s.triggers == (target,)

    def test_a_non_meta_test_edit_does_not_void_it(self):
        # The counter-case to the one above: a sandbox test that is *not*
        # about the pool leaves the pool's tests measuring the same thing.
        s = rc.scope(("eval/mppi_sandbox/tests/test_receipt_scope.py",))
        assert s.verdict == rc.EXEMPTION_ACTIVE

    def test_a_sandbox_test_is_not_mistaken_for_a_guard_source(self):
        assert not rc._is_guard_source("eval/mppi_sandbox/tests/test_x.py")
        assert rc._is_guard_source("eval/mppi_sandbox/receipt_cost.py")
        assert not rc._is_guard_source("eval/mppi_sandbox/receipt_cost.pyc")
        assert not rc._is_guard_source("eval/tests/test_run_metrics.py")
        assert not rc._is_guard_source("eval/mppi_sandbox/controllers/risk_mppi.py")

    def test_empty_meta_suite_fails_closed(self, tmp_path):
        """A broken derivation must not read as "nothing to drop".

        The two states print almost identically and only one is safe to act
        on, so `NO_META_SUITE` is a separate verdict rather than
        `EXEMPTION_ACTIVE` with an empty drop set.
        """
        s = rc.scope(("docs/decisions.md",), root=tmp_path)
        assert s.verdict == rc.NO_META_SUITE
        assert s.is_full
        assert s.dropped == ()

    def test_this_cycles_own_diff_voids_the_exemption(self):
        """The shipping cycle pays the full suite by its own rule.

        `receipt_cost.py` is a guard source and this cycle edits it, so the
        function cannot exempt the run that introduces it.  Stated as a test
        because it is the claim the D-180 entry makes about its own receipt.
        """
        s = rc.scope(("eval/mppi_sandbox/receipt_cost.py",))
        assert s.verdict == rc.EXEMPTION_VOID


class TestPytestArgs:
    """A caller that ignores the Scope object still takes a valid receipt."""

    DEFAULT = (
        "eval/mppi_sandbox/tests/",
        "eval/tests/test_path_tracking_metrics.py",
        "eval/tests/test_run_metrics.py",
    )

    def test_void_returns_the_default_untouched(self):
        s = rc.scope(("eval/mppi_sandbox/receipt_cost.py",))
        assert s.pytest_args(self.DEFAULT) == self.DEFAULT

    def test_active_ignores_each_dropped_module(self):
        s = rc.scope(("docs/decisions.md",))
        args = s.pytest_args(self.DEFAULT)
        assert args[: len(self.DEFAULT)] == self.DEFAULT
        for m in s.dropped:
            assert f"--ignore={m}" in args

    def test_no_meta_suite_returns_the_default(self, tmp_path):
        s = rc.scope(("docs/decisions.md",), root=tmp_path)
        assert s.pytest_args(self.DEFAULT) == self.DEFAULT


class TestChangedPaths:
    """The diff read is a union of three places, not one."""

    def test_reads_something(self):
        paths = rc.changed_paths()
        assert isinstance(paths, tuple)
        assert paths == tuple(sorted(paths))

    def test_describe_names_the_verdict(self):
        assert rc.EXEMPTION_VOID in rc.scope(
            ("eval/mppi_sandbox/receipt_cost.py",)
        ).describe()
        assert rc.EXEMPTION_ACTIVE in rc.scope(("docs/decisions.md",)).describe()

    def test_the_default_base_is_still_main(self):
        # Backwards compatibility is the load-bearing half of Q-129's fix: a
        # caller that passes no base must get exactly the pre-D-180 question,
        # so the narrowing can only ever be opt-in.
        assert rc.changed_paths() == rc.changed_paths(base=rc.DEFAULT_BASE)
        assert rc.DEFAULT_BASE == "main"


def _receipt(head: str, command: tuple[str, ...]) -> "object":
    from eval.mppi_sandbox import push_preflight as pp

    return pp.Receipt(
        head=head,
        worktree_fingerprint="wf",
        committed_fingerprint="cf",
        returncode=0,
        counts={"passed": 1},
        command=command,
    )


FULL_COMMAND = ("python3", "-m", "pytest", "eval/mppi_sandbox/tests/", "-q")


class TestExemptionBase:
    """Q-129: which commit the exemption's diff is taken from.

    Every assertion here is about a *refusal* resolving to a usable ref.  The
    failure mode this class exists to make unreachable is a base that is absent
    or unresolvable, because `git diff` against one of those returns nothing and
    an empty change set reads exactly like "nothing changed" — i.e. the
    exemption would activate at the moment its evidence disappeared.
    """

    def test_a_full_receipt_supplies_its_commit(self, tmp_path):
        head = _head_sha()
        p = tmp_path / "receipt.json"
        p.write_text(_receipt(head, FULL_COMMAND).to_json())
        base = rc.exemption_base(receipt_path=p)
        assert base.verdict == rc.BASE_RECEIPT
        assert base.ref == head
        assert base.is_receipt

    def test_a_narrowed_receipt_is_refused(self, tmp_path):
        # The bootstrap this refusal blocks: a scoped receipt skipped the guard
        # meta-suite, so it cannot be the evidence that the meta-suite may be
        # skipped again.  Accepting it would let the exemption certify itself
        # forward indefinitely off one full run in the distant past.
        p = tmp_path / "receipt.json"
        p.write_text(
            _receipt(
                _head_sha(),
                FULL_COMMAND + ("--ignore=eval/mppi_sandbox/tests/test_probe_reach.py",),
            ).to_json()
        )
        base = rc.exemption_base(receipt_path=p)
        assert base.verdict == rc.BASE_SCOPED_RECEIPT
        assert base.ref == rc.DEFAULT_BASE

    def test_the_narrowing_flag_is_the_one_scope_actually_emits(self):
        # Derived, not typed: `_receipt_is_full` looks for the flags
        # `Scope.pytest_args` produces, so the two cannot drift apart silently.
        args = rc.Scope(
            verdict=rc.EXEMPTION_ACTIVE,
            dropped=("eval/mppi_sandbox/tests/test_probe_reach.py",),
            triggers=(),
        ).pytest_args(("eval/mppi_sandbox/tests/",))
        assert not rc._receipt_is_full(args)
        assert rc._receipt_is_full(("eval/mppi_sandbox/tests/",))

    def test_a_missing_receipt_falls_back(self, tmp_path):
        base = rc.exemption_base(receipt_path=tmp_path / "nope.json")
        assert base.verdict == rc.BASE_NO_RECEIPT
        assert base.ref == rc.DEFAULT_BASE

    def test_an_unparseable_receipt_falls_back(self, tmp_path):
        p = tmp_path / "receipt.json"
        p.write_text("{not json")
        assert rc.exemption_base(receipt_path=p).verdict == rc.BASE_NO_RECEIPT

    def test_an_unresolvable_commit_falls_back(self, tmp_path):
        p = tmp_path / "receipt.json"
        p.write_text(_receipt("0" * 40, FULL_COMMAND).to_json())
        base = rc.exemption_base(receipt_path=p)
        assert base.verdict == rc.BASE_UNKNOWN_COMMIT
        assert base.ref == rc.DEFAULT_BASE

    def test_an_empty_head_falls_back(self, tmp_path):
        p = tmp_path / "receipt.json"
        p.write_text(_receipt("", FULL_COMMAND).to_json())
        assert rc.exemption_base(receipt_path=p).verdict == rc.BASE_UNKNOWN_COMMIT

    def test_every_verdict_yields_a_usable_ref(self, tmp_path):
        # The property that makes the whole thing safe to ignore: there is no
        # code path returning None, so a caller that reads `.ref` blindly gets
        # the conservative question rather than an exception or an empty diff.
        cases = [tmp_path / "absent.json"]
        bad = tmp_path / "bad.json"
        bad.write_text("{not json")
        cases.append(bad)
        gone = tmp_path / "gone.json"
        gone.write_text(_receipt("0" * 40, FULL_COMMAND).to_json())
        cases.append(gone)
        for path in cases:
            base = rc.exemption_base(receipt_path=path)
            assert base.ref
            assert not base.is_receipt
            assert base.verdict in base.describe()


class TestTheBaseActuallyNarrows:
    """Q-129's payload: the reason a nearer base was worth reading at all."""

    def test_a_recent_base_reports_no_more_than_main_does(self, tmp_path):
        # On a long-lived branch this is a large strict shrink (88 → 1 when the
        # fix landed).  Asserted as a subset rather than a magnitude because the
        # magnitude is a property of the branch's age, not of the code, and a
        # pinned number here would go stale on the first merge.
        from_main = set(rc.changed_paths(base="main"))
        from_head = set(rc.changed_paths(base=_head_sha()))
        assert from_head <= from_main

    def test_the_field_the_base_reads_is_one_record_writes(self):
        # The anti-D-182 pin.  Q-129 assumed this field did not exist and
        # costed a `push_preflight` change to create it; it existed all along.
        # What makes that safe to rely on is that `record` keeps writing it —
        # if it ever stops, `exemption_base` degrades to NO_RECEIPT *silently*,
        # which is the fallback, which is invisible.  So the write is pinned.
        import inspect

        from eval.mppi_sandbox import push_preflight as pp

        assert "head" in inspect.signature(pp.Receipt).parameters
        src = inspect.getsource(pp.record)
        assert "head=st.head" in src


def _head_sha() -> str:
    import subprocess

    return subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=str(rc._repo_root()),
        capture_output=True,
        text=True,
        timeout=30,
    ).stdout.strip()

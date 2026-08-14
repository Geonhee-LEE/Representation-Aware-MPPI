"""Negative controls for the typed exemption sets — and a negative control for
the negative controls.

D-076 spent a cycle discovering that a filter had never removed anything.  D-078
shipped a guard together with the tamper proving it could fire.  This file is
the generalisation: one control per registry, plus the tamper that proves
``control()`` is capable of returning ``INERT`` at all.  Without the last one
every ``BITES`` below is an assertion that the code path taken is the only path
there is.
"""

from eval.mppi_sandbox import exemption_control as ec


def test_every_declared_control_bites():
    """Tamper the registry, and something notices — for all ten reachable ones.

    8 -> 10 (D-093): :mod:`suite_memo` arrives with two file-scope allow-lists,
    ``TREE_SUFFIXES`` and ``TREE_SKIP``, and both decide what the memo's tree
    digest can see.  Narrowing either one is a *silent widening* of what the
    cache will serve — drop ``.py`` and the memo stops noticing source edits —
    so they are exactly the shape this census exists for, and both are
    controlled through ``suite_memo.digest_scope`` rather than declared.
    """
    scored = ec.controls()
    assert len(scored) == len(ec.TAMPERS) == 10
    assert [c.verdict for c in scored] == [ec.VERDICT_BITES] * 10
    assert ec.inert(scored) == ()


def test_the_control_verdicts_do_not_depend_on_how_the_module_was_launched():
    """``python -m`` used to grade this module's own registry ``INERT``.

    Running the file as ``__main__`` makes ``importlib.import_module`` load a
    *second* copy under the dotted name; the tamper then patched the copy while
    the reader ran in ``__main__``, and the control reported failure for a
    registry that was correctly wired.  One subprocess, because reproducing a
    ``__main__`` import needs one — and a control that only passes when it is
    imported the convenient way is not a control.
    """
    import subprocess
    import sys
    from pathlib import Path

    root = Path(ec.PACKAGE).parents[1]
    out = subprocess.run([sys.executable, "-m", "eval.mppi_sandbox.exemption_control"],
                         cwd=root, capture_output=True, text=True, timeout=300)
    assert out.returncode == 0, out.stderr
    assert ec.VERDICT_INERT not in out.stdout
    assert "exemption_control.DECLARED_DEF_TIME" in out.stdout
    assert out.stdout.count(ec.VERDICT_BITES) == len(ec.TAMPERS)


def test_the_readings_and_their_directions_are_pinned():
    """The magnitudes, not just the verdict — a control that moves by 0 is not one."""
    by_registry = {c.registry: c for c in ec.controls()}
    assert by_registry["magnitude_survival.SELF_DEFINING"].delta == 1
    assert by_registry["reading_record.CARRIED_FIELDS"].delta == 1
    assert by_registry["guard_reflexivity.NAME_SCOPE_CLAIMS"].delta == -2
    assert by_registry["claim_scope.SCOPED_CLAIMS"].delta == 2
    assert by_registry["claim_scope.DEGENERATE_READINGS"].delta == 1
    assert by_registry["lam_dependence.TEMPERATURE_RELEVANT"].delta == -2
    assert by_registry["predicate_vacuity.EXCLUDED_TESTS"].delta == 1
    assert by_registry["exemption_control.DECLARED_DEF_TIME"].delta == 1


def test_self_definings_zero_bite_is_a_population_fact_not_a_wiring_one():
    """The refinement D-076 could not make with one measurement.

    ``exemption_bite`` removes nothing, and the control reads ``0 -> 1``.  So
    the filter *is* wired and the population simply contains nothing it excludes
    — which is a materially weaker finding than "the filter does nothing", and
    the weaker one is the true one.

    The denominator is **derived, not re-typed**, and that is D-078's rule being
    obeyed rather than cited: D-076 published this reading as ``0 of 22`` and it
    is ``0 of 25`` today, because ``PUBLISHED`` grew three cells afterwards.  A
    test pinning ``22`` would have gone red for the registry doing its job.
    """
    from eval.mppi_sandbox import magnitude_survival as ms
    from eval.mppi_sandbox import published_ratios as pr
    removed, population = ms.exemption_bite()
    assert removed == 0
    assert population == len(pr.PUBLISHED) > 22
    scored = next(c for c in ec.controls()
                  if c.registry == "magnitude_survival.SELF_DEFINING")
    assert (scored.baseline, scored.tampered) == (0, 1)


def test_control_can_return_inert():
    """The negative control for this module.

    A no-op patch must grade ``INERT``.  If it did not, every ``BITES`` above
    would be unfalsifiable — the exact shape of D-075's vacuous test, one layer
    up.
    """
    live = ec._carried_fields()
    noop = ec.Tamper(live.registry, lambda original: original, live.read,
                     live.expect, live.reader)
    result = ec.control(noop)
    assert result.verdict == ec.VERDICT_INERT
    assert result.delta == 0
    assert "shrinks" not in result.note and "grows" in result.note


def test_control_can_return_inert_on_a_wrong_direction_move():
    """Moving is not enough — moving the wrong way is a failure, not a pass."""
    live = ec._carried_fields()
    backwards = ec.Tamper(live.registry, lambda original: original,
                          live.read, "shrinks", live.reader)
    assert ec.control(backwards).verdict == ec.VERDICT_INERT


def test_the_registry_is_restored_even_when_the_reader_raises():
    """A control that leaks its tamper poisons every later test in the run."""
    from eval.mppi_sandbox import reading_record as rr
    original = rr.CARRIED_FIELDS

    def boom() -> int:
        raise RuntimeError("reader failed")

    exploding = ec.Tamper(("reading_record", "CARRIED_FIELDS"),
                          lambda o: tuple(o) + ("x",), boom, "grows", "boom")
    try:
        ec.control(exploding)
    except RuntimeError:
        pass
    assert rr.CARRIED_FIELDS is original


def test_reads_are_attributed_by_resolved_module_not_by_attribute_name():
    """D-080's defect, as a control on synthetic source.

    Two modules declare ``REG``; only ``a``'s is read at call time.  Keying on
    the attribute name — what :func:`references` did until D-080 — hands each
    registry the *union*, so ``b.REG`` inherits a call-time read it does not
    have and is reported controllable when no control over it exists.  This is
    the whole mechanism by which ``predicate_vacuity.EXCLUDED_TESTS`` and
    ``guard_vacuity.EXCLUDED_TESTS`` were credited with each other's readers.
    """
    from pathlib import Path
    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "a.py").write_text("REG = (1,)\n")
        (root / "b.py").write_text("REG = (2,)\n")
        (root / "c.py").write_text(
            "from eval.mppi_sandbox import a\n"
            "from eval.mppi_sandbox import b\n"
            "def reader():\n"
            "    return a.REG\n"
            "def other(x=b.REG):\n"
            "    return x\n"
        )
        a_refs = ec.references(("a", "REG"), package=root)
        b_refs = ec.references(("b", "REG"), package=root)
        assert [(r.module, r.function, r.binding) for r in a_refs] == [
            ("c", "reader", ec.CALL_TIME)]
        assert [(r.module, r.function, r.binding) for r in b_refs] == [
            ("c", "other", ec.DEF_TIME)]
        # The finding: the two disagree.  Under name-keying they could not.
        assert ec.binding(("a", "REG"), package=root) == ec.CALL_TIME
        assert ec.binding(("b", "REG"), package=root) == ec.DEF_TIME
        assert ec.unresolved_reads(("a", "REG"), package=root) == ()


def test_an_unresolvable_read_is_reported_rather_than_attributed():
    """The scan states its own blind spot, so a resolved count is a lower bound."""
    from pathlib import Path
    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "a.py").write_text(
            "REG = (1,)\n"
            "def f(self):\n"
            "    return self.REG\n"
        )
        assert ec.references(("a", "REG"), package=root) == ()
        blind = ec.unresolved_reads(("a", "REG"), package=root)
        assert [(r.module, r.function) for r in blind] == [("a", "f")]


def test_the_two_excluded_tests_registries_have_different_reader_counts():
    """The magnitude D-079 published, corrected — and the count that made it wrong.

    D-079 wrote that *each* registry "is read in exactly one place".  That is
    true of ``guard_vacuity``'s and false of ``predicate_vacuity``'s, which has
    17 readers across four modules; the scan could not tell them apart, so the
    smaller reading was printed for both.  The counts are derived from the scan
    rather than re-typed, so this stays green when a reader is added — what it
    pins is the **inequality**, which is the part D-079 got wrong.
    """
    pv_refs = ec.references(("predicate_vacuity", "EXCLUDED_TESTS"))
    gv_refs = ec.references(("guard_vacuity", "EXCLUDED_TESTS"))
    assert len(gv_refs) == 1
    assert len(pv_refs) > len(gv_refs)
    assert {r.module for r in gv_refs} == {"guard_vacuity"}
    assert len({r.module for r in pv_refs}) > 1
    assert ec.unresolved_reads(("predicate_vacuity", "EXCLUDED_TESTS")) == ()


def test_q085_is_answered_by_reader_price_not_by_preference():
    """Q-085's own decision procedure, run rather than quoted.

    *"(a) 를 고르면 저렴한 non-subprocess reader 가 존재하는지부터 확인해야
    하고, 없으면 (a) 는 자동으로 죽는다."*  It exists for one registry and not
    the other, so the answer splits — which is why Q-085's premise that both
    readers run a suite could not survive being measured.
    """
    pv = ("predicate_vacuity", "EXCLUDED_TESTS")
    gv = ("guard_vacuity", "EXCLUDED_TESTS")

    assert ec.affordable_readers(gv) == ()
    assert [r.cost for r in ec.reader_cost(gv)] == [ec.SUBPROCESS]

    affordable = ec.affordable_readers(pv)
    assert affordable, "option (a) was chosen for pv — a cheap reader must exist"
    assert ("exclusion_scope", "price") in {(r.module, r.function)
                                            for r in affordable}
    # ...and the expensive ones are still priced as expensive.
    assert ("predicate_vacuity", "measure") in {
        (r.module, r.function) for r in ec.reader_cost(pv)
        if r.cost == ec.SUBPROCESS}


def test_reader_pricing_follows_a_subprocess_through_a_local_helper():
    """The control for the pricer.  A direct-call test answers Q-085 backwards.

    ``predicate_vacuity.measure`` spends its subprocess inside ``_run_recorder``;
    priced on its own body it reads ``PURE``, and Q-085's procedure would then
    say a cheap reader exists where none does.
    """
    import ast
    src = (
        "import subprocess\n"
        "def _helper():\n"
        "    subprocess.run(['true'])\n"
        "def reader():\n"
        "    return _helper()\n"
        "def clean():\n"
        "    return 1\n"
    )
    costs = ec._costs(ast.parse(src))
    assert costs["_helper"] == ec.SUBPROCESS
    assert costs["reader"] == ec.SUBPROCESS
    assert costs["clean"] == ec.PURE


def test_the_one_remaining_unreachable_registry_is_declared_not_silent():
    """Q-085 option (b), pinned: a declaration is a reading, not a comment.

    ``guard_vacuity.EXCLUDED_TESTS`` stays default-arg-only on purpose, and the
    reason is machine-checkable — its sole reader is ``SUBPROCESS``-priced, so a
    name-level control would cost a suite run per cycle and would not be run.
    """
    assert ec.unreachable() == ("guard_vacuity.EXCLUDED_TESTS",)
    assert ec.undeclared_unreachable() == ()
    assert set(ec.DECLARED_DEF_TIME) <= set(ec.unreachable())


def test_an_undeclared_unreachable_registry_is_named():
    """The clearance above must be able to go non-empty, or it says nothing."""
    original = dict(ec.DECLARED_DEF_TIME)
    try:
        ec.DECLARED_DEF_TIME.clear()
        assert ec.undeclared_unreachable() == ("guard_vacuity.EXCLUDED_TESTS",)
    finally:
        ec.DECLARED_DEF_TIME.clear()
        ec.DECLARED_DEF_TIME.update(original)


def test_a_call_time_read_is_told_apart_from_a_default_argument_one():
    """The static layer's own negative control, on synthetic source.

    Both forms read the same name; only one is patchable.  Asserting the
    distinction on source this file writes keeps the classifier honest even if
    every real registry later moves to one form.
    """
    import ast
    from pathlib import Path
    import tempfile

    src = (
        "REG = (1, 2)\n"
        "def at_def(x=REG):\n"
        "    return x\n"
        "def at_call():\n"
        "    return REG\n"
    )
    with tempfile.TemporaryDirectory() as tmp:
        (Path(tmp) / "m.py").write_text(src)
        refs = ec.references(("m", "REG"), package=Path(tmp))
        assert {(r.function, r.binding) for r in refs} == {
            ("at_def", ec.DEF_TIME), ("at_call", ec.CALL_TIME)}
        assert ec.binding(("m", "REG"), package=Path(tmp)) == ec.CALL_TIME
        assert ast.parse(src) is not None


def test_the_census_names_what_it_does_not_cover():
    """Eleven registries, ten tampered, one declared — and nothing silent.

    9 -> 11 (D-093): :mod:`suite_memo`'s two scope allow-lists, both tampered.
    The declared-not-tampered count stays at **one**.
    """
    assert len(ec.REGISTRIES) == 11
    assert ec.uncontrolled() == ()


def test_a_registry_without_a_tamper_is_named_rather_than_dropped():
    """The clearance above is a reading, so it must be able to go non-empty."""
    original = ec.REGISTRIES
    try:
        ec.REGISTRIES = original + (("exemption_control", "REGISTRIES"),)
        assert ec.uncontrolled() == ("exemption_control.REGISTRIES",)
    finally:
        ec.REGISTRIES = original


def test_this_module_gives_the_four_unwatched_lists_a_control_not_a_watcher():
    """Stated so the census is not read as having closed D-073's hole.

    ``guard_reflexivity.unwatched_exemptions`` asks *whose population is this
    list*; a control asks *does tampering it move anything*.  Five registries
    now have the second and still lack the first, and conflating them would
    report a fix that did not happen.

    ``RESOLVERS`` (D-275) is the fifth, and it entered unwatched and
    uncontrolled in the same repair, so the subset assertion below is what
    forced `_resolvers` to be written rather than the count to be bumped.  That
    is the pin working as intended: a cycle that adds a declared allow-list
    cannot leave it merely counted.
    """
    from eval.mppi_sandbox import guard_reflexivity as gr
    unwatched = set(gr.unwatched_exemptions())
    controlled = {r.split(".")[-1] for r in
                  (c.registry for c in ec.controls())}
    assert unwatched <= controlled
    assert unwatched == {"DECLARED_DEF_TIME", "DEGENERATE_READINGS",
                         "SCOPED_CLAIMS", "SELF_DEFINING",
                         "TEMPERATURE_RELEVANT", "RESOLVERS"}


def test_this_modules_own_excuse_list_entered_the_population_it_measures():
    """The census cost, paid rather than waived — twenty-second cycle running.

    :data:`DECLARED_DEF_TIME` is a typed exemption set, so writing it grew
    ``unwatched_exemptions`` from four to five within one test run.  The reply
    was a tamper, not an exception: dropping the excuse must make
    :func:`undeclared_unreachable` name the registry it was excusing.  An
    instrument that exempts its own exemption list is the failure this branch
    has recorded under D-073 and would have been repeating.
    """
    from eval.mppi_sandbox import guard_reflexivity as gr
    assert "DECLARED_DEF_TIME" in gr.unwatched_exemptions()
    assert ("exemption_control", "DECLARED_DEF_TIME") in ec.REGISTRIES
    scored = next(c for c in ec.controls()
                  if c.registry == "exemption_control.DECLARED_DEF_TIME")
    assert scored.verdict == ec.VERDICT_BITES
    assert (scored.baseline, scored.tampered) == (0, 1)

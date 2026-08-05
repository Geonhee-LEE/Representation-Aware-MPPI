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
    """Tamper the registry, and something notices — for all six reachable ones."""
    scored = ec.controls()
    assert len(scored) == len(ec.TAMPERS) == 6
    assert [c.verdict for c in scored] == [ec.VERDICT_BITES] * 6
    assert ec.inert(scored) == ()


def test_the_readings_and_their_directions_are_pinned():
    """The magnitudes, not just the verdict — a control that moves by 0 is not one."""
    by_registry = {c.registry: c for c in ec.controls()}
    assert by_registry["magnitude_survival.SELF_DEFINING"].delta == 1
    assert by_registry["reading_record.CARRIED_FIELDS"].delta == 1
    assert by_registry["guard_reflexivity.NAME_SCOPE_CLAIMS"].delta == -2
    assert by_registry["claim_scope.SCOPED_CLAIMS"].delta == 2
    assert by_registry["claim_scope.DEGENERATE_READINGS"].delta == 1
    assert by_registry["lam_dependence.TEMPERATURE_RELEVANT"].delta == -2


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


def test_both_excluded_tests_registries_are_unreachable_through_their_name():
    """The cycle's structural finding, as a reading rather than a paragraph.

    Each is read in exactly one place, and that place is a default argument.
    Rebinding the module global cannot reach any caller, so *no* monkeypatch of
    the name is a control over those readers.
    """
    assert ec.unreachable() == ("guard_vacuity.EXCLUDED_TESTS",
                                "predicate_vacuity.EXCLUDED_TESTS")
    for module in ("predicate_vacuity", "guard_vacuity"):
        refs = ec.references((module, "EXCLUDED_TESTS"))
        assert refs, f"{module}: no reference found at all"
        assert {r.binding for r in refs} == {ec.DEF_TIME}
        assert ec.binding((module, "EXCLUDED_TESTS")) == ec.DEF_TIME


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
    """Eight registries, six tampered, two excused — and nothing silent."""
    assert len(ec.REGISTRIES) == 8
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
    list*; a control asks *does tampering it move anything*.  Four registries
    now have the second and still lack the first, and conflating them would
    report a fix that did not happen.
    """
    from eval.mppi_sandbox import guard_reflexivity as gr
    unwatched = set(gr.unwatched_exemptions())
    controlled = {r.split(".")[-1] for r in
                  (c.registry for c in ec.controls())}
    assert unwatched <= controlled
    assert unwatched == {"DEGENERATE_READINGS", "SCOPED_CLAIMS",
                         "SELF_DEFINING", "TEMPERATURE_RELEVANT"}

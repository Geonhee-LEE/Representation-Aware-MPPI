"""Q-072 (b): the vacuity scan, extended from ``raise`` to boolean returns.

The expensive tests here (anything that runs a real suite under the recorder)
are marked ``slow``.  The cheap ones pin the partition's semantics, the
population's derivation, and the bounds the census reports about itself.
"""

from __future__ import annotations

import ast
import textwrap
from pathlib import Path

import pytest

from eval.mppi_sandbox import predicate_vacuity as pv


# --------------------------------------------------------------------------
# The partition — pure, no suite run
# --------------------------------------------------------------------------


def _pred(site: str, kind: str = pv.KIND_FUNCTION) -> pv.Predicate:
    module, _, qualname = site.partition(".")
    return pv.Predicate(module=module, qualname=qualname, kind=kind, lineno=1,
                        admitted_by=pv.ADMIT_SHAPE, returns=("x > 0",),
                        path=Path("/nowhere.py"))


def _obs(site: str, true: int = 0, false: int = 0, other=()) -> pv.Observation:
    return pv.Observation(site=site, true_calls=true, false_calls=false,
                          other_types=tuple(other))


@pytest.mark.parametrize("true, false, other, expected", [
    (3, 2, (), pv.VERDICT_BOTH),
    (3, 0, (), pv.VERDICT_ALWAYS_TRUE),
    (0, 3, (), pv.VERDICT_ALWAYS_FALSE),
    (0, 0, (), pv.VERDICT_UNOBSERVED),
    (3, 2, ("ndarray",), pv.VERDICT_NON_BOOLEAN),
])
def test_classify_partitions_by_observed_values(true, false, other, expected):
    pred = _pred("m.p")
    obs = {"m.p": _obs("m.p", true, false, other)} if (true or false or other) else {}
    reading, = pv.classify([pred], obs)
    assert reading.verdict == expected


def test_a_predicate_the_suite_never_called_is_unobserved_not_one_sided():
    """D-050's rule: silence from something nobody asked is not evidence.

    The whole point of keeping ``UNOBSERVED`` separate from ``ALWAYS_*`` — a
    census that merged them would report every dead helper as a candidate and
    drown the ones that were actually offered inputs.
    """
    reading, = pv.classify([_pred("m.never")], {})
    assert reading.verdict == pv.VERDICT_UNOBSERVED
    assert not reading.is_candidate


def test_non_boolean_return_is_reported_not_scored_as_one_sided():
    """``arr > 0`` is a comparison and returns an array.

    The population is admitted syntactically and therefore over-admits; this
    verdict is how the over-admission reports itself instead of masquerading as
    a finding.
    """
    reading, = pv.classify([_pred("m.arraylike")],
                           {"m.arraylike": _obs("m.arraylike", other=("ndarray",))})
    assert reading.verdict == pv.VERDICT_NON_BOOLEAN
    assert not reading.is_candidate


def test_by_evidence_orders_candidates_by_call_count():
    """One call and five thousand are the same verdict and different claims."""
    thin, recited = _pred("m.thin"), _pred("m.recited")
    readings = pv.classify([thin, recited], {
        "m.thin": _obs("m.thin", false=1),
        "m.recited": _obs("m.recited", false=5694),
    })
    assert all(r.is_candidate for r in readings)
    assert [r.predicate.site for r in pv.by_evidence(readings)] \
        == ["m.recited", "m.thin"]


# --------------------------------------------------------------------------
# The population — derived from the AST, and its refusals are counted
# --------------------------------------------------------------------------


def _scan_source(tmp_path: Path, body: str):
    (tmp_path / "m.py").write_text(textwrap.dedent(body), encoding="utf-8")
    return pv._scan(tmp_path)


def test_population_admits_comparisons_and_bool_annotations(tmp_path):
    found, _ = _scan_source(tmp_path, """
        def by_shape(x):
            return x > 0

        def by_annotation(x) -> bool:
            return x.flag

        def not_a_predicate(x):
            return x + 1
        """)
    by_site = {p.qualname: p for p in found}
    assert set(by_site) == {"by_shape", "by_annotation"}
    assert by_site["by_shape"].admitted_by == pv.ADMIT_SHAPE
    assert by_site["by_annotation"].admitted_by == pv.ADMIT_ANNOTATION


def test_a_bare_return_disqualifies_the_function(tmp_path):
    """``return`` and ``return x > 0`` in one body is not a predicate.

    Wrapping it would record ``None`` as a non-boolean and the site would score
    ``NON_BOOLEAN`` forever — a population error dressed as a finding.
    """
    found, _ = _scan_source(tmp_path, """
        def mixed(x):
            if x is None:
                return
            return x > 0
        """)
    assert found == []


def test_nested_and_decorated_predicates_are_refused_not_dropped(tmp_path):
    """The recorder patches modules and top-level classes; nothing deeper.

    Refusals are returned so the census can state its own bound.  A scan that
    filtered them before anyone could count them is the shape D-045 through
    D-052 kept finding.
    """
    found, refused = _scan_source(tmp_path, """
        import functools

        def outer(xs):
            def inner(x):
                return x > 0
            return any(inner(x) for x in xs)

        class C:
            @property
            def prop(self):
                return self.n > 0

            @functools.cached_property
            def cached(self):
                return self.n > 0
        """)
    sites = {p.qualname for p in found}
    assert sites == {"outer", "C.prop"}
    assert {p.kind for p in found if p.qualname == "C.prop"} == {pv.KIND_PROPERTY}
    assert set(refused) == {"m.outer.inner", "m.C.cached"}


def test_the_shipped_population_is_derived_and_non_trivial():
    """Six hand-written registries in this package came up short (D-045…D-052).

    Not a magic number: the assertion is that the scan finds a population at all
    and that it is dominated by properties and functions rather than by one
    module, which is what a broken owner-resolution would produce.
    """
    population = pv.predicates()
    assert len(population) > 20
    assert len({p.module for p in population}) > 5
    assert all(p.kind in (pv.KIND_FUNCTION, pv.KIND_METHOD, pv.KIND_PROPERTY)
               for p in population)


def test_excluded_tests_covers_this_file_and_the_witness_file():
    """D-060's lesson, applied before it could bite.

    This file calls the module's own predicates with inputs chosen to exercise
    both answers.  A census that watched it would score them ``BOTH`` for free —
    the instrument eating its own signal, exactly as a coverage census watching
    :mod:`guard_witness` scores all 8 of its candidates ``FIRES``.
    """
    assert "eval/mppi_sandbox/tests/test_predicate_vacuity.py" in pv.EXCLUDED_TESTS
    assert "eval/mppi_sandbox/tests/test_guard_witness.py" in pv.EXCLUDED_TESTS


def test_census_reports_the_suite_it_read_and_the_set_it_refused():
    """The bounds travel with the number, per D-038's excluded-surface rule."""
    cens = pv.Census(readings=(), refused=("m.f",), suite=pv.DEFAULT_SUITE)
    assert cens.suite == pv.DEFAULT_SUITE
    assert cens.refused == ("m.f",)
    assert "refused as unpatchable" in str(cens)


# --------------------------------------------------------------------------
# The recorder — calibrated by construction, because the historical set is 0
# --------------------------------------------------------------------------


@pytest.mark.slow
def test_calibration_census_reproduces_four_known_verdicts(tmp_path):
    """A witness beats a reading (D-060), applied to a scan with no ground truth.

    The four scratch predicates have verdicts known by construction and the
    measurement runs through the shipped :func:`_wrap`/install path, so a green
    result is evidence about the code that ships rather than about a parallel
    implementation.  This is what stands in for the empty historical
    ``CALIBRATION`` registry — an empty registry asserts nothing and reads as a
    clean bill (D-046's shape).
    """
    cens = pv.calibration_census(tmp_path)
    assert pv.miscalibrated(cens) == ()
    verdicts = {r.predicate.site: r.verdict for r in cens.readings}
    assert verdicts == pv.CALIBRATION_EXPECTED


@pytest.mark.slow
def test_the_recorder_sees_a_property_through_the_class(tmp_path):
    """37 of the 59 shipped predicates are properties.

    Patching a property means rebuilding the descriptor, not assigning over the
    attribute — assigning over it replaces the descriptor with a function and
    every read returns the function object.  If that regressed, the census would
    quietly lose two thirds of its population to ``NON_BOOLEAN``.
    """
    (tmp_path / "subject.py").write_text(textwrap.dedent("""
        class C:
            def __init__(self, n):
                self.n = n

            @property
            def positive(self):
                return self.n > 0
        """), encoding="utf-8")
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_s.py").write_text(textwrap.dedent("""
        from subject import C

        def test_both_ways():
            assert C(1).positive
            assert not C(-1).positive
        """), encoding="utf-8")
    population, _ = pv._scan(tmp_path)
    obs = pv._measure_scratch(population, tmp_path)
    reading, = pv.classify(population, obs)
    assert reading.predicate.kind == pv.KIND_PROPERTY
    assert reading.verdict == pv.VERDICT_BOTH


# --------------------------------------------------------------------------
# The first candidate, witnessed rather than read
# --------------------------------------------------------------------------


def test_the_most_recited_candidate_is_satisfiable_by_construction():
    """``guard_reflexivity._shells_out_to_git_diff``: 5694 calls, 0 True.

    D-060's rule is that reading a predicate and judging its other answer
    reachable is the unexecuted claim this package has been wrong about from
    D-045 onward.  So: construct the input.  The detector looks for a bare
    ``"diff"`` string constant, and ``local_only_audit._git("diff", ...)`` is
    exactly such a function **in this tree** — so the other answer is not
    unreachable, and the census's top candidate is an untested arm rather than a
    vacuous one.

    That distinction is the whole yield of this cycle's triage: the population
    is one-sided *for the suite*, and this witness shows the suite is what is
    one-sided, not the predicate.
    """
    from eval.mppi_sandbox import guard_reflexivity as gr

    shells_out = ast.parse(textwrap.dedent("""
        def _git(*args):
            return subprocess.run(["git", "diff", "--name-only", *args])
        """)).body[0]
    does_not = ast.parse(textwrap.dedent("""
        def _plain(*args):
            return subprocess.run(["git", "status"])
        """)).body[0]

    assert gr._shells_out_to_git_diff(shells_out) is True
    assert gr._shells_out_to_git_diff(does_not) is False


# --------------------------------------------------------------------------
# The recorder's two tallies (D-064)
# --------------------------------------------------------------------------


def test_splitting_the_recorder_left_the_value_plugin_byte_identical():
    """The seam is internal — asserted, not claimed in a comment.

    ``_PLUGIN_RECORD_VALUES`` was one constant until the per-origin tally needed
    to replace exactly half of it.  If the split ever drifts, the census this
    module ships changes without anything else in the diff saying so.
    """
    assert pv._PLUGIN_RECORD_VALUES == pv._PLUGIN_TALLY + pv._PLUGIN_WRAP
    assert pv._PLUGIN == (pv._PLUGIN_PRELUDE + pv._PLUGIN_TALLY + pv._PLUGIN_WRAP
                          + pv._PLUGIN_INSTALL + pv._PLUGIN_DUMP)


def test_both_recorders_differ_in_the_tally_and_nowhere_else():
    """One piece of four.  Wrap, install and dump are shared verbatim."""
    assert pv._PLUGIN_ATTRIBUTED == (pv._PLUGIN_PRELUDE + pv._PLUGIN_TALLY_ATTRIBUTED
                                     + pv._PLUGIN_WRAP + pv._PLUGIN_INSTALL
                                     + pv._PLUGIN_DUMP)
    assert pv._PLUGIN_TALLY not in pv._PLUGIN_ATTRIBUTED


def test_both_recorders_compile():
    """Generated source, so a syntax error would only surface mid-measurement."""
    for source in (pv._PLUGIN, pv._PLUGIN_ATTRIBUTED):
        compile(source, "predicate_vacuity_plugin.py", "exec")


def test_fold_of_a_single_origin_is_the_flat_observation():
    """The two tallies must agree when there is nothing to partition."""
    site = "m.p"
    flat = pv.Observation(site=site, true_calls=3, false_calls=1,
                          other_types=("str",))
    assert pv.fold({site: {"a.py": flat}}) == {site: flat}

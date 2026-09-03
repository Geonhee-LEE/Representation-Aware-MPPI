"""D-312 — the extremum sweep, and the three readings it splits into."""

from __future__ import annotations

import ast
import textwrap

import pytest

from eval.mppi_sandbox import extremum_reading as er


def _scan_source(tmp_path, source: str):
    (tmp_path / "probe.py").write_text(textwrap.dedent(source), encoding="utf-8")
    return er.scan_sites(tmp_path)


# --- the discriminator ----------------------------------------------------

def test_only_single_iterable_extrema_are_sites(tmp_path):
    """`max(a, b)` clamps two known values; it reads no set and is not a site."""
    sites = _scan_source(tmp_path, """
        def f(a, b, xs):
            clamp = max(a, b)
            return clamp, max(xs)
    """)
    assert [s.expression for s in sites] == ["max(xs)"]


def test_comparison_is_what_separates_the_36_from_the_176(tmp_path):
    """An extremum that is merely returned asserts no interval."""
    sites = {s.expression: s.consumed_in_comparison
             for s in _scan_source(tmp_path, """
        def stored(xs):
            return {"span": max(xs)}

        def tested(xs, width):
            return min(xs) <= width
    """)}
    assert sites == {"max(xs)": False, "min(xs)": True}


@pytest.mark.parametrize("expr,reaches", [
    ("max(xs) / min(xs) <= 10.0", True),      # through arithmetic
    ("abs(max(xs)) < 1.0", True),             # through a transparent builtin
    ("(max(xs) if xs else 0) > 3", True),     # through an IfExp
    ("record(max(xs))", False),               # consumed by an opaque call
])
def test_value_flow_to_a_comparison(tmp_path, expr, reaches):
    sites = _scan_source(tmp_path, f"""
        def f(xs, record=None):
            return {expr}
    """)
    assert any(s.consumed_in_comparison is reaches
               for s in sites if s.expression.startswith("max"))


def test_sites_carry_their_enclosing_function(tmp_path):
    """Keying by function is what keeps two roles of `min(vals)` apart."""
    sites = _scan_source(tmp_path, """
        def guard(vals):
            return min(vals) > 0

        def span(vals):
            return max(vals) / min(vals) <= 10.0
    """)
    assert {(s.function, s.expression) for s in sites} == {
        ("guard", "min(vals)"), ("span", "max(vals)"), ("span", "min(vals)")}


# --- the registry ---------------------------------------------------------

def test_registry_covers_the_live_population():
    """The whole point: no comparison-consuming site is unruled-on."""
    reading = er.sweep()
    assert reading["unregistered"] == ()
    assert reading["verdict"] == er.SWEEP_CLEAN


def test_registry_has_no_entries_the_source_lost():
    """Not a failure condition, but it should be true today (D-312)."""
    assert er.sweep()["retired"] == ()


def test_the_class_splits_three_ways_and_only_one_is_a_defect():
    by_class = er.sweep()["by_class"]
    assert by_class == {
        er.HULL_OVER_A_SET: 2,
        er.MONOTONE_UNDER_EXTENSION: 15,
        # 17 → 16 (D-321). `k_axis_bracket`'s `max(ks)` was deleted, not
        # reclassified: it spelled `interior_inadmissible_k`'s filter, and "not
        # the top walked column" is not what "interior to the run" means. The
        # class did not change shape — it lost a member because the member's
        # site stopped existing.
        # 16 → 18 (D-334). `scene_separability.is_constant` spells "all eight
        # seed values are the same" as `max(...) == min(...)`, contributing
        # both extremes. Two entrants, one class, and the class is the sound
        # one — see the registry comment for why this is the definition of
        # EXTREME_IS_THE_QUESTION rather than a hull.
        # 18 → 20 (D-349). `ttc_family_has_the_heavier_tail` (D-347) spells a
        # strict all-vs-all separation as `min(ttc) > max(rest)`, contributing
        # both extremes. Two entrants, one class, and the class is the sound
        # one for the same reason `censoring_alignment`'s four are: the
        # extremes are the binding constraints of a universal claim, not an
        # interval standing in for a set.
        # 20 → 21 (D-496). `obstacle_instrumentation.scenes_led_by`'s
        # `max(arms, key=lambda a: arms[a])` was registered by D-495's repair
        # commit itself (07698df) but that commit never re-ran this pin — the
        # commit message says so directly ("suite not re-run this cycle").
        # Same shape as `open_above`/`open_below` above: a single-endpoint
        # argmax membership test, sound under holes.
        er.EXTREME_IS_THE_QUESTION: 21,
    }


def test_every_hull_site_has_a_repair_on_record():
    """D-307's two sites are the only hull reading on the axis, and D-308
    repaired both. An empty return is the sweep's headline result."""
    assert er.unrepaired_hulls() == ()
    assert set(er.HULL_REPAIRED_BY) == {("calibrated_ladder.py", "k_axis_bracket")}


def test_hull_without_a_repair_is_a_finding(monkeypatch):
    """The guard has to be able to fire, or it is decoration."""
    monkeypatch.setattr(er, "HULL_REPAIRED_BY", {})
    assert er.unrepaired_hulls() == (
        ("calibrated_ladder.py", "k_axis_bracket", "max(unan)"),
        ("calibrated_ladder.py", "k_axis_bracket", "min(unan)"),
    )
    assert er.sweep()["verdict"] == er.SWEEP_UNREPAIRED_HULL


def test_an_unregistered_site_outranks_an_unrepaired_hull(monkeypatch):
    """Stale coverage is reported first: a registry that does not know what is
    there cannot be trusted about what is repaired."""
    monkeypatch.setattr(er, "HULL_REPAIRED_BY", {})
    monkeypatch.setattr(er, "SITE_CLASSES",
                        {k: v for k, v in er.SITE_CLASSES.items()
                         if k[0] != "margin_free.py"})
    assert er.sweep()["verdict"] == er.SWEEP_UNREGISTERED


# --- the three readings, as properties rather than as labels --------------

def test_separation_via_extremes_survives_holes():
    """`margin_free.censoring_alignment`'s reading, and the reason the class is
    not "every min/max over a set": punching a hole in either set cannot make a
    separated pair overlap."""
    censored, scoreable = [5, 6, 7], [1, 2, 3]
    assert min(censored) > max(scoreable)
    assert min([5, 7]) > max([1, 3])          # holes in both, still separated


def test_hull_over_a_set_lies_when_the_index_has_a_hole():
    """D-307 in four lines: the hull spans a measured counterexample and the
    two endpoints cannot tell you that it did."""
    contiguous, punctured = (96, 128, 160), (96, 160)
    assert (min(contiguous), max(contiguous)) == (min(punctured), max(punctured))
    walked = (64, 96, 128, 160, 176)
    inside = [k for k in walked if min(punctured) < k < max(punctured)
              and k not in punctured]
    assert inside == [128]                     # measured, non-unanimous, invisible


def test_span_is_monotone_non_decreasing_under_extension():
    """D-311's structural point, which cost an ensemble to learn: a span that
    fails a band can never be rescued by measuring more seeds."""
    ess = [5.0, 8.0, 20.0]
    span = max(ess) / min(ess)
    for extra in (4.0, 25.0, 6.0):
        ess.append(extra)
        assert max(ess) / min(ess) >= span
        span = max(ess) / min(ess)


def test_min_gap_threshold_is_monotone_the_other_way():
    """`any_lam_fits_band` can go False → True under a denser ladder and never
    back. Same shape, opposite direction — which is why the class is named for
    the monotonicity and not for the operator."""
    gaps, width = [0.9, 1.4], 0.5
    assert not min(gaps) <= width
    gaps.append(0.3)
    assert min(gaps) <= width
    for extra in (2.0, 0.8, 5.0):
        gaps.append(extra)
        assert min(gaps) <= width              # never reverts

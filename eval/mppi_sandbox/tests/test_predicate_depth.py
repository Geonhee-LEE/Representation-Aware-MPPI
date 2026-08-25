"""Q-066: do the scan's expression predicates read the same expression at the same depth?

The readings pinned here are the cycle's finding.  They are written as equalities
rather than bounds for the reason D-049 gave: an empty or unchanged result is a
clearance only while something re-derives it.
"""

from __future__ import annotations

import ast

import pytest

from eval.mppi_sandbox import guard_reflexivity as gr
from eval.mppi_sandbox import predicate_depth as pd


# --------------------------------------------------------------------------
# the population is derived, not typed
# --------------------------------------------------------------------------


def test_expr_predicates_are_globbed_from_source() -> None:
    preds = pd.expr_predicates()
    # Derived by annotation, so this must contain the two D-050 collided on.
    assert "_is_set_valued" in preds
    assert "_difference_kind" in preds
    assert len(preds) == 7


def test_every_derived_predicate_has_an_adapter() -> None:
    """D-045's rule: a typed table whose population is not derived goes short."""
    assert pd.unadapted_predicates() == ()


def test_no_adapter_names_a_deleted_predicate() -> None:
    """The mirror of the above — ``guard_direction.stale_probes``' shape."""
    assert pd.stale_adapters() == ()


def test_adapter_keys_are_exactly_the_derived_population() -> None:
    assert set(pd.ADAPTERS) == set(pd.expr_predicates())


# --------------------------------------------------------------------------
# liveness — a ladder over a non-discriminating predicate measures nothing
# --------------------------------------------------------------------------


def test_every_adapter_discriminates_its_grounds() -> None:
    """Each predicate must answer its two grounds differently at ``BARE``.

    The first draft failed this on ``_unwrap_seq``, whose grounds were two Names
    when it only reads list/tuple displays — both read ``()``.  The check caught
    a wrong probe rather than scoring a free ``FOLLOWS`` on every rung.
    """
    for pred in pd.ADAPTERS:
        pd.measure(pred)  # raises ProbeError if the grounds agree


def test_non_discriminating_grounds_raise() -> None:
    bad = dict(pd.ADAPTERS)
    bad["core_name"] = pd.Adapter(pd._call_core_name, "REGISTRY", "REGISTRY")
    original = pd.ADAPTERS.copy()
    pd.ADAPTERS.clear()
    pd.ADAPTERS.update(bad)
    try:
        with pytest.raises(pd.ProbeError, match="does not discriminate"):
            pd.measure("core_name")
    finally:
        pd.ADAPTERS.clear()
        pd.ADAPTERS.update(original)


# --------------------------------------------------------------------------
# the measured profiles
# --------------------------------------------------------------------------


def test_depth_profiles_are_the_measured_ones() -> None:
    """Q-066's answer, as a table.

    No two predicates read the same set of rungs.  ``_resolve`` declares
    ``depth=3`` and reads through exactly one wrapper; ``_difference_kind``
    declares ``depth=2`` and reads through four.  The declared number and the
    measured reach are unrelated quantities.
    """
    assert pd.profiles() == {
        "_difference_kind": ("BARE", "SET_CALL", "COMP", "CALL_1", "CALL_2"),
        "_is_set_valued": ("BARE", "CALL_1", "CALL_2"),
        "_provenance": ("BARE", "SET_CALL", "COMP"),
        "_resolve": ("BARE", "ALIAS"),
        "_unwrap": ("BARE", "SET_CALL"),
        "_unwrap_seq": ("BARE",),
        "core_name": ("BARE", "SET_CALL", "COMP"),
    }


def test_exactly_one_pair_shares_a_profile() -> None:
    """``_provenance`` and ``core_name`` are the only two that read alike."""
    profs = list(pd.profiles().values())
    assert len(profs) - len(set(profs)) == 1
    assert pd.profiles()["_provenance"] == pd.profiles()["core_name"]


def test_spelling_relation_misses_the_d050_pair() -> None:
    """The narrow relation is a lower bound, pinned as such.

    ``_guards_in`` hands ``_is_set_valued`` the operands and ``_difference_kind``
    the population, so the pair D-050 was about shares no argument spelling.  A
    scan keyed on spelling reports four pairs and none of them is the one that
    actually failed.
    """
    assert ("_difference_kind", "_is_set_valued") not in pd.co_applied()
    assert len(pd.co_applied()) == 4


def test_derivation_relation_contains_the_d050_pair() -> None:
    """Tracing to the shared loop variable recovers it."""
    assert ("_difference_kind", "_is_set_valued") in pd.co_derived()
    assert len(pd.co_derived()) == 10


def test_d050_pair_now_agrees_on_the_rungs_d050_fixed() -> None:
    """The fix is confirmed by measurement, and its limit is stated.

    D-050 added the same-module-call arm to ``_is_set_valued``.  The pair now
    agrees on ``CALL_1``/``CALL_2`` — the rungs that failure was about — and
    still differs on ``SET_CALL``/``COMP``, where ``_is_set_valued`` is
    :data:`~eval.mppi_sandbox.predicate_depth.OPAQUE` rather than shallow.
    """
    pairs = {(a, b): rungs for a, b, rungs in pd.disagreements()}
    assert pairs[("_difference_kind", "_is_set_valued")] == ("SET_CALL", "COMP")


def test_nine_of_ten_co_derived_pairs_disagree() -> None:
    """Q-066's headline: depth agreement is the exception, not the rule."""
    dis = pd.disagreements()
    assert len(dis) == 9
    pairs = {(a, b): rungs for a, b, rungs in dis}
    # The consequential one: both are handed ``right`` in ``_guards_in``.
    assert pairs[("_is_set_valued", "_provenance")] == (
        "SET_CALL", "COMP", "CALL_1", "CALL_2")
    # The only agreeing pair is absent from the disagreement list.
    assert ("_provenance", "core_name") not in pairs


# --------------------------------------------------------------------------
# OPAQUE — following is not the same as being right
# --------------------------------------------------------------------------


def test_opaque_readings_are_exactly_is_set_valued_wrappers() -> None:
    """``_is_set_valued`` answers ``True`` from the wrapper at two rungs.

    ``set(5)`` and ``{v for v in 5}`` both read set-valued because ``set`` is in
    ``_SET_CALLS`` and a comprehension is a collection whatever it iterates.
    Neither is a *bug* — a comprehension really is a collection — but neither is
    depth either, and a positive-only ladder would have scored both ``FOLLOWS``
    and reported this predicate as reading 5 of 6 rungs instead of 3.
    """
    assert pd.opaque_readings() == ("_is_set_valued@SET_CALL", "_is_set_valued@COMP")


def test_is_set_valued_calls_a_wrapped_scalar_set_valued() -> None:
    """The OPAQUE verdict, shown directly rather than through the ladder."""
    expr = ast.parse("set(5)", mode="eval").body
    assert gr._is_set_valued(expr, {}, set(), {}) is True


# --------------------------------------------------------------------------
# declared depth vs measured reach
# --------------------------------------------------------------------------


def test_declared_depths_are_read_off_signatures() -> None:
    assert pd.declared_depths() == {
        "_resolve": 3,
        "_is_set_valued": 2,
        "_difference_kind": 2,
        "acts_of": 4,
    }


def test_declared_depth_does_not_predict_measured_reach() -> None:
    """``_resolve`` declares the largest depth and reads the fewest wrappers."""
    declared = pd.declared_depths()
    prof = pd.profiles()
    resolve_reach = len(prof["_resolve"]) - 1          # minus BARE
    diff_reach = len(prof["_difference_kind"]) - 1
    assert declared["_resolve"] > declared["_difference_kind"]
    assert resolve_reach < diff_reach


# --------------------------------------------------------------------------
# what the disagreement costs at HEAD
# --------------------------------------------------------------------------


def test_provenance_depth_exposure_is_latent_not_live() -> None:
    """One entry at HEAD, re-derived rather than asserted — and accepted (D-377).

    The mechanism is real — ``_is_set_valued`` follows a same-module call and
    ``_provenance`` does not, so a registry reached through one helper is
    admitted as a guard and then classified ``DERIVED``, invisible to every
    ``TYPED`` screen.  D-050 named the refactor that would make it live and
    D-052 (b) required a stated repair; ``tail_stability`` performed exactly
    that refactor on 2026-08-20 and the repair **does not work** — see D-377,
    which tried all three spellings the docstring prescribes.

    The entry is pinned rather than driven to zero because the exposure's harm
    does not apply to this member.  The harm is that a ``TYPED`` screen skips a
    guard whose *exemption* could mask a real offence; ``tail_stability.drift``
    has no exemption.  Its only difference-shaped line appends a finding and
    continues — fail-and-report, not exempt-and-skip — so ``KIND_DIFFERENCE`` is
    a false positive on the shape and there is nothing to mask.  Driving it to
    zero makes ``drift`` ``TYPED`` → ``revocable`` → owed a ``guard_direction``
    probe, which is a git-path harness and a category error for a census check.

    A **second** entry is a different claim and must not be waved through by
    this pin: it would have to make its own argument that the harm does not
    apply.  That is why this asserts the exact tuple, not a length or a bound.
    """
    assert pd.provenance_depth_exposure() == (
        ("lam_rollout.reaching_names", "set(qualified_primitives())", "ROLLOUT_PRIMITIVES"),
        ("tail_stability.drift", "saturated_by_midpoint(scene, CENSUS)", "CENSUS"),
    )


def test_exposure_fires_on_a_registry_behind_a_helper() -> None:
    """The instrument is live: build the shape and check ``_provenance`` misses it."""
    src = 'REGISTRY = {"a"}\n\ndef _reg():\n    return REGISTRY\n'
    tree = ast.parse(src)
    consts = gr._set_valued_constants(tree)
    fns = {n.name: n for n in tree.body if isinstance(n, ast.FunctionDef)}
    direct = ast.parse("REGISTRY", mode="eval").body
    behind = ast.parse("set(_reg())", mode="eval").body
    assert gr._provenance(direct, consts, set(), set())[0] == gr.PROV_TYPED
    assert gr._provenance(behind, consts, set(), set())[0] == gr.PROV_DERIVED
    # ...while _is_set_valued reads through the same helper.
    assert gr._is_set_valued(behind, consts, set(), fns) is True


def test_report_runs() -> None:
    text = pd.report()
    assert "depth disagreements among them: 9" in text
    assert "provenance depth exposure" in text

# SPDX-License-Identifier: BSD-3-Clause
"""Q-157's migration partition: the classes, and the two claims that matter."""

from __future__ import annotations

import ast

import pytest

from eval.mppi_sandbox import window_axis_migration as M
from eval.mppi_sandbox import window_axis_reach as W


def _expr(src: str) -> ast.expr:
    return ast.parse(src, mode="eval").body


def _fn(src: str) -> ast.FunctionDef:
    return ast.parse(src).body[0]


# --------------------------------------------------------------------------
# The discriminator is derived, not typed.
# --------------------------------------------------------------------------

def test_weight_param_is_read_off_each_resolver_signature():
    """The `float` parameter is found by annotation, not by the name "weight"."""
    scalars = M.scalar_resolvers()
    assert scalars, "no scalar resolvers — the census would be vacuous"
    for resolver, param in scalars.items():
        import importlib
        import inspect
        fn = getattr(importlib.import_module(resolver[0]), resolver[1])
        ann = inspect.signature(fn).parameters[param].annotation
        text = ann if isinstance(ann, str) else getattr(ann, "__name__", str(ann))
        assert "float" in str(text)


def test_cost_field_resolver_has_nothing_to_migrate():
    """`window_axis_key.lookup` already carries the field, so it is not scalar."""
    aware = [r for r in W.RESOLVERS if W.grade_resolver(*r) == W.COST_FIELD]
    assert aware, "no axis-aware resolver — window_axis_reach's premise is gone"
    for r in aware:
        assert M.weight_param(r) is None
        assert r not in M.scalar_resolvers()


def test_every_argument_form_has_a_cost_class():
    """A new form must be priced, not silently dropped into a default."""
    assert set(M.FORMS) == set(M.COST_CLASS), \
        "a declared form is unpriced, or a priced form is undeclared"
    for form in M.FORMS:
        assert M.cost_class(form) in {
            M.MECHANICAL, M.SITE_LOCAL, M.SIGNATURE, M.DATA_MODEL}
    with pytest.raises(LookupError):
        M.cost_class("NOT_A_FORM")


def test_classify_only_returns_declared_forms():
    """The declaration is not decorative: every graded site is in it."""
    assert {s.form for s in M.sites()} <= set(M.FORMS)


# --------------------------------------------------------------------------
# classify() actually discriminates.
# --------------------------------------------------------------------------

@pytest.mark.parametrize("src,expected", [
    ("10.0", M.LITERAL),
    ("row.weight", M.RECORD_FIELD),
    ("self.weight", M.RECORD_FIELD),
    ("default_weight()", M.DERIVED),
    ("weights[0]", M.COMPUTED),
    ("w * 2", M.COMPUTED),
])
def test_classify_forms_independent_of_enclosing_function(src, expected):
    assert M.classify(_expr(src), None) == expected


def test_name_is_forwarded_only_when_it_is_a_parameter():
    """The same expression grades differently by where it is bound."""
    param = _fn("def f(weight):\n    pass\n")
    local = _fn("def f():\n    weight = 1.0\n")
    arg = _expr("weight")
    assert M.classify(arg, param) == M.FORWARDED
    assert M.classify(arg, local) == M.LOCAL
    assert M.cost_class(M.FORWARDED) != M.cost_class(M.LOCAL)


def test_missing_argument_is_defaulted():
    assert M.classify(None, None) == M.DEFAULTED


# --------------------------------------------------------------------------
# The census agrees with the one it extends.
# --------------------------------------------------------------------------

def test_population_matches_window_axis_reach_blind_consumers():
    """Same sites as D-275's blind production consumers — no second census.

    `window_axis_reach` grades a site by its resolver's signature; this module
    grades the argument at the same site. They must be looking at the same
    call sites, or one of the two numbers is about a population nobody named.
    """
    blind = {(c.path, c.line) for c in W.consumers()
             if not c.is_test and c.verdict != W.AXIS_AWARE}
    here = {(s.path, s.line) for s in M.partition().production}
    assert here == blind


def test_resolver_definitions_are_excluded():
    """`window_axis_key.lookup` calls a scalar resolver in its own body.

    Counting that call would bill the migration for the one production
    function that already carries a cost field — the mirror of the trap
    `window_axis_reach.consumers` documents, and the first reading this
    module produced.
    """
    sites = M.sites()
    assert sites, "empty census"
    for module, attr in W.RESOLVERS:
        short = module.rsplit(".", 1)[-1]
        assert not [s for s in sites
                    if s.path.endswith(f"{short}.py") and s.function == attr]


# --------------------------------------------------------------------------
# The findings.
# --------------------------------------------------------------------------

def test_no_production_site_passes_a_literal():
    """Q-157's cheap-migration assumption does not hold in production.

    The lean toward (b) priced the work as a call-site edit on the strength of
    the test sites passing literals. Not one production caller does.
    """
    p = M.partition()
    assert p.production, "empty production census"
    assert p.mechanical_production == ()
    assert p.forms(test=False)[M.LITERAL] == 0


def test_the_test_half_of_the_lean_does_hold():
    """Counter-weight: most test sites really are mechanical, so the
    partition is discriminating rather than uniformly pessimistic."""
    p = M.partition()
    mechanical = p.costs(test=True)[M.MECHANICAL]
    assert mechanical > len(p.test) / 2


def test_the_enforcing_site_needs_a_data_model_change():
    """The site D-275 called the reason to do this is in the priciest class.

    `comparison_headroom.certify` is the family's only production
    `BLIND_ENFORCEMENT` site and it resolves at `row.weight`, so reaching it
    means `Headroom` grows a cost field and every producer fills it.
    """
    enforcing = [c for c in W.consumers()
                 if not c.is_test and c.verdict == W.BLIND_ENFORCEMENT
                 and "comparison_headroom" in c.path]
    assert len(enforcing) == 1, "the enforcing site moved — re-read D-275"
    site = next(s for s in M.partition().production
                if (s.path, s.line) == (enforcing[0].path, enforcing[0].line))
    assert site.form == M.RECORD_FIELD
    assert site.cost == M.DATA_MODEL


def test_data_model_sites_are_enumerable():
    """A cost class you cannot list is one `published_ratios` would refuse."""
    p = M.partition()
    listed = p.data_model_production
    assert len(listed) == p.costs(test=False)[M.DATA_MODEL]
    assert all(s.form == M.RECORD_FIELD for s in listed)
    for s in listed:
        assert str(s) in M.report()


def test_report_is_non_vacuous():
    text = M.report()
    p = M.partition()
    assert f"{p.total} scalar-resolving call sites" in text
    assert M.DATA_MODEL in text

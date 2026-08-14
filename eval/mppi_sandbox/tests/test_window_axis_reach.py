# SPDX-License-Identifier: BSD-3-Clause
"""D-275: how far D-273's axis question reaches, and where it cannot be put."""

from __future__ import annotations

import ast
import inspect

import pytest

from eval.mppi_sandbox import window_axis_key, window_axis_reach as war


def test_cost_field_param_is_read_off_the_resolver_that_can_ask():
    """The capability is named by `window_axis_key.lookup`, not typed here."""
    name = war.cost_field_param()
    params = inspect.signature(window_axis_key.lookup).parameters
    assert name in params
    ann = params[name].annotation
    assert "Mapping" in str(ann)


def test_cost_field_param_refuses_a_resolver_that_cannot_ask(monkeypatch):
    """If the asking resolver lost its cost field, this raises rather than
    guessing a name — the alternative is silently grading everything blind."""
    def scalar_only(path, scenario, controller, weight: float):
        raise AssertionError("not called")

    monkeypatch.setattr(window_axis_key, "lookup", scalar_only)
    with pytest.raises(LookupError):
        war.cost_field_param()


def test_the_index_is_scalar_only():
    """The finding, at the API: nowhere to put `w_voo`."""
    assert war.grade_resolver(
        "eval.mppi_sandbox.lam_window_index", "resolve") == war.SCALAR_ONLY
    assert war.grade_resolver(
        "eval.mppi_sandbox.lam_window_key", "lookup") == war.SCALAR_ONLY


def test_grading_is_not_uniformly_blind():
    """Non-vacuity: `COST_FIELD` is reachable, so `SCALAR_ONLY` discriminates."""
    grades = set(war.resolvers().values())
    assert war.COST_FIELD in grades and war.SCALAR_ONLY in grades


def test_enforcement_closure_sees_one_level_below_the_raise():
    """`certify` resolves; `assert_certified` raises. The enclosing-function
    test alone misses it, which is the reading this module first produced."""
    from eval.mppi_sandbox import comparison_headroom as ch

    certify = ast.parse(inspect.getsource(ch.certify)).body[0]
    assert not war._raises(certify), "certify itself must not raise"

    enforcers = war.enforcing_functions()
    assert ("eval.mppi_sandbox.comparison_headroom", "certify") in enforcers
    assert ("eval.mppi_sandbox.comparison_headroom", "assert_certified") in enforcers

    sites = [c for c in war.census().blind_enforcement
             if c.function == "certify"]
    assert sites, "the enforcing axis-blind resolve site must be reported"


def test_enforcement_closure_is_not_universal():
    """An over-approximation that swallows everything grades nothing. Most
    axis-blind consumers must remain plain `AXIS_BLIND`."""
    c = war.census()
    assert c.blind, "some consumer must be blind-but-not-enforcing"
    assert len(c.blind_enforcement) < len(c.blind)


def test_only_the_axis_module_resolves_axis_aware_in_production():
    """D-273's instrument reaches exactly the cell D-273 wrote it for.

    Stated structurally rather than as a count: every production consumer that
    can put the axis question lives in `window_axis_key` itself.
    """
    aware = [c for c in war.census().production if c.verdict == war.AXIS_AWARE]
    assert aware, "the q154 lookup must be found, or the scan is broken"
    assert {c.path for c in aware} == {"eval/mppi_sandbox/window_axis_key.py"}


def test_resolver_definitions_are_not_counted_as_consumers():
    """`lam_window_index.resolve` calls `lam_window_key.lookup` internally;
    counting that would make the index look like it consults the key guard on
    the caller's behalf, when it is the call that discards the cost field."""
    inside = [c for c in war.census().consumers
              if c.path == "eval/mppi_sandbox/lam_window_index.py"
              and c.function == "resolve"]
    assert inside == []


def test_every_production_window_importer_is_classified():
    """Keeps :data:`RESOLVERS` honest — a new production module importing the
    key guard is either a registered resolver or a scanned consumer.

    Scoped to production because a test may legitimately import the verdict
    constants without resolving anything (`test_operating_point_certification`
    does), and a guard that grows a name-list every time someone writes a test
    is a guard that gets edited rather than read.
    """
    consumers = {c.path for c in war.census().consumers}
    resolver_mods = {m for m, _ in war.RESOLVERS}
    checked = 0
    for mod in war.window_importers():
        if ".tests." in mod or mod in resolver_mods:
            continue
        if mod in war.NON_RESOLVING_IMPORTERS:
            continue
        path = mod.replace(".", "/") + ".py"
        checked += 1
        assert path in consumers, (
            f"{mod} imports lam_window_key but neither resolves nor consumes; "
            "register it in RESOLVERS or NON_RESOLVING_IMPORTERS")
    assert checked, "no production importer was checked — the scan is vacuous"


def test_report_names_the_blind_enforcement_sites():
    """A count alone would invite minimising it; the members are the payload."""
    text = war.report()
    assert war.BLIND_ENFORCEMENT in text
    assert "comparison_headroom.py" in text

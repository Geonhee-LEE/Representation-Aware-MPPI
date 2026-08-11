"""Tests for :mod:`key_discrimination`.

Two things are pinned here and they carry different weight.

The first is a **fact about today's tree**: the narrow key D-196 deferred reads
``NARROWED_NOT_SEPARATED``.  That pin is what stops a fifth cycle from
re-proposing it as obviously-correct — the measurement now lives in the suite
instead of in one journal paragraph.

The second is that the instrument **can say the other thing**.  A discrimination
reading pinned only on the case where it fires would be a watcher nobody has
shown can pass (D-058), and one that only ever returns
``NARROWED_NOT_SEPARATED`` would look identical to a correct one on this tree.
So the synthetic keys below drive both directions, and — the load-bearing pair —
one key that narrows **hard** without separating and one that separates
**without** narrowing much.  If those two graded the same, the module would be
reporting one number under two names, which is the conflation it was written to
prevent.
"""

from __future__ import annotations

import pytest

from eval.mppi_sandbox import key_discrimination as kd


# --------------------------------------------------------------------------
# Today's tree: the reading D-196 deferred.
# --------------------------------------------------------------------------

def test_the_narrow_key_narrows_but_does_not_separate():
    """The whole finding, in one assertion."""
    r = kd.measure()
    assert r.verdict == kd.NARROWED_NOT_SEPARATED
    assert r.narrowing > 2.0, "the narrow key really is much smaller"
    assert abs(r.discrimination) < 0.05, (
        "...and the composition did not move, which is why 'smaller' bought "
        "nothing")


def test_the_verdict_does_not_turn_on_where_the_margin_sits(monkeypatch):
    """A reading that flipped with the threshold would be worth little."""
    for margin in (0.02, 0.10, 0.50, 0.90):
        monkeypatch.setattr(kd, "SEPARATION_MARGIN", margin)
        assert kd.measure().verdict == kd.NARROWED_NOT_SEPARATED


def test_reprobe_is_the_lone_non_live_narrow_hit():
    """Why it looked like the right key: on this tree it does catch it."""
    r = kd.measure()
    verdicts = kd.population()
    caught = [n for n in r.narrow_names if verdicts.get(n) != "LIVE"]
    assert caught == ["reprobe"]
    assert len(r.narrow_names) > 5, (
        "and it catches it alongside a crowd of LIVE names — the coincidence "
        "D-193 and D-196 both rejected")


def test_no_operator_invoked_verdict_was_issued():
    """`reprobe` stays in the residue.  The key did not earn its removal."""
    assert kd.population()["reprobe"] == "UNREACHED"
    from eval.mppi_sandbox import consumer_reach as cr
    assert "OPERATOR_INVOKED" not in cr.VERDICTS


# --------------------------------------------------------------------------
# The instrument can go the other way.
# --------------------------------------------------------------------------

def _key_over(names):
    """A key matching exactly ``names``, ignoring the prose."""
    wanted = set(names)
    return lambda name, prose: name in wanted


def _split_population():
    verdicts = kd.population()
    live = sorted(n for n, v in verdicts.items() if v == "LIVE")
    other = sorted(n for n, v in verdicts.items() if v != "LIVE")
    return live, other


def test_a_separating_key_is_graded_separates():
    """Narrow set is all non-``LIVE`` ⇒ it selects for the property."""
    live, other = _split_population()
    assert len(other) >= kd.MIN_HITS, "population has a residue to select from"
    r = kd.measure(wide=_key_over(live[:30] + other[:5]),
                   narrow=_key_over(other[:5]))
    assert r.verdict == kd.SEPARATES
    assert r.discrimination > kd.SEPARATION_MARGIN


def test_separating_without_narrowing_still_separates():
    """Discrimination is the reading; narrowing is not a precondition."""
    live, other = _split_population()
    wide = _key_over(live[:4] + other[:4])
    narrow = _key_over(other[:8] if len(other) >= 8 else other)
    r = kd.measure(wide=wide, narrow=narrow)
    assert r.narrowing <= 1.5, "barely smaller"
    assert r.verdict == kd.SEPARATES


def test_narrowing_hard_without_separating_is_not_enough():
    """The failure mode the module exists for, driven synthetically."""
    live, _ = _split_population()
    r = kd.measure(wide=_key_over(live[:40]), narrow=_key_over(live[:4]))
    assert r.narrowing >= 5.0
    assert r.verdict == kd.NARROWED_NOT_SEPARATED


# --------------------------------------------------------------------------
# Negative controls.
# --------------------------------------------------------------------------

def test_a_key_matching_nothing_is_vacuous_not_perfect():
    """Zero hits ⇒ zero ``LIVE`` hits ⇒ a flawless score for an untested key."""
    live, _ = _split_population()
    r = kd.measure(wide=_key_over(live[:30]), narrow=_key_over([]))
    assert r.verdict == kd.VACUOUS
    assert r.verdict != kd.SEPARATES


def test_a_key_below_min_hits_is_vacuous():
    """Composition over one or two names is an anecdote, not a reading."""
    live, other = _split_population()
    r = kd.measure(wide=_key_over(live[:30]),
                   narrow=_key_over(other[:kd.MIN_HITS - 1]))
    assert r.verdict == kd.VACUOUS


def test_an_unmeasured_wide_control_cannot_license_a_verdict():
    """No control ⇒ no reading.  'Few hits' alone is D-196's mistake."""
    _, other = _split_population()
    r = kd.measure(wide=_key_over([]), narrow=_key_over(other[:5]))
    assert r.verdict == kd.VACUOUS


# --------------------------------------------------------------------------
# The two component keys, exercised directly.
# --------------------------------------------------------------------------

def test_the_narrow_key_requires_a_recorded_return_not_just_a_call():
    prose = "`foo('STATE.md')` was run and it did something"
    assert kd.called_with_argument("foo", prose)
    assert not kd.called_with_recorded_return("foo", prose)

    prose = "`foo('STATE.md')` over one entrant -> `INERT_COMPOSED` gen-1"
    assert kd.called_with_recorded_return("foo", prose)


def test_a_bare_mention_is_not_a_call_site():
    """D-189, still: a mention is not a call."""
    assert not kd.called_with_argument("foo", "`foo` is a nice function")
    assert not kd.called_with_argument("foo", "we ran foo('x') unquoted")
    assert not kd.called_with_argument("foo", "`foo()` takes no argument")


def test_the_return_token_ignores_short_shoutier_words():
    """``CI`` and ``PR`` are not verdicts."""
    assert not kd.called_with_recorded_return("foo", "`foo('x')` -> `CI` green")
    assert kd.called_with_recorded_return("foo", "`foo('x')` -> `CONTENT_READ`")


def test_the_return_window_is_bounded():
    """A verdict three paragraphs later is not this call's return value."""
    near = "`foo('x')` -> `INERT_COMPOSED`"
    far = "`foo('x')`" + ("z" * (kd.RETURN_WINDOW + 20)) + "`INERT_COMPOSED`"
    assert kd.called_with_recorded_return("foo", near)
    assert not kd.called_with_recorded_return("foo", far)


def test_population_is_population_b():
    """The verdict would be issued into module-level functions, so measure there."""
    from eval.mppi_sandbox import consumer_reach as cr
    assert set(kd.population()) == {d.name for d in cr.module_functions()}


def test_report_states_both_numbers_separately():
    text = kd.report()
    assert "narrowing" in text and "discrimination" in text
    assert kd.NARROWED_NOT_SEPARATED in text

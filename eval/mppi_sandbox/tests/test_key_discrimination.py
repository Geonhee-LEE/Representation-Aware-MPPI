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
    # 2.7% through D-224. Reads 9.7% as of D-225, because `walk_cells` entered
    # the narrow hit set as a second non-LIVE name (see the rename below). Reads
    # 15.2% as of D-264: `arm_audibility.required_arm_scale` entered as a third,
    # and the previous bound was 15.0% — the watch the D-225 note asked for
    # fired one cycle later. The bound is re-stated rather than the finding
    # re-read: 15.2% is still about half of SEPARATION_MARGIN and the verdict is
    # unmoved. But the trend is now three readings going one way (2.7 -> 9.7 ->
    # 15.2) and each was a single new name, so the next name to land here is
    # likely to be the one that forces D-196's deferred question rather than
    # another re-statement.
    #
    # D-342: it was neither. The reading crossed 0.20 (-> 0.2014) on a cycle
    # that added **no** name to the narrow set. Measured on both sides of
    # D-341: narrow is Composition(hits=16, live=11) at e4070a4 and at
    # 218beca — byte-identical, same 16 names. What moved was the *control*:
    # wide went 60/53 -> 63/56, so its non-LIVE fraction fell 11.67% -> 11.11%
    # and the difference rose by exactly that 0.0056. Three ordinary LIVE
    # functions landing in the wide key pushed `discrimination` through a rung,
    # and the narrow key — the thing the verdict is about — did not move at all.
    #
    # So the trend read as "each was a single new name" was never one trend.
    # `discrimination` is a difference of two fractions and either end can move
    # it; a bound hand-tightened onto the difference is squeezed every time any
    # cycle adds a called function anywhere in the package, for reasons having
    # nothing to do with the key. That is the same failure the D-225 note
    # describes at 0.10 -> 0.20, which is why the rung is not moved a third
    # time. The module docstring already says what to do here: when a reading
    # lands near the line, measure a second axis rather than moving the line.
    #
    # The second axis costs nothing because it is already in the Reading: the
    # narrow composition on its own. It is the stable one, and it is what
    # "the composition did not move enough to separate" was always trying to
    # say. The difference is still asserted, against SEPARATION_MARGIN itself
    # rather than against a tighter literal — below that margin *is* the
    # verdict, and a second constant restating it can only drift away from it.
    assert (r.narrow.hits, r.narrow.live) == (16, 11), (
        "the narrow key's own composition — the axis the verdict is about, and "
        "the one D-341 left untouched while the difference crossed a rung")
    assert abs(r.discrimination) < kd.SEPARATION_MARGIN, (
        "...and the composition did not move enough to separate, which is why "
        "'smaller' bought nothing")


def test_the_verdict_does_not_turn_on_where_the_margin_sits(monkeypatch):
    """A reading that flipped with the threshold would be worth little.

    The claim is bounded, and the bound is the measurement itself.  Any margin
    **above** the measured discrimination reads ``NARROWED_NOT_SEPARATED``, and
    the default 0.25 sits well clear of it — so the verdict is
    not an artefact of where 0.25 was put, which is what this test exists to
    say.  Below the measurement the verdict must flip, and asserting otherwise
    would be asserting the instrument is broken: a margin under the measured
    9.7% is a decision to *call* 9.7% separation, not a different reading of
    the same tree.  Both directions are driven here so that neither a drifting
    measurement nor a silently-retuned constant can pass unnoticed.
    """
    measured = abs(kd.measure().discrimination)

    # Rungs were (0.10, 0.50, 0.90) through D-224, when the measurement read
    # 2.7%. D-225 tripled it to 9.7% and 0.10 stopped being "an order of
    # magnitude clear" — it cleared by 0.003, which is a rung about to fail for
    # reasons having nothing to do with what it tests. Lowest rung moved to
    # 0.20; the assertion below is what caught the squeeze and is left in place.
    #
    # D-342: the squeeze recurred at 0.20, and the assertion caught it — but the
    # thing it caught was the *control* being diluted by three ordinary LIVE
    # functions, with the narrow key unmoved (see the sibling test). Moving the
    # rung a third time would buy one more cycle and re-arm the same trap, since
    # the lowest rung is a hand-typed literal chasing a difference either end can
    # move. So it is derived instead. What this test is for is the *shape* of the
    # verdict — every margin above the measurement reads one way, every margin
    # below reads the other — and that shape is stated relative to the
    # measurement, never relative to a constant. The drift watch the literal was
    # doing has moved to the sibling test's narrow-composition pin, which is the
    # axis that actually moves when the key changes.
    #
    # The one bound worth typing is the real tree's: the shipped margin must
    # clear the shipped measurement, or the verdict on this tree *is* an
    # artefact of where 0.25 was put. That is asserted once, on the default.
    assert kd.SEPARATION_MARGIN > measured, (
        f"the shipped margin {kd.SEPARATION_MARGIN} fell to/below the measured "
        f"discrimination {measured:.3f} — the verdict on today's tree is now an "
        f"artefact of the threshold; re-read the finding, do not move the line")

    for margin in (measured + 0.01, 0.50, 0.90):
        monkeypatch.setattr(kd, "SEPARATION_MARGIN", margin)
        assert kd.measure().verdict == kd.NARROWED_NOT_SEPARATED

    # ...and the instrument is not stuck on one answer: put the margin under
    # the measurement and it says the other thing.
    monkeypatch.setattr(kd, "SEPARATION_MARGIN", measured / 2)
    assert kd.measure().verdict == kd.SEPARATES


def test_reprobe_is_no_longer_the_lone_non_live_narrow_hit():
    """Why it looked like the right key: on this tree it does catch it.

    It no longer catches it *alone*. D-225's `paired_step.walk_cells` entered the
    narrow key's hit set as a second non-`LIVE` name, and the test was renamed
    rather than re-pinned because "lone" was the whole content of the old name.
    D-264's `arm_audibility.required_arm_scale` is now a third, D-304's
    `calibrated_ladder.attribution_separability` a fourth, and D-332's
    `scene_transfer.retake_scene` a fifth. The direction of D-196's finding is
    unchanged and in fact reinforced four times over: a key proposed for its
    precision now admits *four* further unreached names, so the residue it was
    meant to isolate is less isolated on every cycle that adds a module, not
    more.

    D-332's entrant arrived by a **rename**, not a new module — the same
    function was called `retake_cut_in` on the previous tree and did not hit
    this key. That is worth recording: the key discriminates on name shape, so
    the population it isolates moves when nothing about the code's behaviour
    does, which is a sharper version of the same objection.
    """
    r = kd.measure()
    verdicts = kd.population()
    caught = [n for n in r.narrow_names if verdicts.get(n) != "LIVE"]
    assert caught == ["attribution_separability", "reprobe",
                      "required_arm_scale", "retake_scene", "walk_cells"]
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

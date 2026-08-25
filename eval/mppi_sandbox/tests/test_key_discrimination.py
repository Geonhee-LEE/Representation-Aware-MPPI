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
    # The single entrant (D-377) is `tail_stability.drift`'s restored call to
    # `saturated_by_midpoint(scene, CENSUS)` — a called-with-argument site, which
    # is exactly what the narrow key counts. This is the composition moving for
    # an ordinary reason, and the note above is why that does not touch the
    # verdict: the difference stays under `SEPARATION_MARGIN`, so "narrowed, not
    # separated" still holds and no rung is moved to keep it holding.
    #
    # D-381: 17/12 -> 18/13, one LIVE entrant from D-380's `cycle_artifacts`
    # commit. Measured on both sides — 8b2c9f9 reads (17, 12), 9fb0bce reads
    # (18, 13) — so it is an ordinary join, same class as the D-377 entrant
    # above, and the verdict is again unmoved.
    #
    # What this pin caught is worth more than what it says. D-380's tree was
    # **stranded and ungraded**: the commit that moved this census never ran a
    # suite, so the red sat latent on disk and the first cycle to pay for a
    # suite inherited it. That is precisely why `cycle_artifacts stranded`
    # prints "budget a suite run to clear, not just a push" (D-112) and why a
    # strand is a finding rather than a tidiness note — an unpushed tree is
    # also an unmeasured one.
    #
    # This census is in neither `census_preempt.CENSUSES` nor its `UNCOVERED`
    # list, so the ~2 s pre-empt pass could not have caught it and did not
    # admit that it wasn't looking — the exact defect `consumer_reach_residue`'s
    # docstring names (D-344), one census over.
    # D-395: 18/13 -> 19/14, and the note above did not merely predict this —
    # it described it. Measured on both sides: the last *pushed* commit
    # (`3e7ef18`) reads (18, 13); `b0f043f`, the end of the 2026-08-21 01:00
    # cycle, already reads (19, 14) with the same names. So 01:00 moved this
    # census, 01:00 and 02:00 both ended stranded and ungraded, and 03:00 — the
    # first cycle to pay for a suite — inherited a red it did not cause. That
    # is the D-381 paragraph above happening a second time, one strand later.
    #
    # The verdict is again unmoved: `narrowing` 3.79 (> 2.0) and
    # `discrimination` 0.152, still well under `SEPARATION_MARGIN` 0.25. An
    # ordinary join, same class as the D-377 and D-381 entrants — which is why
    # the pin moves and no rung does.
    #
    # The standing lesson is now measured twice and is not about this key at
    # all: **an unpushed tree is an unmeasured one**, and its cost lands on
    # whichever later cycle happens to buy the suite. `cycle_artifacts
    # stranded` says "budget a suite run to clear, not just a push" (D-112) for
    # exactly this, and both times the strand was allowed to persist anyway.
    #
    # D-404 moves it to (20, 15): `declared_suite.scope_of` joined, an ordinary
    # entrant of the same class as the three above, verdict again unmoved. The
    # new fact this time is *where the cost landed*. `census_preempt` ran clean
    # on all five of its censuses before the suite and named the four it does
    # not cover — and this one is in **neither** list, so its silence read as
    # coverage it never claimed. That is D-317's finding recurring against the
    # instrument built to answer it: a check whose scope is narrower than it
    # looks reads exactly like a clean one.
    #
    # D-452 moves it to (21, 15), and this entrant is not the same class as the
    # four above. Two things are new about it.
    #
    # First, `calibrated_cruise` entered on a commit that changed **no code**.
    # D-451 was `qual:doc-only` — `docs/decisions.md`, `docs/deliberations.md`,
    # one journal file — and it moved a census over the *call graph*. It could,
    # because the narrow key matches names in `citation_audit.SCANNED_DOCS`, and
    # D-451's own Decision (3) wrote "`calibrated_cruise(0.8) = 0.723` ... (D-025
    # 의 `CRUISE_BY_VMAX`" — a call site with an argument, with a backticked
    # SCREAMING_SNAKE token 60-odd characters later, which is exactly the shape
    # `called_with_recorded_return` was written to detect. The prose was accurate;
    # it was also a measurement. D-043 says REPORT-phase writes are inside the
    # verification surface, and this is that principle with the code term set to
    # zero: the doc write was the entire commit.
    #
    # Second, it is the first **non-LIVE** entrant since D-332's `retake_scene`.
    # D-377/381/395/404 each moved hits and live together (17/12 -> 20/15), which
    # is why each was an "ordinary join". This one moves hits alone, so it raises
    # the narrow key's non-LIVE fraction on its own account and `discrimination`
    # goes 0.152 -> 0.173. That is the *first* move of this number since D-342
    # that is genuinely about the key rather than about the wide control — D-342's
    # whole finding was that either end can move it, and this is the end that
    # licenses the verdict.
    #
    # The verdict is still unmoved, and the margin is why the rung is not touched:
    # 0.173 against SEPARATION_MARGIN 0.25. But the direction now has a reason
    # behind it rather than a control artifact, so if a seventh non-LIVE name
    # lands here the thing to do is not to re-state this note a sixth time — it is
    # to answer D-196's deferred question, which is what a separating reading was
    # always going to force.
    #
    # The `census_preempt` complaint three paragraphs up is now fixed rather than
    # restated: this census is in that module's `UNCOVERED` list as of this cycle.
    # It is still not *derived* — `UNCOVERED` buys honesty about the gap, not
    # coverage of it — but a reader who follows D-318's instruction and reads the
    # scope clause is now told this census exists and is not being watched.
    # D-460 moves it to (22, 16): `obstacle_reach.measure_at` entered, LIVE. So
    # this is an "ordinary join" of the D-377/381/395/404 class — hits and live
    # together — and the non-LIVE fraction it licenses the verdict on goes *down*,
    # 0.173 -> 0.162. The D-452 note above asks for D-196's deferred question to
    # be answered if a **seventh non-LIVE** name lands; this is not one, so the
    # counter it was watching has not advanced and the note is not re-stated.
    #
    # It is worth recording what did and did not catch this. `census_preempt` ran
    # CLEAN 8/8 before the commit and named this census in its `UNCOVERED` line —
    # exactly as the D-452 paragraph above says it now does — so the honesty that
    # fix bought was real, but honesty is not coverage and a 24m39 suite is still
    # what found it. That is the standing price of this census being pinned by
    # hand rather than derived, and it is the ninth instance of Q-183's shape.
    assert (r.narrow.hits, r.narrow.live) == (22, 16), (
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
    `scene_transfer.retake_scene` a fifth, and D-452's `calibrated_cruise` a
    sixth. The direction of D-196's finding is unchanged and in fact reinforced
    five times over: a key proposed for its precision now admits *five* further
    unreached names, so the residue it was meant to isolate is less isolated on
    every cycle that adds a module, not more.

    D-332's entrant arrived by a **rename**, not a new module — the same
    function was called `retake_cut_in` on the previous tree and did not hit
    this key. That is worth recording: the key discriminates on name shape, so
    the population it isolates moves when nothing about the code's behaviour
    does, which is a sharper version of the same objection.

    D-452's entrant sharpens it once more, in the remaining direction. It
    arrived by neither a new module nor a rename but by **prose**: a doc-only
    commit wrote `calibrated_cruise(0.8) = 0.723` next to a backticked verdict
    token, and a function that had been in this package untouched for weeks
    joined the key. So the population this key isolates moves when nothing about
    the code changes *at all* — not its behaviour, not even its name. The key is
    a reading of the decision log, and the decision log is written by the same
    cycles the key is meant to grade.
    """
    r = kd.measure()
    verdicts = kd.population()
    caught = [n for n in r.narrow_names if verdicts.get(n) != "LIVE"]
    assert caught == ["attribution_separability", "calibrated_cruise", "reprobe",
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

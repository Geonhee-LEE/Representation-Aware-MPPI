# SPDX-License-Identifier: BSD-3-Clause
"""The 8-seed caveat, priced for the first time.

Every table `calibrate_lam` writes walks 8 seeds, and every cycle since D-142
has carried the same standing caveat: the hand-walked cells in
`lam_window_key.REMEASURED` used 16, so a window the table reports might be an
artifact of the cheaper measurement. The caveat was unpriceable rather than
merely unpriced — pricing it needs one cell measured at **both** seed counts,
and no table existed at a weight the registry also held.

D-145's `w = 100` table is the first that does. `HEADON_W100_CELL` walked
`cafe_head_on_v0` at `w = 100`, margin 0.40, 16 seeds; the table walks the same
scene at the same weight and margin with 8. Scene, weight and margin are held
fixed by construction, so the only thing left varying is the seed count — the
same structural isolation `table_shift_census` gets on the weight axis, on the
one axis the census could not previously reach.

What this file does **not** claim: that 8 seeds suffice in general. One cell is
one cell — D-135 wrote the same sentence about its own first re-measurement,
and D-142 then moved 6 of 14 arm-cells. The result here is a price on one cell,
which is strictly more than the zero cells the caveat rested on before.
"""

from __future__ import annotations

import pytest

from eval.mppi_sandbox import lam_window_index as lwi
from eval.mppi_sandbox import lam_window_key as lwk

TABLE_W100 = "eval/scenarios/variants/lam_windows_w100.yaml"
TABLE_W75 = "eval/scenarios/variants/lam_windows_w75.yaml"
TABLE_W10 = "eval/scenarios/variants/lam_windows_w10.yaml"
TABLE_W150 = "eval/scenarios/variants/lam_windows_w150.yaml"
TABLE_W250 = "eval/scenarios/variants/lam_windows_w250.yaml"
HEADON = "cafe_head_on_v0.yaml"
CROSSING = "cafe_obstacle_crossing_v0.yaml"

CENSUS = lwk.seed_census(TABLE_W100)
CENSUS_W150 = lwk.seed_census(TABLE_W150)


# --------------------------------------------------------------------------
# The result
# --------------------------------------------------------------------------

def test_the_eight_seed_table_reproduces_the_sixteen_seed_walk_exactly():
    """Both head_on arms, and **set equality** rather than containment.

    `WINDOW_HELD` alone would be the weaker reading: it is `table <= walk`, so
    a table that agreed by being conservative — reporting a narrower window
    than the expensive walk found — would grade the same. That is a different
    claim, and D-135 drew exactly this distinction about its own result. Here
    the two sets are equal, so the cheap measurement is neither narrower nor
    wider on the rungs both walked."""
    assert CENSUS.compared == 2
    assert set(CENSUS.graded) == {lwk.WINDOW_HELD}
    assert set(CENSUS.exact) == set(CENSUS.graded[lwk.WINDOW_HELD])
    assert CENSUS.exact == (
        f"{HEADON}:risk_mppi@w=100", f"{HEADON}:stock_mppi@w=100")


def test_the_caveat_is_now_priced_at_a_second_weight_not_just_a_second_cell():
    """D-145 priced the 8-seed caveat on one `(scene, weight)` pair. One pair
    cannot separate "8 seeds suffice" from "8 seeds suffice **at w = 100**",
    and D-142's whole finding is that this axis moves things.

    `w = 150` is the second pair, and since D-163 widened that table to a
    second scene it is also the first place the caveat **bites**. Four
    arm-cells compared, and they do not all agree::

        head_on   stock  WINDOW_HELD     (exact)
        head_on   risk   WINDOW_HELD     (exact)
        crossing  stock  WINDOW_CLOSED   (exact — empty on both sides)
        crossing  risk   WINDOW_SHIFTED  8 seeds [0.4, 0.8] vs 16 seeds [0.8]

    That last row is the whole point of having run this. Every previous census
    graded `WINDOW_HELD` everywhere, which is consistent both with "8 seeds
    suffice" and with "we have only ever asked cells that could not disagree".
    One cell disagreeing distinguishes them, and it disagrees in the direction
    the caveat always feared: the **cheap** measurement reports the **wider**
    window, i.e. λ = 0.4 clears 8 seeds and fails 16."""
    assert CENSUS_W150.compared == 4
    assert CENSUS_W150.weight == 150.0
    assert set(CENSUS_W150.graded) == {
        lwk.WINDOW_HELD, lwk.WINDOW_CLOSED, lwk.WINDOW_SHIFTED}
    assert CENSUS_W150.graded[lwk.WINDOW_SHIFTED] == (
        f"{CROSSING}:risk_mppi@w=150",)

    # The disagreement, read off the two sources rather than off the grade —
    # a label can be wrong about its own direction, two windows cannot.
    table = lwk.lookup(TABLE_W150, CROSSING, "risk_mppi", 150.0)
    assert table.usable == (0.4, 0.8)
    assert lwk.CROSSING_W150_CELL.window("risk_mppi") == (0.8,)
    # Cheap-and-wider, not cheap-and-narrower: the 8-seed table is the
    # permissive one, so this axis cannot be dismissed as under-powering.
    assert set(lwk.CROSSING_W150_CELL.window("risk_mppi")) < set(table.usable)


# --------------------------------------------------------------------------
# The cell the table does not have — D-149
# --------------------------------------------------------------------------

def _table_without_crossing(tmp_path) -> str:
    """The `w = 150` table as it stood before D-163 — head_on cells only.

    D-149's defect needs a table that is *missing* a cell the registry holds at
    its own weight, and until this cycle the shipped `w = 150` table was one.
    Buying crossing's two cells fixed the repo and took the witness with it, so
    the witness is reconstructed here instead of being deleted: a guard whose
    last artifact is bought becomes prose, which is `guard_vacuity`'s standing
    complaint, and the defect it pins is one a future one-scene table can
    reintroduce.

    Built by filtering the real table through `calibrate_lam`'s own loader and
    renderer rather than by checking in a second copy — a hand-written fixture
    would be a second statement of the format (D-047).
    """
    from eval.mppi_sandbox import calibrate_lam as cal

    header = cal.load_header(TABLE_W150)
    cells = [c for key, c in cal.load_windows(TABLE_W150).items()
             if key[0] != CROSSING]
    assert len(cells) == 2, "the filter must leave head_on's two arms"
    path = tmp_path / "lam_windows_w150_headon_only.yaml"
    path.write_text(cal._render(header, cells))
    return str(path)


def test_a_cell_the_table_never_walked_is_absent_rather_than_agreeing(tmp_path):
    """The defect a one-scene table made reachable, and the reason it is a
    D-NNN rather than a line in a journal.

    `REMEASURED` holds two cells at `w = 150`: head_on (which this table walked)
    and crossing (which it did not). `Remeasurement.recorded` resolves through
    `lookup`, which returns an empty `admissible` for a **missing** cell exactly
    as it does for a measured-and-windowless one — and `window_shift` reads an
    empty recorded side as `recorded <= remeasured`, i.e. `WINDOW_HELD`. So
    before the fix this census reported that the cheap table agreed with an
    expensive walk on a scene the cheap table never visited, and — because
    crossing's stock arm is windowless at `w = 150` too — listed it in `exact`,
    the strongest grade the census has. Four cells `compared` where two were.

    Q-034's distinction (`NO_CELL` is not `EMPTY_WINDOW`) at the one layer that
    had lost it. The bit was never missing from `lookup`; `recorded` dropped it.

    Run against a reconstructed one-scene table since D-163: the shipped
    `w = 150` table now *has* crossing's cells, and the grade it gives them is
    the reason the diversion matters. `WINDOW_CLOSED` for stock is a real
    reading of two genuinely empty windows; before the fix a *missing* cell
    produced `WINDOW_HELD` + `exact`, the strongest grade the census has, off
    the same empty tuple. Same input shape, opposite epistemic status.
    """
    census = lwk.seed_census(_table_without_crossing(tmp_path))
    absent = set(census.absent)
    assert absent == {f"{CROSSING}:stock_mppi@w=150", f"{CROSSING}:risk_mppi@w=150"}
    # Diverted *before* grading: not counted, not graded, not "exact".
    assert census.compared == 2
    assert not absent & set(census.exact)
    all_graded = {lab for labels in census.graded.values() for lab in labels}
    assert not absent & all_graded

    # …and the shipped table, which now walks those cells, grades them instead
    # of diverting them. The two readings must not be the same object.
    assert CENSUS_W150.absent == ()
    assert CENSUS_W150.compared == 4


def test_absent_is_non_vacuous_in_both_directions(tmp_path):
    """A field that were always populated, or never, would witness nothing.

    Since D-163 **no shipped table** produces a non-empty `absent`: every
    registry cell is now covered by the table at its own weight. That is the
    repo being in better shape, not the distinction ceasing to exist, so the
    populated side is witnessed by the reconstructed one-scene table. If a
    future cycle buys a table at a weight the registry holds and skips a scene,
    this is the reading that catches it."""
    assert CENSUS.absent == ()
    assert CENSUS_W150.absent == ()
    assert lwk.seed_census(_table_without_crossing(tmp_path)).absent != ()


def test_absent_is_not_folded_into_uncompared():
    """The two non-comparisons have different causes and different fixes.
    `uncompared` is "the registry cell is at another weight" — nothing to do,
    it is a different question. `absent` is "the cell is at *this* weight and
    the table skipped the scene" — a table that could be widened. Collapsing
    them would hide which of the two the census is short on."""
    assert set(CENSUS_W150.absent) & set(CENSUS_W150.uncompared) == set()
    assert CENSUS_W150.uncompared == (f"{HEADON}@w=100",)


def test_the_window_agreed_on_is_the_one_the_published_claim_was_walked_at():
    """The agreement would be cheap if it were about temperatures nobody uses.
    λ = 0.8 — D-131/D-132's operating point, and the rung the project's only
    scorable mechanism result was taken at — is in both sources' window for
    both arms."""
    for arm in ("stock_mppi", "risk_mppi"):
        table = lwk.lookup(TABLE_W100, HEADON, arm, 100.0)
        assert table.verdict == lwk.ON_KEY, str(table)
        assert 0.8 in table.usable
        assert 0.8 in lwk.HEADON_W100_CELL.window(arm)


# --------------------------------------------------------------------------
# The confounds, handled rather than assumed away
# --------------------------------------------------------------------------

def test_the_comparison_is_scoped_to_the_rungs_both_sources_walked():
    """The table walks 8 rungs `{0.05 … 6.4}` and the hand walk walked 4
    `{0.2, 0.4, 0.8, 1.6}`. Grading unscoped would let a table rung the hand
    walk never tested read as a disagreement about seeds, when it is a question
    the 16-seed source was never asked."""
    assert CENSUS.ladder == lwk.HEADON_W100_CELL.ladder
    assert set(CENSUS.unwalked) == {0.05, 0.1, 3.2, 6.4}
    assert not set(CENSUS.unwalked) & set(CENSUS.ladder)


def test_the_registry_cells_at_other_weights_are_named_not_dropped():
    """Two of the three hand-walked cells are at `w = 150` and cannot price
    anything against this table. Showing only the comparable one would read as
    "the caveat is priced" when what happened is that one cell of three could
    be looked at — the empty-denominator shape D-107/D-120/D-127 each booked."""
    assert set(CENSUS.uncompared) == {
        "cafe_head_on_v0.yaml@w=150", "cafe_obstacle_crossing_v0.yaml@w=150"}
    assert len(CENSUS.uncompared) + CENSUS.compared // 2 == len(lwk.REMEASURED)


def test_a_table_at_a_weight_no_cell_was_walked_at_compares_nothing():
    """`w = 75` has a table and no hand-walked cell. The census must come back
    empty with every registry cell named as uncompared, rather than reaching
    for the nearest weight — which is the fallback `lam_window_index` refuses
    for D-142's reason: between two weights, cells move and they do not move in
    one direction."""
    census = lwk.seed_census(TABLE_W75)

    assert census.compared == 0
    assert census.graded == {}
    assert len(census.uncompared) == len(lwk.REMEASURED)
    # …and the object says so itself. Asserting `compared == 0` here is the
    # test knowing the case; `verdict` is what a *caller* has to read it from.
    assert census.verdict == lwk.NO_SEED_CONTRAST


def test_a_census_that_compared_nothing_is_not_a_census_that_agreed():
    """The defect this verdict closes: with nothing compared, every field on
    `SeedContrast` reads exactly as it does under total agreement.

    `graded` empty, `exact` empty, and since D-149 `absent` empty too — because
    `absent` means "hand-walked here and missing from the table", and at these
    weights nothing was hand-walked at all. So the natural caller test for "did
    the seed count matter", `not census.exact` or `census.compared == len(...)`,
    is silently wrong for three of the five shipped tables.

    `NO_SEED_CONTRAST` has named this state since D-145 wrote its docstring
    ("Distinct from 'the seed count does not matter': nothing was compared")
    and no code path returned it. `attribution` had already made the identical
    split — `FACTOR_INERT if compared else NO_CONTRAST` — one function over.

    Pinned as the *equality of the fields* plus the *difference of the
    verdicts*, so a future change that makes the fields distinguishable does
    not leave this reading unasserted.
    """
    silent = lwk.seed_census(TABLE_W250)      # nothing walked at w = 250
    spoke = lwk.seed_census(TABLE_W100)       # both arms walked at w = 100

    # Indistinguishable on the fields a caller would reach for…
    assert (silent.graded, silent.exact, silent.absent) == ({}, (), ())
    assert not silent.exact and not spoke.graded.get("WINDOW_MOVED")
    # …and distinguished only by the verdict.
    assert silent.verdict == lwk.NO_SEED_CONTRAST
    assert spoke.verdict == lwk.SEED_CONTRASTED


def test_both_seed_verdicts_are_reachable_over_the_shipped_tables():
    """A verdict no artifact can produce is prose (the rule
    `test_every_verdict_is_reachable_over_the_shipped_tables` states for
    `certify`). Both of these come from real registered tables, and the split
    is 3/2 rather than 5/0 or 0/5 — a verdict property that returned one
    constant everywhere would pass a weaker version of this test.
    """
    verdicts = {}
    for table in lwi.TABLES:
        try:
            census = lwk.seed_census(table)
        except ValueError:
            continue                          # the unkeyed shipped table
        verdicts.setdefault(census.verdict, []).append(census.weight)

    assert set(verdicts) == {lwk.NO_SEED_CONTRAST, lwk.SEED_CONTRASTED}
    assert sorted(verdicts[lwk.NO_SEED_CONTRAST]) == [10.0, 75.0, 250.0]
    assert sorted(verdicts[lwk.SEED_CONTRASTED]) == [100.0, 150.0]


def test_an_unkeyed_table_cannot_hold_the_weight_fixed_and_is_refused(tmp_path):
    """Matching a registry cell to a table that records no
    `calibration_weight:` would be asserting the weight rather than reading it
    (D-107). The seed axis is only isolable with the weight pinned, so this
    refuses instead of guessing `w = 10`.

    **The exemplar is synthetic as of D-477, and that is the finding.** This
    test used to pass the real `eval/scenarios/lam_windows.yaml`, which was the
    repo's only unkeyed table. D-470 measured that file and D-477 installed the
    result, so every shipped table is keyed and the refusal has no live input
    left to demonstrate it on.

    Deleting the test was the wrong move: `seed_census` still has the branch,
    and a refusal with no witness is indistinguishable from a refusal that was
    quietly removed (D-317). So the unkeyed table becomes a fixture and the
    assertion stands exactly as written.
    """
    stray = tmp_path / "lam_windows.yaml"
    stray.write_text("ladder: [0.1]\nseeds: 8\nband_width: 10.0\ncells: []\n")
    with pytest.raises(ValueError, match="calibration_weight"):
        lwk.seed_census(str(stray))


# --------------------------------------------------------------------------
# Non-vacuity — the census can report disagreement
# --------------------------------------------------------------------------

def test_the_census_grades_a_disagreeing_source_rather_than_always_holding():
    """A census whose only outcome is `WINDOW_HELD` proves nothing about the
    seed count — it might grade every input that way. Fed the `w = 150` cell
    against the `w = 100` table (weights deliberately mismatched, which
    `seed_census` itself refuses), the underlying grade moves off HELD, so the
    green result above is a measurement and not a constant.

    Uses `window_shift` through `Remeasurement.shift` because the mismatch is
    the point: this is the comparison the census declines to make, shown to be
    non-trivial. `crossing` at `w = 150` against the `w = 10` table is D-134's
    original finding — recorded `[1.6, 3.2]`, re-measured `{0.8}`.

    Note the direction the grade is *not* free in: an empty recorded window is
    a subset of everything, so `WINDOW_HELD` against a table cell with no
    window would be vacuous. Both crossing arms are windowless at `w = 100`,
    which is why this witness reads the `w = 10` table instead."""
    crossing = lwk.CROSSING_W150_CELL

    assert crossing.shift("risk_mppi", TABLE_W10) == lwk.WINDOW_DISJOINT
    assert crossing.recorded("risk_mppi", TABLE_W10)  # non-empty: not vacuous

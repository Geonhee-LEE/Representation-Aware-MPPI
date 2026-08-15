# SPDX-License-Identifier: BSD-3-Clause
"""D-270 — the `w_voo` ladder re-taken inside `cafe_freezing_v0`'s calibrated window."""

from __future__ import annotations

import inspect

import pytest

from eval.mppi_sandbox import arm_audibility, calibrated_ladder as cl, ess_at_peak
from eval.mppi_sandbox.ab import ess_band


def test_shipped_temperature_is_below_the_calibrated_window():
    """The premise D-268 named but never checked: `lam = 0.1` is out of window."""
    from eval.mppi_sandbox.controllers.stock_mppi import MPPIParams

    window = cl.calibrated_window()
    assert window, "empty window would make this scene unreportable (Q-035)"
    assert MPPIParams().lam < min(window), (
        f"shipped lam {MPPIParams().lam} is inside {window} — then D-268's "
        f"degeneracy needs an explanation other than temperature")


def test_lam_is_unreachable_as_a_controller_kwarg():
    """Why no ladder called `calibrate_lam`: `run_arm(lam=...)` cannot work.

    Pinned because the fix in `sweep`/`sweep_ess` is to pass `params`, and if a
    later change makes `lam` a real kwarg that indirection becomes dead weight
    that should be removed rather than left to rot.
    """
    from eval.mppi_sandbox.controllers.risk_mppi import RiskMPPI
    from eval.mppi_sandbox.controllers.stock_mppi import StockMPPI

    for cls in (StockMPPI, RiskMPPI):
        assert "lam" not in inspect.signature(cls.__init__).parameters, (
            f"{cls.__name__} now takes `lam` directly — drop the `params=` "
            f"indirection in calibrated_ladder.sweep")


def test_both_sweeps_forward_params():
    """The plumbing gap this cycle closed, pinned on both halves of it."""
    for fn in (ess_at_peak.sweep_ess, arm_audibility.sweep_ratio):
        assert "params" in inspect.signature(fn).parameters, (
            f"{fn.__qualname__} dropped `params` — the temperature becomes "
            f"unreachable again and ladders silently revert to lam=0.1")


def test_sweep_ess_refuses_to_pair_recorded_ratios_off_temperature():
    """A ratio measured at `lam = 0.1` does not describe a run at another (D-241).

    Checked on the source rather than by paying for a run: the rung's `ratio`
    must come out `None` whenever `params` is passed.
    """
    src = inspect.getsource(ess_at_peak.sweep_ess)
    assert "params is not None" in src and "ratio=None" in src, (
        "sweep_ess no longer drops the recorded ratio off-temperature")


@pytest.mark.parametrize("lam,weight,ess,ratio", [
    (0.8, 5.0, 31.2344, 0.228470),
    (0.8, 1.0, 116.0037, 0.073362),
    (0.4, 5.0, 1.9995, 0.116878),
])
def test_recorded_cells_match_their_verdict_components(lam, weight, ess, ratio):
    """The three cells the finding turns on, each graded by the imported bars."""
    lo, hi = ess_band(256)
    got = [p for p in cl.points() if p.lam == lam and p.weight == weight]
    assert len(got) == 1
    p = got[0]
    assert p.median_ess == pytest.approx(ess)
    assert p.ratio == pytest.approx(ratio)
    assert p.ess_in_band == (lo <= ess <= hi)
    assert p.audible == (ratio >= arm_audibility.AUDIBLE_RATIO)


def test_the_operating_point_is_the_top_of_the_window_and_is_unique():
    """`(lam 0.8, w_voo 5)` — in band, audible, completed; and nothing else is."""
    usable = cl.usable_points()
    assert [(p.lam, p.weight) for p in usable] == [(0.8, 5.0)], (
        "the co-satisfying set moved — D-270's whole claim is that it is a "
        "single cell at the top of the calibrated window")
    assert usable[0].lam == max(cl.calibrated_window())


def test_usable_requires_all_three_conditions():
    """In band alone, or audible alone, is satisfiable by a degenerate run."""
    base = dict(lam=0.8, weight=5.0, n_samples=256, reached_goal=True)
    assert cl.Point(median_ess=31.0, ratio=0.23, **base).usable
    assert not cl.Point(median_ess=1.0, ratio=0.23, **base).usable      # not weighting
    assert not cl.Point(median_ess=31.0, ratio=0.01, **base).usable     # inaudible
    assert not cl.Point(median_ess=31.0, ratio=0.23,
                        **{**base, "reached_goal": False}).usable       # froze


def test_unmeasured_ratio_is_unknown_not_inaudible():
    """The `lam = 0.2` rows carry no ratio and must not be graded as quiet."""
    quiet = [p for p in cl.points() if p.lam == 0.2]
    assert quiet and all(p.ratio is None for p in quiet)
    assert all(p.audible is None for p in quiet)
    assert not any(p.usable for p in quiet)


def test_verdict_reports_an_operating_point_and_can_now_address_d027():
    v = cl.verdict()
    assert v["verdict"] == "OPERATING_POINT_FOUND"
    assert v["usable_points"] == ((0.8, 5.0),)
    # D-268 could not address D-027 (no in-band rung to fall from). At 0.8 the
    # ladder holds band at w=5 and loses it by w=20, which is that reading.
    assert v["can_address_d027_ceiling"] is True
    assert 0.8 in v["addressable_at_lam"]
    # The scope D-266 fixed is untouched by a temperature change on this scene.
    assert v["transfers_to_ab_scene"] is False


def test_d268_verdict_is_unchanged_at_the_shipped_temperature():
    """This module adds a reading; it does not rewrite the one below it.

    D-268 is a true measurement *at `lam = 0.1`*, which is the temperature the
    rest of the branch ran at. Overwriting it would erase that.
    """
    ratios = {w: r for w, r, _ in arm_audibility.SCENE_CURVES[cl.PEAK_SCENE]}
    rungs = [ess_at_peak.Rung(weight=w, median_ess=e, n_samples=k,
                              reached_goal=g, ratio=ratios.get(w))
             for w, e, k, g in ess_at_peak.MEASURED_ESS]
    got = ess_at_peak.verdict(rungs)
    assert got["verdict"] == "ESS_DEGENERATE_THROUGHOUT"
    assert got["can_address_d027_ceiling"] is False


def test_the_window_this_leans_on_is_not_keyed_to_the_ladders_cost_field():
    """Stated, not hidden: the window was taken with the epistemic channels off."""
    keyed = cl.window_is_keyed()
    assert keyed["grade"] in {"UNKEYED", "OFF_KEY"}
    assert keyed["window_channel_weight"] == 0.0
    assert keyed["ladder_channel"] == "w_voo"


def test_the_rungs_that_decide_anything_move_under_recalibration():
    """Why `SCENE_CURVES[freezing]` is not quotable — stated at rung resolution.

    Not "every rung moves": the middle of the ladder (`w = 20, 50`) is stable
    to within 8%, and asserting otherwise was this test's first version and was
    false. What moves are the two rungs any conclusion rests on — the operating
    point at `w = 5` and the headline top rung at `w = 200`.
    """
    old = {w: r for w, r, _ in arm_audibility.SCENE_CURVES[cl.PEAK_SCENE]}
    new = {p.weight: p.ratio for p in cl.points()
           if p.lam == 0.8 and p.ratio is not None}
    assert new, "no re-measured ratios recorded at the top of the window"
    moved = {w: (r - old[w]) / old[w] for w, r in new.items()}

    assert moved[5.0] > 0.20, (
        f"the operating-point rung moved only {moved[5.0]:.1%} — if it is "
        f"temperature-stable, quoting D-266's row for it is defensible")
    assert moved[200.0] < -0.20, (
        f"the top rung moved {moved[200.0]:.1%}; D-266's headline `3.2644` is "
        f"only unquotable if recalibration pulls it down materially")
    # And the direction is not uniform, which is the reason a blanket rescale
    # of the old row cannot repair it: the ends move opposite ways.
    assert moved[5.0] > 0 > moved[200.0]


def test_middle_of_the_ladder_is_temperature_stable():
    """The honest other half: `w ∈ {20, 50}` survive recalibration within 10%.

    Pinned so the finding cannot later be restated as "the whole curve is
    unreliable", which the measurement does not support.
    """
    old = {w: r for w, r, _ in arm_audibility.SCENE_CURVES[cl.PEAK_SCENE]}
    new = {p.weight: p.ratio for p in cl.points()
           if p.lam == 0.8 and p.ratio is not None}
    for w in (20.0, 50.0):
        assert abs(new[w] - old[w]) / old[w] < 0.10


# --- D-271: the operating point over D-019's seed set -----------------------


def test_seed_zero_reproduces_the_recorded_ladder_cell():
    """The ensemble and the ladder must be the same measurement, not two.

    If these ever disagree the ensemble is walking a different configuration
    and every count below is about a cell nobody claimed.
    """
    ladder = [p for p in cl.points()
              if (p.lam, p.weight) == cl.ENSEMBLE_CELL]
    ens = [p for p in cl.seed_points() if p.seed == 0]
    assert len(ladder) == 1 and len(ens) == 1
    assert ens[0].median_ess == pytest.approx(ladder[0].median_ess)
    assert ens[0].ratio == pytest.approx(ladder[0].ratio)


def test_the_cell_is_not_unanimous_and_is_not_a_seed_zero_artefact():
    """D-271's finding, stated as the two things it rules out.

    The TODO asked which of the two the cell was; the answer is neither, and
    the vocabulary was written before the counts were read so that `7/8` could
    not be talked into whichever word suited it.
    """
    v = cl.seed_verdict()
    assert v["verdict"] == "MAJORITY_USABLE"
    assert v["n"] == cl.ENSEMBLE_SEEDS
    assert v["census"]["n_usable"] == 7
    assert 0 in v["census"]["usable_seeds"], "seed 0 is not the outlier"
    assert len(v["census"]["usable_seeds"]) > 1, "not a seed-0 artefact"


def test_unanimity_is_the_only_thing_that_earns_the_word_window():
    """D-019: `admissible` is an all-seeds conjunction, so 7/8 is not a window.

    Non-vacuous in both directions — the same census with its one miss removed
    must grade `UNANIMOUS_WINDOW`, or the verdict is just always this string.
    """
    assert cl.seed_verdict()["verdict"] != "UNANIMOUS_WINDOW"
    passing = tuple(r for r in cl.MEASURED_SEEDS if r[0] != 4)
    assert cl.seed_verdict(passing)["verdict"] == "UNANIMOUS_WINDOW"
    assert cl.seed_verdict(passing)["n"] == 7, "and it says so at n=7, not n=8"


def test_the_single_miss_is_a_band_miss_not_an_audibility_miss():
    """Which condition failed decides the repair, so it is counted separately.

    Every seed clears the audibility bar; the one failure is the sampler
    falling under the ESS floor. That points at temperature, not at arm scale —
    the opposite of what D-264/D-265 spent three cycles chasing.
    """
    c = cl.seed_verdict()["census"]
    assert c["n_audible"] == c["n"], "audibility is not what fails here"
    assert c["n_reached"] == c["n"], "and nothing froze"
    assert c["failed_band_only"] == (4,)
    assert c["failed_audible_only"] == () and c["failed_both"] == ()


def test_per_seed_ess_span_exceeds_the_figure_that_motivated_the_ensemble():
    """D-019 measured ~5×; this cell is wider, which is why 1 seed was not enough.

    Pinned as a floor rather than a point value: the claim is that the spread
    is at least as bad as the one that motivated re-measuring, not that it is
    exactly 12.7×.
    """
    span = cl.ess_span()
    assert span is not None and span > 5.0, (
        f"span {span} is at or under D-019's ~5× — then a single-seed reading "
        f"at this cell would have been defensible after all")


def test_a_rate_at_n8_is_not_licensed_to_speak_about_other_n():
    """D-019(b): readings at different `n` are different predicates.

    The verdict carries `n` and says what it is comparable to, so a later
    16-seed reading cannot be quoted against this one without noticing.
    """
    v = cl.seed_verdict()
    assert f"n={v['n']}" in v["comparable_to"]
    assert v["usable_rate"] == pytest.approx(7 / 8)
    assert v["transfers_to_ab_scene"] is False


def test_seed_census_is_empty_safe_and_reports_no_readings():
    """An empty ensemble is unknown, not unanimous (D-241)."""
    v = cl.seed_verdict(())
    assert v["verdict"] == "NO_READINGS"
    assert v["usable_rate"] is None and v["ess_span"] is None


def test_sweep_seeds_walks_the_cell_the_claim_is_about():
    """Cheap structural guard — the sweep must not drift off `ENSEMBLE_CELL`."""
    sig = inspect.signature(cl.sweep_seeds).parameters
    assert "seeds" in sig and "cell" in sig
    assert cl.ENSEMBLE_CELL in [(p.lam, p.weight) for p in cl.points()], (
        "the ensemble cell is no longer a cell the ladder measured")


# --- D-272: which side of the band the miss falls on, and which way lam moves it


def test_ess_rises_with_lam_at_every_measured_weight():
    """The fact the repair direction turns on, read off the ladder already on disk.

    Asserted per column rather than on the pooled verdict, so a future table
    that goes non-monotone in one column fails here naming that column instead
    of only flipping the summary word.
    """
    d = cl.ess_direction_in_lam()
    assert d["direction"] == "UP", (
        f"ESS no longer rises with lam ({d['per_weight']}) — then the "
        f"WINDOW_EXHAUSTED verdict below is reasoning from a dead fact")
    assert d["n_columns"] == 5 and d["n_strict"] == 5
    assert set(d["per_weight"].values()) == {"STRICT_UP"}


def test_direction_is_a_conjunction_not_a_majority_vote():
    """One contrary column must sink `UP`, however many agree with it.

    The tempting implementation counts columns and takes the majority, which
    would let a saturated tie or a single reversal ride along unnoticed.
    """
    rows = tuple(cl.MEASURED)
    flipped = tuple(
        (lam, w, (ess if w != 20.0 else {0.2: 9.0, 0.4: 5.0, 0.8: 1.0}[lam]),
         k, r, g)
        for lam, w, ess, k, r, g in rows)
    d = cl.ess_direction_in_lam(flipped)
    assert d["direction"] == "NON_MONOTONE", (
        "four agreeing columns outvoted one contrary column — direction is "
        "supposed to be a conjunction")
    assert d["per_weight"][20.0] == "DOWN"


def test_an_all_tied_table_reports_flat_not_a_borrowed_direction():
    """A sampler pinned at the floor shows no direction; it must not claim one."""
    tied = tuple((lam, w, 1.0, k, r, g)
                 for lam, w, _ess, k, r, g in cl.MEASURED)
    d = cl.ess_direction_in_lam(tied)
    assert d["direction"] == "FLAT"
    assert d["n_strict"] == 0 and d["n_saturated"] == d["n_columns"]


def test_the_windows_untried_rungs_are_on_the_wrong_side_of_the_miss():
    """D-272 — the repair D-271 recommended cannot work, and no run was needed.

    Seed 4 misses *below* the floor, ESS rises with `lam`, and the cell already
    sits at the window's top rung. So `0.4` and `0.2` move ESS further down,
    away from the band. `8/8` is unreachable inside the calibrated window.
    """
    r = cl.band_miss_repair()
    assert r["verdict"] == "WINDOW_EXHAUSTED"
    assert r["missed_below_floor"] == (4,) and r["missed_above_ceiling"] == ()
    assert r["cell_is_window_max"] is True
    assert r["helpful_rungs"] == ()
    # The rungs D-271 named are still named here — the overturned
    # recommendation has to stay visible beside the verdict that overturns it.
    assert r["untried_rungs"] == (0.2, 0.4)


def test_a_miss_above_the_ceiling_would_have_a_repair_inside_the_window():
    """The verdict is not `WINDOW_EXHAUSTED` by construction.

    Same cell, same direction, one seed pushed *over* the ceiling instead of
    under the floor: now the window's lower rungs are the helpful ones and the
    verdict flips. Without this, the test above passes on an implementation
    that always returns exhausted.
    """
    over = tuple((s, (900.0 if s == 4 else ess), k, ratio, g)
                 for s, ess, k, ratio, g in cl.MEASURED_SEEDS)
    r = cl.band_miss_repair(seed_rows=over)
    assert r["verdict"] == "REPAIR_RUNG_AVAILABLE"
    assert r["missed_above_ceiling"] == (4,) and r["missed_below_floor"] == ()
    assert r["helpful_rungs"] == (0.2, 0.4)


def test_misses_on_both_sides_are_not_reported_as_one_repair():
    """No single rung serves a below-floor and an above-ceiling miss at once."""
    both = tuple((s, (900.0 if s == 1 else ess), k, ratio, g)
                 for s, ess, k, ratio, g in cl.MEASURED_SEEDS)
    r = cl.band_miss_repair(seed_rows=both)
    assert r["verdict"] == "MISSES_STRADDLE_BAND"
    assert r["missed_below_floor"] == (4,) and r["missed_above_ceiling"] == (1,)


def test_an_unusable_direction_blocks_the_verdict_rather_than_guessing():
    """`FLAT`/`NON_MONOTONE` means the ladder cannot say — say that, not a rung."""
    tied = tuple((lam, w, 1.0, k, r, g) for lam, w, _e, k, r, g in cl.MEASURED)
    r = cl.band_miss_repair(rows=tied)
    assert r["verdict"] == "DIRECTION_UNKNOWN"
    assert r["helpful_rungs"] == ()


def test_no_band_miss_is_distinct_from_no_repair():
    """A clean ensemble reports nothing to repair, not an exhausted window."""
    clean = tuple((s, 31.2344, k, ratio, g)
                  for s, _ess, k, ratio, g in cl.MEASURED_SEEDS)
    r = cl.band_miss_repair(seed_rows=clean)
    assert r["verdict"] == "NO_BAND_MISS"
    assert r["missed_below_floor"] == () and r["missed_above_ceiling"] == ()


def test_repair_verdict_carries_n_and_refuses_to_transfer():
    """Same D-019(b) discipline the seed verdict carries — `n` rides along."""
    r = cl.band_miss_repair()
    assert f"n={r['n']}" in r["comparable_to"]
    assert r["transfers_to_ab_scene"] is False


# --- Q-153 / D-281: the same cell read at the census's own seed count


def test_the_larger_read_lands_on_the_seed_count_the_census_grades_at():
    """Otherwise the whole point of re-taking is lost — it must be *16*, not "more"."""
    from eval.mppi_sandbox.seed_count_licence import CENSUS_LADDER_SEEDS

    assert cl.CENSUS_SEEDS == CENSUS_LADDER_SEEDS, (
        "CENSUS_SEEDS drifted from the census constant it is supposed to import")
    r = cl.seed_count_readings()
    assert r["reaches_census_n"] is True
    assert sorted(r["readings"]) == [cl.ENSEMBLE_SEEDS, CENSUS_LADDER_SEEDS]


def test_the_sixteen_seed_population_is_the_eight_plus_the_extension():
    """Held as a concatenation so the two tables cannot drift row by row."""
    assert cl.MEASURED_SEEDS_16 == cl.MEASURED_SEEDS + cl.MEASURED_SEEDS_EXT
    assert len(cl.MEASURED_SEEDS_16) == cl.CENSUS_SEEDS
    assert [row[0] for row in cl.MEASURED_SEEDS_16] == list(range(cl.CENSUS_SEEDS))


def test_the_operating_point_was_not_an_eight_seed_artefact():
    """D-271's verdict word survives at the census's `n` — the finding of Q-153.

    Asserted on the *word*, not the rate: D-019(b) makes `0.875` and `0.9375`
    readings of different predicates, so the durable claim is that the same
    vocabulary entry is selected at both counts, not that one number rose.
    """
    r = cl.seed_count_readings()
    at8, at16 = r["readings"][8], r["readings"][16]
    assert at8["verdict"] == at16["verdict"] == "MAJORITY_USABLE"
    assert at16["verdict"] != "UNANIMOUS_WINDOW", (
        "unanimity at n=16 would make this a window (D-019 conjunction), "
        "and it is not one — seed 4 still misses")


def test_the_miss_list_can_only_grow_and_here_it_did_not():
    """A superset read cannot repair a seed — a rising rate must not read as one."""
    r = cl.seed_count_readings()
    at8, at16 = r["unusable_seeds"][8], r["unusable_seeds"][16]
    assert set(at8) <= set(at16), "a seed that failed at n=8 cannot pass at n=16"
    assert at8 == at16 == (4,), "seed 4 is still the sole miss, and still alone"
    for n in (8, 16):
        c = r["readings"][n]["census"]
        assert c["failed_band_only"] == (4,), "the repair axis is still temperature"
        assert c["n_audible"] == c["n_reached"] == n, (
            "audibility and arrival are unanimous at both counts")


def test_the_two_counts_are_co_recorded_and_never_pooled():
    """D-019(b) bars comparison, not co-recording — and nothing subtracts them."""
    r = cl.seed_count_readings()
    assert r["verdicts_comparable"] is False and r["spans_comparable"] is False
    assert not any("delta" in k or "diff" in k or "ratio" in k for k in r), (
        "a difference field between two n would be exactly the comparison "
        "D-019(b) forbids")
    for n, v in r["readings"].items():
        assert v["n"] == n and f"n={n}" in v["comparable_to"]


def test_the_span_is_demoted_to_a_reading_at_one_seed_count():
    """`max/min` can only grow with `n`, so `12.68x` is a fact about `n = 8`.

    D-271 demoted D-019's `~5x` from plant constant to cell property on this
    same argument; it applies once more to D-271's own number.
    """
    r = cl.seed_count_readings()
    assert r["spans"][16] > r["spans"][8], (
        "a superset draw cannot narrow a max/min range")
    assert r["spans"][8] == pytest.approx(12.6816, abs=1e-3)
    assert r["spans"][16] == pytest.approx(17.3389, abs=1e-3)


def test_extension_rows_are_all_in_band_and_audible():
    """The extension is what moved the rate — pin why, not just that it moved."""
    lo, hi = ess_band(256)
    for seed, ess, k, ratio, reached in cl.MEASURED_SEEDS_EXT:
        assert lo < ess < hi, f"seed {seed} ESS {ess} left the band {(lo, hi)}"
        assert ratio > arm_audibility.AUDIBLE_RATIO, f"seed {seed} went silent"
        assert reached is True and k == 256

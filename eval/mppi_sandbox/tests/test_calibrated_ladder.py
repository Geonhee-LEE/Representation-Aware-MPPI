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


# --- D-283: the band is a ratio window, and the screen it licenses -----------

def test_the_band_is_a_ratio_window_and_the_ratio_is_ten_at_every_k():
    """The fact the whole screen rests on, pinned where it can be seen.

    `ESS_BAND_FRACTIONS` is `(0.05, 0.5)` — *fractions of K*, so `ceiling/floor`
    is `10.0` no matter how many rollouts the sampler draws. It is easy to read
    `(12.8, 128.0)` as an interval that widens with `K` and conclude that a
    bigger sampler would fit a wider ensemble. It would not.
    """
    for k in (64, 256, 1024, 4096):
        assert cl.band_width_ratio(k) == pytest.approx(10.0)
    lo, hi = ess_band(256)
    assert (lo, hi) == (12.8, 128.0)


def test_the_ensemble_does_not_fit_the_band_at_the_operating_point():
    """`17.34x` of spread will not go into a `10x` window."""
    r = cl.span_admits_band(cl.MEASURED_SEEDS_16)
    assert r["verdict"] == cl.SPAN_EXCEEDS_BAND
    assert r["span"] == pytest.approx(17.3389, abs=1e-3)
    assert r["band_width"] == pytest.approx(10.0)
    assert r["slack"] < 1.0


def test_the_lift_and_the_headroom_are_one_number_rendered_twice():
    """`required_lift / headroom == span / band_width`, identically.

    Pinned because the payload reports both, and two renderings of one fact
    read as two facts unless something says otherwise. If a future edit makes
    them independent, that is a change of meaning and this should fail.
    """
    r = cl.span_admits_band(cl.MEASURED_SEEDS_16)
    assert r["required_lift"] / r["headroom"] == pytest.approx(
        r["span"] / r["band_width"], rel=1e-12)
    assert r["required_lift"] == pytest.approx(2.8238, abs=1e-3)
    assert r["headroom"] == pytest.approx(1.6286, abs=1e-3)


def test_a_narrow_ensemble_is_admitted_rather_than_refused():
    """The screen must be able to say yes, or its `no` is construction.

    D-272 put two opposite-direction tests beside `WINDOW_EXHAUSTED` for this
    reason; the same precaution applies to a verdict derived from a ratio.
    """
    narrow = tuple((s, ess, 256, 0.3, True)
                   for s, ess in enumerate((20.0, 30.0, 40.0, 60.0)))
    r = cl.span_admits_band(narrow)
    assert r["verdict"] == cl.SPAN_FITS_BAND
    assert r["span"] == pytest.approx(3.0) and r["slack"] > 1.0


def test_two_sample_counts_are_two_bands_and_get_no_single_ratio():
    """A mixed-`K` ensemble has no one band, so it gets no `hi/lo` (D-241)."""
    mixed = ((0, 20.0, 256, 0.3, True), (1, 30.0, 512, 0.3, True))
    r = cl.span_admits_band(mixed)
    assert r["verdict"] == cl.MIXED_SAMPLE_COUNT
    assert r["band_width"] is None
    assert r["n_samples"] == (256, 512)


def test_an_exceeding_span_survives_larger_n_and_a_fitting_one_does_not():
    """`max/min` only grows with `n` (D-281), so the two verdicts differ in kind.

    A refusal is permanent under any larger read; an admission is a statement
    about the seeds drawn so far and nothing more.
    """
    assert cl.span_admits_band(cl.MEASURED_SEEDS_16)["survives_larger_n"] is True
    assert cl.span_admits_band(cl.MEASURED_SEEDS,
                               )["verdict"] == cl.SPAN_EXCEEDS_BAND
    assert cl.span_admits_band(
        cl.MEASURED_SEEDS_16_LAM10, cl.REPAIR_CELL)["survives_larger_n"] is False


def test_the_screens_premise_travels_with_its_verdict():
    """A conditional verdict that does not carry its condition is a claim."""
    r = cl.span_admits_band(cl.MEASURED_SEEDS_16)
    assert "span_response" in r["premise"]


# --- D-283: the premise, measured — and refuted -----------------------------

def test_temperature_compresses_the_spread_it_was_assumed_to_translate():
    """The measurement that voids the screen's own refusal.

    `span_admits_band` at the operating point says no rung can admit this
    ensemble — **conditional** on `lam` scaling every seed by a common factor.
    One rung (16 runs, 116 s) says that condition is false by a wide margin:
    `17.34x -> 5.46x`, a 69% compression. So the refusal bounds nothing, and
    the screen earned its keep by naming the premise rather than by being right.
    """
    r = cl.span_response()
    assert r["verdict"] == cl.SPAN_COMPRESSES
    assert r["relative_change"] < -cl.SPAN_TOLERANCE
    assert r["spans"][cl.ENSEMBLE_CELL] == pytest.approx(17.3389, abs=1e-3)
    assert r["spans"][cl.REPAIR_CELL] == pytest.approx(5.4587, abs=1e-3)
    assert r["admits_band_at"] == (cl.REPAIR_CELL,)
    assert r["same_seeds"] is True


def test_the_repair_rung_is_unanimous_at_the_seed_count_the_census_grades_at():
    """`16/16` at `(lam = 1.0, w_voo = 5)` — the word *window*, finally earned.

    `seed_verdict` reserves `UNANIMOUS_WINDOW` for the all-seeds conjunction
    (D-019), and every reading this branch has taken fell short of it: `7/8`
    (D-271), `15/16` (D-281). This is the first cell that does not.
    """
    v = cl.seed_verdict(cl.MEASURED_SEEDS_16_LAM10, cl.REPAIR_CELL)
    assert v["verdict"] == "UNANIMOUS_WINDOW"
    assert v["n"] == cl.CENSUS_SEEDS == 16
    assert v["usable_rate"] == 1.0
    c = v["census"]
    assert (c["n_in_band"], c["n_audible"], c["n_reached"]) == (16, 16, 16)
    # The cell is reported as the one asked for, not the module default —
    # a verdict labelled `(0.8, 5.0)` here would attribute this to the rung
    # that failed to earn it.
    assert c["cell"] == cl.REPAIR_CELL == (1.0, 5.0)


def test_the_unanimity_still_carries_its_seed_count():
    """`16/16` is a conjunction over 16 draws, and 17 could break it (D-019(b))."""
    v = cl.seed_verdict(cl.MEASURED_SEEDS_16_LAM10, cl.REPAIR_CELL)
    assert v["comparable_to"] == "readings at n=16 only (D-019(b))"
    assert v["transfers_to_ab_scene"] is False


def test_the_repair_rung_rows_clear_the_floor_the_operating_point_missed():
    """Seed 4 is the whole reason the rung was walked — pin what it did."""
    lo, hi = ess_band(256)
    by_seed = {s: (ess, ratio, reached)
               for s, ess, k, ratio, reached in cl.MEASURED_SEEDS_16_LAM10}
    assert by_seed[4][0] > lo, "seed 4 still below the floor — no repair"
    for seed, ess, k, ratio, reached in cl.MEASURED_SEEDS_16_LAM10:
        assert lo < ess < hi, f"seed {seed} ESS {ess} outside {(lo, hi)}"
        assert ratio >= arm_audibility.AUDIBLE_RATIO, f"seed {seed} went silent"
        assert reached is True and k == 256


def test_span_response_refuses_two_different_populations():
    """The licence for this comparison is that the seeds are held fixed."""
    short = cl.MEASURED_SEEDS_16_LAM10[:8]
    r = cl.span_response(cl.MEASURED_SEEDS_16, short)
    assert r["verdict"] == cl.SPANS_INCOMPARABLE
    assert r["same_seeds"] is False


def test_a_widening_response_is_graded_widening():
    """Both directions, so `SPAN_COMPRESSES` is a reading and not a shape."""
    tight = tuple((s, e, 256, 0.3, True) for s, e in enumerate((20.0, 40.0)))
    wide = tuple((s, e, 256, 0.3, True) for s, e in enumerate((20.0, 200.0)))
    assert cl.span_response(tight, wide)["verdict"] == cl.SPAN_WIDENS
    assert cl.span_response(tight, tight)["verdict"] == cl.SPAN_INVARIANT


def test_a_direction_read_on_two_rungs_does_not_extrapolate_to_a_third():
    """Compression between `0.8` and `1.0` licenses no claim about `1.2`."""
    assert cl.span_response()["extrapolates"] is False


def test_seed_points_are_labelled_with_the_cell_they_were_asked_for():
    """The seed tables carry no `lam`, so a forgotten `cell` mislabels rows."""
    pts = cl.seed_points(cl.MEASURED_SEEDS_16_LAM10, cl.REPAIR_CELL)
    assert {p.lam for p in pts} == {1.0}
    assert {p.lam for p in cl.seed_points()} == {0.8}


# --- D-027's ceiling, located at the admissible temperature (D-284) ----------

def test_lam10_ladder_reproduces_the_seed_ensembles_own_cell():
    """`sweep` and `sweep_seeds` land on one cell — the only drift check there is.

    `MEASURED_LAM10`'s `w = 5` row and `MEASURED_SEEDS_16_LAM10`'s seed-0 row
    are the same `(lam, w_voo, seed)` taken through two different sweep bodies.
    If they ever disagree, one of the two changed its isolation or its ratio
    read and the tables have stopped describing the same controller.
    """
    ladder = {w: (ess, ratio) for _l, w, ess, _k, ratio, _r in cl.MEASURED_LAM10}
    seed0 = next(row for row in cl.MEASURED_SEEDS_16_LAM10 if row[0] == 0)
    assert ladder[5.0][0] == seed0[1]
    assert ladder[5.0][1] == seed0[3]


def test_lam10_is_outside_the_calibrated_window():
    """The rung was reached by measurement, not by the table's licence.

    If `1.0` ever enters `lam_windows.yaml` this assertion fails, and it should:
    the module docstring's reason for keeping `MEASURED_LAM10` separate from
    `MEASURED` would no longer hold.
    """
    assert 1.0 not in cl.calibrated_window()
    assert set(cl.calibrated_window()) == {l for l, *_ in cl.MEASURED}


def test_ceiling_is_located_and_audible_on_both_sides_at_lam_10():
    got = cl.ceiling_bracket(lam=1.0)
    assert got["verdict"] == cl.CEILING_LOCATED
    assert got["bracket"] == (5.0, 20.0)
    # A ceiling under a silent arm bounds nothing — both sides must be audible
    # for this to be a bound on the *usable* region.
    assert got["audible_below"] and got["audible_above"]
    assert got["usable_weights"] == (5.0,)


def test_ceiling_needs_an_in_band_rung_to_fall_from():
    """D-268's shape keeps its own verdict rather than borrowing D-027's."""
    degenerate = tuple((0.1, w, 1.0, 256, 0.5, True) for w in (1.0, 5.0, 20.0))
    assert cl.ceiling_bracket(degenerate, lam=0.1)["verdict"] == cl.CEILING_UNREACHABLE


def test_ceiling_absent_when_the_ladder_never_leaves_the_band():
    held = tuple((0.9, w, 50.0, 256, 0.5, True) for w in (1.0, 5.0, 20.0))
    got = cl.ceiling_bracket(held, lam=0.9)
    assert got["verdict"] == cl.CEILING_ABSENT
    assert got["bracket"] is None


def test_inaudible_crossing_is_named_apart_from_a_located_ceiling():
    """`lam = 0.2` crosses the band with the arm still silent below it."""
    assert cl.ceiling_bracket(lam=0.2)["verdict"] == cl.CEILING_INAUDIBLE


def test_the_temperature_lift_did_not_move_the_ceiling():
    """D-283 repaired the seed ensemble at `w = 5`; the ceiling did not move.

    The two are independent questions and this pins the answer to the second:
    same bracket and the same one-rung usable set at both temperatures.
    """
    got = cl.ceiling_response()
    assert got["verdict"] == cl.CEILING_HELD
    assert got["brackets"][0.8] == got["brackets"][1.0] == (5.0, 20.0)
    assert got["usable_weights"][0.8] == got["usable_weights"][1.0] == (5.0,)


def test_ceiling_gap_withholds_its_conclusion_when_the_premise_is_false():
    """The ratio argument needs one common factor, and there is not one.

    `GAP_EXCEEDS_BAND` on the weight axis must **not** read like
    `SPAN_EXCEEDS_BAND` did on the seed axis: there `span_response` discharged
    the premise, here the same two temperatures move the two rungs by
    `1.006x` and `1.374x`. `bars_shared_rung` is the field that carries the
    difference and it must stay `False`.
    """
    got = cl.ceiling_gap(lam=1.0)
    assert got["verdict"] == cl.GAP_EXCEEDS_BAND
    assert got["gap"] > got["band_width"] == cl.band_width_ratio(256)
    assert got["premise_holds"] is False
    assert got["bars_shared_rung"] is False
    assert got["extrapolates"] is False


def test_the_gap_narrows_between_the_two_temperatures():
    """The gap falls between these two rungs — a *local* fact, not a direction.

    D-284 read this pair as a "direction of travel toward the window". D-285's
    third rung (`lam = 1.2`, gap `37.76x`) refutes that reading: the pair below
    is a turning point. The assertion is unchanged because it was never wrong
    about the two temperatures it names; only the interpretation was, and a
    stale interpretation in a docstring retires exactly as silently as a caveat
    (D-047), so it is corrected here rather than left to be re-read.
    """
    wide = cl.ceiling_gap(lam=0.8)["gap"]
    narrow = cl.ceiling_gap(lam=1.0)["gap"]
    assert wide > narrow > cl.band_width_ratio(256)
    # Two rungs license nothing about a third — no temperature at which the
    # gap would close is projected anywhere in the payload.
    assert cl.ceiling_gap(lam=1.0)["extrapolates"] is False


def test_the_third_rung_turns_the_gap_instead_of_closing_it():
    """The narrowing does not continue: `16.33 -> 11.96 -> 37.76`."""
    got = cl.gap_trend()
    assert got["verdict"] == cl.GAP_NON_MONOTONE
    gaps = got["gaps"]
    assert gaps[0.8] > gaps[1.0] < gaps[1.2]
    # The turn is large enough that it is not a re-reading of noise: the third
    # rung is wider than *either* of the first two, not merely than the second.
    assert gaps[1.2] > gaps[0.8] > got["band_width"]


def test_no_walked_temperature_holds_both_sides_of_the_ceiling_in_band():
    """The question D-284 left open, answered over the rungs actually walked."""
    got = cl.gap_trend()
    assert got["any_lam_fits_band"] is False
    assert got["min_gap_at_lam"] == 1.0
    assert got["min_gap"] > got["band_width"]
    # And still no projection to an unwalked temperature — three rungs license
    # a statement about the three. The turn is precisely what a projection off
    # the first two would have got wrong.
    assert got["extrapolates"] is False


def test_the_trend_refuses_gaps_measured_on_different_rung_pairs():
    """Comparing gaps is comparing one quantity only if the bracket held."""
    assert cl.gap_trend()["bracket_stable"] is True
    # Move the top temperature's crossing to a different pair by dropping the
    # in-band rung it shares with the others: the gaps then describe different
    # pairs and no trend is reported.
    rows = tuple(r for r in cl.MEASURED_ALL_LAMS
                 if not (r[0] == 1.2 and r[1] == 5.0))
    assert cl.gap_trend(rows)["verdict"] == cl.GAP_TREND_INCOMPARABLE


def test_the_partial_top_ladder_is_carried_as_a_rung_count():
    """`lam = 1.2` walks the bracketing pair only, and says so."""
    got = cl.gap_trend()
    assert got["n_rungs"] == {0.8: 5, 1.0: 5, 1.2: 2}
    # The unwalked rungs cannot move the bracket: `w = 1` is below the in-band
    # top and `50` / `200` are above an already-out-of-band `20`.
    assert set(got["brackets"].values()) == {(5.0, 20.0)}


def test_the_in_band_side_runs_out_of_band_before_it_runs_out_of_gap():
    """A second constraint, on the repair axis rather than on `w_voo`."""
    got = cl.gap_trend()
    headroom = got["in_band_headroom"]
    # `lam = 1.2` leaves 1.44x before `w = 5` leaves the band through the top,
    # having just been lifted 2.82x. The next comparable step overshoots.
    assert headroom[1.2] < got["per_rung_lift"]["1.0->1.2"][5.0]
    assert headroom[0.8] > headroom[1.2]


def test_lam12_rows_are_held_out_of_the_calibrated_window_table():
    """Same reason `MEASURED_LAM10` is: `1.2` is outside `calibrated_window()`."""
    assert 1.2 not in cl.calibrated_window()
    assert all(row[0] != 1.2 for row in cl.MEASURED)
    assert all(row[0] != 1.2 for row in cl.MEASURED_WITH_LAM10)
    assert cl.MEASURED_ALL_LAMS == cl.MEASURED_WITH_LAM10 + cl.MEASURED_LAM12


def test_the_crossing_is_a_cliff_and_the_region_is_not_a_spacing_artifact():
    """Neither interior rung is in band, so `{w = 5}` survives finer spacing."""
    got = cl.ceiling_resolution()
    assert got["verdict"] == cl.CROSSING_CLIFF
    assert got["interior_rungs"] == (8.0, 12.0)
    assert not any(got["interior_in_band"].values())
    # The whole cliff/slope call is this: the usable set did not grow when the
    # ladder got 2.5x finer, so one rung wide is the sampler, not the rungs.
    assert got["usable_refined"] == got["usable_coarse"] == (5.0,)
    assert got["region_is_artifact"] is False


def test_refining_the_bracket_tightens_it_without_moving_its_in_band_side():
    """`(5, 20] -> (5, 8]` — the crossing localises, it does not relocate."""
    got = cl.ceiling_resolution()
    assert got["bracket_coarse"] == (5.0, 20.0)
    assert got["bracket_refined"] == (5.0, 8.0)
    # The in-band side is the same rung; only the ceiling above it comes down.
    assert got["bracket_refined"][0] == got["bracket_coarse"][0]
    assert got["bracket_tightening"] > 2.9


def test_the_coarse_gap_bundled_decay_that_happens_below_the_band():
    """`11.96x` is the crossing plus `1.84x` of fall entirely under the floor."""
    got = cl.ceiling_resolution()
    assert got["gap_coarse"] > got["gap_refined"]
    assert got["gap_overstated_by"] == pytest.approx(
        got["gap_coarse"] / got["gap_refined"])
    # The bundled part is decay from 8 to 20, and both ends are below the floor
    # of the band — so none of it is the sampler leaving the band.
    lo, _ = cl.ess_band(256)
    below = [p for p in cl.points(cl.MEASURED_LAM10_REFINED)
             if p.lam == 1.0 and 8.0 <= p.weight <= 20.0]
    assert len(below) == 3
    assert all(p.median_ess < lo for p in below)


def test_the_band_verdict_at_this_temperature_is_resolution_dependent():
    """D-285 read `GAP_EXCEEDS_BAND` off a `4x` ladder; at `1.6x` it fits."""
    got = cl.ceiling_resolution()
    assert got["gap_fits_band_coarse"] is False
    assert got["gap_fits_band_refined"] is True
    assert got["gap_verdict_flips"] is True
    assert got["gap_refined"] < got["band_width"] < got["gap_coarse"]
    # And the coarse reading is exactly what `ceiling_gap` still reports, so
    # the flip is a statement about resolution rather than a disagreement.
    assert cl.ceiling_gap(cl.MEASURED_WITH_LAM10, 1.0)["verdict"] == (
        cl.GAP_EXCEEDS_BAND)


def test_a_fitting_gap_still_does_not_license_a_shared_rung():
    """The premise D-284 measured false is not repaired by a finer ladder."""
    got = cl.ceiling_resolution()
    assert got["gap_fits_band_refined"] is True
    # Arithmetic, not a temperature. Same withholding `ceiling_gap` does.
    assert got["bars_shared_rung"] is False
    assert cl.ceiling_gap(cl.MEASURED_WITH_LAM10, 1.0)["premise_holds"] is False


def test_only_the_refined_temperature_is_claimed():
    """`0.8` and `1.2` have no interior rung, so their gaps stay coarse."""
    got = cl.ceiling_resolution()
    assert got["refined_at_lams"] == (1.0,)
    assert got["coarse_at_lams"] == (0.8, 1.2)
    for lam in got["coarse_at_lams"]:
        walked = {p.weight for p in cl.points(cl.MEASURED_ALL_LAMS_REFINED)
                  if p.lam == lam}
        assert not {w for w in walked if 5.0 < w < 20.0}
    # `gap_trend`'s reading is left standing at its own resolution rather than
    # restated at this one.
    assert cl.gap_trend()["any_lam_fits_band"] is False


def test_the_cliff_call_is_band_membership_not_a_steepness_bar():
    """`local_exponents` is descriptive; no threshold decides the verdict."""
    got = cl.ceiling_resolution()
    exps = got["local_exponents"]
    # The crossing rung is an order of magnitude steeper than its neighbours,
    # which is worth seeing — but nothing in the verdict reads this number.
    assert exps["5->8"] > 10 * exps["8->12"]
    assert got["ess_monotone"] is True
    # Swapping the verdict would need a band membership to change, not an
    # exponent: put an interior rung in band and the call becomes a slope.
    rows = tuple((1.0, 8.0, 30.0, 256, 0.5, True) if r[:2] == (1.0, 8.0) else r
                 for r in cl.MEASURED_LAM10_REFINED)
    assert cl.ceiling_resolution(rows)["verdict"] == cl.CROSSING_SLOPE


def test_a_non_monotone_ladder_withholds_the_verdict():
    """Every bracket reader here assumes one crossing; withhold without it."""
    rows = tuple((1.0, 12.0, 90.0, 256, 0.37, True) if r[:2] == (1.0, 12.0)
                 else r for r in cl.MEASURED_LAM10_REFINED)
    assert cl.ceiling_resolution(rows)["verdict"] == cl.CROSSING_NON_MONOTONE


def test_an_unprobed_bracket_says_so_rather_than_calling_it_a_cliff():
    """The coarse ladder alone cannot answer, and does not pretend to."""
    got = cl.ceiling_resolution(cl.MEASURED_LAM10)
    assert got["verdict"] == cl.CROSSING_UNPROBED
    assert got["interior_rungs"] == ()
    assert got["region_is_artifact"] is None


def test_fine_rows_are_a_concatenation_not_a_retyped_table():
    """The coarse rows keep exactly one statement of themselves (D-047)."""
    assert cl.MEASURED_LAM10_REFINED == cl.MEASURED_LAM10 + cl.MEASURED_LAM10_FINE
    assert cl.MEASURED_ALL_LAMS_REFINED == (
        cl.MEASURED + cl.MEASURED_LAM10_REFINED + cl.MEASURED_LAM12)
    # Still outside the calibrated window, same as every other `lam = 1.0` row.
    assert 1.0 not in cl.calibrated_window()
    assert all(row[0] == 1.0 for row in cl.MEASURED_LAM10_FINE)


def test_the_spacing_is_now_uniform_across_all_three_temperatures():
    """The D-019 objection to D-286's mixed reading, answered on its own terms."""
    got = cl.uniform_resolution_trend()
    assert got["resolution_uniform"] is True
    assert set(got["interior_rungs"].values()) == {(8.0, 12.0)}
    # Every temperature now walks the same four rungs across the bracket.
    for lam in (0.8, 1.0, 1.2):
        walked = {p.weight for p in cl.points(cl.MEASURED_ALL_LAMS_UNIFORM)
                  if p.lam == lam and 5.0 <= p.weight <= 20.0}
        assert walked == {5.0, 8.0, 12.0, 20.0}


def test_uniform_spacing_does_not_make_the_three_gaps_comparable():
    """Spacing was one obstacle; `1.2`'s shape is a second one under it."""
    got = cl.uniform_resolution_trend()
    assert got["verdict"] == cl.UNIFORM_TREND_WITHHELD
    assert got["all_comparable"] is False
    assert got["withheld_at_lams"] == {1.2: cl.CROSSING_NON_MONOTONE}
    assert got["comparable_lams"] == (0.8, 1.0)
    # Uniform *and* incomparable at once — that pair is the finding.
    assert got["resolution_uniform"] is True


def test_the_withheld_temperature_keeps_its_refined_gap_out_of_the_minimum():
    """`1.2`'s `19.36x` exists arithmetically and is excluded on purpose."""
    got = cl.uniform_resolution_trend()
    assert 1.2 not in got["gaps_refined"]
    solo = cl.ceiling_resolution(cl.MEASURED_LAM12_REFINED, 1.2,
                                 coarse=cl.MEASURED_LAM12)
    assert solo["verdict"] == cl.CROSSING_NON_MONOTONE
    assert solo["gap_refined"] > got["band_width"]
    # Excluding it is not what produces the flip — it would not have fitted.
    assert got["min_gap_refined"] < got["band_width"] < solo["gap_refined"]


def test_lam_12_is_non_monotone_because_ess_rises_across_the_interior():
    """`88.59 -> 4.58 -> 9.14 -> 2.35`: no single crossing to bracket."""
    pts = sorted((p for p in cl.points(cl.MEASURED_LAM12_REFINED)),
                 key=lambda p: p.weight)
    ess = [p.median_ess for p in pts]
    assert not all(b <= a for a, b in zip(ess, ess[1:]))
    # The rise is exactly the 8 -> 12 step, and it is the only one.
    rises = [(a.weight, b.weight) for a, b in zip(pts, pts[1:])
             if b.median_ess > a.median_ess]
    assert rises == [(8.0, 12.0)]
    # Both ends of it still sit below the band's floor, so the rise does not
    # recover a usable rung — the region stays `{w = 5}` at this temperature.
    lo, _ = cl.ess_band(256)
    assert all(p.median_ess < lo for p in pts if 8.0 <= p.weight <= 12.0)


def test_the_band_verdict_flips_at_every_temperature_it_can_be_checked_at():
    """D-285's `any_lam_fits_band = False` was resolution-dependent throughout."""
    got = cl.uniform_resolution_trend()
    assert got["any_lam_fits_band_coarse"] is False
    assert got["any_lam_fits_band_refined"] is True
    assert got["verdict_flips"] is True
    # Not one temperature flipping and dragging a minimum with it: both
    # comparable temperatures cross the band on their own.
    for lam, gap in got["gaps_refined"].items():
        assert got["gaps_coarse"][lam] > got["band_width"] >= gap
    # And `0.8` overstated by more than `1.0` did, so D-286's `1.84x` was the
    # milder of the two rather than the representative one.
    assert got["gap_overstated_by"][0.8] > got["gap_overstated_by"][1.0] > 1.0


def test_two_comparable_temperatures_are_not_reported_as_a_trend():
    """D-285's own lesson, applied to the reader that supersedes it."""
    got = cl.uniform_resolution_trend()
    assert got["n_comparable"] == 2
    assert got["trend_verdict"] is None
    assert got["extrapolates"] is False
    # The withheld temperature is named rather than dropped silently, so a
    # reader can see the trend is unavailable rather than absent.
    assert got["per_lam_verdict"][1.2] == cl.CROSSING_NON_MONOTONE


def test_uniform_reader_still_withholds_the_shared_rung_and_the_scene():
    """Resolution repairs neither D-284's premise nor the single-scene limit."""
    got = cl.uniform_resolution_trend()
    assert got["bars_shared_rung"] is False
    assert got["transfers_to_ab_scene"] is False
    assert got["ab_scene_blocked_by"] == "PR #68 (unmerged)"


def test_a_partly_probed_table_reports_unprobed_rather_than_withheld():
    """Mixed spacing is a different failure from an incomparable shape."""
    got = cl.uniform_resolution_trend(cl.MEASURED_ALL_LAMS_REFINED)
    assert got["verdict"] == cl.UNIFORM_TREND_UNPROBED
    assert got["resolution_uniform"] is False
    # That table is exactly D-286's mixed one, which is why it cannot answer.
    assert got["interior_rungs"][1.0] == (8.0, 12.0)
    assert got["interior_rungs"][0.8] == ()


def test_uniform_rows_are_a_concatenation_not_a_retyped_table():
    """One statement of every coarse row, same as D-286's tables (D-047)."""
    assert cl.MEASURED_LAM12_REFINED == cl.MEASURED_LAM12 + cl.MEASURED_LAM12_FINE
    assert cl.MEASURED_ALL_LAMS_UNIFORM == (
        cl.MEASURED + cl.MEASURED_LAM08_FINE
        + cl.MEASURED_LAM10_REFINED + cl.MEASURED_LAM12_REFINED)
    assert all(row[0] == 0.8 for row in cl.MEASURED_LAM08_FINE)
    assert all(row[0] == 1.2 for row in cl.MEASURED_LAM12_FINE)
    # The interior pair is the same two weights at every temperature.
    assert ({row[1] for row in cl.MEASURED_LAM08_FINE}
            == {row[1] for row in cl.MEASURED_LAM10_FINE}
            == {row[1] for row in cl.MEASURED_LAM12_FINE} == {8.0, 12.0})


def test_the_rise_attribution_survives_the_census_seed_count():
    """D-288 called the `8 -> 12` rise seed 0's on three seeds; at 16 it holds.

    The ensemble medians fall monotonically across all three rungs, so there is
    no shape anomaly on this temperature to explain — `1.2` is a temperature to
    walk, which is what this cycle did.
    """
    got = cl.census_ladder()
    assert got["seed_count_is_census"] is True
    assert got["ess_monotone"] is True
    assert got["rise_attribution_holds"] is True
    # 13 fall against 3 rise — not a majority that could flip on one seed.
    assert len(got["fall_seeds"]) == 13 and len(got["rise_seeds"]) == 3
    ladder = [got["ensemble_median_ess"][w] for w in (5.0, 8.0, 12.0)]
    assert ladder == sorted(ladder, reverse=True)


def test_the_rung_carrying_the_crossing_is_wider_than_the_band():
    """The finding: `w = 8` spans `22.91x` against a `10.0x` window.

    D-283's argument arriving on the rung axis — both quantities are ratios, so
    a common factor slides the sample without narrowing it and a rung wider than
    the window admits no unanimous verdict at *any* temperature. The rung that
    fails the test is the interior one the crossing needs; its two neighbours
    both pass.
    """
    got = cl.census_ladder()
    assert got["verdict"] == cl.CENSUS_RUNG_INADMISSIBLE
    assert got["inadmissible_rungs"] == (8.0,)
    assert got["span"][8.0] > got["band_width"]
    assert got["rung_admits_band"] == {5.0: True, 8.0: False, 12.0: True}


def test_the_failing_rungs_fail_at_opposite_band_edges():
    """Band-membership counts read as a clean decay and hide the direction.

    `15/16`, `10/16`, `1/16` in band looks like one mechanism. It is two:
    `w = 5`'s sole miss is *above* the ceiling, every other miss is *below* the
    floor. D-285 saw this band close from above and could only report headroom.
    """
    got = cl.census_ladder()
    assert {w: len(v) for w, v in got["in_band_seeds"].items()} == {
        5.0: 15, 8.0: 10, 12.0: 1}
    assert got["above_ceiling_seeds"] == {5.0: (5,), 8.0: (), 12.0: ()}
    assert got["below_floor_seeds"][5.0] == ()
    assert all(got["below_floor_seeds"][w] for w in (8.0, 12.0))
    # No rung is unanimous, so the withholding stands on its own terms too.
    assert not any(got["conjunction_met"].values())
    assert got["reinstates_trend"] is False


def test_the_repair_factor_is_quoted_as_a_premise_not_as_a_verdict():
    """`w = 5` needs `1.12x` down and has `1.62x` of room — arithmetic only.

    The common-factor premise is exactly what D-284 measured false on this axis,
    so `factor_exists` may not reach the verdict. It names a rung worth walking.
    """
    got = cl.census_ladder()
    five = got["repair_arithmetic"][5.0]
    assert five["factor_exists"] is True
    assert five["need_down"] < five["room_down"]
    # ...and the verdict is decided by admissibility, not by this.
    assert got["verdict"] == cl.CENSUS_RUNG_INADMISSIBLE
    assert "D-284" in got["repair_premise"]
    assert got["bars_shared_rung"] is False and got["extrapolates"] is False


def test_no_span_is_compared_across_the_two_seed_counts():
    """D-281's discipline: `span` is `max/min`, monotone in `n`, so `3.70x` at
    `n = 3` and `22.91x` at `n = 16` are two statistics, not a widening."""
    got = cl.census_ladder()
    assert got["spans_comparable_across_n"] is False
    banned = ("delta", "diff", "ratio_vs", "change", "widen")
    assert not [k for k in got if any(b in k.lower() for b in banned)]


def test_the_census_table_is_the_census_seed_count_at_every_rung():
    """One statement of the walked population (D-047): 16 seeds x 3 rungs."""
    from eval.mppi_sandbox.seed_count_licence import CENSUS_LADDER_SEEDS

    by_rung: dict[float, set[int]] = {}
    for p in cl.MEASURED_LAM12_CENSUS:
        assert p.lam == 1.2 and p.n_samples == 256
        by_rung.setdefault(p.weight, set()).add(p.seed)
    assert set(by_rung) == {5.0, 8.0, 12.0}
    for w, seeds in by_rung.items():
        assert seeds == set(range(CENSUS_LADDER_SEEDS)), w


def test_the_unanimous_temperature_is_bounded_on_both_sides():
    """The headline: `w = 5`'s unanimous set is an interval, not a half-line.

    Every prior band-membership reading on this branch was taken at one
    temperature. Stacking the columns shows the run `{1.0, 1.1}` fails on both
    sides — and at *opposite* band edges, which is what distinguishes a band
    the ensemble crossed from a walk that stopped early.
    """
    v = cl.unanimity_bracket()
    assert v["verdict"] == cl.BRACKET_CLOSED_BOTH_EDGES
    assert v["unanimous_lams"] == (1.0, 1.1)
    assert v["unanimous_run_contiguous"] is True
    assert v["failing_neighbour_edges"] == {"below": "floor", "above": "ceiling"}
    # Endpoints are bracketed, never quoted as a width.
    assert v["lower_endpoint_in"] == (0.9, 1.0)
    assert v["upper_endpoint_in"] == (1.1, 1.15)  # narrowed from (1.1, 1.2) by D-291
    assert v["endpoints_located"] is False


def test_the_second_unanimous_window_is_the_one_the_bottleneck_asked_for():
    """`lam = 1.1` at `w = 5` is `16/16` — the branch's second, on its own terms."""
    v = cl.seed_verdict(cl.MEASURED_SEEDS_16_LAM11, (1.1, 5.0))
    assert v["verdict"] == "UNANIMOUS_WINDOW"
    assert v["n"] == cl.CENSUS_SEEDS == 16
    assert v["census"]["cell"] == (1.1, 5.0)
    # And it is a *different* cell from the first one, not a relabelling.
    assert cl.seed_verdict(cl.MEASURED_SEEDS_16_LAM10,
                           cl.REPAIR_CELL)["verdict"] == "UNANIMOUS_WINDOW"


def test_membership_dips_before_it_rises():
    """`15, 14, 16, 16, 15` — not monotone and not even unimodal.

    Load-bearing: a unimodal reader would extrapolate the lower endpoint below
    `0.8`, where the measured column is *better* than `0.9`.
    """
    v = cl.unanimity_bracket()
    counts = tuple(v["per_lam"][l]["n_in_band"] for l in v["walked_lams"])
    assert counts == (15, 14, 16, 16, 15, 15, 14)
    assert v["membership_monotone"] is False
    assert v["membership_unimodal"] is False
    assert cl._unimodal((1, 2, 2, 1)) is True
    assert cl._unimodal((2, 1, 2)) is False


def test_the_two_endpoints_are_different_kinds_of_boundary():
    """D-283's admissibility test separates them: one is structural, one is not."""
    v = cl.unanimity_bracket()
    assert v["endpoint_mechanism"] == {"below": "span_exceeds_band",
                                       "above": "translated_out_of_band"}
    # The claim behind each label, read off the failing neighbours themselves.
    assert v["per_lam"][0.9]["span"] > v["band_width"]
    assert v["per_lam"][1.15]["span"] < v["band_width"]


def test_the_bracket_refuses_mixed_populations_rather_than_pooling():
    """Two seed counts are two populations; neither brackets the other."""
    short = {0.8: cl.MEASURED_SEEDS_16, 1.0: cl.MEASURED_SEEDS_16_LAM10[:8]}
    assert cl.unanimity_bracket(short)["verdict"] == cl.BRACKET_INCOMPARABLE
    assert cl.unanimity_bracket({0.8: cl.MEASURED_SEEDS_16})["verdict"] == \
        cl.BRACKET_UNWALKED


def test_the_bracket_claims_nothing_beyond_its_rung_and_scene():
    """`w = 8` spans `22.91x` (D-289) — there is no bracket to read there."""
    v = cl.unanimity_bracket()
    assert v["applies_to_other_rungs"] is False
    assert v["transfers_to_ab_scene"] is False
    assert v["extrapolates"] is False
    assert v["comparable_to"] == "readings at n=16 only (D-019(b))"


def test_the_new_columns_are_the_census_population_at_the_shared_rung():
    """One statement of the walked population (D-047): 16 seeds, K=256, w=5."""
    from eval.mppi_sandbox.seed_count_licence import CENSUS_LADDER_SEEDS

    for lam, rows in cl.CENSUS_COLUMN_ROWS.items():
        assert {r[0] for r in rows} == set(range(CENSUS_LADDER_SEEDS)), lam
        assert {r[2] for r in rows} == {256}, lam
        assert all(r[4] for r in rows), f"a seed failed to reach goal at {lam}"


def test_walking_inside_the_interval_narrows_the_upper_endpoint():
    """D-291: `lam = 1.15` fails, so the endpoint is in `(1.1, 1.15)`.

    D-290 could only bracket it to `(1.1, 1.2)` because nothing had been walked
    inside. The run itself is unchanged — narrowing an endpoint must not move
    the set it bounds.
    """
    v = cl.unanimity_bracket()
    assert v["verdict"] == cl.BRACKET_CLOSED_BOTH_EDGES
    assert v["unanimous_lams"] == (1.0, 1.1)
    assert v["upper_endpoint_in"] == (1.1, 1.15)
    assert v["lower_endpoint_in"] == (0.9, 1.0)
    assert v["endpoints_located"] is False


def test_membership_does_not_recover_above_the_failing_neighbour():
    """`lam = 1.25` was walked to look for a second unanimous region. There is none."""
    v = cl.unanimity_bracket()
    per = v["per_lam"]
    assert per[1.25]["n_in_band"] == 14
    # Monotone decay above the run — 16, 15, 15, 14 — and every miss is over
    # the ceiling, never under the floor.
    assert tuple(per[l]["n_in_band"] for l in (1.1, 1.15, 1.2, 1.25)) == (16, 15, 15, 14)
    for lam in (1.15, 1.2, 1.25):
        assert per[lam]["miss_edge"] == "ceiling", lam
        assert per[lam]["missed_below_floor"] == ()


def test_the_tightest_column_is_not_the_most_unanimous_one():
    """Span-admissibility is necessary and plainly not sufficient.

    `lam = 1.25` has the narrowest span of any `w = 5` column — `2.90x` against
    a `10.0x` band — and is the *least* unanimous of the upper columns. The
    cluster contracts and is carried through the ceiling at the same time.
    """
    per = cl.unanimity_bracket()["per_lam"]
    spans = {lam: per[lam]["span"] for lam in per}
    assert min(spans, key=spans.get) == 1.25
    assert spans[1.25] == pytest.approx(2.8966, abs=1e-3)
    assert spans[1.25] < cl.band_width_ratio(256) / 3
    # Tightest span, yet fewer seeds in band than columns with wider spans.
    assert per[1.25]["n_in_band"] < per[1.1]["n_in_band"]
    assert spans[1.25] < spans[1.1]


def test_lam_cannot_repair_the_endpoint_it_is_blamed_for():
    """D-291's headline: `translated_out_of_band` is not repairable on this axis.

    The misses are over the ceiling, so repair means moving the ensemble down;
    `lam` moves it up. The only `lam` that moves it down is a smaller one, and
    that is inside the unanimous run.
    """
    v = cl.endpoint_repair_axis()
    assert v["verdict"] == cl.REPAIR_AXIS_REVERSES_INTO_RUN
    assert v["failing_neighbour"] == 1.15
    assert v["axis_moves_ensemble"] == "up"
    assert v["repair_needs_ensemble_moved"] == "down"
    assert v["repair_available_on_lam_axis"] is False
    assert v["reversing_lands_in_unanimous_run"] is True
    # The arithmetic exists — that is exactly why the axis result is the finding
    # and not a restatement of D-283's admissibility test.
    assert v["repair_arithmetic_exists"] is True
    assert v["repair_factor"] == pytest.approx(1.0943, abs=1e-3)
    assert v["neighbour_span"] < v["band_width"]


def test_the_repair_direction_is_read_on_one_side_and_says_so():
    """The lone dip is at `0.8 -> 0.9`, on the side where the question is moot."""
    v = cl.endpoint_repair_axis()
    assert v["axis_monotone"] is True
    assert v["axis_monotone_globally"] is False
    side = [lam for lam, _ in v["median_ess_on_side"]]
    assert side == [1.1, 1.15, 1.2, 1.25]
    med = [m for _, m in v["median_ess_on_side"]]
    assert med == sorted(med) and len(set(med)) == len(med)
    # The excluded columns are still reported, so the narrowing is visible.
    assert len(v["median_ess_by_lam"]) == 7


def test_the_lower_endpoint_never_reaches_the_axis_question():
    """Its span exceeds the band, so no common factor admits it (D-283)."""
    v = cl.endpoint_repair_axis(side="below")
    assert v["verdict"] == cl.REPAIR_AXIS_INADMISSIBLE
    assert v["failing_neighbour"] == 0.9
    assert v["neighbour_span"] > v["band_width"]
    assert "repair_factor" not in v


def test_the_repair_axis_reading_refuses_thin_and_bad_input():
    """No bracket, no direction to read — and `side` is not a free-form string."""
    thin = {0.8: cl.MEASURED_SEEDS_16}
    assert cl.endpoint_repair_axis(thin)["verdict"] == cl.REPAIR_AXIS_UNWALKED
    with pytest.raises(ValueError):
        cl.endpoint_repair_axis(side="sideways")


def test_the_repair_axis_reading_claims_nothing_beyond_its_rung_and_scene():
    v = cl.endpoint_repair_axis()
    assert v["extrapolates"] is False
    assert v["transfers_to_ab_scene"] is False
    assert v["comparable_to"] == "readings at n=16, w=5.0 only (D-019(b))"


def test_k_is_the_repair_axis_lam_was_not():
    """D-292's headline: the endpoint D-291 blamed on `lam` is repaired by `K`.

    And it is repaired by *lowering* `K`, not raising it — `K = 128` puts all
    16 seeds in band at `lam = 1.15`, the temperature that misses at `K = 256`.
    """
    v = cl.ensemble_scaling_in_k()
    assert v["verdict"] == cl.K_MOVES_ENSEMBLE_UP
    assert v["repair_needs_ensemble_moved"] == "down"
    assert v["repair_direction_in_k"] == "decrease"
    assert v["repair_available_on_k_axis"] is True
    # Measured, not arithmetic — this is the difference from D-291's finding.
    assert v["repair_is_measured_not_arithmetic"] is True
    assert v["unanimous_k"] == (128,)
    assert v["per_k"][128]["n_in_band"] == 16
    assert v["per_k"][128]["miss_edge"] is None


def test_raw_median_and_band_relative_position_point_the_same_way_here():
    """Both rise with `K` — but only one of them is the membership coordinate.

    The band is `(0.05K, 0.5K)`, so a column is read in `median ESS / K`. The
    raw sequence is reported alongside precisely so the two are never quoted
    interchangeably; on this walk they happen to agree in sign, and that
    agreement is a fact about these columns, not a licence to use either.
    """
    v = cl.ensemble_scaling_in_k()
    raw = [m for _, m in v["median_ess_by_k"]]
    frac = [f for _, f in v["median_frac_by_k"]]
    assert raw == sorted(raw) and frac == sorted(frac)
    # Raw median grows 6.2x across the walk while the band-relative position
    # moves only 1.55x — the band absorbs most of the raw change.
    assert raw[-1] / raw[0] == pytest.approx(6.185, abs=1e-2)
    assert frac[-1] / frac[0] == pytest.approx(1.546, abs=1e-2)
    assert v["raw_median_rises_with_k"] is True
    assert v["frac_drift"] > cl.K_FLAT_TOLERANCE


def test_k_is_not_a_common_factor_it_changes_the_spread():
    """Raising `K` pulls the ensemble apart; `K = 512` is inadmissible (D-283).

    A common factor multiplies every seed by the same number and so leaves
    `span` (a ratio) fixed. `K` does not: `3.80x -> 5.37x -> 18.63x`. At
    `K = 512` the span exceeds the `10.0x` band, so that column cannot be made
    unanimous by *any* further common factor, and it misses at both edges.
    """
    v = cl.ensemble_scaling_in_k()
    assert v["acts_as_common_factor"] is False
    spans = [s for _, s in v["span_by_k"]]
    assert spans == sorted(spans)
    assert v["inadmissible_k"] == (512,)
    assert v["per_k"][512]["span"] > v["per_k"][512]["band_width"]
    assert v["per_k"][512]["miss_edge"] == "both"
    # The band width itself is `K`-invariant, so the disqualification is a fact
    # about the column and not about which `K` it was measured at.
    assert v["band_width_is_k_invariant"] is True
    assert cl.band_width_ratio(128) == cl.band_width_ratio(512) == 10.0


def test_membership_decays_monotonically_as_k_rises():
    """`16, 15, 11` — and the two failures are different in kind."""
    v = cl.ensemble_scaling_in_k()
    counts = [n for _, n in v["membership_by_k"]]
    assert counts == [16, 15, 11]
    assert counts == sorted(counts, reverse=True)
    # `K = 256` slid off the ceiling (translated); `K = 512` came apart.
    assert v["per_k"][256]["miss_edge"] == "ceiling"
    assert v["per_k"][256]["span"] < v["per_k"][256]["band_width"]
    assert v["per_k"][512]["miss_edge"] == "both"


def test_the_k_reading_refuses_thin_input():
    """One column is not an axis, and a short column is not the census."""
    assert cl.ensemble_scaling_in_k(
        {256: cl.MEASURED_SEEDS_16_LAM115})["verdict"] == cl.K_UNWALKED
    short = {128: cl.MEASURED_SEEDS_16_LAM115_K128[:8],
             256: cl.MEASURED_SEEDS_16_LAM115[:8]}
    assert cl.ensemble_scaling_in_k(short)["verdict"] == cl.K_UNWALKED


def test_an_exactly_linear_column_reads_as_unmoved():
    """The tolerance branch, exercised on a synthetic where `K` *is* a factor.

    Doubling `K` and every seed's ESS together leaves the band-relative
    position and the membership count identical — the control case that shows
    the real walk's `K_MOVES_ENSEMBLE_UP` is a measurement and not an artefact
    of the coordinate.
    """
    doubled = tuple((s, e * 2, 512, r, g)
                    for s, e, _, r, g in cl.MEASURED_SEEDS_16_LAM115)
    v = cl.ensemble_scaling_in_k({256: cl.MEASURED_SEEDS_16_LAM115, 512: doubled})
    assert v["verdict"] == cl.K_LEAVES_ENSEMBLE_IN_PLACE
    assert v["frac_drift"] == pytest.approx(0.0, abs=1e-12)
    assert [n for _, n in v["membership_by_k"]] == [15, 15]
    assert v["acts_as_common_factor"] is True


def test_the_k_reading_claims_nothing_beyond_its_cell_and_scene():
    v = cl.ensemble_scaling_in_k()
    assert v["extrapolates"] is False
    assert v["applies_to_other_rungs"] is False
    assert v["applies_to_other_lams"] is False
    assert v["transfers_to_ab_scene"] is False
    assert v["endpoints_located"] is False
    assert v["comparable_to"] == "readings at n=16, w=5.0, lam=1.15 only (D-019(b))"


# --- D-293: is the `K = 128` unanimous run wider, or has it translated? -------


def test_the_k128_run_translates_it_does_not_widen():
    """The headline. Same run *length*, different member, opposite edges."""
    v = cl.unanimity_run_in_k()
    assert v["verdict"] == cl.RUN_TRANSLATES_IN_K
    assert v["unanimous_by_k"] == {128: (1.15,), 256: (1.0,)}
    assert v["gained_at_lower_k"] == (1.15,)
    assert v["lost_at_lower_k"] == (1.0,)
    # "Wider" would mean a longer run. It is the same length on the common grid.
    assert v["run_length_by_k"] == {128: 1, 256: 1}
    assert v["run_length_unchanged"] is True


def test_the_two_membership_changes_are_one_downward_slide():
    """The gain comes off the ceiling, the loss goes out the floor.

    This is what separates a slide from two unrelated seeds moving: a single
    ensemble sliding down crosses the ceiling on its way *in* at high `lam` and
    the floor on its way *out* at low `lam`, and nothing else produces that
    pairing.
    """
    v = cl.unanimity_run_in_k()
    assert v["gain_came_off_edge"] == ("ceiling",)
    assert v["loss_went_out_edge"] == ("floor",)
    assert v["slide_direction"] == "down"


def test_the_slide_direction_agrees_with_d292_derived_independently():
    """Cross-check, not restatement.

    D-292 read the direction off `median ESS / K` on the `lam = 1.15` column.
    This reading gets it from membership changes on the `1.0` and `1.25`
    columns — different seeds, different temperatures, same answer. Lowering
    `K` lowers the band-relative position, so the ensemble slides *down*.
    """
    v = cl.unanimity_run_in_k()
    assert v["frac_rises_with_k"] is True
    assert v["slide_direction"] == "down"
    k = cl.ensemble_scaling_in_k()
    assert k["verdict"] == cl.K_MOVES_ENSEMBLE_UP
    assert k["repair_direction_in_k"] == "decrease"


def test_the_comparison_is_restricted_to_the_common_grid():
    """The trap this function exists to avoid (D-278).

    `K = 256` carries seven temperatures, `K = 128` three. Counting the full
    grids would charge `K = 128` for `lam = 1.1`, which was never walked there
    — absence of measurement rendered as failure.
    """
    v = cl.unanimity_run_in_k()
    assert v["common_lams"] == (1.0, 1.15, 1.25)
    assert v["grid_sizes"] == {128: 3, 256: 7}
    assert v["grids_unequal"] is True
    # 1.1 is unanimous at K=256 and unwalked at K=128. It must not appear as a
    # loss — that is precisely the miscount.
    assert 1.1 not in v["lost_at_lower_k"]
    assert 1.1 not in v["common_lams"]


def test_ignoring_the_grid_restriction_would_flip_the_verdict():
    """The control for the previous test: show the wrong answer is reachable.

    Feeding the *unrestricted* `K = 256` census against the `K = 128` grid, as
    if the missing temperatures were failures, turns a translation into a
    narrowing. The restriction is load-bearing, not decoration.
    """
    sunk = tuple((s, 1.0, 128, 0.1, True)
                 for s, *_ in cl.MEASURED_SEEDS_16_LAM115_K128)
    padded = dict(cl.K128_COLUMN_ROWS)
    for lam in cl.CENSUS_COLUMN_ROWS:
        padded.setdefault(lam, sunk)       # unwalked -> "all seeds under floor"
    v = cl.unanimity_run_in_k({128: padded, 256: cl.CENSUS_COLUMN_ROWS})
    assert v["verdict"] == cl.RUN_TRANSLATES_IN_K
    assert 1.1 in v["lost_at_lower_k"]     # the phantom loss the real read omits
    assert v["run_length_by_k"] == {128: 1, 256: 2}
    assert v["run_length_unchanged"] is False


def test_the_lost_column_is_not_merely_out_of_band_it_is_inadmissible():
    """`lam = 1.0` at `K = 128` spans `10.23x` against a `10.0x` band.

    D-283 disqualifies such a column structurally: no common factor puts it
    back, because a common factor translates a spread and cannot narrow one.
    So lowering `K` did not just slide this temperature out of the window — it
    put it beyond repair by the axis that moved it.
    """
    v = cl.unanimity_run_in_k()
    assert (128, 1.0) in v["inadmissible_cells"]
    assert (256, 1.0) not in v["inadmissible_cells"]
    lo = v["per_k"][128][1.0]
    assert lo["span"] > lo["band_width"]
    assert lo["span_admissible"] is False


def test_k_does_not_act_on_spread_uniformly_across_temperature():
    """D-292's "`K` pulls the ensemble apart" does not generalise off its column.

    Span *rises* with `K` at `lam = 1.15` (the column D-292 walked) and *falls*
    with `K` at both `1.0` and `1.25`. The prior reading stands where it was
    taken and nowhere else.
    """
    v = cl.unanimity_run_in_k()
    assert v["span_response_uniform"] is False
    assert v["span_response_in_k"][1.15] == "rises_with_k"
    assert v["span_response_in_k"][1.0] == "falls_with_k"
    assert v["span_response_in_k"][1.25] == "falls_with_k"


def test_a_miss_that_clears_the_edge_by_a_hair_is_reported_as_such():
    """`15/16` at `lam = 1.25`, `K = 128` — the miss is `0.18%` over the ceiling.

    Still counted a miss. But `unanimity_bracket`'s `15/16` at `K = 256` clears
    by `9.4%`, and a bare count spells the two identically.
    """
    v = cl.unanimity_run_in_k()
    marginal = dict(v["marginal_misses_by_k"][128])
    assert 1.25 in marginal
    (seed, ess, edge, margin), = marginal[1.25]
    assert (seed, edge) == (11, "ceiling")
    assert margin < cl.MARGINAL_MISS_TOLERANCE
    assert ess > v["per_k"][128][1.25]["band"][1]
    # The K=256 misses are not marginal — that is the contrast.
    assert dict(v["marginal_misses_by_k"][256]) == {}


def test_a_strictly_larger_unanimous_set_reads_as_widening():
    """The `RUN_WIDENS_AT_LOWER_K` branch, on a synthetic that earns it."""
    mid = tuple((s, 30.0, 128, 0.3, True)
                for s, *_ in cl.MEASURED_SEEDS_16_LAM115_K128)
    wide = {1.0: mid, 1.15: cl.MEASURED_SEEDS_16_LAM115_K128, 1.25: mid}
    v = cl.unanimity_run_in_k({128: wide, 256: cl.CENSUS_COLUMN_ROWS})
    assert v["verdict"] == cl.RUN_WIDENS_AT_LOWER_K
    assert set(v["gained_at_lower_k"]) == {1.15, 1.25}
    assert v["lost_at_lower_k"] == ()


def test_gain_and_loss_at_the_same_edge_is_not_a_slide():
    """`RUN_MOVES_INCOHERENTLY`: movement without a single direction.

    Built by making the lost column miss at the *ceiling* — the same edge the
    gained one came off — so the pair no longer describes one ensemble sliding.
    """
    over = tuple((s, 400.0, 128, 0.3, True)
                 for s, *_ in cl.MEASURED_SEEDS_16_LAM115_K128)
    cols = dict(cl.K128_COLUMN_ROWS)
    cols[1.0] = over
    v = cl.unanimity_run_in_k({128: cols, 256: cl.CENSUS_COLUMN_ROWS})
    assert v["verdict"] == cl.RUN_MOVES_INCOHERENTLY
    assert v["slide_direction"] is None


def test_identical_columns_read_as_unchanged():
    """`K` moved nothing across a walked band edge — the null result's own name."""
    v = cl.unanimity_run_in_k({128: cl.CENSUS_COLUMN_ROWS,
                               256: cl.CENSUS_COLUMN_ROWS})
    assert v["verdict"] in (cl.RUN_UNCHANGED_IN_K, cl.RUN_NO_UNANIMITY_AT_SOME_K)


def test_two_grids_that_barely_overlap_are_not_compared():
    """D-019(b): a one-temperature intersection is not a comparison."""
    thin = {1.15: cl.MEASURED_SEEDS_16_LAM115_K128}
    v = cl.unanimity_run_in_k({128: thin, 256: cl.CENSUS_COLUMN_ROWS})
    assert v["verdict"] == cl.RUN_GRIDS_TOO_THIN
    assert v["endpoints_located"] is False


def test_a_short_seed_column_is_refused():
    """Census predicate is `n = 16`; `n = 8` is a different predicate (D-281)."""
    short = {l: r[:8] for l, r in cl.K128_COLUMN_ROWS.items()}
    v = cl.unanimity_run_in_k({128: short, 256: cl.CENSUS_COLUMN_ROWS})
    assert v["verdict"] == cl.RUN_GRIDS_TOO_THIN


def test_the_run_reading_claims_nothing_beyond_its_grid_and_scene():
    v = cl.unanimity_run_in_k()
    assert v["endpoints_located"] is False
    assert v["extrapolates"] is False
    assert v["applies_to_other_rungs"] is False
    # STATE's second open question — explicitly still open, not implied closed.
    assert v["k_axis_bracketed_below"] is False
    assert v["transfers_to_ab_scene"] is False
    assert v["ab_scene_blocked_by"] == "PR #68 (unmerged)"
    assert v["comparable_to"] == "readings at n=16, w=5.0 only (D-019(b))"


def test_every_k128_run_reached_goal():
    """Membership readings on crashed runs would be measurements of nothing."""
    for lam, rows in cl.K128_COLUMN_ROWS.items():
        assert all(r[4] for r in rows), lam
        assert all(r[2] == 128 for r in rows), lam
        assert len(rows) == cl.CENSUS_SEEDS, lam

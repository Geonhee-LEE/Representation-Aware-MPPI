# SPDX-License-Identifier: BSD-3-Clause
"""The feed's pairing rider, pinned: `rho`'s sign varies, so there is no policy.

The claims under test are the ones a future cycle would otherwise re-derive
before spending STATE #1's 256 rollouts. They are pinned as literals so that a
re-take of `clearance_census.SEED_ENSEMBLE` that moved any of them goes red here
rather than quietly changing the recommendation.
"""

from __future__ import annotations

import math

import pytest

from eval.mppi_sandbox import pairing_precondition as pp
from eval.mppi_sandbox.clearance_census import BASELINE, SEED_ENSEMBLE, SEEDS


def _by_pair() -> dict[tuple[str, str], pp.PairReading]:
    return {tuple(sorted((r.arm_a, r.arm_b))): r for r in pp.readings()}


# --- the arithmetic itself ------------------------------------------------

def test_pearson_is_one_on_a_column_against_itself():
    col = SEED_ENSEMBLE[BASELINE]
    assert pp.pearson(col, col) == pytest.approx(1.0)


def test_pearson_is_minus_one_on_a_negated_column():
    col = SEED_ENSEMBLE[BASELINE]
    assert pp.pearson(col, tuple(-x for x in col)) == pytest.approx(-1.0)


def test_pearson_is_zero_when_one_column_does_not_vary():
    """A flat column has no seed-level variation, so pairing is inert on it.

    The alternative is `ZeroDivisionError`, which pushes the interpretation onto
    every caller; `0.0` says the same thing and says it once.
    """
    flat = (0.5,) * SEEDS
    assert pp.pearson(SEED_ENSEMBLE[BASELINE], flat) == 0.0
    assert pp.pearson(flat, flat) == 0.0


def test_pearson_refuses_columns_of_different_width():
    with pytest.raises(ValueError, match="differ in width"):
        pp.pearson((0.1, 0.2, 0.3), (0.1, 0.2))


# --- the headline ---------------------------------------------------------

def test_the_sign_varies_so_there_is_no_branch_wide_pairing_policy():
    """The finding. `UNIFORMLY_POSITIVE` would license a blanket rider; it does not."""
    assert pp.branch_wide_verdict() == "SIGN_VARIES"


def test_nine_of_twenty_six_non_degenerate_pairs_correlate_negatively():
    pop = pp.population()
    assert len(pop) == 26
    assert sum(1 for r in pop if r.rho < 0.0) == 9


def test_the_measured_range_straddles_zero_and_undershoots_the_source_paper():
    """`2512.24145` measured `rho = 0.681-0.993`; the feed read that as a best case.

    Confirmed in the warned direction and past it: our range does not merely sit
    lower, it **crosses zero**, which is the regime the source's own limit #2
    says reverses the variance comparison.
    """
    pop = pp.population()
    lo = min(r.rho for r in pop)
    hi = max(r.rho for r in pop)
    assert lo == pytest.approx(-0.7402, abs=1e-4)
    assert hi == pytest.approx(+0.7963, abs=1e-4)
    assert lo < 0.0 < hi
    assert hi < 0.993, "our best pair still undershoots the source paper's best"


# --- the population that actually bears on the deficit claim --------------

def test_the_four_worst_correlations_all_involve_the_baseline_column():
    """Not a tail effect — the failures land on the comparison that is load-bearing.

    Four and not two because `geometric_mppi` **reproduces** `stock_mppi` (the
    `DEGENERATE` identity above), so every baseline pair appears twice in the
    population: once against the baseline and once against its inert clone. The
    census-level statement is therefore about the baseline *column*, not the
    baseline *name*, and writing it as "the worst two are against `stock_mppi`"
    is false on the second-place tie for a reason that has nothing to do with
    correlation.
    """
    pop = pp.population()
    worst_four = sorted(pop, key=lambda r: r.rho)[:4]
    baseline_column = {BASELINE, "geometric_mppi"}
    assert all(baseline_column & {r.arm_a, r.arm_b} for r in worst_four)
    others = {r.arm_a for r in worst_four} | {r.arm_b for r in worst_four}
    assert others - baseline_column == {"essps_mppi", "gap_gated_mppi"}
    assert all(r.rho < -0.69 for r in worst_four)


def test_half_the_baseline_pairs_would_be_hurt_by_pairing():
    baseline_pairs = pp.against_baseline()
    assert len(baseline_pairs) == 6
    hurt = [r for r in baseline_pairs if r.verdict == "PAIRED_HURTS"]
    assert {r.arm_a if r.arm_b == BASELINE else r.arm_b for r in hurt} == {
        "essps_mppi", "gap_gated_mppi", "cbf_mppi",
    }


def test_pairing_would_inflate_the_two_worst_baseline_differences():
    """`sd_ratio > 1` is the concrete cost: a wider interval at the same budget."""
    by_pair = _by_pair()
    for arm, expected in (("essps_mppi", 1.319), ("gap_gated_mppi", 1.303)):
        r = by_pair[tuple(sorted((arm, BASELINE)))]
        assert r.sd_ratio == pytest.approx(expected, abs=1e-3)
        assert r.sd_ratio > pp.NEUTRAL_SD_RATIO


def test_the_best_pair_shrinks_the_interval_by_more_than_half():
    by_pair = _by_pair()
    r = by_pair[("risk_mppi", "social_mppi")]
    assert r.rho == pytest.approx(0.7963, abs=1e-4)
    assert r.sd_ratio == pytest.approx(0.451, abs=1e-3)
    assert r.verdict == "PAIRED_HELPS"


# --- the degenerate pairs -------------------------------------------------

def test_the_identity_pairs_are_exactly_the_ones_clearance_census_calls_inert():
    """Perfect seed-level correlation detects the inert channel that module documents."""
    ones = {tuple(sorted((r.arm_a, r.arm_b)))
            for r in pp.readings() if r.rho == pytest.approx(1.0)}
    assert ones == set(pp.DEGENERATE)
    for a, b in pp.DEGENERATE:
        assert SEED_ENSEMBLE[a] == SEED_ENSEMBLE[b], "identity is by reproduction"


def test_degenerate_pairs_are_excluded_from_the_population():
    """Two constructed `1.0`s must not flatter the branch-wide positive count."""
    pop_pairs = {tuple(sorted((r.arm_a, r.arm_b))) for r in pp.population()}
    assert pop_pairs.isdisjoint(set(pp.DEGENERATE))
    assert len(pp.readings()) == len(pp.population()) + len(pp.DEGENERATE)


def test_sd_ratio_stays_real_on_the_identity_pairs():
    """Float leaves `1 - rho` at `-2.2e-16`, and `(-2.2e-16) ** 0.5` is complex."""
    for r in pp.readings():
        assert isinstance(r.sd_ratio, float)
        assert math.isfinite(r.sd_ratio)
        assert r.sd_ratio >= 0.0


# --- structural: the census cannot drift from its source ------------------

def test_every_registry_arm_in_the_ensemble_is_paired_exactly_once():
    n = len(SEED_ENSEMBLE)
    assert len(pp.readings()) == n * (n - 1) // 2
    for r in pp.readings():
        assert r.arm_a in SEED_ENSEMBLE and r.arm_b in SEED_ENSEMBLE
        assert r.arm_a < r.arm_b, "pairs are canonically ordered"


def test_declared_degenerates_are_canonically_ordered_and_real_arms():
    for pair in pp.DEGENERATE:
        assert tuple(sorted(pair)) == pair
        assert all(arm in SEED_ENSEMBLE for arm in pair)


def test_verdicts_partition_the_readings():
    counts: dict[str, int] = {}
    for r in pp.readings():
        counts[r.verdict] = counts.get(r.verdict, 0) + 1
    assert counts["DEGENERATE"] == len(pp.DEGENERATE)
    assert counts["PAIRED_HURTS"] == 9
    assert counts["PAIRED_HELPS"] == 17
    assert sum(counts.values()) == len(pp.readings())


def test_main_prints_the_verdict(capsys):
    pp.main()
    out = capsys.readouterr().out
    assert "SIGN_VARIES" in out
    assert "against the baseline" in out
    assert "j" not in out.split("against the baseline")[0].split("sd x")[-1][:8]

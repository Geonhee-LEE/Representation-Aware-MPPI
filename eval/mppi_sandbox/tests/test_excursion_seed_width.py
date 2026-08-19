# SPDX-License-Identifier: BSD-3-Clause
"""D-370: the binding pair of D-363's spread separation, widened to eight seeds."""

from __future__ import annotations

from eval.mppi_sandbox import cte_peak_vacuity, excursion_seed_width as esw
from eval.mppi_sandbox import excursion_tracking


def test_ensemble_is_rectangular_at_the_declared_seed_width():
    for scene, cols in esw.SEED_ENSEMBLE.items():
        assert len(cols) == 8, scene
        for arm, row in cols.items():
            assert len(row) == esw.SEEDS, (scene, arm)


def test_ensemble_covers_the_full_arm_registry_on_both_scenes():
    from eval.mppi_sandbox.controllers import REGISTRY
    for scene, cols in esw.SEED_ENSEMBLE.items():
        assert sorted(cols) == sorted(REGISTRY), scene


def test_endpoints_are_the_two_scenes_that_set_the_separation():
    """The pair must be the argmin/argmax of the seed-0 spread column."""
    rows = excursion_tracking.measure()
    exc = min(excursion_tracking.excited(), key=lambda s: rows[s][3])
    unexc = max(excursion_tracking.unexcited(), key=lambda s: rows[s][3])
    assert esw.ENDPOINTS == (exc, unexc)


def test_seed0_reproduces_the_pinned_seed0_harvest():
    """Same measurement widened, not a different one — this is the join."""
    assert esw.seed0_agrees() == ()


def test_seed0_column_matches_cte_peak_vacuity_cell_by_cell():
    for scene, cols in esw.SEED_ENSEMBLE.items():
        pinned = cte_peak_vacuity.CTE_MAX_SEED0[scene]
        for arm, row in cols.items():
            assert abs(row[0] - pinned[arm]) <= 5e-5, (scene, arm)


def test_unpaired_robust_separation_fails():
    """Finding #1 — the claim D-363 made as `no overlap` inverts at seed width."""
    assert esw.separates() is False
    lo, hi = esw.robust_separation()
    assert lo < hi
    assert esw.robust_separation() == esw.ROBUST_SEPARATION


def test_the_inversion_is_not_marginal_in_the_direction_that_would_excuse_it():
    """`0.838x` is a real crossing, not a rounding artefact at the 4th dp."""
    lo, hi = esw.robust_separation()
    assert hi - lo > 0.01


def test_paired_by_seed_index_holds_on_every_seed():
    """Finding #2's suggestive half — reported, and not the licensed reading."""
    assert esw.paired_holds() == (esw.SEEDS, esw.SEEDS) == esw.PAIRED_HOLDS


def test_the_two_readings_genuinely_disagree():
    """The whole point: paired says yes, unpaired says no, on the same numbers."""
    assert esw.paired_holds()[0] == esw.SEEDS
    assert esw.separates() is False


def test_verdict_is_the_downgrade_and_not_a_refutation_or_a_survival():
    v = esw.VERDICT
    assert "seed 0" in v and "unproven" in v
    assert "refuted" not in v and "survives" not in v


def test_unexcited_endpoint_has_a_near_degenerate_arm_population():
    """Finding #3 — seven of eight arms are bit-identical on all eight seeds."""
    assert esw.effective_arms("city_curved_v0") == 2
    tied = esw.tied_arms("city_curved_v0")
    assert len(tied) == 1 and len(tied[0]) == 7
    assert "essps_mppi" not in tied[0]


def test_excited_endpoint_ties_only_the_known_inert_channel():
    """`geometric_mppi` reproducing `stock_mppi` is `clearance_census`'s signature."""
    assert esw.effective_arms("cafe_convoy_v0") == 7
    assert esw.tied_arms("cafe_convoy_v0") == (("geometric_mppi", "stock_mppi"),)


def test_effective_arm_counts_match_the_pins():
    assert {s: esw.effective_arms(s) for s in esw.SEED_ENSEMBLE} == esw.EFFECTIVE_ARMS


def test_unexcited_endpoint_has_a_negative_intersection_width():
    """Finding #4 — seed noise exceeds arm spread; no bar cuts it on every seed."""
    lo, hi, w = esw.intersection("city_curved_v0")
    assert w < 0.0 and hi < lo


def test_excited_endpoint_stays_barrable_at_seed_width():
    """The one piece of D-363's proposal this module leaves standing."""
    lo, hi, w = esw.intersection("cafe_convoy_v0")
    assert w > 0.0 and lo < hi
    assert esw.barrable_at_seed_width() == ("cafe_convoy_v0",)


def test_intersection_widths_match_the_pins():
    assert {s: esw.intersection(s)[2] for s in esw.SEED_ENSEMBLE} == esw.INTERSECTION


def test_a_bar_inside_the_positive_intersection_cuts_on_every_seed():
    """The intersection's operational meaning, checked rather than asserted."""
    lo, hi, _ = esw.intersection("cafe_convoy_v0")
    bar = (lo + hi) / 2.0
    cols = esw.SEED_ENSEMBLE["cafe_convoy_v0"]
    for s in range(esw.SEEDS):
        vals = [r[s] for r in cols.values()]
        assert any(v > bar for v in vals) and any(v <= bar for v in vals), s


def test_no_bar_cuts_the_negative_intersection_scene_on_every_seed():
    """Contrapositive of the above, over the whole attained range."""
    cols = esw.SEED_ENSEMBLE["city_curved_v0"]
    flat = [v for r in cols.values() for v in r]
    grid = [min(flat) + i * (max(flat) - min(flat)) / 200.0 for i in range(201)]
    for bar in grid:
        cuts = all(
            any(r[s] > bar for r in cols.values())
            and any(r[s] <= bar for r in cols.values())
            for s in range(esw.SEEDS)
        )
        assert not cuts, bar


def test_remaining_debt_is_the_six_unwidened_scenes():
    n = len(excursion_tracking.CENSUS) - len(esw.SEED_ENSEMBLE)
    assert esw.REMAINING_DEBT == n * len(esw.SEED_ENSEMBLE["cafe_convoy_v0"]) * esw.SEEDS


def test_scope_is_narrower_than_the_claim_it_refutes():
    """Two scenes can kill a min-vs-max claim and cannot re-derive one."""
    assert len(esw.SEED_ENSEMBLE) < len(excursion_tracking.CENSUS)
    assert esw.REMAINING_DEBT > 0


def test_cli_is_clean_and_drift_free():
    assert esw.drift() == ()
    assert esw.main([]) == 0

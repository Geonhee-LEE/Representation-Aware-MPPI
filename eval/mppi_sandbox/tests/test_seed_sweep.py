# SPDX-License-Identifier: BSD-3-Clause
"""Tests for the rate-over-seeds aggregator (eval/mppi_sandbox/seed_sweep.py).

Two layers:
1. Pure aggregation logic (`_classify`, rate arithmetic) — driven with a
   monkeypatched `run_scenario` so the outcome mix is exact and fast.
2. A thin end-to-end smoke over the real sandbox on `cafe_straight_v0` to prove
   the aggregator wires into `run_scenario` and that a single-seed sweep matches
   the underlying per-seed numbers (the "adds search, not behavior" contract).
"""

from __future__ import annotations

from pathlib import Path

import pytest

from eval.mppi_sandbox import seed_sweep as ss
from eval.mppi_sandbox.run import run_scenario

STRAIGHT = "eval/scenarios/cafe_straight_v0.yaml"


# ---- layer 1: aggregation logic with a fake run_scenario -------------------

def _fake_runs(clearances):
    """Build a run_scenario stub that returns the given clearance per call."""
    calls = {"i": 0}

    def fake(scenario_path, *, controller, seed, run_id, out_dir, **kw):
        c = clearances[calls["i"]]
        calls["i"] += 1
        return {
            "min_obstacle_clearance": c,
            "collision": bool(c < 0.0),
            "pass": bool(c >= 0.0),
            "seed": seed,
        }
    return fake


def test_classify_bands():
    assert ss._classify(-0.01, 0.10) == "collision"
    assert ss._classify(0.0, 0.10) == "near_miss"
    assert ss._classify(0.05, 0.10) == "near_miss"
    assert ss._classify(0.10, 0.10) == "safe"
    assert ss._classify(1.0, 0.10) == "safe"


def test_rates_count_correctly(monkeypatch):
    # 8 seeds: 2 collide, 2 near-miss, 4 safe.
    clearances = [-0.2, -0.1, 0.05, 0.09, 0.5, 0.5, 0.5, 0.5]
    monkeypatch.setattr(ss, "run_scenario", _fake_runs(clearances))
    r = ss.seed_sweep(STRAIGHT, controller="stock_mppi",
                      seeds=range(8), near_miss_m=0.10)
    assert r["n_seeds"] == 8
    assert r["collision_rate"] == pytest.approx(2 / 8)
    assert r["near_miss_rate"] == pytest.approx(2 / 8)
    assert r["unsafe_rate"] == pytest.approx(4 / 8)
    assert r["pass_rate"] == pytest.approx(6 / 8)   # the 6 non-colliding runs
    assert r["clearance_min"] == pytest.approx(-0.2)


def test_all_rates_in_unit_interval(monkeypatch):
    clearances = [-0.2, 0.05, 0.5]
    monkeypatch.setattr(ss, "run_scenario", _fake_runs(clearances))
    r = ss.seed_sweep(STRAIGHT, seeds=range(3))
    for key in ("collision_rate", "near_miss_rate", "unsafe_rate", "pass_rate"):
        assert 0.0 <= r[key] <= 1.0


def test_near_miss_threshold_monotonic(monkeypatch):
    # A wider near-miss band can only *increase* (never decrease) near_miss_rate.
    clearances = [0.05, 0.15, 0.25, 0.5]

    def sweep(nm):
        monkeypatch.setattr(ss, "run_scenario", _fake_runs(list(clearances)))
        return ss.seed_sweep(STRAIGHT, seeds=range(4), near_miss_m=nm)

    rates = [sweep(nm)["near_miss_rate"] for nm in (0.10, 0.20, 0.30)]
    assert rates == sorted(rates)
    assert rates[0] == pytest.approx(1 / 4)   # only 0.05
    assert rates[2] == pytest.approx(3 / 4)   # 0.05, 0.15, 0.25


def test_empty_seeds_rejected():
    with pytest.raises(ValueError):
        ss.seed_sweep(STRAIGHT, seeds=[])


def test_negative_near_miss_rejected():
    with pytest.raises(ValueError):
        ss.seed_sweep(STRAIGHT, seeds=range(2), near_miss_m=-0.1)


def test_parse_seeds():
    assert ss._parse_seeds("8") == list(range(8))
    assert ss._parse_seeds("0,3,7") == [0, 3, 7]
    assert ss._parse_seeds("2-5") == [2, 3, 4, 5]


# ---- layer 2: real-sandbox smoke -------------------------------------------

def test_single_seed_sweep_matches_run_scenario():
    """A 1-seed sweep must reproduce the underlying run_scenario clearance —
    the aggregator adds search, not simulation behavior."""
    ref = run_scenario(STRAIGHT, controller="stock_mppi", seed=0, out_dir=None)
    r = ss.seed_sweep(STRAIGHT, controller="stock_mppi", seeds=[0])
    assert r["n_seeds"] == 1
    assert r["clearance_min"] == pytest.approx(ref["min_obstacle_clearance"])
    assert r["per_seed"][0]["collision"] == ref["collision"]


def test_multi_seed_sweep_writes_json(tmp_path):
    r = ss.seed_sweep(STRAIGHT, controller="stock_mppi", seeds=range(3),
                      run_id="unit-straight-sweep", out_dir=tmp_path)
    out = Path(tmp_path) / "unit-straight-sweep.json"
    assert out.exists()
    assert r["n_seeds"] == 3
    assert len(r["per_seed"]) == 3
    # cafe_straight has no obstacles → clearance is +inf, zero unsafe.
    assert r["collision_rate"] == 0.0

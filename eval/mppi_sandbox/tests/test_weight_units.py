# SPDX-License-Identifier: BSD-3-Clause
"""Q-049 — in what units should a cost weight be swept?

D-027 found `w_voo = 200` was **6.19×** the median baseline cost spread on
`cafe_obstacle_crossing_v0`, which made it a disguised temperature change
(median ESS 77.9 → 1.00, argmin-over-draws, and the arm collides). STATE #2
asked whether the other three shipped critic weights carry the same hazard.
This file answers it with `weight_units.measure`, and the answer is **not the
one the question presumed** — three of the four cannot be given a ratio at all,
and the ratio's *denominator* turns out to be the load-bearing choice.

## 1. Q-049's four weights do not form one class

| knob | shipped | ratio on the healthy baseline arm | why |
|---|---|---|---|
| `w_terminal` | 30 | **0.328** | the only one that is a plain additive coefficient with a live term |
| `w_risk` | 40 | **0.064** (on its own arm) | live, but small |
| `w_epist` | 200 | **exactly 0** | multiplies a term whose spread is identically 0 (D-021) |
| `k_margin_per_sigma` | 0 | **undefined** | not a coefficient on a term — unit is metres |

So the units hazard D-027 surfaced is real but **narrow**: it applies to the
one term that is both live and large, and the two epistemic knobs escape it for
opposite reasons — one multiplies nothing, the other is not a multiplier.

## 2. The denominator is the finding, not the numerator

`w_voo = 200`, same scene, same `lam = 1.6`, measured two ways:

- against the arm it is **added to** (`w_voo = 0`, 114 steps): **6.19×** (D-027)
- against the arm it is **carried on** (`w_voo = 200`, 1000 steps): **1.46×**

The self-referential measurement **understates by 4.2×**, and the mechanism is
worse than a scale error: at `w_voo = 200` the run **never completes** (1000
steps against the baseline's 114), so it spends most of its life far off-path,
and `w_path`'s own spread inflates **11.6×** (48.1 → 555.7). The denominator
rises 79.09 → 862.6, a **10.9× inflation of the landscape the weight itself
created**. A weight measured on its own arm is graded against the damage it
did — and the worse the weight, the more it flatters itself. The ratio is only
meaningful against the baseline the weight is being **added to**.

## 3. `w_collision = 1e4` is the repo's largest weight and it is silent

Its per-sample spread is **exactly 0 at the median on both arms** — even the
derailed one, where it fires only intermittently (mean 2210, median 0). It is a
guard, not a competitor. Note this refutes the tempting explanation for §2:
the inflated denominator is *not* the collision term waking up, it is ordinary
path-tracking cost on a trajectory that went bad. The real competitor on the
healthy arm is `w_path = 20` at ratio **2.42** — the baseline landscape *is*
path tracking.

## 4. The exchange rate is exactly linear, and still not extrapolable

On a fixed rollout batch `ptp(w·f)/w` is constant to machine precision for
every additive coefficient (ratio 1.000000, not merely ≈). In closed loop the
same quantity for `w_voo` reads 2.50 / 2.34 / 5.30 at w = 1 / 7 / 200 — because
a different weight steers to a different state sequence. So the algebra is
linear and the *measurement* is not: a ratio must be measured at the weight you
intend to ship, never extrapolated from a cheap small-weight probe.
"""

from __future__ import annotations

import numpy as np
import pytest

from eval.mppi_sandbox.controllers import make_controller
from eval.mppi_sandbox.controllers.stock_mppi import MPPIParams
from eval.mppi_sandbox.run import ROBOT_RADIUS
from eval.mppi_sandbox.scenario import load_scenario
from eval.mppi_sandbox.weight_units import (ADDITIVE_WEIGHTS,
                                            NON_ADDITIVE_KNOBS,
                                            REPORTING_STATISTIC,
                                            batch_per_unit_spread,
                                            closed_loop_per_unit_spread,
                                            format_table, measure, shadow_batch,
                                            _set)

CROSSING = "eval/scenarios/cafe_obstacle_crossing_v0.yaml"
#: The temperature D-027 measured the 6.19× at — quoted so both files' ratios
#: are comparable. The shipped `lam = 0.1` is argmin-over-draws (D-024).
LAM = 1.6
#: Isolate the epistemic terms from the DYNAMIC risk cost and the margin
#: critic, matching `test_observation_value_critic` / `test_epistemic_reach_gate`.
_ISOLATE = dict(w_risk=0.0, k_margin_per_sigma=0.0)
_W_LOUD = 200.0

_CACHE: dict = {}


def _crossing():
    if "sc" not in _CACHE:
        _CACHE["sc"] = load_scenario(CROSSING)
    return _CACHE["sc"]


def _table(**kw) -> dict:
    key = tuple(sorted(kw.items()))
    if key not in _CACHE:
        _CACHE[key] = measure(_crossing(), params=MPPIParams(lam=LAM), **kw)
    return _CACHE[key]


def _baseline():
    """The healthy arm every add-on weight is being *added to*."""
    return _table(**_ISOLATE, w_voo=0.0)


@pytest.mark.slow
class TestTheDecompositionIsExact:
    """Leave-one-out by weight-toggling must recover the cost exactly, or every
    number in this file is measuring a re-implementation rather than the
    controller (the drift failure mode `ab.median_ess` was written to avoid)."""

    def test_zeroing_every_weight_zeroes_the_cost(self):
        """Every term in `_cost` carries a weight — nothing is unattributed."""
        ctrl = make_controller("risk_mppi", _crossing(), seed=0,
                               robot_radius=ROBOT_RADIUS,
                               params=MPPIParams(lam=LAM), **_ISOLATE,
                               w_voo=_W_LOUD)
        state = np.zeros(5)
        state[:3] = _crossing().start[:3]
        ctrl.command(state, 0.0)
        traj = shadow_batch(ctrl)
        for path in ADDITIVE_WEIGHTS.values():
            try:
                _set(ctrl, path, 0.0)
            except AttributeError:
                pass
        assert np.allclose(ctrl._cost(traj, 0.0), 0.0), (
            "a cost term survived with every declared weight at 0 — "
            "ADDITIVE_WEIGHTS is missing a term, so its spread is silently "
            "folded into every other term's `rest` denominator")

    def test_toggling_a_weight_restores_it(self):
        """`measure` must leave the arm it borrowed exactly as it found it."""
        before = _baseline()
        again = measure(_crossing(), params=MPPIParams(lam=LAM),
                        **_ISOLATE, w_voo=0.0)
        assert {k: v.spread_median for k, v in before.items()} == \
               {k: v.spread_median for k, v in again.items()}


class TestTheRatioPrecondition:
    """§4 — "w is r× the baseline" presumes ptp(w·f) is linear in w."""

    @pytest.mark.parametrize("knob,weights", [
        ("w_voo", [1.0, 7.0, _W_LOUD]),
        ("w_terminal", [1.0, 30.0]),
        ("w_path", [1.0, 20.0]),
    ])
    def test_additive_coefficients_are_linear_to_machine_precision(
            self, knob, weights):
        v = batch_per_unit_spread(_crossing(), knob, weights,
                                  params=MPPIParams(lam=LAM), **_ISOLATE)
        assert max(v) - min(v) <= 1e-9 * max(v), (
            f"{knob} per-unit spread varies across weights {weights}: {v} — "
            f"it is not a plain coefficient and has no exchange rate")

    def test_the_margin_knob_is_not_linear_and_so_has_no_ratio(self):
        """`k_margin_per_sigma` shifts `clear` inside `exp(-clear/scale)` and
        inside the `clear < 0` indicator. Measured on a batch that actually
        reaches the shadow (the closed loop does not — D-021), the per-unit
        spread moves by more than 2× across the knob's own range."""
        ctrl = make_controller("risk_mppi", _crossing(), seed=0,
                               robot_radius=ROBOT_RADIUS,
                               params=MPPIParams(lam=LAM), w_risk=1.0,
                               k_margin_per_sigma=0.2)
        state = np.zeros(5)
        state[:3] = _crossing().start[:3]
        ctrl.command(state, 0.0)
        _set(ctrl, "w_risk", 0.0)
        traj = shadow_batch(ctrl)

        per_unit = []
        for k in (0.05, 0.1, 0.2, 0.4):
            _set(ctrl, "critic.k_margin_per_sigma", k)
            full = ctrl._cost(traj, 0.0)
            _set(ctrl, "critic.k_margin_per_sigma", 0.0)
            per_unit.append(float(np.ptp(full - ctrl._cost(traj, 0.0))) / k)

        assert min(per_unit) > 0.0, (
            "the margin knob was inert on the shadow batch too — the "
            "non-additivity claim is untested, not established")
        assert max(per_unit) / min(per_unit) > 2.0, (
            f"per-unit spread {per_unit} is nearly constant — "
            f"`k_margin_per_sigma` may be expressible as a coefficient after "
            f"all, and NON_ADDITIVE_KNOBS should be revisited")

    def test_measure_refuses_a_live_margin_knob(self):
        """Leaving it on would make every *other* row conditional on it."""
        with pytest.raises(ValueError, match="not an additive cost"):
            measure(_crossing(), k_margin_per_sigma=0.2)

    def test_the_knob_is_documented_with_its_real_unit(self):
        assert "metres" in NON_ADDITIVE_KNOBS["k_margin_per_sigma"]


@pytest.mark.slow
class TestTheShippedWeightsTable:
    """§1 — Q-049's actual question, on the healthy baseline arm."""

    def test_path_tracking_is_the_baseline_landscape(self):
        base = _baseline()
        assert base["w_path"].ratio > 1.0
        loudest = max(base.values(), key=lambda t: t.ratio)
        assert loudest.name == "w_path", (
            f"{loudest.name} now spans more of the cost than path tracking "
            f"— the 'baseline landscape is path tracking' claim in this "
            f"file's docstring needs re-deriving")

    def test_terminal_is_the_only_shipped_weight_with_a_live_ratio(self):
        base = _baseline()
        assert 0.0 < base["w_terminal"].ratio < 1.0, (
            "w_terminal=30 moved out of the modest band — it was the one "
            "Q-049 knob that was neither silent nor non-additive")

    def test_the_largest_weight_in_the_repo_is_exactly_silent(self):
        """§3 — `w_collision = 1e4` never varies across a healthy batch."""
        base = _baseline()
        assert base["w_collision"].weight >= 1e4
        assert base["w_collision"].spread_median == 0.0, (
            "the collision indicator now has spread on a healthy run — this "
            "arm is colliding and every `rest` denominator here is inflated")

    def test_w_epist_is_a_large_weight_multiplying_exactly_zero(self):
        """D-021 re-derived by the general instrument rather than quoted."""
        tb = _table(**_ISOLATE, w_epist=_W_LOUD)
        assert tb["w_epist"].weight == _W_LOUD
        assert tb["w_epist"].spread_median == 0.0
        assert tb["w_epist"].ratio == 0.0

    def test_w_risk_is_live_but_small_on_its_own_arm(self):
        tb = _table(k_margin_per_sigma=0.0)          # w_risk=40 default
        assert 0.0 < tb["w_risk"].ratio < 0.5

    def test_the_table_renders(self):
        out = format_table(_baseline())
        assert out.startswith("| term |") and "`w_path`" in out


@pytest.mark.slow
class TestTheDenominatorIsTheFinding:
    """§2 — the same weight reads harmless or catastrophic depending on which
    arm supplies the denominator, and the difference is two orders of
    magnitude. This is the part of Q-049 that generalises."""

    def test_the_self_referential_ratio_understates_the_hazard(self):
        """1.46× on its own arm vs 6.19× (D-027) against the baseline. Both
        exceed 1, so the *verdict* survives here — but the margin does not, and
        §2's mechanism says the understatement grows with the damage."""
        own = _table(**_ISOLATE, w_voo=_W_LOUD)
        base = _baseline()
        against_baseline = (own["w_voo"].spread_per_unit_weight * _W_LOUD
                            / base["w_collision"].rest_median)
        assert own["w_voo"].ratio < against_baseline / 2.0, (
            f"self-referential {own['w_voo'].ratio:.3g} is no longer a "
            f"substantial understatement of {against_baseline:.3g} — the trap "
            f"this class documents may have closed on its own")

    def test_measured_against_the_baseline_it_is_added_to_it_is_catastrophic(self):
        base = _baseline()
        # D-027's construction: exchange rate probed on the *baseline*
        # trajectory (2.45 per unit), denominator the baseline's own spread.
        assert 5.0 < _W_LOUD * 2.45 / base["w_collision"].rest_median < 8.0, (
            f"the baseline spread moved from D-027's 79.09 to "
            f"{base['w_collision'].rest_median:.4g}; the quoted 6.19x no "
            f"longer follows and §2 needs re-deriving")

    def test_the_two_denominators_disagree_by_an_order_of_magnitude(self):
        own = _table(**_ISOLATE, w_voo=_W_LOUD)
        base = _baseline()
        assert (own["w_collision"].rest_median
                / base["w_collision"].rest_median) > 5.0, (
            "the self-referential and baseline denominators have converged — "
            "the 'a weight is graded against the damage it did' finding is "
            "scene- or version-specific and should be re-stated")

    def test_the_inflation_is_a_landscape_the_weight_created(self):
        """Mechanism. Not the collision term (silent at the median on both
        arms) — the loud arm simply never finishes, so ordinary path-tracking
        cost is evaluated on a trajectory that has gone bad."""
        own = _table(**_ISOLATE, w_voo=_W_LOUD)
        base = _baseline()
        assert own["w_path"].n_steps > 3 * base["w_path"].n_steps, (
            "the loud arm now completes in a comparable number of steps, so "
            "the 'it is graded on its own wreckage' explanation is wrong")
        assert own["w_path"].spread_median > 5 * base["w_path"].spread_median
        assert own["w_collision"].spread_median == 0.0, (
            "the collision indicator now moves the *median* — §3's claim that "
            "the inflation is not the collision term needs re-checking")


@pytest.mark.slow
class TestExtrapolationFails:
    """§4's second half — linear algebra, non-transferable measurement."""

    def test_closed_loop_exchange_rate_moves_with_the_weight(self):
        v = closed_loop_per_unit_spread(
            _crossing(), "w_voo", [1.0, 7.0, _W_LOUD],
            params=MPPIParams(lam=LAM), **_ISOLATE)
        assert max(v) / min(v) > 1.5, (
            f"closed-loop per-unit spread {v} is near-constant — a cheap "
            f"small-weight probe would then be a valid way to pick a shipping "
            f"weight, which this file claims it is not")


class TestTheStatisticIsDeclared:
    """The D-024 mistake class: never divide by a statistic nobody named."""

    def test_the_reporting_statistic_is_median(self):
        assert REPORTING_STATISTIC == "median"

    def test_median_and_mean_disagree_enough_for_the_choice_to_matter(self):
        """On the *raw* spread the two differ ~48× (79.09 vs 3806.8 in D-027).
        The ratio is a quotient of two skewed quantities so it is far tamer —
        which is itself the reason to report the ratio rather than the spread,
        and the reason this bound is loose rather than dramatic."""
        base = _baseline()
        assert max(t.statistic_disagreement for t in base.values()) > 1.1

# SPDX-License-Identifier: BSD-3-Clause
"""Q-042: what should window admissibility *be*, given D-019 showed the
shipped rule is a conjunction that tightens monotonically with `n`?

STATE's first item asked whether the three candidate criteria could be scored
without new simulation, gated on "does `ab.LamProbe` retain per-seed ESS?".
**It does not — and it never needed to.** Seeds are exchangeable, so the
per-seed in-band indicator is an unordered binary vector and `(n_in_band, n)`
is a sufficient statistic for it. Every criterion below is a function of that
pair, so the *in-band* half of Q-042 was always re-scorable from stored
probes.

The completion half was not, and that is the one real gap: `all_reached` is a
boolean, and `False` is consistent with any `n_reached` in `[0, n)`. Fixed
here by recording `n_reached`; historical probes carry the `-1` sentinel and
the fractional criteria refuse to guess on them.

Scored on the case that forced the question — `stock_mppi @ lam = 1.6` on
`cafe_obstacle_crossing_v0`, D-019's flip, where completion is perfect at both
counts (8/8 reach) so *only* the band moves:

| criterion                   | n = 4 (4/4) | n = 8 (7/8) | verdict stable? |
|-----------------------------|-------------|-------------|-----------------|
| (a) all seeds               | admissible  | lost        | **no**          |
| (b) quantile >= ceil(0.9 n) | admissible  | lost        | **no**          |
| (c) Wilson lower bound      | 0.510       | 0.529       | **yes**         |

Two findings, in descending order of how much they cost to get:

1. **(b) is a no-op, not a near-miss.** `ceil(0.9 n) == n` for every `n <= 9`,
   so at the seed counts this repo runs (4 and 8) criterion (b) is *pointwise
   identical* to (a) — same verdicts, same monotone bias, same everything. It
   becomes a distinct rule only at `n >= 10`. Pure arithmetic; zero runs.
2. **(c) inverts the bias rather than softening it.** At `k = n` the Wilson
   lower bound is exactly `n / (n + z^2)`, strictly *increasing* in `n`: seeds
   that all pass buy confidence instead of spending it, so a window can grow
   with evidence. On the measured case the seed lost at n = 8 is more than
   paid for by the four extra draws, and the verdict holds for any threshold
   outside the sliver `(0.510, 0.529]`.

D-019 keeps (a) as the default and stamps `n` on every verdict; nothing in the
repo's reported windows moves. This file is the evidence for what should
replace it, and the API to do so when the queue drains.

CI cost: **two seed sweeps** (n = 4 and n = 8, one arm, one rung) — the same
probe D-019 already paid for, reused via a module-level memo. Every other test
here is arithmetic on constructed probes and simulates nothing.
"""

from math import ceil, comb

import numpy as np
import pytest

from eval.mppi_sandbox import ab
from eval.mppi_sandbox.scenario import load_scenario

PARENT = "eval/scenarios/cafe_obstacle_crossing_v0.yaml"
LAM = 1.6           # the rung D-019's flip turns on
ARM = "stock_mppi"  # the arm that loses it

_CACHE: dict[int, ab.LamProbe] = {}


def _probe(n: int) -> ab.LamProbe:
    """D-019's probe at seed count `n`. Two sweeps total for the whole file."""
    if n not in _CACHE:
        _CACHE[n] = ab.lam_ladder(load_scenario(PARENT), ARM, [LAM],
                                  seeds=range(n))[0]
    return _CACHE[n]


def _fake(n_in_band: int, n: int, n_reached: int | None = None) -> ab.LamProbe:
    """A probe with only the fields the criteria read. Simulates nothing."""
    reached = n if n_reached is None else n_reached
    return ab.LamProbe(lam=LAM, median_ess=50.0, min_ess=40.0, max_ess=60.0,
                       n_in_band=n_in_band, n=n, all_reached=reached == n,
                       n_reached=reached)


# --- 1. the opening question: what is re-scorable without new runs -----------

class TestWhatStoredProbesCanAnswer:

    def test_the_in_band_half_needs_only_the_count_not_the_per_seed_values(self):
        """The answer to STATE item #1's gate.

        `lam_ladder` discards per-seed ESS and keeps `(n_in_band, n)`. That is
        a **sufficient statistic**: two probes agreeing on the pair are
        indistinguishable to every criterion here, however different the ESS
        values behind them were. So "does LamProbe retain per-seed ESS?" was
        the wrong gate — the answer is no, and the in-band half is re-scorable
        anyway.
        """
        tight = ab.LamProbe(lam=LAM, median_ess=13.0, min_ess=12.9,
                            max_ess=13.1, n_in_band=7, n=8, all_reached=True,
                            n_reached=8)
        scattered = ab.LamProbe(lam=LAM, median_ess=90.0, min_ess=1.0,
                                max_ess=200.0, n_in_band=7, n=8,
                                all_reached=True, n_reached=8)
        for criterion in (ab.all_seeds, ab.at_least_quantile(0.9),
                          ab.wilson_lower_at_least(0.5)):
            assert criterion(tight) == criterion(scattered)

    def test_a_bootstrap_over_seeds_is_a_function_of_the_same_pair(self):
        """Criterion (c) was filed as "seed-bootstrap interval estimate", which
        sounds like it needs the per-seed vector. It does not: resampling an
        exchangeable binary vector with `k` ones is resampling from `(k, n)`,
        so the bootstrap has no information the stored counts lack.

        The sufficient-statistic claim, stated exactly: the resample mean of a
        binary vector with `k` ones is distributed as `Binomial(n, k/n) / n`,
        whatever order the ones sit in. Two different orderings are each
        checked against that same closed form — matching each other only
        because both match it.

        (An earlier draft compared the two orderings' *realised* samples under
        a shared index matrix. That is the wrong test: exchangeability equates
        distributions, not sample paths, and the realisations differ by
        Monte-Carlo noise.)
        """
        k, n, trials = 7, 8, 40_000
        exact = np.array([comb(n, j) * (k / n) ** j * (1 - k / n) ** (n - j)
                          for j in range(n + 1)])

        for ones_at_end, vec in (
                (True, np.array([0, 1, 1, 1, 1, 1, 1, 1], dtype=float)),
                (False, np.array([1, 1, 1, 1, 1, 1, 1, 0], dtype=float))):
            idx = np.random.default_rng(1).integers(0, n, size=(trials, n))
            counts = vec[idx].sum(axis=1).astype(int)
            empirical = np.bincount(counts, minlength=n + 1) / trials
            assert np.abs(empirical - exact).max() < 0.01, (
                f"ordering (zero last={not ones_at_end}) departs from "
                "Binomial(n, k/n) — the resample would then carry information "
                "beyond (k, n)")

    def test_but_the_bootstrap_is_too_granular_to_use_at_these_seed_counts(self):
        """**Why (c) ships as a closed form rather than as the resampling its
        Q-042 wording implied** — and this cycle's one genuine surprise: the
        two do *not* agree at n = 8.

        A resample of `n` draws has support on the lattice `{0, 1/n, ..., 1}`,
        so its lower quantile is quantised to `1/n` — while the effect Q-042
        needs to resolve is the 0.019 gap between the n = 4 and n = 8 bounds.
        At n = 8 the step is `0.125`, nearly seven times the signal. Measured
        like-for-like (both 2.5% lower ends, `k/n = 0.875`):

        | n    | bootstrap p2.5 | Wilson | gap    | lattice 1/n |
        |------|----------------|--------|--------|-------------|
        | 8    | 0.6250         | 0.5291 | +0.096 | 0.125       |
        | 40   | 0.7750         | 0.7389 | +0.036 | 0.025       |
        | 1000 | 0.8540         | 0.8531 | +0.001 | 0.001       |

        Two things this does **not** show, stated because the first draft of
        this test asserted both and failed: the gap is *not* bounded by one
        lattice unit (n = 40 exceeds it — Wilson's small-sample conservatism
        contributes on top of granularity), and the bootstrap is not merely
        noisy but systematically **anti-conservative** here, sitting above the
        closed form at every `n`. What survives is the convergence and the
        magnitude at n = 8, which is all Q-042 needs.
        """
        k = lambda n: round(0.875 * n)   # noqa: E731 — table row helper
        gaps = {}
        for n in (8, 40, 1000):
            draws = np.random.default_rng(0).binomial(
                n, k(n) / n, size=40_000) / n
            gaps[n] = np.percentile(draws, 2.5) - ab.wilson_lower(k(n), n)
            assert gaps[n] > 0, f"n={n}: bootstrap fell below the closed form"

        assert gaps[8] > gaps[40] > gaps[1000]
        assert gaps[1000] < 1e-3, "the two should agree in the large-n limit"
        # The n = 8 disagreement dwarfs the effect the criterion must resolve.
        assert gaps[8] > 4 * (ab.wilson_lower(7, 8) - ab.wilson_lower(4, 4))

    def test_the_completion_half_refuses_to_guess_on_a_pre_q042_probe(self):
        """The one thing that genuinely was not re-scorable, and the reason
        `n_reached` had to be added rather than derived.

        `all_reached=False` maps to any `n_reached` in `[0, n)`; reading it as
        `0` or as `n - 1` are both fabrications. The fractional criteria raise
        instead — while `all_seeds`, which needs only the boolean, still works
        on the very same probe.
        """
        legacy = ab.LamProbe(lam=LAM, median_ess=50.0, min_ess=40.0,
                             max_ess=60.0, n_in_band=8, n=8, all_reached=False)
        assert legacy.n_reached == -1
        assert np.isnan(legacy.reached_fraction)
        assert ab.all_seeds(legacy) is False        # boolean is enough

        for criterion in (ab.at_least_quantile(0.9),
                          ab.wilson_lower_at_least(0.5)):
            with pytest.raises(ValueError, match="no `n_reached`"):
                criterion(legacy)

    def test_lam_ladder_now_records_the_count(self):
        """Going forward the gap is closed at the source."""
        p = _probe(8)
        assert p.n_reached == 8 and p.reached_fraction == 1.0
        assert p.all_reached is (p.n_reached == p.n)


# --- 2. criterion (b) is a no-op below n = 11 --------------------------------

class TestTheQuantileCriterionIsIdenticalToAllSeeds:

    @pytest.mark.parametrize("n", range(1, 10))
    def test_ceil_of_nine_tenths_n_is_n_for_every_seed_count_we_run(self, n):
        """`ceil(0.9 n) == n` up to n = 9 — so "at least 90% of seeds" and
        "every seed" are the same sentence at n = 4 and n = 8, the only two
        counts in this repo."""
        assert ceil(0.9 * n) == n

    @pytest.mark.parametrize("n_in_band,n", [(4, 4), (7, 8), (8, 8), (0, 4),
                                             (3, 4), (6, 8)])
    def test_the_two_criteria_agree_pointwise_at_these_counts(self, n_in_band, n):
        probe = _fake(n_in_band, n)
        assert ab.at_least_quantile(0.9)(probe) == ab.all_seeds(probe)

    def test_they_diverge_once_there_are_ten_seeds(self):
        """Not vacuously true — the criterion does eventually differ, which is
        what makes "no-op at n <= 9" a measurement rather than a tautology.
        n = 10 is the first count at which (b) tolerates a failing seed."""
        assert ceil(0.9 * 10) == 9
        ten = _fake(9, 10)
        assert ab.at_least_quantile(0.9)(ten) and not ab.all_seeds(ten)


# --- 3. criterion (c) is not biased by the seed count ------------------------

class TestTheWilsonCriterionRewardsEvidence:

    def test_a_perfect_arm_scores_higher_the_more_seeds_it_survives(self):
        """The direct inversion of D-019's defect. At `k = n` the bound is
        `n / (n + z^2)`, so unlike a conjunction it *rises* with `n`."""
        bounds = [ab.wilson_lower(n, n) for n in (2, 4, 8, 16, 32)]
        assert bounds == sorted(bounds) and len(set(bounds)) == len(bounds)
        for n in (2, 4, 8, 16, 32):
            assert ab.wilson_lower(n, n) == pytest.approx(
                n / (n + ab.Z_95 ** 2))

    def test_it_never_claims_certainty_from_a_finite_sample(self):
        """`k / n = 1` reads as proof; the interval does not. This is the
        property that stops a 2-seed sweep outranking an 8-seed one.

        The zero end is exactly `0.0`, not merely small — at `k = 0` the
        Wilson centre and half-width are both `z^2 / 2n` and cancel. So the
        bound is a genuine `[0, 1]` quantity with both ends attainable only in
        the limit, and a rung no seed passes cannot be rescued by any
        threshold above zero.
        """
        assert ab.wilson_lower(4, 4) < 1.0
        assert ab.wilson_lower(0, 8) == 0.0
        assert not ab.wilson_lower_at_least(1e-9)(_fake(0, 8))
        assert np.isnan(ab.wilson_lower(0, 0))


# --- 4. the three criteria on D-019's actual flip ----------------------------

class TestScoredOnTheCaseThatForcedTheQuestion:

    def test_the_flip_is_purely_in_band_completion_is_perfect_at_both_counts(self):
        """Prerequisite for the comparison below to be about the band at all.
        If completion moved too, the criteria would be scored on a confounded
        case and none of the verdicts would be attributable."""
        four, eight = _probe(4), _probe(8)
        assert (four.n_in_band, four.n) == (4, 4)
        assert (eight.n_in_band, eight.n) == (7, 8)
        assert four.reached_fraction == eight.reached_fraction == 1.0

    def test_criteria_a_and_b_both_flip_with_the_seed_count(self):
        """D-019, reproduced — and (b) fails in exactly the same place, which
        is the whole content of "(b) is a no-op"."""
        four, eight = [_probe(n) for n in (4, 8)]
        for criterion in (ab.all_seeds, ab.at_least_quantile(0.9)):
            assert criterion(four) and not criterion(eight)

    def test_criterion_c_holds_the_verdict_across_the_same_flip(self):
        """The payoff. The bound does not merely survive the extra seeds, it
        *improves* — the four additional draws outweigh the one that fell out
        of band, so the n = 8 window is the better-evidenced of the two."""
        four, eight = [ab.wilson_lower(p.n_in_band, p.n)
                       for p in (_probe(4), _probe(8))]
        assert four == pytest.approx(0.510, abs=0.01)
        assert eight == pytest.approx(0.529, abs=0.01)
        assert eight > four

        # Same verdict at any threshold outside the (0.510, 0.529] sliver.
        for threshold in (0.3, 0.4, 0.5, 0.55, 0.6):
            criterion = ab.wilson_lower_at_least(threshold)
            assert criterion(_probe(4)) == criterion(_probe(8)), (
                f"threshold {threshold} splits the two seed counts")

    def test_the_window_reported_in_the_repo_is_unchanged_by_this_cycle(self):
        """D-019 keeps (a) as the default, so `admissible_lams` must return
        exactly what it returned before the `criterion` parameter existed. If
        this fails, every window in every journal entry silently moved."""
        four, eight = _probe(4), _probe(8)
        assert ab.admissible_lams([four]) == (LAM,)
        assert ab.admissible_lams([eight]) == ()
        assert ab.admissible_lams([four, eight], ab.all_seeds) == (LAM,)

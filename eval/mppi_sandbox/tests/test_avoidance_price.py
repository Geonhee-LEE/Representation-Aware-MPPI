# SPDX-License-Identifier: BSD-3-Clause
"""Q-185 answered, and its premise corrected on the way.

D-440 shipped `w_heading`, watched it convert 16/16 seeds on the obstacle-free
scene and only 11/5 on `cafe_obstacle_crossing_v0`, and filed Q-185 rather than
guessing which of two things the leftover residual was:

  (a) unpriced tracking error  -> tune / reshape the term
  (b) the definitional price of leaving the path to avoid  -> move the
      acceptance threshold or the metric's reference, not the cost

Q-185 named the discriminator: correlate each seed's heading residual against
how much avoidance that seed bought, **in both arms**. If the tie loosens once
heading is priced, the term collected the tracking share and (a) is what is
left; if it survives, the share was never tracking error and (b) holds.

Measured 2026-08-23 11:00, `cafe_obstacle_crossing_v0`, n = 16 paired seeds,
32 integrations, ~19 s:

    proxy       w_heading=0            w_heading=32
    detour      rho = +0.962  p<1e-4   rho = +0.977  p<1e-4
    clearance   rho = -0.468  p=0.069  rho = -0.518  p=0.042

The tie does not loosen. It **tightens**. Pricing heading at 32 — the weight
that converts every seed on the obstacle-free scene — leaves the residual just
as tightly ranked by detour as it was unpriced. That is branch (b), and it is
not a marginal reading: rho = 0.96 on 16 points is a near-perfect rank
agreement, and the same number at both arms means the priced term did not
touch that component at all.

**The premise correction.** Q-181 and Q-185 both assumed the deviation was
*buying* clearance — "residual is the price of avoidance". On this scene it is
not. Detour and clearance are **negatively** correlated in both arms
(rho = -0.550, p = 0.030 at w=0; rho = -0.526, p = 0.040 at w=32): the seeds
that deviate most from the path are the seeds that pass **closest** to the
obstacle. The deviation is a late swerve that pays in heading error and does
not buy clearance back. So the residual is definitional *with respect to the
reference path* (b holds) while the avoidance it is supposedly the price of is
not being purchased — which makes "raise the threshold on obstacle scenes" the
wrong repair for the right reason, and points at the ordering/timing of the
avoidance response instead.

`test_the_two_proxies_disagree_in_sign` exists because that correction is the
part most likely to be dropped when this gets quoted: the headline verdict is
one string and the sign split is the thing under it.
"""

import numpy as np
import pytest

from eval.mppi_sandbox import avoidance_price as ap
from eval.mppi_sandbox.scenario import load_scenario

# Cheap in the tests; the module default (20_000) is what a cycle quotes.
# 2_000 resolves p to ~5e-4, far finer than any threshold asserted here.
PERM = 2_000


@pytest.fixture(scope="module")
def arms():
    """Both arms, measured once. 32 integrations, ~19 s — the whole cost."""
    sc = load_scenario(ap.SCENE)
    off = ap.measure_arm(sc, 0.0)
    on = ap.measure_arm(sc, 32.0)
    # The reached-goal precondition used to be asserted here; D-443 moved it
    # into `measure_arm` as a raise. Not a deletion — the check is stricter
    # there (it names the offending seeds and fires before any caller sees the
    # rows) and it keeps this fixture free of assertions on the runs, which is
    # what `test_two_sites_are_not_tests_and_neither_bills_a_sim` reads.
    return off, on


# --- the reading ---------------------------------------------------------


def test_the_tie_to_detour_survives_being_priced(arms):
    """Q-185 resolves to (b): rho does not loosen at w_heading = 32.

    The load-bearing assertion of this file. If a future cycle strengthens the
    heading term and this starts failing, Q-185's answer has changed and the
    threshold argument built on it is stale — which is exactly what should
    make noise.
    """
    off_rows, on_rows = arms
    off = ap.correlate(off_rows, 0.0, n_perm=PERM)
    on = ap.correlate(on_rows, 32.0, n_perm=PERM)

    # Both arms: the residual is ranked by detour, near-perfectly.
    assert off.rho_detour > 0.85, f"unpriced arm: rho={off.rho_detour:.3f}"
    assert on.rho_detour > 0.85, f"priced arm: rho={on.rho_detour:.3f}"
    assert off.p_detour < 0.01 and on.p_detour < 0.01

    assert not ap.loosened(off, on, proxy="detour"), (
        f"the tie loosened ({off.rho_detour:.3f} -> {on.rho_detour:.3f}) — "
        "Q-185 branch (a), not (b); re-read before quoting D-442")
    assert ap.verdict(off, on).startswith("Q-185 (b)")


def test_pricing_heading_still_moved_the_mean(arms):
    """(b) is not "the term did nothing" — guard against that misreading.

    D-440's -13% is still there. The term moves the *level* of the residual
    and leaves its *composition* untouched, and those are different claims;
    this pins the first so (b) cannot be quoted as "w_heading is inert here"
    the way D-433's `w_omega` genuinely was.
    """
    off_rows, on_rows = arms
    off_h = np.array([r.heading_rms for r in off_rows])
    on_h = np.array([r.heading_rms for r in on_rows])
    assert on_h.mean() < off_h.mean(), (
        f"mean did not improve: {off_h.mean():.4f} -> {on_h.mean():.4f}")
    # And it is genuinely partial — the obstacle-free scene converts 16/16.
    improved = int(((on_h - off_h) < 0).sum())
    assert 0 < improved < 16, f"expected a split, got {improved}/16"


def test_the_two_proxies_disagree_in_sign(arms):
    """Detour and clearance point opposite ways — and both arms agree on that.

    `ArmCorrelation.proxies_agree` is False here, deliberately surfaced rather
    than resolved. Reported because the verdict string keys on |rho| and would
    otherwise hide it.
    """
    off_rows, on_rows = arms
    off = ap.correlate(off_rows, 0.0, n_perm=PERM)
    on = ap.correlate(on_rows, 32.0, n_perm=PERM)

    assert off.rho_detour > 0 and on.rho_detour > 0
    assert off.rho_clearance < 0 and on.rho_clearance < 0
    assert not off.proxies_agree and not on.proxies_agree


def test_deviation_does_not_buy_clearance(arms):
    """The premise correction: detour and clearance are *anti*-correlated.

    Q-181/Q-185 both phrased the residual as "the price of avoidance", which
    presumes the deviation buys clearance. On this scene it does not — the
    seeds that leave the path most are the ones that pass closest. Pinned
    because it changes what the repair should be, and because it is the one
    number here that neither question asked for.

    Measured: rho = -0.550 (p = 0.030) unpriced, -0.526 (p = 0.040) priced.
    """
    for rows, label in zip(arms, ("w_heading=0", "w_heading=32")):
        d = np.array([r.detour for r in rows])
        c = np.array([r.clearance for r in rows])
        rho = ap.spearman(d, c)
        assert rho < -0.3, (
            f"{label}: detour vs clearance rho={rho:+.3f} — if this is now "
            "positive the deviation does buy clearance and the D-442 "
            "premise correction is stale")


# --- the statistics, checked against values that do not need a sim -------


def test_spearman_matches_hand_computable_cases():
    x = np.arange(8, dtype=float)
    assert ap.spearman(x, 2.0 * x + 1.0) == pytest.approx(1.0)
    assert ap.spearman(x, -x) == pytest.approx(-1.0)
    # Monotone but wildly non-linear: rank correlation is blind to the shape,
    # which is why it is the statistic here and Pearson is not.
    assert ap.spearman(x, np.exp(x)) == pytest.approx(1.0)
    assert np.isnan(ap.spearman(x, np.ones(8)))


def test_ties_share_a_rank():
    """Competition ranking would order equal clearances by seed index."""
    r = ap._rank(np.array([1.0, 2.0, 2.0, 5.0]))
    np.testing.assert_allclose(r, [1.0, 2.5, 2.5, 4.0])
    # A tied vector correlates perfectly with itself under average ranks;
    # under competition ranking it would depend on the input order.
    v = np.array([3.0, 1.0, 3.0, 1.0])
    assert ap.spearman(v, v) == pytest.approx(1.0)


def test_permutation_p_is_add_one_corrected_and_reproducible():
    x = np.arange(16, dtype=float)
    p_perfect = ap.permutation_p(x, x, n_perm=500, seed=0)
    assert p_perfect == pytest.approx(1.0 / 501.0), "never report p = 0"

    # Same seed, same number — a p that redraws is not a number to quote.
    rng_a = ap.permutation_p(x, x[::-1] + np.arange(16) % 3, n_perm=500, seed=1)
    rng_b = ap.permutation_p(x, x[::-1] + np.arange(16) % 3, n_perm=500, seed=1)
    assert rng_a == rng_b

    # Pure noise should not look significant.
    y = np.random.default_rng(7).normal(size=16)
    assert ap.permutation_p(x, y, n_perm=2000, seed=0) > 0.05


def test_detour_of_the_reference_path_is_one():
    """Driving the polyline exactly scores 1.0, not 1.0-plus-discretisation."""
    wp = np.array([[0.0, 0.0], [3.0, 0.0], [3.0, 4.0]])
    pts = np.array([[0.0, 0.0], [1.5, 0.0], [3.0, 0.0], [3.0, 2.0], [3.0, 4.0]])
    traj = np.column_stack([np.arange(len(pts)) * 0.1, pts,
                            np.zeros(len(pts))])
    assert ap._detour(traj, wp) == pytest.approx(1.0)


def test_loosened_reads_magnitude_not_sign():
    """A sign flip at low |rho| is noise wearing a direction."""
    def arm(rc, rd):
        return ap.ArmCorrelation(w_heading=0.0, n=16, heading_mean=0.1,
                                 rho_clearance=rc, p_clearance=0.5,
                                 rho_detour=rd, p_detour=0.5)
    # -0.9 -> +0.9 is a sign flip and *not* a loosening.
    assert not ap.loosened(arm(0.0, -0.9), arm(0.0, 0.9), proxy="detour")
    assert ap.loosened(arm(0.0, -0.9), arm(0.0, 0.2), proxy="detour")


def test_verdict_names_a_proxy_split_instead_of_picking_one():
    def arm(rc, rd):
        return ap.ArmCorrelation(w_heading=0.0, n=16, heading_mean=0.1,
                                 rho_clearance=rc, p_clearance=0.5,
                                 rho_detour=rd, p_detour=0.5)
    # clearance loosens, detour holds -> the split must surface.
    v = ap.verdict(arm(0.9, 0.5), arm(0.2, 0.9))
    assert v.startswith("Q-185 SPLIT"), v

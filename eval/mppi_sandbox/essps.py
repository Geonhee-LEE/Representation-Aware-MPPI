# SPDX-License-Identifier: BSD-3-Clause
"""Does an ESS-targeted `lam` exist for `cafe_freezing_v0` — and does it help?

The feed lead (Watson & Peters, `2210.03512`, CoRL 2022) proposes **ESSPS**:
pick the likelihood temperature by solving ``arg min_a |N_a - N*|`` for a target
effective sample size, a gradient-free 1-D solve. The quantity that ports is
the *fraction* ``phi = 10/32`` rather than the constant, because ESS is a
function of the **normalized** weights and is therefore cost-scale-invariant.
(The paper's other rule, LBPS, includes a ``||R||_inf`` term and is *not*
scale-invariant; only ESSPS is borrowed here.)

Why the branch wanted it
------------------------
D-273 established that every shipped `lam` window was measured at ``w_voo = 0``,
so no rung of this ladder sits in the cost field its calibration ran in. Making
a window binding means one table per `w_voo` value (Q-155), and each new axis
multiplies the calibration matrix. A *solved* `lam` would need no table at all
— the only option that deletes the multiplication rather than paying it.

The question asked, and the answer
----------------------------------
**Does such a `lam` exist here at all?** The TODO expected a "no" to be the
stronger result — it would have made `ess_at_peak`'s `ESS_DEGENERATE_THROUGHOUT`
a property of the scene's cost landscape rather than of the temperature.

It is a **yes, at every step, and the yes is uninteresting.** ESS is monotone
increasing in `lam` for any fixed cost vector — ``1`` as ``lam -> 0`` (softmax
becomes argmin), ``K`` as ``lam -> inf`` (weights become uniform) — so a target
anywhere in ``(1, K)`` is hit by exactly one `lam`, and a root-find always
succeeds. Existence was never the discriminating question; :data:`SOLVED_LAM`
records a solve at **115 of 115** steps.

What the measurement actually settles
-------------------------------------
The load-bearing reading is the *spread*, not the existence. Across one episode
at the operating point the per-step solved `lam` moves **47.6x** (``0.428`` to
``20.36``, median ``1.479``). A single scalar cannot sit where a quantity that
moves 47x needs to be, and the consequence is measured rather than argued:

- Matching the **median** ESS to the target picks ``lam = 1.488``, which holds
  the Q-026 band on **57 of 115** steps.
- The **compliance-optimal** fixed `lam` is ``0.787`` — holding on **69 of 115**
  — and that is the shipped operating point ``0.8`` to within 1.6%.

So a per-scene ESSPS scalar is **dominated by the table it was meant to
replace**, and the calibrated window's top rung is already (to 1.6%) the best
constant temperature this scene admits. The comparison is run against the
compliance-optimal constant on purpose: matching the median is ESSPS's own
objective, and beating a strawman constant would have proven nothing.

The reason is distributional. Per-step ESS at a fixed `lam` is skewed, so
matching the median pushes the upper tail through the ceiling (max ``182.03``
against a ceiling of ``128.0``) while the lower tail is still under the floor.
Even at the optimum, **44 of 115** steps sit below the floor and 2 above the
ceiling: *no* constant temperature holds this band through the episode.

What this does and does not license
-----------------------------------
It does **not** retire ESSPS. It retires **ESSPS-as-a-per-scene-constant**,
which is the only form that would have removed the table. The paper solves the
temperature **per iteration**, and that is a live option — but it is a change to
the controller's inner loop, not a calibration artifact, and it would re-date
every `lam`-conditioned number this branch has recorded. That cost is Q-155's to
price, and this module deliberately stops short of paying it.

Scope: one scene, one seed, one episode (115 steps), at the operating point
``(lam = 0.8, w_voo = 5)`` in `ess_at_peak.ISOLATION`. The harvested run
reproduces D-270's recorded median ESS ``31.2344`` to 4 decimals, which is the
provenance check that this cost stream is the one the branch has been reading.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.optimize import brentq

from .ab import ess_band
from .ess_at_peak import ISOLATION, PEAK_SCENE

#: Watson & Peters' target, kept as a **fraction** of `K`. The paper's `N* = 10`
#: at `K = 32` is not portable as a constant; the fraction is, because ESS
#: depends only on the normalized weights. At `K = 256` this is `80.0`, which
#: sits inside `ab.ess_band(256) == (12.8, 128.0)` — so the target is not
#: trivially unreachable by construction.
TARGET_FRACTION: float = 10.0 / 32.0

#: The operating point the cost stream was harvested at (D-270/D-271).
OPERATING_LAM: float = 0.8
OPERATING_W_VOO: float = 5.0

#: Bracket for the root-find, in `lam`. Wide enough that the monotone ESS curve
#: spans `(1, K)` across it for any cost vector this sandbox produces; the solve
#: reports `None` rather than clipping if a target somehow falls outside.
LAM_BRACKET: tuple[float, float] = (1e-4, 1e6)

#: Median per-step ESS logged by the harvested run, against D-270's recorded
#: `31.2344` for the same cell. Equality to 4 dp is the provenance check that
#: this module reads the same cost stream the rest of the branch does.
HARVEST_MEDIAN_ESS: float = 31.2344

#: Per-step solved `lam` over the harvested episode: `(n_steps, n_solved,
#: min, p50, max)`. Recorded rather than recomputed on import — the harvest is
#: a ~13 s closed-loop run and the *shape* is the finding, not the reproduction.
SOLVED_LAM: tuple[int, int, float, float, float] = (115, 115, 0.4281, 1.4786, 20.3615)

#: `(lam, steps_in_band, n_steps, median_ess)` for the two constant temperatures
#: the finding compares. `MEDIAN_MATCHED` is ESSPS's own objective applied
#: per-scene; `COMPLIANCE_OPTIMAL` is the best constant available on the band
#: criterion, found by sweeping — the control that makes the comparison fair.
MEDIAN_MATCHED: tuple[float, int, int, float] = (1.4882, 57, 115, 80.32)
COMPLIANCE_OPTIMAL: tuple[float, int, int, float] = (0.7870, 69, 115, 30.31)

#: Steps below floor / above ceiling at :data:`COMPLIANCE_OPTIMAL`. Both nonzero
#: is the statement that no constant holds the band on this scene.
OPTIMAL_OUT_OF_BAND: tuple[int, int] = (44, 2)


def ess_of(costs, lam: float) -> float:
    """Effective sample size of the MPPI softmax at temperature `lam`.

    Mirrors `StockMPPI.command`'s weighting exactly — ``exp(-(cost - min)/lam)``,
    normalized, then ``1/sum(w^2)``. It is restated here because this module
    needs ESS as a *function of `lam`* and the controller only ever evaluates it
    at its own; `tests/test_essps.py` pins the two equal at the controller's
    temperature so the pair cannot drift (D-047).
    """
    c = np.asarray(costs, dtype=float)
    w = np.exp(-(c - c.min()) / float(lam))
    w /= w.sum()
    return float(1.0 / np.square(w).sum())


def solve_lam_for_ess(costs, target: float | None = None, *,
                      bracket: tuple[float, float] = LAM_BRACKET) -> float | None:
    """ESSPS: the `lam` whose softmax over `costs` has ESS `target`.

    Returns `None` when the target lies outside the curve's reachable range on
    `bracket` — which for a non-degenerate cost vector means the caller asked
    for ESS outside ``(1, K)``, not that the scene refused.

    The paper minimizes ``|N_a - N*|`` with Brent. Because ESS is *strictly
    monotone* in `lam`, that objective has a unique zero and root-finding
    reaches the same point with better conditioning; the equivalence is pinned
    by `test_root_find_matches_paper_objective`. The solve runs in `log lam`
    since the reachable range spans decades.
    """
    c = np.asarray(costs, dtype=float)
    tgt = float(TARGET_FRACTION * c.size if target is None else target)
    f = lambda log_lam: ess_of(c, float(np.exp(log_lam))) - tgt
    lo, hi = float(np.log(bracket[0])), float(np.log(bracket[1]))
    if f(lo) > 0.0 or f(hi) < 0.0:
        return None
    return float(np.exp(brentq(f, lo, hi, xtol=1e-10)))


@dataclass(frozen=True)
class ScalarVerdict:
    """Whether a per-scene ESSPS constant can replace the calibrated window."""

    solved_steps: int
    n_steps: int
    lam_spread: float
    median_matched_in_band: int
    optimal_in_band: int
    optimal_lam: float

    @property
    def exists(self) -> bool:
        """Did a target-ESS `lam` exist at every step? (Structurally, yes.)"""
        return self.solved_steps == self.n_steps

    @property
    def beats_constant(self) -> bool:
        """Does the ESSPS scalar beat the best constant on band compliance?"""
        return self.median_matched_in_band > self.optimal_in_band

    @property
    def any_constant_holds(self) -> bool:
        """Does *some* constant hold the band at every step?"""
        return self.optimal_in_band == self.n_steps


def verdict() -> dict:
    """Grade the recorded measurement.

    Reports existence and usefulness **separately**: they answer different
    questions and the pair is the finding. Collapsing them into one flag would
    report the structural `yes` as if it were a win.
    """
    n_steps, solved, lam_lo, lam_med, lam_hi = SOLVED_LAM
    mm_lam, mm_band, _, mm_med = MEDIAN_MATCHED
    co_lam, co_band, _, co_med = COMPLIANCE_OPTIMAL
    v = ScalarVerdict(
        solved_steps=solved, n_steps=n_steps, lam_spread=lam_hi / lam_lo,
        median_matched_in_band=mm_band, optimal_in_band=co_band,
        optimal_lam=co_lam,
    )

    if not v.exists:
        name = "NO_TARGET_LAM"          # the result the TODO expected
    elif v.beats_constant:
        name = "SCALAR_ESSPS_WINS"
    elif v.any_constant_holds:
        name = "CONSTANT_SUFFICES"
    else:
        # A target-ESS lam exists everywhere, the per-scene scalar is dominated
        # by the best constant, and no constant holds the band either. The
        # per-iteration solve is untouched by this and stays open.
        name = "SCALAR_ESSPS_DOMINATED"

    return {
        "verdict": name,
        "scene": PEAK_SCENE,
        "operating_point": {"lam": OPERATING_LAM, "w_voo": OPERATING_W_VOO},
        "target_ess": TARGET_FRACTION * 256,
        "band": ess_band(256),
        "solved_at": f"{solved}/{n_steps} steps",
        "lam_spread": round(v.lam_spread, 2),
        "lam_median": lam_med,
        "median_matched": {"lam": mm_lam, "in_band": f"{mm_band}/{n_steps}",
                           "median_ess": mm_med},
        "compliance_optimal": {"lam": co_lam, "in_band": f"{co_band}/{n_steps}",
                               "median_ess": co_med},
        # 0.787 vs the shipped 0.8 — the window's top rung is already the best
        # constant this scene admits.
        "optimal_matches_shipped_rung": abs(co_lam - OPERATING_LAM) / OPERATING_LAM < 0.02,
        "below_floor_at_optimal": OPTIMAL_OUT_OF_BAND[0],
        "above_ceiling_at_optimal": OPTIMAL_OUT_OF_BAND[1],
        # What is retired and what is not.
        "retires_per_scene_essps_constant": True,
        "retires_per_iteration_essps": False,
        "removes_lam_window_table": False,
        "scope": "one scene, one seed, one episode; not transferred (D-266)",
    }


def harvest_costs(scenario, *, seed: int = 0, lam: float = OPERATING_LAM,
                  w_voo: float = OPERATING_W_VOO):
    """Capture the per-step rollout cost vectors of one closed-loop run.

    On-demand (~13 s), not called by any test — the recorded constants above are
    what the suite checks, following `ess_at_peak.MEASURED_ESS`'s precedent.
    Returns `(costs (T,K), median_ess)`.
    """
    from .controllers import make_controller
    from .controllers.stock_mppi import MPPIParams
    from .run import ROBOT_RADIUS, simulate

    ctrl = make_controller("risk_mppi", scenario, seed=seed,
                           robot_radius=ROBOT_RADIUS,
                           params=MPPIParams(lam=lam), w_voo=w_voo,
                           w_epist=0.0, **ISOLATION)
    captured: list[np.ndarray] = []
    inner = ctrl._cost

    def capture(traj, t0):
        c = inner(traj, t0)
        captured.append(np.asarray(c, dtype=float).copy())
        return c

    ctrl._cost = capture
    simulate(scenario, ctrl)
    return np.array(captured), float(np.median(ctrl.ess_log))

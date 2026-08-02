# SPDX-License-Identifier: BSD-3-Clause
"""Is the rollout horizon a knob you may sweep? — and the leave-one-out blind
spot that answering it exposed.

Why this exists
---------------
Q-043 asked whether to pick scenes whose shadows fall inside the rollout cone,
or to **change the planner so they do**. D-027 answered the first half by
changing the cost's *construction*, and left the obvious second half open: make
the cone longer. STATE item #1 accordingly specified a `(w_voo, horizon)` 2×2 —
the epistemic weight crossed with the rollout horizon — at a scale-matched
weight, `lam ∈ {1.6, 3.2}`, ratio ≤ 0.25 (D-029).

That 2×2 cannot be run, and the reason has nothing to do with `w_voo`. On
`cafe_obstacle_crossing_v0` / `risk_mppi` at `lam = 1.6`, the **baseline** arm —
`w_voo = 0`, every other weight shipped — stops driving between `H = 34` and
`H = 35` (n = 2, `cruise_speed`, full timeout):

=====  =============  ==========  ==============  ===========
`H`    median steps   cruise      mean clearance  reached?
=====  =============  ==========  ==============  ===========
15     101            0.8000      +0.0888         yes
30     102            0.7998      +0.0709         yes
34     102            0.7723      +0.0193         yes
**35** **960**        **0.1135**  **+0.2429**     **yes**
38     1001           0.1374      +0.2049         yes
45     899            0.1331      +0.2214         yes
60     576            0.1349      +0.3585         yes
=====  =============  ==========  ==============  ===========

A **6.8×** cruise collapse across a single step of `H`, sustained to 2× the
shipped horizon, and a real edge rather than a threshold artefact: `H = 34`
still holds **96.6 %** of the shipped rung's cruise. So the horizon axis has
exactly one admissible rung on this scene and the 2×2 degenerates to the 1×2
D-027 already ran. Q-043's "lengthen the cone" branch is refuted at the
*baseline*, before any epistemic term is involved — a cheaper refutation than
it would have been had the 2×2 been run naively and its horizon column read as
a `w_voo` result.

Even had the baseline held, the 2×2's own weight axis does not survive the
horizon axis. Almost every term in `_cost` is a **sum over H**, so
`scale_match.exchange_rate` (now horizon-aware) reads, same scene and `lam`:

=====  ============  ==========  =====================
`H`    `per_unit`    `rest`      `w_voo` at ratio 0.25
=====  ============  ==========  =====================
15     0.775         21.70       7.00
30     2.356         101.21      10.74
34     2.929         163.64      13.97
=====  ============  ==========  =====================

**2.0× of scale-matched weight over a 2.3× horizon change** — the same order as
the 2.11× `lam` swing D-029 called a fixed point. A `(w_voo, horizon)` 2×2 that
holds `w_voo` fixed down its horizon column is therefore not crossing two
factors; it is confounding a weight change with a horizon change.

Two traps this measurement walks into, both already named in this repo
-----------------------------------------------------------------------
1. **`all_reached` is True in every row above, frozen ones included.** Completion
   is not the guard here — the frozen arm does finish, it just takes 9× as long.
   Only `speed_audit.cruise_speed` separates the rows, which is D-025's point
   arriving a second time and D-026's `city_figure8_v0` (0.016 m/s, "reached")
   in a scene that is otherwise healthy.
2. **The clearance column improves monotonically through the collapse** (0.019 →
   0.386, **20×**). Read without the cruise column it says a longer horizon is
   safer. It is the freeze-buys-berth confound `ab`'s speed control exists for,
   and the horizon axis is the one axis a `v_max` handicap **cannot** control:
   handicapping only lowers a speed limit, and the frozen arm is slow by
   *choice*, not by limit. There is no way to run the two horizons at matched
   speed, so the axis is not merely inconvenient — it is unidentifiable.

The finding worth carrying: leave-one-out cannot see a redundant cause
----------------------------------------------------------------------
Attributing the collapse by intervention (D-026's lesson — rank the mechanism
by ablation, not by reading the cost function) gives, at `H = 45`, seeds 0–1:

=============================  ==============  ==========  ==========
arm                            median steps    cruise      clearance
=============================  ==============  ==========  ==========
intact (`H = 45`)              899             0.1331      +0.2214
`w_collision = 0`              830             0.1287      +0.2516
`w_obs_soft = 0`               864             0.1201      +0.1934
**both zero**                  **116**         **0.7479**  **−0.0907**
=============================  ==============  ==========  ==========

**Neither obstacle term causes the freeze. Both do.** Removing either one alone
leaves cruise at 0.90–0.97× the intact arm — not merely a small improvement but
*no* improvement; removing the pair restores it **5.6×**, back to the healthy
0.75–0.80 band. (The pair-ablated arm then collides, which is the other half of
the sentence: the freeze is buying real safety, badly.) The two terms are
**substitutes** — each is independently sufficient to make standing still the
cheapest plan at this horizon, so knocking one out changes nothing because the
other still fires.

This is a direct limitation of `weight_units.measure`, D-028's instrument: it is
leave-**one**-out by construction (`cost(w) − cost(0)` per weight, one at a
time), so its table would credit each of these two terms with ≈ 0 responsibility
for a behaviour they jointly and entirely determine. LOO answers "what does this
weight add on the margin", never "what is this behaviour caused by", and the
gap between the two questions is exactly the size of the redundancy. `ablate`
below is the minimal repair: sweep the **power set** of a small group of
candidate terms, not the singletons.

And D-028's damage guard does not catch this
---------------------------------------------
`scale_match.check_undamaged` compares the probe run's length to the *baseline
arm's* length. At `H = 45` both arms are frozen equally, so it reads
`damage = 0.69` — comfortably "undamaged" — on an arm that is not driving at
all. Worse, the number it then certifies is wrong in the flattering direction:
a frozen robot presents a flat landscape, so `rest` **falls** 163.6 → 38.8 from
`H = 34` to `H = 45`, and the scale-matched weight it prescribes (4.27) is 3.3×
smaller than the one for the last healthy rung. The guard is *relative*; it
cannot see that its own reference is broken. `cruise_ceiling` is the missing
absolute precondition — check the baseline is driving before pricing anything
against it.

Cost
----
`scan` is one closed-loop run per (horizon, seed); frozen rungs are the
expensive ones (~15 s each at the full timeout), which is what `max_steps`
is for — a driving-vs-frozen verdict is legible at ~1.5× the healthy run
length, and the truncated ablation returns the *identical* `redundant_sets`
verdict at ~5× less cost (both were run). `ablate` over `g` groups is `2**g`
runs per seed; keep `g ≤ 3`.

`test_horizon_audit.py` nonetheless costs **~122 s**, and the trimming that is
available without weakening a claim only bought 15 s of that. The floor is the
three measurements that *must* run untruncated, because truncating them would
destroy the thing they assert: the frozen arm still reaching the goal, and the
two exchange rates at the frozen rung. That is a real addition to a suite
already at 504 s, and it is an argument for a `slow` marker — not for deleting
the evidence behind D-030.
"""

from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations
from typing import Iterable, Mapping, Sequence

import numpy as np

from . import speed_audit
from .ab import ArmRun, seed_sweep, summarize
from .controllers.stock_mppi import MPPIParams
from .scenario import Scenario

#: The horizon every recorded sandbox result was measured at.
SHIPPED_HORIZON = MPPIParams().horizon

#: Cruise fraction of the shipped-horizon arm below which a rung is "frozen".
#: The observed gap is 12×, so any threshold in (0.1, 0.9) picks the same
#: ceiling on this scene — 0.5 is chosen to be unremarkable rather than tuned,
#: and `cruise_ceiling` reports the margin so a borderline scene is visible.
FROZEN_BELOW = 0.5

#: Enough steps to tell a driving arm from a frozen one on the shipped scenes,
#: whose healthy runs are ~100 steps. A frozen arm needs > 800; anything that
#: has not finished by here is not driving at the baseline's pace.
VERDICT_STEPS = 160


@dataclass(frozen=True)
class HorizonRow:
    """One rung of a horizon scan. `cruise` is the column that separates them."""

    horizon: int
    n_seeds: int
    median_steps: float
    cruise: float
    mean_clearance: float
    all_reached: bool
    median_ess: float
    truncated: bool

    @property
    def stalled(self) -> bool:
        """`cruise_speed` returns NaN for an arm that never leaves the
        transient — a stall, which is a stronger statement than slow."""
        return not np.isfinite(self.cruise)

    def __str__(self) -> str:
        return (f"H={self.horizon:3d} steps={self.median_steps:6.0f} "
                f"cruise={self.cruise:.4f} clear={self.mean_clearance:+.4f} "
                f"reached={self.all_reached}"
                + (" [truncated]" if self.truncated else ""))


def _cruise(runs: Sequence[ArmRun], scenario: Scenario) -> float:
    """Median per-seed cruise speed. NaN seeds propagate as NaN (a stalled seed
    has no cruise and must not be averaged away — D-025)."""
    return float(np.median([speed_audit.cruise_speed(r.traj, scenario)
                            for r in runs]))


def _row(scenario: Scenario, runs: Sequence[ArmRun], horizon: int,
         max_steps: int | None) -> HorizonRow:
    st = summarize(runs)
    steps = [len(r.traj) for r in runs]
    return HorizonRow(
        horizon=horizon,
        n_seeds=st.n,
        median_steps=float(np.median(steps)),
        cruise=_cruise(runs, scenario),
        mean_clearance=st.mean_clearance,
        all_reached=st.all_reached,
        median_ess=st.median_ess,
        truncated=max_steps is not None and max(steps) >= max_steps,
    )


def scan(scenario: Scenario, controller: str = "risk_mppi", *,
         horizons: Iterable[int] = (SHIPPED_HORIZON, 2 * SHIPPED_HORIZON),
         seeds: Iterable[int] = range(2),
         lam: float = 1.6,
         max_steps: int | None = None,
         **arm_kwargs) -> list[HorizonRow]:
    """Closed-loop behaviour vs rollout horizon, one row per rung.

    `lam` is explicit and defaults to an *admissible* temperature rather than
    the shipped 0.1: at 0.1 every arm this repo has measured sits below the ESS
    floor, so a horizon effect measured there could not be told from a sampler
    that was not weighting. D-029's window for this scene is [1.6, 3.2].
    """
    seeds = list(seeds)
    return [_row(scenario,
                 seed_sweep(scenario, controller, seeds, max_steps=max_steps,
                            params=MPPIParams(lam=lam, horizon=int(H)),
                            **arm_kwargs),
                 int(H), max_steps)
            for H in horizons]


def cruise_ceiling(rows: Sequence[HorizonRow], *,
                   reference: int = SHIPPED_HORIZON,
                   frozen_below: float = FROZEN_BELOW) -> tuple[int, float]:
    """`(largest sweepable horizon, margin)` — the answer to "may I sweep H?".

    Walks *upward* from `reference` and stops at the first rung whose cruise
    falls below `frozen_below ×` the reference rung's. Contiguity is deliberate:
    a rung above a frozen one that happens to read fast again is not evidence
    the axis is sweepable, it is evidence the axis is non-monotone, and either
    way the arms on both sides of a freeze are not comparable.

    `margin` is the ceiling rung's cruise as a fraction of the reference — a
    value near 1 means the ceiling is a real edge, near `frozen_below` means
    the scene is borderline and the threshold is doing the work.
    """
    by_h = {r.horizon: r for r in sorted(rows, key=lambda r: r.horizon)}
    if reference not in by_h:
        raise KeyError(f"scan has no reference rung H={reference} to normalize "
                       f"against — got {sorted(by_h)}")
    ref = by_h[reference].cruise
    if not np.isfinite(ref) or ref <= 0.0:
        raise ValueError(f"reference rung H={reference} is itself stalled "
                         f"(cruise={ref}) — nothing to normalize against")
    ceiling, margin = reference, 1.0
    for h in sorted(by_h):
        if h <= reference:
            continue
        frac = by_h[h].cruise / ref
        if not np.isfinite(frac) or frac < frozen_below:
            break
        ceiling, margin = h, float(frac)
    return ceiling, float(margin)


def ablate(scenario: Scenario, controller: str = "risk_mppi", *,
           groups: Mapping[str, Mapping[str, float]],
           horizon: int,
           seeds: Iterable[int] = range(2),
           lam: float = 1.6,
           max_steps: int | None = VERDICT_STEPS,
           **arm_kwargs) -> dict[frozenset[str], HorizonRow]:
    """Power-set ablation — the repair for leave-one-out's redundancy blind spot.

    `groups` maps a label to the parameter overrides that *disable* it, e.g.
    ``{"collision": {"w_collision": 0.0}, "barrier": {"w_obs_soft": 0.0}}``.
    Every subset is run, including the empty one (the intact arm), so a cause
    carried redundantly by two members is visible as "neither singleton moves
    the behaviour, the pair does" — the pattern `weight_units.measure` cannot
    represent, since it varies exactly one weight at a time.

    `2**len(groups)` runs per seed; `groups` is meant to be a short list of
    *suspects*, produced by reading the cost function, and then adjudicated
    here. Defaults to a truncated run because the question is behavioural.
    """
    seeds = list(seeds)
    out: dict[frozenset[str], HorizonRow] = {}
    names = list(groups)
    for k in range(len(names) + 1):
        for combo in combinations(names, k):
            over: dict[str, float] = {}
            for name in combo:
                over.update(groups[name])
            runs = seed_sweep(scenario, controller, seeds, max_steps=max_steps,
                              params=MPPIParams(lam=lam, horizon=int(horizon),
                                                **over),
                              **arm_kwargs)
            out[frozenset(combo)] = _row(scenario, runs, int(horizon), max_steps)
    return out


def redundant_sets(table: Mapping[frozenset[str], HorizonRow], *,
                   restored: float = 2.0) -> list[frozenset[str]]:
    """Subsets that restore cruise while **no proper subset** of them does.

    "Restore" = cruise ≥ `restored` × the intact arm's. A returned set of size
    ≥ 2 is a redundant cause: its members are individually inert and jointly
    decisive, so any leave-one-out attribution of this behaviour is wrong by
    construction rather than by imprecision.
    """
    intact = table.get(frozenset())
    if intact is None:
        raise KeyError("ablation table has no intact arm (the empty subset)")
    base = intact.cruise
    if not np.isfinite(base) or base <= 0.0:
        raise ValueError(f"intact arm is stalled (cruise={base}) — a ratio "
                         f"against it is not a measurement")

    def _restores(s: frozenset[str]) -> bool:
        row = table.get(s)
        return (row is not None and np.isfinite(row.cruise)
                and row.cruise >= restored * base)

    hits = [s for s in table if s and _restores(s)]
    return sorted(
        (s for s in hits
         if not any(p < s and _restores(p) for p in hits)),
        key=lambda s: (len(s), sorted(s)))


def format_scan(rows: Sequence[HorizonRow]) -> str:
    """Markdown, with cruise and clearance adjacent — they move in *opposite*
    directions through a freeze, and a table that shows only one of them
    supports the wrong conclusion."""
    head = ["| `H` | median steps | cruise | mean clearance | all reached |",
            "|---|---|---|---|---|"]
    return "\n".join(head + [
        f"| {r.horizon} | {r.median_steps:.0f} | {r.cruise:.4f} | "
        f"{r.mean_clearance:+.4f} | {r.all_reached} |"
        for r in sorted(rows, key=lambda r: r.horizon)])

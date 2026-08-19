# SPDX-License-Identifier: BSD-3-Clause
"""Is `cte_max` within-run-sample-limited? — no, and that keeps the expensive prong open.

`research/feed.md`'s 2026-08-20 00:00 entry (Krishnamachari `2605.00428`, §17)
supplied the cheapest hypothesis any cycle has offered against STATE's standing
fork. Verbatim from the paper: *"For tail metrics (p99), the relevant quantity
is the number of tail samples per run, not the number of runs. A run with too
few requests gives an unstable p99 no matter how many times it is repeated."*
`cte_max` is `float(np.max(np.abs(cte)))` — `eval/path_tracking_metrics.py:237`
— a per-run extreme order statistic, i.e. exactly that case, and it is the
column that fails while the mean-like `clearance` column clears on the *same*
eight runs. The feed drew the consequence: if `cte_max` is limited by the
within-run sample count, then **the 512 rollouts buy a `2.10x` smaller floor on
a quantity that will still be unreadable**, and the expensive prong of the fork
can be eliminated for free.

The feed also named the test, and named it as free: *"take the existing eight
runs, count CTE timesteps per run, and check whether `max|cte|` has stabilised
within a run."* This module runs it. **The hypothesis is refuted**, on the scene
that decides the fork, by the reading the feed itself proposed.

**Finding #1 — the running max is not still climbing. It has saturated by the
midpoint of every run, in all sixteen.** :data:`CENSUS` records
`half_max / cte_max` per cell, where `half_max` is the maximum over the first
half of the CTE series. The column is `1.0000` for **16 of 16** runs across both
scenes — every arm on both scenes attains its whole-run maximum *before* the
halfway point. `argmax` lands at fraction `0.068`–`0.410` of the run on
`cafe_convoy_v0` and `0.170`–`0.214` on `city_curved_v0`.

That is the paper's own test, answered in the negative. Doubling the within-run
sample count would not have moved `cte_max` in a single one of these runs,
because the max was already attained in the first half. Whatever makes this
column ungradeable, it is **not** a shortage of within-run samples — so the
prong stays open and the fork stays unresolved. The cheap way out is closed.

**Finding #2 — and the estimator-class story does not survive either, at the
place it was supposed to bite.** Split each series into even- and odd-indexed
timesteps and compare `max` on the two halves; that gap is the within-run
instability of the maximum, in the same metres as the arm spread a bar must
resolve. On `cafe_convoy_v0` — the scene supplying the excited minimum, and the
one whose `0.96x` failure the fork is about:

    arm spread (cte_max)         0.1187
    split-half gap, median       0.0006     ->  spread is 198x the instability
    split-half gap, worst arm    0.0018     ->  spread is  66x the instability

So on the failing scene the maximum is *stable* to within a fraction of a
percent of the quantity it is being asked to discriminate. The feed's framing —
that `clearance` and `cte_max` "differ in estimator class, not in scene
content" — predicts the opposite ordering, and :data:`CENSUS` does not show it.

**Finding #3 — the instability that does exist sits on the wrong scene.** The
same split-half gap on `city_curved_v0`, the *unexcited* control:

    arm spread (cte_max)         0.0569
    split-half gap, median       0.0093     ->  spread is  6.1x the instability
    split-half gap, worst arm    0.0277     ->  spread is  2.1x the instability

`city_curved_v0`'s maximum is **31x** less stable relative to its own arm spread
than `cafe_convoy_v0`'s (`65.9x` against `2.1x` on the worst arm; `197.8x`
against `6.1x` on the median). If a tail-sample argument applies anywhere in this
harness it applies to the scene nobody proposed to grade, not to the scene the
512 rollouts were priced for. :data:`TAIL_LIMITED` returns the scenes where the
worst-arm gap exceeds a tenth of the arm spread: `city_curved_v0` alone.

**Scope, stated before the numbers are used — and the first item is the one
that matters.**

* **Even/odd split-half understates instability on an autocorrelated series**,
  and a CTE trace is strongly autocorrelated: adjacent timesteps are nearly the
  same pose, so the two halves are close to duplicates by construction. This is
  the same autocorrelation the feed's 08-19 Islam entry warns inflated that
  paper's `p = 0.0016`. Findings #2/#3 are therefore **lower bounds** on the
  instability and must not be read as "the maximum is stable, full stop".
  Finding #1 carries no such caveat — `half_max / cte_max` is a statement about
  *where in the run* the max is attained, and autocorrelation cannot manufacture
  a `1.0000`. **The refutation rests on finding #1**; #2 and #3 corroborate it
  at a strength their own construction limits.
* Seed 0 only, both scenes, 8 arms — the same seed-0 scope
  :data:`excursion_tracking.SEED_SCOPE` has carried since D-363. This module
  does not pay that debt and does not claim to; it answers a *within-run*
  question, which is orthogonal to the across-seed one.
* Two scenes, not eight. They are the binding pair for the `1.97x` separation
  (:mod:`excursion_seed_width`'s reasoning): `cafe_convoy_v0` supplies the
  excited minimum and `city_curved_v0` the unexcited maximum. A third scene
  cannot move a min-vs-max comparison without first crossing one of these.
* `n` varies 6x across arms (122–674 steps) because arms terminate at different
  times. Finding #1 is a *within-run fraction*, so it is immune to that; the
  split-half gaps are not compared across arms for the same reason.

**What this does to the bottleneck.** It removes an option rather than adding
one. Before this reading the fork had a possible third exit — "the seed axis is
the wrong axis, so decline to buy" — which would have let the branch skip the
expensive decision on a technical argument. That exit is closed: the seed axis
is not disqualified by within-run sample starvation. The fork is still the two
prongs STATE names, and it is still not a question the executor can answer.

CLI:
    python -m eval.mppi_sandbox.tail_stability   # rc=1 on drift from CENSUS
"""

from __future__ import annotations

import sys

#: Scenes measured, in the role each plays in the `1.97x` separation.
SCENES: tuple[str, ...] = ("cafe_convoy_v0", "city_curved_v0")

#: Scene whose `cte_max` failure the 512-rollout fork is priced for.
DECIDING_SCENE = "cafe_convoy_v0"

#: `scene -> arm -> (n_steps, cte_max, half_max/cte_max, split_half_max_gap)`.
#:
#: Harvested 2026-08-20 via `simulate()` + `cross_track_error()` at seed 0,
#: `lam=0.8`, the same operating point :mod:`clearance_census` harvests at.
#: `half_max` is the max over `cte[: n // 2]`; the split-half gap is
#: `abs(max(cte[0::2]) - max(cte[1::2]))`. Re-derive with :func:`retake`.
CENSUS: dict[str, dict[str, tuple[int, float, float, float]]] = {
    "cafe_convoy_v0": {
        "cbf_mppi": (670, 0.0915, 1.0000, 0.0010),
        "essps_mppi": (213, 0.1572, 1.0000, 0.0000),
        "frozen_risk_mppi": (139, 0.1269, 1.0000, 0.0018),
        "gap_gated_mppi": (674, 0.1114, 1.0000, 0.0007),
        "geometric_mppi": (674, 0.1365, 1.0000, 0.0002),
        "risk_mppi": (139, 0.1269, 1.0000, 0.0018),
        "social_mppi": (122, 0.2102, 1.0000, 0.0005),
        "stock_mppi": (674, 0.1365, 1.0000, 0.0002),
    },
    "city_curved_v0": {
        "cbf_mppi": (342, 0.3284, 1.0000, 0.0093),
        "essps_mppi": (257, 0.3853, 1.0000, 0.0277),
        "frozen_risk_mppi": (342, 0.3284, 1.0000, 0.0093),
        "gap_gated_mppi": (342, 0.3284, 1.0000, 0.0093),
        "geometric_mppi": (342, 0.3284, 1.0000, 0.0093),
        "risk_mppi": (342, 0.3284, 1.0000, 0.0093),
        "social_mppi": (342, 0.3284, 1.0000, 0.0093),
        "stock_mppi": (342, 0.3284, 1.0000, 0.0093),
    },
}

#: Fraction of the arm spread the worst-arm split-half gap must exceed for a
#: scene to be called tail-limited. A tenth is deliberately generous: the
#: even/odd split understates instability (see scope), so a *lenient* threshold
#: that still returns the deciding scene as clean is the honest way to fail to
#: find the effect.
TAIL_LIMITED_FRACTION = 0.10

#: `half_max / cte_max` at or above which a run's maximum counts as attained in
#: the first half. Shared by :func:`saturated_by_midpoint` and the guard spelled
#: inline in :func:`drift`, which cannot call the helper without going `DERIVED`.
SATURATION_RATIO = 1.0


def saturated_by_midpoint(scene: str, census: dict | None = None) -> tuple[str, ...]:
    """Arms whose whole-run `cte_max` is already attained in the first half.

    `census` is threaded rather than closed over so that a caller whose own
    expression is read as a **guard** can name the registry at its call site.
    `predicate_depth.provenance_depth_exposure` flags exactly the shape this
    parameter avoids: a guard that reaches a hand-typed registry one same-module
    frame down is admitted by `_is_set_valued` (which follows the call) and then
    classified `DERIVED` by `_provenance` (which does not), so every `TYPED`
    screen — including the whole of `exemption_masking` — skips it silently.
    See `drift`, the one call site that must pass it explicitly.
    """
    return tuple(sorted(a for a, (_n, _mx, ratio, _g) in (census or CENSUS)[scene].items()
                        if ratio >= SATURATION_RATIO))


def arm_spread(scene: str) -> float:
    """Max-minus-min of `cte_max` across arms — what a bar must resolve."""
    col = [mx for _n, mx, _r, _g in CENSUS[scene].values()]
    return round(max(col) - min(col), 4)


def split_half_gap(scene: str) -> tuple[float, float]:
    """`(median, worst)` within-run split-half instability of the maximum."""
    gaps = sorted(g for _n, _mx, _r, g in CENSUS[scene].values())
    mid = len(gaps) // 2
    median = gaps[mid] if len(gaps) % 2 else (gaps[mid - 1] + gaps[mid]) / 2
    return round(median, 4), round(gaps[-1], 4)


def spread_over_instability(scene: str) -> tuple[float, float]:
    """`(vs median gap, vs worst gap)` — how many instabilities fit in a spread.

    Large ⇒ the maximum is stable relative to what it must discriminate, i.e.
    the tail-sample hypothesis does not bite on this scene.
    """
    spread = arm_spread(scene)
    median, worst = split_half_gap(scene)
    return (round(spread / median, 1) if median else float("inf"),
            round(spread / worst, 1) if worst else float("inf"))


def tail_limited() -> tuple[str, ...]:
    """Scenes where the maximum is plausibly within-run-sample-limited.

    The deciding scene's absence from this tuple is the module's finding.
    """
    return tuple(s for s in SCENES
                 if split_half_gap(s)[1] > TAIL_LIMITED_FRACTION * arm_spread(s))


def seed_axis_disqualified() -> bool:
    """Would the tail argument let the branch decline the 512 rollouts?

    False ⇒ the cheap exit from STATE's fork is closed and the expensive
    decision stands.
    """
    return DECIDING_SCENE in tail_limited()


def retake(*, seed: int = 0) -> dict[str, dict[str, tuple[int, float, float, float]]]:
    """Re-measure :data:`CENSUS` from source. Not called by tests (~90 s)."""
    import numpy as np

    from eval.path_tracking_metrics import cross_track_error

    from .clearance_census import ISOLATION, REGISTRY, takes_epistemic_kwargs
    from .controllers import make_controller
    from .controllers.stock_mppi import MPPIParams
    from .essps import OPERATING_LAM, OPERATING_W_VOO
    from .run import ROBOT_RADIUS, simulate
    from .scenario import load_scenario

    out: dict[str, dict[str, tuple[int, float, float, float]]] = {}
    for scene in SCENES:
        sc = load_scenario(f"eval/scenarios/{scene}.yaml")
        path = np.asarray(sc.waypoints, dtype=float)
        out[scene] = {}
        for name in sorted(REGISTRY):
            kw = dict(w_voo=OPERATING_W_VOO, w_epist=0.0, **ISOLATION) \
                if takes_epistemic_kwargs(name, sc) else {}
            ctrl = make_controller(name, sc, seed=seed, robot_radius=ROBOT_RADIUS,
                                   params=MPPIParams(lam=OPERATING_LAM), **kw)
            cte = np.abs(cross_track_error(simulate(sc, ctrl), path))
            out[scene][name] = (
                int(cte.size),
                round(float(cte.max()), 4),
                round(float(cte[: cte.size // 2].max() / cte.max()), 4),
                round(float(abs(cte[0::2].max() - cte[1::2].max())), 4),
            )
    return out


def drift() -> tuple[str, ...]:
    """Internal-consistency read: the prose's claims against :data:`CENSUS`."""
    bad: list[str] = []
    for scene in SCENES:
        if scene not in CENSUS:
            bad.append(f"{scene}: absent from CENSUS")
            continue
        # Counted, not spelled as a second `not in`. The obvious phrasing —
        # `[a for a in CENSUS[scene] if a not in saturated_by_midpoint(scene)]` —
        # is read as a **guard exemption**, and it reaches its registry one
        # same-module frame down, which `_provenance` classifies `DERIVED` while
        # `_is_set_valued` still admits it. That combination is exactly
        # `predicate_depth.provenance_depth_exposure`, and it silently drops the
        # guard from every `TYPED` screen (`bite`, `unwatched_exemptions`, all of
        # `exemption_masking`). Inlining the set against `CENSUS` fixes the
        # provenance but adds a *second* typed exemption on the same constant,
        # and `exemption_masking.routes` keys on (guard, constant) — so `typed`
        # outgrows `routes` and the screen's own population pin goes red. A count
        # comparison is not an exemption at all, so `drift` keeps exactly one
        # (`scene not in CENSUS` above) and the two censuses agree.
        n_late = len(CENSUS[scene]) - len(saturated_by_midpoint(scene, CENSUS))
        if n_late:
            bad.append(f"{scene}: {n_late} arms not saturated by midpoint")
    if seed_axis_disqualified():
        bad.append(f"{DECIDING_SCENE}: now tail-limited — finding #1 inverted")
    if tail_limited() != ("city_curved_v0",):
        bad.append(f"tail_limited() = {tail_limited()} != ('city_curved_v0',)")
    return tuple(bad)


def format_census() -> str:
    """One-screen reading, for a human looking at the cycle's output."""
    lines = ["tail_stability — is cte_max within-run-sample-limited? seed 0, lam=0.8", ""]
    for scene in SCENES:
        med, worst = split_half_gap(scene)
        vs_med, vs_worst = spread_over_instability(scene)
        role = "  <- deciding scene" if scene == DECIDING_SCENE else ""
        lines += [
            f"{scene}{role}",
            f"    saturated by midpoint   {len(saturated_by_midpoint(scene))}"
            f"/{len(CENSUS[scene])} arms",
            f"    arm spread (cte_max)    {arm_spread(scene):.4f}",
            f"    split-half gap          median {med:.4f}   worst {worst:.4f}",
            f"    spread / instability    {vs_med:.1f}x (median)   {vs_worst:.1f}x (worst)",
            "",
        ]
    lines += [
        f"tail-limited scenes:     {tail_limited() or '(none)'}",
        f"seed axis disqualified:  {seed_axis_disqualified()} "
        f"-- False ⇒ the cheap exit from the fork is closed",
    ]
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    print(format_census())
    bad = drift()
    if bad:
        print("\nDRIFT:", file=sys.stderr)
        for line in bad:
            print(f"  {line}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

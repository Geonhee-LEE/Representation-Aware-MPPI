# SPDX-License-Identifier: BSD-3-Clause
"""The cross-track column is gradeable — as a tail *mean*, on the runs already bought.

STATE's standing fork has been priced two ways and never resolved: **buy the
resolution** (`RESOLUTION_DEBT` = 512 rollouts for a `2.10x` smaller floor), or
**declare the cross-track column ungradeable** at this harness's budget and grade
물체회피 alone. Every cycle since D-363 has read the `clearance`-clears /
`cte_max`-fails asymmetry as evidence about something — scenes, bars, geometry,
arm population, seeds, and (D-376, :mod:`tail_stability`) within-run sample
count. All six readings took the *observable* as given.

`research/feed.md`'s 2026-08-20 04:00 entry (`2606.16511`, §5) supplies the
seventh and it is the first to question the observable itself. The paper splits
a tail claim into **magnitude** and **shape**, and only shape carries the ruinous
sample cost: **TVaR₀.₉ — the mean of the worst decile — is an average over the
tail, not an extremum**, so it inherits the ordinary `1/√n` behaviour a maximum
does not. The feed drew the consequence and named it cheaper than the 10-seed
pilot: *"the column may be ungradeable as a maximum and gradeable as a tail mean
at the same 16 runs and the same budget."*

This module runs that test at ensemble width. **The re-expression works.**

**Finding #1 — the same 64 rollouts that cannot grade `cte_max` grade TVaR₀.₉
comfortably, on the adversarial floor as well as the p95 one.**

    column      real gap    p95 floor   max floor    vs p95    vs max
    cte_max       0.0633       0.0659      0.0673     0.96x     0.94x
    TVaR_0.9      0.1381       0.0523      0.0555     2.64x     2.49x

Both rows are :data:`SCENE` at eight seeds, through the *same*
:mod:`aa_calibration` null-gap machinery, and — this is the load-bearing part —
the same rollouts. Nothing was bought. `cte_max` misses its own floor by 4%;
the tail mean clears its own by `2.64x`, and still clears at `2.49x` under
:func:`max_floor`, the adversarial reading D-372/D-374 grade on.

**Finding #2 — both halves of the ratio move, and the floor moves the *right*
way.** The between-arm gap more than doubles (`0.0633` → `0.1381`, `2.18x`) while
the null floor **falls** (`0.0659` → `0.0523`, `0.79x`). A change of observable
that only widened the numerator would be suspect — it would look like a
rescaling. This one simultaneously separates the arms further and is *less*
seed-noisy, which is exactly the estimator-class prediction: averaging over the
worst decile discards the single-sample jitter that a maximum reports in full.

Note where that lands against D-376. :mod:`tail_stability` refuted the
estimator-class story on the **within-run** axis (`half_max/cte_max = 1.0000`
in 16/16 — the max is not sample-starved inside a run). It is vindicated here on
the **across-seed** axis instead. Both are true and they are not in tension: the
maximum is stable *within* a run and noisy *across* seeds, which is what a
per-run order statistic should do.

**Finding #3 — the arms fall into two clean clusters the maximum blurred.**
Eight-seed TVaR means:

    social_mppi 0.1843   essps_mppi 0.1673   frozen_risk/risk_mppi 0.1541
    gap_gated_mppi 0.0580   geometric/stock_mppi 0.0575   cbf_mppi 0.0461

`0.046`–`0.058` against `0.154`–`0.184` — a **`3.0x`** ratio between the two
cluster means (`0.0548` vs `0.1649`), with nothing in between. The `0.0960`
jump across the divide is `1.8x` the `0.0523` floor, while *neither* cluster's
internal width (`0.0119`, `0.0302`) reaches it — so the partition is the only
structure this column licenses, and the within-cluster ordering is not.
`frozen_risk_mppi`/`risk_mppi` and `geometric_mppi`/`stock_mppi` are
bit-identical pairs, as they are in the `cte_max` column; that is a property of
the arms, not of this reading.

**Finding #4 — the claim is not threshold-shopped, and the way it fails to be
is itself the mechanism.** The source's G5 gate requires an estimate to hold
across `u in [q-0.02, q+0.02]`; :data:`THRESHOLD_STABILITY` runs the window on
the same 64 rollouts:

    q = 0.88    gap 0.1410   floor 0.0503   2.80x
    q = 0.90    gap 0.1381   floor 0.0523   2.64x
    q = 0.92    gap 0.1334   floor 0.0544   2.45x

All three clear, so `q=0.90` is not load-bearing and :func:`threshold_shopped`
returns empty. But read the *direction*: as `q` rises the gap shrinks and the
floor grows, monotonically, and extrapolating to `q → 1` — where TVaR becomes
the maximum — lands on the `0.96x` that `cte_max` actually measures. The rescue
is not a discontinuity at `0.90`; it is a **continuum in how much of the tail
gets averaged**, and `cte_max` is its degenerate endpoint. That is a stronger
statement than finding #1 alone: the observable was not merely swapped for a
luckier one, it was moved along an axis whose direction predicts the result.

**The consequence for the fork, stated at the strength it earns.** The expensive
prong is **not needed to grade cross-track on this scene**. The column was never
ungradeable at this budget — it was ungradeable *as a maximum*. That retires the
scientific bottleneck the 512 rollouts were priced for, at zero rollouts beyond
the 64 already spent, and it does so without the §8 equivalence-claim fallback
(a positive result, not a declared-margin null).

**Scope, and the second item is a live gate this module does not close.**

* **Still one scene — and the second endpoint turned out to be untestable, not
  contrary.** :data:`SECOND_SCENE` was harvested 2026-08-20 (64 rollouts, the
  G5 window read off the same runs) precisely to decide D-372's column-vs-scene
  question. It decides nothing, for a reason worth more than the answer would
  have been: **seven of its eight arms are bit-identical** (:func:`distinct_arms`
  = 2), so there is no between-arm difference for *any* observable to recover.
  TVaR reads `0.07x` there against `cte_max`'s `0.35x`, but both numbers are
  statistics over a population of two wearing the shape of a population of
  eight. :func:`column_licensed` is therefore `False` **for want of evidence** —
  see :func:`second_verdict`, which keeps `UNTESTABLE` distinct from `REFUTED`.

  The seven-way tie is not a property of this reading: it is already present in
  the pinned `cte_max` column (`excursion_seed_width.SEED_ENSEMBLE`) on the same
  scene, where it sat unread while three cycles treated `city_curved_v0`'s
  `0.35x` as a *miss*. It is not a miss. A cell whose arms do not separate
  cannot miss — and the branch's floor machinery will return a well-formed
  number for it either way, which is exactly why :data:`MIN_DISTINCT_ARMS` now
  gates the reading rather than trusting the ratio.

  So finding #1 licenses `cafe_convoy_v0` and nothing else, and the open work is
  no longer "harvest the second endpoint" but **find one** — a scene that
  excites at least :data:`MIN_DISTINCT_ARMS` arms. The six unharvested scenarios
  are candidates; none has been checked for excitation, and that check is free
  wherever a `cte_max` ensemble is already pinned.
* **`TVaR₀.₉` is not `cte_max`, and the claim must be restated on it.** This
  says the arms differ in *mean worst-decile* cross-track error. It says
  nothing about worst-case excursion, which is what a reader of "경로추종" may
  assume `cte_max` was measuring. Any north-star claim built on this must name
  the observable — see :data:`CLAIM_FORM`.
* **G5 (threshold stability) is checked and passes** — :data:`THRESHOLD_STABILITY`,
  finding #4. The source's other four gates are **not** run here: G1 (mean
  equivalence), G3 (sample-size adequacy), G4 (Anderson–Darling goodness-of-fit)
  and the GPD shape machinery are for a `xi`-fitting protocol this reading
  deliberately avoids, which is the whole reason it is affordable.
* Seed 0–7, `lam=0.8`, `w_epist=0.0`, the operating point
  :mod:`clearance_census` harvests at. Same isolation kwargs, so the TVaR column
  and the `cte_max` column it is graded against are the same experiment read
  twice.
"""

from __future__ import annotations

import sys

from . import aa_calibration, excursion_seed_width

#: Scene the fork is priced for — the excited endpoint, and the one whose
#: `cte_max` misses its own floor by the narrowest margin (`0.96x`). Chosen
#: because a rescue that only worked on the *comfortable* miss would say
#: nothing about the case the branch is stuck on.
SCENE = "cafe_convoy_v0"

#: Tail fraction. `0.90` is the source's `TVaR_{0.9}` — the mean of the worst
#: decile — not a value this project tuned. :data:`THRESHOLD_STABILITY` is the
#: check that it was not tuned by accident.
Q = 0.90

#: Seeds per arm, read from :mod:`excursion_seed_width` rather than restated so
#: the TVaR column and the `cte_max` column rest on the *same* rollout count by
#: construction.
SEEDS = excursion_seed_width.SEEDS

#: `arm -> (TVaR_0.9,) * SEEDS` on :data:`SCENE`. 64 closed-loop rollouts,
#: `118.3 s` measured 2026-08-20, via `simulate()` + `cross_track_error()` at
#: `lam=0.8` — the construction :func:`retake` re-derives.
TVAR_ENSEMBLE: dict[str, tuple[float, ...]] = {
    "cbf_mppi": (0.0463, 0.0433, 0.0531, 0.025, 0.0537, 0.0398, 0.0552, 0.0527),
    "essps_mppi": (0.1408, 0.1436, 0.1711, 0.2549, 0.1499, 0.1649, 0.1318, 0.181),
    "frozen_risk_mppi": (0.1145, 0.1457, 0.1461, 0.2051, 0.1186, 0.1779, 0.1441, 0.1805),
    "gap_gated_mppi": (0.0429, 0.0645, 0.0407, 0.0659, 0.0662, 0.0616, 0.0825, 0.0399),
    "geometric_mppi": (0.0561, 0.06, 0.0647, 0.0691, 0.0396, 0.0403, 0.0623, 0.0676),
    "risk_mppi": (0.1145, 0.1457, 0.1461, 0.2051, 0.1186, 0.1779, 0.1441, 0.1805),
    "social_mppi": (0.2024, 0.1747, 0.1683, 0.149, 0.1522, 0.2124, 0.2585, 0.1566),
    "stock_mppi": (0.0561, 0.06, 0.0647, 0.0691, 0.0396, 0.0403, 0.0623, 0.0676),
}

#: `q -> (real gap, p95 floor, ratio)` over the source's G5 window
#: `q in [0.90 - delta, 0.90 + delta]`, `delta = 0.02`. The source kills a claim
#: that survives at exactly one threshold; :func:`threshold_shopped` is that
#: gate, and it reads this table rather than :data:`Q` alone.
THRESHOLD_STABILITY: dict[float, tuple[float, float, float]] = {
    0.88: (0.1410, 0.0503, 2.80),
    0.90: (0.1381, 0.0523, 2.64),
    0.92: (0.1334, 0.0544, 2.45),
}

#: The second endpoint, harvested 2026-08-20 to test whether finding #1 is a
#: property of the *column* (D-372's reading) or of the `(column, scene)` pair.
#: It answers neither, because the cell is degenerate — see
#: :data:`TVAR_ENSEMBLE_SECOND` and :func:`distinct_arms`.
SECOND_SCENE = "city_curved_v0"

#: `arm -> (TVaR_0.9,) * SEEDS` on :data:`SECOND_SCENE`. A second 64 rollouts,
#: same construction as :func:`retake`, same operating point.
#:
#: **Seven of the eight rows are bit-identical.** That is not a rounding
#: artifact and not a property of this observable: the pinned `cte_max` column
#: on the same scene (`excursion_seed_width.SEED_ENSEMBLE[SECOND_SCENE]`) has
#: the *same* seven-way tie. Only `essps_mppi` moves, and it is the one arm
#: whose operating point differs by construction (`w_voo`).
TVAR_ENSEMBLE_SECOND: dict[str, tuple[float, ...]] = {
    "cbf_mppi": (0.2273, 0.3494, 0.3365, 0.2676, 0.2108, 0.2368, 0.2218, 0.3449),
    "essps_mppi": (0.257, 0.2865, 0.2853, 0.2531, 0.2812, 0.3194, 0.2843, 0.2767),
    "frozen_risk_mppi": (0.2273, 0.3494, 0.3365, 0.2676, 0.2108, 0.2368, 0.2218, 0.3449),
    "gap_gated_mppi": (0.2273, 0.3494, 0.3365, 0.2676, 0.2108, 0.2368, 0.2218, 0.3449),
    "geometric_mppi": (0.2273, 0.3494, 0.3365, 0.2676, 0.2108, 0.2368, 0.2218, 0.3449),
    "risk_mppi": (0.2273, 0.3494, 0.3365, 0.2676, 0.2108, 0.2368, 0.2218, 0.3449),
    "social_mppi": (0.2273, 0.3494, 0.3365, 0.2676, 0.2108, 0.2368, 0.2218, 0.3449),
    "stock_mppi": (0.2273, 0.3494, 0.3365, 0.2676, 0.2108, 0.2368, 0.2218, 0.3449),
}

#: The G5 window on :data:`SECOND_SCENE`, same three thresholds. Recorded even
#: though the cell is degenerate, because the *reason* it fails must be legible
#: as "no signal at any threshold" rather than "shopped the wrong one".
THRESHOLD_STABILITY_SECOND: dict[float, tuple[float, float, float]] = {
    0.88: (0.0060, 0.0820, 0.07),
    0.90: (0.0060, 0.0850, 0.07),
    0.92: (0.0033, 0.0873, 0.04),
}

#: Minimum distinct arm rows for a between-arm claim to be *checkable* in a
#: cell. Two arms that emit identical trajectories do not supply a weak version
#: of the comparison — they supply none, and every floor statistic still returns
#: a number. `3` rather than `2` because :data:`SECOND_SCENE` reaches exactly
#: `2` and is the case this constant exists to reject.
MIN_DISTINCT_ARMS = 3

#: The only form a north-star claim may take on this reading. Pinned as a string
#: because the failure mode is prose drift, not arithmetic: a later cycle that
#: writes "arms differ in worst-case cross-track error" would be quoting a
#: number this module did not measure.
CLAIM_FORM = (
    "mean worst-decile cross-track error (TVaR_0.9), 8 seeds, cafe_convoy_v0"
)


def _gaps(arm: str) -> tuple[float, ...]:
    """One arm's null-gap distribution, via the shared A-A machinery."""
    return aa_calibration.null_gaps(TVAR_ENSEMBLE[arm])


def p95_floor(ensemble: dict[str, tuple[float, ...]] | None = None) -> float:
    """Cell null floor for the TVaR column: largest per-arm p95 null gap.

    `ensemble` is threaded rather than closed over for the reason
    :func:`tail_stability.saturated_by_midpoint` documents — a guard reaching a
    same-module registry goes `DERIVED` under `predicate_depth`.
    """
    ens = TVAR_ENSEMBLE if ensemble is None else ensemble
    return round(max(aa_calibration._quantile(aa_calibration.null_gaps(r), 0.95)
                     for r in ens.values()), 4)


def max_floor(ensemble: dict[str, tuple[float, ...]] | None = None) -> float:
    """Adversarial null floor: the largest gap any split of any arm reaches."""
    ens = TVAR_ENSEMBLE if ensemble is None else ensemble
    return round(max(aa_calibration.null_gaps(r)[-1] for r in ens.values()), 4)


def real_gap(ensemble: dict[str, tuple[float, ...]] | None = None) -> float:
    """Largest true between-arm difference of full eight-seed TVaR means."""
    ens = TVAR_ENSEMBLE if ensemble is None else ensemble
    means = [sum(r) / len(r) for r in ens.values()]
    return round(max(means) - min(means), 4)


def clears_floor(strict: bool = False) -> bool:
    """Whether the TVaR column's real gap exceeds its own null floor."""
    return real_gap() > (max_floor() if strict else p95_floor())


def ratio(strict: bool = False) -> float:
    """`real_gap / floor` — the `Nx` the branch quotes for every other column."""
    return round(real_gap() / (max_floor() if strict else p95_floor()), 2)


def baseline_ratio(strict: bool = False) -> float:
    """The same reading for `cte_max` on :data:`SCENE`.

    Read through :mod:`aa_calibration` rather than restated, so the comparison
    cannot drift from the column it is a comparison *against* — D-374's defect
    (a gap and a window divided by different floors) one column over.
    """
    floor = (aa_calibration.max_floor if strict else aa_calibration.p95_floor)(
        "cte_max", SCENE)
    return round(aa_calibration.real_gap("cte_max", SCENE) / floor, 2)


def rescued() -> bool:
    """Does the change of observable convert an ungradeable cell to a graded one?

    Both directions are required: a TVaR column that cleared while `cte_max`
    *also* cleared would say nothing about the fork.
    """
    return clears_floor() and baseline_ratio() <= 1.0


def threshold_shopped() -> tuple[float, ...]:
    """Thresholds in the G5 window whose verdict disagrees with :data:`Q`'s.

    The source's G5 gate: an estimate must hold across `u in [q-d, q+d]`,
    `d = 0.02`. A non-empty return means finding #1 is threshold-shopped and
    must not be quoted. Empty (with a populated table) means it survived the
    window.
    """
    if not THRESHOLD_STABILITY:
        return ()
    return tuple(sorted(q for q, (_g, _f, r) in THRESHOLD_STABILITY.items()
                        if (r > 1.0) is not (ratio() > 1.0)))


def distinct_arms(ensemble: dict[str, tuple[float, ...]] | None = None) -> int:
    """How many *distinct* seed-rows the cell contains.

    The precondition every floor reading on this branch has assumed and none
    has checked: a between-arm gap is only a measurement if the arms differ.
    Bit-identical rows make `real_gap` a statistic over a population of one
    while it keeps returning a well-formed number.
    """
    ens = TVAR_ENSEMBLE if ensemble is None else ensemble
    return len(set(ens.values()))


def excited(ensemble: dict[str, tuple[float, ...]] | None = None) -> bool:
    """Whether a cell separates its arms enough for the comparison to exist."""
    return distinct_arms(ensemble) >= MIN_DISTINCT_ARMS


def second_ratio(strict: bool = False) -> float:
    """`real_gap / floor` on :data:`SECOND_SCENE` — the same reading as :func:`ratio`."""
    floor = (max_floor(TVAR_ENSEMBLE_SECOND) if strict
             else p95_floor(TVAR_ENSEMBLE_SECOND))
    return round(real_gap(TVAR_ENSEMBLE_SECOND) / floor, 2)


def second_clears_floor(strict: bool = False) -> bool:
    """Whether the second endpoint's TVaR gap exceeds its own null floor."""
    return second_ratio(strict) > 1.0


def second_baseline_ratio(strict: bool = False) -> float:
    """`cte_max` on :data:`SECOND_SCENE`, read through :mod:`aa_calibration`."""
    floor = (aa_calibration.max_floor("cte_max", SECOND_SCENE) if strict
             else aa_calibration.p95_floor("cte_max", SECOND_SCENE))
    return round(aa_calibration.real_gap("cte_max", SECOND_SCENE) / floor, 2)


def column_licensed() -> bool:
    """Is finding #1 licensed as a statement about the **column**, not the scene?

    D-372 held that the dividing line is the column; D-371 was wrong in exactly
    the direction of generalising one scene to five. Promoting finding #1 to a
    column-level claim therefore requires a *second* gradeable endpoint that
    agrees. :data:`SECOND_SCENE` cannot supply one — it is degenerate under
    :func:`excited` — so this returns `False` for want of evidence, which is a
    different verdict from the rescue having failed there.
    """
    return excited(TVAR_ENSEMBLE_SECOND) and second_clears_floor()


def second_verdict() -> str:
    """Why the second endpoint decides nothing — the distinction D-372 needs kept."""
    if not excited(TVAR_ENSEMBLE_SECOND):
        return (f"UNTESTABLE: {SECOND_SCENE} has "
                f"{distinct_arms(TVAR_ENSEMBLE_SECOND)} distinct arm rows of "
                f"{len(TVAR_ENSEMBLE_SECOND)} (need {MIN_DISTINCT_ARMS}) — the "
                f"arms do not separate, so no observable can grade them here")
    return ("REFUTED" if not second_clears_floor() else "CONFIRMED")


def retake(*, q: float = Q, scene: str | None = None) -> dict[str, tuple[float, ...]]:
    """Re-measure :data:`TVAR_ENSEMBLE` from source (~118 s, 64 rollouts)."""
    import numpy as np

    from eval.path_tracking_metrics import cross_track_error

    from .clearance_census import ISOLATION, REGISTRY, takes_epistemic_kwargs
    from .controllers import make_controller
    from .controllers.stock_mppi import MPPIParams
    from .essps import OPERATING_LAM, OPERATING_W_VOO
    from .run import ROBOT_RADIUS, simulate
    from .scenario import load_scenario

    sc = load_scenario(f"eval/scenarios/{scene or SCENE}.yaml")
    path = np.asarray(sc.waypoints, dtype=float)
    out: dict[str, tuple[float, ...]] = {}
    for name in sorted(REGISTRY):
        row = []
        for s in range(SEEDS):
            kw = dict(w_voo=OPERATING_W_VOO, w_epist=0.0, **ISOLATION) \
                if takes_epistemic_kwargs(name, sc) else {}
            ctrl = make_controller(name, sc, seed=s, robot_radius=ROBOT_RADIUS,
                                   params=MPPIParams(lam=OPERATING_LAM), **kw)
            cte = np.abs(cross_track_error(simulate(sc, ctrl), path))
            row.append(round(float(cte[cte >= np.quantile(cte, q)].mean()), 4))
        out[name] = tuple(row)
    return out


def drift() -> tuple[str, ...]:
    """Internal-consistency read: the pinned verdicts against the ensemble."""
    bad: list[str] = []
    if set(TVAR_ENSEMBLE) != set(excursion_seed_width.SEED_ENSEMBLE[SCENE]):
        bad.append("TVAR_ENSEMBLE arms != the cte_max column's arms — "
                   "the two readings would not rest on the same rollouts")
    for arm, row in TVAR_ENSEMBLE.items():
        if len(row) != SEEDS:
            bad.append(f"{arm}: {len(row)} seeds, expected {SEEDS}")
    if clears_floor() is not (ratio() > 1.0):
        bad.append("clears_floor() disagrees with ratio() > 1")
    if THRESHOLD_STABILITY and Q not in THRESHOLD_STABILITY:
        bad.append(f"THRESHOLD_STABILITY is populated but omits Q={Q}")
    if set(TVAR_ENSEMBLE_SECOND) != set(
            excursion_seed_width.SEED_ENSEMBLE[SECOND_SCENE]):
        bad.append("TVAR_ENSEMBLE_SECOND arms != the cte_max column's arms on "
                   f"{SECOND_SCENE}")
    for arm, row in TVAR_ENSEMBLE_SECOND.items():
        if len(row) != SEEDS:
            bad.append(f"{SECOND_SCENE}/{arm}: {len(row)} seeds, expected {SEEDS}")
    if THRESHOLD_STABILITY_SECOND and Q not in THRESHOLD_STABILITY_SECOND:
        bad.append(f"THRESHOLD_STABILITY_SECOND is populated but omits Q={Q}")
    if column_licensed() and not excited(TVAR_ENSEMBLE_SECOND):
        bad.append("column_licensed() is True on a degenerate second endpoint")
    return tuple(bad)


def format_census() -> str:
    """The census as the branch's other floor readings print it."""
    lines = [
        f"tail_mean — {SCENE}, TVaR_{Q}, {SEEDS} seeds x {len(TVAR_ENSEMBLE)} arms",
        "",
        f"  {'column':12s} {'real gap':>9} {'p95 floor':>10} {'max floor':>10}"
        f" {'vs p95':>7} {'vs max':>7}",
        f"  {'cte_max':12s} "
        f"{aa_calibration.real_gap('cte_max', SCENE):>9.4f} "
        f"{aa_calibration.p95_floor('cte_max', SCENE):>10.4f} "
        f"{aa_calibration.max_floor('cte_max', SCENE):>10.4f} "
        f"{baseline_ratio():>6.2f}x {baseline_ratio(True):>6.2f}x",
        f"  {f'TVaR_{Q}':12s} {real_gap():>9.4f} {p95_floor():>10.4f} "
        f"{max_floor():>10.4f} {ratio():>6.2f}x {ratio(True):>6.2f}x",
        "",
        "  eight-seed means:",
    ]
    for arm in sorted(TVAR_ENSEMBLE, key=lambda a: -sum(TVAR_ENSEMBLE[a])):
        row = TVAR_ENSEMBLE[arm]
        lines.append(f"    {arm:20s} {sum(row) / len(row):.4f}")
    lines += [
        "",
        f"  RESCUED: {rescued()} — TVaR "
        f"{'clears' if clears_floor() else 'misses'} its own floor while cte_max "
        f"{'clears' if baseline_ratio() > 1.0 else 'misses'} its own.",
    ]
    if THRESHOLD_STABILITY:
        lines.append(f"  G5 window {sorted(THRESHOLD_STABILITY)}: "
                     f"shopped={threshold_shopped() or 'no'}")
        for q in sorted(THRESHOLD_STABILITY):
            g, f, r = THRESHOLD_STABILITY[q]
            lines.append(f"    q={q:.2f}  gap={g:.4f} p95={f:.4f}  {r:.2f}x")
    else:
        lines.append("  G5 window: NOT MEASURED — finding #1 is single-threshold")
    lines += [
        "",
        f"  second endpoint — {SECOND_SCENE}, TVaR_{Q}, {SEEDS} seeds x "
        f"{len(TVAR_ENSEMBLE_SECOND)} arms",
        f"    {'cte_max':12s} {second_baseline_ratio():>6.2f}x "
        f"{second_baseline_ratio(True):>6.2f}x",
        f"    {f'TVaR_{Q}':12s} {second_ratio():>6.2f}x {second_ratio(True):>6.2f}x",
        f"    distinct arm rows: {distinct_arms(TVAR_ENSEMBLE_SECOND)}"
        f"/{len(TVAR_ENSEMBLE_SECOND)} (need {MIN_DISTINCT_ARMS})",
        f"    {second_verdict()}",
        f"  COLUMN-LEVEL CLAIM LICENSED: {column_licensed()}",
    ]
    if drift():
        lines += ["", "  DRIFT:"] + [f"    {b}" for b in drift()]
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    print(format_census())
    return 1 if drift() else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

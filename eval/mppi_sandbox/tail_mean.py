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
:mod:`aa_calibration` null-gap machinery. `cte_max` misses its own floor by 4%;
the tail mean clears its own by `2.64x`, and still clears at `2.49x` under
:func:`max_floor`, the adversarial reading D-372/D-374 grade on.

.. warning::

   **Q-175 (2026-08-20) — "the same rollouts" was the load-bearing half of this
   paragraph and it is not established.** The two columns are built by different
   code paths at different operating points, and each pin is reproduced by
   exactly one of them and not the other. Measured on `cafe_head_on_v0`, seed 0,
   all eight arms: :data:`TVAR_ENSEMBLE_THIRD` reproduces under :func:`retake`
   (`lam=OPERATING_LAM` plus `clearance_census.ISOLATION`) and not under
   `run_scenario` defaults; `excursion_seed_width.SEED_ENSEMBLE` reproduces
   under `run_scenario` defaults and not under :func:`retake`. A structural
   fingerprint agrees: `risk_mppi` and `frozen_risk_mppi` are bit-identical
   under the isolation kwargs and *differ* in the `cte_max` pin.

   Nothing here re-derives across the boundary, which is why no guard caught it
   — :func:`drift` compares the two columns' **arm names** and never their
   values. What the readings still share is scene, arm set and seed set; what
   they do not share is the rollouts. Until this is reconciled, treat
   :func:`dominance_holds` as a comparison of two experiments rather than two
   observables on one, and do not quote finding #1 as a zero-cost
   re-expression.

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

#: The **third** endpoint, and the first one chosen by the clearance ordering
#: rather than by where a `cte_max` ensemble happened to be pinned. D-386 left
#: the branch needing a scene that passes :func:`excited`; this one does, at
#: `6/8` distinct arm rows, and it grades `3.88x` (`3.32x` adversarial).
THIRD_SCENE = "cafe_head_on_v0"

#: `cafe_head_on_v0`, TVaR₀.₉, 8 seeds × 8 arms, 64 rollouts (~118 s).
TVAR_ENSEMBLE_THIRD: dict[str, tuple[float, ...]] = {
    "cbf_mppi": (0.3474, 0.424, 0.3171, 0.3858, 0.3683, 0.3487, 0.41, 0.3032),
    "essps_mppi": (0.1856, 0.1852, 0.1825, 0.1973, 0.1825, 0.2089, 0.168, 0.1527),
    "frozen_risk_mppi": (0.1356, 0.1644, 0.1265, 0.1502, 0.1501, 0.1557, 0.1642, 0.1254),
    "gap_gated_mppi": (0.1387, 0.1504, 0.1169, 0.1544, 0.1203, 0.1425, 0.1643, 0.1128),
    "geometric_mppi": (0.1308, 0.1504, 0.1105, 0.1536, 0.1207, 0.145, 0.1658, 0.1278),
    "risk_mppi": (0.1356, 0.1644, 0.1265, 0.1502, 0.1501, 0.1557, 0.1642, 0.1254),
    "social_mppi": (0.1938, 0.2311, 0.1747, 0.2116, 0.2013, 0.2277, 0.2275, 0.1778),
    "stock_mppi": (0.1308, 0.1504, 0.1105, 0.1536, 0.1207, 0.145, 0.1658, 0.1278),
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


def second_ratio_raw(strict: bool = False) -> float:
    """The arithmetic behind :func:`second_ratio`, ungated.

    Split out under Q-176(b) so the gate has something to gate. Everything a
    reader could mis-cite lives here, and the *only* licensed callers are
    :func:`second_ratio` and the tests that pin this cell's numbers — a test
    asserting `0.07` is asserting about the construction, not citing a finding.
    A production caller wanting the number must go through the gate and handle
    the `None`, which is the whole content of the decision.
    """
    floor = (max_floor(TVAR_ENSEMBLE_SECOND) if strict
             else p95_floor(TVAR_ENSEMBLE_SECOND))
    return round(real_gap(TVAR_ENSEMBLE_SECOND) / floor, 2)


def second_ratio(strict: bool = False) -> float | None:
    """`real_gap / floor` on :data:`SECOND_SCENE`, or `None` when it cannot be read.

    Q-176 answered (b): D-394's mark fixed *one print site*, not the return
    value, so any caller — and any future cycle's prose — could still read the
    float and cite it without the caveat. `None` makes that citation
    syntactically impossible rather than merely discouraged; the defence stops
    depending on the reader (D-397).

    The gate is derived from :func:`scene_mark`, not from a named scene, for
    the reason D-396 paid for: the number becomes readable again on exactly the
    harvest that makes the scene gradeable, with nothing to remember. No
    recursion — :func:`ungradeable_scenes` reaches `full_screen`, which does
    not call back into this helper.
    """
    return None if scene_mark(SECOND_SCENE) else second_ratio_raw(strict)


def second_clears_floor(strict: bool = False) -> bool | None:
    """Whether the second endpoint's TVaR gap exceeds its own null floor.

    `None` when the ratio is `None`. This is the hole D-397 named: the verdict
    read the cell *through* :func:`second_ratio` and so escaped D-393's audit,
    and what actually kept it honest was an `excited()` short-circuit in
    :func:`second_verdict` — a precondition with no connection to
    gradeability. It now carries the unreadability itself.
    """
    ratio = second_ratio(strict)
    return None if ratio is None else ratio > 1.0


def second_baseline_ratio_raw(strict: bool = False) -> float:
    """The arithmetic behind :func:`second_baseline_ratio`, ungated."""
    floor = (aa_calibration.max_floor("cte_max", SECOND_SCENE) if strict
             else aa_calibration.p95_floor("cte_max", SECOND_SCENE))
    return round(aa_calibration.real_gap("cte_max", SECOND_SCENE) / floor, 2)


def second_baseline_ratio(strict: bool = False) -> float | None:
    """`cte_max` on :data:`SECOND_SCENE`, or `None` when it cannot be read.

    Same gate as :func:`second_ratio`, same reason.
    """
    return (None if scene_mark(SECOND_SCENE)
            else second_baseline_ratio_raw(strict))


def third_ratio(strict: bool = False) -> float:
    """`real_gap / floor` on :data:`THIRD_SCENE` — the same reading as :func:`ratio`."""
    floor = (max_floor(TVAR_ENSEMBLE_THIRD) if strict
             else p95_floor(TVAR_ENSEMBLE_THIRD))
    return round(real_gap(TVAR_ENSEMBLE_THIRD) / floor, 2)


def third_clears_floor(strict: bool = False) -> bool:
    """Whether the third endpoint's TVaR gap exceeds its own null floor."""
    return third_ratio(strict) > 1.0


def third_paired() -> bool:
    """Whether :data:`THIRD_SCENE` can be *contrasted* against `cte_max`, not just graded.

    It can, as of the 2026-08-20 harvest that bought the missing half (64
    rollouts, `52.5 s`, pinned in `excursion_seed_width.SEED_ENSEMBLE`). Until
    then this returned `False`, and the asymmetry it named was real:
    :data:`SECOND_SCENE` was chosen *because* a `cte_max` ensemble was already
    pinned there — which is what made a paired reading free, and also what made
    the scene degenerate, since the pin and the tie came from the same eight
    rollouts. :data:`THIRD_SCENE` was chosen by the clearance ordering instead,
    so its pairing had to be paid for separately. It was, and see
    :func:`contrast_replicates` for what the paid reading says.
    """
    return THIRD_SCENE in excursion_seed_width.SEED_ENSEMBLE


def third_baseline_ratio(strict: bool = False) -> float:
    """`cte_max` on :data:`THIRD_SCENE`, read through :mod:`aa_calibration`.

    The half :func:`third_paired` was waiting on. Same construction as
    :func:`second_baseline_ratio`, same floor machinery, same 8 seeds.
    """
    floor = (aa_calibration.max_floor("cte_max", THIRD_SCENE) if strict
             else aa_calibration.p95_floor("cte_max", THIRD_SCENE))
    return round(aa_calibration.real_gap("cte_max", THIRD_SCENE) / floor, 2)


def contrast_replicates() -> bool:
    """Does finding #1's **contrast** hold on the second scene that can test it?

    **It does not, and this is the reading the pairing was bought to get.**

    Finding #1 on :data:`SCENE` is a conjunction of two halves: `cte_max`
    *misses* its own null floor (`0.96x`) while TVaR₀.₉ *clears* (`2.64x`).
    Five cycles read that as a fact about the observable — D-383 went further and
    called `cte_max` the degenerate endpoint of a tail-averaging continuum. On
    :data:`THIRD_SCENE`, the first scene excited in **both** columns since, the
    second half reproduces (`3.88x`) and the first half **does not**: `cte_max`
    grades there at `3.12x`, comfortably above its own floor.

    So the population of scenes on which a maximum is ungradeable is still
    **one**, and the honest generalisation is not "TVaR grades where `cte_max`
    cannot" but :func:`dominance_holds` — TVaR's ratio exceeds `cte_max`'s on
    both scenes that can be compared. The mechanism that survives is a
    *noise-reduction* one, and it is only decisive where the effect is marginal
    against seed noise: convoy's `cte_max` gap is `0.0633` against a `0.0659`
    floor, while head-on's is `0.2960` — **4.7x larger** — against a floor of
    comparable size (`0.0948`). A big enough effect clears an 8-seed floor as a
    maximum; that is why buying this scene could not have been skipped by
    reasoning from the first.
    """
    return third_baseline_ratio() <= 1.0


def dominance_holds() -> bool:
    """The claim that *does* survive the pairing: TVaR ≥ `cte_max`, cell by cell.

    Restricted to cells :func:`excited` admits — :data:`SECOND_SCENE` is
    excluded, and not because it disagrees (it does, `0.07x` vs `0.35x`) but
    because a population of two distinct arm rows grades nothing in either
    column. Reading a degenerate cell as a counter-example is exactly the
    `UNTESTABLE`/`REFUTED` collapse :func:`second_verdict` exists to prevent.
    """
    return all(tv > base for tv, base in COMPARABLE_CELLS.values())


#: `scene -> (TVaR_0.9 ratio, cte_max ratio)` on every scene excited in **both**
#: columns. Two entries: the two halves of :func:`dominance_holds`'s evidence,
#: and the whole of it — a population of two, stated as a population of two.
COMPARABLE_CELLS: dict[str, tuple[float, float]] = {
    "cafe_convoy_v0": (2.64, 0.96),
    "cafe_head_on_v0": (3.88, 3.12),
}

#: The `cte_max` column re-harvested under :func:`retake`'s **own** construction
#: — `lam=OPERATING_LAM` plus `clearance_census.ISOLATION` — answering Q-175 in
#: favour of option (a). 128 rollouts, 2026-08-20.
#:
#: Two reproduction checks ran before anything was read off it. The TVaR column
#: harvested in the same loop reproduces :data:`TVAR_ENSEMBLE` and
#: :data:`TVAR_ENSEMBLE_THIRD` **8/8 arms on both scenes**, so this construction
#: *is* the operating point those pins were taken at; and the `cte_max` column
#: it produces matches `excursion_seed_width.SEED_ENSEMBLE` **0/8 on both**, so
#: the old pin is *not*. Q-175's diagnosis reproduces from the other side.
CTE_MAX_AT_OPERATING_POINT: dict[str, dict[str, tuple[float, ...]]] = {
    "cafe_convoy_v0": {
        "cbf_mppi": (0.0915, 0.1157, 0.1348, 0.0578, 0.1519, 0.0878, 0.1168, 0.1314),
        "essps_mppi": (0.1572, 0.1655, 0.1831, 0.2724, 0.1708, 0.1761, 0.1422, 0.2086),
        "frozen_risk_mppi": (0.1269, 0.1654, 0.1669, 0.2297, 0.127, 0.2015, 0.1554, 0.2006),
        "gap_gated_mppi": (0.1114, 0.1585, 0.1062, 0.1786, 0.1714, 0.1251, 0.1944, 0.1022),
        "geometric_mppi": (0.1365, 0.1552, 0.1654, 0.1379, 0.1303, 0.0715, 0.1184, 0.1587),
        "risk_mppi": (0.1269, 0.1654, 0.1669, 0.2297, 0.127, 0.2015, 0.1554, 0.2006),
        "social_mppi": (0.2102, 0.1787, 0.1757, 0.1572, 0.1621, 0.2376, 0.2743, 0.1683),
        "stock_mppi": (0.1365, 0.1552, 0.1654, 0.1379, 0.1303, 0.0715, 0.1184, 0.1587),
    },
    "cafe_head_on_v0": {
        "cbf_mppi": (0.9694, 0.8987, 0.9355, 0.9335, 1.0186, 0.8833, 0.9483, 0.8862),
        "essps_mppi": (0.6085, 0.6107, 0.6068, 0.6146, 0.6107, 0.6189, 0.611, 0.6112),
        "frozen_risk_mppi": (0.6196, 0.619, 0.6132, 0.6027, 0.607, 0.6557, 0.6086, 0.6009),
        "gap_gated_mppi": (0.6188, 0.6069, 0.6112, 0.6197, 0.5979, 0.6127, 0.6097, 0.6147),
        "geometric_mppi": (0.6119, 0.6069, 0.6001, 0.6037, 0.5978, 0.6079, 0.61, 0.6108),
        "risk_mppi": (0.6196, 0.619, 0.6132, 0.6027, 0.607, 0.6557, 0.6086, 0.6009),
        "social_mppi": (0.6975, 0.6858, 0.7134, 0.6577, 0.7428, 0.78, 0.802, 0.7321),
        "stock_mppi": (0.6119, 0.6069, 0.6001, 0.6037, 0.5978, 0.6079, 0.61, 0.6108),
    },
    # The third row of `aa_calibration.COLUMN_VERDICT["cte_max"]`, bought so
    # that column's tally would stop mixing operating points (64 rollouts,
    # `57.3 s`, 2026-08-21). It does not buy that, and see
    # :func:`aligned_second_verdict` for what it buys instead: at the operating
    # point this cell is **degenerate**, exactly as it is at the old one.
    "city_curved_v0": {
        "cbf_mppi": (0.3284, 0.5255, 0.4805, 0.4213, 0.3373, 0.459, 0.3219, 0.5162),
        "essps_mppi": (0.3853, 0.4133, 0.4033, 0.3644, 0.4208, 0.4532, 0.4241, 0.4051),
        "frozen_risk_mppi": (0.3284, 0.5255, 0.4805, 0.4213, 0.3373, 0.459, 0.3219, 0.5162),
        "gap_gated_mppi": (0.3284, 0.5255, 0.4805, 0.4213, 0.3373, 0.459, 0.3219, 0.5162),
        "geometric_mppi": (0.3284, 0.5255, 0.4805, 0.4213, 0.3373, 0.459, 0.3219, 0.5162),
        "risk_mppi": (0.3284, 0.5255, 0.4805, 0.4213, 0.3373, 0.459, 0.3219, 0.5162),
        "social_mppi": (0.3284, 0.5255, 0.4805, 0.4213, 0.3373, 0.459, 0.3219, 0.5162),
        "stock_mppi": (0.3284, 0.5255, 0.4805, 0.4213, 0.3373, 0.459, 0.3219, 0.5162),
    },
}

#: Why `city_curved_v0` is pinned above but absent from :data:`ALIGNED_CELLS`.
#:
#: `(distinct arms, needed, aligned headroom, old headroom)`. The re-take was
#: bought on the premise — written into `aa_calibration.
#: MIXED_OPERATING_POINT_COLUMNS` — that the `cte_max` tally read `1 of 3` over
#: two operating points and that harvesting the third row at the operating
#: point would make it countable. **It does not.** The cell separates
#: :data:`MIN_DISTINCT_ARMS`-1 arms here just as it does at the old point: seven
#: of the eight arms return bit-identical rows, so `real_gap` is a statistic
#: over a population of two and grades nothing at either operating point.
#:
#: So the aligned population is still two cells, and the correct reading of the
#: shipped `1 of 3` is not "mixed" but "one of the three rows was never
#: gradeable in the first place" — see `aa_calibration.degenerate_tally_rows`.
ALIGNED_SECOND: tuple[int, int, float, float] = (2, MIN_DISTINCT_ARMS, 0.12, 0.35)

#: :data:`COMPARABLE_CELLS`, re-derived with both columns at the **same**
#: operating point: `scene -> (TVaR_0.9 headroom, cte_max headroom)`.
#:
#: This is the table :func:`dominance_holds` should always have been reading.
#: Both entries move and **one of them inverts**, so the realignment is not a
#: rounding correction to the old claim — it is a different claim.
ALIGNED_CELLS: dict[str, tuple[float, float]] = {
    "cafe_convoy_v0": (2.64, 1.46),
    "cafe_head_on_v0": (3.88, 4.93),
}


def dominance_at_operating_point() -> bool:
    """:func:`dominance_holds`, asked of one experiment instead of two.

    **False.** `cafe_head_on_v0` inverts — `cte_max` clears its own null by
    `4.93x` against TVaR's `3.88x` — so "TVaR's ratio exceeds `cte_max`'s"
    survives on 1 of 2 cells, which is not a claim.
    """
    return all(tv > base for tv, base in ALIGNED_CELLS.values())


#: Claims retired by the realignment, each with what it said and what the
#: aligned measurement says instead. Retired **by pin rather than by deletion**
#: (the D-387 convention) so a later cycle re-reading the prose that quotes them
#: finds the retraction attached rather than a missing name.
RETIRED_BY_ALIGNMENT: tuple[tuple[str, str, str], ...] = (
    ("tail_mean.dominance_holds",
     "TVaR's ratio exceeds cte_max's on 2/2 comparable cells (2.64>0.96, 3.88>3.12)",
     "1/2 at the aligned operating point (2.64>1.46, 3.88<4.93) — refuted"),
    ("aa_calibration.CONVOY_SPLIT",
     "cafe_convoy_v0 holds everything fixed and cte_max does not clear at all (0.96x)",
     "cte_max clears there (1.46x, adversarial 1.31x); the two rows were never "
     "the same rollouts, so nothing was held fixed"),
)


def aligned_contrast_count() -> int:
    """Cells where `cte_max` misses its own null floor, at the aligned point.

    **Zero.** This is the re-pricing D-390 implied and did not carry through to
    the call sites. The old table made the count 1 of 2 — convoy's `0.96x` —
    and every reader of it inherited the claim that the `cte_max`-fails half of
    finding #1 was *scene-specific*: true on convoy, false on head-on. Read at
    one operating point it is neither. It is true on **no** cell, because the
    only cell that ever supported it was reading different rollouts than the
    column it was being contrasted against.
    """
    return sum(1 for _tv, base in ALIGNED_CELLS.values() if base <= 1.0)


def aligned_dominance_count() -> int:
    """Cells where TVaR's ratio exceeds `cte_max`'s, at the aligned point.

    1 of 2 — the arithmetic behind :func:`dominance_at_operating_point`
    returning False, exposed as a count so :func:`report` can state the
    survival rate rather than a bare boolean.
    """
    return sum(1 for tv, base in ALIGNED_CELLS.values() if tv > base)


def alignment_gain() -> dict[str, tuple[float, float]]:
    """`scene -> (old cte_max headroom, aligned cte_max headroom)`.

    Both scenes read **higher** aligned. The old column was not a noisier
    version of this one; it was a different operating point, and the direction
    of the difference is not something the mismatch predicted.
    """
    return {s: (COMPARABLE_CELLS[s][1], ALIGNED_CELLS[s][1]) for s in ALIGNED_CELLS}


def aligned_second_verdict() -> str:
    """What the third `cte_max` row decides once harvested at the operating point.

    **UNGRADEABLE, and that is the answer to the question the harvest was
    bought to settle.** `aa_calibration.MIXED_OPERATING_POINT_COLUMNS` said the
    `1 of 3` tally was uncountable because one row lacked an aligned re-take.
    The re-take exists now and the tally is still uncountable, for a reason the
    marker did not name: this cell is degenerate at *both* operating points
    (:data:`ALIGNED_SECOND`), so no construction makes it a third row.

    Read the same way :func:`second_verdict` reads the TVaR column here, and it
    reaches the same conclusion from the other column — which is the useful
    part. Degeneracy on :data:`SECOND_SCENE` is a property of the **scene**, not
    of an observable and not of a harvest: the arms do not separate, so nothing
    measured on them grades.
    """
    distinct, need, aligned, old = ALIGNED_SECOND
    return (f"UNGRADEABLE: {SECOND_SCENE} cte_max has {distinct} distinct arm "
            f"rows of {SEEDS} (need {need}) at the operating point, the same as "
            f"at the old one — the aligned {aligned}x and the old {old}x are "
            f"both statistics over a population of two")


def aligned_second_is_gradeable() -> bool:
    """Whether the third row can join :data:`ALIGNED_CELLS`. It cannot."""
    return excited(CTE_MAX_AT_OPERATING_POINT[SECOND_SCENE])


#: How many of the eight arms reproduce across the two operating points on
#: :data:`SECOND_SCENE` — and the arm that does.
#:
#: The two *excited* scenes agree `0/8` (`test_the_old_cte_max_pin_is_a_
#: different_experiment`), which is the signature Q-175 used to establish that
#: the old pin is a different experiment. Here it is `1/8`, and the agreeing arm
#: is `essps_mppi` — the only arm this scene separates at all. The seven arms
#: that collapse to one row disagree across the operating points; the one arm
#: that responds does not.
#:
#: So `0/8` is not the signature of a construction mismatch as such. It is what
#: a mismatch looks like when there are eight independent rows to disagree
#: about, and it degrades toward agreement exactly as the cell degenerates.
ALIGNED_SECOND_AGREEMENT: tuple[int, str] = (1, "essps_mppi")


def retake_max(*, scene: str | None = None) -> dict[str, tuple[float, ...]]:
    """Re-measure :data:`CTE_MAX_AT_OPERATING_POINT` from source (~150 s/scene).

    Byte-for-byte :func:`retake`'s construction with one statistic swapped —
    `cte.max()` for the tail mean — which is the whole content of the claim
    that the two columns now share an operating point. Kept as a callable
    re-derivation because Q-175's defect was precisely that no re-derivation
    crossed the module boundary: the two pins were joined only by prose.
    """
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
            row.append(round(float(cte.max()), 4))
        out[name] = tuple(row)
    return out


def third_verdict() -> str:
    """What the third endpoint decides, now that both its columns are pinned."""
    if not excited(TVAR_ENSEMBLE_THIRD):
        return (f"UNTESTABLE: {THIRD_SCENE} has "
                f"{distinct_arms(TVAR_ENSEMBLE_THIRD)} distinct arm rows of "
                f"{len(TVAR_ENSEMBLE_THIRD)} (need {MIN_DISTINCT_ARMS})")
    if not third_clears_floor():
        return f"REFUTED: {THIRD_SCENE} TVaR misses its own floor"
    if not third_paired():
        paired = ("UNPAIRED — no cte_max ensemble is pinned on this scene, so "
                  "this grades the TVaR column here but does not reproduce the "
                  "cte_max-fails/TVaR-clears contrast finding #1 rests on")
    elif contrast_replicates():
        paired = (f"paired, and the contrast replicates: cte_max "
                  f"{third_baseline_ratio()}x misses its own floor here too")
    else:
        paired = (f"paired, and the contrast DOES NOT replicate: cte_max grades "
                  f"here at {third_baseline_ratio()}x (adversarial "
                  f"{third_baseline_ratio(True)}x), so finding #1's "
                  f"cte_max-fails half is scene-specific — see dominance_holds()")
    return (f"CONFIRMED: {third_ratio()}x (adversarial {third_ratio(True)}x), "
            f"{distinct_arms(TVAR_ENSEMBLE_THIRD)}/"
            f"{len(TVAR_ENSEMBLE_THIRD)} distinct arms; {paired}")


def column_licensed() -> bool:
    """Is finding #1 licensed as a statement about the **column**, not the scene?

    D-372 held that the dividing line is the column; D-371 was wrong in exactly
    the direction of generalising one scene to five. Promoting finding #1 to a
    column-level claim therefore requires a *second* gradeable endpoint that
    agrees. :data:`SECOND_SCENE` cannot supply one — it is degenerate under
    :func:`excited`, which is want of evidence and not a failed rescue.
    :data:`THIRD_SCENE` does: it is excited and it clears.

    What this licenses is bounded, and the bound moved when the third endpoint
    was paired. Two excited scenes clear their own null floors as tail means, so
    *"the TVaR column is gradeable on this harness's budget"* is a column-level
    claim. The stronger reading — *"TVaR grades where `cte_max` cannot"* — is no
    longer merely unproven on a second scene: it is **measured and false there**
    (:func:`contrast_replicates`).

    What replaced it was :func:`dominance_holds`, and that replacement is now
    **itself retired** — D-390 re-read both columns at one operating point and
    it survives on 1 of 2 cells (:func:`dominance_at_operating_point`). So the
    licensed claim is narrower than either: the TVaR column is gradeable, and
    nothing about `cte_max`'s relative standing is. Note the direction — the
    aligned reading makes `cte_max` clear on **both** cells
    (:func:`aligned_contrast_count` is 0), so the contrast did not merely fail
    to generalise; it has no surviving cell at all.
    :data:`COLUMN_CLAIM_FORM` holds the wording.
    """
    return excited(TVAR_ENSEMBLE_THIRD) and third_clears_floor()


#: The only form the *column-level* claim may take, pinned for the reason
#: :data:`CLAIM_FORM` is. The overstatement this now blocks is no longer "two
#: clearing endpoints reproduce finding #1 twice" (the caveat when the third
#: endpoint was unpaired) but the same sentence after the pairing came back
#: *negative* — the contrast was tested on a second scene and did not hold.
COLUMN_CLAIM_FORM: str = (
    "the cross-track column is gradeable as TVaR_0.9 at 64 rollouts on two "
    "excited scenes (cafe_convoy_v0 2.64x, cafe_head_on_v0 3.88x); read at the "
    "same operating point cte_max is gradeable on both of them too (1.46x, "
    "4.93x), so the cte_max-fails half of the contrast survives on zero cells "
    "and TVaR_0.9 grades above cte_max on one of two -- what is licensed is the "
    "TVaR column's own gradeability, and neither the contrast nor dominance"
)


def second_verdict() -> str:
    """Why the second endpoint decides nothing — the distinction D-372 needs kept."""
    if not excited(TVAR_ENSEMBLE_SECOND):
        return (f"UNTESTABLE: {SECOND_SCENE} has "
                f"{distinct_arms(TVAR_ENSEMBLE_SECOND)} distinct arm rows of "
                f"{len(TVAR_ENSEMBLE_SECOND)} (need {MIN_DISTINCT_ARMS}) — the "
                f"arms do not separate, so no observable can grade them here")
    # No `None` branch here, and that is a measurement rather than an omission:
    # `scene_mark(SECOND_SCENE) != ""` requires *every* held column to be
    # degenerate (`ungradeable_scenes`), which entails the TVaR column is —
    # so the `excited` guard above is strictly *stronger* than the gate, and a
    # `None` branch below it could never be reached. D-397 called this
    # precondition "unrelated"; it is unrelated in *subject* but not
    # independent in *extension*. The `None` in `second_clears_floor` is
    # therefore a guard for callers that do not come through here.
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


#: Columns whose per-seed ensembles are pinned somewhere on the branch, and the
#: module holding each. The screen below reads these and nothing else — a scene
#: absent from a column's harvest is not *degenerate* there, it is **unmeasured**
#: there, and the two must not print the same way.
SCREENABLE_COLUMNS: tuple[str, ...] = ("cte_max", "clearance")


def screen() -> dict[tuple[str, str], int]:
    """`(column, scene) -> distinct arm rows`, over every pinned ensemble.

    STATE's next-action #1 asked for this on "the six unharvested scenarios",
    on the premise that it "costs zero rollouts wherever a `cte_max` ensemble is
    already pinned". The premise is sound and the conjunction is empty — see
    :func:`free_screen_gap`. What the screen *can* reach for free is the
    `clearance` column, which is a different question than the one asked and the
    only one the pinned data answers.
    """
    from . import scene_transfer

    out: dict[tuple[str, str], int] = {}
    for scene, ens in excursion_seed_width.SEED_ENSEMBLE.items():
        out[("cte_max", scene)] = distinct_arms(ens)
    for scene, ens in scene_transfer._COLUMNS.items():
        out[("clearance", scene)] = distinct_arms(ens)
    return out


def free_screen_gap() -> tuple[str, ...]:
    """Scenes the cross-track screen cannot reach without buying rollouts.

    The correction this function exists to carry: `cte_max` is pinned on exactly
    the two scenes already harvested, so *every* scene the screen was aimed at is
    outside it. "Screen the six for free" is not a cheaper version of harvesting
    them — it is the same purchase (`excursion_seed_width.REMAINING_DEBT`) under
    a different name, and a cycle that reads next-action #1 without this will
    plan a free step that does not exist.
    """
    harvested = set(excursion_seed_width.SEED_ENSEMBLE)
    return tuple(sorted(
        scene for scene in _all_scenes() if scene not in harvested))


def _all_scenes() -> tuple[str, ...]:
    """Scenario ids the matrix is defined over, from the yaml directory."""
    from pathlib import Path

    root = Path(__file__).resolve().parents[2] / "eval" / "scenarios"
    return tuple(sorted(
        p.stem for p in root.glob("*.yaml") if p.stem != "lam_windows"))


def degenerate_cells() -> tuple[tuple[str, str], ...]:
    """Pinned cells that cannot grade a between-arm claim, over both columns.

    STATE's next-action #2 — "audit whether `clearance` columns rest on
    degenerate cells" — is answered here rather than in a module of its own,
    because it is the same predicate D-385 already wrote and the answer is only
    interesting beside the cross-track one.
    """
    return tuple(sorted(cell for cell, n in screen().items()
                        if n < MIN_DISTINCT_ARMS))


def full_screen() -> dict[tuple[str, str], int]:
    """:func:`screen`, plus the two columns it cannot reach.

    :func:`screen` covers `cte_max` (via `excursion_seed_width.SEED_ENSEMBLE`)
    and `clearance`; it does not see the TVaR ensembles this module pins
    directly, nor `cte_max` re-read at the operating point. Scene-level
    questions need all four, because "this scene grades nothing" is false the
    moment *any* held column separates its arms.

    Derived from the pins themselves rather than listed, so a fifth column
    lands here by being pinned.
    """
    out = dict(screen())
    for scene, ens in ((SCENE, TVAR_ENSEMBLE),
                       (SECOND_SCENE, TVAR_ENSEMBLE_SECOND),
                       (THIRD_SCENE, TVAR_ENSEMBLE_THIRD)):
        out[(f"TVaR_{Q}", scene)] = distinct_arms(ens)
    for scene, ens in CTE_MAX_AT_OPERATING_POINT.items():
        out[("cte_max@op", scene)] = distinct_arms(ens)
    return out


def ungradeable_scenes() -> tuple[str, ...]:
    """Scenes where **every** column this harness holds is degenerate.

    The claim D-392 reached and could not state: degeneracy on
    :data:`SECOND_SCENE` is a property of the *scene*. `second_verdict` says it
    of the TVaR column, `aligned_second_verdict` says it of `cte_max` at the
    operating point, and `aa_calibration.degenerate_tally_rows` says it of the
    tally row — three statements of one fact, none of which forbids the next
    cycle from buying a *fourth* cell here. This does: a scene in this tuple
    separates fewer than :data:`MIN_DISTINCT_ARMS` arms in every column held,
    so no observable measured on it can grade a between-arm claim, and no
    harvest changes that.

    Derived from :func:`full_screen`, never typed — a scene leaves this set by
    a column separating, which is exactly the event that should release it.
    """
    by_scene: dict[str, list[int]] = {}
    for (_column, scene), n in full_screen().items():
        by_scene.setdefault(scene, []).append(n)
    return tuple(sorted(scene for scene, counts in by_scene.items()
                        if all(n < MIN_DISTINCT_ARMS for n in counts)))


def scene_scoped_claims(scene: str = SECOND_SCENE) -> dict[str, str]:
    """`callable -> RETIRED | LOAD_BEARING` for this module's claims about `scene`.

    The audit half of the TODO, done by reading this module's own source rather
    than by typing a list of names — a typed list is the thing that goes stale
    the cycle after it is written (D-072), and this one would have to be
    re-checked every time a `second_*` helper is added.

    A claim is **RETIRED** if its body already says the cell decides nothing
    (`UNTESTABLE` / `UNGRADEABLE` appear in its source). It is **LOAD_BEARING**
    if it still returns a number or a bool computed on the degenerate cell —
    those are the dangerous ones, because they read like results. On
    :data:`SECOND_SCENE` the load-bearing set is not empty: `second_ratio`,
    `second_baseline_ratio` and `aligned_second_is_gradeable` each return a
    statistic over a population of two, and :func:`report` prints the first two
    beside the gradeable scenes' numbers with nothing marking the difference.

    The audit is **direct, not transitive**: `second_clears_floor` is just as
    load-bearing but reads the cell through `second_ratio` rather than naming a
    pin, so it does not appear. Stated rather than fixed — a call-graph walk
    would catch it and would also drag in every caller of `report`, and the
    direct set is the one a cycle can act on.

    Two things make the detection worth more than a grep for the scene id.
    A claim reaches the scene through the *symbol its ensemble is pinned under*
    (`second_ratio` names `TVAR_ENSEMBLE_SECOND` and never `SECOND_SCENE`), so
    the aliases are resolved by identity against the pins — missing
    `second_ratio` would have missed the one :func:`report` prints. And a
    function that names this scene *beside the others* is enumerating, not
    claiming: :func:`full_screen` and :func:`format_census` walk every scene,
    so requiring the other scenes' aliases to be **absent** drops them without
    a hand-maintained exclusion list.

    Only callables defined in this module are audited; the pinned data
    (:data:`ALIGNED_SECOND`, :data:`ALIGNED_SECOND_AGREEMENT`) carries its own
    caveat in prose and has no body to read.
    """
    import inspect
    import re
    import sys

    retired_markers = ("UNTESTABLE", "UNGRADEABLE")
    module = sys.modules[__name__]
    members = vars(module)

    def mentions(body: str, names: set[str]) -> bool:
        """Whole-symbol match. Plain `in` is wrong here and silently so: every
        alias of this scene *contains* an alias of another (`SCENE` inside
        `SECOND_SCENE`, `TVAR_ENSEMBLE` inside `TVAR_ENSEMBLE_SECOND`), so a
        substring test scores every `second_*` claim as an enumerator and
        returns an empty audit that reads exactly like a clean one.
        """
        return any(re.search(rf"\b{re.escape(n)}\b", body) for n in names)

    pins: dict[str, list[object]] = {}
    for s, ens in ((SCENE, TVAR_ENSEMBLE), (SECOND_SCENE, TVAR_ENSEMBLE_SECOND),
                   (THIRD_SCENE, TVAR_ENSEMBLE_THIRD)):
        pins.setdefault(s, []).append(ens)

    def aliases(target: str) -> set[str]:
        """Module symbols that denote `target` — the id, and its pinned cells."""
        out = {repr(target)}
        out |= {n for n, v in members.items()
                if isinstance(v, str) and v == target}
        out |= {n for n, v in members.items()
                if any(v is pin for pin in pins.get(target, ()))}
        return out

    mine = aliases(scene)
    others: set[str] = set()
    for s in pins:
        if s != scene:
            others |= aliases(s)

    out: dict[str, str] = {}
    for name, obj in members.items():
        if name.startswith("_") or not inspect.isfunction(obj):
            continue
        if getattr(obj, "__module__", None) != __name__:
            continue
        try:
            src = inspect.getsource(obj)
        except OSError:  # pragma: no cover - source always available in-tree
            continue
        body = src.split('"""')[-1] if src.count('"""') >= 2 else src
        if not mentions(body, mine):
            continue
        if mentions(body, others):
            continue  # enumerating every scene, not claiming about this one
        out[name] = ("RETIRED" if any(m in body for m in retired_markers)
                     else "LOAD_BEARING")
    return out


def ungradeable_scene_verdict(scene: str = SECOND_SCENE) -> str:
    """One line stating what the scene grades, and what still reads off it."""
    if scene not in ungradeable_scenes():
        return f"GRADEABLE: {scene} separates arms in at least one held column"
    columns = sorted(column for (column, s), n in full_screen().items()
                     if s == scene and n < MIN_DISTINCT_ARMS)
    claims = scene_scoped_claims(scene)
    load = sorted(n for n, disposition in claims.items()
                  if disposition == "LOAD_BEARING")
    return (f"UNGRADEABLE_SCENE: {scene} separates < {MIN_DISTINCT_ARMS} arms "
            f"in all {len(columns)} held columns ({', '.join(columns)}) — buy "
            f"no further cells here; {len(load)} of {len(claims)} scoped "
            f"claims still return a statistic over it ({', '.join(load)})")


CLAIM_MARK = "‡"


def scene_mark(scene: str) -> str:
    """The mark every statistic scoped to `scene` must carry at a print site.

    Derived from :func:`ungradeable_scenes`, so a scene starts carrying the
    mark — and stops — on exactly the event that puts it in or out of that
    tuple. Nothing here names a scene, which is why the first and third
    endpoints are already covered should a later harvest flatten one of them.
    """
    return CLAIM_MARK if scene in ungradeable_scenes() else ""


def marked(value: float | None, scene: str) -> str:
    """A census ratio carrying its scene's gradeability mark.

    The gap D-393 named and did not close. :func:`scene_scoped_claims` knew
    which helpers return a statistic over a population of two;
    :func:`format_census` printed those floats in the same `x.xx` column as the
    gradeable endpoints' with nothing distinguishing them, so the knowledge
    stopped at the audit and never reached a reader. Routing *every* endpoint's
    ratios through here makes the mark structural rather than remembered: a
    print site cannot drop it without dropping the formatter, and
    :func:`unmarked_print_sites` counts the ones that did.
    """
    if value is None:
        # The Q-176(b) case: the claim refused to return a number at all. The
        # column still has to hold its width, and the mark still has to be
        # there — an unreadable cell that printed blank would read as a
        # formatting gap rather than as a refusal.
        return f"{'--':>7s}{scene_mark(scene) or ' '}"
    return f"{value:>6.2f}x{scene_mark(scene) or ' '}"


def printed_load_bearing(scene: str = SECOND_SCENE) -> tuple[str, ...]:
    """LOAD_BEARING claims about `scene` that :func:`format_census` calls.

    The subset of the audit that reaches a reader — `aligned_second_is_gradeable`
    is just as load-bearing but is not printed, so marking it would be marking
    nothing. Read off the census's source rather than typed, for the same
    reason the audit itself is (D-072): a fourth `second_*` helper joins this
    set by being called, not by someone remembering to list it.
    """
    import inspect
    import re

    src = inspect.getsource(format_census)
    return tuple(sorted(
        name for name, disposition in scene_scoped_claims(scene).items()
        if disposition == "LOAD_BEARING"
        and re.search(rf"\b{re.escape(name)}\s*\(", src)))


def bare_print_sites(scene: str = SECOND_SCENE) -> tuple[str, ...]:
    """The raw source scan: census call sites that bypass :func:`marked`.

    Counted **per call site**, not per name. Each marked helper is printed
    twice (lenient and strict), and one wrapped call beside one bare one is
    exactly the half-done marking this closes — a name-level check would score
    that clean, which is the failure mode the whole audit exists to avoid.

    Split out of :func:`unmarked_print_sites` (D-396) so the *precondition* and
    the *scan* return their empty tuples for distinguishable reasons. Both read
    `()`; only one of them is a finding of no defect, and D-394 already paid for
    the lesson that an empty population reads exactly like a clean one.
    """
    import inspect
    import re

    src = inspect.getsource(format_census)
    out = []
    for name in printed_load_bearing(scene):
        total = len(re.findall(rf"\b{re.escape(name)}\s*\(", src))
        wrapped = len(re.findall(rf"marked\(\s*{re.escape(name)}\s*\(", src))
        if wrapped != total:
            out.append(f"{name}: {total - wrapped} of {total} call site(s) bare")
    return tuple(out)


def unmarked_print_sites(scene: str = SECOND_SCENE) -> tuple[str, ...]:
    """Bare census call sites *that were supposed to carry a mark*.

    The precondition is the whole of D-396. Without it the detector scanned
    every scene alike and reported `baseline_ratio: 1 of 3 call site(s) bare`
    on `cafe_convoy_v0` — a **false** finding, because `scene_mark` returns `""`
    there, so `marked(v, scene)` and a bare `f"{v:.2f}"` differ by a space and
    carry the same information. There is no mark for a gradeable scene's print
    site to have dropped. Five such findings stood on `SCENE` and two on
    `THIRD_SCENE`, none of them defects, and the only reason `drift()` stayed
    green is that it happened to ask about the one scene where the reading was
    accidentally right.

    Deriving the gate from :func:`scene_mark` rather than from
    :func:`ungradeable_scenes` directly keeps the detector and the formatter
    answering the *same* question: the sites this flags are exactly the sites
    where `marked` would have printed something a bare call does not.
    """
    if not scene_mark(scene):
        return ()
    return bare_print_sites(scene)


#: Directories that can hold a Python caller. `build/` and `install/` are
#: colcon output (copies of `src/`) and would double-count; `.github/` holds
#: workflow helpers that import nothing from here.
SOURCE_ROOTS: tuple[str, ...] = ("eval", "src")


def citation_sites(scene: str = SECOND_SCENE) -> tuple[str, ...]:
    """Call sites of `scene`'s LOAD_BEARING claims *outside this module*.

    The population Q-176 asked for, and the half :func:`unmarked_print_sites`
    is constitutionally unable to see: that detector scans :func:`format_census`
    only, so it grades the one print site this module owns. A caller in another
    module receives the same bare float and no guard on this branch looks at it
    — which is the asymmetry the whole question turns on. A mark lives at a
    print site; a **return value travels**.

    Each entry is `path:line: name`, counted per call site rather than per name
    for the reason :func:`bare_print_sites` is (one cited call beside one
    marked one is exactly the half-done case a name-level check scores clean).

    Derived by scanning the source roots' `*.py` rather than by listing the
    modules that are allowed to call — same reason as D-072/D-047. A caller
    joins this set by *existing*, not by someone remembering to register it.

    :data:`SOURCE_ROOTS` rather than the repo root, and the difference is not
    cosmetic. The first cut here rglob'd from the root, which made this module
    a **reader of the whole tree**: `inert_surface staged` immediately reported
    five withdrawn pins (`JOURNAL.md`, `RESULTS.md`, `STATE.md`, `journal/`,
    `results/`) and the D-044 tax that comes with them. Those paths hold no
    Python and can never contain a caller, so the breadth bought nothing and
    cost a second suite run. A census should read exactly its population.
    """
    import pathlib
    import re

    here = pathlib.Path(__file__).resolve()
    names = sorted(n for n, disposition in scene_scoped_claims(scene).items()
                   if disposition == "LOAD_BEARING")
    if not names:
        return ()
    pattern = re.compile(rf"\b({'|'.join(re.escape(n) for n in names)})\s*\(")

    out = []
    root = here.parent.parent.parent
    candidates = [p for d in SOURCE_ROOTS for p in (root / d).rglob("*.py")]
    for path in sorted(candidates):
        if path.resolve() == here:
            continue
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except OSError:  # pragma: no cover - unreadable file in-tree
            continue
        for lineno, line in enumerate(lines, 1):
            for hit in pattern.finditer(line):
                rel = path.relative_to(root)
                out.append(f"{rel}:{lineno}: {hit.group(1)}")
    return tuple(out)


def uncited_by_tests_only(scene: str = SECOND_SCENE) -> tuple[str, ...]:
    """The finding half of :func:`citation_sites` — non-test external callers.

    A **test** reading one of these floats is the audit working: it asserts the
    number *as* a statistic over an ungradeable cell, and the assertion is what
    keeps the degeneracy pinned. Production code reading it is the citation
    accident the mark cannot prevent.

    Measured 2026-08-21: this returns `()` while :func:`citation_sites` returns
    **eight**, across `tests/test_tail_mean.py` (7) and
    `tests/test_column_alignment.py` (1). That measurement is what answers
    Q-176 — see D-397.

    The count is also the D-072 lesson landing a second time. Q-176 named two
    helpers and asked for a grep of them; the derived census reports three,
    because `aligned_second_is_gradeable` is equally LOAD_BEARING and has an
    external caller the hand-typed pair could not have found. The question's
    own scope was one member short of its own population.

    Read this together with :func:`citation_sites`: an empty return here means
    "no production caller" only when the scan behind it is non-empty, and
    D-394 already paid once for an empty population reading exactly like a
    clean one.
    """
    return tuple(s for s in citation_sites(scene)
                 if "test" not in pathlib_stem(s))


def pathlib_stem(entry: str) -> str:
    """The path half of a `path:line: name` entry from :func:`citation_sites`."""
    return entry.split(":", 1)[0]


def both_columns_scenes() -> tuple[str, ...]:
    """Scenes carrying a pinned ensemble in *both* screenable columns.

    The population any "clearance excitation predicts cross-track excitation"
    inference would have to rest on. It has **two** members since
    `cafe_head_on_v0` was harvested, and both agree — which is still not
    evidence for the inference, because neither member had a chance to
    disagree: a scene is only in this set once its cross-track column has been
    *bought*, so the set can never contain the falsifying case (clearance
    excited, cross-track degenerate and unharvested). :data:`SCREEN_VERDICT`
    therefore still calls the clearance result an ordering hint and not a
    licence to skip a harvest.
    """
    from . import scene_transfer

    return tuple(sorted(set(excursion_seed_width.SEED_ENSEMBLE)
                        & set(scene_transfer._COLUMNS)))


#: What the screen leaves standing, pinned against prose drift for the same
#: reason as :data:`CLAIM_FORM`: the tempting misreading is that five excited
#: clearance cells supply five candidate cross-track endpoints, and they do not.
SCREEN_VERDICT: str = (
    "every pinned clearance cell is excited and no cross-track cell outside the "
    "three already harvested is pinned at all; the clearance result orders which "
    "scene to harvest next, it does not license grading one without the harvest"
)


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
    if column_licensed() and not excited(TVAR_ENSEMBLE_THIRD):
        bad.append("column_licensed() is True on a degenerate third endpoint")
    # The third endpoint has no cte_max column to be checked against — that is
    # exactly what third_paired() reports — so its arms are checked against the
    # controller registry the harvest actually walked.
    if set(TVAR_ENSEMBLE_THIRD) != set(TVAR_ENSEMBLE):
        bad.append(f"TVAR_ENSEMBLE_THIRD arms != the arms graded on {SCENE}")
    for arm, row in TVAR_ENSEMBLE_THIRD.items():
        if len(row) != SEEDS:
            bad.append(f"{THIRD_SCENE}/{arm}: {len(row)} seeds, expected {SEEDS}")
    if third_paired() != (THIRD_SCENE in excursion_seed_width.SEED_ENSEMBLE):
        bad.append("third_paired() disagrees with the pinned cte_max harvest")
    if third_paired() and "UNPAIRED" in third_verdict():
        bad.append("third_verdict() calls the endpoint unpaired while a "
                   f"cte_max ensemble is pinned on {THIRD_SCENE}")
    if not third_paired() and THIRD_SCENE not in free_screen_gap():
        bad.append(f"{THIRD_SCENE} is unpaired but the screen does not list it "
                   "as unreachable for cte_max")
    # Re-priced (D-391). This clause used to *require* the string
    # "cafe_convoy_v0 only" — the scene-specific reading of the contrast — so
    # the guard was itself one of the sites quoting a cross-experiment claim,
    # and it would have gone red on any correct re-wording. The caveat it now
    # demands is the aligned one, and it is checked against the count rather
    # than against a remembered phrase: a wording that says "zero" while
    # ALIGNED_CELLS says otherwise is the drift worth catching.
    if column_licensed() and "survives on zero cells" not in COLUMN_CLAIM_FORM:
        bad.append("COLUMN_CLAIM_FORM drops the aligned contrast retraction")
    if (aligned_contrast_count() == 0) is not (
            "survives on zero cells" in COLUMN_CLAIM_FORM):
        bad.append("COLUMN_CLAIM_FORM's contrast count disagrees with "
                   f"ALIGNED_CELLS ({aligned_contrast_count()} cell(s) miss)")
    if (aligned_dominance_count() == len(ALIGNED_CELLS)) is not (
            "grades above cte_max on both" in COLUMN_CLAIM_FORM):
        bad.append("COLUMN_CLAIM_FORM's dominance wording disagrees with "
                   f"ALIGNED_CELLS ({aligned_dominance_count()}"
                   f"/{len(ALIGNED_CELLS)})")
    # NOTE (D-388): the COMPARABLE_CELLS consistency checks live in
    # `test_comparable_cells_are_the_live_readings_not_a_restatement` and not
    # here, and the reason is a measurement rather than a preference. Written as
    # `drift()` clauses they gave this function a difference-shaped population
    # (`guard_reflexivity.KIND_DIFFERENCE`), which promoted `tail_mean.drift`
    # into `revocable_collections()` — a pool every member of which owes
    # `guard_direction.PROBES` an executed direction reading. It had none, so
    # `unprobed_revocable()` went from `()` to `('tail_mean.drift',)` and took
    # 12 tests down across three modules. The checks are worth the same in the
    # test layer, which is where every other pin on this module is verified.
    if ("cte_max", SECOND_SCENE) not in degenerate_cells():
        bad.append(f"the screen does not see {SECOND_SCENE}/cte_max as "
                   "degenerate, but second_verdict() calls it UNTESTABLE")
    if set(both_columns_scenes()) - set(excursion_seed_width.SEED_ENSEMBLE):
        bad.append("both_columns_scenes() names a scene with no cte_max harvest")
    # D-396: iterate the pin, not the default argument. This clause used to ask
    # `unmarked_print_sites()` — `SECOND_SCENE` and nothing else — so the check
    # was pinned to whichever scene happened to be ungradeable when it was
    # written. Had a later harvest flattened `cafe_convoy_v0`, `marked()` would
    # have started marking it (`scene_mark` is derived) while this guard went on
    # reading `city_curved_v0`, and the census could have printed a bare
    # ungradeable ratio with drift() green. Iterating `ungradeable_scenes()`
    # makes the guard's population the same one the mark is derived from.
    for ungradeable in ungradeable_scenes():
        for site in unmarked_print_sites(ungradeable):
            bad.append("the census prints a load-bearing claim bare — "
                       f"{ungradeable}/{site}")
    for scene in free_screen_gap():
        if ("cte_max", scene) in screen():
            bad.append(f"{scene} is called unscreenable while its cte_max "
                       "ensemble is pinned")
    return tuple(bad)


def format_census() -> str:
    """The census as the branch's other floor readings print it."""
    lines = [
        f"tail_mean — {SCENE}, TVaR_{Q}, {SEEDS} seeds x {len(TVAR_ENSEMBLE)} arms",
        "",
    ]
    if ungradeable_scenes():
        lines += [
            f"  {CLAIM_MARK} marks a ratio measured on an ungradeable scene — "
            f"fewer than {MIN_DISTINCT_ARMS} distinct arms in every column the "
            f"harness holds, so the number grades nothing no matter how it "
            f"reads: {', '.join(ungradeable_scenes())}",
            "",
        ]
    lines += [
        f"  {'column':12s} {'real gap':>9} {'p95 floor':>10} {'max floor':>10}"
        f" {'vs p95':>7} {'vs max':>7}",
        f"  {'cte_max':12s} "
        f"{aa_calibration.real_gap('cte_max', SCENE):>9.4f} "
        f"{aa_calibration.p95_floor('cte_max', SCENE):>10.4f} "
        f"{aa_calibration.max_floor('cte_max', SCENE):>10.4f} "
        f"{marked(baseline_ratio(), SCENE)}{marked(baseline_ratio(True), SCENE)}",
        f"  {f'TVaR_{Q}':12s} {real_gap():>9.4f} {p95_floor():>10.4f} "
        f"{max_floor():>10.4f} {marked(ratio(), SCENE)}"
        f"{marked(ratio(True), SCENE)}",
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
        f"    {'cte_max':12s} {marked(second_baseline_ratio(), SECOND_SCENE)}"
        f"{marked(second_baseline_ratio(True), SECOND_SCENE)}",
        f"    {f'TVaR_{Q}':12s} {marked(second_ratio(), SECOND_SCENE)}"
        f"{marked(second_ratio(True), SECOND_SCENE)}",
        f"    distinct arm rows: {distinct_arms(TVAR_ENSEMBLE_SECOND)}"
        f"/{len(TVAR_ENSEMBLE_SECOND)} (need {MIN_DISTINCT_ARMS})",
        f"    {second_verdict()}",
        "",
        f"  third endpoint — {THIRD_SCENE}, TVaR_{Q}, {SEEDS} seeds x "
        f"{len(TVAR_ENSEMBLE_THIRD)} arms",
        f"    {'cte_max':12s} {marked(third_baseline_ratio(), THIRD_SCENE)}"
        f"{marked(third_baseline_ratio(True), THIRD_SCENE)}" if third_paired() else
        f"    {'cte_max':12s}  (unpaired — no ensemble pinned)",
        f"    {f'TVaR_{Q}':12s} {marked(third_ratio(), THIRD_SCENE)}"
        f"{marked(third_ratio(True), THIRD_SCENE)}",
        f"    distinct arm rows: {distinct_arms(TVAR_ENSEMBLE_THIRD)}"
        f"/{len(TVAR_ENSEMBLE_THIRD)} (need {MIN_DISTINCT_ARMS})",
        f"    {third_verdict()}",
        "",
        f"  CONTRAST REPLICATES: {contrast_replicates()} — at the aligned "
        f"operating point the cte_max-fails half of finding #1 holds on "
        f"{aligned_contrast_count()}/{len(ALIGNED_CELLS)} comparable cells",
        f"  DOMINANCE (aligned): {dominance_at_operating_point()} — TVaR_{Q} "
        f"grades above cte_max on {aligned_dominance_count()}"
        f"/{len(ALIGNED_CELLS)}",
    ] + [
        f"    {scene:26s} TVaR {tv:.2f}x  vs  cte_max {base:.2f}x"
        f"   (retired: cte_max {COMPARABLE_CELLS[scene][1]:.2f}x)"
        for scene, (tv, base) in sorted(ALIGNED_CELLS.items())
    ] + [
        "",
        "  RETIRED BY THE REALIGNMENT (D-390) — quoted here so a reader of the",
        "  numbers above cannot reach them without the retraction:",
    ] + [
        f"    {name}\n      was: {was}\n      now: {now}"
        for name, was, now in RETIRED_BY_ALIGNMENT
    ] + [
        f"  COLUMN-LEVEL CLAIM LICENSED: {column_licensed()}",
        f"    {COLUMN_CLAIM_FORM}",
        "",
        f"  excitation screen — {len(screen())} pinned cells, "
        f"need {MIN_DISTINCT_ARMS} distinct arm rows",
    ]
    for (column, scene), n in sorted(screen().items()):
        mark = "ok " if n >= MIN_DISTINCT_ARMS else "DEGENERATE"
        lines.append(f"    {column:9s} {scene:26s} {n}/8  {mark}")
    lines += [
        f"    unscreenable for cte_max (no pinned ensemble): "
        f"{len(free_screen_gap())} scenes, "
        f"{excursion_seed_width.REMAINING_DEBT} rollouts",
        f"    scenes pinned in both columns: {both_columns_scenes()}",
        f"    {SCREEN_VERDICT}",
    ]
    if drift():
        lines += ["", "  DRIFT:"] + [f"    {b}" for b in drift()]
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if "--retake-max" in argv:
        # The operator entry point for re-deriving CTE_MAX_AT_OPERATING_POINT.
        # Wired rather than left as a residue: Q-175's defect was a pin with no
        # executable path back to its own construction.
        import json
        scenes = [a for a in argv if not a.startswith("-")] or \
            sorted(CTE_MAX_AT_OPERATING_POINT)
        print(json.dumps({s: retake_max(scene=s) for s in scenes}, indent=1))
        return 0
    print(format_census())
    return 1 if drift() else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

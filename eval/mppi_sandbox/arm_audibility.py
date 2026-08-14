# SPDX-License-Identifier: BSD-3-Clause
"""Is an `arm_freeze` arm's epistemic channel audible against the costs it joins?

D-263 froze Q-148's four arms and named `ARM_SCALE` as the one input with no
measurement behind it: the ratio decides the cost field's *sign*, but the scale
decides whether the epistemic channel is heard at all next to the obstacle and
path terms already in `_cost`. If it is not, every arm is the control and the
A/B is vacuous before the scene arrives. This module answers that question and
nothing else.

## It measures nothing itself — that instrument already exists

`weight_units.measure` prices any additive coefficient in units of the cost it
competes against, by zeroing the weight and re-evaluating the real `_cost`
(leave-one-out, no second copy of the cost formula). `w_epist` and `w_voo` are
both in its `ADDITIVE_WEIGHTS`, so the audibility question is that module's
`ratio` read on the two channels an `Arm` sets. This module supplies the arm,
the verdict vocabulary, and the inversion; re-deriving the spread here would be
the D-047 failure — one quantity, two statements that can drift apart.

## The verdict, and the threshold it rests on

`AUDIBLE_RATIO = 0.1` — a channel is `AUDIBLE` when its per-sample spread is at
least a tenth of the rest of the cost's spread. **This is a declared
convention, not a measurement**, which is why it is a module constant and a
keyword argument rather than a number buried in a comparison: D-024's failure
class is a screen driven by a quantity nobody declared. :func:`grade` returns
the raw ratio alongside the verdict so a caller can apply their own bar without
re-running, and `threshold` is echoed in the result for the same reason.

Between `SILENT` and `AUDIBLE` sits `FAINT` — live, but under the bar. The
distinction is load-bearing for the next section: `FAINT` is a statement about
the *scale*, and rescalable; `SILENT` is a statement about the *scene*, and is
not.

## Why a zero spread does not get a required scale

The spread is linear in the weight for an additive coefficient
(`weight_units.unit_spread_is_linear`), and that linearity is the whole licence
for inverting the ratio into "the scale at which this channel would clear the
bar" — multiply the exchange rate, do not re-run. But the inversion divides by
the exchange rate, and a channel whose spread is *identically zero* has an
exchange rate of zero: no finite scale makes it audible, because scaling zero
is zero. :attr:`ChannelAudibility.required_weight` is therefore `None` for a
`SILENT` channel rather than `inf` or some large number, and the tests pin it.
Reporting a number there would be the D-241 shape exactly — a null dressed as a
quantity, in the direction that flatters the experiment.

## What was measured, and the scene it was not measured on

At `ARM_SCALE = 1.0`, on the scenes this branch can run:

- **`w_voo` (attract) is `FAINT`** — ratio `0.0184` on `cafe_obstacle_crossing_v0`,
  `0.0229` on `cafe_freezing_v0`, `0.0233` on `cafe_cut_in_v0`, against `w_path`
  at `1.98`–`2.20`. Roughly two orders of magnitude down on the dominant
  baseline term, and it clears the bar only near `scale ≈ 54`.
- **`w_epist` (repel) is `SILENT`** — spread exactly `0.0` on *every* scene
  available here, at both `w_epist = 1.0` (`REPEL_ONLY`) and `0.2918`
  (`BOTH_ON`). It is the D-021 reading again: the shadow critic prices a shadow,
  and none of these scenes casts one.

The scene the A/B actually runs on — `cafe_blind_corner_v0` — is on unmerged
PR #68, so it is **quoted, never imported** (the same feasibility boundary
`ratio_pick` holds for `SCENE_RADIUS`). That makes the `SILENT` reading above
strictly a statement about the scenes without an occluder, and
:func:`scene_caveat` returns it as data with `recheck_on_merge: True`. D-260 and
D-262 both caught this branch over-transferring a cost-field reading across
geometry; the attract channel's `FAINT` has three scenes behind it and is the
more transferable of the two, but neither is a reading of the A/B scene.

## And the weight that fixes `FAINT` is a property of the scene (D-266)

D-265 read the `w_voo` ladder on one scene and reported a shape. Re-taken on the
other two, the shape is that scene's and not the ratio's — `cafe_freezing_v0`
and `cafe_cut_in_v0` both rise **monotonically** through `w=200` with no
collapse, while `cafe_obstacle_crossing_v0`'s `rest_median` jumps `87×` in its
last step alone. Worse for Q-148, the bar is crossed at three weights that do
not overlap: `(1, 5]` on `freezing`, `(5, 8]` on `crossing`, `(50, 200]` on
`cut_in`. :func:`common_audible_weights` is therefore **empty** on the measured
points — and `ARM_SCALE` is one number every run of the A/B shares. So the
audit's conclusion is not a scale but a scope: no scale measured here transfers,
and the only reading that would settle Q-148 is one taken on `AB_SCENE`, which
is on unmerged PR #68. See :func:`scale_is_per_scene`.
"""

from __future__ import annotations

from dataclasses import dataclass

from .arm_freeze import ARM_SCALE, Arm, freeze
from .weight_units import measure

#: A channel is AUDIBLE at or above this multiple of the rest-of-cost spread.
#: Declared convention, not a measurement — see the module docstring.
AUDIBLE_RATIO = 0.1

#: The two channels an arm sets, in `arm_freeze`'s reporting order.
EPISTEMIC_CHANNELS = ("w_epist", "w_voo")

AUDIBLE = "AUDIBLE"
FAINT = "FAINT"
SILENT = "SILENT"

#: The A/B scene, quoted rather than imported — it lives on unmerged PR #68.
AB_SCENE = "cafe_blind_corner_v0"


@dataclass(frozen=True)
class ChannelAudibility:
    """One channel's verdict on one (arm, scene), plus what would change it."""

    channel: str
    weight: float
    ratio: float
    spread_per_unit_weight: float
    threshold: float
    verdict: str

    @property
    def required_weight(self) -> float | None:
        """The **channel weight** at which this channel would clear the bar.

        A **prediction, not a measurement** — see :func:`window_verdict`. The
        linear inversion is exact for a fixed rollout batch, but this ratio's
        denominator is the rest of the cost *on the run the weight produced*,
        and the weight moves the run. Measured against the ladder it overstates
        by up to :func:`inversion_error`, and the ratio is not even monotone in
        the weight, so this number is an optimistic lower bound on the weight
        to try first — not the weight that works.

        `None` for a `SILENT` channel: the exchange rate is zero, so no finite
        weight lifts it. See the module docstring's fourth section for why this
        is not `inf`.

        This is a weight, **not** an `ARM_SCALE`. The two coincide only on a
        single-channel arm, where the arm spends all its authority here; on
        `BOTH_ON` this channel holds a `1/(1+ratio)` share of the scale, so
        converting needs :func:`required_arm_scale` and not this number
        directly. Naming it `required_scale` — as this property briefly was —
        is the D-047 defect the branch has now caught three times: one quantity
        wearing two names until they drift.
        """
        if self.verdict == SILENT or self.ratio == 0.0:
            return None
        return float(self.weight * self.threshold / self.ratio)

    @property
    def is_rescalable(self) -> bool:
        """Would a different `ARM_SCALE` change this verdict?"""
        return self.verdict != SILENT

    def __str__(self) -> str:
        need = ("—" if self.required_weight is None
                else f"{self.required_weight:.4g}")
        return (f"{self.channel:<8} w={self.weight:<7.4g} "
                f"ratio={self.ratio:<9.4g} {self.verdict:<8} "
                f"needs weight {need}")


def required_arm_scale(channel: ChannelAudibility, arm: Arm) -> float | None:
    """`ARM_SCALE` at which `channel` clears its bar on `arm` — or `None`.

    `required_weight` divided by the share of the arm's authority this channel
    holds. The share is read off the arm rather than recomputed from the ratio,
    so an `arm_freeze` normalisation change (Q-150's live alternative) cannot
    leave this function quietly describing the old table.
    """
    need = channel.required_weight
    if need is None or not arm.is_active:
        return None
    share = getattr(arm, channel.channel) / arm.authority
    return None if share == 0.0 else float(need / share)


def _verdict(ratio: float, threshold: float) -> str:
    if ratio == 0.0:
        return SILENT
    return AUDIBLE if ratio >= threshold else FAINT


def grade(scenario, arm: Arm, *, seed: int = 0,
          threshold: float = AUDIBLE_RATIO,
          **measure_kwargs) -> dict[str, ChannelAudibility]:
    """Grade `arm`'s two epistemic channels on `scenario`.

    Channels the arm leaves at zero weight are absent from the result: they are
    off by the arm's definition, and a verdict on them would be a fact about the
    table, not a measurement. `k_margin_per_sigma` is forced to 0 — it is not an
    additive coefficient, and `weight_units.measure` refuses to report a table
    while it is live, since every other row would be conditional on it.
    """
    measure_kwargs.setdefault("k_margin_per_sigma", 0.0)
    spreads = measure(scenario, "risk_mppi", seed=seed,
                      **arm.as_config(), **measure_kwargs)
    out = {}
    for channel in EPISTEMIC_CHANNELS:
        term = spreads.get(channel)
        if term is None:          # weight is 0 on this arm — not measured
            continue
        out[channel] = ChannelAudibility(
            channel=channel,
            weight=term.weight,
            ratio=term.ratio,
            spread_per_unit_weight=term.spread_per_unit_weight,
            threshold=threshold,
            verdict=_verdict(term.ratio, threshold),
        )
    return out


def arm_is_audible(graded: dict[str, ChannelAudibility]) -> bool:
    """Does *any* channel of this arm clear the bar?

    `any`, not `all`: an arm whose one live channel is heard is not vacuous,
    and `BOTH_ON` would otherwise be graded by its quieter half.
    """
    return any(c.verdict == AUDIBLE for c in graded.values())


def ab_is_vacuous(per_arm: dict[str, dict[str, ChannelAudibility]]) -> bool:
    """Is every active arm inaudible — i.e. is the A/B all control?

    The question D-263 raised. `True` means each arm differs from `CONTROL` by
    a cost term the softmax cannot hear, so the arms' outcomes differ only by
    sampling noise no matter which scene they run on.
    """
    graded = [g for g in per_arm.values() if g]
    return bool(graded) and not any(arm_is_audible(g) for g in graded)


def scene_caveat() -> dict:
    """The scope of a `SILENT` reading taken away from the A/B scene.

    Data rather than prose because the natural misreading — "the repel arm is
    silent, so the A/B is dead" — over-transfers a geometry-dependent reading,
    which is the error D-260 and D-262 each caught once on this branch.
    """
    return {
        "ab_scene": AB_SCENE,
        "ab_scene_available_here": False,
        "ab_scene_blocked_by": "PR #68 (unmerged)",
        "quoted_not_imported": True,
        "silent_reading_scope": "scenes without an occluder; the shadow critic "
                                "prices a shadow and these scenes cast none",
        "faint_reading_scope": "three scenes with live VOO geometry",
        "recheck_on_merge": True,
        "refs": ("D-021", "D-260", "D-262", "D-263"),
    }


#: Weights `w_voo` was actually swept to on `cafe_obstacle_crossing_v0`
#: (`risk_mppi`, seed 0, `w_epist=0`, `w_risk=0`, `k_margin_per_sigma=0`) —
#: the same isolation `grade` uses. Recorded rather than recomputed on import:
#: each point costs a closed-loop run (~13s), and the shape is the finding.
#: Re-take with :func:`sweep_ratio`.
MEASURED_CURVE: tuple[tuple[float, float, float], ...] = (
    # (w_voo, measured ratio, rest-of-cost median)
    (1.0,     0.022693,   117.14),
    (5.0,     0.083540,   141.177),
    (20.0,    0.371720,   134.508),
    (50.0,    0.620510,   187.850),
    (200.0,   0.048758, 10183.100),
)


def sweep_ratio(scenario, weights=(1.0, 5.0, 20.0, 50.0, 200.0), *,
                seed: int = 0,
                channel: str = "w_voo") -> tuple[tuple[float, float, float], ...]:
    """Re-take :data:`MEASURED_CURVE` — `(weight, ratio, rest_median)` per point.

    One closed-loop run per weight, so this is a minutes-scale call and no test
    runs the whole ladder. It exists so the recorded table above is a cache of
    a reproducible measurement rather than a number typed once.
    """
    out = []
    for w in weights:
        term = measure(scenario, "risk_mppi", seed=seed,
                       **{channel: float(w)},
                       **{c: 0.0 for c in EPISTEMIC_CHANNELS if c != channel},
                       w_risk=0.0, k_margin_per_sigma=0.0)[channel]
        out.append((float(w), term.ratio, term.rest_median))
    return tuple(out)


#: The `(5, 20]` bracket D-265 left open, bisected on the same scene and in the
#: same isolation. Recorded, not recomputed — four more closed-loop runs.
BISECT_CURVE: tuple[tuple[float, float, float], ...] = (
    (8.0,  0.154144, 129.749),
    (11.0, 0.190834, 154.497),
    (14.0, 0.289459, 114.542),
    (17.0, 0.276499, 146.022),
)

#: The ladder re-taken on the other two scenes with live VOO geometry, plus the
#: reference scene's ladder merged with :data:`BISECT_CURVE`. Same isolation
#: throughout (`risk_mppi`, seed 0, `w_epist=0`, `w_risk=0`, `k_margin=0`).
#: `cafe_blind_corner_v0` — the scene the A/B runs on — is absent, and that
#: absence is the finding's whole scope: see :func:`scale_is_per_scene`.
SCENE_CURVES: dict[str, tuple[tuple[float, float, float], ...]] = {
    "cafe_obstacle_crossing_v0": tuple(sorted(MEASURED_CURVE + BISECT_CURVE)),
    "cafe_freezing_v0": (
        (1.0,   0.058085,  52.940),
        (5.0,   0.166172,  97.758),
        (20.0,  0.384071, 178.341),
        (50.0,  0.892384, 188.065),
        (200.0, 3.264371, 215.994),
    ),
    "cafe_cut_in_v0": (
        (1.0,   0.000784, 10079.811),
        (5.0,   0.004435, 10100.613),
        (20.0,  0.016717, 10092.674),
        (50.0,  0.036563, 10087.223),
        (200.0, 0.102026, 10062.184),
    ),
}


def bar_crossing(curve=MEASURED_CURVE,
                 threshold: float = AUDIBLE_RATIO) -> tuple[float | None, float | None]:
    """`(last weight below the bar, first weight at or above it)` on `curve`.

    A **bracket**, not a crossing weight: the ladder is a finite set of measured
    points and the ratio between them is not interpolated, because D-265 showed
    it is not monotone and interpolation would assume the shape the measurement
    is supposed to report. `(None, w)` means the lowest point already clears the
    bar; `(w, None)` means no measured point does.
    """
    below = [w for w, r, _ in curve if r < threshold]
    at_or_above = [w for w, r, _ in curve if r >= threshold]
    if not at_or_above:
        return (max(below) if below else None), None
    first = min(at_or_above)
    under = [w for w in below if w < first]
    return (max(under) if under else None), first


def common_audible_weights(curves=None,
                           threshold: float = AUDIBLE_RATIO) -> tuple[float, ...]:
    """Weights that clear the bar on **every** scene in `curves`.

    Empty is the D-266 result. `ARM_SCALE` is one number shared by every run of
    the A/B, so a weight that is audible on one scene and silent on another is
    not a scale this experiment can adopt — and on the three scenes available
    here there is no weight that is audible on all three at once.
    """
    curves = SCENE_CURVES if curves is None else curves
    audible = [{w for w, r, _ in c if r >= threshold} for c in curves.values()]
    if not audible:
        return ()
    return tuple(sorted(set.intersection(*audible)))


def scale_is_per_scene(curves=None, threshold: float = AUDIBLE_RATIO) -> dict:
    """D-266: the audible weight is a property of the **scene**, not of the arm.

    D-265 read one scene and reported a shape — rise, peak near `w=50`,
    collapse at `200`. Two more scenes say the shape is that scene's:

    - `cafe_freezing_v0` rises **monotonically** to `3.264` at `w=200` with no
      collapse; its `rest_median` grows a mild `4.1×` across the whole ladder.
    - `cafe_cut_in_v0` also rises monotonically but sits `~30×` quieter, because
      its `rest_median` is `~1.0e4` from the first point — the collision term is
      already firing at `w_voo = 1`, so the epistemic channel is competing
      against a cost this scene pays regardless of the arm.
    - `cafe_obstacle_crossing_v0`'s collapse is its own: `rest_median` jumps
      `87×` only between `w=50` and `200`, when the arm steers the robot into
      geometry the other two scenes already occupy.

    So the collapse is not a property of the ratio; it is one scene's geometry
    reached at one weight. The consequence for Q-148 is the harder half: the
    bar is crossed at three weights spanning the ladder's whole range, so a
    single `ARM_SCALE` makes the attract arm audible on at most some of the
    scenes, and :func:`common_audible_weights` is empty on the measured points.
    """
    curves = SCENE_CURVES if curves is None else curves
    brackets = {k: bar_crossing(c, threshold) for k, c in curves.items()}
    common = common_audible_weights(curves, threshold)
    monotone = {k: ratio_is_monotone(c) for k, c in curves.items()}
    return {
        "bar_crossing_brackets": brackets,
        "ratio_is_monotone": monotone,
        "shape_transfers": len(set(monotone.values())) == 1,
        "common_audible_weights": common,
        "one_scale_works": bool(common),
        "scenes_measured": tuple(curves),
        "ab_scene_measured": AB_SCENE in curves,
        "why_it_matters": ("ARM_SCALE is one number shared by every run of the "
                           "A/B; the audible weight is not, so no scale read "
                           "here transfers to the A/B scene"),
        "blocked_by": "PR #68 (unmerged) — the A/B scene cannot be measured here",
        "refs": ("D-021", "D-260", "D-264", "D-265", "Q-148", "Q-151"),
    }


def predicted_ratio(curve=MEASURED_CURVE) -> tuple[tuple[float, float, float], ...]:
    """`(weight, measured ratio, ratio the linear inversion predicts)`.

    The prediction is :attr:`ChannelAudibility.required_weight`'s arithmetic run
    forwards: spread is linear in the weight, so from the lowest point on the
    curve the ratio at `w` should be `ratio_0 · w / w_0`. That is exactly the
    step `required_weight` inverts, which is why disagreement here is a fact
    about the inversion and not about this function.
    """
    w0, r0, _ = curve[0]
    return tuple((w, r, r0 * w / w0) for w, r, _ in curve)


def inversion_error(curve=MEASURED_CURVE) -> float:
    """Worst-case factor by which the linear inversion overstates the ratio."""
    return max(pred / meas for _, meas, pred in predicted_ratio(curve) if meas)


def ratio_is_monotone(curve=MEASURED_CURVE) -> bool:
    """Does the ratio rise with the weight over the whole ladder?

    It does not, and that is the Q-151 result. The numerator *is* linear — the
    per-unit spread reads `2.658` at `w=1` and `2.483` at `w=200`, a 6.6% drift
    — but the ratio's denominator is the rest of the cost **on the run that
    weight produced**, and past some weight the arm steers into geometry where
    `w_collision` fires. `rest_median` goes `117 → 10183` (87×) between `w=50`
    and `w=200`, which drags the ratio back *down* through the bar it had
    already cleared.
    """
    ratios = [r for _, r, _ in curve]
    return all(b > a for a, b in zip(ratios, ratios[1:]))


def peak(curve=MEASURED_CURVE) -> tuple[float, float]:
    """`(weight, ratio)` at the ladder's largest measured ratio."""
    w, r, _ = max(curve, key=lambda p: p[1])
    return w, r


def window_verdict(curve=MEASURED_CURVE,
                   threshold: float = AUDIBLE_RATIO,
                   d027_ceiling: float = 6.19) -> dict:
    """Q-151's answer: the floor and the ceiling are **not in one unit**.

    Q-151 leaned on combining D-264's floor (`ratio ≥ 0.1`, this module) with
    D-027's ceiling (`6.19×`, the weight at which the softmax collapsed) into a
    single window, on the stated ground that both are "multiples of the
    baseline spread". The ladder above refutes the premise two ways, and either
    alone is fatal to the arithmetic:

    1. **The denominators are different objects.** D-027 priced `w_voo` against
       a *baseline* run's spread; `weight_units` prices it against the rest of
       the cost on *the same, perturbed* run. Those agree only while the weight
       does not move the trajectory — i.e. exactly where the ceiling is not.
    2. **The ratio is not monotone in the weight**, so it is not an interval in
       the first place. It peaks at `0.6205` near `w=50` and falls to `0.0488`
       at `w=200`; `6.19` is never attained anywhere on the ladder. A "window"
       `[0.1, 6.19]` names an upper bound the quantity cannot reach and hides
       that the *audible* set is bounded above by a collapse, not by a value.

    The consequence for D-264 is direct: `required_weight` is a **prediction**,
    not a measurement. It reads `5.428` for `ATTRACT_ONLY`; the measured curve
    is still `FAINT` at `w=5` (`0.0835`) and does not clear `0.1` until
    somewhere in `(5, 20]`. The inversion overstates by up to
    :func:`inversion_error`.
    """
    audible = [w for w, r, _ in curve if r >= threshold]
    return {
        "premise": "floor and ceiling share a unit",
        "premise_holds": False,
        "why": ("D-027's denominator is a baseline run's spread; "
                "weight_units' is the same run's rest-of-cost. They diverge "
                "exactly where the weight changes the trajectory."),
        "ratio_is_monotone": ratio_is_monotone(curve),
        "peak": peak(curve),
        "d027_ceiling_attained": max(r for _, r, _ in curve) >= d027_ceiling,
        "audible_weights_on_ladder": tuple(audible),
        "bar_crossed_between": (5.0, 20.0),
        "inversion_overstates_by": inversion_error(curve),
        "falls_back_to": "Q-151 option (a) — declare the bar, sweep the weight",
        "refs": ("D-027", "D-264", "Q-151"),
    }


def format_grade(scenario, scale: float = ARM_SCALE,
                 seed: int = 0) -> str:  # pragma: no cover - manual read
    arms = freeze(scale)
    if arms is None:
        return "arm_audibility — UNPOSED at the scene radius; no arms"
    lines = [f"arm_audibility — scale={scale}, threshold={AUDIBLE_RATIO}"]
    per_arm = {}
    for a in arms:
        if not a.is_active:
            continue
        graded = grade(scenario, a, seed=seed)
        per_arm[a.name] = graded
        lines.append(f"  {a.name}")
        lines += [f"    {c}" for c in graded.values()]
    lines.append(f"  A/B vacuous at this scale? {ab_is_vacuous(per_arm)}")
    return "\n".join(lines)


if __name__ == "__main__":     # pragma: no cover - manual read
    from .run import load_scenario
    print(format_grade(load_scenario("eval/scenarios/cafe_obstacle_crossing_v0.yaml")))

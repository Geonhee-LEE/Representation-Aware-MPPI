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

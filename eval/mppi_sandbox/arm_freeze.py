# SPDX-License-Identifier: BSD-3-Clause
"""Q-148's four arms, frozen as an explicit `(w_epist, w_voo)` table.

Everything the A/B needs that does not need the scene. `ratio_pick` chose the
both-on cell's *ratio* (D-261); this module turns that one number into the four
weight pairs a run config consumes, and records the three things a future cycle
would otherwise have to reconstruct from six decisions of prose: what the arms
are, what the ratio's sign does and does not mean (D-262), and what the A/B is
allowed to be scored on (D-250).

The ratio is measured; the scale is not
----------------------------------------

D-256 measured the summed sign to be invariant under `w ∈ {1, 10, 200}` — the
cost field's verdict depends on `w_epist : w_voo` and on nothing else. That is a
statement about the *cost field*, and it does not survive into closed loop: in a
run these weights are added to `_extra_cost` alongside the obstacle and path
terms, so the overall magnitude decides whether the epistemic channel is audible
at all against costs this branch never measured. Nothing on this branch fixes
it.

So `ARM_SCALE` is declared as what it is — a free parameter with no measurement
behind it — rather than being spelled `1.0` at four call sites where it would
read like a result. :func:`unmeasured_parameters` returns it as data so the
first closed-loop cycle has to confront it instead of inheriting it.

Allocation control, and what it costs
---------------------------------------

The three active arms are normalised to spend the **same total weight**
`ARM_SCALE` (L1), so `BOTH_ON` is `(ratio, 1)` scaled to sum to `ARM_SCALE`
rather than laid on top of a single-arm cell. A difference between arms is then
attributable to *how* the authority is allocated between the two channels and
not to *how much* was spent — which is the contrast Q-148 asks for, since both
single arms already differ from the control by amount.

The cost is real and is asserted rather than remembered. Under L1 control
`BOTH_ON`'s repel component (`0.2919·ARM_SCALE`) is strictly weaker than
`REPEL_ONLY`'s (`ARM_SCALE`), and likewise for attract, so **no single-arm →
both-on contrast is a pure "add the other channel"**. :func:`is_pure_addition_to`
returns `False` for both, by construction, and the test pins it: the honest
reading of a `BOTH_ON` vs `REPEL_ONLY` difference is *reallocation*, never
*addition*. Pinning one arm's weight instead would buy one pure contrast at the
price of the other and would make the two active single arms unequal in amount;
that alternative is live and is recorded in Q-150, not silently discarded here.

The both-on sign is not a tiebreak between the arms (D-262)
-------------------------------------------------------------

`BOTH_ON` sits at the contended cell, where the instrument reads
`INDETERMINATE`. That reading is carried here so it cannot be re-derived as
"the scene is balanced": D-262 measured the two arms' live sets to be
**disjoint** on the planner's support (Jaccard `0.0072` at this radius, `0.0` at
`r=0.5`), with the repel arm's live set exactly equal to `classify`'s exposed
partition at 8/8 seeds. The root is therefore an exchange rate between two
regions that never charge the same candidate — a `BOTH_ON` cell is two channels
priced against each other across a boundary, not two forces meeting at a point.
The A/B stays valid because MPPI scores whole trajectories, so a rollout that
enters the shadow pays one arm and forgoes the other.

Scoring is closed-loop only
-----------------------------

:func:`adjudication` names near-miss and clearance as the verdict quantities and
`d_reached` as forbidden (D-250: 9/9 arrival blinds it). It is returned as data
because the temptation this table creates is precisely to grade the arms on the
cost-field quantities that produced it, and those are the quantities D-260/D-262
spent three cycles showing are easy to misread.
"""

from __future__ import annotations

from dataclasses import dataclass

from .ratio_pick import SCENE_RADIUS, pick

#: Total weight each *active* arm spends across the two channels. Not measured —
#: see the module docstring's second section and :func:`unmeasured_parameters`.
ARM_SCALE = 1.0

CONTROL = "CONTROL"
REPEL_ONLY = "REPEL_ONLY"
ATTRACT_ONLY = "ATTRACT_ONLY"
BOTH_ON = "BOTH_ON"

#: Arm order is the reporting order: control first, single arms, mixed cell last.
ARM_NAMES = (CONTROL, REPEL_ONLY, ATTRACT_ONLY, BOTH_ON)


@dataclass(frozen=True)
class Arm:
    """One cell of the A/B: a name and the two critic weights it sets."""

    name: str
    w_epist: float      # ShadowCostCritic.w_epist — repel
    w_voo: float        # ObservationValueCritic.w_voo — attract

    @property
    def is_active(self) -> bool:
        return self.w_epist > 0.0 or self.w_voo > 0.0

    @property
    def authority(self) -> float:
        """Total weight spent across both channels — the controlled quantity."""
        return self.w_epist + self.w_voo

    @property
    def channels_on(self) -> int:
        return int(self.w_epist > 0.0) + int(self.w_voo > 0.0)

    def as_config(self) -> dict:
        """The critic kwargs this arm sets, ready to splat into a run config."""
        return {"w_epist": self.w_epist, "w_voo": self.w_voo}

    def __str__(self) -> str:  # pragma: no cover - formatting
        return f"{self.name:<13} w_epist={self.w_epist:.4f}  w_voo={self.w_voo:.4f}"


def freeze(scale: float = ARM_SCALE,
           radius: float = SCENE_RADIUS) -> tuple[Arm, ...] | None:
    """The four arms at `scale`, or `None` where the geometry poses no question.

    `None` propagates `ratio_pick.pick`'s refusal rather than substituting
    another radius's ratio — the bands share no common point (D-261's
    measurement 2), so a fallback would be a ratio for a scene that is not the
    one being run.
    """
    chosen = pick(radius)
    if chosen is None:
        return None
    ratio = chosen.ratio
    # L1 normalisation: (ratio, 1) rescaled to sum to `scale`, so every active
    # arm spends the same authority and the ratio is preserved exactly.
    denom = 1.0 + ratio
    return (
        Arm(CONTROL, 0.0, 0.0),
        Arm(REPEL_ONLY, scale, 0.0),
        Arm(ATTRACT_ONLY, 0.0, scale),
        Arm(BOTH_ON, scale * ratio / denom, scale / denom),
    )


def arm(name: str, scale: float = ARM_SCALE,
        radius: float = SCENE_RADIUS) -> Arm | None:
    """One arm by name, or `None` if the geometry is unposed."""
    arms = freeze(scale, radius)
    if arms is None:
        return None
    return next(a for a in arms if a.name == name)


def both_on_ratio(arms: tuple[Arm, ...]) -> float:
    """`w_epist : w_voo` of the mixed cell — must reproduce `ratio_pick`'s pick."""
    cell = next(a for a in arms if a.name == BOTH_ON)
    return cell.w_epist / cell.w_voo


def allocation_is_controlled(arms: tuple[Arm, ...]) -> bool:
    """Do all *active* arms spend the same total authority?

    The property that makes an arm-to-arm difference a statement about
    allocation. False would mean the A/B confounds allocation with amount.
    """
    spends = [a.authority for a in arms if a.is_active]
    return max(spends) - min(spends) < 1e-12


def is_pure_addition_to(mixed: Arm, single: Arm) -> bool:
    """Is `mixed` `single` with the other channel added on top?

    Measured `False` for both single arms, by construction of the L1 control —
    the stated cost of :func:`allocation_is_controlled`, kept as a check so a
    later cycle reading "BOTH_ON vs REPEL_ONLY" cannot narrate it as addition.
    """
    return (mixed.w_epist >= single.w_epist and mixed.w_voo >= single.w_voo
            and mixed.channels_on > single.channels_on)


def adjudication() -> dict:
    """What the A/B is scored on — and what it must not be scored on."""
    return {
        "verdict_metrics": ("near_miss", "clearance"),
        "forbidden_metrics": ("d_reached",),
        "forbidden_because": "9/9 arrival blinds it (D-250)",
        "cost_field_sign_required": False,
        "scene": "cafe_blind_corner_v0",
    }


def sign_reading() -> dict:
    """What `BOTH_ON`'s `INDETERMINATE` sign means, per D-262.

    Data rather than prose because the misreading it guards against — "the two
    arms balance here" — is the natural one, and it is wrong for a structural
    reason that no number in this table displays on its own.
    """
    chosen = pick()
    return {
        "sign": None if chosen is None else chosen.sign,
        "is_pointwise_contest": False,
        "means": "exchange rate between two disjoint regions",
        "live_set_jaccard_at_scene_radius": 0.0072,
        "repel_live_set_equals_exposed_partition": True,
        "seeds_agreeing": "8/8",
        "invalidates_ab": False,
        "ab_valid_because": "MPPI scores whole trajectories, so a rollout "
                            "entering the shadow pays one arm and forgoes the other",
        "ref": "D-262",
    }


def unmeasured_parameters() -> dict:
    """The knobs this table sets without evidence, named so they get confronted.

    `ratio` is absent on purpose: it is the one number here that *is* measured.
    """
    return {
        "arm_scale": {
            "value": ARM_SCALE,
            "measured": False,
            "why_it_matters": "decides audibility against the obstacle and path "
                              "terms, which this branch never measured",
            "scope": "shared by every active arm, so cross-arm contrasts are "
                     "scale-controlled even while the scale is arbitrary",
        },
        "normalisation": {
            "value": "L1 — equal total authority per active arm",
            "measured": False,
            "alternative": "pin one single arm's weight; buys one pure "
                           "addition contrast, loses equal amount",
            "ref": "Q-150",
        },
    }


def format_freeze() -> str:  # pragma: no cover - manual read
    arms = freeze()
    if arms is None:
        return "arm_freeze — UNPOSED at the scene radius; no table"
    lines = [f"arm_freeze — Q-148's four arms (r={SCENE_RADIUS}, scale={ARM_SCALE})"]
    lines += [f"  {a}" for a in arms]
    mixed = next(a for a in arms if a.name == BOTH_ON)
    repel = next(a for a in arms if a.name == REPEL_ONLY)
    adj = adjudication()
    lines += [
        f"  both-on ratio        {both_on_ratio(arms):.4f} (ratio_pick)",
        f"  allocation controlled {allocation_is_controlled(arms)}",
        f"  BOTH_ON adds to REPEL_ONLY? {is_pure_addition_to(mixed, repel)} "
        f"— reallocation, not addition",
        f"  sign                 {sign_reading()['sign']} — {sign_reading()['means']}",
        f"  scored on            {', '.join(adj['verdict_metrics'])}; "
        f"never {', '.join(adj['forbidden_metrics'])}",
    ]
    return "\n".join(lines)


if __name__ == "__main__":     # pragma: no cover - manual read
    print(format_freeze())

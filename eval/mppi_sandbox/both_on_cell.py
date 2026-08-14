# SPDX-License-Identifier: BSD-3-Clause
"""Where does Q-148's both-arms-on cell sit once the support is the planner's?

D-258 moved the cancelling root off the grid: on an MPPI-shaped rollout cloud it
sits at `0.7475` where the grid puts it at `0.3470` (`r=0.5`, bands disjoint),
`SEPARATED` at 4 of D-257's 7 radii and never in the other direction. It closed
with the consequence rather than the fix — *"A/B 의 arm 무게는 지금 폐기된
support 에서 유도된 값이므로 다시 배치해야 한다"*. This module is that
re-placement, and it reports the quantity D-258 did not: **which side of zero**
the summed weight lands on.

Why the sign and not only the magnitude
---------------------------------------

D-256 → D-258 have reported the cell as a *headroom* — 2.79x on the grid, ~1.34x
on the rollout band — which is a distance from the root and says nothing about
direction. `research/feed.md`'s 2026-08-14 12:00 entry (SOMBRL, `2511.20066`)
makes the direction its own reportable: SOMBRL greedily maximises a **weighted
sum of extrinsic reward and the agent's epistemic uncertainty** — algebraically
`J = task_cost − λ·σ`, this branch's *attract* sign with a free weight — and
proves **sublinear regret for nonlinear dynamics** in that weighting. A repel
arm heavy enough to flip the summed sign is therefore not merely on the far side
of a numerical crossing; it is outside the only regime in this cluster with a
guarantee attached. So `REPEL` and `ATTRACT` are not two labels of equal
standing here, and a cell reported as "1.34x of headroom" hides which one it is.

The algebra, and why the band is the unit
-----------------------------------------

Each arm is linear in its own weight, so the summed split at `(w_epist, w_voo)`
is `w_epist·s₁ − w_voo·root`, with `s₁ = REPEL_SPLIT_UNIT` (exactly 1.0 — a
structural constant, not a measurement; see `cancelling_stability`). Positive is
`REPEL`, negative is `ATTRACT`, and the crossing is at `w_epist : w_voo = root`.

The root is a **band** over the seed ensemble, never a scalar, so a placement's
sign is only settled if it is settled *for every root in the band*. That gives
three outcomes rather than two, and the third one is the useful one:

- ratio **above** `band.hi` → `REPEL` for every root in the band;
- ratio **below** `band.lo` → `ATTRACT` for every root in the band;
- ratio **inside** the band → `INDETERMINATE`: this instrument does not resolve
  which side of zero the cell is on, and no A/B run at that cell can be
  attributed to a sign.

`INDETERMINATE` is not a failure mode to be tuned away. It is the exact price of
placing the cell where the arms genuinely contend — the maximally-contended
ratio (`band.mean`) is by construction the least sign-resolved one — and naming
it is what stops a both-on arm from being reported as "attract" because the
band's midpoint happened to fall on that side.

The headline: the published cell changes sign on the correct support
--------------------------------------------------------------------

The cell Q-148 currently carries is placed at the **grid** root — `0.3587 : 1`,
the ratio at which D-256 measured the sum to cancel. Re-read against the rollout
band that same ratio is not near-cancelling and not marginally repel: it is
below `band.lo` (`0.6386`), so it is **robustly `ATTRACT` across the whole
band**. The published both-on cell is not a contended cell on the planner's
support at all — it is an attract cell that was labelled as a cancelling one.

That is a sign error, not a magnitude error, and D-258's `2.79x → ~1.34x`
framing could not have surfaced it: both numbers are headroom on the *repel*
side of a root the cell does not in fact sit on the repel side of.

Across D-257's radius set the reading is `ATTRACT` at **5** radii,
`INDETERMINATE` at `r=0.3` (band `[0.1704, 0.5770]` is wide enough to contain
the published ratio) and `UNPLACEABLE` at `r=1.25`. So the claim is not that the
cell is attract *everywhere* — it is that the cell is **never repel** where the
question is posed (:func:`published_cell_is_never_repel`), and unresolved at the
one radius whose band is widest. The weaker per-radius stability predicate is
kept and reads `False`; collapsing the two would hide the unresolved cell.

What to place instead
---------------------

The sign-robust repel cell needs `ratio > band.hi` and the sign-robust attract
cell `ratio < band.lo`; :func:`sign_robust_bracket` returns the pair, and
:func:`contended_ratio` returns the maximally-contended `band.mean` that is
`INDETERMINATE` by construction. This module does **not** pick one — that is
Q-148's open question, and the A/B it feeds is still blocked on PR #68's
occlusion scene. What it removes is the option of running the A/B at the
published ratio while believing that cell is near the crossing.

`UNPOSED` propagates
--------------------

At `r=1.25` the rollout support poses no question (`classify` refuses — every
point a forward rollout reaches is observed), so there is no root and no cell.
This module returns `UNPLACEABLE` there rather than falling back to the grid
root, which would be precisely the substitution D-258 rejected in its
alternative (b).
"""

from __future__ import annotations

from dataclasses import dataclass

from . import rollout_cloud as rc
from .cancelling_stability import DEFAULT_RADII, REPEL_SPLIT_UNIT
from .epistemic_sign import ATTRACT, REPEL

#: The band straddles zero at this ratio — the sign is not resolved by the
#: instrument. Distinct from `epistemic_sign.CANCELLED`, which is a *measured*
#: exact cancellation at one candidate set, not an unresolved interval.
INDETERMINATE = "INDETERMINATE"

#: No root exists on the planner's support at this geometry, so no cell can be
#: placed. See the module docstring's `UNPOSED` note.
UNPLACEABLE = "UNPLACEABLE"

#: The ratio Q-148's both-on cell is currently placed at: D-256's grid root.
#: Quoted, not re-derived — `cancelling_stability.grade_single` already owns the
#: question of whether this number is in its own band (it is; to zero decimals).
PUBLISHED_RATIO = 0.3587


@dataclass(frozen=True)
class Placement:
    """One candidate both-on cell, graded against a root band.

    Weights are carried rather than only their ratio: the A/B needs a concrete
    `(w_epist, w_voo)` pair, and the ratio alone would let a caller reconstruct
    the cell at an arbitrary overall scale — which is a different experiment,
    since the arms are only *jointly* linear along the ratio.
    """

    radius: float
    w_epist: float
    w_voo: float
    band: rc.CloudBand

    @property
    def ratio(self) -> float:
        """`w_epist : w_voo`, the coordinate the summed sign depends on."""
        return self.w_epist / self.w_voo

    def split_against(self, root: float) -> float:
        """The summed split this cell produces if the root is `root`.

        Positive is repel-dominant. `REPEL_SPLIT_UNIT` is imported rather than
        written as `1.0` so the structural constant has one statement of itself
        (D-047) — if the EPISTEMIC channel ever stops being binary, this follows.
        """
        return self.w_epist * REPEL_SPLIT_UNIT - self.w_voo * root

    @property
    def splits(self) -> tuple[float, ...]:
        """The summed split against every root in the band."""
        return tuple(self.split_against(r) for r in self.band.roots)

    @property
    def sign(self) -> str:
        """Which side of zero — or `INDETERMINATE` if the band does not say.

        The conjunction is over the band's *members*, not its `lo`/`hi`, so this
        stays correct if a future ensemble is not an interval.
        """
        splits = self.splits
        if all(s > 0.0 for s in splits):
            return REPEL
        if all(s < 0.0 for s in splits):
            return ATTRACT
        return INDETERMINATE

    @property
    def headroom(self) -> float:
        """The factor `w_voo` must scale by for this cell to reach cancelling.

        `ratio / root`, which at `w_epist = w_voo` reproduces the published
        numbers exactly — `1 / 0.3587 = 2.79x` (D-256, grid) and
        `1 / 0.7475 = 1.34x` (D-258, rollout). Reported beside the sign, never
        instead of it: a value **below 1** means the cell is already past the
        root on the attract side, which is precisely the case no headroom
        figure alone can distinguish from being short of it.
        """
        return self.ratio / self.band.mean

    @property
    def sign_is_guaranteed_regime(self) -> bool:
        """Is this cell in SOMBRL's optimistic weighting, the one with a bound?

        `2511.20066` proves sublinear regret for the attract sign only. This is
        a property of the *placement*, not a recommendation — Q-148's lean (a)
        is still evidence-free (D-021 measured repel silent, which is not the
        same as attract being better).
        """
        return self.sign == ATTRACT

    def __str__(self) -> str:  # pragma: no cover - formatting
        return (f"r={self.radius:<5.2f} w_epist={self.w_epist:7.4f} "
                f"w_voo={self.w_voo:7.4f} ratio={self.ratio:7.4f} "
                f"{self.sign:14s} band=[{self.band.lo:.4f}, {self.band.hi:.4f}] "
                f"headroom={self.headroom:5.2f}x")


def rollout_band(radius: float = 0.5, stride: int = 13,
                 seeds=rc.DEFAULT_SEEDS) -> rc.CloudBand | None:
    """The planner-support root band, or `None` where the question is unposed.

    `None` rather than an exception: `UNPOSED` is a legitimate reading of the
    geometry (D-258 measurement 2), and callers surveying a radius set must be
    able to carry it alongside real bands without a try/except per cell.
    """
    try:
        return rc.band_on(rc.ROLLOUT, radius, rc.matched_k(radius, stride), seeds)
    except ValueError:
        return None


def place_at_ratio(ratio: float, band: rc.CloudBand,
                   w_voo: float = 1.0) -> Placement:
    """The cell at a given `w_epist : w_voo`, normalised on the attract arm.

    `w_voo` is the free scale because the attract arm is the one whose weight
    the ratio is expressed against (`root : 1`), so `w_voo = 1` makes
    `w_epist` read as the ratio itself.
    """
    return Placement(band.radius, ratio * w_voo, w_voo, band)


def sign_robust_bracket(band: rc.CloudBand) -> tuple[float, float]:
    """`(attract_below, repel_above)` — the ratios at which the sign is settled.

    Any ratio strictly inside is `INDETERMINATE`. The bracket's *width* is the
    price the band's spread charges for a sign-resolved cell, which is the
    quantity that decides whether a sign-robust both-on cell can be placed at
    all without the cell ceasing to be contended.
    """
    return band.lo, band.hi


def contended_ratio(band: rc.CloudBand) -> float:
    """The maximally-contended placement: the band's mean root.

    This is where the two arms most nearly cancel and therefore where the A/B
    is most informative about *which arm wins in closed loop* — at the cost of
    being `INDETERMINATE` on sign by construction. The two desiderata are in
    genuine tension; `survey` reports both rather than picking.
    """
    return band.mean


def republished_placement(radius: float = 0.5, stride: int = 13) -> Placement | None:
    """Q-148's *current* cell (the grid root) re-read on the planner support.

    The headline. Returns `None` where the rollout support is `UNPOSED`.
    """
    band = rollout_band(radius, stride)
    return None if band is None else place_at_ratio(PUBLISHED_RATIO, band)


def survey(radii=DEFAULT_RADII, stride: int = 13) -> dict[float, dict]:
    """Per-radius: the published cell's sign, the bracket, the contended ratio.

    Keyed by radius. An `UNPLACEABLE` cell carries no band and no ratio — the
    grid root is deliberately *not* substituted (D-258 alternative (b)).
    """
    out: dict[float, dict] = {}
    for r in radii:
        band = rollout_band(r, stride)
        if band is None:
            out[r] = {"status": UNPLACEABLE}
            continue
        published = place_at_ratio(PUBLISHED_RATIO, band)
        out[r] = {
            "status": published.sign,
            "band": band,
            "published": published,
            "bracket": sign_robust_bracket(band),
            "contended": contended_ratio(band),
        }
    return out


def published_cell_sign_is_stable(surveyed: dict[float, dict]) -> bool:
    """Does the published cell read the *same* sign at every posed radius?

    Measured `False`, and the reason is worth more than the predicate: the
    disagreement is `ATTRACT` (5 radii) against `INDETERMINATE` (`r=0.3`, whose
    band `[0.1704, 0.5770]` is wide enough to contain the published ratio), not
    two opposed signs. Use :func:`published_cell_is_never_repel` for the claim
    that actually holds — this one is kept because reporting only the stronger
    predicate would hide that one radius does not resolve.
    """
    signs = {v["status"] for v in surveyed.values() if v["status"] != UNPLACEABLE}
    return len(signs) == 1


def published_cell_is_never_repel(surveyed: dict[float, dict]) -> bool:
    """The claim the survey supports: no posed radius reads the cell as repel.

    This is the finding's honest form. The published cell was placed as a
    *cancelling* cell on the grid, so a both-on arm run at it was expected to
    sit at the crossing with the repel side within reach. On the planner's
    support it is `ATTRACT` wherever the sign resolves and unresolved nowhere in
    the repel direction — so the A/B's both-on arm, as currently weighted, is
    an attract arm with extra steps.
    """
    return not any(v["status"] == REPEL for v in surveyed.values())


def format_survey(surveyed: dict[float, dict]) -> str:  # pragma: no cover
    lines = ["both_on_cell — Q-148's cell re-placed on the ROLLOUT support",
             f"  published ratio {PUBLISHED_RATIO} (D-256's grid root)",
             f"  {'r':>5} {'sign':>14} {'band lo':>8} {'band hi':>8} "
             f"{'contended':>10} {'headroom':>9}"]
    for r, v in surveyed.items():
        if v["status"] == UNPLACEABLE:
            lines.append(f"  {r:5.2f} {UNPLACEABLE:>14} "
                         f"{'—':>8} {'—':>8} {'—':>10} {'—':>9}")
            continue
        b, p = v["band"], v["published"]
        lines.append(f"  {r:5.2f} {v['status']:>14} {b.lo:8.4f} {b.hi:8.4f} "
                     f"{v['contended']:10.4f} {p.headroom:8.2f}x")
    lines.append(f"  published-cell sign stable across posed radii: "
                 f"{published_cell_sign_is_stable(surveyed)}")
    return "\n".join(lines)


if __name__ == "__main__":     # pragma: no cover - manual read
    print(format_survey(survey()))

# SPDX-License-Identifier: BSD-3-Clause
"""Is arm spread the *general* mechanism of vacuity? No — the two columns fail differently.

D-363 found that on the 경로추종 column gradeability is made of **spread**: a bar
can only cut a scene whose arms differ, and the five `VACUOUS_PASS` cells are
the scenes whose eight arms sit within `0.0070`–`0.0730 m` of one another. STATE
#3 asked the obvious follow-up — if spread is the mechanism, it should carry to
the 물체회피 column too, where D-357 swept `min_distance_to_obstacle` and found
**1** vacuous scene against cross-track's 5. Both harvests are already pinned,
so this is arithmetic on disk. Zero rollouts, as :mod:`excursion_tracking`,
:mod:`obstacle_reach` and :mod:`path_curvature` were.

**The hypothesis is refuted, and the refutation is the finding.** Joining
:data:`threshold_vacuity.CENSUS` to the clearance ranges in
:data:`scene_census.SCENE_SEED0`:

=========================  ========  ========  =========  ==========  ================
scene                      clr lo    clr hi    clr sprd   cte sprd    clearance verdict
=========================  ========  ========  =========  ==========  ================
`cafe_cut_in_v0`           0.0271    0.3783    0.3512     0.6173      DISCRIMINATING
`cafe_obstacle_crossing_v0`  0.0049  0.3255    0.3206     0.8937      DISCRIMINATING
`cafe_convoy_v0`           0.2874    0.5573    0.2699     0.1441      DISCRIMINATING
`cafe_head_on_v0`          0.0039    0.2003    0.1964     0.2804      **VACUOUS_FAIL**
=========================  ========  ========  =========  ==========  ================

**Finding #1 — the clearance column has no narrow-spread scene at all, so
spread cannot be what makes its one vacuous cell vacuous.** Every scene where
clearance is measurable spreads `0.1964`–`0.3512 m`. The cross-track column's
vacuous five spread `0.0070`–`0.0730`. There is no overlap between those two
sets and no clearance scene lands in the narrow band — so the statistic that
separated the cross-track partition is **constant-ish** across the whole
clearance population and separates nothing. :data:`CLEARANCE_SPREAD_FLOOR` pins
the minimum.

**Finding #2 — the vacuous clearance scene spreads its arms *wider* than a
cross-track scene that grades.** `cafe_head_on_v0` is `VACUOUS_FAIL` at spread
`0.1964`, while `cafe_convoy_v0` grades on cross-track at spread `0.1441`. So
ample dispersion is present and the criterion still cannot cut. Spread is
**necessary** for gradeability (D-363 stands) and **not sufficient** (this
module). :data:`SPREAD_NOT_SUFFICIENT` pins the pair.

**Finding #3 — the two columns are vacuous for two different reasons, and only
one of them is repairable by moving a constant.** The mechanisms:

* **cross-track — a *width* failure.** The arms do not differ, so no bar value
  cuts. Unfixable by re-numbering: D-356/357/358 refused alt (c) three times
  and were right to, because there is no constant to shop for.
* **clearance — a *placement* failure.** The arms differ by `0.1964 m` and the
  declared `0.40` sits **above the entire range** (best arm `0.2003`), so all
  8/8 fail always. The distribution is wide, the bar simply misses it.

That asymmetry has a consequence the branch has been carrying the wrong way.
The standing refusal to touch a threshold was learned on the *width* column and
has been applied as a blanket rule; on the *placement* column it is the wrong
call, because there the constant genuinely is mis-set and moving it into the
attained range is a repair rather than threshold-shopping.
:data:`REPAIRABLE_BY_PLACEMENT` names the one scene where that holds.

**Finding #4 — `cafe_head_on_v0` is the only scene with the dispersion for both
channels, and it grades on neither.** Its clearance spread is `0.1964`
(vacuous-fail) and its cross-track spread `0.2804` puts it in D-363's excited
partition — yet D-362 found it declares no `cte_max` key at all. So the one
scene in the registry that could carry a joint 물체회피 + 경로추종 reading is
silent on both, for two unrelated reasons. :data:`BOTH_CHANNELS_SILENT` pins it.
This sharpens STATE's user-blocked #1 and #2 into a single cheaper move: the
scene that needs authoring may already exist.

Scope, stated before the numbers because it bounds them:

* **Seed 0 only**, inherited from both input harvests. `SEED_SCOPE` in
  :mod:`excursion_tracking` carries the same caveat and it is unpaid here too;
  spread is across *arms*, not across seeds.
* **`n = 4` scenes** on the clearance side — the three obstacle-free scenes are
  `UNMEASURABLE` (no obstacle, no clearance) and `cafe_freezing_v0` is
  `UNDECLARED`; all four carry an empty clearance column, so :func:`measure`
  drops them by reading the column rather than by consulting a verdict
  allow-list (D-330). Four points cannot locate a threshold and this module claims
  none; the finding is a *refutation* of a proposed mechanism, which four
  points are enough for, not the discovery of a replacement one.
* Finding #3's repair direction is an argument about which constant is
  mis-set, **not** a proposal of a value. What `0.40` should become is scene
  intent and stays user-blocked.

CLI:
    python -m eval.mppi_sandbox.spread_generality   # rc=1 on drift from CENSUS
"""

from __future__ import annotations

import sys

from . import excursion_tracking, scene_census, threshold_vacuity

#: Smallest arm spread in metres, 4 dp, over the scenes where clearance is
#: measurable. Compare against the cross-track column's vacuous band
#: (`0.0070`–`0.0730`): no clearance scene reaches it, which is finding #1.
CLEARANCE_SPREAD_FLOOR: float = 0.1964

#: `(vacuous clearance scene, its spread, grading cross-track scene, its spread)`
#: — the pair showing spread is necessary but not sufficient (finding #2).
SPREAD_NOT_SUFFICIENT: tuple[str, float, str, float] = (
    "cafe_head_on_v0",
    0.1964,
    "cafe_convoy_v0",
    0.1441,
)

#: Scenes whose criterion is vacuous by *placement* — the arms spread widely and
#: the declared bar sits outside their attained range. Unlike a width failure,
#: this one is repairable by moving the constant into the range (finding #3).
REPAIRABLE_BY_PLACEMENT: tuple[str, ...] = ("cafe_head_on_v0",)

#: The scene carrying dispersion on *both* channels while grading on neither.
#: Clearance `VACUOUS_FAIL`, cross-track excited but `UNDECLARED` (D-362).
BOTH_CHANNELS_SILENT: tuple[str, ...] = ("cafe_head_on_v0",)

#: `scene -> (clearance lo, hi, spread, cross-track spread, clearance verdict)`
#: in metres, 4 dp — the joined table the findings are read off. Restricted to
#: scenes with a measurable clearance range.
CENSUS: dict[str, tuple[float, float, float, float, str]] = {
    "cafe_convoy_v0": (0.2874, 0.5573, 0.2699, 0.1441, "DISCRIMINATING"),
    "cafe_cut_in_v0": (0.0271, 0.3783, 0.3512, 0.6173, "DISCRIMINATING"),
    "cafe_head_on_v0": (0.0039, 0.2003, 0.1964, 0.2804, "VACUOUS_FAIL"),
    "cafe_obstacle_crossing_v0": (0.0049, 0.3255, 0.3206, 0.8937, "DISCRIMINATING"),
}


def measure() -> dict[str, tuple[float, float, float, float, str]]:
    """Join the clearance and cross-track harvests on the measurable scenes.

    Reads :data:`threshold_vacuity.CENSUS` for the clearance verdict,
    :data:`scene_census.SCENE_SEED0` for the attained clearance range, and
    :func:`excursion_tracking.measure` for the cross-track spread. No rollouts
    and no yaml — every operand is already on disk.
    """
    cte = excursion_tracking.measure()
    out: dict[str, tuple[float, float, float, float, str]] = {}
    for scene, verdict in threshold_vacuity.CENSUS.items():
        # Membership in a verdict allow-list is *not* the test (D-330): a scene
        # is measurable iff it actually has an attained range, which is the
        # property itself rather than a label asserting it. The two coincide
        # exactly here — `UNMEASURABLE`/`UNDECLARED` scenes carry zero entries —
        # so reading the column subsumes the label and cannot drift from it.
        col = [v for v in scene_census.SCENE_SEED0.get(scene, {}).values() if v is not None]
        if not col:
            continue
        lo, hi = min(col), max(col)
        out[scene] = (
            round(lo, 4),
            round(hi, 4),
            round(hi - lo, 4),
            cte[scene][3],
            verdict,
        )
    return out


def spread_floor() -> float:
    """Minimum arm spread over the measurable clearance scenes, 4 dp."""
    return round(min(row[2] for row in measure().values()), 4)


def vacuous() -> tuple[str, ...]:
    """Measurable clearance scenes whose criterion grades nothing, sorted."""
    return tuple(sorted(s for s, row in measure().items() if row[4] != "DISCRIMINATING"))


def main() -> int:
    """Print the joined table; rc=1 if it has drifted from :data:`CENSUS`."""
    got = measure()
    for scene in sorted(got):
        lo, hi, sprd, cte_sprd, verdict = got[scene]
        print(f"{scene:28} clr [{lo:.4f}, {hi:.4f}] sprd {sprd:.4f}  cte sprd {cte_sprd:.4f}  {verdict}")
    print(f"\nclearance spread floor {spread_floor():.4f} — cross-track's vacuous band is 0.0070-0.0730")
    if got != CENSUS:
        print("DRIFT: measured table differs from CENSUS", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())

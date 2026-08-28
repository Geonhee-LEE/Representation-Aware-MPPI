# SPDX-License-Identifier: BSD-3-Clause
"""Can P5 name one arm per north-star class? — the contract D-486 forces.

:mod:`baseline_domination` closed the single-baseline question negatively: on
the joint surface the Pareto frontier is the *entire* registry, so there is no
one arm to nominate. `STATE.md` drew the consequence — *"the report now needs a
per-class contract — one arm named per class"* — and named the cheap first cut:
enumerate the classes from :func:`baseline_domination.coverage`'s own partition
and ask, per class, whether any arm is non-dominated **within that class
alone**. A class with a unique winner is a contract line; a class without one is
a second-order finding of D-486's kind.

The answer is **one line, not two**, and the two classes fail differently.

**1. 물체회피 has a contract line, and it is stronger than non-domination.**
`cbf_mppi` is not merely the singleton frontier on the clearance axis — it wins
**outright on all five** scenes that pose the clearance question, strictly
ahead of every other arm on every one. :func:`total_order_winner` tests for
that separately from :func:`frontier_in_class` because the two are different
claims: a singleton frontier says *nothing dominates it*, a total order says
*it dominates everything*. The contract needs the second, and here it holds.

**2. 경로추종 has none, and the plurality candidate is weaker than its record
looks.** `essps_mppi` takes 6 of 7 cross-track scenes, which reads like a line
waiting to be written. It is not, for two independent reasons. The frontier is
three arms wide (`essps_mppi` / `frozen_risk_mppi` / `risk_mppi`), and
`risk_mppi` beats `essps_mppi` outright on `cafe_convoy_v0` — so no total order
exists. And the 6 decomposes: on **three** of those scenes
(`cafe_straight_v0`, `city_curved_v0`, `city_figure8_v0`) the entire rest of the
field is **bit-identical**, so the column has exactly two distinct values and
can say only *"essps differs from everyone"* — it cannot rank the field or name
a runner-up. Restricted to the four scenes that do rank it, `essps_mppi` is
**3 of 4**. That is the honest denominator for a contract argument.

**3. Duplicate classes are axis-dependent, so D-486's collapse is not
reusable per class.** On the joint surface exactly one pair is bit-identical
(`geometric_mppi` / `stock_mppi`). On the clearance axis alone there are
**two** — `frozen_risk_mppi` and `risk_mppi` are identical on all five
clearance scenes and separate only on cross-track. So the 물체회피 class holds
**6** distinct arms, not the joint surface's 7, and a contract that reused the
joint collapse would overstate that class's width by one. This is the third
disjoint column set on which the inert-channel signature :mod:`clearance_census`
first pinned has reproduced.

**4. The one line the tree can draft rests partly on a cell the calibration
table does not admit — and survives its removal.** `cbf_mppi ×
cafe_obstacle_crossing_v0` is `reportable_surface().empty`'s single member
(D-482/Q-206), and it sits inside the 물체회피 class. Dropping it,
`cbf_mppi` still wins the remaining four outright, so the contract line does not
depend on the uncalibrated cell. :func:`line_survives_inadmissible` derives that
rather than asserting it, because the opposite outcome — a contract line that
exists only because of a cell taken at an inadmissible temperature — is exactly
the failure this branch keeps finding, and it must be *checked*, not hoped.

Scope, inherited whole from :mod:`baseline_domination` and not re-litigated
here: seed 0 on both columns, no `time_to_goal` or smoothness census at all
(:data:`baseline_domination.UNCENSUSED_AXES`), so a class with a line today may
lose it once either uncensused axis is bought. A contract line is therefore a
**claim about the two axes that are measured**, and the P5 report must say so
in those words.

CLI:
    python -m eval.mppi_sandbox.class_contract   # rc=1 on drift from CENSUS
"""

from __future__ import annotations

import sys

#: North-star clause -> the axis that instruments it. This is the one typed
#: thing in the module and it is a *definition*, not a copy of a registry
#: (D-047): `CLAUDE.md`'s north star names 물체회피 and 경로추종 as the two
#: halves of "완벽", and clearance/cross-track are the columns this tree has
#: bought for them. The scenes belonging to each class are **derived** from
#: :func:`baseline_domination.coverage`, so a new census moves them without an
#: edit here.
CLASS_AXIS: dict[str, str] = {
    "obstacle": "clear",   # 물체회피
    "tracking": "cte",     # 경로추종
}

#: Distinct values a column must hold before it is allowed to *rank* the field
#: rather than merely separate one arm from a tied block. Two values partition
#: eight arms into "the winner" and "everyone else", which names a winner but
#: cannot name a runner-up — see finding #2. Three is the smallest count that
#: orders three groups, so it is the smallest honest bar, not a tuned one.
RANKING_RESOLUTION: int = 3

#: The census this module pins.
CENSUS: dict[str, str] = {
    "obstacle_line": "cbf_mppi",
    "obstacle_total_order": "yes",
    "obstacle_distinct_arms": "6",
    "obstacle_line_survives_inadmissible": "yes",
    "tracking_line": "",
    "tracking_reason": "NO_FRONTIER_SINGLETON",
    "tracking_distinct_arms": "7",
    "tracking_plurality": "essps_mppi 6/7",
    "tracking_ranking_record": "essps_mppi 3/4",
    "tracking_inert_block_scenes": "cafe_straight_v0,city_curved_v0,city_figure8_v0",
}


def classes() -> tuple[str, ...]:
    """The north-star classes a P5 contract must cover."""
    return tuple(sorted(CLASS_AXIS))


def scenes(cls: str) -> tuple[str, ...]:
    """Scenes belonging to `cls`, derived from the coverage partition.

    Deliberately *not* the joint surface: a per-class contract is entitled to
    every scene its own axis records, and restricting to the joint intersection
    would throw away three of the tracking class's seven scenes for the sake of
    a column that class does not use.
    """
    from .baseline_domination import coverage

    key = {"clear": "clearance", "cte": "cte"}[CLASS_AXIS[cls]]
    return coverage()[key]


def columns(cls: str) -> dict[str, dict[str, float]]:
    """`scene -> {arm: higher-is-better score}` on the class's own axis."""
    from .baseline_domination import columns as joint_columns

    axis = CLASS_AXIS[cls]
    return {s: col for (s, a), col in joint_columns((axis,)).items() if a == axis}


def duplicates_in_class(cls: str) -> tuple[tuple[str, ...], ...]:
    """Arm classes bit-identical on *this class's* columns.

    Separate from :func:`baseline_domination.duplicates` because the answer
    differs — see finding #3. Two arms that separate only on the axis a class
    does not use are, inside that class, one arm.
    """
    from .baseline_domination import duplicates

    return duplicates((CLASS_AXIS[cls],))


def distinct_arms(cls: str) -> int:
    """Arm count with each in-class duplicate collapsed to one representative."""
    from .baseline_domination import arms

    collapsed = sum(len(g) - 1 for g in duplicates_in_class(cls))
    return len(arms()) - collapsed


def frontier_in_class(cls: str) -> tuple[str, ...]:
    """Arms no other arm dominates, within `cls` alone."""
    from .baseline_domination import distinct_frontier

    return distinct_frontier((CLASS_AXIS[cls],))


def resolution(cls: str, scene: str) -> int:
    """Distinct values in one scene's column — how finely it ranks the field."""
    return len({round(v, 12) for v in columns(cls)[scene].values()})


def ranking_scenes(cls: str) -> tuple[str, ...]:
    """Scenes whose column resolves at least :data:`RANKING_RESOLUTION` groups."""
    return tuple(s for s in scenes(cls) if resolution(cls, s) >= RANKING_RESOLUTION)


def inert_block_scenes(cls: str) -> tuple[str, ...]:
    """Scenes that separate one arm from a single tied block and no further.

    The complement of :func:`ranking_scenes`. Named rather than left as a
    subtraction because these are the scenes that inflate a plurality record
    without supporting it: a win here is a win over a block that did not move.
    """
    return tuple(s for s in scenes(cls) if s not in ranking_scenes(cls))


def outright_wins(cls: str, restrict: tuple[str, ...] | None = None) -> dict[str, int]:
    """Per-arm count of scenes where the arm is strictly ahead of every other.

    Ties do not count for either side: an arm sharing the maximum with a
    non-duplicate has not won the scene, and one sharing it with its own
    duplicate has not won it *alone*. Both cases are excluded, which is what
    makes a full sweep here equivalent to a total order.
    """
    from .baseline_domination import arms

    pool = restrict if restrict is not None else scenes(cls)
    cols = columns(cls)
    tally = {a: 0 for a in arms()}
    for scene in pool:
        col = cols[scene]
        for arm, val in col.items():
            if all(val > other for name, other in col.items() if name != arm):
                tally[arm] += 1
    return tally


def total_order_winner(cls: str, restrict: tuple[str, ...] | None = None) -> str | None:
    """The arm that wins *every* scene of `cls` outright, or `None`.

    A stronger claim than a singleton frontier, and the one a contract line
    needs: non-domination says nothing beats this arm, a total order says this
    arm beats everything. The tracking class has the first and not the second.
    """
    pool = restrict if restrict is not None else scenes(cls)
    if not pool:
        return None
    for arm, won in outright_wins(cls, pool).items():
        if won == len(pool):
            return arm
    return None


def inadmissible_scenes(cls: str, arm: str) -> tuple[str, ...]:
    """Scenes of `cls` where `arm`'s cell has no admissible temperature window."""
    from .baseline_domination import inadmissible_joint_cells

    mine = {s for s, a in inadmissible_joint_cells() if a == arm}
    return tuple(s for s in scenes(cls) if s in mine)


def line_survives_inadmissible(cls: str) -> bool | None:
    """Does the contract line hold with the line-arm's uncalibrated cells cut?

    `None` when there is no line to test. `True` when either the arm has no
    inadmissible cell in this class, or it still wins every remaining scene
    outright. Finding #4 is this function's output, not a claim beside it.
    """
    arm = total_order_winner(cls)
    if arm is None:
        return None
    bad = set(inadmissible_scenes(cls, arm))
    if not bad:
        return True
    kept = tuple(s for s in scenes(cls) if s not in bad)
    return total_order_winner(cls, kept) == arm


def plurality(cls: str, restrict: tuple[str, ...] | None = None) -> tuple[str, int, int]:
    """`(arm, wins, scenes)` for the arm winning the most scenes outright."""
    pool = restrict if restrict is not None else scenes(cls)
    tally = outright_wins(cls, pool)
    arm = max(sorted(tally), key=lambda a: tally[a])
    return arm, tally[arm], len(pool)


def contract_line(cls: str) -> tuple[str | None, str]:
    """`(arm, reason)` — the class's contract line, or `None` and why not.

    Two refusal codes, and they are not the same failure. `NO_FRONTIER_SINGLETON`
    means several arms are mutually non-dominated, so the class genuinely
    trades off. `NO_TOTAL_ORDER` means one arm *is* the singleton frontier but
    does not beat the field everywhere — a weaker, more recoverable gap, and
    the one to quote when the class has a favourite that a single scene refutes.
    """
    front = frontier_in_class(cls)
    winner = total_order_winner(cls)
    if winner is not None:
        return winner, "TOTAL_ORDER"
    if len(front) > 1:
        return None, "NO_FRONTIER_SINGLETON"
    return None, "NO_TOTAL_ORDER"


def census() -> dict[str, str]:
    """The derived counterpart of :data:`CENSUS`."""
    obs_line, _ = contract_line("obstacle")
    trk_line, trk_reason = contract_line("tracking")
    p_arm, p_won, p_of = plurality("tracking")
    r_arm, r_won, r_of = plurality("tracking", ranking_scenes("tracking"))
    return {
        "obstacle_line": obs_line or "",
        "obstacle_total_order": "yes" if total_order_winner("obstacle") else "no",
        "obstacle_distinct_arms": str(distinct_arms("obstacle")),
        "obstacle_line_survives_inadmissible":
            {True: "yes", False: "no", None: "n/a"}[line_survives_inadmissible("obstacle")],
        "tracking_line": trk_line or "",
        "tracking_reason": trk_reason,
        "tracking_distinct_arms": str(distinct_arms("tracking")),
        "tracking_plurality": f"{p_arm} {p_won}/{p_of}",
        "tracking_ranking_record": f"{r_arm} {r_won}/{r_of}",
        "tracking_inert_block_scenes": ",".join(inert_block_scenes("tracking")),
    }


def drift() -> tuple[str, ...]:
    """Keys where the derived census disagrees with the pinned one."""
    got = census()
    return tuple(
        f"{k}: pinned {CENSUS[k]!r} != derived {got.get(k)!r}"
        for k in sorted(CENSUS) if CENSUS[k] != got.get(k)
    )


def main() -> int:
    got = census()
    print(f"class_contract — {len(classes())} north-star class(es)")
    for cls in classes():
        arm, reason = contract_line(cls)
        pool, rank = scenes(cls), ranking_scenes(cls)
        print(f"\n  [{cls}] axis={CLASS_AXIS[cls]} "
              f"{len(pool)} scene(s), {len(rank)} ranking, "
              f"{distinct_arms(cls)} distinct arm(s)")
        print(f"    frontier   : {', '.join(frontier_in_class(cls))}")
        if arm:
            surv = line_survives_inadmissible(cls)
            bad = inadmissible_scenes(cls, arm)
            print(f"    CONTRACT   : {arm}  ({reason})")
            print(f"    inadmissible cell(s): {', '.join(bad) or 'none'}"
                  f" -> line survives: {'yes' if surv else 'no'}")
        else:
            p_arm, p_won, p_of = plurality(cls)
            r_arm, r_won, r_of = plurality(cls, rank)
            print(f"    NO LINE    : {reason}")
            print(f"    plurality  : {p_arm} {p_won}/{p_of} "
                  f"-> on ranking scenes only: {r_arm} {r_won}/{r_of}")
            print(f"    inert-block scene(s): {', '.join(inert_block_scenes(cls)) or 'none'}")
    lines = sum(1 for c in classes() if contract_line(c)[0])
    print(f"\n  contract: {lines} of {len(classes())} class(es) have a line")
    bad = drift()
    for line in bad:
        print(f"  DRIFT {line}")
    print(f"{len(bad)} drift.")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())

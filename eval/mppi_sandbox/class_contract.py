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

**5. The tracking record was computed over a run that never arrived, and it
does not survive removing it — the honest figure is `essps_mppi` 2/3.** D-488
bought the `time_to_goal` column and immediately found (`axis_purchase.unfinished`)
that `essps_mppi × cafe_obstacle_crossing_v0` returns `time_to_goal is None`,
which by D-241's pinned construction means the run does not reach the goal. That
cell nevertheless carries a `cte_rms` of `0.0369`, and finding #2 above counted
it as one of `essps_mppi`'s three ranking wins. A cross-track RMS over a run
that never arrives measures how tidily an arm failed, so the win is not a
tracking win. :func:`arrival_gated` cuts the cell and the record falls to **2 of
3** — the arm is not merely one win poorer, it is *ineligible* on that scene, so
the denominator drops too. Three consequences, each derived rather than asserted:

* **The plurality nearly vanishes.** Ungated the tally is 3-1; gated it is
  **2-1-1**, with the forfeited scene going to `social_mppi`. A "6 of 7" that
  reads like a contract line waiting to be written is, on the population that
  can actually rank the field and did actually arrive, a two-win lead over a
  two-way tie. This strengthens D-487's `NO_FRONTIER_SINGLETON` refusal from a
  frontier-width argument into a record argument as well.
* **The obstacle line survives the same cut** (:func:`line_survives_arrival`).
  `cafe_obstacle_crossing_v0` is a 물체회피 scene too, so the gate applies there
  as well; `cbf_mppi` still wins all five outright once `essps_mppi` leaves the
  column. The cut was checked against *both* classes rather than the one it was
  expected to move — the D-487 pattern of verifying the direction you do not
  want.
* **No scene changes ranking status.** Removing an arm can only lower a column's
  resolution, so gating could in principle demote a ranking scene to an
  inert block and shrink the denominator a second time. It does not
  (:func:`gate_preserves_resolution`): the four ranking columns fall 7→6 and
  6→5 distinct values, both still above :data:`RANKING_RESOLUTION`.

**6. The arrival gate is total over the population it judges, which is luck
worth recording, not a property.** `axis_purchase.AXIS_SEED0` censuses the four
*joint* scenes, while the tracking class owns seven. Those extra three are
exactly the inert-block scenes, so the arrival census covers **4 of 4 ranking
scenes** — every cell the record is computed from has an arrival reading, and
the gate is nowhere guessing. :func:`arrival_gate_coverage` derives that
fraction instead of leaving it implicit, because it is a coincidence of the
current scene sets and the first widening of either census can break it. A
future cycle that adds a ranking scene outside the joint surface gets a coverage
reading below total, and must then say so rather than quoting a gated record as
if the gate had seen everything.

The caveat is not hypothetical — it is **already live in the other class**. The
물체회피 class owns `cafe_obstacle_contested_v0`, which is outside the joint
surface, so the obstacle gate covers only **4 of 5** and finding #5's second
bullet is correspondingly weaker than it looks: `cbf_mppi`'s line survives the
cells the gate can see, and one of its five scenes was never asked. Both
fractions are pinned separately for that reason.

Scope, inherited whole from :mod:`baseline_domination` and not re-litigated
here: seed 0 on both columns, no smoothness census in the contract at all
(`time_to_goal` now enters only as the arrival *gate* of finding #5, not as a
scored axis), so a class with a line today may lose it once smoothness is
scored. A contract line is therefore a **claim about the two axes that are
measured**, and the P5 report must say so in those words.

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
    # --- finding #5/#6: the arrival gate. Kept beside the ungated keys rather
    # --- than replacing them, because D-487 quoted the ungated record and a
    # --- census that silently redefined its own keys would let that citation
    # --- drift without anything going red.
    "tracking_unfinished_cells": "essps_mppi@cafe_obstacle_crossing_v0",
    "tracking_gated_record": "essps_mppi 2/3",
    "tracking_gated_tally": "essps_mppi 2, risk_mppi 1, social_mppi 1",
    "obstacle_line_survives_arrival": "yes",
    "arrival_gate_coverage": "4/4",
    "obstacle_arrival_gate_coverage": "4/5",
    "gate_preserves_resolution": "yes",
    # --- D-491: the shipped record is labelled with the clause set it was
    # --- computed on, and the widened one is cited beside it. `CLASS_AXIS` is
    # --- still not re-pointed: D-490's verdict changes what the class *means*,
    # --- not which column D-487/D-489 measured, and overwriting those keys
    # --- would move two shipped citations to record a third.
    "tracking_gated_record_clauses": "cross-track error",
    "tracking_widened_record": "none 0/4",
    "tracking_widened_record_clauses": "cross-track error+smoothness+time-to-goal",
    "tracking_record_pools_equal": "yes",
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


def columns(cls: str, gated: bool = False) -> dict[str, dict[str, float]]:
    """`scene -> {arm: higher-is-better score}` on the class's own axis.

    With `gated=True`, cells whose run never reached the goal are **absent**
    rather than zeroed or ranked last (finding #5). Absence is the honest
    encoding: a non-arrival has no tracking quality to score, so the arm is not
    a competitor on that scene at all — which is why gating moves the record's
    denominator and not just its numerator.
    """
    from .baseline_domination import columns as joint_columns

    axis = CLASS_AXIS[cls]
    cols = {s: col for (s, a), col in joint_columns((axis,)).items() if a == axis}
    if not gated:
        return cols
    cut = unfinished_cells(cls)
    return {
        s: {a: v for a, v in col.items() if (a, s) not in cut}
        for s, col in cols.items()
    }


def unfinished_cells(cls: str) -> frozenset[tuple[str, str]]:
    """`(arm, scene)` cells of `cls` whose run never reached the goal.

    Read from :func:`axis_purchase.unfinished` rather than typed here (D-047):
    that census is derived from the `time_to_goal` column, and a cell's arrival
    status is its property, not this module's opinion. Restricted to `cls`'s own
    scenes so each class gates only what it scores.
    """
    from .axis_purchase import unfinished

    mine = set(scenes(cls))
    return frozenset((arm, scene) for arm, scene in unfinished() if scene in mine)


def arrival_censused_scenes(cls: str) -> tuple[str, ...]:
    """Scenes of `cls` for which an arrival reading exists at all.

    The gate can only speak where `axis_purchase` censused. Scenes outside that
    population are neither gated nor certified — see finding #6.
    """
    from .axis_purchase import AXIS_SEED0

    return tuple(s for s in scenes(cls) if s in AXIS_SEED0)


def arrival_gate_coverage(cls: str) -> tuple[int, int]:
    """`(censused, total)` ranking scenes — how much of the record the gate saw.

    Total coverage is the current reading and is a coincidence of the scene
    sets, not a guarantee; finding #6 says why this is derived and pinned.
    """
    rank = ranking_scenes(cls)
    censused = set(arrival_censused_scenes(cls))
    return sum(1 for s in rank if s in censused), len(rank)


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


def resolution(cls: str, scene: str, gated: bool = False) -> int:
    """Distinct values in one scene's column — how finely it ranks the field."""
    return len({round(v, 12) for v in columns(cls, gated)[scene].values()})


def ranking_scenes(cls: str, gated: bool = False) -> tuple[str, ...]:
    """Scenes whose column resolves at least :data:`RANKING_RESOLUTION` groups."""
    return tuple(s for s in scenes(cls) if resolution(cls, s, gated) >= RANKING_RESOLUTION)


def gate_preserves_resolution(cls: str) -> bool:
    """Does gating leave every ranking scene still able to rank?

    Removing an arm can only lower a column's resolution, so the gate could
    demote a ranking scene to an inert block and shrink the record's
    denominator a second time, for a reason unrelated to arrival. Finding #5's
    third bullet is this function's output.
    """
    return set(ranking_scenes(cls, gated=True)) == set(ranking_scenes(cls))


def inert_block_scenes(cls: str) -> tuple[str, ...]:
    """Scenes that separate one arm from a single tied block and no further.

    The complement of :func:`ranking_scenes`. Named rather than left as a
    subtraction because these are the scenes that inflate a plurality record
    without supporting it: a win here is a win over a block that did not move.
    """
    return tuple(s for s in scenes(cls) if s not in ranking_scenes(cls))


def outright_wins(
    cls: str, restrict: tuple[str, ...] | None = None, gated: bool = False
) -> dict[str, int]:
    """Per-arm count of scenes where the arm is strictly ahead of every other.

    Ties do not count for either side: an arm sharing the maximum with a
    non-duplicate has not won the scene, and one sharing it with its own
    duplicate has not won it *alone*. Both cases are excluded, which is what
    makes a full sweep here equivalent to a total order.
    """
    from .baseline_domination import arms

    pool = restrict if restrict is not None else scenes(cls)
    cols = columns(cls, gated)
    tally = {a: 0 for a in arms()}
    for scene in pool:
        col = cols[scene]
        for arm, val in col.items():
            if all(val > other for name, other in col.items() if name != arm):
                tally[arm] += 1
    return tally


def total_order_winner(
    cls: str, restrict: tuple[str, ...] | None = None, gated: bool = False
) -> str | None:
    """The arm that wins *every* scene of `cls` outright, or `None`.

    A stronger claim than a singleton frontier, and the one a contract line
    needs: non-domination says nothing beats this arm, a total order says this
    arm beats everything. The tracking class has the first and not the second.
    """
    pool = restrict if restrict is not None else scenes(cls)
    if not pool:
        return None
    for arm, won in outright_wins(cls, pool, gated).items():
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


def plurality(
    cls: str, restrict: tuple[str, ...] | None = None, gated: bool = False
) -> tuple[str, int, int]:
    """`(arm, wins, scenes)` for the arm winning the most scenes outright."""
    pool = restrict if restrict is not None else scenes(cls)
    tally = outright_wins(cls, pool, gated)
    arm = max(sorted(tally), key=lambda a: tally[a])
    return arm, tally[arm], len(pool)


def eligible_scenes(cls: str, arm: str, pool: tuple[str, ...]) -> tuple[str, ...]:
    """Scenes of `pool` where `arm` still has a cell after gating.

    An arm that never arrived is not a competitor that lost — it is absent. So
    the honest denominator for its record counts only where it ran to the goal.
    """
    cols = columns(cls, gated=True)
    return tuple(s for s in pool if arm in cols[s])


def arrival_gated(cls: str) -> tuple[str, int, int]:
    """`(arm, wins, eligible)` — the class's record with non-arrivals cut.

    Finding #5. Both parts of the fraction move: the arm loses the win it took
    on a scene it never finished, *and* loses that scene from its denominator.
    Reporting only the first would understate the correction by making the arm
    look beaten rather than absent.

    The pool is the **ungated** ranking scenes deliberately. Gating can drop a
    column's resolution below the ranking bar, and re-filtering afterwards would
    shrink the denominator a second time for a reason that is not arrival —
    charging the gate for a loss of resolution and reporting one number for two
    causes. :func:`gate_preserves_resolution` reports that effect separately,
    which is the only way either can be read.
    """
    rank = ranking_scenes(cls)
    arm, _, _ = plurality(cls, rank, gated=True)
    won = outright_wins(cls, rank, gated=True)[arm]
    return arm, won, len(eligible_scenes(cls, arm, rank))


def gated_tally(cls: str) -> tuple[tuple[str, int], ...]:
    """Every arm with ≥1 gated ranking win, most wins first then name.

    Pinned because the *shape* of the lead is the finding, not just its owner:
    3-1 and 2-1-1 support very different sentences in a P5 report.
    """
    rank = ranking_scenes(cls)
    tally = outright_wins(cls, rank, gated=True)
    return tuple(sorted(
        ((a, n) for a, n in tally.items() if n > 0), key=lambda kv: (-kv[1], kv[0])
    ))


def line_survives_arrival(cls: str) -> bool | None:
    """Does the contract line hold once non-arrival cells are cut?

    `None` when there is no line to test. The sibling of
    :func:`line_survives_inadmissible`, and asked for the same reason: the gate
    was introduced by a tracking finding, so checking it against the *obstacle*
    class is checking the direction the cycle did not expect to move.
    """
    arm = total_order_winner(cls)
    if arm is None:
        return None
    return total_order_winner(cls, scenes(cls), gated=True) == arm


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
    g_arm, g_won, g_of = arrival_gated("tracking")
    cov_n, cov_d = arrival_gate_coverage("tracking")
    return {
        "tracking_unfinished_cells": ",".join(
            f"{a}@{s}" for a, s in sorted(unfinished_cells("tracking"))
        ),
        "tracking_gated_record": f"{g_arm} {g_won}/{g_of}",
        "tracking_gated_tally": ", ".join(f"{a} {n}" for a, n in gated_tally("tracking")),
        "obstacle_line_survives_arrival":
            {True: "yes", False: "no", None: "n/a"}[line_survives_arrival("obstacle")],
        "arrival_gate_coverage": f"{cov_n}/{cov_d}",
        "obstacle_arrival_gate_coverage": "{}/{}".format(*arrival_gate_coverage("obstacle")),
        "gate_preserves_resolution":
            "yes" if all(gate_preserves_resolution(c) for c in classes()) else "no",
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
        **_widened_citation(),
    }


def _widened_citation() -> dict[str, str]:
    """The widened record's keys, **cited** from :mod:`tracking_instrumentation`.

    Read across rather than recomputed. The three-clause columns are that
    module's (it builds and gates them itself, D-490 finding #3), so a second
    derivation here would be a second answer to one question — the failure mode
    D-490 avoided by declining to re-point :data:`CLASS_AXIS` in the first place.

    The clause labels are the load-bearing part. `tracking_gated_record` and
    `tracking_widened_record` are both fractions about 경로추종 over the *same*
    four scenes, and they disagree completely — `essps_mppi 2/3` against nobody
    at all — because one asks for a cross-track lead and the other asks for
    three leads at once. Unlabelled, that reads as a contradiction or as a
    correction. Labelled, it is the finding.
    """
    from . import tracking_instrumentation as ti

    return {
        "tracking_gated_record_clauses": "cross-track error",
        "tracking_widened_record": ti.census()["record_widened"],
        "tracking_widened_record_clauses": "+".join(ti.censused_clauses()),
        "tracking_record_pools_equal": "yes" if ti.record_pools_equal() else "no",
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
        cut = sorted(unfinished_cells(cls))
        cov_n, cov_d = arrival_gate_coverage(cls)
        print(f"    arrival gate: {len(cut)} cell(s) cut "
              f"[{', '.join(f'{a}@{s}' for a, s in cut) or 'none'}], "
              f"covers {cov_n}/{cov_d} ranking scene(s)"
              f"{'' if gate_preserves_resolution(cls) else ' — RESOLUTION LOST'}")
        if arm:
            print(f"    line survives arrival gate: "
                  f"{'yes' if line_survives_arrival(cls) else 'no'}")
        else:
            g_arm, g_won, g_of = arrival_gated(cls)
            print(f"    gated record: {g_arm} {g_won}/{g_of}  "
                  f"(tally: {', '.join(f'{a} {n}' for a, n in gated_tally(cls))})")
    lines = sum(1 for c in classes() if contract_line(c)[0])
    print(f"\n  contract: {lines} of {len(classes())} class(es) have a line")
    bad = drift()
    for line in bad:
        print(f"  DRIFT {line}")
    print(f"{len(bad)} drift.")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())

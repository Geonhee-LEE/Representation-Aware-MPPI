# SPDX-License-Identifier: BSD-3-Clause
"""물체회피 instrumentation — the other half of `CLAUDE.md`'s "완벽".

STATE's second open question after D-491, in its own words: *"물체회피's
`cbf_mppi` holds a 5/5 total order on one clause, and whether it survives its
own class's full clause set has never been run."*

**It cannot be run, and the reason is the result.** The two north-star classes
name clauses of different *kinds*, and `CLAUDE.md` says so in two adjacent
lines:

- 경로추종: *"cross-track error / heading error / smoothness / time-to-goal
  **동시** 만족"* — four **metrics**, conjoined. Widening means adding a
  **column**, which is what :mod:`tracking_instrumentation` did (D-490/D-491).
- 물체회피: *"static + dynamic + 다중 + 가까운 + 가려진 + 의외 — **모든
  클래스**"* — six **obstacle populations**, quantified over. Widening means
  adding a **scene**, not a column.

So the conjunctive-record machinery does not transfer. `cbf_mppi`'s 5/5 is a
claim about one metric over five scenes; the constitution's bar for its class
is a claim about six *kinds of encounter*. Asking whether the line survives "the
full clause set" presupposes columns that the constitution never asked for.

What this module runs instead is the question the constitution actually poses:
**which of the six obstacle classes does the measured surface contain a scene
for?** That is the obstacle-side analogue of D-490's censused / unbought /
unmeasurable split, and it lands on a different leg of it:

============  ==============================  ===================================
class kind    경로추종 (D-490)                 물체회피 (here)
============  ==============================  ===================================
gap shape     **unbought** — reader exists,    **unmeasurable** — no schema field
              column missing                   and no sensor model
price         32 rollouts, under a minute      a visibility model: a P3/P4 build
============  ==============================  ===================================

That asymmetry is the planning consequence. The tracking gap is a *purchase*;
the obstacle gap is a *build*. A P5 report that quoted "one class has a line"
without it would price two unlike debts the same way.

**This module decides nothing about `CLASS_AXIS` and re-points nothing.** Like
:mod:`tracking_instrumentation` it ships beside the shipped keys, under
class-labelled names, so D-487's `cbf_mppi` citation does not move.

Membership is **derived from the scenario yaml**, never typed (D-047): the
scene population grows every time someone adds a file, and a hand-written
census of a growing population is the failure this tree keeps paying for. Only
:data:`NORTH_STAR_CLASSES` is typed, and it has the same standing
:data:`tracking_instrumentation.NORTH_STAR_CLAUSES` has — a *definition* read
off the constitution file, not a copy of a registry.
"""

from __future__ import annotations

import glob
import os
import sys
from pathlib import Path

import yaml

#: The six obstacle classes `CLAUDE.md`'s north star names for 물체회피, quoted
#: in its own order: *"static + dynamic + 다중 + 가까운 + 가려진 + 의외 — 모든
#: 클래스"*. Typed because it is a *definition* read off the constitution, not a
#: copy of a registry (D-047).
NORTH_STAR_CLASSES: tuple[str, ...] = (
    "static",
    "dynamic",
    "다중",
    "가까운",
    "가려진",
    "의외",
)

#: Classes whose membership the scenario schema **cannot express**, with the
#: artefact each one would need. Both require knowing what the robot *knew*
#: at a time, and the sandbox's obstacle model is full-state: every
#: :class:`obstacles.CircleObstacle` is visible to every controller for the
#: whole episode. So there is no field to read and no rollout that would
#: create one — the gap is a build, not a purchase.
#:
#: Deliberately keyed on the missing *artefact* rather than on the class name,
#: because that is the thing a future cycle has to produce. `env_class: D`'s
#: trailing comment on four cafe scenes literally reads "occluded" — and prose
#: is not a field (D-485). A census that accepted it would report coverage the
#: measured surface does not have.
UNMEASURABLE_CLASSES: dict[str, str] = {
    "가려진": "visibility model (occlusion between robot and obstacle)",
    "의외": "appearance model (obstacle enters the known set mid-episode)",
}

#: Class -> the yaml/​column predicate that decides membership, as prose. Kept
#: beside the code so the derivation is auditable without reading it; the test
#: pins the two key sets equal.
DERIVATION: dict[str, str] = {
    "static": "an obstacle with an empty schedule (never moves)",
    "dynamic": "an obstacle with a non-empty schedule (moves)",
    "다중": "two or more moving obstacles",
    "가까운": "some arm's measured clearance is at or below the scene's own "
              "declared `acceptance.min_distance_to_obstacle` budget",
}

#: The census this module pins. Each entry is load-bearing for the P5 report's
#: 물체회피 section.
CENSUS: dict[str, str] = {
    "verdict": "CLAUSE_KINDS_DIFFER",
    "class_count": "6",
    "scene_pool": "5",
    "covered_classes": "dynamic,다중,가까운",
    "uncovered_classes": "static",
    "unmeasurable_classes": "가려진,의외",
    "line_class_coverage": "cbf_mppi 3/6",
    "gap_shape": "unmeasurable",
    "tracking_gap_shape": "unbought",
    # --- the dropped-scene count, shipped beside the coverage it narrows.
    "close_askable": "3/4",
    "close_unasked_scenes": "cafe_freezing_v0",
    "unbuilt_artefacts": "가려진,의외",
}

_SCENARIO_GLOB = "eval/scenarios/*.yaml"


def classes() -> tuple[str, ...]:
    """The north-star obstacle classes for 물체회피."""
    return NORTH_STAR_CLASSES


def _scene_pool() -> tuple[str, ...]:
    """Scenes the 물체회피 class owns, from the coverage partition.

    Same source :func:`class_contract.scenes` uses, so this census and the
    contract line it grades are stated over one population by construction
    rather than by two filters that happen to agree (D-491's lesson).
    """
    from .class_contract import scenes

    return scenes("obstacle")


def _raw(scene: str) -> dict:
    """The scenario yaml for `scene`, as loaded.

    Read raw rather than through :func:`scenario.load_scenario` because the
    fields this census needs (`env_class`, the per-obstacle schedule shape) are
    partly outside the physics-relevant subset that loader consumes.
    """
    path = Path(f"eval/scenarios/{scene}.yaml")
    return yaml.safe_load(path.read_text()) or {}


def _obstacles(scene: str):
    """`CircleObstacle`s of `scene`, so schedule emptiness decides motion."""
    from .scenario import load_scenario

    return load_scenario(f"eval/scenarios/{scene}.yaml").obstacles


def static_obstacles(scene: str) -> int:
    """Count of obstacles in `scene` that never move.

    `CircleObstacle.schedule` empty **is** the static encoding (`obstacles.py`
    says so in a comment on the field), so this reads the model rather than
    re-deciding what static means.
    """
    return sum(1 for o in _obstacles(scene) if len(o.schedule) == 0)


def moving_obstacles(scene: str) -> int:
    """Count of obstacles in `scene` that follow a schedule."""
    return sum(1 for o in _obstacles(scene) if len(o.schedule) > 0)


def declared_clearance_budget(scene: str) -> float | None:
    """The scene's own `acceptance.min_distance_to_obstacle`, or `None`.

    The scene's declared budget is used as the 가까운 threshold rather than a
    tuned constant: it is the bar that file already commits to, so a scene that
    loosens its own budget stops counting as a close-quarters scene without an
    edit here.
    """
    acc = (_raw(scene).get("acceptance") or {})
    v = acc.get("min_distance_to_obstacle")
    return None if v is None else float(v)


def measured_clearances(scene: str) -> dict[str, float]:
    """`{arm: metres}` measured clearance on `scene`, higher-is-better.

    Sourced from the same columns the contract line is computed from, so a
    scene graded 가까운 here is close *in the data the line was won on*, not in
    a separate sweep that might disagree.
    """
    from .class_contract import columns

    return columns("obstacle").get(scene, {})


def exercises(cls: str, scene: str) -> bool | None:
    """Does `scene` exercise obstacle class `cls`?

    `None` — not `False` — for the two unmeasurable classes. The distinction is
    the module's point: `False` says the scene was asked and did not qualify,
    `None` says nothing in the schema can answer. Collapsing them would let a
    report count "not occluded" scenes as evidence about occlusion (D-241).
    """
    if cls in UNMEASURABLE_CLASSES:
        return None
    if cls == "static":
        return static_obstacles(scene) > 0
    if cls == "dynamic":
        return moving_obstacles(scene) > 0
    if cls == "다중":
        return moving_obstacles(scene) >= 2
    if cls == "가까운":
        budget = declared_clearance_budget(scene)
        if budget is None:
            # Not `False`. A scene that declares no clearance budget has not
            # been *asked* whether it is close quarters — there is no bar to
            # compare against. Returning `False` here would have counted it as
            # evidence of a non-close scene, which is the same collapse the
            # unmeasurable classes are kept out of (D-241). Found by this
            # module's own complement test, not by inspection.
            return None
        return any(v <= budget for v in measured_clearances(scene).values())
    raise KeyError(f"unknown obstacle class: {cls}")


def unaskable_scenes(cls: str) -> tuple[str, ...]:
    """Scenes where `cls`'s question cannot be put at all.

    Distinct from "scenes that answered no". Shipped beside the coverage count
    rather than folded into it, because a census that silently narrows its own
    denominator reports a smaller population as though it were the whole one —
    the failure Nav2's `planner_benchmarking` harness has in exactly this shape
    (it `print`s discarded trials and reports the surviving mean with no record
    of the discard count).
    """
    return tuple(s for s in _scene_pool() if exercises(cls, s) is None)


def askable_coverage(cls: str) -> tuple[int, int]:
    """`(scenes exercising cls, scenes that could be asked)`."""
    askable = [s for s in _scene_pool() if exercises(cls, s) is not None]
    return len(scenes_for(cls)), len(askable)


def scenes_for(cls: str) -> tuple[str, ...]:
    """Scenes in the 물체회피 pool that exercise `cls`; empty when unmeasurable."""
    return tuple(s for s in _scene_pool() if exercises(cls, s) is True)


def covered_classes() -> tuple[str, ...]:
    """Classes with at least one scene, in north-star order."""
    return tuple(c for c in NORTH_STAR_CLASSES if scenes_for(c))


def uncovered_classes() -> tuple[str, ...]:
    """Classes that are *derivable* and have zero scenes.

    Kept apart from :func:`unmeasurable_classes` for the reason D-490 kept
    unbought apart from unmeasurable: an uncovered-but-derivable class is fixed
    by **authoring a scene**, an unmeasurable one by **building a model**, and a
    report that merged them would price the second like the first.
    """
    return tuple(
        c for c in NORTH_STAR_CLASSES
        if c not in UNMEASURABLE_CLASSES and not scenes_for(c)
    )


def unmeasurable_classes() -> tuple[str, ...]:
    """Classes the scenario schema cannot express, in north-star order."""
    return tuple(c for c in NORTH_STAR_CLASSES if c in UNMEASURABLE_CLASSES)


def unbuilt_artefacts() -> tuple[str, ...]:
    """Unmeasurable classes whose enabling artefact does not exist yet.

    Population is :data:`UNMEASURABLE_CLASSES` itself, which is the point: an
    allow-list is covered when some guard's population *is* that list
    (`guard_reflexivity.exemption_watchers`), and without this the constant
    would sit on `unwatched_exemptions` — declared, and watched by nobody.

    An artefact counts as built when the sandbox grows a module exporting a
    reader for it. Resolved by import rather than by a typed flag, so the day
    someone lands a visibility model this shrinks on its own instead of
    needing an edit here — the same standing
    :func:`tracking_instrumentation.reader_for` has.

    Expected to name **both** classes today. That is the debt, stated where a
    census can see it rather than in prose.
    """
    import importlib

    built: list[str] = []
    for cls, need in UNMEASURABLE_CLASSES.items():
        mod = "visibility" if cls == "가려진" else "appearance"
        try:
            importlib.import_module(f".{mod}", __package__)
        except ImportError:
            continue
        built.append(cls)
    return tuple(c for c in UNMEASURABLE_CLASSES if c not in built)


def coverage() -> tuple[int, int]:
    """`(covered, total)` over the six north-star obstacle classes."""
    return len(covered_classes()), len(NORTH_STAR_CLASSES)


def line_class_coverage() -> tuple[str | None, int, int]:
    """`(line, covered, total)` — what the shipped contract line actually spans.

    The line is read from :func:`class_contract.contract_line`, never retyped,
    so if D-487's winner ever changes this claim follows it.

    This is the headline. `cbf_mppi` wins all five obstacle scenes outright, and
    that total order is real — but the five scenes it sweeps sit inside three of
    the six classes the constitution names, so the line's *scope* is half its
    class. Quoting 5/5 without this fraction states a total order over an
    unstated population.
    """
    from .class_contract import contract_line

    line, _ = contract_line("obstacle")
    covered, total = coverage()
    return line, covered, total


def clause_kinds_differ() -> bool:
    """Do the two classes' north-star clauses quantify over different things?

    True iff 경로추종's clauses are all *metrics* (each has a reader in
    `path_tracking_metrics`) and 물체회피's are not (none does). Derived rather
    than asserted, so if someone later writes a `static`/`dynamic` metric the
    premise of this whole module goes False instead of staying true in prose.
    """
    from eval import path_tracking_metrics

    from . import tracking_instrumentation as ti

    tracking_all_metrics = all(
        ti.reader_for(c) is not None for c in ti.NORTH_STAR_CLAUSES
    )
    obstacle_none_metrics = not any(
        getattr(path_tracking_metrics, c, None) is not None
        for c in NORTH_STAR_CLASSES
    )
    return tracking_all_metrics and obstacle_none_metrics


def gap_shapes() -> tuple[str, str]:
    """`(obstacle, tracking)` gap shape — the planning consequence.

    Both are derived from the respective modules' own populations, so neither
    string can drift from the census it describes.
    """
    from . import tracking_instrumentation as ti

    obstacle = "unmeasurable" if unmeasurable_classes() else (
        "uncovered" if uncovered_classes() else "complete"
    )
    tracking = "unbought" if ti.unbought_clauses() else (
        "unmeasurable" if ti.unmeasurable_clauses() else "complete"
    )
    return obstacle, tracking


def verdict() -> str:
    """`CLAUSE_KINDS_DIFFER` when the conjunctive-record question is ill-posed.

    The one verdict this module can return that is *not* a finding is
    `CLAUSE_KINDS_MATCH` — which would mean the constitution names metrics for
    both classes and STATE's question was well-posed after all.
    """
    return "CLAUSE_KINDS_DIFFER" if clause_kinds_differ() else "CLAUSE_KINDS_MATCH"


def census() -> dict[str, str]:
    """Re-derive :data:`CENSUS` from the scenes. The test pins the two equal."""
    line, covered, total = line_class_coverage()
    obstacle_gap, tracking_gap = gap_shapes()
    return {
        "verdict": verdict(),
        "class_count": str(len(NORTH_STAR_CLASSES)),
        "scene_pool": str(len(_scene_pool())),
        "covered_classes": ",".join(covered_classes()) or "none",
        "uncovered_classes": ",".join(uncovered_classes()) or "none",
        "unmeasurable_classes": ",".join(unmeasurable_classes()) or "none",
        "line_class_coverage": f"{line or 'none'} {covered}/{total}",
        "gap_shape": obstacle_gap,
        "tracking_gap_shape": tracking_gap,
        "close_askable": "{}/{}".format(*askable_coverage("가까운")),
        "close_unasked_scenes": ",".join(unaskable_scenes("가까운")) or "none",
        "unbuilt_artefacts": ",".join(unbuilt_artefacts()) or "none",
    }


def drift() -> tuple[str, ...]:
    """Keys where :data:`CENSUS` and :func:`census` disagree."""
    live = census()
    return tuple(
        f"{k}: pinned={v!r} live={live.get(k)!r}"
        for k, v in CENSUS.items() if live.get(k) != v
    )


def format_table() -> str:
    """Human-readable per-class coverage table."""
    rows = ["  class       scenes  derivation"]
    for c in NORTH_STAR_CLASSES:
        if c in UNMEASURABLE_CLASSES:
            rows.append(f"  {c:<11} {'—':>6}  needs {UNMEASURABLE_CLASSES[c]}")
        else:
            hits = scenes_for(c)
            rows.append(f"  {c:<11} {len(hits):>6}  {DERIVATION[c]}")
    return "\n".join(rows)


def main() -> int:  # pragma: no cover - CLI
    print(f"obstacle_instrumentation — {len(_scene_pool())} scene(s) in the 물체회피 pool\n")
    print(format_table())
    print()
    for k, v in census().items():
        print(f"  {k:<24} {v}")
    d = drift()
    print(f"\n{len(d)} drift.")
    for line in d:
        print(f"  {line}")
    return 1 if d else 0


if __name__ == "__main__":  # pragma: no cover - CLI
    sys.exit(main())

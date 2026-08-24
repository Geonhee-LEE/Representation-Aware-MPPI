# SPDX-License-Identifier: BSD-3-Clause
"""Does the branch's **already-declared** margin vocabulary meet `cafe_freezing_v0`'s window? Yes — in exactly one point.

:mod:`declaration_gap` derived the seed-robust discriminating window for the one
scene that declares no ``min_distance_to_obstacle``: any bar strictly inside
:data:`~declaration_gap.COMMON_WINDOW` = ``(0.3359, 0.7713)`` cuts the arm
population on **all eight** seeds. It then stopped, deliberately and correctly::

    The bar's *value* is scene intent and stays user-blocked — this module
    reports the interval a value may be drawn from and proposes none.

That is the right refusal and this module does not overturn it. It asks the
strictly narrower question the refusal leaves open: the branch has **already
declared** margins on four other scenes, so the user is not in fact choosing
from the reals. How many of the values already in the vocabulary land inside
the window?

**One.** The vocabulary is ``{0.30, 0.40}`` and:

* ``0.30`` — declared by ``cafe_convoy_v0``, ``cafe_cut_in_v0`` and
  ``cafe_obstacle_crossing_v0``, three of the four declaring scenes — sits
  **below every seed's attained floor** (the window's ``lo`` is ``0.3359``, and
  the ensemble's global minimum over all 64 cells is ``0.3069``; ``0.30``
  undercuts both). It is a :data:`FLOOR`: adopting it would flip the scene to
  eligible *and* grade it ``64/64`` green, a bar reporting avoidance skill it
  never tested.
* ``0.40`` — declared by ``cafe_head_on_v0`` alone — is **interior**. It cuts
  ``45/64`` cells, separates ``4/8`` arm rows all-seeds, and straddles three
  arms' own per-seed ranges (:func:`~declaration_gap.straddling_arms`).

So the decision STATE has carried as ``freeze-margin`` for several cycles is
**forced up to precedent**: adopt an existing branch value and there is exactly
one that discriminates, or invent a value outside the vocabulary and own that
choice explicitly. :func:`verdict` returns :data:`FORCED` for that shape. The
user-blocked half is untouched — *whether* the scene should declare a bar at
all remains scene intent, and this module proposes nothing.

**Why this is worth a module rather than a journal line.** The vocabulary is
*derived*, never typed: :func:`vocabulary` calls
:func:`threshold_vacuity.declared_thresholds`, which reads the scenario yamls
off disk. That is the D-413 lesson applied before it costs anything — a typed
``frozenset({0.30, 0.40})`` would be correct today and would silently stop
being the vocabulary the moment any scene declares a third value, which is
exactly the kind of drift that makes a green census a false lead (D-412). The
graded statement here is that the intersection has **one** member; a fifth
scene declaring ``0.35`` would move it to two and this goes red rather than
leaving STATE's "forced" reading standing unearned.

Scope, stated before the numbers:

* **One scene.** Everything is about ``cafe_freezing_v0``, for the reason
  :data:`declaration_gap.SEED_ENSEMBLE_SCENES` pins: it is the only scene with
  an eight-seed clearance ensemble on disk, so it is the only scene whose
  window is seed-robust rather than asserted at seed 0.
* **Precedent, not optimality.** ``0.40`` being the only interior *declared*
  value is not a claim that ``0.40`` is the best bar. The window is ``0.4354 m``
  wide and holds uncountably many better candidates; this module reports which
  values the branch has already committed to elsewhere, nothing more.
* **The bound `declaration_gap` states still applies.** D-374 grades
  ``COMMON_WINDOW``'s width against the scene's A-A null floor in
  :mod:`floor_reach` (``5.44x``, so it clears). This module inherits that
  caveat rather than re-deriving it; the window is no more declarable here
  than it was there.
* **``min_distance_to_obstacle`` only** — :data:`threshold_vacuity.SWEPT_KEY`.
  The scene's other silent acceptance keys are that module's ``UNSWEPT_KEYS``.

Zero rollouts: every operand is a recorded constant or a yaml already on disk.

CLI:
    python -m eval.mppi_sandbox.margin_vocabulary   # rc=1 on drift from the pins
"""

from __future__ import annotations

import sys

from . import declaration_gap, threshold_vacuity

#: The scene whose bar is missing. Shared with :mod:`declaration_gap` rather
#: than respelled, so the two cannot drift on which scene this is (D-047).
SCENE = declaration_gap.SCENE

#: A declared value strictly inside :data:`declaration_gap.COMMON_WINDOW`. It
#: cuts the arm population on every seed of the ensemble.
INTERIOR = "INTERIOR"
#: A declared value at or below the window's floor. Every arm on every seed
#: clears it, so it grades green without testing anything.
FLOOR = "FLOOR"
#: A declared value at or above the window's ceiling. No arm clears it on every
#: seed. Not reached by the current vocabulary; named so :func:`grade` has all
#: three outcomes and a future declaration landing here is a stated result
#: rather than a missing branch.
CEILING = "CEILING"

#: Exactly one value in the vocabulary is :data:`INTERIOR` — adopting precedent
#: determines the bar.
FORCED = "FORCED"
#: More than one — precedent narrows the choice but does not settle it.
AMBIGUOUS = "AMBIGUOUS"
#: None — no value the branch already uses would discriminate on this scene.
NO_PRECEDENT = "NO_PRECEDENT"

#: `margin -> (scenes declaring it, ...)`, as the scenarios read today. Pinned
#: so that a scene declaring a new value moves :func:`verdict`'s denominator
#: loudly instead of quietly. Derived by :func:`vocabulary`; this is the
#: expectation, not the source.
PRECEDENT: dict[float, tuple[str, ...]] = {
    0.30: ("cafe_convoy_v0", "cafe_cut_in_v0", "cafe_obstacle_contested_v0",
           "cafe_obstacle_crossing_v0"),
    0.40: ("cafe_head_on_v0",),
}

#: `margin -> grade` against :data:`declaration_gap.COMMON_WINDOW`.
GRADES: dict[float, str] = {0.30: FLOOR, 0.40: INTERIOR}

#: The graded headline: one interior value, so precedent forces the bar.
VERDICT = FORCED


def vocabulary() -> dict[float, tuple[str, ...]]:
    """`margin -> declaring scenes`, read from the scenario yamls.

    Derived, never typed: :func:`threshold_vacuity.declared_thresholds` walks
    ``eval/scenarios/`` so this set has exactly one statement of itself. The
    target scene declares nothing, so it cannot appear.
    """
    by_margin: dict[float, list[str]] = {}
    for scene, margin in threshold_vacuity.declared_thresholds().items():
        by_margin.setdefault(round(float(margin), 4), []).append(scene)
    return {m: tuple(sorted(s)) for m, s in sorted(by_margin.items())}


def grade(margin: float) -> str:
    """Grade one margin against the seed-robust window.

    Strict interiority is the same definition :mod:`declaration_gap` used for
    :data:`~declaration_gap.COMMON_WINDOW`: a bar equal to an endpoint does not
    cut the population on the seed that attains it.
    """
    lo, hi = declaration_gap.common_window()
    if margin <= lo:
        return FLOOR
    if margin >= hi:
        return CEILING
    return INTERIOR


def graded_vocabulary() -> dict[float, str]:
    """Every declared margin, graded. The population :data:`GRADES` pins."""
    return {m: grade(m) for m in vocabulary()}


def interior_values() -> tuple[float, ...]:
    """The declared margins that would discriminate on all eight seeds."""
    return tuple(m for m, g in graded_vocabulary().items() if g == INTERIOR)


def verdict() -> str:
    """Does precedent settle the bar? :data:`FORCED` iff exactly one interior."""
    n = len(interior_values())
    if n == 1:
        return FORCED
    return AMBIGUOUS if n > 1 else NO_PRECEDENT


def drift() -> tuple[str, ...]:
    """Every disagreement between the derived reading and the pins above."""
    bad: list[str] = []
    vocab = vocabulary()
    if vocab != PRECEDENT:
        bad.append(f"vocabulary: {PRECEDENT} -> {vocab}")
    graded = graded_vocabulary()
    if graded != GRADES:
        bad.append(f"grades: {GRADES} -> {graded}")
    if verdict() != VERDICT:
        bad.append(f"verdict: {VERDICT} -> {verdict()}")
    return tuple(bad)


def main() -> int:
    lo, hi = declaration_gap.common_window()
    print(
        f"margin vocabulary — {SCENE} declares no bar; "
        f"window ({lo:.4f}, {hi:.4f}) from {declaration_gap.SEEDS} seeds"
    )
    for margin, scenes in vocabulary().items():
        g = grade(margin)
        straddle = declaration_gap.straddling_arms(margin)
        print(
            f"  {margin:.2f}  {g:<10} declared by {len(scenes)} "
            f"({', '.join(scenes)}); straddles {len(straddle)} arm(s)"
        )
    interior = interior_values()
    print(
        f"verdict: {verdict()} — {len(interior)} of {len(vocabulary())} "
        f"declared value(s) interior: {interior or '(none)'}"
    )
    print(
        "  the bar's value remains scene intent (declaration_gap); this is "
        "precedent, not optimality — the window holds better candidates."
    )
    bad = drift()
    for line in bad:
        print(f"DRIFT: {line}", file=sys.stderr)
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())

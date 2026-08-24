"""Who actually reads a `d_enc`-derived value — counted from source, not assumed.

Q-200 asks whether re-pointing :func:`obstacle_reach.scene_reach` at the
realized cruise (D-460) can be bought in one cycle, and its own `다음 action`
line fixes the gating measurement: *enumerate the `d_enc` consumers before
starting, and split into two cycles if the count exceeds 6 modules.* D-455 is
the reason that instruction is worded that way — a census whose population was
"whatever someone typed" read clean while missing the thing it was pinning. So
this module derives the population by walking the AST of every `.py` under
`eval/`, and pins the derivation rather than the sentence.

The count, and it is smaller than the prose that motivated the question::

    consumer                                    kind  symbols read
    ------------------------------------------  ----  ------------------------
    mppi_sandbox/excursion_tracking.py          code  CENSUS
    mppi_sandbox/tests/test_excursion_tracking  test  CENSUS, UNBARRED_EXCITED
    mppi_sandbox/tests/test_obstacle_reach      test  DISCRIMINATING_SCENE,
                                                      OBSTACLE_FREE_SCENES,
                                                      UNBARRED_EXCITED, drift,
                                                      measure, obstacle_free,
                                                      scene_reach,
                                                      unbarred_excited
    mppi_sandbox/tests/test_speed_load_bearing  test  CRUISE_CENSUS,
                                                      DISCRIMINATING_SCENE,
                                                      SPEED_INVERTED, drift,
                                                      measure, measure_at,
                                                      speed_inversions

**One** module outside :mod:`obstacle_reach` consumes a `d_enc` value in
non-test code, and it reads exactly one symbol (`CENSUS`). Three test modules
assert on one. That is the Q-200 answer: 4 < 6, so the re-point is a one-cycle
job under the question's own splitting rule, and the "cascade of unmeasured
width" STATE recorded as the bottleneck has now been measured and is narrow.

The count was **wrong twice before it was right**, both times in the direction
that flatters the answer, which is why the derivation is the deliverable and
the number is not. A hand pin typed off `grep` claimed 5 and named
`test_key_discrimination`, which only mentions `measure_at` in a comment. The
first AST cut then reported 3, dropping `test_speed_load_bearing` — the module
written *about* this census — because it imports `obstacle_reach as ore` and
the walk matched only the literal module name. Neither error was visible in its
own output; both surfaced only when pin and walk were compared.

The sharper half is a **negative** result about this project's own prose.
:data:`obstacle_reach.SPEED_IS_LOAD_BEARING` — written one cycle ago, and the
sentence STATE's bottleneck quotes — names four things as readings of the wrong
robot: `CENSUS`, `UNBARRED_EXCITED`, the `0.5070` floor, and "threshold_vacuity's
VACUOUS_PASS for contested". The first three are internal to
:mod:`obstacle_reach`. The fourth is **not a consumer at all**:
:mod:`threshold_vacuity` imports from :mod:`clearance_census` and
:mod:`scene_census` and reads zero `obstacle_reach` symbols; its verdicts come
from :func:`threshold_vacuity.attained`, which reads *measured* arm-clearance
tables. D-460 already suspected this in the narrow — it recorded that
`attained()` is measured "so it may survive" — but the suspicion never reached
the sentence, and STATE inherited the sentence. :data:`PROSE_OVERREACH` grades
that gap so the correction is not re-derived a third time.

Why this is a module and not a journal line: the same walk that answers Q-200
today is the thing that goes red when a tenth consumer appears. A count written
into prose is a claim about the tree on the day it was typed.
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path

#: Repo-relative root the walk covers. Every `.py` beneath it is read.
EVAL_ROOT = Path(__file__).resolve().parents[1]

#: The :mod:`obstacle_reach` names whose value is a function of `d_enc`. Chosen
#: by hand — this is the one hand-typed set here and it is the *upstream* one,
#: so a mistake in it is loud (a missing name shrinks the derived consumer set,
#: which :func:`drift` compares against a pin). Deliberately excludes
#: `nominal_traversal` (produces the trajectory `d_enc` is measured *on*, not a
#: `d_enc`), `declared_bars` / `DECLARED_SPEEDS` (read off the yaml), and
#: `NOMINAL_DT` / `SCENARIO_DIR` / `ROBOT_RADIUS` (parameters of the
#: measurement, not results of it).
D_ENC_DERIVED: frozenset[str] = frozenset({
    "CENSUS",
    "CRUISE_CENSUS",
    "DISCRIMINATING_SCENE",
    "OBSTACLE_FREE_SCENES",
    "SPEED_INVERTED",
    "UNBARRED_EXCITED",
    "drift",
    "measure",
    "measure_at",
    "obstacle_free",
    "scene_reach",
    "speed_inversions",
    "unbarred_excited",
})

#: The module the symbols live in. Its own file is excluded from the walk: a
#: module is not a consumer of itself, and including it would make the count
#: unfalsifiable (it references every symbol by definition).
SOURCE_MODULE = "obstacle_reach"

#: `repo-relative path -> the D_ENC_DERIVED symbols it reads`, derived by
#: :func:`consumers` and pinned so a new consumer is a failing test rather than
#: a silently wider cascade. This is the Q-200 gating count.
CONSUMERS: dict[str, tuple[str, ...]] = {
    "mppi_sandbox/excursion_tracking.py": ("CENSUS",),
    "mppi_sandbox/tests/test_excursion_tracking.py": ("CENSUS", "UNBARRED_EXCITED"),
    "mppi_sandbox/tests/test_obstacle_reach.py": (
        "DISCRIMINATING_SCENE", "OBSTACLE_FREE_SCENES", "UNBARRED_EXCITED",
        "drift", "measure", "obstacle_free", "scene_reach", "unbarred_excited",
    ),
    "mppi_sandbox/tests/test_speed_load_bearing.py": (
        "CRUISE_CENSUS", "DISCRIMINATING_SCENE", "SPEED_INVERTED",
        "drift", "measure", "measure_at", "speed_inversions",
    ),
}

#: The splitting threshold Q-200 set for itself: "열거 결과가 6 module 을
#: 넘으면 2 cycle 로 분할". Named so the comparison is graded rather than
#: eyeballed by whichever cycle picks the re-point up.
Q200_SPLIT_THRESHOLD = 6

#: Modules named in :data:`obstacle_reach.SPEED_IS_LOAD_BEARING` as carrying a
#: `d_enc`-derived reading which the walk finds read **no** `d_enc` symbol at
#: all. Not a code defect — a prose defect, and it is load-bearing because
#: STATE's `Current bottleneck` quotes the prose and inherits the error.
PROSE_OVERREACH: tuple[str, ...] = ("threshold_vacuity",)

#: Modules that mention :mod:`obstacle_reach` only in comments or docstrings.
#: Kept separate from :data:`CONSUMERS` because a prose mention costs nothing to
#: re-point, and folding the two together is exactly how the cascade got
#: estimated wide. `loop_reach` cites `obstacle_reach.CENSUS` in two comments;
#: `spread_generality` names the module as precedent.
PROSE_ONLY: tuple[str, ...] = ("loop_reach", "spread_generality")

#: Finding, stated once so callers quote rather than re-derive.
Q200_VERDICT = (
    "4 modules consume a d_enc-derived value outside obstacle_reach itself "
    "(1 non-test: excursion_tracking, reading CENSUS only; 3 tests). Q-200's "
    "own splitting rule is >6, so the scene_reach re-point is a one-cycle job, "
    "not the cascade of unmeasured width STATE recorded. The prose that "
    "motivated the question over-counts: threshold_vacuity is named in "
    "SPEED_IS_LOAD_BEARING but reads zero obstacle_reach symbols — its "
    "VACUOUS_PASS comes from attained(), which reads measured clearance "
    "tables, so it does not move when scene_reach does."
)


def _read_symbols(tree: ast.Module) -> set[str]:
    """The :data:`D_ENC_DERIVED` names this AST actually reads.

    Three access shapes count: `obstacle_reach.CENSUS` (attribute on the module),
    `from .obstacle_reach import CENSUS` (direct name binding), and the aliased
    module import `from eval.mppi_sandbox import obstacle_reach as ore` followed
    by `ore.CENSUS`. The third is not hypothetical and is why this function
    binds aliases instead of matching the literal module name: a first cut
    matched only `obstacle_reach.<sym>` and reported **3** consumers, silently
    dropping `test_speed_load_bearing` — the one test module written
    specifically about this census — because it imports `as ore`. A walk that
    misses the alias under-counts exactly the consumer that matters most.

    A bare `CENSUS` with no such import does not count — it would be some other
    module's identically-named census, and conflating the two is the D-459
    join-census mistake. Neither does a name inside a comment or docstring:
    `test_key_discrimination` mentions `obstacle_reach.measure_at` in a comment
    and reads nothing, which is why it is absent from :data:`CONSUMERS`.
    """
    found: set[str] = set()
    imported: set[str] = set()
    module_aliases: set[str] = {SOURCE_MODULE}
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            tail = node.module.split(".")[-1]
            for alias in node.names:
                if tail == SOURCE_MODULE and alias.name in D_ENC_DERIVED:
                    imported.add(alias.asname or alias.name)
                    found.add(alias.name)
                elif alias.name == SOURCE_MODULE:
                    module_aliases.add(alias.asname or alias.name)
        elif isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.split(".")[-1] == SOURCE_MODULE:
                    module_aliases.add(alias.asname or alias.name.split(".")[-1])
    for node in ast.walk(tree):
        if isinstance(node, ast.Attribute) and node.attr in D_ENC_DERIVED and \
                isinstance(node.value, ast.Name) and node.value.id in module_aliases:
            found.add(node.attr)
        elif isinstance(node, ast.Name) and node.id in imported:
            found.add(node.id)
    return found


def consumers() -> dict[str, tuple[str, ...]]:
    """Re-derive `path -> symbols` by walking every `.py` under `eval/`."""
    out: dict[str, tuple[str, ...]] = {}
    for path in sorted(EVAL_ROOT.rglob("*.py")):
        if path.stem == SOURCE_MODULE:
            continue
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except SyntaxError:                                   # pragma: no cover
            continue
        syms = _read_symbols(tree)
        if syms:
            out[path.relative_to(EVAL_ROOT).as_posix()] = tuple(sorted(syms))
    return out


def code_consumers() -> tuple[str, ...]:
    """Consumer paths that are not tests — the ones a re-point must edit."""
    return tuple(p for p in sorted(consumers()) if "/tests/" not in p)


def fits_one_cycle() -> bool:
    """Whether the Q-200 re-point clears the question's own splitting rule."""
    return len(consumers()) <= Q200_SPLIT_THRESHOLD


def prose_overreach() -> tuple[str, ...]:
    """Modules :data:`PROSE_OVERREACH` names, confirmed to read no symbol.

    Returns the subset that is still a genuine over-claim. An empty return
    means the prose was repaired (or the module became a real consumer) and
    :data:`PROSE_OVERREACH` should shrink in the same commit.
    """
    live = consumers()
    return tuple(m for m in PROSE_OVERREACH
                 if not any(Path(p).stem == m for p in live))


def drift() -> list[str]:
    """Lines describing every disagreement between pin and tree. `[]` is clean."""
    live, out = consumers(), []
    for path in sorted(set(live) | set(CONSUMERS)):
        got, want = live.get(path), CONSUMERS.get(path)
        if got is None:
            out.append(f"pinned consumer vanished: {path} (was {want})")
        elif want is None:
            out.append(f"NEW d_enc consumer: {path} reads {got}")
        elif got != want:
            out.append(f"symbol drift in {path}: pinned {want}, live {got}")
    for module in PROSE_OVERREACH:
        if module not in prose_overreach():
            out.append(f"{module} is no longer a prose over-claim — unpin it")
    return out


def main() -> int:                                            # pragma: no cover
    live = consumers()
    print(f"d_enc_consumers — {len(live)} consumer module(s), "
          f"{len(code_consumers())} of them non-test")
    for path, syms in sorted(live.items()):
        kind = "test" if "/tests/" in path else "code"
        print(f"  {kind:4s}  {path:52s} {', '.join(syms)}")
    verdict = "FITS_ONE_CYCLE" if fits_one_cycle() else "SPLIT_REQUIRED"
    print(f"  Q-200: {verdict} ({len(live)} vs threshold "
          f"{Q200_SPLIT_THRESHOLD})")
    over = prose_overreach()
    print(f"  prose over-claim: {', '.join(over) if over else 'none'}")
    print(f"  prose-only (free to re-point): {', '.join(PROSE_ONLY)}")
    problems = drift()
    for line in problems:
        print(f"  DRIFT: {line}")
    return 1 if problems else 0


if __name__ == "__main__":                                    # pragma: no cover
    sys.exit(main())

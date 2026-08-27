# SPDX-License-Identifier: BSD-3-Clause
"""Does STATE's ``## Current bottleneck`` name a scene already retired by proof?

Why this exists
---------------
STATE.md of 2026-08-21 22:00 named the next thrust verbatim:

    `cafe_cut_in_v0` fails `goal_reached` at **every** collision margin — the
    first P3 blocker since D-409 that the knee provably does not reach.

Every clause is true and the conclusion is still wrong. `feasibility` proved in
2026-08-02 that this scene's goal ball is permanently occupied — best attainable
clearance **-0.2 m** — so `goal_reached: 1` and `collision: 0` are mutually
unsatisfiable *by construction*, and `scene_eligibility` has excluded it under
`GOAL_BALL_BLOCKED` ever since. "The knee provably does not reach it" is not a
new P3 blocker; it is the screen's own verdict, re-derived from closed-loop runs
by a cycle that did not know the screen had already spoken.

That is the D-047 shape one level up. D-047 caught a *guard* hand-copying a
registry that had grown; here the hand-copy is the **bottleneck sentence**, and
its reader is next cycle's PLAN. The cost is worse than a stale grep: PLAN's
decision tree consumes this line as its candidate pool, so a retired scene named
here spends a whole cycle re-measuring an infeasibility that costs milliseconds
to look up.

What this screens
-----------------
One question: of the scenes STATE's bottleneck section *names*, which does the
eligibility census already exclude? A named-and-excluded scene is `RETIRED` —
the bottleneck is asking for work no controller can do. Anything else is `LIVE`
and this module says nothing about it.

Scene names are **derived from the census**, never typed. That is not a style
preference: a typed list is precisely the defect this module exists to catch,
and a screen that reproduced it would go green on the day the matrix grew
(D-047, D-072).

Necessary, not sufficient
-------------------------
A `LIVE` verdict means "not refuted here" — the bottleneck may still be
misdirected for reasons no static screen models (wrong axis, answered upstream,
already measured). Only the `RETIRED` direction is a finding, and it is a proof:
the scene's exclusion is a geometric fact about the yaml, not an observation
about any run. The asymmetry is deliberate, in `feasibility`'s idiom — this
screen may never retire a bottleneck a cycle could actually act on.

A screen with no caller is not a screen (D-481)
-----------------------------------------------
Shipped 2026-08-21 with 15 tests, and every one of them built its own STATE in
`tmp_path`. So the machinery was covered and the **live file was never read by
anybody**: no step of `scripts/prompts/auto_research.md` invoked this module,
and the suite stayed green while `STATE.md` carried a `RETIRED` bottleneck for
three consecutive cycles (2026-08-22 → 08-26). On 2026-08-28 05:00 the loop was
one PLAN step from spending a cycle re-measuring `cafe_cut_in_v0`'s
infeasibility — the exact cost the section above predicts — and the screen that
existed to prevent it had been sitting red on disk the whole time.

That is the D-318 shape with the scope narrowed to zero: a clean suite
over-stating what it covered, because what it covered was fixtures. So
:func:`wired_into_loop` derives, from the prompt file itself, whether the loop
actually calls this module, and a test pins it. The pin is the durable half —
the prompt edit alone is one careless rewrite away from silently reverting, and
a reverted wiring reads exactly like a wiring that works.

The pin can only ever check the **call**, not the reading: `STATE.md` is
local-only under D-011, so CI has no live file to screen and a test that read
one would be red on every runner. Catching an actually-retired bottleneck is
therefore a job only the loop can do, which is precisely why the loop has to
be the thing that calls.
"""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from pathlib import Path

from .scene_eligibility import EligibilityCensus, SceneEligibility, census

#: The loop's own constitution — the file whose steps a cycle executes. Derived
#: from this module's location so a repo move cannot leave it pointing at a path
#: that no longer exists while still reporting `True`.
LOOP_PROMPT = (Path(__file__).resolve().parents[2]
               / "scripts" / "prompts" / "auto_research.md")

#: How an invocation of this module is spelled in the prompt. Built from
#: `__name__` rather than typed, so renaming the module breaks the pin loudly
#: instead of leaving it matching a string nothing runs (D-047).
INVOCATION = f"python3 -m {__name__}"


def wired_into_loop(prompt_path: str | Path | None = None) -> bool:
    """Does the loop prompt actually invoke this screen?

    The half of D-481 that survives a careless rewrite. Returns `False` — not
    an exception — when the prompt is missing, because "no prompt" and "prompt
    that does not call" are the same finding for the only reader that matters:
    a cycle that will not run the screen either way.
    """
    path = Path(prompt_path) if prompt_path is not None else LOOP_PROMPT
    try:
        return INVOCATION in path.read_text(encoding="utf-8")
    except OSError:
        return False


#: The heading whose body PLAN's decision tree consumes. Spelled once.
BOTTLENECK_HEADING = "## Current bottleneck"

#: Named-and-excluded: the bottleneck asks for a scene proven uncompletable.
RETIRED = "RETIRED"

#: The bottleneck names no excluded scene. Not a claim that it is well-aimed.
LIVE = "LIVE"

#: The section is absent or empty — nothing to screen. Distinct from `LIVE`,
#: because an empty population reads as a clean one (D-107) and this module
#: refuses to let it.
NO_BOTTLENECK = "NO_BOTTLENECK"


def bottleneck_text(state_path: str | Path = "STATE.md") -> str:
    """The body of STATE's `## Current bottleneck` section, or `""`.

    Reads to the next `## ` heading. Returns empty for a missing file so the
    screen degrades to `NO_BOTTLENECK` rather than raising — a bootstrap tree
    has no STATE.md and that is not a finding.
    """
    path = Path(state_path)
    if not path.is_file():
        return ""
    lines = path.read_text(encoding="utf-8").splitlines()
    try:
        start = next(i for i, ln in enumerate(lines)
                     if ln.strip() == BOTTLENECK_HEADING)
    except StopIteration:
        return ""
    body: list[str] = []
    for ln in lines[start + 1:]:
        if ln.startswith("## "):
            break
        body.append(ln)
    return "\n".join(body).strip()


def _spellings(name: str) -> frozenset[str]:
    """Both spellings of a scene stem.

    `census` keys on the file stem (`cafe_cut_in_v0`) while the yaml's own
    `name:` and most prose use hyphens (`cafe-cut-in-v0`). A screen that knew
    only one spelling would miss the sentence that motivated this module.
    """
    return frozenset({name, name.replace("_", "-"), name.replace("-", "_")})


def named_scenes(text: str, matrix: EligibilityCensus) -> tuple[str, ...]:
    """Scene stems from `matrix` that appear in `text`, in census order.

    Matching is word-bounded so `cafe_cut_in_v0` does not match inside a longer
    token, and case-insensitive because prose capitalises at sentence start.
    """
    found = []
    for scene in matrix.scenes:
        alts = "|".join(re.escape(s) for s in sorted(_spellings(scene.scenario)))
        if re.search(rf"(?<![\w-]){alts}(?![\w-])", text, flags=re.IGNORECASE):
            found.append(scene.scenario)
    return tuple(found)


@dataclass(frozen=True)
class BottleneckScope:
    """Whether the bottleneck sentence points at work that can be done."""

    text: str
    #: Named scenes the census excludes — each a proof the ask is unreachable.
    retired: tuple[SceneEligibility, ...]
    #: Named scenes that survive every screen.
    live: tuple[SceneEligibility, ...]

    @property
    def verdict(self) -> str:
        if not self.text:
            return NO_BOTTLENECK
        return RETIRED if self.retired else LIVE

    def __str__(self) -> str:
        if self.verdict == NO_BOTTLENECK:
            return (f"bottleneck_scope: {NO_BOTTLENECK} — no "
                    f"`{BOTTLENECK_HEADING}` section to screen")
        named = len(self.retired) + len(self.live)
        head = (f"bottleneck_scope: {self.verdict} — {named} scene(s) named, "
                f"{len(self.retired)} retired by proof")
        lines = [head]
        for s in self.retired:
            reasons = ", ".join(sorted(s.exclusions))
            lines.append(f"  RETIRED {s.scenario}: {reasons} "
                         f"(best goal clearance {s.best_goal_clearance:+.2f} m) "
                         f"— excluded by screen; no controller completes it")
        for s in self.live:
            lines.append(f"  live    {s.scenario}: eligible")
        if self.retired:
            lines.append("  ⇒ the bottleneck asks for work the scene matrix "
                         "has already proven unreachable; re-aim it before PLAN "
                         "consumes it as a candidate pool")
        return "\n".join(lines)


def scope(state_path: str | Path = "STATE.md",
          matrix: EligibilityCensus | None = None) -> BottleneckScope:
    """Screen STATE's bottleneck against the eligibility census."""
    matrix = census() if matrix is None else matrix
    text = bottleneck_text(state_path)
    named = set(named_scenes(text, matrix))
    by_name = {s.scenario: s for s in matrix.scenes}
    hits = [by_name[n] for n in matrix_order(matrix) if n in named]
    return BottleneckScope(
        text=text,
        retired=tuple(s for s in hits if not s.eligible),
        live=tuple(s for s in hits if s.eligible),
    )


def matrix_order(matrix: EligibilityCensus) -> tuple[str, ...]:
    """Census order, as names. Kept separate so `scope` has one source of
    ordering and tests can assert on it without reaching into the dataclass."""
    return tuple(s.scenario for s in matrix.scenes)


def main(argv=None) -> int:
    import argparse

    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--state", default="STATE.md")
    args = ap.parse_args(argv)
    result = scope(args.state)
    print(result)
    return 1 if result.verdict == RETIRED else 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())

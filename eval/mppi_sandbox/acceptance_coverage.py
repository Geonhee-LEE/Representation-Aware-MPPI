# SPDX-License-Identifier: BSD-3-Clause
"""Which declared acceptance criteria does the sandbox actually grade?

D-241 found `cafe_freezing_v0` declaring `freeze_duration_max`, ranking it
*second* in `success_metric_priority`, and never computing it: `check_acceptance`
maps an unknown key to the string `"skipped"`, and `run_scenario` computes `pass`
over `[v for v in checks.values() if isinstance(v, bool)]`, so a `str` is dropped
silently. The scene that exists for the freezing failure mode was passing without
being asked about freezing.

That was found by grep, one scene at a time. This module is the sweep. It derives
the graded set by *calling* the checker rather than mirroring its rules table —
D-047's failure was a hand-typed copy of a registry drifting from the registry,
and a probe cannot drift from the function it probes. Every shipped scene's
`acceptance` block is read against it and the difference reported. The
census below pins today's debt by name, so a *new* ungraded key fails the suite
on the cycle that introduces it instead of surviving to a later grep.

Direction is deliberate and asymmetric: grading a key that the census lists as
ungraded is a *win* and must not be a failure — shrink the census in the same
commit. Only an unpinned gap is a finding.

CLI:
    python -m eval.mppi_sandbox.acceptance_coverage        # rc=1 on drift
"""

from __future__ import annotations

import sys
from pathlib import Path

import yaml

from .run import check_acceptance

SCENARIO_DIR = Path(__file__).resolve().parents[2] / "eval" / "scenarios"

# Declared-but-ungraded acceptance keys, per scene, as measured on 2026-08-13.
# Each entry is a scene whose `pass` is computed over fewer criteria than it
# declares. Four of these five sit in the scene's own `success_metric_priority`.
#
# These are *not* wired yet because each needs a definition decision, not
# plumbing — unlike `jerk_lat_max`, whose metric already existed on every run
# and which this cycle wired for that reason:
#   - time_to_goal_max        : needs first-arrival time; `duration_s` is the
#                               whole sim, not the arrival (13.1 s vs a 12.0 s
#                               limit on a run that *did* reach the goal).
#   - time_to_goal_max_ratio  : ratio against an unobstructed reference time
#                               that the harness does not currently produce.
#   - cut_in_detection_latency_max,
#     yield_or_pass_decision_time_max
#                             : require a definition of the detection/decision
#                               instant; no such event is recorded today.
UNGRADED_CENSUS = {
    "cafe_convoy_v0": ["time_to_goal_max_ratio"],
    "cafe_cut_in_v0": ["cut_in_detection_latency_max"],
    "cafe_freezing_v0": ["time_to_goal_max"],
    "cafe_head_on_v0": ["yield_or_pass_decision_time_max"],
}


def scene_paths() -> list[Path]:
    return sorted(SCENARIO_DIR.glob("*.yaml"))


#: Metrics wide enough for every rule to evaluate. Only the *shape* of the
#: verdict is read here (bool vs the "skipped" str), never its truth, so the
#: values are arbitrary — the probe asks "is this key graded", not "does it pass".
PROBE_METRICS = {
    "cte_rms": 0.0, "cte_max": 0.0, "heading_err_rms": 0.0,
    "completion_final": 1.0, "goal_reached": 1, "freeze_duration": 0.0,
    "jerk_lat": 0.0,
}


def grades(key: str) -> bool:
    """Does `check_acceptance` actually score this key?

    Derived by *calling* it, never by reading a copy of its rules table. D-047's
    failure was a hand-typed registry drifting from the registry it mirrored; a
    guard that asks the function cannot drift from it, and it stays correct when
    a rule is added without anyone remembering this module exists.
    """
    verdict = check_acceptance({key: 0.0}, dict(PROBE_METRICS), 0.0)
    return key in verdict and isinstance(verdict[key], bool)


def ungraded_keys(path: Path) -> list[str]:
    """Acceptance keys this scene declares that nothing grades.

    A *parameter* (it tunes another check rather than being one) is dropped by
    `check_acceptance` before it can be scored, so it never appears in the
    verdict at all — which is how this tells it apart from an ungraded check
    without a second list of parameter names to keep in step.
    """
    doc = yaml.safe_load(path.read_text()) or {}
    acc = doc.get("acceptance") or {}
    verdict = check_acceptance(dict.fromkeys(acc, 0.0), dict(PROBE_METRICS), 0.0)
    return sorted(k for k in acc
                  if k in verdict and not isinstance(verdict[k], bool))


def survey() -> dict[str, list[str]]:
    """Scene stem → its ungraded acceptance keys. Fully-graded scenes omitted."""
    out = {}
    for path in scene_paths():
        keys = ungraded_keys(path)
        if keys:
            out[path.stem] = keys
    return out


def prioritised_but_ungraded() -> dict[str, list[str]]:
    """The sharp subset: ungraded keys the scene itself ranks as top-3 success.

    A gap here is worse than a merely-unwired key — the scene names the criterion
    as one of the three things it exists to measure, and then does not measure it.
    """
    out = {}
    for path in scene_paths():
        doc = yaml.safe_load(path.read_text()) or {}
        prio = doc.get("success_metric_priority") or []
        hits = [k for k in ungraded_keys(path) if k in prio]
        if hits:
            out[path.stem] = sorted(hits)
    return out


def drift(census: dict[str, list[str]] | None = None) -> list[str]:
    """Census vs tree. Only *unpinned* gaps are findings; grading one is a win.

    The census is a **parameter** with a module default, not a constant this
    function closes over. That is deliberate: a filter set written at the filter
    site is a registry `guard_reflexivity` must watch, and the 14th consecutive
    cycle to add one would have been this one. Injecting it also lets the tests
    drive both drift directions without mutating module state.
    """
    census = census if census is not None else UNGRADED_CENSUS
    found, msgs = survey(), []
    for scene in sorted(set(found) | set(census)):
        now = set(found[scene]) if scene in found else set()
        pinned = set(census[scene]) if scene in census else set()
        for key in sorted(now - pinned):
            msgs.append(f"UNPINNED_UNGRADED: {scene}.{key} is declared and "
                        f"nothing grades it — wire it, or add it to the census")
        for key in sorted(pinned - now):
            msgs.append(f"CENSUS_STALE: {scene}.{key} is now graded — drop it "
                        f"from UNGRADED_CENSUS in the same commit")
    return msgs


def main(argv=None) -> int:
    found, prio = survey(), prioritised_but_ungraded()
    declared = {k for p in scene_paths()
                for k in (yaml.safe_load(p.read_text()) or {}).get("acceptance") or {}}
    graded = sum(1 for k in declared if grades(k))
    print(f"acceptance_coverage — {len(scene_paths())} scenes, "
          f"{graded} graded keys, {sum(len(v) for v in found.values())} ungraded")
    for scene, keys in sorted(found.items()):
        mark = " [in success_metric_priority]" if scene in prio else ""
        print(f"  {scene}: {', '.join(keys)}{mark}")
    msgs = drift()
    for m in msgs:
        print(f"  {m}")
    return 1 if msgs else 0


if __name__ == "__main__":
    sys.exit(main())

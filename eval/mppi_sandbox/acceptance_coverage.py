# SPDX-License-Identifier: BSD-3-Clause
"""Which declared acceptance criteria does the sandbox actually grade?

D-241 found `cafe_freezing_v0` declaring `freeze_duration_max`, ranking it
*second* in `success_metric_priority`, and never computing it: `check_acceptance`
maps an unknown key to the string `"skipped"`, and `run_scenario` computes `pass`
over `[v for v in checks.values() if isinstance(v, bool)]`, so a `str` is dropped
silently. The scene that exists for the freezing failure mode was passing without
being asked about freezing.

That was found by grep, one scene at a time. This module is the sweep: it reads
the graded set out of `run.ACCEPTANCE_RULES` (never a second copy of it — D-047)
and every shipped scene's `acceptance` block, and reports the difference. The
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

from .run import ACCEPTANCE_PARAMS, ACCEPTANCE_RULES

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


def ungraded_keys(path: Path) -> list[str]:
    """Acceptance keys this scene declares that nothing grades."""
    doc = yaml.safe_load(path.read_text()) or {}
    acc = doc.get("acceptance") or {}
    return sorted(k for k in acc
                  if k not in ACCEPTANCE_RULES and k not in ACCEPTANCE_PARAMS)


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


def drift() -> list[str]:
    """Census vs tree. Only *unpinned* gaps are findings; grading one is a win."""
    found, msgs = survey(), []
    for scene in sorted(set(found) | set(UNGRADED_CENSUS)):
        now = set(found.get(scene, []))
        pinned = set(UNGRADED_CENSUS.get(scene, []))
        for key in sorted(now - pinned):
            msgs.append(f"UNPINNED_UNGRADED: {scene}.{key} is declared and "
                        f"nothing grades it — wire it, or add it to the census")
        for key in sorted(pinned - now):
            msgs.append(f"CENSUS_STALE: {scene}.{key} is now graded — drop it "
                        f"from UNGRADED_CENSUS in the same commit")
    return msgs


def main(argv=None) -> int:
    found, prio = survey(), prioritised_but_ungraded()
    graded = len(ACCEPTANCE_RULES)
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

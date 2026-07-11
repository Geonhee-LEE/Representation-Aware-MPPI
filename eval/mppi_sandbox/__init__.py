# SPDX-License-Identifier: BSD-3-Clause
"""Python-native MPPI sandbox — the project's *primary* verification surface.

Deterministic, dependency-light (NumPy + PyYAML), runs a full scenario in
seconds — so the hourly auto-research executor and CI can actually *prove*
that new controller / representation code drives, avoids, and reaches goals.
Gazebo + Nav2 remains the occasional high-fidelity bench (user-run).

Design decision: docs/decisions.md D-016. Pattern reference:
tkkim-robot/safe_control (numpy sim loop + pluggable safety controllers).

Layout
------
- dynamics.py     diff-drive kinematics, batch-vectorized (shared by sim + rollout)
- obstacles.py    circle obstacles: static + time-waypoint scripted (scenario yaml)
- scenario.py     loader for eval/scenarios/*.yaml
- controllers/    plug-in registry; v0 ships stock_mppi (pure NumPy MPPI)
- run.py          scenario → closed-loop sim → runs/<run_id>.json (run_metrics schema)
- tests/          pytest — the CI contract every new controller must pass
"""

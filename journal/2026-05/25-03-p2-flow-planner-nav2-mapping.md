# Flow Planner Hierarchical CFM → Nav2 Architecture Mapping

- **Cycle**: 2026-05-25 03:00 KST
- **Branch**: `autoresearch/p2-flow-planner-nav2-mapping`
- **TODO**: `36ac5d39` [research] Map Flow Planner hierarchical CFM onto Nav2 global/local split
- **Phase**: P2
- **Status**: keep

## What I tried

- Read Flow Planner (frankcholula/flow_planner) source via GitHub API: backbone.py, planners.py, sampling.py
- Analyzed `StatefulHierarchicalPlanner` architecture: Global (obs-space waypoint CFM, cached + infrequent replan) → Local (action-space CFM, every step, conditioned on subgoal)
- Created `docs/cfm_mppi_analysis.md` mapping the hierarchy onto Nav2's global/local split
- Added adoption strategy table (skip/inspire/port per component per phase)

## What worked / what failed

- The structural mapping is clean: Flow Planner's architecture is nearly 1:1 with Nav2's global/local division, confirming our "CFM at local level only" decision is well-supported
- Flow Planner's MLP backbone is simpler than TCFM's TemporalUnet — could be a lighter alternative for short-horizon action generation
- No code artifacts produced — pure design analysis (as scoped by the TODO)
- The "Why Not Full Replacement" section crystallizes three concrete reasons to keep the classical global planner

## North-star delta

- +1 design decision documented and justified (local-only CFM integration)
- Comparison matrix (cfm_mppi vs TCFM vs Flow Planner) completes the P2 design landscape — all three candidate architectures now analyzed
- Zero code-level movement — design clarity, not execution distance

## Key learnings

- Flow Planner's `global_replan_freq` is identical in concept to Nav2's `planner_frequency` — no architectural novelty needed there
- The local planner conditioning on `(current_state, subgoal_from_global_plan)` is exactly how our TCFM TemporalUnet should interface with MPPI — this is a confirmed pattern across both Flow Planner and cfm_mppi
- MLP backbone with sinusoidal time embedding + FiLM conditioning may suffice for our 2D unicycle action generation (5-dim state, 2-dim action) without the TemporalUnet's full 1D conv stack

## Recommended next 1–3 priorities

1. **(blocked)** Adapt TCFM TemporalUnet for 2D unicycle training — requires PR #23 merge
2. **(new)** Evaluate MLP backbone (Flow Planner style) as lightweight alternative to TemporalUnet for short-horizon action generation
3. **(user)** Merge PR cluster #22–#25 to unblock training pipeline

## Artifacts

- PR: https://github.com/Geonhee-LEE/Representation-Aware-MPPI/pull/25
- Files touched: docs/cfm_mppi_analysis.md (new), docs/README.md
- TSV row appended: yes

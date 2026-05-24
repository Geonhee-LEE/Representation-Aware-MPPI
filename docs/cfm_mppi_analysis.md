# CFM-MPPI Integration Analysis

_Ongoing analysis of Conditional Flow Matching approaches for MPPI sample generation.
See also: `docs/tcfm_evaluation.md` (on PR #22 branch) for TCFM architecture deep-dive._

Related issue: [#17](https://github.com/Geonhee-LEE/Representation-Aware-MPPI/issues/17)

---

## Flow Planner → Nav2 Architecture Mapping

**Source**: [frankcholula/flow_planner](https://github.com/frankcholula/flow_planner)
(MIT License, Box2D environments: LunarLander, BipedalWalker, CarRacing)

### Architecture

Flow Planner is a hierarchical trajectory planning framework built on CFM with two
stages running inside a receding-horizon MPC loop:

1. **Global Planner (Waypoint CFM)** — generates a full state-space trajectory
   (observation-only, long horizon). Runs infrequently (`global_replan_freq` steps).
   Backbone: MLP or CNN with sinusoidal time embedding + FiLM conditioning.
   Conditioning: `start_obs` or `(start_obs, goal_obs)`.

2. **Local Planner (Action CFM)** — generates short-horizon action sequences.
   Runs every control step, conditioned on `(current_state, subgoal)` where `subgoal`
   is extracted from the cached global plan at a lookahead index.

The `StatefulHierarchicalPlanner` caches the global plan and only replans when the
step counter exceeds `global_replan_freq`, then always runs the local planner to
produce fine-grained actions toward the next waypoint.

### Mapping to Nav2 Global/Local Split

| Flow Planner | Nav2 Equivalent | Structural Similarity |
|---|---|---|
| Global Planner (obs_only CFM) | Global Planner (NavFn / Theta* / Smac) | Both produce a reference trajectory; FP adds velocity profiles |
| Local Planner (act_only CFM) | Local Controller (MPPI) | Both produce control sequences; FP uses CFM instead of Gaussian sampling |
| `global_replan_freq` | `planner_frequency` param | Same concept — amortize expensive global compute |
| Subgoal extraction at lookahead | PathHandler lookahead point | Same carrot-chasing pattern |
| `(start_obs, goal_obs)` conditioning | Costmap + goal pose input | FP conditions on raw state; Nav2 uses spatial representations |

### Key Insight for Our Project

Flow Planner's hierarchy is **structurally identical** to Nav2's global/local split,
but replaces rule-based search and hand-tuned sampling with learned CFM generators at
both levels. The three CFM-for-MPPI approaches occupy different integration depths:

```
                    Replace global?   Replace local sampling?
cfm_mppi (Mizuta)        No                 Yes (full)
Flow Planner             Yes                Yes (full)
Our approach (P2)        No                 Partial (warm-start)
```

**Our recommended integration (Option A from TCFM evaluation):**
- **Keep Nav2's graph-based global planner** — proven, fast, handles arbitrary costmaps.
- **Use CFM at the local level only** — TCFM's TemporalUnet generates candidate
  trajectories that warm-start MPPI's sampling distribution. MPPI's cost evaluation
  + weighted selection provides the safety/obstacle-awareness layer that pure CFM lacks.
- **Conditioning enrichment path** (P3+): instead of raw `(state, goal)`, condition
  the local CFM on BEV/risk channel features — this is where our representation-aware
  thesis materializes.

### Why Not Full Replacement (Flow Planner Style)?

1. **Nav2 global planner handles dynamic costmap updates** (inflation, voxel layers)
   without retraining. A CFM global planner would need fine-tuning per environment.
2. **Safety guarantee**: MPPI's cost evaluation provides a hard constraint layer
   (CBF-MPPI, obstacle critics) that pure generative sampling cannot.
3. **Sim-to-real**: Our Gazebo environments are limited; a learned global planner
   trained on them would not generalize. The local planner operates on shorter
   horizons where sim-to-real gap is smaller.

### Adoption Strategy

| Component | Strategy | Phase |
|---|---|---|
| Hierarchical replan structure | **Inspire** — confirm our existing Nav2 frequencies are compatible | P2 |
| CFM local planner conditioning on `(state, subgoal)` | **Port** — this is exactly how TCFM integrates into MPPI | P2 |
| Global plan as waypoint source for local conditioning | **Already have** — Nav2 PathHandler does this | — |
| MLP backbone (simpler than TemporalUnet) | **Evaluate** — may suffice for short-horizon action generation | P2 |
| Reward-conditioned generation | **Inspire** — analogous to MPPI cost-weighted selection | P3 |

---

## References

- Flow Planner: https://github.com/frankcholula/flow_planner
- cfm_mppi (Mizuta & Leung, ICRA 2026): https://arxiv.org/abs/2508.01192
- TCFM (Ye & Gombolay): https://arxiv.org/abs/2403.10809
- Issue #17: CFM-MPPI analysis + roadmap mapping

# Research State — auto-generated each cycle

_Last updated: 2026-05-31 21:00 KST · cycle p2-residual-dynamics-mlp-scaffold_

## North star distance

Still **0 measured numbers** (P5 baseline sim run `runs/cafe-001.json` remains
user-blocked). But P2 moved from design to code: the learned residual-dynamics
model decided in D-009 now **exists** — NumPy nominal diff-drive (`f_nominal`) +
PyTorch MLP-ensemble residual (`g_theta`) with an epistemic-uncertainty hook
(ensemble std). Untrained and not yet in the MPPI rollout, so no closed-loop gain
yet.

## Current bottleneck

**The residual model can't be trained or queried yet** — two pieces are missing:
(1) a training data pipeline producing `(s, a, s_next)` tuples + the residual
target `s_next - f_nominal(s,a)` from sim rollouts, and (2) the MPPI rollout hook
that swaps analytic dynamics for `g_theta`. The data pipeline is the gating one
(no data → no trained model). torch is also absent in the executor env, so any
training-smoke step needs PyTorch installed (user-blocked).

## Open experiments

| branch | last update | last description | days open |
|---|---|---|---|
| `autoresearch/p2-residual-dynamics-mlp-scaffold` | 2026-05-31 21:00 | scaffold built, PR #44 open | 0 |
| `autoresearch/p2-residual-dynamics-decision-matrix` | 2026-05-31 00:00 | D-009 ADR, PR #43 | ~1 |
| `autoresearch/p2-unicycle-dataset-generator` | ~05-25 | unicycle dataset gen (PR #23) | ~6 |
| `autoresearch/p2-ensemble-residual-dynamics-compat` | ~05-27 | ensemble compat (PR #27) | ~4 |
| `autoresearch/p2-energy-based-residual-dynamics-reg` | ~05-26 | energy reg (PR #24) | ~5 |

## Recent learnings (last 3 cycles)

- Scaffold built: nominal model is torch-free (runs in rollout); learned ensemble
  is torch-only and import-isolated so the torch-free core tests every cycle.
- Residual target convention locked to `s_next - f_nominal(s,a)` — the data
  pipeline must compute against this exact nominal model.
- (decision-matrix) MLP-ensemble chosen over MAML/Koopman/NODE (D-009): build-first,
  rollout-native, ensemble variance = cheapest path to a P3 epistemic channel.

## Next claude-actionable (this cycle would pick from here)

1. **Training data pipeline** — collect `(s,a,s_next)` from sim rollouts, store
   residual target `s_next - f_nominal(s,a)`; reuse the unicycle generator (#23)
   format. _Feasible once #23 lands on main; bootstrap synthetic data otherwise._
2. **MPPI rollout integration point** — wrap `ResidualDynamicsEnsemble` so a
   sampled action batch returns corrected next-states; interface-first, no torch
   dependency in the import path.
3. **Ensemble trainer skeleton** — per-member bootstrap/seed, MSE→NLL loss,
   checkpoint save/load; gated on PyTorch being installed.

## Next user-blocked (waiting on user action — surfaces in Telegram queue, not for PLAN)

1. **Merge the P2 PR stack** (#23 #24 #27 #43 #44) — scaffold (#44) is standalone
   off main, but data-pipeline work needs #23 on main to be feasible.
2. **Install PyTorch** in the dev/executor env — unblocks ensemble training-smoke
   and the torch-dependent unit tests (currently skipped).
3. **Run `cafe_straight_v0` sim** with `include_run_metrics:=true` → first
   quantitative baseline `runs/cafe-001.json` (Owner=user, 20+ days open).

## Cycles to date

- This week (from Mon 2026-05-25): includes this cycle
- Project total: ~17 (per merged PR #41 + in-flight stack)

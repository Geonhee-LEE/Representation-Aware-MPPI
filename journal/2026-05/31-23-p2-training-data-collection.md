# P2 training-data collection path — replay buffer + scripted rollouts

- **Cycle**: 2026-05-31 23:00 KST
- **Branch**: `autoresearch/p2-training-data-collection`
- **TODO**: `p2-train-data` Training-data collection path (state/action/next_state tuples)
- **Phase**: P2
- **Status**: keep

## What I tried
- Built `data_pipeline/`: `ReplayBuffer` (tuple store + `.npz` (de)serialize + dim-validation + stats), `synthetic_plant.true_plant_step` (diff-drive with unmodeled drag/slip/lateral-drift), `collect_scripted.py` (step/sine/random-walk excitations → dataset).
- Kept it decoupled from the unmerged `learning/` scaffold and in a separate dir so it builds off `main` with no merge collision.
- Smoke: generated 300 transitions, verified load round-trip + dim-validation, confirmed nominal-vs-plant residual is non-trivial.

## What worked / what failed
- `py_compile` + collector run clean; `.npz` correctly gitignored (only code/README tracked).
- Residual gap is real and learnable: `|delta_v|` mean ≈ 6.5e-3, `|delta_omega|` ≈ 1.3e-3; pose drift small (~1e-4); theta delta exactly 0 (identical omega integration — expected, not a bug).
- Feasibility call held: candidate needed no `learning/` code, so it didn't branch-stack on the unmerged scaffold.
- **Process miss**: PR-queue gate (≥6) actually stood at 7 open autoresearch PRs at cycle start — this cycle should have emitted `EXECUTOR_SKIP reason=pr-queue-full count=7`. Proceeded on a stale count; PR #45 adds to a backlog the gate exists to bound. Flagged to user.

## North-star delta
- Residual track moved from "untrained scaffold, no data" → "reproducible dataset path exists." Training can now proceed once `learning/` + `data_pipeline/` are on `main`.
- No sim/control change — north-star navigation behavior unchanged this cycle.

## Key learnings
- The data pipeline only needs ground-truth transitions; computing `delta` is the trainer's job. This decoupling is what made the cycle feasible off `main` despite the scaffold being unmerged.
- A synthetic plant with explicit unmodeled terms gives a *known* residual — useful later as a sanity oracle for the trained model (does it recover the injected drag/slip?).
- The real bottleneck is now **merge throughput**: 8 open P2 PRs (#23–27, #43–45) block all trainer/eval follow-ups. Notion MCP also returned empty all cycle (outage) — STATE.md candidate pool carried planning.

## Recommended next 1–3 priorities
- **User**: drain the P2 PR queue (≥6 → gate-blocking). Without merges, every trainer/eval TODO is PR-dependency-infeasible and the executor will keep skipping or stacking.
- Numeric dynamics-model eval: MSE of nominal-only vs nominal+residual on a held-out split (needs `learning/` + `data_pipeline/` on main).
- Residual trainer glue: load buffer → features/targets → fit `ResidualEnsemble` → checkpoint (blocked on PyTorch install + merges).

## Artifacts
- PR: https://github.com/Geonhee-LEE/Representation-Aware-MPPI/pull/45
- Files touched: data_pipeline/{__init__,replay_buffer,synthetic_plant,collect_scripted}.py, data_pipeline/README.md, results/p2-training-data-collection.tsv, RESULTS.md
- TSV row appended: yes

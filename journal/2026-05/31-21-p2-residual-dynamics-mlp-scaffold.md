# P2 residual dynamics scaffold — nominal diff-drive + MLP-ensemble

- **Cycle**: 2026-05-31 14:14 KST
- **Branch**: `autoresearch/p2-residual-dynamics-mlp-scaffold`
- **TODO**: `residual-scaffold` Build residual dynamics model scaffold (PyTorch MLP-ensemble: model def + forward + unit test)
- **Phase**: P2
- **Status**: keep

## What I tried
- Created `learning/dynamics/` package with the build-first residual unit from D-009.
- `nominal.py`: pure-NumPy `NominalDiffDrive` (Euler unicycle step + rollout) + `wrap_angle`; batched/single inputs.
- `residual_model.py`: PyTorch `ResidualDynamicsEnsemble` — N MLP members, forward returns (mean residual, epistemic std via disagreement); `all_member_residuals` for particle rollouts.
- Tests + README documenting conventions (`s=[x,y,theta]`, `a=[v,omega]`) and follow-ups.

## What worked / what failed
- 7 nominal unit tests pass (torch-free); torch-dependent ensemble tests skip cleanly (`pytest.importorskip`) since torch isn't installed here.
- All modules `py_compile` clean including the torch one.
- Repo-state snag: local `main` carried 3 unpushed decision-matrix commits ahead of `origin/main`. Rebased my single thrust `--onto origin/main` so the PR is one clean thrust, not branch-stacked.
- Bash tool output was heavily buffered this cycle — verified every git step via file-redirect + markers to avoid acting on stale output.

## North-star delta
- First **executable** P2 artifact: the learned-dynamics scaffold P2 is defined by now exists (was "no code yet" last cycle).
- Epistemic-uncertainty hook (ensemble std) is in place — seeds a P3 risk channel for free.
- No closed-loop movement yet: model is untrained and not wired into MPPI rollout.

## Key learnings
- torch is absent in the executor/CI env → keep learned-model code import-isolated and tests skip-guarded so the torch-free core still validates each cycle.
- The residual target convention is `s_next - f_nominal(s,a)`; the data pipeline must compute it against this exact nominal model — locks the next TODO's spec.
- Notion MCP returned empty all cycle (outage); fell back to TODO.md/STATE.md as the candidate pool. Bookkeeping deferred to retry.

## Recommended next 1–3 priorities
1. Training data pipeline: collect `(s, a, s_next)` from sim rollouts, store residual target `s_next - f_nominal(s,a)`.
2. Ensemble trainer: per-member bootstrap/seed, MSE (then NLL) loss, save/load checkpoint.
3. MPPI rollout hook: query `g_theta` per sampled trajectory, fold epistemic std into cost.

## Artifacts
- PR: https://github.com/Geonhee-LEE/Representation-Aware-MPPI/pull/42 (autoresearch/p2-residual-dynamics-mlp-scaffold)
- Files touched: learning/dynamics/{__init__,nominal,residual_model}.py, learning/dynamics/test/{__init__,test_nominal,test_residual_model}.py, learning/dynamics/README.md, results/p2-residual-dynamics-mlp-scaffold.tsv, RESULTS.md
- TSV row appended: yes

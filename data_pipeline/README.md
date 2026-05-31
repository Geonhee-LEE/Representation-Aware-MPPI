# data_pipeline — residual-dynamics training data

Produces `(state, action, next_state, dt)` transitions for the residual
dynamics learner (`learning.residual.ResidualEnsemble`). Decoupled from the
model code on purpose: this pipeline only emits **ground-truth** transitions;
the trainer computes its target as `delta = next_state - nominal(state, action)`.

## Tuple schema (contract, `SCHEMA_VERSION = 1`)

| field | shape | meaning |
|---|---|---|
| `state` | `(5,)` | `[x, y, theta, v, omega]` (SE(2) pose + body twist) |
| `action` | `(2,)` | `[v_cmd, omega_cmd]` commanded body twist |
| `next_state` | `(5,)` | observed next state (ground truth) |
| `dt` | scalar | integration timestep (s) |

Stacked on disk as a compressed `.npz` with arrays `states`, `actions`,
`next_states`, `dts`, plus `schema_version`. Conventions match
`learning/nominal.py` and `learning/residual.py`.

## Components

- `replay_buffer.py` — `ReplayBuffer`: `add` / `add_rollout` / `as_arrays` /
  `stats` / `save` / `load`. numpy-only, no torch.
- `synthetic_plant.py` — `true_plant_step`: a diff-drive plant with
  **deliberately unmodeled** effects (drag, slip, lateral drift) so there is a
  real residual to learn. Stand-in for sim/rosbag data; replace once real
  rollout logging exists.
- `collect_scripted.py` — runs step / sine-sweep / random-walk excitations
  through the true plant and writes a dataset.

## Generate a dataset

```bash
python3 data_pipeline/collect_scripted.py \
    --episodes 12 --steps 200 --dt 0.1 --seed 0 \
    --out data/replay_scripted.npz
```

Output `.npz` is gitignored (`data/*.npz`); regenerate from `--seed` for
reproducibility.

## How the trainer will consume it

```python
import numpy as np
from data_pipeline.replay_buffer import ReplayBuffer
from learning.nominal import nominal_step

buf = ReplayBuffer.load("data/replay_scripted.npz")
states, actions, next_states, dts = buf.as_arrays()
features = np.concatenate([states, actions], axis=1)          # (N, 7)
nominal_next = np.stack([nominal_step(s, a, dt) for s, a, dt
                         in zip(states, actions, dts)])
targets = next_states - nominal_next                          # (N, 5)
```

`features`/`targets` feed `ResidualEnsemble` (FEATURE_DIM=7, RESIDUAL_DIM=5).

> **Cross-branch note:** `learning/` currently lives on the
> `autoresearch/p2-residual-dynamics-mlp-scaffold` branch (not yet on `main`).
> This pipeline is intentionally importable without it; the trainer glue lands
> once both are on `main`.

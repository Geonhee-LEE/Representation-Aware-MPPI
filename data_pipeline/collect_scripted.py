"""Generate scripted diff-drive rollouts into a replay buffer.

Runs a handful of excitation patterns (step, sine-sweep, random-walk
commands) through the synthetic true plant and logs every transition. This
gives the residual trainer a diverse-enough dataset to fit the unmodeled
dynamics gap before sim/rosbag logging exists.

Usage::

    python3 data_pipeline/collect_scripted.py \
        --episodes 12 --steps 200 --dt 0.1 --out data/replay_scripted.npz

The output ``.npz`` is gitignored (``data/*.npz``); only the generator is
versioned, so the dataset is reproducible from ``--seed``.
"""

from __future__ import annotations

import argparse

import numpy as np

from data_pipeline.replay_buffer import ReplayBuffer
from data_pipeline.synthetic_plant import true_plant_step


def _action_sequence(kind: str, steps: int, rng: np.random.Generator):
    """Return a (steps, 2) array of [v_cmd, omega_cmd] for an excitation."""
    t = np.arange(steps)
    if kind == "step":
        v = np.where(t < steps // 2, 0.4, 0.8)
        w = np.where(t < steps // 3, 0.0, 0.5)
    elif kind == "sine":
        v = 0.5 + 0.3 * np.sin(2 * np.pi * t / 40.0)
        w = 0.6 * np.sin(2 * np.pi * t / 25.0)
    elif kind == "random_walk":
        v = np.clip(np.cumsum(rng.normal(0, 0.05, steps)) + 0.5, 0.0, 1.0)
        w = np.clip(np.cumsum(rng.normal(0, 0.08, steps)), -1.0, 1.0)
    else:
        raise ValueError(f"unknown excitation kind: {kind}")
    return np.stack([v, w], axis=1)


def collect(episodes: int, steps: int, dt: float, seed: int) -> ReplayBuffer:
    """Roll out scripted excitations through the true plant into a buffer."""
    rng = np.random.default_rng(seed)
    kinds = ["step", "sine", "random_walk"]
    buf = ReplayBuffer()
    for ep in range(episodes):
        kind = kinds[ep % len(kinds)]
        actions = _action_sequence(kind, steps, rng)
        # Randomized but bounded initial state.
        state = np.array([
            rng.uniform(-1, 1), rng.uniform(-1, 1),
            rng.uniform(-np.pi, np.pi), 0.0, 0.0,
        ])
        for k in range(steps):
            action = actions[k]
            next_state = true_plant_step(state, action, dt=dt)
            buf.add(state, action, next_state, dt)
            state = next_state
    return buf


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--episodes", type=int, default=12)
    ap.add_argument("--steps", type=int, default=200)
    ap.add_argument("--dt", type=float, default=0.1)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--out", type=str, default="data/replay_scripted.npz")
    args = ap.parse_args()

    buf = collect(args.episodes, args.steps, args.dt, args.seed)
    buf.save(args.out)
    stats = buf.stats()
    print(f"collected {stats['n']} transitions -> {args.out}")
    print(f"  state_mean          = {stats['state_mean']}")
    print(f"  action_mean         = {stats['action_mean']}")
    print(f"  step_delta_abs_mean = {stats['step_delta_abs_mean']}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Generate synthetic unicycle trajectory dataset for TCFM training bootstrap.

Differential-drive kinematics with proportional goal-tracking controller
+ process noise. Outputs TCFM-compatible .npz format.

Usage:
    python scripts/gen_unicycle_dataset.py --num-trajs 1000 --output data/unicycle_train.npz
    python scripts/gen_unicycle_dataset.py --num-trajs 200  --output data/unicycle_val.npz
"""
from __future__ import annotations

import argparse
import math
import os
from pathlib import Path

import numpy as np


def unicycle_step(
    state: np.ndarray, action: np.ndarray, dt: float
) -> np.ndarray:
    x, y, theta, v, omega = state
    v_cmd, omega_cmd = action
    tau_v, tau_omega = 0.2, 0.1
    v_new = v + (v_cmd - v) / tau_v * dt
    omega_new = omega + (omega_cmd - omega) / tau_omega * dt
    v_avg = (v + v_new) / 2.0
    omega_avg = (omega + omega_new) / 2.0
    theta_new = theta + omega_avg * dt
    x_new = x + v_avg * math.cos((theta + theta_new) / 2.0) * dt
    y_new = y + v_avg * math.sin((theta + theta_new) / 2.0) * dt
    return np.array([x_new, y_new, theta_new, v_new, omega_new])


def proportional_controller(
    state: np.ndarray,
    goal: np.ndarray,
    rng: np.random.Generator,
    v_max: float = 0.5,
    omega_max: float = 1.5,
    noise_v: float = 0.05,
    noise_omega: float = 0.1,
) -> np.ndarray:
    x, y, theta, _v, _omega = state
    dx = goal[0] - x
    dy = goal[1] - y
    dist = math.sqrt(dx * dx + dy * dy)
    angle_to_goal = math.atan2(dy, dx)
    heading_err = angle_to_goal - theta
    heading_err = math.atan2(math.sin(heading_err), math.cos(heading_err))

    kp_v = 1.0
    kp_omega = 2.5
    v_cmd = min(kp_v * dist, v_max)
    if abs(heading_err) > math.pi / 4:
        v_cmd *= 0.3
    omega_cmd = np.clip(kp_omega * heading_err, -omega_max, omega_max)

    v_cmd += rng.normal(0, noise_v)
    omega_cmd += rng.normal(0, noise_omega)
    v_cmd = np.clip(v_cmd, 0.0, v_max)
    omega_cmd = np.clip(omega_cmd, -omega_max, omega_max)
    return np.array([v_cmd, omega_cmd])


def generate_trajectory(
    rng: np.random.Generator,
    horizon: int,
    dt: float,
    arena_size: float = 5.0,
) -> dict:
    start = np.array([
        rng.uniform(-arena_size, arena_size),
        rng.uniform(-arena_size, arena_size),
        rng.uniform(-math.pi, math.pi),
        0.0,
        0.0,
    ])
    min_goal_dist = 1.5
    while True:
        goal = rng.uniform(-arena_size, arena_size, size=2)
        if np.linalg.norm(goal - start[:2]) >= min_goal_dist:
            break

    states = np.zeros((horizon, 5))
    actions = np.zeros((horizon, 2))
    states[0] = start

    for t in range(horizon - 1):
        action = proportional_controller(states[t], goal, rng)
        actions[t] = action
        states[t + 1] = unicycle_step(states[t], action, dt)
        if np.linalg.norm(states[t + 1, :2] - goal) < 0.15:
            states[t + 1:] = states[t + 1]
            break

    return {"states": states, "actions": actions, "goal": goal}


def normalize_minmax(data: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    mins = data.min(axis=(0, 1))
    maxs = data.max(axis=(0, 1))
    span = maxs - mins
    span[span < 1e-8] = 1.0
    normalized = 2.0 * (data - mins) / span - 1.0
    return normalized, mins, maxs


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--num-trajs", type=int, default=1000)
    parser.add_argument("--horizon", type=int, default=64)
    parser.add_argument("--dt", type=float, default=0.1)
    parser.add_argument("--arena-size", type=float, default=3.0)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--output", type=str, default="data/unicycle_train.npz")
    parser.add_argument("--skip-normalize", action="store_true")
    args = parser.parse_args()

    rng = np.random.default_rng(args.seed)
    all_states = []
    all_actions = []
    all_goals = []

    reached = 0
    for i in range(args.num_trajs):
        traj = generate_trajectory(rng, args.horizon, args.dt, args.arena_size)
        all_states.append(traj["states"])
        all_actions.append(traj["actions"])
        all_goals.append(traj["goal"])
        final_dist = np.linalg.norm(traj["states"][-1, :2] - traj["goal"])
        if final_dist < 0.15:
            reached += 1

    states = np.stack(all_states)   # [N, T, 5]
    actions = np.stack(all_actions) # [N, T, 2]
    goals = np.stack(all_goals)     # [N, 2]

    save_dict: dict = {
        "states_raw": states,
        "actions_raw": actions,
        "goals": goals,
        "dt": np.float64(args.dt),
        "horizon": np.int64(args.horizon),
        "state_dim": np.int64(5),
        "action_dim": np.int64(2),
        "state_labels": np.array(["x", "y", "theta", "v", "omega"]),
        "action_labels": np.array(["v_cmd", "omega_cmd"]),
    }

    if not args.skip_normalize:
        states_norm, s_mins, s_maxs = normalize_minmax(states)
        actions_norm, a_mins, a_maxs = normalize_minmax(actions)
        save_dict.update({
            "states": states_norm,
            "actions": actions_norm,
            "norm_state_min": s_mins,
            "norm_state_max": s_maxs,
            "norm_action_min": a_mins,
            "norm_action_max": a_maxs,
        })
    else:
        save_dict["states"] = states
        save_dict["actions"] = actions

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(str(out_path), **save_dict)

    print(f"Generated {args.num_trajs} trajectories → {out_path}")
    print(f"  states:  {states.shape}  (x, y, θ, v, ω)")
    print(f"  actions: {actions.shape}  (v_cmd, ω_cmd)")
    print(f"  goals:   {goals.shape}")
    print(f"  horizon: {args.horizon} steps @ dt={args.dt}s ({args.horizon * args.dt:.1f}s)")
    print(f"  goal reached: {reached}/{args.num_trajs} ({100*reached/args.num_trajs:.1f}%)")
    if not args.skip_normalize:
        print(f"  normalized to [-1, 1] (TCFM-compatible)")
        print(f"  state range:  min={s_mins}, max={s_maxs}")
        print(f"  action range: min={a_mins}, max={a_maxs}")


if __name__ == "__main__":
    main()

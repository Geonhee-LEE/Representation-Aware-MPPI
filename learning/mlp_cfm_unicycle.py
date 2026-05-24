"""MLP-based Conditional Flow Matching velocity field for unicycle dynamics.

Flow Planner-style architecture: sinusoidal time embedding + FiLM conditioning.
Self-contained — generates inline synthetic data, no external file dependencies.

Usage:
    python learning/mlp_cfm_unicycle.py [--epochs 200] [--n-trajs 500]
"""

import argparse
import math
from pathlib import Path

import torch
import torch.nn as nn
import torch.nn.functional as F


class SinusoidalTimeEmbedding(nn.Module):
    def __init__(self, dim: int):
        super().__init__()
        self.dim = dim

    def forward(self, t: torch.Tensor) -> torch.Tensor:
        half = self.dim // 2
        freqs = torch.exp(-math.log(10000) * torch.arange(half, device=t.device) / half)
        args = t[:, None] * freqs[None, :]
        return torch.cat([args.sin(), args.cos()], dim=-1)


class FiLMBlock(nn.Module):
    """Feature-wise Linear Modulation: scale + shift from conditioning."""

    def __init__(self, feature_dim: int, cond_dim: int):
        super().__init__()
        self.proj = nn.Linear(cond_dim, feature_dim * 2)

    def forward(self, x: torch.Tensor, cond: torch.Tensor) -> torch.Tensor:
        gamma, beta = self.proj(cond).chunk(2, dim=-1)
        return x * (1 + gamma) + beta


class MLPCFMVelocityField(nn.Module):
    """MLP velocity field v(x_t, t; cond) for conditional flow matching.

    Architecture mirrors Flow Planner's backbone: time embedding → concat with
    noisy sample → FiLM-conditioned hidden layers → output velocity.
    """

    def __init__(self, state_dim: int = 5, action_dim: int = 2, hidden: int = 128, time_dim: int = 32):
        super().__init__()
        self.time_embed = SinusoidalTimeEmbedding(time_dim)
        cond_dim = state_dim + action_dim + time_dim

        self.input_net = nn.Sequential(
            nn.Linear(state_dim + time_dim, hidden),
            nn.SiLU(),
            nn.Linear(hidden, hidden),
            nn.SiLU(),
        )
        self.film1 = FiLMBlock(hidden, cond_dim)
        self.mid_net = nn.Sequential(nn.Linear(hidden, hidden), nn.SiLU())
        self.film2 = FiLMBlock(hidden, cond_dim)
        self.output_head = nn.Linear(hidden, state_dim)

    def forward(self, x_t: torch.Tensor, t: torch.Tensor, state: torch.Tensor, action: torch.Tensor) -> torch.Tensor:
        t_emb = self.time_embed(t)
        cond = torch.cat([state, action, t_emb], dim=-1)
        h = self.input_net(torch.cat([x_t, t_emb], dim=-1))
        h = self.film1(h, cond)
        h = self.mid_net(h)
        h = self.film2(h, cond)
        return self.output_head(h)


def unicycle_step(state: torch.Tensor, action: torch.Tensor, dt: float = 0.1) -> torch.Tensor:
    """Deterministic unicycle dynamics: state=(x,y,θ,v,ω), action=(v_cmd,ω_cmd)."""
    x, y, theta, v, omega = state.unbind(-1)
    v_cmd, omega_cmd = action.unbind(-1)
    tau = 0.3
    v_new = v + (v_cmd - v) / tau * dt
    omega_new = omega + (omega_cmd - omega) / tau * dt
    theta_new = theta + omega_new * dt
    x_new = x + v_new * torch.cos(theta_new) * dt
    y_new = y + v_new * torch.sin(theta_new) * dt
    return torch.stack([x_new, y_new, theta_new, v_new, omega_new], dim=-1)


def generate_inline_dataset(n_trajs: int = 500, horizon: int = 20, dt: float = 0.1) -> tuple:
    """Generate synthetic unicycle trajectories with random actions."""
    states_all, actions_all, next_states_all = [], [], []
    for _ in range(n_trajs):
        state = torch.zeros(5)
        state[0] = torch.randn(1).item() * 2
        state[1] = torch.randn(1).item() * 2
        state[2] = torch.rand(1).item() * 2 * math.pi - math.pi
        for _ in range(horizon):
            action = torch.tensor([
                torch.rand(1).item() * 1.0 - 0.1,
                torch.randn(1).item() * 0.5,
            ])
            next_state = unicycle_step(state, action, dt)
            states_all.append(state)
            actions_all.append(action)
            next_states_all.append(next_state)
            state = next_state
    return torch.stack(states_all), torch.stack(actions_all), torch.stack(next_states_all)


def cfm_loss(model: MLPCFMVelocityField, x0: torch.Tensor, x1: torch.Tensor,
             state: torch.Tensor, action: torch.Tensor) -> torch.Tensor:
    """Optimal-transport CFM loss: MSE between predicted and true velocity along linear path."""
    t = torch.rand(x0.shape[0], device=x0.device)
    x_t = (1 - t[:, None]) * x0 + t[:, None] * x1
    target_v = x1 - x0
    pred_v = model(x_t, t, state, action)
    return F.mse_loss(pred_v, target_v)


@torch.no_grad()
def sample_cfm(model: MLPCFMVelocityField, state: torch.Tensor, action: torch.Tensor,
               n_steps: int = 20) -> torch.Tensor:
    """Euler integration of the learned velocity field from noise → prediction."""
    x = torch.randn(state.shape[0], 5, device=state.device)
    dt = 1.0 / n_steps
    for i in range(n_steps):
        t = torch.full((state.shape[0],), i * dt, device=state.device)
        v = model(x, t, state, action)
        x = x + v * dt
    return x


def train(epochs: int = 200, n_trajs: int = 500, lr: float = 1e-3, batch_size: int = 256):
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Device: {device}")

    states, actions, next_states = generate_inline_dataset(n_trajs)
    delta_states = next_states - states
    states, actions, delta_states = states.to(device), actions.to(device), delta_states.to(device)

    n_train = int(len(states) * 0.8)
    train_s, train_a, train_d = states[:n_train], actions[:n_train], delta_states[:n_train]
    val_s, val_a, val_d = states[n_train:], actions[n_train:], delta_states[n_train:]

    model = MLPCFMVelocityField().to(device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=lr)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=epochs)

    best_val_loss = float("inf")
    for epoch in range(epochs):
        model.train()
        perm = torch.randperm(n_train, device=device)
        epoch_loss = 0.0
        n_batches = 0
        for i in range(0, n_train, batch_size):
            idx = perm[i:i + batch_size]
            x0 = torch.randn_like(train_d[idx])
            loss = cfm_loss(model, x0, train_d[idx], train_s[idx], train_a[idx])
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
            epoch_loss += loss.item()
            n_batches += 1
        scheduler.step()

        if (epoch + 1) % 20 == 0 or epoch == 0:
            model.eval()
            with torch.no_grad():
                x0_val = torch.randn_like(val_d)
                val_loss = cfm_loss(model, x0_val, val_d, val_s, val_a).item()
                pred = sample_cfm(model, val_s, val_a)
                mae = (pred - val_d).abs().mean().item()
            print(f"Epoch {epoch+1:3d} | train_loss={epoch_loss/n_batches:.4f} | val_loss={val_loss:.4f} | sample_MAE={mae:.4f}")
            if val_loss < best_val_loss:
                best_val_loss = val_loss

    model.eval()
    pred = sample_cfm(model, val_s, val_a)
    final_mae = (pred - val_d).abs().mean().item()
    per_dim_mae = (pred - val_d).abs().mean(dim=0)
    print(f"\nFinal validation MAE: {final_mae:.4f}")
    print(f"Per-dim MAE (x,y,θ,v,ω): {per_dim_mae.cpu().numpy().round(4)}")
    print(f"Best val CFM loss: {best_val_loss:.4f}")

    out_dir = Path("learning/checkpoints")
    out_dir.mkdir(parents=True, exist_ok=True)
    ckpt_path = out_dir / "mlp_cfm_unicycle.pt"
    torch.save({"model_state": model.state_dict(), "val_mae": final_mae, "best_val_loss": best_val_loss}, ckpt_path)
    print(f"Checkpoint saved: {ckpt_path}")
    return final_mae, best_val_loss


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--epochs", type=int, default=200)
    parser.add_argument("--n-trajs", type=int, default=500)
    args = parser.parse_args()
    train(epochs=args.epochs, n_trajs=args.n_trajs)

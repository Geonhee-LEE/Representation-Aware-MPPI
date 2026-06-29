"""Energy-based regularizer for residual dynamics (arxiv 2604.14678).

Prevents learned residual dynamics from destabilizing MPPI rollouts
by penalizing energy increases relative to the nominal model.

Usage:
    from learning.energy_regularizer import (
        EnergyRegularizer, UnicycleNominalDynamics, ResidualDynamicsNet,
    )

Run standalone for a sanity-check demo:
    python -m learning.energy_regularizer
"""

import math

import torch
import torch.nn as nn


class UnicycleNominalDynamics:
    """Discrete-time unicycle with first-order velocity lag.

    State: [x, y, theta, v, omega]  (5-dim)
    Action: [v_cmd, omega_cmd]      (2-dim)
    """

    def __init__(self, dt: float = 0.1, tau_v: float = 0.2, tau_omega: float = 0.1):
        self.dt = dt
        self.tau_v = tau_v
        self.tau_omega = tau_omega

    def forward(self, state: torch.Tensor, action: torch.Tensor) -> torch.Tensor:
        x, y, theta, v, omega = state.unbind(dim=-1)
        v_cmd, omega_cmd = action.unbind(dim=-1)

        v_next = v + (v_cmd - v) * (self.dt / self.tau_v)
        omega_next = omega + (omega_cmd - omega) * (self.dt / self.tau_omega)

        x_next = x + v * torch.cos(theta) * self.dt
        y_next = y + v * torch.sin(theta) * self.dt
        theta_next = theta + omega * self.dt

        return torch.stack([x_next, y_next, theta_next, v_next, omega_next], dim=-1)


class ResidualDynamicsNet(nn.Module):
    """MLP residual: delta_x = f_res(x, u; theta)."""

    def __init__(self, state_dim: int = 5, action_dim: int = 2, hidden_dim: int = 64):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(state_dim + action_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, state_dim),
        )
        nn.init.zeros_(self.net[-1].weight)
        nn.init.zeros_(self.net[-1].bias)

    def forward(self, state: torch.Tensor, action: torch.Tensor) -> torch.Tensor:
        return self.net(torch.cat([state, action], dim=-1))


class EnergyRegularizer:
    """Hinge-loss energy regularizer for residual dynamics.

    L_energy = mean(max(0, V(x_combined) - V(x_nominal)))

    Only activates when the residual *increases* energy — energy-neutral
    or energy-reducing corrections pass through unpenalized.
    """

    def __init__(self, energy_fn=None):
        self.energy_fn = energy_fn or self.kinetic_energy

    @staticmethod
    def kinetic_energy(state: torch.Tensor) -> torch.Tensor:
        """V = 0.5 * (v^2 + omega^2). Goal-free, prevents velocity blow-up."""
        v = state[..., 3]
        omega = state[..., 4]
        return 0.5 * (v**2 + omega**2)

    @staticmethod
    def quadratic_goal_energy(
        state: torch.Tensor, goal: torch.Tensor | None = None, alpha: float = 0.1
    ) -> torch.Tensor:
        """V = ||pos - goal||^2 + alpha * (v^2 + omega^2)."""
        if goal is None:
            goal = torch.zeros(2, device=state.device)
        pos = state[..., :2]
        v, omega = state[..., 3], state[..., 4]
        return ((pos - goal) ** 2).sum(dim=-1) + alpha * (v**2 + omega**2)

    def compute(
        self, nominal_next: torch.Tensor, combined_next: torch.Tensor
    ) -> torch.Tensor:
        """Compute regularization loss (scalar)."""
        e_nom = self.energy_fn(nominal_next)
        e_comb = self.energy_fn(combined_next)
        return torch.relu(e_comb - e_nom).mean()


class EnergyRegularizedTrainer:
    """Training loop: MSE data loss + energy regularization."""

    def __init__(
        self,
        nominal: UnicycleNominalDynamics,
        residual: ResidualDynamicsNet,
        lambda_energy: float = 0.1,
        lr: float = 1e-3,
    ):
        self.nominal = nominal
        self.residual = residual
        self.regularizer = EnergyRegularizer()
        self.lambda_energy = lambda_energy
        self.optimizer = torch.optim.Adam(self.residual.parameters(), lr=lr)

    def train_step(
        self,
        states: torch.Tensor,
        actions: torch.Tensor,
        next_states_true: torch.Tensor,
    ) -> dict:
        self.optimizer.zero_grad()

        nominal_next = self.nominal.forward(states, actions)
        residual = self.residual(states, actions)
        combined_next = nominal_next + residual

        l_data = nn.functional.mse_loss(combined_next, next_states_true)
        l_energy = self.regularizer.compute(nominal_next, combined_next)

        loss = l_data + self.lambda_energy * l_energy
        loss.backward()
        self.optimizer.step()

        return {
            "loss": loss.item(),
            "L_data": l_data.item(),
            "L_energy": l_energy.item(),
        }


def demo():
    """Sanity check: train on synthetic data, verify residual stays bounded."""
    torch.manual_seed(42)

    nominal = UnicycleNominalDynamics(dt=0.1)
    residual = ResidualDynamicsNet()
    trainer = EnergyRegularizedTrainer(nominal, residual, lambda_energy=0.5)

    batch = 256
    states = torch.randn(batch, 5) * torch.tensor([2.0, 2.0, math.pi, 0.5, 0.3])
    actions = torch.randn(batch, 2) * torch.tensor([0.5, 0.3])

    with torch.no_grad():
        true_next = nominal.forward(states, actions) + 0.01 * torch.randn(batch, 5)

    for step in range(100):
        metrics = trainer.train_step(states, actions, true_next)
        if step % 20 == 0:
            print(
                f"step {step:3d}  loss={metrics['loss']:.6f}  "
                f"data={metrics['L_data']:.6f}  energy={metrics['L_energy']:.6f}"
            )

    with torch.no_grad():
        res = residual(states[:5], actions[:5])
        mag = res.abs().mean().item()
        print(f"\nResidual magnitude: {mag:.4f} (target ~0.01)")

    print("\n--- Multi-step rollout stability check ---")
    with torch.no_grad():
        x = torch.tensor([[0.0, 0.0, 0.0, 0.3, 0.0]])
        u = torch.tensor([[0.5, 0.1]])
        energies_nom, energies_comb = [], []
        for _ in range(64):
            x_nom = nominal.forward(x, u)
            x_comb = x_nom + residual(x, u)
            energies_nom.append(EnergyRegularizer.kinetic_energy(x_nom).item())
            energies_comb.append(EnergyRegularizer.kinetic_energy(x_comb).item())
            x = x_comb

        drift = max(energies_comb) - max(energies_nom)
        print(f"Peak energy — nominal: {max(energies_nom):.4f}, combined: {max(energies_comb):.4f}")
        print(f"Energy drift: {drift:+.4f} ({'STABLE' if drift < 0.05 else 'UNSTABLE'})")


if __name__ == "__main__":
    demo()

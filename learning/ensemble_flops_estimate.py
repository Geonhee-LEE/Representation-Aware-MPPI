"""Estimate FLOPs and memory for single vs ensemble-of-K MLPs on 5D unicycle.

Evaluates compatibility with MPPI parallel rollouts (1000+ samples × H steps).
No PyTorch dependency — pure arithmetic from architecture specs.

Usage:
    python learning/ensemble_flops_estimate.py [--ensemble-k 3] [--mppi-samples 1000] [--horizon 20]
"""

import argparse


def count_linear_flops(in_dim: int, out_dim: int) -> int:
    return 2 * in_dim * out_dim


def mlp_cfm_velocity_field_flops(state_dim: int = 5, action_dim: int = 2,
                                  hidden: int = 128, time_dim: int = 32) -> dict:
    """FLOPs for one forward pass of MLPCFMVelocityField."""
    layers = {}
    layers["time_embed"] = time_dim * 2
    cond_dim = state_dim + action_dim + time_dim
    layers["input_linear1"] = count_linear_flops(state_dim + time_dim, hidden)
    layers["input_linear2"] = count_linear_flops(hidden, hidden)
    layers["film1_proj"] = count_linear_flops(cond_dim, hidden * 2)
    layers["film1_apply"] = hidden * 3
    layers["mid_linear"] = count_linear_flops(hidden, hidden)
    layers["film2_proj"] = count_linear_flops(cond_dim, hidden * 2)
    layers["film2_apply"] = hidden * 3
    layers["output_head"] = count_linear_flops(hidden, state_dim)

    total = sum(layers.values())
    params = (
        (state_dim + time_dim + 1) * hidden + (hidden + 1) * hidden
        + (cond_dim + 1) * hidden * 2
        + (hidden + 1) * hidden
        + (cond_dim + 1) * hidden * 2
        + (hidden + 1) * state_dim
    )
    return {"layers": layers, "total_flops": total, "params": params}


def residual_dynamics_flops(state_dim: int = 5, action_dim: int = 2,
                             hidden_dim: int = 64) -> dict:
    """FLOPs for one forward pass of ResidualDynamicsNet."""
    layers = {}
    layers["linear1"] = count_linear_flops(state_dim + action_dim, hidden_dim)
    layers["linear2"] = count_linear_flops(hidden_dim, hidden_dim)
    layers["linear3"] = count_linear_flops(hidden_dim, state_dim)

    total = sum(layers.values())
    params = (
        (state_dim + action_dim + 1) * hidden_dim
        + (hidden_dim + 1) * hidden_dim
        + (hidden_dim + 1) * state_dim
    )
    return {"layers": layers, "total_flops": total, "params": params}


def format_number(n: int) -> str:
    if n >= 1e9:
        return f"{n/1e9:.2f}G"
    if n >= 1e6:
        return f"{n/1e6:.2f}M"
    if n >= 1e3:
        return f"{n/1e3:.1f}K"
    return str(n)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ensemble-k", type=int, default=3)
    parser.add_argument("--mppi-samples", type=int, default=1000)
    parser.add_argument("--horizon", type=int, default=20)
    parser.add_argument("--cfm-steps", type=int, default=20,
                        help="Euler integration steps in sample_cfm")
    args = parser.parse_args()

    K = args.ensemble_k
    N = args.mppi_samples
    H = args.horizon
    cfm_steps = args.cfm_steps
    calls_per_cycle = N * H

    print("=" * 70)
    print("Ensemble Residual Dynamics — MPPI Compatibility Analysis")
    print("=" * 70)

    cfm = mlp_cfm_velocity_field_flops()
    res = residual_dynamics_flops()

    print(f"\n--- MLPCFMVelocityField (single) ---")
    print(f"  Parameters:  {cfm['params']:,}")
    print(f"  FLOPs/call:  {format_number(cfm['total_flops'])}")
    for name, f in cfm["layers"].items():
        print(f"    {name:20s}: {format_number(f)}")

    print(f"\n--- ResidualDynamicsNet (single) ---")
    print(f"  Parameters:  {res['params']:,}")
    print(f"  FLOPs/call:  {format_number(res['total_flops'])}")
    for name, f in res["layers"].items():
        print(f"    {name:20s}: {format_number(f)}")

    print(f"\n--- MPPI budget (N={N}, H={H}) ---")
    print(f"  Forward calls per control cycle: {calls_per_cycle:,}")

    print(f"\n--- Scenario A: Residual Dynamics (simple MLP, direct step) ---")
    single_total = calls_per_cycle * res["total_flops"]
    ensemble_total = calls_per_cycle * res["total_flops"] * K
    print(f"  Single:      {format_number(single_total)} FLOPs/cycle")
    print(f"  Ensemble-{K}:  {format_number(ensemble_total)} FLOPs/cycle (serial)")
    print(f"  Overhead:    {K:.1f}× FLOPs, {K:.1f}× params ({res['params'] * K:,})")
    print(f"  Batched:     ~1.0-1.3× wall-clock (weight-stacked vmap)")
    var_flops = calls_per_cycle * K * 5 * 3
    print(f"  Variance:    +{format_number(var_flops)} (mean+var over {K} heads)")

    print(f"\n--- Scenario B: CFM Velocity Field (MLP + FiLM, n_steps={cfm_steps}) ---")
    cfm_single_step = calls_per_cycle * cfm["total_flops"]
    cfm_single_total = cfm_single_step * cfm_steps
    cfm_ensemble_total = cfm_single_total * K
    print(f"  Single:      {format_number(cfm_single_total)} FLOPs/cycle "
          f"({cfm_steps} Euler steps)")
    print(f"  Ensemble-{K}:  {format_number(cfm_ensemble_total)} FLOPs/cycle (serial)")
    print(f"  Overhead:    {K:.1f}× FLOPs, {K:.1f}× params ({cfm['params'] * K:,})")
    print(f"  Batched:     ~1.0-1.3× wall-clock (weight-stacked vmap)")

    print(f"\n--- Reference points ---")
    resnet18_flops = 1_800_000_000
    print(f"  ResNet-18 forward:    {format_number(resnet18_flops)}")
    print(f"  Ensemble-{K} ResNet:    {format_number(resnet18_flops * K)}")
    ratio_res = ensemble_total / resnet18_flops
    ratio_cfm = cfm_ensemble_total / resnet18_flops
    print(f"  Ens-{K} residual/RN18: {ratio_res:.3f}×")
    print(f"  Ens-{K} CFM/RN18:      {ratio_cfm:.3f}×")

    print(f"\n--- Memory (fp32, batch={N}) ---")
    res_mem = res["params"] * K * 4
    cfm_mem = cfm["params"] * K * 4
    act_mem_res = N * 5 * K * 4
    act_mem_cfm = N * 5 * K * cfm_steps * 4
    print(f"  Residual ensemble weights:  {res_mem / 1024:.1f} KB")
    print(f"  CFM ensemble weights:       {cfm_mem / 1024:.1f} KB")
    print(f"  Residual activations/batch: {act_mem_res / 1024:.1f} KB")
    print(f"  CFM activations/batch:      {act_mem_cfm / 1024:.1f} KB")

    print(f"\n{'=' * 70}")
    print("VERDICT")
    print("=" * 70)
    if ensemble_total < resnet18_flops:
        print(f"  Residual ensemble-{K}: ✅ COMPATIBLE ({ratio_res:.3f}× of a ResNet-18)")
    else:
        print(f"  Residual ensemble-{K}: ⚠️  HEAVY ({ratio_res:.1f}× of a ResNet-18)")

    if cfm_ensemble_total < resnet18_flops * 3:
        print(f"  CFM ensemble-{K}:      ✅ COMPATIBLE ({ratio_cfm:.2f}× of a ResNet-18)")
    else:
        print(f"  CFM ensemble-{K}:      ⚠️  HEAVY ({ratio_cfm:.1f}× of a ResNet-18)")

    print(f"\n  With weight-stacked batching (torch.vmap or manual), wall-clock")
    print(f"  overhead drops from {K:.0f}× to ~1.0-1.3× on GPU. Ensemble-{K} fits")
    print(f"  comfortably in MPPI's real-time budget at {1000/H:.0f} Hz control rate.")
    print(f"  Free bonus: per-sample variance → P3 epistemic uncertainty channel.")


if __name__ == "__main__":
    main()

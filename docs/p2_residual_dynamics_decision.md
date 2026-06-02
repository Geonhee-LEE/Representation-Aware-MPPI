# P2 Residual-Dynamics Architecture — Decision Matrix

_Phase P2 · 2026-05-31 · consolidates the residual-dynamics research fan-out into a single build-first decision (see [`decisions.md`](decisions.md) D-009)._

## Why this doc exists

P2's design space fragmented across ~8 research entries and 5 open analysis PRs
(#23 unicycle-dataset, #24 energy-reg, #25 flow-planner-map, #26 mlp-cfm,
#27 ensemble-residual) with **no convergence on what to actually build**. The
bottleneck is no longer "no training data" (the synthetic-unicycle generator,
#23, addresses that) — it is **deciding which residual architecture gets the
first implementation**. This matrix collapses the candidates onto the axes that
matter for *our* constraints (MPPI batched rollout, synthetic-unicycle
bootstrap, P3 uncertainty-channel synergy) and commits to one.

## Candidate set

| # | Candidate | Source | Residual form |
|---|---|---|---|
| C1 | **MLP-ensemble residual** | doi:10.3390/s26010340 (#27) | K small MLP heads, bootstrap-resampled |
| C2 | **STRIDE** nominal(LNN)+residual(CFM) | arXiv 2603.08478 | Conditional-Flow-Matching residual |
| C3 | **ICODE** continuous-time NODE | feed | Neural-ODE residual |
| C4 | **SFKD** env-Koopman + ISS residual | arXiv 2605.16754 | contraction-constrained NN, ISS cert |
| C5 | **T2S-MPC** time-embedded two-timescale | arXiv 2605.24852 | online residual, slow base + fast track |
| C6 | **Adapt-on-the-Fly** low-rank online | arXiv 2604.04039 | offline net + low-rank 2nd-order online update |
| C7 | **MAML** meta-residual | arXiv 2504.16369 | meta-learned fast adaptation |
| C8 | **Energy-reg** residual | arXiv 2604.14678 | MLP + energy-based regularizer |

Cross-cutting regularizer (not a standalone architecture): **MWM
Action-Conditioned Consistency** (arXiv 2603.07799) — a rollout-drift penalty
that can be bolted onto any of C1/C3/C8.

## Decision axes

| Axis | C1 ensemble | C2 STRIDE-CFM | C3 ICODE | C4 SFKD | C5 T2S | C6 low-rank | C7 MAML | C8 energy |
|---|---|---|---|---|---|---|---|---|
| Time-varying mismatch | ✗ (frozen) | ✗ | ✗ | partial (env-switch) | ✓✓ | ✓ | ✓ | ✗ |
| Offline→online adapt | offline | offline | offline | offline | online | online | online | offline |
| Stability certificate | ✗ | ✗ | ✗ | ✓✓ (ISS) | partial | ✗ | ✗ | partial (energy) |
| Uncertainty channel (→P3) | ✓✓ (var) | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| MPPI batched-rollout fit | ✓✓ (vectorized fwd) | ✗ (ODE solve/sample) | ✗ (ODE integ) | ✓ | ✓ | ✓ | ✓ | ✓✓ |
| Compute / real-time | ✓✓ | ✗ | ✗ | ✓ | ✓ | ✓ | ✓ | ✓✓ |
| Unicycle-bootstrap fit | ✓✓ | ✓ | ✓ | partial (needs env labels) | ✓ | ✓ | partial (task dist) | ✓✓ |
| Impl complexity (1=low) | 1 | 4 | 3 | 5 | 4 | 4 | 4 | 2 |

Legend: ✓✓ strong fit · ✓ workable · partial conditional · ✗ poor/absent.

## Decision (D-009)

**Build first: C1 — small MLP-ensemble residual (K=3), offline-frozen on the
synthetic-unicycle bootstrap (#23), wrapped for MPPI batched rollout.**

Rationale, ranked by our constraints:

1. **MPPI-rollout-native.** A forward MLP is a single vectorized matmul per
   rollout step — it drops into the existing batched-rollout loop with no ODE
   solver or sampling inner loop (kills C2/C3 for the *first* build).
2. **Bootstrappable today.** Trains directly on #23's `.npz` without env labels
   (rules out C4) or a task distribution (rules out C7 first).
3. **Free P3 synergy.** Ensemble variance → epistemic channel, the exact P3
   risk/uncertainty-field input — no other candidate gives this for free.
4. **Lowest complexity, fastest to a measurable result** — matches the
   project's "experiment speed > production polish" preference.

### Deferred upgrades (sequenced, not rejected)

- **U1 — distribution-shift probe.** Once C1 runs, measure offline-frozen
  degradation under a perturbed-unicycle (payload/drift) eval. This is the
  empirical trigger for online adaptation.
- **U2 — online adaptation.** If U1 shows decay, add **C6 low-rank online
  update** (cheapest) before the heavier **C5 two-timescale**. T2S only if the
  mismatch is shown to be *periodic/drifting*, not just constant-but-unknown.
- **U3 — stability certificate.** Adopt **C4 SFKD ISS** only if C1 rollouts
  destabilize the MPPI horizon (watch for blow-up in long-horizon rollouts);
  the ISS cert is insurance, not a day-1 need.
- **U4 — rollout-drift reg.** Bolt **MWM Action-Conditioned Consistency** onto
  C1 if multi-step rollout error compounds.
- **STRIDE-CFM (C2)** remains the *eventual* target once a learned generative
  residual is justified — but only after C1 establishes the analytic-nominal +
  MPPI-integration plumbing it would reuse.

## Open question carried to deliberations

Whether the nominal model for the residual should be the **analytic unicycle**
(simplest, our bootstrap) or a **learned LNN** (STRIDE-style) is deferred — C1
uses analytic-nominal first; revisit when real diff-drive/Gazebo data exists.
See [`deliberations.md`](deliberations.md).

# Residual-in-Rollout + Variance→Safety — Implementation Reference

_Phase P3 (bridges P2) · 2026-06-12 · extracts the [Stochastic-MPPI](https://github.com/RIVeR-Lab/Stochastic-MPPI)
mechanism into a wiring spec for the D-009 ensemble residual and the P3 epistemic
channel. See [`decisions.md`](decisions.md) D-009, [`p2_residual_dynamics_decision.md`](p2_residual_dynamics_decision.md)._

## Why this doc exists

Two open design questions have been blocking on "we'll figure out the wiring when
the code lands":

1. **How does a learned residual ride along inside nav2_mppi's _batched_ rollout?**
   D-009 committed to a K=3 MLP-ensemble residual but deferred the rollout-integration
   shape. This is the hardest part of the (currently merge-blocked) `EnsembleResidualDynamics`
   wrapper — worth de-risking now so the wrapper is mechanical once #44 reaches main.
2. **How does posterior disagreement become _safety_ rather than getting averaged away?**
   This is the P3 epistemic-channel question, now in-phase (P3 = risk/uncertainty fields).

[Stochastic-MPPI](https://github.com/RIVeR-Lab/Stochastic-MPPI) (RIVeR-Lab, ICRA-2025,
GP-enhanced chance-constrained MPPI for skid-steer off-road nav) is the closest **runnable**
external peer that already fuses both axes, with pretrained models on real
Asphalt/Grass/Tile terrains — i.e. exactly the north-star outdoor (small_city)
terrain-shift regime. Skid-steer ≠ our diff-drive, so the borrow is the **mechanism**,
not the platform stack.

## Axis 1 — residual evaluated inside the batched rollout

### What Stochastic-MPPI does

- Nominal physics model `f_nom(s,a)` + a **GP residual** `g(s,a)` learned per terrain.
- The GP is a **GPyTorch batch GP**: one forward call evaluates all `M` sampled rollouts ×
  `T` horizon steps at once on GPU (batched kernel eval), so the residual cost is a
  tensor op, not an `M·T` Python loop.
- Predicted next state per rollout step: `s_{t+1} = f_nom(s_t,a_t) + μ_g(s_t,a_t)`,
  with the GP posterior **variance** `σ²_g` carried alongside (Axis 2).

### Mapping onto the D-009 K=3 MLP-ensemble

The ensemble is structurally _cheaper_ to batch than a GP — this is a strength, not a gap:

| Concern | Stochastic-MPPI (batch GP) | D-009 ensemble (K=3 MLP) | Implication for our wrapper |
|---|---|---|---|
| Rollout-step op | batched kernel eval (GPyTorch) | `K` small matmuls (`[M·T, d]→[M·T, d]`) | matmul-only, no kernel/ODE solver — fits nav2_mppi's per-step budget |
| Batch shape | `[M, T, d]` GPU tensor | same, stack `K` heads on a leading axis `[K, M, T, d]` | one `torch.bmm`/`einsum` per step or vectorize the whole horizon |
| Mean prediction | GP posterior mean `μ_g` | ensemble mean `μ = (1/K)Σ_k h_k` | drop-in for the `+ residual` term |
| Disagreement | GP posterior `σ²_g` | ensemble variance `σ² = Var_k h_k` | **free** — already computed from the K heads (Axis 2) |
| Train cost | per-terrain GP fit | offline-frozen bootstrap-resampled MLPs | D-009 already chose offline-frozen; no online GP refit |

**Concrete wiring recommendation for `EnsembleResidualDynamics`** (ready to apply when #44 lands):

- Hold the K heads as a single stacked module; forward signature
  `residual(s, a) -> (mu[..., d], var[..., d])` operating on the **flattened
  `[M·T, ·]` batch** nav2_mppi already materializes — never a per-sample loop.
- Compose in the rollout as `s_next = f_nom(s,a) + mu`; thread `var` out as a
  second return so the cost layer can consume it without re-running the heads.
- Keep `f_nom` = the existing diff-drive kinematic step (matmul/closed-form), so the
  whole rollout stays solver-free — the Stochastic-MPPI lesson is "residual must be a
  tensor op that batches with the sampler", which the ensemble satisfies _more_ easily
  than their GP.

## Axis 2 — variance → tightened chance constraint (the P3 epistemic channel)

### What Stochastic-MPPI does

The GP variance is **not** averaged into the mean cost — it **tightens the constraint**:
an obstacle/path chance-constraint `P(collision) ≤ ε` is enforced by inflating the
effective obstacle margin (or the cost barrier) by a term monotone in `σ_g`. High
posterior disagreement ⇒ wider safety margin ⇒ the planner is _automatically more
conservative exactly where the dynamics model is least trusted_.

### Mapping onto our P3 risk/uncertainty field

- Ensemble variance `σ²` is the **epistemic** signal (model disagreement), distinct
  from aleatoric noise — this is the channel split P3 wants (epistemic vs aleatoric).
- Routing options for the MPPI cost (to be ablated in P5), in increasing coupling:
  1. **Additive risk penalty**: `cost += λ · σ²` per rollout step — simplest, but this
     is the "average it into the cost" path Stochastic-MPPI deliberately _avoids_.
  2. **Margin inflation (recommended, matches the reference)**: inflate the
     obstacle-distance threshold by `k·σ` before the collision/barrier term, so
     disagreement tightens the _constraint geometry_ rather than just adding scalar cost.
  3. **Per-step state-distribution**: propagate `σ` as a covariance and use a
     Mahalanobis/chance-constraint collision check (heavier; overlaps the C²U-MPPI
     research TODO for P4).
- The variance field is **render-ready as a BEV channel** — `σ²` mapped to ego-frame
  grid is the epistemic channel of the multi-channel risk BEV (P3 deliverable), and
  it costs nothing extra once the K heads run in the rollout.

## What we deliberately do NOT borrow

- The **GP machinery** (GPyTorch, per-terrain fit) — D-009 already chose MLP-ensemble
  for rollout-nativeness; the GP is the reference's _mechanism illustration_, not a
  re-decision. (If offline ensembles prove insufficient on real terrain shift, online
  adaptation is the separately-tracked U2 question, not this doc.)
- The **skid-steer motion model** and chance-constraint solver stack — our `f_nom`
  is diff-drive and our constraint lives in the nav2_mppi cost critic.

## Open question raised

Margin-inflation (Axis 2 option 2) needs a `k` (margin per unit σ). Stochastic-MPPI
derives it from the chance-constraint level ε; we have no `ε` target yet (no
quantitative harness until P5). Logged as a deliberation — the epistemic→margin gain
is a P3/P5 tuning knob that should be set against a measured near-miss rate, not
hand-picked. See [`deliberations.md`](deliberations.md).

## Refs

- Stochastic-MPPI: https://github.com/RIVeR-Lab/Stochastic-MPPI (ICRA-2025; ICRA-2024
  probabilistic skid-steer motion model). Research feed entry 2026-06-11 08:00.
- D-009 (MLP-ensemble build-first): [`decisions.md`](decisions.md),
  [`p2_residual_dynamics_decision.md`](p2_residual_dynamics_decision.md).
- P3 uncertainty-channel track: [`dynamic_obstacles_uncertainty_track.md`](dynamic_obstacles_uncertainty_track.md).

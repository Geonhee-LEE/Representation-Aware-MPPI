# Aleatoric Risk Cost-Critic Interface — where the chance-constraint / CVaR tightening enters nav2_mppi

_Phase P3 · 2026-06-27 · specs the **exact point in the nav2_mppi cost** where the
aleatoric channel (idx 4) applies a **risk-sensitive constraint tightening**, the
sibling of the epistemic margin-inflation route. Interface/design only — no code
dependency on the (merge-blocked) ensemble. This is the consumer end of the
stack-tensor contract for the **aleatoric** row: the aleatoric channel
([`aleatoric_channel_bev_rendering.md`](aleatoric_channel_bev_rendering.md), idx 4 of
[`multi_channel_risk_bev_stack.md`](multi_channel_risk_bev_stack.md) §4) feeds the
risk term specced here; its epistemic twin is
[`margin_inflation_cost_critic_interface.md`](margin_inflation_cost_critic_interface.md)
(idx 3). The rollout-wiring that produces the per-cell variance is
[`residual_in_rollout_reference.md`](residual_in_rollout_reference.md).
See [`decisions.md`](decisions.md) D-009/D-012/D-013, [`deliberations.md`](deliberations.md)
Q-009/Q-010/Q-011._

## 0. What this doc closes

Three upstream docs all defer the same one sentence to "a sibling of the
margin-inflation interface, to be specced once that one lands":

- aleatoric_channel_bev_rendering.md §4 fixes that aleatoric routes as a
  **chance-constraint / CVaR tightening, not margin inflation**, and §7 logs the
  "concrete nav2_mppi insertion point" as an explicit follow-up — "to be specced once
  [the margin interface] lands so they share the critic-config surface."
- multi_channel_risk_bev_stack.md §4 routes row 4 (aleatoric) to "chance-constraint /
  CVaR tightening" — pointing here.
- margin_inflation_cost_critic_interface.md §5 states the epistemic critic consumes
  **only** idx 3 and that "the aleatoric→risk-sensitive term is the sibling spec
  (separate TODO); this doc owns the epistemic→margin route only."

The margin-inflation interface (PR #53) has now merged, so the critic-config surface it
established (a standalone risk critic, `k=0`-style no-op default, config-not-literal
knobs, mask-gating) is available to mirror. The genuinely-new decision here: **which
nav2_mppi cost term consumes the aleatoric channel, and how the predicted noise changes
its output**, given the *actual* critic stack in `config/nav2_mppi_params.yaml`.

## 1. Why this cannot reuse the margin-inflation route

The epistemic route subtracts `k·σ` from clearance (a **geometry** change: obstacles
treated as closer where the model is *ignorant*). Aleatoric noise is **irreducible** —
it does not shrink with data — so feeding it into a back-off-where-ignorant margin would
produce *permanent* over-conservatism that never improves as the model trains (the swap
error tabulated in aleatoric §4). The correct response to irreducible noise is to
**hedge a fixed risk**: respect a tighter collision-probability / penalize the
distribution tail, reflecting that even a perfectly-trained model faces this noise.

| | epistemic (idx 3, margin inflation) | aleatoric (idx 4, **this doc**) |
|---|---|---|
| signal | `Var_k μ_k` — ensemble disagreement (reducible) | `mean_k σ²_k` — mean predicted noise (irreducible) |
| response | shrink clearance by `k·σ` (geometry) | tighten chance-constraint / CVaR tail penalty (risk) |
| as data grows | margin → 0 (model learns) | term persists (noise is real) |
| critic | `RiskInflationCritic` | `AleatoricRiskCritic` (this doc) |

## 2. The actual obstacle terms — same two anchors as the epistemic doc

Per margin_inflation_cost_critic_interface.md §1, only **`CostCritic`** (a) runs inside
the per-rollout scoring loop and (b) consumes a spatial field at trajectory-point
granularity; the `local_costmap` inflation layer is a global pre-rollout transform that
cannot vary per cell by a field recomputed each control step. So — identically to the
epistemic case — the aleatoric risk term must enter at the **critic** level.

But the *form* differs. `CostCritic` scores a single nominal trajectory point against
the costmap. A chance-constraint / CVaR term is **distributional**: it scores the
trajectory point against a *risk measure of the collision event under the predicted
noise*, not the nominal clearance alone. The aleatoric channel supplies exactly the
per-cell noise scale that turns a deterministic clearance into a probabilistic one.

> **Decision (→ D-014, pending decisions.md promotion): introduce a standalone
> `AleatoricRiskCritic`, do not overload `CostCritic` or `RiskInflationCritic`.**
> Same three reasons as D-013: (1) a separate critic keeps the baseline obstacle term
> untouched, so disabling it reproduces the exact baseline trajectory (the P5 ablation
> invariant); (2) it gives the aleatoric risk its own `cost_weight` independent of both
> `CostCritic`'s 3.81 and the epistemic critic's gain; (3) it isolates the P5 tail-level
> sweep (`α`/`δ` below) to one plugin. Critically, **epistemic and aleatoric stay two
> critics, not one "uncertainty" critic** — collapsing them re-merges the epi/ale split
> that is P3's reason for being, and the two consume different stack rows via different
> math (clearance subtraction vs tail measure).

## 3. The risk-tightening rule

The aleatoric channel supplies, per ego-frame cell, a real-unit predictive standard
deviation `σ_ale(x,y)` (the `sigma_raw` raster from aleatoric §3b — *not* the `[0,1]`
form; risk math needs physical units). For a sampled trajectory point at ego-frame
position `(x,y)` with nominal clearance `d(x,y)`:

```
σ_pt   = sample(sigma_raw_ale, x, y)         # NN-lookup into the aleatoric raster
d_eff  = d(x,y) − z(δ) · σ_pt                # chance-constraint form: shrink clearance by
                                             # a fixed quantile of the noise, NOT by k·σ
cost_pt = barrier(d_eff)                      # same barrier shape CostCritic uses
```

The chance-constraint form looks superficially like the epistemic `d − k·σ`, but the
multiplier is **fixed by a target collision probability `δ`** (`z(δ)` = the `(1−δ)`
Gaussian quantile, e.g. `z=1.64` for `δ=0.05`), *not* a tunable margin gain. The
semantic difference is load-bearing: `k` (epistemic) is "how much to distrust the model
here" and goes to 0 as the model learns; `z(δ)` (aleatoric) is "the safety probability I
demand against irreducible noise" and is a **fixed risk appetite** the operator sets
once. They are not the same knob with a different name.

### CVaR variant (preferred when the noise is non-Gaussian)

When the predictive distribution is heavy-tailed (the variance head's Gaussian
assumption is only a first cut), a **CVaR (expected-shortfall) tail penalty** is the
more honest risk measure than a single quantile:

```
cost_pt += w_ale · CVaR_α[ collision_cost | noise ]    # mean cost over the worst-α tail
```

with `CVaR_α` the average barrier cost over the worst `α`-fraction of the noise
distribution at that point (for a Gaussian `σ_pt`, `CVaR_α` has a closed form
∝ `σ_pt · φ(z_α)/α`, so no sampling is needed at control rate). Ship the
**chance-constraint quantile form as the default** (cheaper, one lookup) and expose CVaR
as a config-selectable risk measure for the heavy-tail case.

Key properties this rule must preserve (mirroring the epistemic doc's invariants):

- **Tightening only ever tightens, never loosens.** `z(δ) ≥ 0`, `σ ≥ 0` ⇒ `d_eff ≤ d`.
  A representation channel must never *reduce* a margin and drive into an obstacle.
- **Bounded.** Clamp `z(δ)·σ_pt ≤ Δ_max_ale` (config) so a pathological σ spike cannot
  freeze the robot. Defaults to the costmap `inflation_radius` (0.4 m), same ceiling as
  the epistemic clamp — never tighten beyond the existing safety layer.
- **Persists with data.** Unlike the epistemic margin, this term must **not** be expected
  to vanish as the model trains — that is the whole point. The P5 win condition is *fewer
  near-misses in genuinely-noisy regions at fixed success/time-to-goal*, not "the term
  goes to zero."

## 4. Unobserved cells — no tightening (mask-gated)

Per the stack-tensor contract (multi_channel_risk_bev_stack.md §2) the aleatoric row
travels with an observability plane (mask idx 4). The critic **must** gate on it,
exactly as the epistemic critic does:

```
σ_pt_effective = mask[ALEATORIC, x, y] ? σ_pt : 0.0
```

- mask `0` (no rollout sample landed in that cell) ⇒ **no tightening**. The planner
  isn't considering trajectories there, so there is nothing to make risk-sensitive; the
  *occupancy* safety of unseen cells is the costmap's job, not this critic's.
- The critic must never read an unobserved cell as `σ=high` (phantom risk on every
  missed cell) nor as a confident `σ=0`. The mask is the only correct disambiguator —
  the same reason the stack doc carries it explicitly rather than as a NaN sentinel.

## 5. The knobs (`δ` / `α` / risk-measure) — config, never literals

This doc routes the tail level but **does not set** it — like Q-008's `k`, the risk
appetite is a P5 metric-driven choice. The interface obligation is only that every knob
is a documented plugin parameter, defaulted, never hard-coded:

```yaml
AleatoricRiskCritic:
  enabled: true
  cost_power: 1
  cost_weight: 0.0           # DEFAULT 0.0 ⇒ exact-baseline no-op until tuned (D-013 discipline)
  risk_measure: chance       # "chance" (quantile) | "cvar"; chance is the cheap default (§3)
  chance_delta: 0.05         # target per-point collision prob; z(0.05)=1.64. P5-tuned.
  cvar_alpha: 0.10           # worst-α tail fraction when risk_measure=cvar. P5-tuned.
  max_tighten_m: 0.4         # == local_costmap inflation_radius; hard upper clamp
  aleatoric_channel_index: 4 # RiskChannel.ALEATORIC (stack-tensor enum, never guessed)
  trajectory_point_step: 2   # match CostCritic so the two score the same points
```

**`cost_weight` defaults to `0.0`** (not `chance_delta` — `δ` has no meaningful "off"
value, but a zero weight is a clean no-op). This mirrors the epistemic critic's `k=0`
default: shipping the critic disabled makes it identical to baseline, so the *plumbing*
can land and be smoke-tested before any tuned risk level exists, and the P5 ablation
flips a single number rather than wiring a new critic under deadline.

## 6. Acceptance / what "done" looks like (when code unblocks)

The implementing PR (post-#44, post-ensemble, post-aleatoric-render, and only if #44
ships **heteroscedastic** heads — Q-010) should satisfy:

1. An `AleatoricRiskCritic` nav2_mppi critic plugin registered alongside the existing 8
   (`ConstraintCritic`, `CostCritic`, `GoalCritic`, `GoalAngleCritic`, `PathAlignCritic`,
   `PathFollowCritic`, `PathAngleCritic`, `PreferForwardCritic`) and the epistemic
   `RiskInflationCritic` — **off by default via `cost_weight=0`** so adding it to the
   `critics:` list is a no-op until tuned.
2. It samples `sigma_raw_ale` + `mask` (aleatoric channel, idx 4) at each trajectory
   point, applies §3's bounded, tighten-only, mask-gated chance-constraint (or CVaR)
   tightening, and adds the resulting cost.
3. `risk_measure`, `chance_delta`, `cvar_alpha`, `max_tighten_m`, `aleatoric_channel_index`,
   `trajectory_point_step` are all config (§5) — no literals.
4. Disabling the critic (or `cost_weight=0`) reproduces the exact baseline trajectory —
   the ablation invariant.
5. With **both** risk critics enabled, an epistemic-only ablation (`AleatoricRiskCritic`
   off) and an aleatoric-only ablation (`RiskInflationCritic` off) are each one config
   flag — the two-axis P5 study the epi/ale split exists to enable.
6. `qual:` metric pre-P5; the quantitative gate is the P5 near-miss-rate sweep over
   `δ`/`α` once the eval harness lands — fewer near-misses in noisy regions at fixed
   success/time-to-goal is the win condition (and unlike the epistemic term, this one is
   *not* expected to trend toward zero as the model improves).

## 7. Open questions raised (→ deliberations)

- **Q-012 (the risk level `δ`/`α`) — new, P5-deferred.** This doc resolves *where* and
  *how* the aleatoric tail enters (→ the `AleatoricRiskCritic`, chance-constraint default
  with CVaR option) but not *what δ/α are*; that is a P5 metric-driven sweep, the
  aleatoric sibling of Q-008's `k`. Logged to deliberations.md.
- **Gaussian-tail vs empirical-CVaR.** §3 gives the Gaussian closed-form CVaR; if the
  variance head is later replaced by a quantile/distributional head, the closed form no
  longer holds and CVaR must be estimated from samples (cost at control rate). Defer the
  distributional-head case to whenever such a head exists; the Gaussian form is the
  shipping default. Logged as O-2 (sibling of the epistemic doc's O-1 footprint case).
- **Hard dependency on heteroscedastic heads (Q-010) carries through.** If #44 ships MSE
  point heads, there is no aleatoric signal, so this critic has nothing to consume — it
  is built only after the aleatoric channel renders a non-degenerate field (Q-011's
  heteroscedasticity acceptance check passes).

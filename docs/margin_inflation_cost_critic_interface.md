# Margin-Inflation Cost-Critic Interface — where `k·σ` enters nav2_mppi

_Phase P3 · 2026-06-19 · specs the **exact point in the nav2_mppi cost** where the
epistemic channel inflates the obstacle margin, closing the routing half of Q-008.
Interface/design only — no code dependency on the (merge-blocked) ensemble. This is
the consumer end of the stack-tensor contract: the epistemic channel
([`epistemic_channel_bev_rendering.md`](epistemic_channel_bev_rendering.md), idx 3 of
[`multi_channel_risk_bev_stack.md`](multi_channel_risk_bev_stack.md) §4) feeds the
margin gain `k·σ` specced here; the rollout-wiring that produces `σ` is
[`residual_in_rollout_reference.md`](residual_in_rollout_reference.md) Axis 2.
See [`decisions.md`](decisions.md) D-009/D-012, [`deliberations.md`](deliberations.md) Q-008.
(The §1 critic-placement decision is promoted to `decisions.md` as **D-013** by a
follow-up cycle once that file is conflict-free — open PR #52 currently holds the D-012
prepend, so this cycle records the decision here + in Q-008 to avoid the D-011 conflict trap.)_

## 0. What this doc closes

Three upstream docs all defer the same one sentence to "the critic-interface doc":

- residual_in_rollout_reference.md §Axis-2 picks **margin inflation** (option 2) over
  additive `λσ²` as the variance→safety route, but leaves *where in nav2_mppi* unspecified.
- epistemic_channel_bev_rendering.md §3 produces a `σ_raw` raster "in real σ units
  (`k·σ` in meters)" for "the margin-inflation critic" — but does not define that critic.
- multi_channel_risk_bev_stack.md §4 routes row 3 (epistemic) to "margin inflation `k·σ`
  → TODO `37cc5d39-…-8171`" — this doc.

The genuinely-new decision here: **which nav2_mppi cost term consumes the epistemic
channel, and how `k·σ` changes its output**, given the *actual* critic stack in
`config/nav2_mppi_params.yaml`.

## 1. The actual obstacle terms in our nav2_mppi config

Two places encode obstacle distance in the live config (`nav2_mppi_params.yaml`,
mirrored in `nav2_jackal_params.yaml` / `nav2_outdoor_params.yaml`):

| Where | Mechanism | Margin knob today | Per-trajectory-point? |
|---|---|---|---|
| `CostCritic` (MPPI critic) | looks up the **inflated costmap cost** at each sampled trajectory point; `near_collision_cost: 253`, `critical_cost: 300.0`, `collision_cost: 1e6` | thresholds on the costmap cost value | **yes** — scores every rollout |
| `local_costmap` → `inflation_layer` | pre-inflates obstacles into a cost field (`inflation_radius: 0.4`, `cost_scaling_factor`) | `inflation_radius` (global, static) | no — a map-wide preprocess |

The costmap inflation is a **global, pre-rollout** transform: it cannot vary the margin
per cell by an epistemic field that is itself recomputed each control step from the
rollouts. `CostCritic` is the **only** term that (a) runs inside the per-rollout scoring
loop and (b) already consumes a spatial field at trajectory-point granularity. So the
epistemic margin must enter at the **critic** level, not the costmap-layer level.

> **Decision (→ D-013, pending decisions.md promotion): introduce a standalone
> `RiskInflationCritic`, do not overload `CostCritic`.** A separate critic keeps the baseline obstacle term untouched (clean
> ablation: disable the new critic → exact baseline), gives the epistemic margin its
> own `cost_weight` independent of `CostCritic`'s 3.81, and isolates the P5 `k`-sweep to
> one plugin. Overloading `CostCritic` would entangle two gains in one weight and make
> "MPPI without representation-aware margin" un-measurable — fatal for the P5 ablation
> that is the whole point of the project.

## 2. The margin-inflation rule

The epistemic channel supplies, per ego-frame cell, a real-unit disagreement `σ(x,y)`
(the `sigma_raw` raster from epistemic §2.3, *not* the `[0,1]` form — margins are meters).
For a sampled trajectory point at ego-frame position `(x,y)`:

```
σ_pt      = sample(sigma_raw, x, y)          # NN-lookup into the epistemic raster
d_eff     = d_obstacle(x,y) − k · σ_pt       # effective clearance, shrunk by disagreement
cost_pt   = barrier(d_eff)                   # same barrier shape CostCritic uses
```

Equivalently, since `CostCritic` works in costmap-cost space rather than metric
clearance, the implementation **inflates the effective obstacle footprint** seen by the
critic by `k·σ_pt` meters before the cost lookup — i.e. a trajectory point is treated as
if obstacles were `k·σ_pt` closer than they metrically are. High disagreement ⇒ larger
effective footprint ⇒ the planner backs off **exactly where the dynamics model is least
trusted**, which is the Stochastic-MPPI mechanism (residual_in_rollout_reference.md §Axis-2)
expressed in our critic stack.

Key properties this rule must preserve:

- **Inflation only ever tightens, never loosens.** `k ≥ 0`, `σ ≥ 0` ⇒ `d_eff ≤ d_obstacle`.
  A representation channel must not be able to *reduce* a margin and drive into an obstacle.
- **Bounded.** Clamp `k·σ_pt ≤ Δ_max` (config) so a pathological σ spike cannot inflate
  the footprint to "everything is a collision" and freeze the robot. `Δ_max` defaults to
  the costmap `inflation_radius` (0.4 m) — never inflate beyond the existing safety layer.
- **Margin is additive in clearance, not multiplicative in cost.** This is the
  residual_in_rollout_reference.md §Axis-2 choice (option 2, not option 1's `cost += λσ²`):
  it changes the *constraint geometry*, so the effect is interpretable in meters and
  composes with `CostCritic`'s existing thresholds instead of fighting its weight.

## 3. Unobserved cells — no inflation (mask-gated)

Per the stack-tensor contract (multi_channel_risk_bev_stack.md §2) the epistemic row
travels with an observability plane (mask idx 3). The critic **must** gate on it:

```
σ_pt_effective = mask[EPISTEMIC, x, y] ? σ_pt : 0.0
```

- mask `0` (unevaluated — no rollout sample landed in that cell) ⇒ **no inflation**.
  This matches epistemic §3: "the planner isn't considering trajectories there, so
  there's nothing to make conservative." The *occupancy* safety of unseen cells is the
  costmap's job (and the 미관측-prior question O-1 in the stack doc), **not** this critic's.
- The critic must never read an unobserved cell as `σ=high` (would invent phantom margins
  on every cell a rollout missed) nor as a confident `σ=0` smuggled through — the mask is
  the only correct disambiguator, which is exactly why the stack doc carries it explicitly
  rather than as a NaN sentinel.

## 4. The `k` knob (Q-008) — config, never a literal

`k` (meters of margin per unit σ) is the gain this doc routes but **does not set** — its
value is Q-008, deferred to P5 because it must be tuned against a measured near-miss /
success-rate metric we do not yet have. The interface obligation is only that `k` (and
`Δ_max`) are **plugin parameters**, defaulted and documented, never hard-coded:

```yaml
RiskInflationCritic:
  enabled: true
  cost_power: 1
  cost_weight: 3.81          # start == CostCritic; independent so P5 can sweep it
  k_margin_per_sigma: 0.0    # Q-008: DEFAULT 0.0 ⇒ exact-baseline behavior until tuned
  max_inflation_m: 0.4       # == local_costmap inflation_radius; hard upper clamp
  epistemic_channel_index: 3 # RiskChannel.EPISTEMIC (stack-tensor enum, never guessed)
  trajectory_point_step: 2   # match CostCritic so the two score the same points
```

**`k_margin_per_sigma` defaults to `0.0`.** This is deliberate: shipping the critic with
`k=0` makes it a no-op identical to baseline, so the *plumbing* can land and be smoke-
tested before any tuned gain exists — and the P5 ablation flips a single number rather
than wiring a new critic under deadline. (Same discipline as epistemic §2.2 weights and
`σ²_ref`: ship a documented default, never a silent literal.)

## 5. Epistemic vs aleatoric routing stays split here too

This critic consumes **only** the epistemic row (idx 3). The aleatoric row (idx 4) routes
to a *different* term — chance-constraint / CVaR tightening (stack doc §4, aleatoric doc
§4) — because irreducible noise does not shrink with data and so should not feed a
back-off-where-ignorant margin. Wiring both rows into one margin would re-collapse the
epi/ale split that is P3's reason for being. The aleatoric→risk-sensitive term is the
sibling spec (separate TODO); this doc owns the epistemic→margin route only.

## 6. Acceptance / what "done" looks like (when code unblocks)

The implementing PR (post-#44, post-ensemble, post-stack-render) should satisfy:

1. A `RiskInflationCritic` nav2_mppi critic plugin registered alongside the existing 8,
   **off by default via `k=0`** so adding it to the `critics:` list is a no-op until tuned.
2. It samples `sigma_raw` + `mask` (epistemic channel, idx 3) at each trajectory point,
   applies §2's bounded, tighten-only, mask-gated inflation, and adds the resulting cost.
3. `k_margin_per_sigma`, `max_inflation_m`, `epistemic_channel_index`, `trajectory_point_step`
   are all config (§4) — no literals; `k`/`Δ_max` documented as Q-008 / safety clamps.
4. Disabling the critic (or `k=0`) reproduces the exact baseline trajectory — the
   ablation invariant.
5. `qual:` metric pre-P5; the quantitative gate is the P5 near-miss-rate sweep over `k`
   (Q-008) once the eval harness lands — lower near-miss at fixed success/time-to-goal is
   the win condition.

## 7. Open questions raised (→ deliberations)

- **Q-008 (the `k` value) stays open** — this doc resolves *where* `k·σ` enters (routing →
  the `RiskInflationCritic` placement decision, D-013 pending) but not *what k is*; that is
  a P5 metric-driven sweep. Updated Q-008's note to reflect the routing half is now closed.
- **Footprint-inflation vs clearance-subtraction equivalence.** §2 gives two framings
  (subtract `k·σ` from clearance, or inflate the effective footprint by `k·σ`). They are
  equal for a circular footprint but diverge once `CostCritic.consider_footprint: true`
  (currently `false`). Defer the polygon-footprint case to whenever footprint-aware costing
  is turned on; the circular-clearance form is the shipping default. Logged as O-1 here.
- **O-2 — is margin-inflation the right *response mode* for the epistemic channel at all?**
  This doc, §5, and the stack §4 fix that epistemic ≠ aleatoric *routing*, then assume the
  epistemic response **is** a passive back-off (widen clearance by `k·σ` where the learned
  model is ignorant). But epistemic uncertainty is by definition **reducible by sensing /
  replanning / data** — so the distinctive correct response to it may be to *actively reduce*
  it, not just stand further back. Four independent 2026-06-29 feed entries converge on this
  fork and it is **not** yet captured in the design: **TRIAGE** (arXiv 2603.08128) makes the
  routing-by-dominant-type principle explicit — epistemic-dominated risk should drive
  *information-gathering / conservative replanning*, aleatoric-dominated risk a
  disturbance-margin; **PA-MPPI** (2509.14978) is the executable form — a *perception cost
  term inside MPPI* that biases rollouts toward poses which observe the unobserved (the
  active half our unobserved-mask, §3, only marks passively); **the GP-contraction-tube MPC**
  (2507.02098) offers a *principled* epistemic-σ→margin map (a contraction-bounded reachable
  tube) as the disciplined alternative to a hand-set `k` multiplier; **BC-MPPI** (2510.00272)
  is the in-sampler aleatoric sibling (a learned feasibility-probability reweight toward a
  prescribed violation rate). The open question: **does the epistemic channel warrant a
  *second* response term (info-gather / active-perception cost, à la PA-MPPI) in addition to
  — or instead of — the §2 `k·σ` margin, and is the tube (2507.02098) a better σ→margin map
  than a swept scalar `k`?** This is a P3-design / P5-ablation fork (margin-only vs
  margin+active-perception vs tube-margin), distinct from Q-008 which only asks the *value*
  of `k` under the margin-only assumption. **Promoted to `deliberations.md` Q-014**
  (2026-07-02, once PR #56's Q-013/D-015 edits landed on main and cleared the D-011
  same-file-prepend collision). This §7 O-2 block stays the canonical *rationale*; Q-014 is
  the tracked open-question stub — resolve there when the P5 3-way ablation runs.
</content>

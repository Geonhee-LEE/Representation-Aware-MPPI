# Epistemic Channel — BEV Rendering Spec

_Phase P3 · 2026-06-13 · specs how the K=3 ensemble variance `σ²` becomes an
**ego-frame BEV grid channel** of the multi-channel risk field. Interface/design
only — no dependency on the (merge-blocked) ensemble code. Companion to the
rollout-wiring + cost-routing spec
[`residual_in_rollout_reference.md`](residual_in_rollout_reference.md) (lands with PR #49);
this doc fills its one-line "render-ready as a BEV channel" claim with an actual
rendering contract. See [`decisions.md`](decisions.md) D-009,
[`dynamic_obstacles_uncertainty_track.md`](dynamic_obstacles_uncertainty_track.md) §3._

## Scope of this doc

The rollout-wiring spec established that `EnsembleResidualDynamics.residual(s,a)`
returns `(mu, var)` per rollout step and that `var` (epistemic `σ²`) should route
into safety via **margin inflation**, not additive cost. It left one claim
unimplemented: _"the variance field is render-ready as a BEV channel — `σ²` mapped
to ego-frame grid is the epistemic channel of the multi-channel risk BEV."_

That sentence hides the actual design problem: **`σ²` is born in trajectory space,
not grid space.** The ensemble emits a variance per sampled rollout step — a value
attached to a `[M, T]` cloud of predicted states — but a BEV channel is a dense
`[H, W]` ego-frame raster. This doc specs the map between them: what produces the
field, the grid geometry, the `σ² → channel-value` reduction, and how the channel
composes with the other risk channels. It is the P3 epistemic-channel deliverable
in `dynamic_obstacles_uncertainty_track.md` §3 (Stage U1/U2 for the epistemic row).

## 1. Two sources for the field — decouple rendering from the sampler

`σ²` can reach the grid two ways. They are **not** alternatives to pick between;
they serve different consumers and the spec keeps both.

### 1a. Scatter path (rollout-coupled) — for the cost critic

The MPPI rollout already evaluates `residual(s,a)` over its `[M, T]` sampled
trajectories, so `σ²` is free at exactly the states the planner is considering.
Render by **scattering** each rollout step's `σ²` into the grid cell containing its
predicted `(x, y)`, then reducing per cell:

- cell value `= max` over all `(m, t)` steps landing in that cell (max, not mean:
  a single high-disagreement sample passing through a cell is the safety-relevant
  signal; averaging dilutes it with confident neighbours).
- cells with no rollout coverage are **unobserved**, not zero — see §3 fill rule.

This path is sparse (covers only where rollouts go) and **re-renders every control
step**. It is the one that should drive the margin-inflation critic, because it
reflects disagreement *on the trajectories actually being scored*.

### 1b. Query-grid path (sampler-independent) — for visualization + dense composition

Evaluate the ensemble on a **fixed dense grid** of query states: for each cell
center `(x, y)`, query `residual` at `(s=[x, y, θ_robot, v_nominal, ω_nominal], a=nominal)`
and take `σ²`. This yields a fully-populated `[H, W]` raster independent of the
sampler — the clean form for an RViz overlay, for stacking with the static/aleatoric
channels at equal density, and for the P5 uncertainty-calibration metric (ECE/MCE
needs a dense field, not a rollout cloud).

Cost: `H·W` extra residual evals per render. At the §2 default grid (120×120) and a
K=3 MLP this is one `[14400, d]` batched matmul per head — cheap, and **throttleable**
(render at e.g. 5 Hz, decoupled from the control rate). θ/v/ω for the query are held
at the current robot estimate; the field is therefore a *slice* of the epistemic
volume at the robot's current heading/speed, which is the right conditioning for a
local BEV.

> **Default**: build 1b first (deterministic, testable without the MPPI loop, gives
> the RViz overlay that makes the channel reviewable), then add 1a when the
> margin-inflation critic is wired. Both reduce `σ²` identically (§2.3) so the
> channel value is consistent across the two.

## 2. Grid geometry + value contract

### 2.1 Frame and extent — mirror the local costmap

The channel is **ego-frame, rolling-window**, aligned 1:1 with the nav2 local
costmap so it composes with existing nav2 layers without a resample:

| Param | Value | Rationale |
|---|---|---|
| frame | `base_link` (ego), rolling | matches `local_costmap` rolling_window=true |
| extent | **6 m × 6 m** (outdoor/jackal) / **3 m × 3 m** (mppi base) | exactly the `local_costmap` width/height in `nav2_outdoor_params.yaml` / `nav2_mppi_params.yaml` |
| origin | robot at grid center | rolling ego-frame convention |
| native res | 0.05 m (costmap-matched) **render res 0.10–0.20 m** | `σ²` is spatially smooth; rendering at 0.10 m cuts cells 4× (120×120 @ 0.10 m for 6 m) with no signal loss. Upsample to 0.05 m only at the costmap-compose boundary. |

`[H, W] = [120, 120]` at 0.10 m / 6 m is the working default; the critic consumes
it at costmap-native 0.05 m via nearest-neighbor upsample (the field is smoother
than the costmap, so NN is adequate and avoids edge blur into obstacle cells).

### 2.2 `σ²` is per-dimension — reduce to a scalar first

The ensemble variance is `σ² ∈ R^d` (one per residual output dim — for the diff-drive
residual, per predicted state-delta component). A grid cell needs a scalar. Reduce by
a **scale-normalized, position-weighted norm**, not a raw trace:

```
σ²_cell = Σ_i w_i · σ²_i / s_i²
```

- `s_i` = a fixed per-dimension scale (the residual's typical magnitude on that dim,
  measured once on the training set) so dimensions with different units (m vs rad vs
  m/s) are commensurable before summing. A raw `trace(Σ)` would let whichever dim has
  the largest unit dominate the channel — a bug, not a feature.
- `w_i` = task weight. **Default: weight the position/heading dims, down-weight pure
  velocity-residual dims** — the BEV channel exists to inflate *spatial* obstacle
  margins, so disagreement that moves the predicted *pose* matters more than
  disagreement in the predicted speed. (Exact weights are a P5 ablation knob; ship a
  documented default, do not hard-code silently — same Q-008 discipline as the `k`
  gain.)

### 2.3 Normalization to channel value `∈ [0, 1]`

Channels in the multi-channel BEV are `[0, 1]` rasters. Map `σ²_cell` with a **fixed,
documented scale** rather than per-frame min-max:

```
c = clip(σ²_cell / σ²_ref, 0, 1)        # σ²_ref = a fixed reference variance
```

- **Fixed `σ²_ref`, not per-frame normalization.** Per-frame min-max would make the
  channel relative ("this frame's worst cell") and destroy cross-frame/cross-episode
  comparability — fatal for the P5 calibration metric and for a margin that must mean
  the same thing in every frame. `σ²_ref` is set once (e.g. the 95th-percentile cell
  variance on a held-out OOD set) and frozen.
- Optionally emit the **raw `σ²_cell`** as a parallel float raster alongside the `[0,1]`
  channel — the margin-inflation critic wants real `σ` units (`k·σ` in meters), while
  the `[0,1]` form is for the stacked-BEV tensor and the RGB overlay. Rendering both
  from the same reduction keeps them consistent.

## 3. Composition with the other risk channels

Per `dynamic_obstacles_uncertainty_track.md` §3 the risk BEV has 5 channels; this
specs the **epistemic** row and its relation to the others:

| Channel | Type | This doc's relation |
|---|---|---|
| static | aleatoric | independent (occupancy noise); same grid geometry |
| dynamic | aleatoric | independent (tracker covariance); same grid geometry |
| traversability | aleatoric | independent (semseg confidence) |
| **epistemic** | **epistemic** | **this doc — ensemble `σ²`** |
| aleatoric | aleatoric | the residual's *predictive-variance head*, **not** ensemble spread — keep separate (see below) |

- **Epistemic vs aleatoric must stay separate channels.** Ensemble disagreement
  (`Var_k h_k`, *reducible* — shrinks with more data / in-distribution states) is a
  different physical quantity from a predictive-variance head (irreducible task noise).
  Collapsing them into one "uncertainty" channel would defeat the P3 reason-for-being
  (the epi/ale split). They share grid geometry (§2.1) and the `[0,1]` contract (§2.3)
  but are rendered from different signals and stacked as distinct channels.
- **Stacking**: channels are a `[5, H, W]` tensor in the fixed order above. The
  risk-aware MPPI cost consumes them per the margin-inflation interface
  (separate TODO `37cc5d39-…-8171`): the epistemic channel feeds the `k·σ`
  obstacle-margin inflation; the aleatoric channels feed their own terms. This doc
  produces the channel; that doc specs where it enters the cost.

### Unobserved-cell fill rule

Scatter-path (§1a) cells with no rollout coverage are **NaN/unobserved**, distinct
from `σ²=0` (confident). For the cost critic, unobserved ⇒ **no inflation** (the
planner isn't considering trajectories there, so there's nothing to make conservative).
For the dense query-path (§1b) every cell is observed, so this only affects 1a.
Encode unobserved as a separate mask channel rather than a sentinel value, so the
critic and the visualizer can tell "confident" from "unevaluated".

## 4. Acceptance / what "done" looks like (when code unblocks)

This is a design contract; the implementing PR (post-#44) should satisfy:

1. A `render_epistemic_channel(residual, robot_state, grid_cfg) -> (channel[0..1], sigma_raw, mask)`
   producing the §2 rasters via the §1b query path.
2. Grid geometry pulled from the active `local_costmap` params (no second source of
   truth for extent/res).
3. Per-dimension reduction (§2.2) and fixed-`σ²_ref` normalization (§2.3) with the
   scales/`σ²_ref`/weights as **config**, not literals.
4. An RViz `OccupancyGrid`/`Image` overlay of the `[0,1]` channel for visual review.
5. `qual:` metric pre-P5; the quantitative gate is the §3 epi/ale calibration check
   (epistemic ↑ on OOD, stable in-distribution) once the P5 harness lands.

## 5. Open questions raised (→ deliberations)

- **`σ²_ref` source.** Set from a held-out OOD percentile — but we have no OOD set
  until real rosbag/terrain-shift data exists. Until then `σ²_ref` is a documented
  placeholder, same un-set-knob status as the `k` margin gain (Q-008). Logged as a
  deliberation: epistemic normalization reference should be calibrated against
  measured OOD spread, not hand-picked.
- **Query-slice conditioning.** The 1b dense field fixes `θ/v/ω` at the current robot
  estimate, so the channel is a heading/speed *slice* of the epistemic volume. Is a
  single slice enough, or does the margin need the max over a small `(v, ω)` fan? Defer
  to P5 ablation; ship the single-slice default.

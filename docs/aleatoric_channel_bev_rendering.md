# Aleatoric Channel — BEV Rendering Spec

_Phase P3 · 2026-06-15 · specs how the residual's **predictive-variance head**
(irreducible task noise) becomes an **ego-frame BEV grid channel** of the
multi-channel risk field. Interface/design only — no dependency on the
(merge-blocked) ensemble code. Symmetric sibling of
[`epistemic_channel_bev_rendering.md`](epistemic_channel_bev_rendering.md): it
reuses that doc's grid geometry, per-dim reduction, and fixed-ref `[0,1]`
normalization verbatim, and only the **source signal + cost routing** differ.
See [`decisions.md`](decisions.md) D-009,
[`dynamic_obstacles_uncertainty_track.md`](dynamic_obstacles_uncertainty_track.md) §3._

## Scope of this doc

The epistemic doc rendered ensemble disagreement `Var_k h_k(s,a)` (a *reducible*
signal — shrinks with more data / in-distribution states) into the epistemic BEV
channel. This doc specs the **aleatoric** row of the same `[5,H,W]` stack: the
*irreducible* predictive noise the residual model assigns to a state-action, which
is a physically different quantity and must stay a separate channel (the P3 epi/ale
split is the whole reason these are two rows, not one "uncertainty" channel — see
`dynamic_obstacles_uncertainty_track.md` §3, row `aleatoric`).

Everything about *getting a value onto the grid* is identical to the epistemic doc
and is **not re-derived here** — this doc states only the deltas. Where it says
"per epistemic §2.1" it means: take that contract unchanged.

## 1. Source signal — predictive-variance head, not ensemble spread

The standard deep-ensemble uncertainty decomposition (Lakshminarayanan et al. 2017)
splits a K-head ensemble of **heteroscedastic** regressors `h_k(s,a) = (μ_k, σ²_k)`
(each head trained with a Gaussian NLL / variance-output head) into:

```
epistemic  =  Var_k μ_k          # disagreement of the means          → epistemic doc
aleatoric  =  (1/K) Σ_k σ²_k      # mean of the heads' predicted noise  → THIS doc
```

So the two channels are **two reductions of the same ensemble forward pass** — no
extra model, no second inference. The epistemic channel reads the *spread of the
means*; the aleatoric channel reads the *average of the predicted variances*.

> **⚠ Hard dependency on the D-009 head architecture (PR #44).** This decomposition
> only exists if the ensemble heads are **heteroscedastic** — i.e. each head emits a
> per-dim predictive variance `σ²_k`, trained with NLL, not plain MSE point
> regression. If the D-009 scaffold ships MSE heads, **there is no aleatoric signal at
> all** and this channel cannot be built. This is a concrete architecture decision the
> scaffold must make, surfaced as Q-010 below. The epistemic channel does **not** need
> this (it only needs the means), which is why epistemic was specced first.

## 2. The degeneracy risk that defines this channel's value

An aleatoric BEV channel is only worth a row in the stack **if the predicted noise is
state-dependent (heteroscedastic in the input).** If the variance head learns a single
global noise level (homoscedastic — the common failure mode of a lazily-trained NLL
head), then `σ²_ale(s,a)` is ~constant across the grid and the channel is a **flat
raster carrying zero spatial information** — pure overhead.

The channel earns its place exactly when noise *varies with location/regime*, e.g.:
- predicted dynamics noise grows on rough/loose terrain vs smooth floor,
- noise grows in high-`(v,ω)` regimes the model can't resolve crisply,
- noise grows near actuation limits where the diff-drive response is least repeatable.

**Design consequence**: the rendering contract below is identical to epistemic, but
the channel's *acceptance test* (§4) must include a heteroscedasticity check — if the
rendered channel is statistically flat on a varied-terrain slice, the channel is
reporting "the variance head collapsed", not "the world is uniformly noisy", and the
fix is upstream (head training), not in the renderer. Logged as Q-011.

## 3. Grid + value contract — inherited from epistemic, two deltas

Reuse the epistemic doc **unchanged** for:
- **§2.1 frame/extent/res** — same `base_link` rolling window, same 6 m / 3 m extent
  mirrored from `local_costmap`, same `[120,120] @ 0.10 m` working default, same NN
  upsample to costmap-native 0.05 m at the compose boundary.
- **§1a/1b scatter vs query-grid paths** — same two producers. Scatter (rollout-coupled,
  `max` over `(m,t)` per cell) drives the cost; query-grid (dense, throttleable ~5 Hz)
  drives viz + dense composition + the P5 calibration metric. Build 1b first.
- **§2.2 per-dim scale-normalized reduction** `σ²_cell = Σ_i w_i · σ²_i / s_i²` — same
  per-dim scales `s_i` (commensurate units before summing) and same position/heading
  weighting `w_i`.

### Delta 3a — reduction `max` vs `mean` on the scatter path

Epistemic uses `max` over rollout steps per cell (one high-disagreement sample is the
safety signal). For aleatoric, **`mean` (or a high percentile, e.g. p75) is the right
reducer, not `max`**: aleatoric noise is a property of the *region*, not of an
individual unlucky sample, so averaging the steps landing in a cell estimates the
local noise level, whereas `max` would just surface sampling outliers. Ship `mean` as
default, expose the reducer as config (same no-hard-code discipline as Q-008's `k`).

### Delta 3b — normalization reference `σ²_ref_ale`

Same fixed-ref `[0,1]` map `c = clip(σ²_cell / σ²_ref_ale, 0, 1)`, **per-frame min-max
still banned** for the same cross-frame-comparability reason. But `σ²_ref_ale` is a
**different reference from the epistemic `σ²_ref`**:

- Epistemic `σ²_ref` = a held-out **OOD** percentile (epistemic *spikes* on OOD).
- Aleatoric `σ²_ref_ale` = a typical **in-distribution** predictive-variance scale
  (e.g. the median/p90 predicted `σ²` on the *training* set), because aleatoric noise
  is present in-distribution and does **not** spike on OOD — normalizing it against an
  OOD percentile would crush all in-distribution structure to ≈0.

The two references are set from different data splits and must not be shared. Both are
config placeholders until the data exists (epistemic needs an OOD set; aleatoric needs
only the training set, so `σ²_ref_ale` is actually *settable today* once #44 trains —
a rare un-blocked knob). Optionally emit raw `σ_ale` (in physical units) alongside the
`[0,1]` channel, same as epistemic.

## 4. Cost routing — aleatoric is NOT margin inflation

This is the load-bearing distinction from the epistemic channel and the reason routing
can't be copy-pasted from the margin-inflation interface
(TODO `37cc5d39-…-8171`):

| | epistemic (`k·σ` margin inflation) | aleatoric (this channel) |
|---|---|---|
| meaning | "model doesn't know here" (reducible) | "world is genuinely noisy here" (irreducible) |
| right response | **back off** — inflate obstacle margin, shrink trust horizon; shrinks as data grows | **hedge a fixed risk** — tighten a chance-constraint / add a risk-sensitive (CVaR-style) penalty that does *not* vanish with more data |
| wrong if swapped | inflating margin for irreducible noise → permanent over-conservatism that never improves | chance-tightening for epistemic → under-reacts to true OOD ignorance |

So aleatoric routes as a **constraint-tightening / risk-sensitivity term**, not a
margin gain: it raises the collision-probability the planner must respect (or weights
the rollout cost by a tail measure), reflecting that even a perfectly-trained model
faces this noise. Concretely it pairs with the chance-constraint arms the feed tracks
(Stochastic-MPPI variance→chance-constraint, C²U-MPPI Mahalanobis tightening) rather
than the barrier-margin arm. **The exact entry point is a separate spec** (a sibling to
the margin-inflation interface TODO) — this doc fixes only that aleatoric ≠ epistemic
routing and produces the channel; it does not wire the cost. Logged as a follow-up.

## 5. Composition

Identical to epistemic §3: stacked as a distinct row in the `[5,H,W]` tensor in the
fixed channel order (static / dynamic / traversability / epistemic / **aleatoric**),
shared grid geometry, shared `[0,1]` contract, shared **unobserved-mask** channel
(scatter-path cells with no rollout coverage are NaN/unobserved, distinct from a
confident `σ²=0`). The multi-channel stack tensor TODO (`37dc5d39-…-0436`) owns the
channel-order + mask contract; this doc just claims the `aleatoric` row of it.

## 6. Acceptance / what "done" looks like (when code unblocks)

The implementing PR (post-#44, and only if #44 ships heteroscedastic heads) should:

1. A `render_aleatoric_channel(residual, robot_state, grid_cfg) -> (channel[0..1], sigma_raw, mask)`
   reusing the epistemic renderer's grid/normalization code paths — ideally the two
   channels share one `render_uncertainty_channel(reduce_fn, ref, ...)` with `reduce_fn`
   = `Var_k μ_k` (epi) vs `mean_k σ²_k` (ale) injected, so geometry has one source of truth.
2. Grid geometry pulled from the active `local_costmap` params (no second source of truth).
3. Reducer = `mean`/p75 (§3a), `σ²_ref_ale` = in-distribution scale (§3b), both **config**.
4. RViz overlay of the `[0,1]` channel.
5. **Heteroscedasticity acceptance check (§2)**: on a varied-terrain/varied-`(v,ω)` slice,
   the rendered channel must show non-trivial spatial variance (e.g. coefficient-of-variation
   above a documented floor). A flat channel ⇒ upstream head-training bug, not a pass.
6. `qual:` metric pre-P5; quantitative gate is the §3 epi/ale calibration split once the
   P5 harness lands (aleatoric should be ~stable across in-distribution vs OOD, the mirror
   image of epistemic's OOD-spike check).

## 7. Open questions raised (→ deliberations)

- **Q-010 — heteroscedastic vs MSE heads in D-009 (PR #44).** This channel does not exist
  unless the ensemble heads emit a per-dim predictive variance (NLL training). The scaffold
  must decide: MSE point heads (epistemic-only, simpler) vs NLL variance heads (unlocks
  aleatoric, +training complexity). Lean: NLL heads — the epi/ale split is a core P3
  deliverable and the cost is one extra output dim + a Gaussian NLL loss, not a new model.
- **Q-011 — homoscedastic degeneracy guard.** A collapsed variance head renders a flat,
  worthless channel that *looks* like a valid output. The §4-style acceptance check (spatial
  CoV floor) is the proposed guard, but the floor value is unset until #44 trains — same
  un-set-knob status as `k` (Q-008) and `σ²_ref` (Q-009).
- **Aleatoric cost-routing entry point.** §4 fixes that routing is chance-constraint
  tightening / CVaR, not margin inflation, but the concrete nav2_mppi insertion point is
  unspecified — a sibling to the margin-inflation interface TODO, to be specced once that
  one lands so they share the critic-config surface.

# Multi-Channel Risk BEV Stack — Tensor Contract

_Phase P3 · 2026-06-17 · defines the **single `[C,H,W]` ego-frame tensor** that the
risk-aware MPPI cost consumes, and the **unobserved-mask** that travels with it.
Interface/design only — no code dependency. This doc is the **canonical owner** of
the channel-order + mask contract that the per-channel rendering docs already point
back to (see [`aleatoric_channel_bev_rendering.md`](aleatoric_channel_bev_rendering.md)
§5, [`epistemic_channel_bev_rendering.md`](epistemic_channel_bev_rendering.md) §3,
[`dynamic_obstacles_uncertainty_track.md`](dynamic_obstacles_uncertainty_track.md) §3,
[`decisions.md`](decisions.md) D-012). Pairs with the margin-inflation cost-critic
interface TODO (`37cc5d39-…-8171`), which consumes this tensor._

## 0. Why a single tensor (and why this doc owns it)

Each risk channel is specced in its own doc, but the MPPI cost must read **one**
object with a fixed layout — otherwise every channel that lands re-negotiates the
input shape and the cost critic churns. The two rendered channels so far (epistemic,
aleatoric) each already declare "I am row _k_ of the `[5,H,W]` stack, and the stack
doc owns the order + mask." This doc closes that forward reference: it fixes the
channel index map, the grid geometry shared by all rows, the dtype/value contract,
and — the genuinely new design decision — **how an unevaluated cell is represented**
so it is never confused with a confident zero.

## 1. Channel order (fixed, canonical)

The five risk channels of `dynamic_obstacles_uncertainty_track.md` §3, in this **fixed
index order**. Order is part of the contract: producers write their own row, the cost
critic indexes rows by name via this enum, never by guessing.

| idx | channel | kind | source (eventual) | rendered yet? |
|---|---|---|---|---|
| 0 | `static` | aleatoric | static occupancy / P1 BEV semseg | no (U2) |
| 1 | `dynamic` | aleatoric | obstacle-motion / tracker covariance | no (P4) |
| 2 | `traversability` | aleatoric | terrain variance / semseg confidence | no (U3) |
| 3 | `epistemic` | epistemic | ensemble disagreement `Var_k μ_k` | **spec'd** (#50) |
| 4 | `aleatoric` | aleatoric | predictive-variance head `mean_k σ²_k` | **spec'd** (#51) |

Reference enum (the single source of truth; channel count `C=5` for the risk rows):

```python
class RiskChannel(IntEnum):
    STATIC = 0
    DYNAMIC = 1
    TRAVERSABILITY = 2
    EPISTEMIC = 3
    ALEATORIC = 4
# tensor: risk[C, H, W], C == len(RiskChannel)
```

Rationale for the order: the three **scene/perception** channels (static, dynamic,
traversability) lead; the two **model-uncertainty** channels (epistemic, aleatoric)
trail. This groups rows by where they come from and by cost-routing class (§4), so the
critic config can slice `[:3]` (perception risk) vs `[3:]` (model uncertainty) without
a lookup. Inserting a future channel appends at the tail — **never reuse or shift an
existing index** (a shipped critic config references indices).

## 2. The unobserved-mask channel — the new contract

A risk value of `0.0` is ambiguous: it can mean **"evaluated, confidently zero risk"**
(open floor, in-distribution → epistemic σ²≈0) or **"never evaluated here"** (no rollout
sample landed in this cell; sensor never saw it). These must be distinguished — a planner
that reads unevaluated cells as zero-risk will happily drive into the **미관측 / 가려진**
region, the exact north-star failure mode the feed's occlusion (CMPC) and
state-uncertainty (DUCCT-MPPI) arms target.

**Decision: carry observability as an explicit mask, not as a sentinel in the data
plane.** NaN-in-the-value-channel was rejected — NaN silently poisons `sum`/`mean`/`max`
reductions in the cost and is easy to forget to guard; an explicit boolean plane forces
every consumer to decide what an unobserved cell means.

Mask semantics (per cell, per channel that has a scatter/coverage notion):
- `1` = observed/evaluated → the value in that cell is meaningful (including a true 0).
- `0` = unobserved/unevaluated → the value is undefined; the cost critic must apply its
  **unobserved policy** (default: treat as a configurable pessimistic prior, NOT 0).

### 2a. One shared mask vs per-channel mask — open, lean per-channel

A cell can be observed for `static` (costmap covers it) yet unevaluated for `epistemic`
(no rollout sample landed there this tick). So a single shared mask is **wrong in
general**. The faithful contract is a **`[C,H,W]` mask mirror** (one observability plane
per risk row), giving total tensor footprint `2·C·H·W`. The cheap alternative — a single
`[H,W]` mask = AND/OR of all channels — loses the per-channel distinction. Ship the
per-channel `[C,H,W]` mask as the contract (correctness first; at `C=5, [120,120]` it is
~144 KB float32 / ~18 KB as uint8/bool — negligible), and let a producer that genuinely
shares coverage across rows write the same plane into several slots. Open question O-1.

## 3. Grid + value contract (shared by all rows)

Inherited verbatim from the channel docs so there is exactly one source of truth for
geometry — this doc does **not** re-derive it, it pins it as the stack-wide invariant:

- **Frame/extent/res**: `base_link` rolling window, 6 m × 3 m extent mirrored from
  `local_costmap`, working default `[H,W] = [120,120] @ 0.10 m`, NN-upsampled to the
  costmap-native 0.05 m at the compose boundary (epistemic §2.1).
- **Normalization**: every channel is fixed-ref-mapped to `[0,1]`
  (`c = clip(x / x_ref, 0, 1)`). **Per-frame min-max is banned** stack-wide — cross-frame
  comparability is required for a stable cost. Each channel keeps its **own** reference
  (`σ²_ref` epistemic = OOD percentile; `σ²_ref_ale` aleatoric = in-distribution scale;
  static/dynamic/traversability set theirs in their own docs). References are per-row, the
  `[0,1]` codomain is shared.
- **Dtype / layout**: values `float32`, channel-first `[C,H,W]`, C-contiguous (rows are
  the slow axis → a producer writes one contiguous `[H,W]` slab). Mask `uint8`/bool,
  same `[C,H,W]` shape (§2a).
- **Grid geometry comes from the live `local_costmap` params at runtime**, not hard-coded
  here — `[120,120]@0.10` is the design default, the contract is "mirror the active local
  costmap window."

## 4. Per-channel cost routing (summary; full wiring in the critic-interface doc)

The stack carries the data; the cost critic decides what each row *does*. Routing is
**not uniform** — collapsing all rows into one additive `Σ w_i·c_i` term is the design
error this table prevents (it is exactly why epistemic ≠ aleatoric routing, aleatoric
doc §4):

| row | cost role | routing class |
|---|---|---|
| static, dynamic | occupancy / collision likelihood | additive obstacle cost (+ dynamic chance-constraint, P4) |
| traversability | preference / soft cost | additive weighted cost |
| epistemic | **margin inflation** `k·σ` — back off where the model is ignorant (reducible) | obstacle-margin gain → TODO `37cc5d39-…-8171` |
| aleatoric | **chance-constraint / CVaR tightening** — hedge irreducible noise (does not vanish with data) | risk-sensitive term, sibling spec |

The two model-uncertainty rows route through **different mechanisms** (margin vs
chance-tightening); the stack tensor must therefore stay channel-addressable to the very
end — never pre-summed into a scalar risk map before the critic.

## 5. Partial-stack handling (P3 reality)

Today only rows 3–4 (epistemic, aleatoric) have renderers; rows 0–2 land later (U2/U3/P4).
The stack is **always allocated full `C=5`**; an absent channel is published as an
**all-unobserved row** (mask `0` everywhere), not an all-zero row. This way the cost
critic's "unobserved policy" (§2) transparently covers not-yet-implemented channels —
adding a renderer later flips that row's mask on with **zero cost-side code change**. A
config flag lists which rows are live, for logging/asserts only; it must not change the
tensor shape.

## 6. Acceptance / what "done" looks like (when code unblocks)

Doc/interface deliverable now; the implementing PR (post-channel-renderers) should:

1. Ship the `RiskChannel` `IntEnum` as the one import every producer + the critic uses.
2. Provide a `RiskBevStack` container: `values[C,H,W] float32`, `mask[C,H,W] uint8`,
   `grid_cfg` (frame/extent/res pulled from live `local_costmap`), with a `write_row(
   RiskChannel, value_slab, mask_slab)` that asserts shape/geometry match.
3. Default unobserved-policy = configurable pessimistic prior (not 0), exposed as critic
   config (same no-hard-code discipline as Q-008 `k`).
4. Partial-stack: unimplemented rows publish all-unobserved (§5); flipping a renderer on
   needs no critic change.
5. RViz: per-row overlay + a combined observability overlay (where is the stack blind).
6. `qual:` pre-P5; quantitative gate is the P5 risk-field ablation (#16) once the harness lands.

## 7. Open questions (kept inline — promote to deliberations.md only after #50 merges)

> #50 currently prepends Q-009 to `deliberations.md`; a concurrent prepend here would
> textually conflict on the file top (the D-011 multi-branch failure mode). So these are
> logged inline and promoted in a later cycle, exactly as Q-010/Q-011 were deferred.

- **O-1 — mask granularity (→ Q at promotion).** Per-channel `[C,H,W]` mask (correct,
  ~2× footprint, lean) vs single shared `[H,W]` mask (cheap, lossy). Footprint is
  negligible at design resolution, so correctness wins unless a profiling result later
  forces the shared plane. Decide for real when the first multi-row renderer ships.
- **O-2 — channel weighting matrix vs per-channel routing (→ Q at promotion).** §4 routes
  each row through a class-specific mechanism. Stage U3 ("5채널 + critic 가중치 매트릭스",
  track §3) implies a weight matrix; reconcile "weight matrix" with "heterogeneous routing"
  before U3 — they are not the same object and must not be conflated.
- **O-3 — `static` channel overlap with the existing costmap.** Row 0 (`static`) and Nav2's
  own `local_costmap` both encode static occupancy; define whether row 0 is the costmap
  itself, its uncertainty, or a replacement, to avoid double-counting static obstacles in
  the cost. Defer to the U2 static-channel prototype.

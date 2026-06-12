# Research State — auto-generated each cycle

_Last updated: 2026-06-13 00:00 KST · cycle p3-epistemic-channel-bev-rendering_

## North star distance

Still **0 measured numbers** — first quantitative baseline (`runs/cafe-001.json`)
remains unrun (Owner=user). Phase clock is **P3** (risk/uncertainty fields). The P3
design lane keeps advancing while the P2 build path stays merge-blocked: this cycle
specced the **epistemic channel BEV rendering** (ensemble σ² → ego-frame grid), the
keystone "render-ready as a BEV channel" claim that the residual-rollout reference
(PR #49) left as a one-liner. Two of the five risk-BEV channels are now design-pinned
(epistemic this cycle; the rollout/cost wiring in #49).

## Current bottleneck

**Human merge bandwidth on build-path code PRs — unchanged.** PR queue at 5 (gate-1
cleared this cycle, queue < 6, so the carried `Doing` TODO finally ran). The P2 code
lane (#44 D-009 scaffold keystone, #45 training-data, #23 dataset-gen) plus the D-011
root gate fix (#47) all need human merge — Curator auto-merges only safe-surface docs.
Until #44/#45 land, every P2 code step is PR-dependency-blocked (feasibility filter),
so the executor keeps working the independent P3 design lane. Note: STATE/JOURNAL/RESULTS
snapshots still ride on feature branches (the #47/D-011 fix that strips them is itself
merge-stuck), so the design-lane PRs (#49, #50) carry interleaving snapshot diffs.

## Open experiments

| branch | last update | last description | days open |
|---|---|---|---|
| `autoresearch/p3-epistemic-channel-bev-rendering` | 2026-06-13 00:00 | epistemic σ²→BEV grid spec, **doc-only** | 0 (PR #50) |
| `autoresearch/p3-residual-rollout-epistemic-ref` | 2026-06-12 01:00 | residual-in-rollout + variance→margin ref, doc-only | ~1 (PR #49) |
| `autoresearch/p0-gate1-exclude-closed-pr-branches` | 2026-06-09 | D-011 root gate fix, **MERGEABLE** | ~4 (PR #47) |
| `autoresearch/p2-residual-dynamics-mlp-scaffold` | 2026-06-09 | D-009 scaffold (keystone) | ~10 (PR #44) |
| `autoresearch/p2-training-data-collection` | 2026-06-09 | replay buffer | ~10 (PR #45) |
| `autoresearch/p2-unicycle-dataset-generator` | 2026-06-09 | dataset gen | ~16 (PR #23) |
| `autoresearch/p2-energy-based-residual-dynamics-reg` | 2026-06-09 | energy reg | ~16 (PR #24) |

## Recent learnings (last 3 cycles)

- **(this cycle)** "Render-ready as a BEV channel" hid a trajectory-space→grid-space
  map: σ² is per-rollout-step, not native to a grid. The content is the **scatter
  (→critic) vs query-grid (→viz/P5)** split, each path assigned to its consumer.
- **(this cycle)** Epistemic normalization needs a **fixed `σ²_ref`** (per-frame min-max
  kills cross-frame comparability + the P5 calibration metric) — which exposed Q-009:
  `σ²_ref` and the margin gain `k` (Q-008) are the same un-set knob, gated on a P5 OOD
  measurement, and should be swept together.
- **(06-12)** K=3 ensemble batches more easily than a GP (flattened `[M·T,d]` matmul,
  solver-free); var→margin **inflation** beats additive λσ² for routing disagreement→safety.

## Next claude-actionable (this cycle would pick from here)

1. **Spec the aleatoric channel** (predictive-variance head → BEV) as the symmetric
   sibling of the epistemic channel, reusing this cycle's grid/normalization contract.
   Why-now: keeps the P3 epi/ale pair complete and is feasible doc-only, no code dep.
2. **Spec the multi-channel BEV stack tensor** (`[5,H,W]` channel order + unobserved-mask
   channel) — the single interface the risk-aware MPPI cost consumes. Why-now: unifies
   the now-specced epistemic + the margin-inflation cost interface into one contract.
3. **Spec margin-inflation cost-critic interface** (`k·σ` entry point, TODO `37cc5d39-…-8171`,
   already `Today`) — pairs with #1/#2; sets up Q-008's `k` knob. Why-now: independent
   design step, still merge-unblocked.

_(All three are doc/interface steps — safe-surface, Curator-drainable, no PR-dependency.
The P2 code TODOs — EnsembleResidualDynamics wrapper, MPPI rollout integration — stay
infeasible until #44/#45 reach main.)_

## Next user-blocked (waiting on user action — surfaces in Telegram queue, not for PLAN)

1. **Merge build-path PRs #44 (keystone) → #45 → #23, and #47 (D-011 root gate fix).**
   These need human review (touch `learning/`/`scripts/`), Curator won't auto-merge them.
   Until they land, the P2 code lane is fully blocked and the snapshot-on-branch conflict
   surface persists. Run `bash scripts/aggregate_results.sh` on main afterward.
2. **`358c5d39`** Run `cafe_straight_v0` sim with `include_run_metrics:=true` →
   `runs/cafe-001.json` (first quantitative baseline). Owner=user, 25+ days.
3. **`36bc5d39`** Install PyTorch (if claude-side install refused) — blocks ML
   training validation.

## Cycles to date

- 이번 주: 2 productive cycles (P3 design lane: residual-rollout ref + epistemic BEV render).
- 프로젝트 통합: ~20 productive cycles.

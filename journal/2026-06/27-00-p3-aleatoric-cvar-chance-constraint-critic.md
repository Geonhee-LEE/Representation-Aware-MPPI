# P3 aleatoric risk cost-critic interface (chance-constraint / CVaR)

- **Cycle**: 2026-06-27 00:00 KST
- **Branch**: `autoresearch/p3-aleatoric-cvar-chance-constraint-critic`
- **TODO**: `p3-aleatoric-cvar` Spec the aleatoric → CVaR / chance-constraint sibling cost-critic interface (stack idx 4)
- **Phase**: P3
- **Status**: keep

## What I tried
- Authored `docs/aleatoric_risk_cost_critic_interface.md` — the consumer end of the
  aleatoric (idx 4) stack row, sibling of the merged epistemic margin interface (#53).
  Routes irreducible noise via a **standalone `AleatoricRiskCritic`**: chance-constraint
  `d_eff = d − z(δ)·σ` tightening (default) + optional Gaussian closed-form **CVaR** tail
  penalty; tighten-only / `Δ_max`-clamped / mask-gated; `cost_weight=0` no-op default.
- Promoted the deferred **D-013** (epistemic critic placement, from #53) + new **D-014**
  (this) into decisions.md — now conflict-free post-#52/#53 merge.
- Promoted **Q-010/Q-011/Q-012** into deliberations.md and cross-linked stack §4 + aleatoric §7.

## What worked / what failed
- Timing was exactly right: aleatoric render doc §4/§7 explicitly deferred this to "a
  sibling of the margin interface, once it lands so they share the config surface" — #53
  merged at 23:00 KST this very cycle, so the sibling could finally be written.
- Caught dangling refs: Q-010/Q-011 were cited by the merged #51 doc but never existed in
  deliberations.md (the recurring prepend-data-loss pathology) — promoted them, closing the gap.
- Pure design/doc; no code, so no build risk. The epi/ale split is now load-bearing in the
  critic stack (two critics, two stack rows, two mechanisms — never collapsed).

## North-star delta
- **P3 variance→safety routing design lane is now COMPLETE**: both model-uncertainty rows
  have concrete nav2_mppi critic specs (epistemic→margin `RiskInflationCritic`,
  aleatoric→risk `AleatoricRiskCritic`) sharing one config surface, both with `=0` ablation no-ops.
- No measured numbers yet (still 0). All remaining P3 forward motion is now gated purely on
  P2 build-path code reaching main — the doc lane has genuinely run out of conflict-free work.

## Key learnings
- The epistemic `k` and aleatoric `z(δ)`/`α` look like the same "multiply σ" knob but are
  semantically distinct: `k`→0 as the model learns (reducible distrust), `δ`/`α` are a fixed
  risk appetite that persists (irreducible noise). Conflating them is the P3-defining error.
- When an append-at-top shared doc (decisions/deliberations) is free of open-PR contention,
  batch ALL pending promotions in one pass — it's the cheapest moment and prevents the
  dangling-ref data loss that bit Q-008/Q-010/Q-011.

## Recommended next 1–3 priorities
1. (user) **Merge the P2 build-path cluster #44→#45→#23** — the sole gate on every P3 code
   step (ensemble → renderers → stack → both risk critics). The entire P3 design is now spec-complete.
2. (claude, if any conflict-free doc work remains) audit P3 spec docs for any other
   forward-reference / dangling Q-D id before the lane fully idles on P2.
3. (P5) the `δ`/`α` (Q-012) + `k` (Q-008) + `σ²_ref`/`σ²_ref_ale` (Q-009/Q-011) sweep all
   land in one risk-calibration harness — note for the P5 eval-harness design.

## Artifacts
- PR: #54 (https://github.com/Geonhee-LEE/Representation-Aware-MPPI/pull/54)
- Files touched: docs/aleatoric_risk_cost_critic_interface.md (new), docs/decisions.md, docs/deliberations.md, docs/aleatoric_channel_bev_rendering.md, docs/multi_channel_risk_bev_stack.md, results/p3-aleatoric-cvar-chance-constraint-critic.tsv
- TSV row appended: yes

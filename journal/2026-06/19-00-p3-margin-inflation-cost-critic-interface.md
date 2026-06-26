# P3 margin-inflation cost-critic interface — where epistemic k·σ enters nav2_mppi

- **Cycle**: 2026-06-19 (KST)
- **Branch**: `autoresearch/p3-margin-inflation-cost-critic-interface`
- **TODO**: `37cc5d39` Spec margin-inflation cost-critic interface (sets up Q-008 k knob)
- **Phase**: P3
- **Status**: keep

## What I tried
- Authored `docs/margin_inflation_cost_critic_interface.md`: the consumer end of the P3
  risk-stack — fixes **where** the epistemic channel (idx 3) inflates the obstacle margin
  inside the *actual* nav2_mppi critic stack (`CostCritic` + `inflation_layer` from
  `config/nav2_mppi_params.yaml`).
- Decided: a **standalone `RiskInflationCritic`**, not a `CostCritic` overload — and a
  **tighten-only, bounded (≤ inflation_radius), mask-gated** `k·σ` rule (unobserved ⇒ no
  inflation), epistemic-only (aleatoric → sibling CVaR term).
- Restored the **Q-008** deliberation (it was missing from `deliberations.md` despite being
  cited by `residual_in_rollout_reference.md` + STATE — lost in an earlier prepend conflict);
  marked it `partially-answered` (routing resolved, `k` value still P5).

## What worked / what failed
- The interface dropped out cleanly because the three upstream docs (residual-in-rollout,
  epistemic, stack-tensor) had each deferred the *exact same sentence* to "the critic doc" —
  this cycle just had to honor those forward-references against the real config.
- Avoided the D-011 trap: `decisions.md` top on main is still D-011 (D-012 lives only on
  open #52), so prepending D-013 here would add/add-conflict with #52. Deferred the D-013
  promotion; recorded the decision inline + in Q-008 instead. `deliberations.md` was safe
  (its toucher #50 merged; #52 doesn't touch it).
- Found a real data-loss bug: Q-008 had silently vanished from `deliberations.md` — the
  concurrent-prepend conflict class D-011 targets has already cost one deliberation entry.

## North-star delta
- **P3 design lane is now complete**: rollout-wiring + epistemic render + aleatoric render +
  stack-tensor contract + **margin-inflation routing** all specced. The variance→safety path
  is fully drawn on paper; only code (blocked on #44/#45 reaching main) remains.
- No measured numbers yet (still 0 — gated on the P5 harness + the user baseline run).

## Key learnings
- The obstacle margin can only be made representation-aware at the **critic** level, not the
  costmap-inflation level: inflation is a global pre-rollout transform and can't vary per
  cell by a field recomputed each control step. This pins all future risk-routing to critics.
- `k=0` default is the discipline that lets P3 *plumbing* land and smoke-test before any
  tuned gain exists — the ablation flips one number instead of wiring a critic under deadline.
- Shared append-at-top docs keep losing entries to prepend conflicts; restoring Q-008 is a
  reminder to grep for cited-but-missing Q/D ids when touching these files.

## Recommended next 1–3 priorities
1. (user) Merge the P2 build-path cluster (#44 keystone → #45 → #23) — every P3 code step
   (ensemble → renderers → RiskInflationCritic) stays blocked until they reach main.
2. After #52 merges: promote the `RiskInflationCritic` placement decision to `decisions.md`
   as **D-013**, and batch the pending Q-010/Q-011 + O-1/O-2 promotions in one conflict-free
   pass.
3. Spec the **aleatoric → CVaR/chance-constraint** sibling cost term (idx 4 routing) — the
   one remaining unspecced channel-routing half, now that epistemic routing is fixed.

## Artifacts
- PR: #53 (autoresearch/p3-margin-inflation-cost-critic-interface)
- Files touched: docs/margin_inflation_cost_critic_interface.md, docs/deliberations.md, results/p3-margin-inflation-cost-critic-interface.tsv
- TSV row appended: yes

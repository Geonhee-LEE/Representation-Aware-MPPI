# The default D-405 wanted to lower was never shipped

- **Cycle**: 2026-08-21 16:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: `3c3c5d39` Ship `w_voo` 200 → 50 in `RiskMPPI` with a pytest pinning the Pareto claim
- **Phase**: P3
- **Status**: keep

## What I tried

- Picked STATE's next-actionable #1 exactly as written: change `RiskMPPI`'s
  D-027-inherited `w_voo` default from 200 to the measured 50, with a pytest
  pinning D-405's Pareto claim.
- Opened `risk_mppi.py` to make the one-token change and found `w_voo: float = 0.0`.
  Stopped and verified the premise three ways before writing anything.
- Deliverable re-aimed on the spot: correct the single false sentence, and pin the
  true default in the tree so the claim is checkable rather than quotable.

## What worked / what failed

- **The premise does not exist.** Three independent checks agree: `RiskMPPI.__init__`
  ships `w_voo = 0.0`; `ObservationValueCritic.w_voo` is `0.0` (already pinned at
  `test_arm_freeze.py:135`); and `git log -S "w_voo: float = 200" --all` is **empty
  across all history** — 200 was never a default in any commit.
- **D-027 says the opposite of what was attributed to it.** Its Decision (5) reads
  "default 는 하나도 안 움직인다. `w_voo` default 0.0 → byte-identical no-op". D-027
  *measured* 200 as the naive sweep's pick and **rejected** it — 6.19× the baseline
  cost spread, median ESS 77.9 → 1.00, arm collides.
- **The propagation path is one line.** `scale_match.py:7` said "D-027 **shipped**
  `ObservationValueCritic` at `w_voo = 200`". The other two modules carrying the same
  number are correct: `weight_units.py:5` calls it "the naive weight",
  `denominator_scope.py:4` says "priced". One of three was wrong, and it is the one
  D-405 cited by line number.
- **The real change is `0 → 50`, not `200 → 50`** — a critic-activation decision, not
  a de-tuning. It would break D-027's ablation invariant *by design* (`w_voo = 0` must
  be byte-identical to the all-off arm) and silently re-baseline every downstream
  comparison that builds `RiskMPPI` without an explicit `w_voo`. Not purchasable with
  one scene × 5 seeds, so the default stayed put.
- 4 new assertions pass in 2.30 s; `census_preempt` clean on all 5 re-derived censuses
  (`citation_sites` 0 unregistered — the 6.19× citation survives the correction intact).

## North-star delta

- **No planner movement, and deliberately so** — this cycle spent its budget proving a
  proposed planner change was aimed at nothing. That is negative-delta work that
  prevents a wrong positive-delta commit.
- D-405's two measured numbers (`cte_rms` 0.1314, `clear_min` 0.0273 at `w_voo=50`)
  **survive unchanged**; only the sentence describing what they should be compared
  against was wrong. The comparison is now correctly stated as against a *shipped-off*
  critic.
- +3 assertions converting an 11-week-old prose claim into a tree-checkable one.

## Key learnings

- **Citation preserves the magnitude but not the verb.** `w_voo = 200` is cited at 9
  registered sites; `swept` / `priced` / `shipped` all wrapped the same number, and the
  one wrong verb aimed a whole cycle's work at a non-existent target. `citation_audit`
  catches an *unregistered* magnitude, not a *false claim about* a registered one.
- **The cheapest check on a task is opening the file it names.** D-405, STATE, and the
  TODO all agreed with each other and none of the three agreed with `risk_mppi.py`.
  Mutual agreement among derived documents is not corroboration.
- **A default that is "inherited" is worth grepping before it is worth changing.** The
  word "inherited" in D-405 was doing the work of a measurement.

## Recommended next 1–3 priorities

1. Re-run the D-405 grid on a **second scene** (`cafe_cut_in_v0` / `city_curved_v0`).
   This was already priority #2 and is now the *only* way the `0 → 50` question can
   advance — one scene cannot buy an ablation-invariant break.
2. Decide `ShadowCostCritic` retirement (inert at 2000 across D-021 and D-405, 11 weeks
   apart). Unchanged by this cycle.
3. Consider whether `citation_audit` should register a claim's **verb**, not just its
   magnitude — this cycle is the first measured instance of that gap costing a cycle.

## Artifacts
- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic)
- Files touched: eval/mppi_sandbox/scale_match.py, eval/mppi_sandbox/tests/test_observation_value_critic.py, docs/decisions.md, journal/2026-08/21-16-*.md, results/p3-epistemic-shadow-cost-critic.tsv
- TSV row appended: pending

# P3→P5: record the σ-calibration-quality axis fork (deferred Q-015)

- **Cycle**: 2026-07-03 00:00 KST
- **Branch**: `autoresearch/p3-sigma-calibration-quality-axis`
- **TODO**: `p3-sigma-calib` (authored this cycle — no Notion, unauthenticated)
- **Phase**: P3
- **Status**: keep

## What I tried
- Phase-0 scan surfaced a **4-entry same-day (2026-07-02) feed convergence** on one
  uncovered fork: the σ/covariance the risk margins consume must itself be *calibrated*,
  and calibration quality is its own metric — Rethinking-Gaussian (`2603.10407`), OCULAR
  (`2605.13028`), Scenario-aware UQ (`2512.05682`), How-Human-Motion (`2601.09856`).
- Verified the gap is real: `p5_risk_calibration_harness.md` §2 sweeps σ-*consumer* gains
  (`k`/`δ`/`α`/`σ²_ref`) and §3's metric vector scores only downstream outcomes
  (near-miss, time-to-goal, cte, jerk) — no ECE/reliability/coverage axis, and §4 excludes
  only the `σ²_ref` *scale*, not σ-trustworthiness.
- Recorded it as harness **§3½ + deferred Q-015**; deferred the `deliberations.md` prepend
  (D-011 trap — #58 owns a pending Q-014 prepend). Doc-only, +60/-1.

## What worked / what failed
- Re-open condition (b) fired cleanly: STATE (07-02 23:00) declared the *deferred-ref* lane
  exhausted, but its Phase-0 that cycle picked the deferred Q-014 and never scanned fresh
  feed for **new** forks — so this convergence was genuinely unclaimed, not filler.
- Confirmed Q-015 is orthogonal to Q-013/D-015: those are *how-to-sweep* / *who-owns-sweep*
  of the consumer gains; Q-015 is **upstream** — is the σ input trustworthy + does §3 need a
  calibration metric. No overlap, so it earns its own Q.
- Notion MCP unauthenticated again (gates 2/4 + Phase 5 reconcile from STATE, per precedent).

## North-star delta
- No measured numbers (still 0 — gated on P2). Pure design-lane motion: +1 P3→P5 design
  fork recorded, closing a real hole in the harness spec (it would have silently absorbed σ
  miscalibration into `k` and mis-generalized across scenarios).

## Key learnings
- "Doc lane exhausted" is scoped to *deferred refs*, not to *fresh-feed forks*: a Phase-0
  convergence can re-open genuine design work even when every prior deferred ref is cleared
  and the build lane is blocked. The exhaustion claim must be re-tested against Phase-0 each
  cycle, not inherited from STATE.
- The defer→promote (D-011) lane now has **two** items queued behind #58: Q-014 (its own
  content) and Q-015 (this cycle, inline in the harness doc). When #58 merges, one cycle can
  promote Q-015 to `deliberations.md`.

## Recommended next 1–3 priorities
1. (user) Merge P2 build-path cluster #44→#45→#23→#24 — still the sole gate on all P3 code.
2. Once #58 merges: promote Q-015 (σ-calibration-quality axis) to a canonical
   `deliberations.md` stub + mark the §3½ note "Promoted".
3. If a P2 PR merges: the §3½ **ECE/coverage metric axis** needs no new σ source — it can be
   added to the harness §3 table immediately as the first concrete calibration-metric step.

## Artifacts
- PR: #59 (autoresearch/p3-sigma-calibration-quality-axis)
- Files touched: docs/p5_risk_calibration_harness.md, results/p3-sigma-calibration-quality-axis.tsv
- TSV row appended: yes

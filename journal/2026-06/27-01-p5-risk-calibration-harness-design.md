# P5 risk-calibration harness design — one sweep owns all P3 uncertainty knobs

- **Cycle**: 2026-06-27 01:00 KST
- **Branch**: `autoresearch/p5-risk-calibration-harness-design`
- **TODO**: `p5-risk-calib` Draft the P5 risk-calibration harness design note
- **Phase**: P3 (→P5 bridge)
- **Status**: keep

## What I tried
- The P3 design lane completed last cycle (#54) but left **five tuning knobs**
  (`k`/`δ`/`α`/`σ²_ref`/`σ²_ref_ale`) each parked in a different deliberation with
  **no owner of the calibration procedure**. Authored `docs/p5_risk_calibration_harness.md`
  specifying a single offline harness `eval/calibrate_risk.py` that sweeps them jointly.
- Reused the existing `run_metrics` / `path_tracking_metrics` JSON as the objective
  (adds *search*, not a new metric); sweeps the coupled `(k, δ)` plane with refs frozen;
  emits a (near-miss, time-to-goal) Pareto front per scenario.
- Recorded the harness-ownership decision (pending D-015) + sweep-strategy open
  question (pending Q-013) **inside the new doc**, deferring both shared-file prepends.

## What worked / what failed
- Single new file + its TSV — **zero shared-file edits**, so no D-011 conflict trap with
  open #54 (which holds the decisions.md / deliberations.md prepends). Verified main's
  decisions.md still tops at D-012, confirming #54 is the live contender.
- The genuinely-new content is the **coupling argument**: `k·σ` and `z(δ)·σ_ale` subtract
  from the *same* `d_eff`, so five isolated sweeps would double-count safety and
  over-inflate — that is the concrete reason "one harness" beats "five notebooks", not
  just DRY plumbing.
- Cost discipline: rejected the combinatorial 5-D grid; froze the scale refs (`σ²_ref`
  has no OOD set anyway, `σ²_ref_ale` settable today) and swept only the 2-D gain plane.

## North-star delta
- No measured numbers (still 0). But this is the **first artifact that names the path to
  the first numbers**: it pins which metric the P3 risk knobs get tuned against and how,
  collapsing five future P5 tasks into one harness spec a cycle can pick up cold.
- Pure design — build status unchanged; forward code motion still gated on P2 merges.

## Key learnings
- The design lane wasn't *quite* empty: "the knobs exist but nothing says how to tune
  them" was a real, conflict-free gap distinct from the two thin STATE items — and it has
  higher leverage (gateway to quantitative eval) than the dangling-ref audit.
- This cycle pushed the queue to **6**, so next cycle will `pr-queue-full` skip. The doc
  lane is now genuinely exhausted of conflict-free work that doesn't add queue pressure —
  the honest next move is **user merges P2**, not more executor docs.

## Recommended next 1–3 priorities
1. (user) Merge the P2 build-path cluster #44→#45→#23 — the sole gate on all P3 code AND
   on ever running this calibration harness.
2. (claude, low) The dangling-ref audit (remaining STATE item) — only if queue drains
   below 6; otherwise it just deepens queue pressure for near-zero north-star value.
3. (later) Once #54 merges and decisions.md is conflict-free, promote D-015 (harness
   ownership) + Q-013 (sweep strategy) from this doc into the shared ledgers.

## Artifacts
- PR: #55 (autoresearch/p5-risk-calibration-harness-design)
- Files touched: docs/p5_risk_calibration_harness.md, results/p5-risk-calibration-harness-design.tsv
- TSV row appended: yes

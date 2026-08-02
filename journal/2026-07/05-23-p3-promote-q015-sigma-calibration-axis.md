# Promote Q-015 (σ-calibration-quality axis) to deliberations.md

- **Cycle**: 2026-07-05 23:00 KST
- **Branch**: `autoresearch/p3-promote-q015-sigma-calibration-axis`
- **TODO**: `p3-sigma-calib-promote` Promote Q-015 (σ-calibration quality axis) inline → canonical deliberations.md
- **Phase**: P3
- **Status**: keep

## What I tried
- Verified PR #58 (Q-014 promotion) and PR #59 (Q-015 inline record) both merged at 23:00:45/51 KST during cycle startup — the D-011 defer condition named in the §3½ deferred note was cleared
- Extracted Q-015 content from harness §3½ and promoted to a canonical 12-line stub in `deliberations.md` (prepended above Q-014, newest-first convention)
- Replaced the 11-line §3½ deferred block with a 3-line "Promoted" note linking to deliberations.md
- Updated harness footer cross-ref from "(+ Q-015 deferred inline §3½…)" to clean `Q-015` reference

## What worked / what failed
- Same defer→promote pattern as Q-013 (#56) and Q-014 (#58) — executed cleanly with zero contention (deliberations.md now has no open PRs touching it)
- Branch carries only unique-path files (deliberations.md, harness doc, TSV) — no snapshot conflict risk
- Gate-1 recount after #58/#59 merge: true queue = 4 (P2 build-path only), well under cap of 6

## North-star delta
- No motion toward first quantitative numbers; this is pure design-lane maintenance
- Q-015 is now canonical in deliberations.md — the σ-calibration-quality question (is the σ trustworthy before we sweep against it?) has its proper home and will surface in future PLAN passes
- The deferred-ref doc lane for the current P3 design epoch is now fully cleared: Q-013 → #56, Q-014 → #58, Q-015 → this PR (#60)

## Key learnings
- PR #58 and #59 merged at 23:00:45/51 KST — just ~37s after cycle start. Gate-1 check ran at 23:00:08, captured them as OPEN; by planning time they were MERGED. Always recount the gate after fetching the full PR state before deciding to skip
- "Doc lane exhausted" must be re-evaluated each cycle against the current merge state, not inherited from STATE — the same lesson from the 07-03 STATE re-open condition (b)
- The research feed (top 3 entries today) has new P2/P3 Suggested TODOs (condition-aware residual, MPPI-PID, HOLO-MPPI) — all require P2 code, so they are backlog until #44/#45/#23/#24 merge

## Recommended next 1–3 priorities
1. (user) Merge P2 build-path cluster: #44 → #45 → #23 → #24 — sole gate on all downstream P3/P4/P5 code work
2. (claude, once any P2 PR merges) Add ECE/coverage metric axis to harness §3 — Q-015 Lean says this needs no new σ source, so it is immediately feasible once the file is conflict-free after the P2 PRs process
3. (claude, backlog) Evaluate top-3 research Suggested TODOs from 2026-07-05 feed: condition-aware residual dynamics (P2), MPPI-PID (P2/경로추종), HOLO-MPPI (P1/core) — create [research]-prefixed TODOs once Notion MCP is reachable

## Artifacts
- PR: #60 pending merge (`autoresearch/p3-promote-q015-sigma-calibration-axis`)
- Files touched: `docs/deliberations.md`, `docs/p5_risk_calibration_harness.md`
- TSV row appended: yes (`results/p3-promote-q015-sigma-calibration-axis.tsv`)

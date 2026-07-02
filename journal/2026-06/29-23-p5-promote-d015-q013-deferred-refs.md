# Promote deferred D-015 + Q-013 into the canonical logs

- **Cycle**: 2026-06-29 23:00 KST
- **Branch**: `autoresearch/p5-promote-d015-q013-deferred-refs`
- **TODO**: `p5-promote-d015-q013` (authored — STATE `Next claude-actionable` #1 dangling-ref audit; Notion MCP unavailable this cron run)
- **Phase**: P3
- **Status**: keep

## What I tried
- The Curator merged #54/#55 at exactly this cycle's boundary (14:00:49–55Z), draining the queue 6→4 — the drain STATE predicted for *06-30* actually landed *now*, so the executor became feasible a cycle early.
- Ran the STATE-flagged P3/P5 dangling-ref audit. Finding: D-015 (calib-harness ownership) and Q-013 (sweep strategy) were recorded *inline* in `p5_risk_calibration_harness.md` (06-27, #55) with their `decisions.md`/`deliberations.md` prepends **deferred** to dodge the D-011 conflict trap.
- With #55 now merged and all 4 remaining open PRs P2 build-path (verified zero contention on the two logs), promoted both entries and marked the harness doc's two pending-promotion notes resolved.

## What worked / what failed
- Clean conflict-free promotion: only `decisions.md` + `deliberations.md` + the harness doc + a new TSV touched; no snapshot files, no `src/`, no contention with the 4 open PRs.
- Verified post-edit: D-015/Q-013 each present exactly once; the only residual `(→D-015)` is inside D-015's own historical-context sentence (intentional).
- Notion MCP was unauthenticated in this cron run (headless limitation) — TODO reconciliation/announce-id fell back to a synthetic id; flagged for PLAN_NEXT.

## North-star delta
- No motion on measured numbers (still 0 — gated on P2). Pure design-lane hygiene.
- But the audit trail is now coherent: the two highest design decisions of the P3→P5 bridge live in the canonical ADR/deliberation logs instead of buried in a spec doc — D-008's whole point, and what a future P5 cycle reads cold.

## Key learnings
- The "low-value, defer-while-queue≥6" audit STATE parked was actually *higher* value once #55 merged: it wasn't a generic dangling-ref sweep, it was recovering two real deferred decisions before they rotted. The conflict-free doc lane re-opens the moment the contending PR merges — worth re-checking each cycle, not assuming "exhausted" is permanent.
- The Curator/executor 23:00 co-fire creates a race: the queue snapshot can read stale (pre-merge). Always recompute queue depth *after* `git fetch` near the top of the hour before trusting a `pr-queue-full` skip.

## Recommended next 1–3 priorities
- (user) Merge the P2 build-path cluster #44 (keystone) → #45 → #23, then #24. Still the sole gate on ALL P3 code (ensemble → renderers → critics → this calibration harness).
- (claude) Doc lane is now genuinely thin again — next conflict-free candidate is small. Prefer waiting for P2 over authoring filler. Re-audit deferred refs only if a new merge lands.

## Artifacts
- PR: https://github.com/Geonhee-LEE/Representation-Aware-MPPI/pull/56
- Files touched: docs/decisions.md, docs/deliberations.md, docs/p5_risk_calibration_harness.md, results/p5-promote-d015-q013-deferred-refs.tsv
- TSV row appended: yes

# Promote Q-014 (epistemic response-mode fork) to deliberations.md

- **Cycle**: 2026-07-02 23:00 KST
- **Branch**: `autoresearch/p3-promote-q014-epistemic-response-mode`
- **TODO**: doc-lane deferred-ref cleanup (STATE re-open condition (a): a merge landed)
- **Phase**: P3
- **Status**: keep

## What I tried
- Promoted the **O-2 fork** (is passive `k·σ` margin the right *response mode* for the
  epistemic channel, or does it need an active-perception / tube term?) from inline-only in
  `margin_inflation_cost_critic_interface.md` §7 to a canonical **Q-014** stub at the top of
  `deliberations.md`.
- Updated the margin-doc §7 note from "Deferred as Q-014 — to be prepended once #56 merges"
  → "Promoted to `deliberations.md` Q-014"; the §7 O-2 block stays the canonical rationale.

## What worked / what failed
- **Queue-race caught (again).** Pre-fetch snapshot read queue=6 (would `pr-queue-full` skip);
  a fresh fetch showed #56 **and** #57 both merged at the 23:00 co-fire → true queue=4. The
  06-29 learning ("recompute after fetch before trusting a skip") paid off directly this cycle.
- **The deferred ref was real, not filler.** #56's merge cleared the exact D-011 same-file
  collision that forced Q-014 inline-only; leaving it would have left the deliberation log
  missing a logged open question two design docs forward-reference.
- Clean doc-only diff (+14/-4 across 2 files); no snapshot-file leak; PR #58 opened.

## North-star delta
- No motion toward first numbers — still 0 measured, P2-gated. This is design-record hygiene.
- Design coherence +1: the epistemic response-mode fork is now a tracked Q, not a dangling
  inline note — the P5 ablation matrix (margin-only vs +active-perception vs tube) is now
  discoverable from the canonical deliberation log.

## Key learnings
- The "doc lane exhausted" STATE claim keeps being **conditional on no fresh input** — a merge
  (not just a new feed entry) re-opens conflict-free deferred-ref work. This is the 3rd cycle
  where a co-fire merge unblocked a same-file-deferred prepend; the D-011 defer→promote pattern
  is now a recurring, predictable lane.
- After this promotion the doc lane is **genuinely thin again** — no further deferred refs are
  outstanding (D-015/Q-013 done via #56, Q-014 done here). Next value is P2-merge-gated.

## Recommended next 1–3 priorities
1. (user) Merge the P2 build-path cluster #44 (keystone) → #45 → #23 → #24 — the sole gate on
   ALL P3 code (ensemble → renderers → `[5,H,W]` stack → both risk critics → calib harness).
2. (claude) Prefer an honest `plan-no-fit` skip over filler until a P2 PR merges OR a new
   same-day feed convergence surfaces an uncovered fork.
3. (claude, when P3 code unblocks) Implement the margin-only `RiskInflationCritic` baseline
   first (D-013) so Q-014's 3-way ablation has a `k=0` reference arm.

## Artifacts
- PR: https://github.com/Geonhee-LEE/Representation-Aware-MPPI/pull/58 (autoresearch/p3-promote-q014-epistemic-response-mode)
- Files touched: docs/deliberations.md, docs/margin_inflation_cost_critic_interface.md
- TSV row appended: yes

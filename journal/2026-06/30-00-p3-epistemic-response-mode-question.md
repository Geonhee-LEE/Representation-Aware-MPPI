# P3 epistemic response-mode open question (margin vs active-perception)

- **Cycle**: 2026-06-30 00:00 KST
- **Branch**: `autoresearch/p3-epistemic-response-mode-question`
- **TODO**: feed-driven (Notion unreachable this cycle — gate 2/4 read from STATE instead)
- **Phase**: P3
- **Status**: keep

## What I tried
- STATE declared the build lane fully P2-blocked and the doc lane "exhausted", recommending a `plan-no-fit` skip. But Phase 0 surfaced **four** independent 2026-06-29 feed entries converging on one design fork the spec'd P3 epistemic critic does not consider.
- Recorded that fork as **O-2 / deferred Q-014** in the *uncontended* `docs/margin_inflation_cost_critic_interface.md` §7 — conflict-free with the open PRs (#56 owns `deliberations.md`/`decisions.md`; the P2 cluster owns `learning/`/`data_pipeline/`).
- Deferred the `Q-014` deliberations.md promotion inline (D-011 same-file-prepend trap), mirroring the proven 06-27→06-29 deferred-ref pattern.

## What worked / what failed
- **Worked**: found a genuinely conflict-free, non-filler design-lane edit even with 5 PRs in queue — the critic interface docs are owned by no open PR.
- **Worked**: the fork is real, not invented — the current design (§5) only splits epistemic-*routing* from aleatoric; it silently assumes the epistemic *response* is passive `k·σ` margin. TRIAGE/PA-MPPI say epistemic risk (reducible by sensing) may warrant *active* info-gathering instead.
- **Failed/limited**: Notion MCP was not permission-granted this non-interactive run, so gates 2 (stuck-TODO) and 4 (empty-backlog) were evaluated from STATE.md, and no Notion bookkeeping (Phase 5a–5d) could be written. Logged here instead.

## North-star delta
- No measured numbers (still 0; gated on P2 + the user-owned `cafe-001.json` run).
- + 1 design fork captured before implementation: when P2 lands and the epistemic critic is built, the implementer now has the explicit margin-only-vs-margin+active-perception-vs-tube-margin choice on record, with 4 citations, instead of silently defaulting to margin-only.

## Key learnings
- "Doc lane exhausted" (STATE) is conditional on *no fresh input* — a same-day feed convergence re-opens genuine design-lane value even when the build lane is blocked. Phase 0's literature pre-emption is exactly for this; it overrode a stale-by-1-hour skip recommendation.
- The contended-file map matters: with 5 open PRs, the conflict-free surface is precisely the docs no open PR touches. Check `gh pr view --json files` before picking a doc target.

## Recommended next 1–3 priorities
1. **(user)** Merge the P2 build-path cluster #44→#45→#23→#24 — still the sole gate on every downstream P3 step.
2. After #56 merges, promote **Q-014** (epistemic response-mode) from this doc's §7 into `deliberations.md`, alongside re-checking other deferred refs.
3. When the epistemic critic is implemented (post-P2), make the active-perception term a P5 ablation arm (margin-only vs margin+PA-MPPI-cost vs contraction-tube margin), not a hidden default.

## Artifacts
- PR: https://github.com/Geonhee-LEE/Representation-Aware-MPPI/pull/57
- Files touched: docs/margin_inflation_cost_critic_interface.md, results/p3-epistemic-response-mode-question.tsv
- TSV row appended: yes

# Q-016 (HOLO-MPPI prior interface) — deliberations.md 등록

- **Cycle**: 2026-07-08 23:00 KST
- **Branch**: `autoresearch/p3-q016-holo-mppi-prior-interface`
- **TODO**: (triggered by #61 merge) Q-016 HOLO-MPPI prior interface
- **Phase**: P3
- **Status**: keep

## What I tried
- Confirmed PR #60 and #61 merged at 23:00 KST (Curator auto-merge succeeded) — real queue dropped from 6 to 4, safety gate passed
- Pulled main, read `docs/research_feed_synthesis_2026_07_05.md` to extract the Q-016 definition explicitly deferred by #61
- Prepended Q-016 entry to `docs/deliberations.md` above Q-015 (newest-first convention)
- TSV row appended; PR #63 opened with `safe-auto-merge` label

## What worked / what failed
- Curator auto-merge at 23:00 KST worked exactly as predicted (PRs #60 + #61 merged at 14:00:44Z and 14:00:50Z UTC = 23:00 KST)
- Feed synthesis doc in #61 already defined Q-016 content and reason for deferral (D-011 conflict avoidance) — no ambiguity in writing the entry
- Notion MCP denied (25th cumulative) — could not create research Backlog TODOs (HOLO-MPPI/DUCCT-MPPI/iCrowdNav) as planned in STATE.md; that action remains blocked by MCP grant
- Doc-only change; no build smoke needed

## North-star delta
- +1 deliberation entry: HOLO-MPPI prior interface (Q-016) formalizes the key representation-to-sampler interface question — "should the learned prior see P1 BEV or P2 dynamics latent or both?" with a lean toward (a) P1 BEV-only first
- No code movement; pure design-space formalization
- P3 ends tomorrow (2026-07-09); this closes the last pending design-lane trigger before P4 starts 2026-07-10

## Key learnings
- The feed synthesis (#61) did the heavy lifting — it not only ranked the top-3 TODOs but pre-wrote the Q-016 content and explicitly flagged the D-011 conflict avoidance deferral. Good pattern: research entries should include a concrete Q-NNN draft when they identify an open trade-off.
- Curator auto-merge reliability is now validated: 23:00 KST on-schedule merge of #60+#61 resolved the 6-day queue stall cleanly. The deadlock-breaker (close #24 at 17:00) + Curator (merge #60+#61 at 23:00) together brought queue from 6 → 4 in one evening.
- Notion MCP still denied (25 consecutive). Backlog TODO creation remains the persistent gap — HOLO-MPPI/condition-aware-residual/MPPI-PID TODOs exist only in STATE.md next-actionable, not in Notion yet.

## Recommended next 1–3 priorities
1. **P4 kick-off doc spec** (2026-07-10 — tomorrow, day P4 starts): write `docs/p4_dynamic_obstacles_kickoff.md` scoping dynamic-obstacle risk channel, Gazebo actor setup, iCrowdNav I²Former as Phase 0 candidate — no P2 dependency, no Notion needed
2. **Merge the P2 build-path cluster**: #44 → #45 → #23 (user-blocked; Telegram queue for user)
3. **Create research Backlog TODOs** when Notion MCP grant arrives: HOLO-MPPI BEV-conditioned prior (P1, Priority=P1), condition-aware residual (P2, Priority=P1), MPPI-PID gain-space (P2/P3, Priority=P2), DUCCT-MPPI proper-scoring (P5, Priority=P2), iCrowdNav I²Former (P4, Priority=P2)

## Artifacts
- PR: https://github.com/Geonhee-LEE/Representation-Aware-MPPI/pull/63 (safe-auto-merge label)
- Files touched: `docs/deliberations.md`, `results/p3-q016-holo-mppi-prior-interface.tsv`
- TSV row appended: yes

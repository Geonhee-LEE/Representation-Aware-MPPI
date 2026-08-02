# 2026-07-05 Top-3 Feed Synthesis: Post-P2 Backlog Ranking

- **Cycle**: 2026-07-06 00:00 KST
- **Branch**: `autoresearch/p3-research-feed-eval-0705`
- **TODO**: feed-synthesis-0705 — Rank 2026-07-05 top-3 research Suggested TODOs for post-P2 backlog
- **Phase**: P3
- **Status**: keep

## What I tried

- Read the top-5 entries from `research/feed.md`; 3 of 5 had actionable Suggested TODOs
- Evaluated HOLO-MPPI (BEV-conditioned sampling prior, arXiv 2606.16480), condition-aware residual dynamics (Variational Neural Dynamics, arXiv 2606.27353), and MPPI-PID gain-space path-following (arXiv 2603.29499) against north star and current bottleneck
- Authored `docs/research_feed_synthesis_2026_07_05.md` — ranked evaluation with recommended Backlog order, Q-016 candidate, and per-entry dependency analysis

## What worked / what failed

- Synthesis is straightforward: the three entries are clearly distinguishable on thesis-alignment vs phase-dependency axes
- Notion MCP unauthenticated (again) — could not create the [research]-prefixed Backlog TODOs in Notion; deferred to next cycle when MCP is reachable
- #60 (Q-015 promotion) still open → deliberations.md conflict-blocked; Q-016 candidate captured inline in the synthesis doc, promotion deferred to post-#60-merge
- All three entries require P2 code; HOLO-MPPI is the exception — it can start with P1 BEV and is P2-independent for a first prototype

## North-star delta

- +1 concrete ranked backlog entry: executor now has a cold-start ranking (HOLO-MPPI > condition-aware residual > MPPI-PID) with per-entry dependency analysis; prevents re-reading 3 dense feed entries next cycle
- No movement on measured numbers — doc-only cycle; bottleneck unchanged
- HOLO-MPPI identified as the only top-3 entry that is P2-independent and can be started before #44 merges — potential scheduling advantage

## Key learnings

- HOLO-MPPI is the most thesis-central of the three: representation → sampler-prior is exactly the "representation-aware" coupling the project name promises; its P2 independence is a concrete scheduling lever if the P2 stall extends into P4
- Condition-aware residual (recurrent regime encoder) is the strongest multi-venue answer once P2 lands, but strictly gated on #44
- MPPI-PID can be started with unicycle dynamics (no NN residual), making it the one entry that doesn't require any PR merge; however it's a path-tracking efficiency lever, not a representation thesis move — lower priority unless 경로추종 becomes the specific bottleneck
- Q-016 (HOLO-MPPI prior interface: P1-BEV-only vs P2-latent vs both) is a meaningful architecture fork worth capturing in deliberations.md once #60 merges

## Recommended next 1–3 priorities

1. **(user)** Merge P2 cluster: #44 (keystone) → #45 → #23 → #24 — still sole gate
2. **(claude, when Notion reachable)** Create [research]-prefixed Backlog TODOs for HOLO-MPPI, condition-aware residual, MPPI-PID (from this doc's §Recommended order)
3. **(claude, when #60 merges)** Promote Q-016 (HOLO-MPPI prior interface) to deliberations.md

## Artifacts

- PR: #61 pending merge (autoresearch/p3-research-feed-eval-0705)
- Files touched: `docs/research_feed_synthesis_2026_07_05.md`, `results/p3-research-feed-eval-0705.tsv`
- TSV row appended: yes

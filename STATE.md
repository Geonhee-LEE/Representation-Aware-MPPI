# Research State — auto-generated each cycle

_Last updated: 2026-05-25 00:00 KST · cycle p2-tcfm-evaluation_

## North star distance

Still **0 measured numbers** — the user sim run for `runs/cafe-001.json` remains unexecuted (14+ days). However, P2 work has now started: TCFM architecture evaluation maps a concrete learned-dynamics integration path (Option A: trajectory generator → MPPI cost eval) that will produce the first "learned representation → MPPI" demo once training data exists. The 15-day executor drought is broken.

## Current bottleneck

**No trajectory training data for learned dynamics (P2)**. Synthetic unicycle dataset generator can bootstrap TCFM training without waiting for user sim runs. This is the first claude-actionable step toward a working P2 prototype.

## Open experiments

| branch | last update | last description | days open |
|---|---|---|---|
| `autoresearch/p2-tcfm-evaluation` | 2026-05-25 00:00 | qual:doc-only | 0 (PR #22 open) |
| `autoresearch/p0-state-template-split-next-priorities` | 2026-05-10 18:08 | qual:doc-only | 15 (PR #12 open) |

## Recent learnings (last 3 cycles)

- **(this cycle)** TCFM and cfm_mppi are complementary — TCFM provides the velocity-field backbone + training pipeline, cfm_mppi provides the MPPI integration pattern. Option A (trajectory generator) is the simpler P2 prototype path.
- **(this cycle)** CFM's speed advantage is architecturally simple: single ODE solve (~100 Euler steps) replaces diffusion's ~1000 denoising steps, making real-time MPPI feasible.
- **(cycle p0-state-template-split-next-priorities)** Structural template fixes (claude-actionable vs user-blocked sections) prevent Owner-mismatch fix-up commits from recurring.

## Next claude-actionable (this cycle would pick from here)

1. **`(author new)`** Create synthetic unicycle trajectory dataset generator (`scripts/gen_unicycle_dataset.py`) — diff-drive kinematics + random goals, outputs TCFM-compatible `.npz` format. Directly unblocks P2 TCFM training without user sim data.
2. **`36ac5d39…81ec`** [research] Map Flow Planner hierarchical CFM onto Nav2 global/local split — add 1-paragraph to `docs/cfm_mppi_analysis.md`. Complements TCFM evaluation, builds P2 design landscape. Owner=claude, P1, P2, Backlog.
3. **`36ac5d39…81fc`** [research] Extract PA-MPPI perception-aware cost (arxiv 2509.14978) — candidate critic for forward-camera FoV awareness. Owner=claude, P1, P3, Backlog.

## Next user-blocked (waiting on user action — surfaces in Telegram queue, not for PLAN)

1. **`358c5d39`** Run `cafe_straight_v0` sim with `include_run_metrics:=true` → capture `runs/cafe-001.json` (first quantitative baseline). Owner=user, NeedsUserTest=true, P0. 14+ days carrying.
2. **(implicit)** Merge PR #12 (STATE template split) + PR #22 (TCFM evaluation) — doc-only, low-risk.

## Cycles to date

- 이번 주 (Mon 2026-05-19 시작): **1** (first cycle after 15-day drought)
- 프로젝트 통합: **10**

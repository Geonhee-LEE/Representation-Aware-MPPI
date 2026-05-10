# Research State — auto-generated each cycle

_Last updated: 2026-05-10 17:00 KST · cycle p0-prompt-pr-dep-fallback-decision-tree_

## North star distance

Still **0 measured numbers**. PRs #7/#8/#9 are merged; PR #10 (`aggregate_results.sh` PR-status surface) and PR #11 (this cycle, decision-tree feasibility filter) are open. The 1-shot user sim (`ros2 launch … jackal_cafe.launch.py include_run_metrics:=true run_id:=cafe-001`) remains the single action that produces `runs/cafe-001.json` — all claude-side blockers cleared days ago, the gap is human-time on the user side.

## Current bottleneck

**User-owned sim run for `runs/cafe-001.json`** — TODO `358c5d39` (Today, Owner=user, NeedsUserTest=true, P0). Until it lands, calibration of `docs/path_tracking_metrics.md` against measured baselines (TODO `357c5d39…81f1`) stays gated. No claude-actionable item directly addresses this — claude-side cycles compound on infra/process improvements meanwhile.

## Open experiments

| branch | last update | last description | days open |
|---|---|---|---|
| `autoresearch/p0-aggregate-results-pr-merge-status` | 2026-05-10 16:05 | qual:script-syntax-ok | 0 (PR #10 open) |
| `autoresearch/p0-prompt-pr-dep-fallback-decision-tree` | 2026-05-10 17:03 | qual:doc-only | 0 (PR #11 open) |

## Recent learnings (last 3 cycles)

- **(이번 cycle)** Decision tree step 2 was strict-match wording but used as a top-down walk in practice — encoding the walk + feasibility filter (PR-dep / Owner=user exclusions) removes drift, makes rationale paragraphs auditable.
- **(cycle p0-aggregate-results-pr-merge-status)** Decision tree handles freshly-shifted bottlenecks cleanly only if REVIEW recomputes the bottleneck instead of trusting stale STATE.md text. STATE rewrite each cycle is load-bearing.
- **(cycle p0-aggregate-results-pr-merge-status)** `gh pr list --head <branch> --state all` is the load-bearing detail; default `--state open` returns 0 for merged repos and silently produces "no PR" everywhere.

## Next 3 priorities (actionable)

1. **(user)** Run `cafe_straight_v0` sim with `include_run_metrics:=true` → capture `runs/cafe-001.json` (TODO `358c5d39`). First quantitative number.
2. **(claude)** [infra] STATE.md template: surface "claude-actionable next" separately from "user-blocked next" so the bottleneck line stops being misread as a claude-pick. ~10 LOC prompt edit, P3 doc-only, useful immediately.
3. **(claude)** [stage-2] Verify `@claude` mention + claude_dev workflows end-to-end on a test issue (TODO `357c5d39…81c6`). Independent from sim run; promotable to Today next cycle.

## Cycles to date

- 이번 주 (Mon 2026-05-04 시작): **8** (5-phase 루프 cycle 1–8)
- 프로젝트 통합: **8**

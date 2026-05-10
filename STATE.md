# Research State — auto-generated each cycle

_Last updated: 2026-05-10 18:00 KST · cycle p0-state-template-split-next-priorities_

## North star distance

Still **0 measured numbers**. PRs #7/#8/#9 merged days ago; PR #10 (aggregate-results PR-status surface), PR #11 (decision-tree feasibility filter), and PR #12 (this cycle, STATE template split) all open. The 1-shot user sim remains the gating action — `ros2 launch … jackal_cafe.launch.py include_run_metrics:=true run_id:=cafe-001` produces `runs/cafe-001.json`, the first quantitative datum. All claude-side blockers cleared.

## Current bottleneck

**User-owned sim run for `runs/cafe-001.json`** — TODO `358c5d39` (Today, Owner=user, NeedsUserTest=true, P0). Until it lands, calibration of `docs/path_tracking_metrics.md` against measured baselines (TODO `357c5d39…81f1`) stays gated. No claude-side TODO directly produces this datum; claude-cycles compound on infra/process improvements meanwhile.

## Open experiments

| branch | last update | last description | days open |
|---|---|---|---|
| `autoresearch/p0-aggregate-results-pr-merge-status` | 2026-05-10 16:05 | qual:script-syntax-ok | 0 (PR #10 open) |
| `autoresearch/p0-prompt-pr-dep-fallback-decision-tree` | 2026-05-10 17:03 | qual:doc-only | 0 (PR #11 open) |
| `autoresearch/p0-state-template-split-next-priorities` | 2026-05-10 18:08 | qual:doc-only | 0 (PR #12 open) |

## Recent learnings (last 3 cycles)

- **(이번 cycle)** Single fix-up commits (`a0a3420`-style) are cheaper to remove via template change than to catch in PLAN_NEXT 5a every cycle — the structural fix lasts forever, the per-cycle catch costs budget every hour.
- **(cycle p0-prompt-pr-dep-fallback-decision-tree)** Decision tree step 2 was strict-match wording but used as a top-down walk; encoding the walk + PR-dep filter removes drift, makes rationale paragraphs auditable.
- **(cycle p0-aggregate-results-pr-merge-status)** STATE rewrite each cycle is load-bearing — REVIEW recomputing the bottleneck against fresh state matters more than trusting prior STATE prose.

## Next claude-actionable (this cycle would pick from here)

1. **`357c5d39…819a`** Add per-class result reporting contract to `scripts/aggregate_results.sh` (no single-mean aggregation) — Backlog, P3, Phase=P5. Pre-positions infra for taxonomy v0 §4 promise; pure Bash/Python extension to existing aggregator, doable cold without sim data.
2. **(author new)** Housekeeping pass: once PRs #10/#11/#12 merge to main, update STATE template wording in next cycle's STATE.md to use the new sections — and confirm 5a's Owner-mismatch check fires correctly on the first cycle that exercises it.

## Next user-blocked (waiting on user action — surfaces in Telegram queue, not for PLAN)

1. **`358c5d39`** Run `cafe_straight_v0` sim with `include_run_metrics:=true` → capture `runs/cafe-001.json` (first quantitative baseline). Owner=user, NeedsUserTest=true, P0. Single mover toward north-star quantitative gate.
2. **(implicit)** Merge open PR cluster (#10 aggregate-results-pr-status, #11 decision-tree feasibility, #12 STATE template split) — all doc/script-only, low-risk, but each adds ~30 min latency before next cycle inherits the change.

## Cycles to date

- 이번 주 (Mon 2026-05-04 시작): **9** (5-phase 루프 cycle 1–9)
- 프로젝트 통합: **9**

# PR-dependency feasibility filter in PLAN decision tree

- **Cycle**: 2026-05-10 17:00 KST
- **Branch**: `autoresearch/p0-prompt-pr-dep-fallback-decision-tree`
- **TODO**: `357c5d39` [infra] auto_research.md: encode PR-dependency fallback in decision tree
- **Phase**: P0
- **Status**: keep

## What I tried
- Edited `scripts/prompts/auto_research.md` PLAN decision tree step 2: replaced single-pick wording with a top-down walk over the priority-ranked Today (claude) list, applying an explicit feasibility filter for "code lives only on an unmerged `autoresearch/*` branch".
- Added an inline "Owner=user is already excluded" reminder to short-circuit the recurring temptation to pick the user-owned P0 sim TODO when nothing else looks aligned.
- Step 3 (Backlog promotion) inherits the same feasibility rule. Net diff +5/-2 lines.

## What worked / what failed
- Edit kept step numbering intact, so the existing `step (4)` reference at line 107 of the same file still resolves correctly — no cascading edits needed.
- TSV row + RESULTS regen + push + PR open all clean. Decision-tree dogfood: this very cycle hit the case the new rule covers (top P0 picks all Owner=user ⇒ fall through to lower-priority claude item), and proceeded to EXECUTE without needing the `EXECUTOR_SKIP` path.
- Did not re-test PLAN behavior end-to-end — the dogfood is the next cycle's rationale paragraph, which is the natural place this lands.

## North-star delta
- 0 measured numbers — pure prompt/process change.
- Reduces a recurring source of cycle waste (stale-bottleneck → silent skip vs. drop-to-next-priority drift). Compounds across the remaining 6-month horizon at ~1 averted skip/week.

## Key learnings
- The prompt's decision tree was strict-match: step 2 said "the top one", with no explicit walk semantics. Empirically, three cycles already used "drop to next" — codifying it removes ambiguity and makes the executor's reasoning auditable in the journal rationale.
- "Owner=user is excluded by the `Owner=claude` filter" is worth stating in-line because the cycle-by-cycle pull to pick the user's blocking item is real (PRs merged → user TODO bubbles to top → executor wants to satisfy bottleneck).

## Recommended next 1–3 priorities
1. **(user)** Run `cafe_straight_v0` sim → `runs/cafe-001.json` (TODO `358c5d39`). Still the single bottleneck for first quantitative number; nothing claude-side moves it.
2. **(claude)** [infra] STATE.md template: surface "claude-actionable next" separately from "user-blocked next" so the bottleneck line stops being misread as a claude-pick. ~10 LOC prompt edit, P3.
3. **(claude)** [stage-2] Verify `@claude` mention + claude_dev workflows end-to-end on a test issue (TODO `357c5d39…81c6`, currently Backlog/Today claude). Independent from sim run; promotable.

## Artifacts
- PR: https://github.com/Geonhee-LEE/Representation-Aware-MPPI/pull/11
- Files touched: `scripts/prompts/auto_research.md`, `results/p0-prompt-pr-dep-fallback-decision-tree.tsv`, `RESULTS.md`
- TSV row appended: yes

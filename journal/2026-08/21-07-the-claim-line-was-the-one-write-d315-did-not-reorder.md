# The claim line was the one write D-315 did not re-order

- **Cycle**: 2026-08-21 07:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: authored this cycle (decision tree step 4) — "4a claim-line ordering contradicts D-315"
- **Phase**: P5
- **Status**: keep

## What I tried

- Planned STATE next-action #1 (execute Q-176's (b): `float → None` on the three
  LOAD_BEARING accessors). Sized it before committing: **30 reference sites
  across 3 files**, and the change adds two raw accessors to `tail_mean.py`.
- **Cut it at the `elapsed` reading, not at minute 34** (D-181). `SUITE_AFFORDABLE`
  gave a suite-start deadline of 8m37; the census interaction below made a clean
  first suite improbable inside that window.
- Fixed instead the defect the 06:00 cycle named and flagged "Worth a D-NNN":
  4a told cycles to update the `TSV row appended:` claim line "after the TSV
  append (**the last write before push**)" — which under D-315 is a write *after*
  the receipt, i.e. a guaranteed `STALE` refusal.
- Two edits to `scripts/prompts/auto_research.md`: the 4a window is now "after
  the TSV append and **before the commit**", and the D-315 order line names the
  claim-line as its own step.

## What worked / what failed

- **The reason for cutting Q-176(b) is specific, not vague budget fear.** Adding
  `second_ratio_raw` / `second_baseline_ratio_raw` shifts `scene_scoped_claims()`
  and `citation_sites()` — the derived-census `+1` shape that has gone RED on
  the *first* suite for **8 consecutive cycles**. A red suite costs 22 min and
  produces nothing pushable; there was no second suite in this budget.
- **Checked the recursion risk rather than assuming it.** `full_screen()` — which
  `ungradeable_scenes()` and hence `scene_mark()` derive from — does not call
  `second_ratio`, so the `None` gate is safe to write when the change is next
  attempted. That is a real result for the next cycle, not a guess.
- **The prompt file is inside the test surface, and I found out before the suite.**
  `test_local_only_audit.py` and `guard_witness.py` both read
  `scripts/prompts/auto_research.md`. Ran those two files first (2.5 s, 39
  passed) — the D-390/D-396 "guard reads prose" shape would have surfaced there
  22 minutes cheaper than in the receipt suite.
- `census_preempt` clean on all 5 censuses before staging.

## North-star delta

- **Zero. Thirtieth consecutive cycle with no planner movement.** 0 rollouts, no
  controller, representation or dynamics code touched. This is process repair.
- The one honest defence: the repair removes a *recurring, guaranteed* tax —
  every cycle following 4a literally loses a suite — rather than a one-off.
- The gap that actually matters is unchanged: PRs #66–#69 unmerged for **41
  days**, and the branch has spent ~30 cycles on census/guard machinery.

## Key learnings

- **A constitution can contradict itself across sections, and the older section
  wins by being local.** D-315 re-ordered every write it enumerated; 4a's
  claim-line lived in a different section and kept its pre-D-315 wording. The
  cycle that follows the nearest instruction is behaving correctly and still
  loses. Cross-references, not just correct rules.
- **D-162's property is what makes the fix free**, and it was already written
  one section below: `claim` counts a row whether or not it is committed. The
  fix needed no new mechanism — only for the two statements to be read together.
- **Size a change against the guard population, not the line count.** Q-176(b)
  is ~10 edits and looks small; what makes it a full-budget task is that it
  moves two derived censuses.

## Recommended next 1–3 priorities

1. **Execute Q-176's (b) with a full EXECUTE budget** — start it at cycle open,
   not after a REVIEW. Expect to re-pin `scene_scoped_claims()` /
   `citation_sites()` literals in the same commit; budget for the census `+1`.
   Recursion already cleared: `full_screen()` does not reach `second_ratio`.
2. **The 41-day merge stall is now the dominant project risk** — D-140 keeps the
   executor moving on PR #67, but nothing has reached `main` since 2026-07-12.
   Escalation window opens 2026-08-22 04:07.
3. Consider whether the ~22-min receipt suite is affordable at all at a 35-min
   budget — it is 64% of the cycle and is what forced this cycle's scope cut.

## Artifacts
- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic)
- Files touched: scripts/prompts/auto_research.md, docs/decisions.md, journal/2026-08/21-07-*.md, results/p3-epistemic-shadow-cost-critic.tsv
- TSV row appended: yes

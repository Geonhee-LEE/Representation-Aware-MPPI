# The writable window is for prose, not for code

- **Cycle**: 2026-08-22 06:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: STATE #1 `strand-clear` — one suite on `76b4fee`, then push
- **Phase**: P3
- **Status**: in_progress — **suite RED, push refused, strand not cleared**

## What I tried

- Phase 1 Step 0 fired: `cycle_artifacts stranded` named the 05:00 journal and
  **2 commits** (`76b4fee`, `29fc5e1`) that never reached `origin`. Per D-112
  that outranks the decision tree, so this cycle's pick was the strand itself —
  decision-tree step 1 (resume in-flight), not a new thrust.
- Took all three entry readings before touching anything. `push_preflight probe`
  returned `OTHER_TREE` (the green receipt grades `0559b8e9`, not `29fc5e17`),
  so the suite was genuinely owed and D-315's shortcut was unavailable.
- Started the suite as the first EXECUTE action, then wrote this report **inside
  its window** per D-414.
- Confirmed gate 1 passes without a deadlock-breaker: the queue is at **6/6**,
  but this branch already carries **OPEN PR #67**, so continuing on it adds no
  review bandwidth (D-140). No new branch, no new PR.

## What worked / what failed

- **The strand did NOT clear — the suite came back RED and the gate refused.**
  `4040 passed, 5 failed` in 1421 s. This is the honest headline and it inverts
  the plan: the strand is now **3 commits**, not 2. The bookkeeping half was
  clean (`claim` → `DISCHARGE_PUSH`, `tsv_timestamp check` → `NO_PENDING_ROW`),
  so 05:00's row and journal were already honest; what was **not** clean was
  05:00's own code, and nothing before this suite had graded it.
- **All four census failures are one root cause, already named and skipped.**
  05:00 added `source_reach.vocabulary_gap`, whose `set(...) & VOCABULARY`
  enrolled it in the guard population — and four pins across four modules never
  moved with it:
  - `test_guard_reflexivity::test_and_shaped_guards_are_exactly_these_four` —
    extra item `source_reach.vocabulary_gap`
  - `test_guard_direction::test_the_exclusion_is_not_special_cased…` — `19 != 18`
  - `test_exemption_control::…gives_the_four_unwatched_lists_a_control…` — subset
    assertion, missing `CARRIED_FIELDS` / `EXCLUDED_TESTS` / `NAME_SCOPE_CLAIMS`
  - `test_exemption_masking::test_module_global_route_covers_the_rest` — `27 != 26`
  `census_preempt` returned **CLEAN on all 5 it covers** and printed the gap in
  its own `UNCOVERED` line: `exemption_control.REGISTRIES`,
  `extremum_reading.SITE_CLASSES`. 05:00 repaired the two censuses that tool
  watches and the four it does not are exactly what went red — **D-318 for the
  second time, in the direction D-318 warned about.** The guard *tally* pin
  (138) is watched and passed; the guard *membership* pin is not watched and
  failed. A count matching is not a set matching.
- **The fifth failure is unrelated and may be state-coupled**:
  `test_receipt_store::test_cli_recall_reports_miss_then_hit` — `rs._main(['recall'])`
  returned 1 where 0 was expected. This run archived a receipt
  (`results/receipts/9a0f574e685a1e10.json`) *while the suite was running*, so a
  "miss-then-hit" CLI test plausibly saw a pre-existing hit. Next cycle should
  confirm before assuming it is a real defect — it is the one failure not
  explained by the guard-population story.
- **D-414's window has an edge, and I nearly walked over it.** The window is
  writable because `record` stamps *after* the run — but the suite's assertions
  ran against the tree as it stood at **launch**. Prose landing mid-run is
  therefore covered honestly (no test reads it for truth); *code* landing
  mid-run would be graded green by a suite that never executed it. STATE #2
  `register-scene-transfer` was the obvious thing to slot into the idle 22
  minutes, and doing so would have shipped an unrun registry change under a
  green receipt (**D-418**).
- **`cycle_wallclock review` was right and was actionable for once.** It graded
  05:00 as `OVERRUN` — 24m08, long enough for a receipt, still no publish — and
  told me the failure mode ahead was post-suite budget, not pre-suite. Cutting
  scope to strand-clear-only came from that sentence.

## North-star delta

- **Negative: no controller moved, zero rollouts, and nothing shipped.** The
  strand grew from 2 commits to 3. The one thing bought was the **reading** —
  05:00's work is now graded, and the four failing pins are named with their
  exact assertion deltas, so the repair is mechanical rather than exploratory.
- No coverage number changed. This cycle deliberately did not re-derive the
  bottleneck sentence; STATE's own instruction says not to until
  `scene_transfer` is registered, and that is still ahead.

## Key learnings

- **A strand is cheap to repay and expensive to re-earn.** 05:00 left one
  correctly by D-181's rule; the cost was one suite. What makes strands
  dangerous is stacking — each unpushed cycle adds a journal the next one must
  also carry, and `stranded` only names the pile, never shrinks it.
- **"The window is writable" and "the window is free" are different claims.**
  D-414 established the first. Reading it as the second is the trap, and the
  trap is invisible because the receipt comes back green either way.
- **A clean `census_preempt` is not a clean tree, and its `UNCOVERED` line is
  the part that matters.** It printed exactly the four censuses that then went
  red. I read that line, quoted it in the pre-commit output, and still treated
  `5 censuses re-derived, all clean` as the verdict. The tool is honest about
  its own scope; the failure is that its scope is narrower than the thing it
  looks like it measures — D-317's lesson, unlearned.
- **Gate 1 at cap is not a stop when the branch is already open.** D-140 turned
  what would have been a `pr-queue-full` skip into a normal cycle. The queue has
  now been stalled **41 days**; D-140 is the only reason work continues at all.

## Recommended next 1–3 priorities

1. **`pin-repair-then-push` — the only pick.** Four pins, deltas already known
   (see above), then **one** suite, then push. Do not diagnose again; the log is
   at `/tmp/suite-receipt.json.log` and the deltas are quoted here. Start the
   suite before 8m00 or it will not fit. Confirm the `receipt_store` failure is
   real or state-coupled before touching it.
2. **Widen `census_preempt` to the guard *membership* pin** — it watches the
   tally (138) and missed the set, which is the whole failure. Its `UNCOVERED`
   line is doing its job and being read as decoration; either the four
   uncovered censuses get covered or D-318 will land a third time.
3. **`register-scene-transfer`** — unchanged and still next once the branch is
   green; do not start it on a red tree.

## Artifacts

- PR: #67 (open) — **nothing pushed**; strand now `76b4fee`, `29fc5e1`, `2c5dbc2` + this correction
- Receipt: `results/receipts/9a0f574e685a1e10.json` — RED, 4040/5/164, 1421 s
- Suite log (keep for next cycle): `/tmp/suite-receipt.json.log`
- Files touched: `journal/2026-08/22-06-*.md`, `docs/decisions.md`, `results/p3-epistemic-shadow-cost-critic.tsv`
- TSV row appended: yes

# The 9th scene is half-harvested — and the repair cascaded one more layer

- **Cycle**: 2026-08-24 19:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: strand-clearing (STATE next-action #1) — fix the 8 reds, one receipt, push
- **Phase**: P3
- **Status**: keep

## What I tried

- Scope-cut to exactly one thing: the 8 reds D-458 left, then **one** receipt, then push.
  No new scenes, no new columns, no Q-198 work. The branch has been unpushed for three
  consecutive cycles and a fourth strand was the failure to avoid.
- Reproduced the 8 narrowly first: they run in **0.16 s**, all static-census, no rollouts.
  That reading is what made the scope-cut affordable to decide.
- Fixed the join (`spread_generality.measure()`), the set-difference assertion
  (`test_excursion_tracking`), and D-458's own Status line wording.

## What worked / what failed

- **The 8 reds were 2 root causes, not 8.** Six of them were a single `KeyError`:
  `cafe_obstacle_contested_v0` carries a *measured* clearance column (8 arms,
  0.4323–0.7314 m) but **no** cross-track column, so the census that joins the two
  had nothing to join. The 9th scene is **half-harvested** — one operand on disk,
  one operand still the pinned debt of D-458(2).
- **The repair cascaded again — but `census_preempt` caught it in 2 s.** Renaming the
  test drifted `loop_reach.READING` (1 unrecorded + 1 retired). D-458 found this class
  of thing via a **20-minute red suite**; the D-318 placement of `census_preempt` right
  before the commit found the same class **before** the suite. First dividend that
  placement has paid.
- **`retirement_reach` caught a real ambiguity, not a false positive.** D-458's Status
  line read `accepted (… 철회한다 …)` where the verb's subject was an internal claim,
  not the entry. I fixed the wording rather than the gate — the line a grep-arriving
  reader uses to judge liveness was genuinely ambiguous.
- **My own first reword failed the same gate**, because it still contained `은퇴` and
  `retirer` (both matched `RETIREMENT_VERBS`, the latter by substring on `retire`).
  Caught in 0.15 s on the re-run.
- **Failed / cut**: a broad `-m "not slow"` pre-sweep to hunt further cascades hit a
  400 s timeout and bought nothing. That is ~7 min I spent on the D-458 lesson
  ("the red list is a subset") and did not get an answer from.

## North-star delta

- **No measured physical quantity moved. Zero.** Every edit this cycle was census /
  verification plumbing. Honest accounting: this cycle bought the *ability to publish*
  three cycles of stranded work, not any avoidance or tracking capability.
- The 9th scene remains `VACUOUS_PASS`: placed in the matrix, grading nothing. The
  "다중 obstacle" class is still represented-but-untested in the only sense that counts.
- Q-198 (re-author `contested_v0` vs buy its ~80 rollouts) is untouched and still blocking.

## Key learnings

- **A "free" static re-pin has a two-layer tail, not one.** D-458 found layer 1 (join
  censuses). Layer 2 is that *fixing* the join moves a test name, and test names are
  themselves a pinned population. Each layer was found by a cheaper instrument than the
  last (20 min suite → 2 s census). That is the direction to keep pushing.
- **Half-harvested is a new scene state.** Until now a scene either had its columns or
  had none. A scene can now hold one operand and owe the other, which is invisible to
  any census reading a single column and only shows up in a *join*. Joins are where
  partial harvests surface.
- **A one-mechanism claim survives until a scene splits it.** Same shape as D-458's
  excite finding, twice in two cycles. Worth suspecting every remaining
  "the reason is X" assertion in the census layer of being a one-sample generalisation.
- **Budget**: `SUITE_UNAFFORDABLE` fired at 6m34 and I started the suite anyway, because
  the alternative was a 4th strand. Correct call here, but it means the wall-clock
  advisory and "clear the strand" can directly conflict — worth naming rather than
  quietly overrunning each time.

## Recommended next 1–3 priorities

1. **Answer Q-198 before spending any rollouts.** Move `contested_v0`'s obstacle lane to
   ~0.3 m of the path (a 1-line yaml edit) so the ~80 rollouts buy a scene that actually
   asks a question. Do not buy the columns for the scene as currently authored.
2. **Sweep the census layer for other joins.** `spread_generality` was the only join that
   broke, but nothing has enumerated how many census readers are joins vs single-column.
   A half-harvested scene is only visible to the former.
3. **Do not add a 10th scene until (1) is resolved** — the cascade cost per scene is now
   measured at two layers and is not yet bounded.

## Artifacts

- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic)
- Files touched: `eval/mppi_sandbox/spread_generality.py`, `eval/mppi_sandbox/loop_reach.py`, `eval/mppi_sandbox/tests/test_spread_generality.py`, `eval/mppi_sandbox/tests/test_excursion_tracking.py`, `docs/decisions.md`
- TSV row appended: pending

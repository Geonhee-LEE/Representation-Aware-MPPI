# The completion clause reads arrival — and the grid says it changes nothing

- **Cycle**: 2026-08-14 08:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: `STATE-q146` Resolve the `admissible` clause-2 scope bug (`n_reached` → `n_arrived`)
- **Phase**: P3
- **Status**: keep

## What I tried

- Q-146's next action, literally: point `admissible`'s completion clause at
  `n_arrived` instead of `n_reached`, then re-read D-250's grid to see whether
  the verdict moves.
- Stated the clause **once** as `freeze_weight.completes` and pointed both
  callers at it. The second caller is `verdict`'s `NO_FREEZE_TO_PRICE` baseline
  check, which applies the same "did every run finish" question — fixing only
  `admissible` would have left the cheapest verdict on the old predicate.
- Re-ran the full grid (10 weights × 12 seeds, `lam = 0.8`, arrival scope) on the
  **unfixed** code to get a before-reading, then computed the after-verdict off
  the same cells rather than paying a second 9-minute sweep.

## What worked / what failed

- **Q-146's prediction is refuted, and the refutation is the finding.** It
  expected `1e5`/`3e5`/`1e6` to move because they are censored. They do not move:
  those cells carry `exceed before` 1/12, 11/12, 12/12 and so fail **clause 1**
  before completion is consulted. No cell changes admissibility; the verdict
  stays `NO_FREEZE_TO_PRICE` at every rung of the eps ladder.
- **The mechanism is a fallback I had to be corrected on by the measurement.** I
  first wrote — in the new docstring — that a never-arriving cell gets a vacuous
  `n_exceed_in(before) == 0` because the arrival window is empty. That is wrong.
  `freeze_duration_before` *defines* `arrival = None` as `before == whole`, so
  such a run is scored on its whole trajectory, which on this scene is large.
  The two clauses are **correlated on this grid, not independent** — which is
  precisely why a wrong predicate survived four cycles of arrival-scope work.
- **The residual is real but off-grid.** The cell only completion can convict is
  one that *never stalls and never arrives*: smooth to the goal's xy, finishing
  at the wrong heading. Clause 1 sees no stall, clause 3 no clearance loss, and
  `n_reached` called it complete. Pinned as a test; it is not on this grid, so
  this is a latent-correctness fix, not a result.
- Test fixtures encoded the old predicate: `cell()` defaulted `arrival` to
  all-`None`, so 10 synthetic tests went inadmissible for a reason they are not
  about. Fixed at the helper, with non-completion now stated explicitly.

## North-star delta

- **No movement on the planner question.** The standing D-250/D-253 claim —
  `ProgressPriceCritic` has no supported cell at any tested weight — is
  unchanged, and is now known to be robust to the completion predicate.
- One correctness defect closed on the path the P3 freeze verdicts are read
  through, with the cell it protects against named and pinned.
- Grid re-measured at n=12: the ablation arrives 12/12 with `exceed before` 0/12,
  which is what `NO_FREEZE_TO_PRICE` rests on.

## Key learnings

- **A predicate fix whose verdict does not move is still worth measuring — the
  reason it does not move is the content.** Had I shipped it on the strength of
  the argument alone, I would have shipped the vacuity story, which is false.
- **Correlated guards hide wrong predicates.** Clause 1 was silently doing
  clause 2's job on every cell that could have exposed the bug. Worth asking of
  the other multi-clause verdicts on this branch whether any clause has ever been
  the binding one.
- The `cell()` helper's default is a reminder that fixtures carry the old
  semantics: changing a predicate re-grades every synthetic cell built before it.

## Recommended next 1–3 priorities

1. The planner question proper — the first cycle in four with no publication or
   correctness debt in front of it.
2. Q-147 (per-run cross-metric invariant), now with `arrival_scope_census` as the
   census that says which invariants are true.
3. Q-146's part (a): count what re-baselining `ab.reached_goal` onto pose would
   cost, now that (b) is landed and measured.

## Artifacts

- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic)
- Files touched: `eval/mppi_sandbox/freeze_weight.py`, `eval/mppi_sandbox/tests/test_freeze_weight.py`, `docs/decisions.md`, `docs/deliberations.md`
- TSV row appended: pending

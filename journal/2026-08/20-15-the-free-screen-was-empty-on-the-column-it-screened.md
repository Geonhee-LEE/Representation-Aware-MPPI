# The free screen was empty on the column it was aimed at

- **Cycle**: 2026-08-20 15:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: STATE next-actionable #1 + #2 (screen the six for excitation; audit `clearance` for degeneracy)
- **Phase**: P3
- **Status**: keep

## What I tried

- Took STATE's next-action #1 literally and built the screen it priced at zero
  rollouts: `distinct_arms` over every `(column, scene)` cell with a pinned
  per-seed ensemble, plus the gap between that set and the scenario registry.
- Folded next-action #2 into the same predicate rather than a module of its own
  — "is the `clearance` column degenerate anywhere" is D-385's question one
  column over, and the answer is only interesting beside the cross-track one.
- Pinned `SCREEN_VERDICT` against the misreading the result invites, and added a
  drift check tying the screen to `second_verdict()` so the two cannot disagree.

## What worked / what failed

- **The screen ran, and next-action #1 as written cannot be executed.** Its
  premise ("free wherever a `cte_max` ensemble is already pinned") is true; the
  conjunction is empty. `excursion_seed_width.SEED_ENSEMBLE` holds exactly the
  two scenes already harvested, so all **6** scenes the screen was aimed at are
  unpinned in precisely the column it needed. The free step does not exist — the
  cost is `REMAINING_DEBT` = **384** rollouts, unchanged, under a new name.
- **Next-action #2 came back clean, at zero rollouts.** All **5** pinned
  `clearance` cells sit at **6/8** distinct arm rows, well over
  `MIN_DISTINCT_ARMS` = 3. D-385's blind spot does not repeat one column over.
- **The only degenerate pinned cell in the repo is the one D-385 already found**
  (`cte_max`/`city_curved_v0`, 2/8). The screen now says that independently of
  `second_verdict()`, and `drift()` fails if they ever diverge.
- **`census_preempt` earned its 2 s for the third cycle running**: +3 guards
  against a pin of 130, caught pre-commit. Repaired to 133.

## North-star delta

- **Zero direct movement** — no cost term, channel or scenario metric moved.
  This is measurement about the measurement surface, and it is the fifteenth
  consecutive cycle with no north-star delta.
- What it does buy is honest: the next harvest is now **priced** (384 rollouts,
  6 scenes) instead of mis-priced at zero, and one of the two STATE actions is
  closed rather than carried.

## Key learnings

- **"Free wherever X is pinned" is a claim about a conjunction, and the
  conjunction was never checked.** The premise and the target set were each
  correct in isolation; their intersection is empty. Three cycles of STATE prose
  carried this forward because the sentence reads true.
- **A cell being unmeasured and a cell being degenerate must not print the
  same.** `city_curved_v0` is degenerate (2/8, harvested); the other six are
  simply absent. Collapsing them would turn "we have not looked" into "there is
  nothing there" — the same `UNTESTABLE`/`REFUTED` distinction D-385 paid for,
  one level up.
- **Cross-column inference has a population of one.** Only `cafe_convoy_v0`
  carries both columns, and it agrees. One agreeing case with no disagreeing
  case it could have had is not evidence; the five excited clearance cells order
  which scene to harvest next and license nothing about grading one without the
  harvest.
- **`tail_mean.drift` entered the guard registry by gaining one `-`.** It was
  already an auditor using `set(A) != set(B)`; swapping in a set difference —
  which names the offenders rather than reporting that a difference exists —
  moved it in. That sharpens what the pool keys on better than the two
  purpose-built entrants did.

## Recommended next 1–3 priorities

1. **Buy one cross-track harvest, chosen by the clearance ordering** — 64
   rollouts on one excited-in-clearance scene (`cafe_head_on_v0` or
   `cafe_obstacle_crossing_v0`), not the full 384. One gradeable second endpoint
   is all D-372's fork needs.
2. **Report the tail per the feed's RS-Diffuser rider** — mean / median /
   `TVaR₀.₉` in adjacent columns plus a separate violation tally, with a paired
   error bar, whenever the second endpoint lands.
3. **PR #67 review/merge** (user) — queue at cap 6, 40 days since a merge.

## Artifacts
- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic)
- Files touched: eval/mppi_sandbox/tail_mean.py, eval/mppi_sandbox/tests/test_tail_mean.py, eval/mppi_sandbox/tests/test_guard_reflexivity.py, docs/decisions.md
- TSV row appended: pending

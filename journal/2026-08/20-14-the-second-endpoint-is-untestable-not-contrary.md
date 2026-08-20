# The second endpoint is untestable, not contrary — seven of its eight arms are the same run

- **Cycle**: 2026-08-20 14:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: `3c2c5d39` TVaR₀.₉ 를 city_curved_v0 에서도 수확 — 두 번째 endpoint
- **Phase**: P3
- **Status**: keep

## What I tried

- Harvested TVaR on `city_curved_v0` (64 rollouts) to decide D-372's
  column-vs-scene question, reading the G5 window (`q ∈ {0.88, 0.90, 0.92}`) off
  the **same** runs rather than re-simulating per threshold — 118 s for all
  three instead of 354 s.
- Added `TVAR_ENSEMBLE_SECOND` / `THRESHOLD_STABILITY_SECOND` additively, leaving
  the single-scene API the existing 13 tests pin completely untouched.
- Added the precondition the branch has assumed everywhere and never checked:
  `distinct_arms()` / `excited()` / `MIN_DISTINCT_ARMS`, plus `column_licensed()`
  and `second_verdict()`.

## What worked / what failed

- **The harvest answered the question by refusing it.** On `city_curved_v0`
  seven of eight arms are **bit-identical** across all 8 seeds — `distinct_arms`
  = 2 of 8. Only `essps_mppi` moves, the one arm whose operating point differs
  by construction (`w_voo`).
- TVaR reads `0.07x` there (adversarial `0.06x`) against `cte_max`'s `0.35x`.
  Both are well-formed numbers computed over a population of **two** wearing the
  shape of a population of eight. That is the trap: no ratio on the cell shows
  the defect.
- **The degeneracy is the scene's, not this observable's.** The identical
  seven-way tie is already present in `excursion_seed_width.SEED_ENSEMBLE` —
  data pinned before `tail_mean` existed. It sat unread while three cycles
  treated the `0.35x` as a *miss*.
- 21 tests pass (13 pre-existing + 8 new). `census_preempt` clean before and
  after; no pin moved this cycle.

## North-star delta

- **No new controller result, and one retracted in scope**: the branch still
  licenses `cafe_convoy_v0` only. `column_licensed()` returns `False` — and it
  is `False` *for want of evidence*, which `second_verdict()` keeps distinct
  from `REFUTED`.
- **+1 real guard on a live failure mode**: a between-arm claim is now gated on
  the arms actually differing. Every floor reading on this branch has assumed
  that precondition; none checked it.
- 물체회피 unmoved. This cycle bought scope honesty, not capability.

## Key learnings

- **A cell whose arms do not separate cannot miss its floor.** Three cycles read
  `city_curved_v0`'s `0.35x` as a narrow-vs-wide miss and reasoned about *why*
  the column was hard to grade there. The right reading is that there was
  nothing to grade, and it was visible in already-pinned data for free.
- **`UNTESTABLE` and `REFUTED` must not collapse.** Recorded as a refutation,
  this harvest would stand as evidence *against* finding #1 forever, when it is
  evidence about the scene. The distinction cost one function and one test.
- **The open work changed shape.** It is no longer "harvest the second endpoint"
  but *find* one — a scene exciting ≥ 3 arms. That check is free wherever a
  `cte_max` ensemble is already pinned, and expensive (118 s) where it is not.
- D-372 survives intact but is now underdetermined: the column-vs-scene question
  has had exactly one gradeable cell put to it.

## Recommended next 1–3 priorities

1. **Screen the six unharvested scenarios for arm excitation** before spending
   any more 118 s harvests — cheap where `cte_max` ensembles exist.
2. **Re-ask D-372's column question on a scene that passes `excited()`** — the
   original TODO's intent, now with a precondition attached.
3. **Audit whether other branch columns rest on degenerate cells** — the same
   blind spot may sit under `clearance`.

## Artifacts

- PR: #67 (already open — D-140: continuing on an open PR adds nothing to the queue)
- Files touched: `eval/mppi_sandbox/tail_mean.py`, `eval/mppi_sandbox/tests/test_tail_mean.py`, `docs/decisions.md`, `results/p3-epistemic-shadow-cost-critic.tsv`
- TSV row appended: yes

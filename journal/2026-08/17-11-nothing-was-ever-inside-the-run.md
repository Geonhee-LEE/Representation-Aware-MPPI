# The other interior field was never about the run

- **Cycle**: 2026-08-17 11:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: `3bec5d39-a41c` [sandbox] Give `interior_inadmissible_k` the D-320 treatment
- **Phase**: P3
- **Status**: keep

## What I tried

- STATE's bottleneck, stated verbatim: one payload answers "what is inside the
  run" two ways — D-320 made `interior_membership_by_k` return `None` under
  `K_INTERIOR_NOT_A_RUN`, and `interior_inadmissible_k` stayed a plain tuple
  built as `k != max(ks)`.
- Measured the field before repairing it (D-186) across all four measured
  grids rather than reading its definition.
- Scoped it to the run's own block, refused it under `K_INTERIOR_NOT_A_RUN`,
  and gave D-307's finding its own name (`run_punctures`).
- Published `unanimity_implies_span_admissible` as a per-column **measurement**
  so the emptiness below is not a silent assumption.

## What worked / what failed

- **The measurement moved the deliverable.** The disagreement was not about
  refusing, it was about what "interior" *names*. The old spelling was the
  walked axis minus its top column — one-sided, run-blind. On the **default
  grid**, the one every reading in this branch uses, it published `(192,)`
  while the run is `(96, 128, 160)`: `192` is above the whole run and above
  `above_k = 176` besides. It was in the tuple only because it is not `512`.
  STATE framed this as a punctured-grid problem; it was wrong on the grid the
  branch actually walks.
- **Scoped correctly, the field is empty by construction.** `span_admissible`
  is `span <= band_width_ratio(k)`; a unanimous column has every seed inside
  `[0.05K, 0.5K]`, which bounds its span by exactly that ratio. So unanimity
  *implies* span admissibility, and since a run's interior is a subset of the
  run, no member of it can be inadmissible. Nothing was ever in this field that
  belonged in it — every column it ever published was outside the run.
- **D-304's "two fields move with the ensemble" is now one.** Its second mover
  was `interior_inadmissible_k` going `() → (176,)` on a grid whose run is the
  single column `(160,)`. D-304 said in prose that both movers "are D-303
  restated through the consumer"; the scoping makes that literal.
- **The negative control is unreachable and was measured rather than faked** —
  the same shape D-320 hit one hour ago with `K_INTERIOR_READABLE`. A unanimous
  span-inadmissible column cannot exist while `need` is the column size, and
  `n_required < 16` short-circuits to `K_BRACKET_NO_RUN` before the field is
  built. So the test **derives the old predicate in-line** and asserts it
  disagrees with the new one on ≥ 2 measured grids: the control is that the
  repair bites, not that the flag can come back full.
- **`census_preempt` paid on its third standing run**, ~2 s: `DRIFT`, one new
  population claim unregistered in `READING` — before the suite, not 800 s
  into it. Second consecutive cycle it has caught this class.
- **⚠️ And then the suite went red on the census `census_preempt` prints as
  `UNCOVERED`.** 790 s, `3476 passed / 2 failed`, both in
  `test_extremum_reading.py`: `sweep()["retired"]` named
  `("calibrated_ladder.py", "k_axis_bracket", "max(ks)")` and the class tally
  dropped `EXTREME_IS_THE_QUESTION` 17 → 16. The cause is the **inverse** of
  the usual one — not a site added, a site **deleted**: the `k != max(ks)`
  filter this cycle removed was a registered member, so the registry had an
  entry the source lost. Repair took 3 s once named. `census_preempt`'s
  `UNCOVERED` line lists `extremum_reading.SITE_CLASSES` explicitly, I read it,
  and I read it as a scope note rather than as the specific risk of a commit
  whose whole content is deleting an extremum expression. D-317 paid 785 s for
  a check narrower than it looked; this cycle paid 790 s for the same shape one
  layer over, with the omission printed on screen.
- **Deliberate budget overrun.** The second suite puts this cycle at ~42 min
  against 35. Taken knowingly: the alternative is stranding six files that a
  future cycle must clear, and the 00:00 → 03:00 strand this week cost three
  full cycles to unwind against one suite's worth of overrun here.

## North-star delta

- No movement. Zero sim runs, one scene, one rung, one temperature;
  `transfers_to_ab_scene` still `False` behind PR #68.
- What moved is again the validity of standing claims: a field five decisions
  quoted as "interior" was naming columns outside the run on the default grid.

## Key learnings

- **A consistency repair can find the field was never coherent.** STATE asked
  for D-320's refusal to be carried across. Carrying it required deciding what
  "interior" meant, and that question had no answer the old code implemented.
- **Check the field on the grid the branch actually uses, not the one the
  bottleneck names.** The punctured grid was the *weaker* case: `(128, 176)`
  at least contains one genuinely interior column. The default grid's `(192,)`
  contains none.
- **An emptiness is worth publishing only with the implication that causes
  it.** `interior_inadmissible_k == ()` alone is indistinguishable from a
  filter that is broken; beside `unanimity_implies_span_admissible` it is a
  measurement that goes non-empty the day the band stops bounding the span.

## Recommended next 1–3 priorities

1. Decide whether this branch closes. PR #67 now carries sixteen commits
   spanning a cost critic, a verification surface, and a `K` axis — one
   unreviewable diff, and D-321 is the third consecutive cycle of payload
   hygiene rather than the axis question.
2. Place the 4a `claim` fill beside `tsv_timestamp check` in `CLAUDE.md` — it
   has been missed four cycles running because it lives in memory, not in the
   loop text. Same repair D-199 made for `staged`.
3. Move `aggregate_results.sh` above the receipt in the push block (D-316).

## Artifacts

- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic)
- Files touched: eval/mppi_sandbox/calibrated_ladder.py, eval/mppi_sandbox/loop_reach.py, eval/mppi_sandbox/tests/test_calibrated_ladder.py, docs/decisions.md, results/p3-epistemic-shadow-cost-critic.tsv
- TSV row appended: yes

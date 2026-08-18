# The fragility coordinate is the facing end — the TTC-family reading is refuted

- **Cycle**: 2026-08-18 18:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: STATE #1 — test the TTC-family reading
- **Phase**: P3
- **Status**: in_progress  (receipt RED, 8 pins — push refused, cycle stranded)

## What I tried

- D-346 left a hypothesis: the two cells the doubling deleted were both TTC
  columns, a ratio with a closing-speed denominator is heavy-tailed, and
  `separates` is pure min/max — so more seeds can only hurt them.
- Measured `tail_extension` — how far a column's own extremes move outward
  under the doubling, in units of the eight-seed pooled span — over **every**
  scene × observable × policy, not only the cells that separated, so the
  reading is not the tautology of grading the dead.
- When that refuted the hypothesis, measured the correction it implies:
  `facing_extension`, the same movement restricted to the end of the column
  that faces the gap.

## What worked / what failed

- **The TTC-family reading is refuted.** The heaviest-tailed column is
  `lateralness` (`0.2455`), which is bounded to `[0, 1]` by construction and is
  the one column that *cannot* be heavy-tailed in the sense meant. `min_ttc`
  is second (`0.1725`) and `ttc` fifth (`0.0838`), below `closing_speed`
  (`0.1612`). The TTC coincidence stands as a coincidence.
- **The two-ended reading fails in the mirror image of margin rank.** The
  thinnest cell in the suite — `head_on`/`closing_speed`@first_detection, the
  one that survives — has the **largest** two-ended extension of any cell in
  the ranked table. A fragility coordinate built on it would rank the survivor
  first to die, exactly as margin rank did.
- **The reason both fail is the same, and it names the real coordinate.**
  `separates` compares one end of the column against one end of the pooled
  rest; movement at the other end is invisible to it. The thinnest cell's
  entire `0.1612` extension is on the *away* side — its facing extension is
  `0.0000`, which is why a gap of `+0.0228` survived a doubling.
- **`facing_extension / margin` predicts all five cells.** Ratios `0.00, 1.32,
  1.83, 0.58, 0.00` against a threshold of 1; the two above it are exactly the
  two the doubling deleted. Both terms are eight-seed quantities plus the
  movement of two extremes — neither consults the sixteen-seed verdict, so this
  is a prediction, not a restatement.
- `census_preempt` caught two drifts at the stage (`guard_tally` +2,
  `exemption_registry` +1) in ~2 s. Both repaired before the suite.
- **The receipt came back RED anyway — 8 pins, and every one of them is in the
  gap `census_preempt` names in its own `UNCOVERED` line.** `exemption_control.
  REGISTRIES` and `extremum_reading.SITE_CLASSES` are two of the four it says
  it does not cover, and they account for three of the eight. This is the
  D-334 shape recurring exactly: a census re-derives *populations*, never
  *placements*, and an entrant owes hand-written entries in registries no
  count can find. Diagnosed in 40 s by running the eight node IDs alone
  (vs the 1341 s suite), which is the 08:00 precedent working as intended.
- **The eight, and the repair each needs** — all mechanical, none conceptual:
  `exemption_control` (`TTC_FAMILY` into the controlled set), `exemption_masking`
  (module-global route 23 -> 25), `extremum_reading` ×2 (two `min`/`max` sites
  in `ttc_family_has_the_heavier_tail` unregistered; sweep verdict flips to
  `UNREGISTERED_SITES`), `guard_direction` ×2 (scalar pool 16 -> 18,
  `format_tail_grade` enters `unprobeable_revocable`), `guard_reflexivity` ×2.
- **Push refused, and correctly** (D-082): the gate wants a green receipt on
  this tree and there is not one. No second suite — the cycle was at 33 min
  when the red landed, so repairing and re-measuring would have blown the
  budget for a verdict the next cycle can take in one shot.

## North-star delta

- No planner movement — representation diagnostics, honestly so.
- What moved: the branch now has a **rule for which separation claims are worth
  taking**, computable at one seed count. A cell whose gap-facing extreme has
  room to move is not evidence, whatever its margin. That is the first thing
  this branch has produced that transfers to a claim it has not yet measured.

## Key learnings

- **A one-sided rule needs a one-sided statistic.** Two cycles looked for the
  fragility coordinate in quantities symmetric in the column (margin, tail) and
  both were refuted by the same cell, for the same reason.
- **The refuted control is worth keeping.** `tail_extension` stays in the
  module and is what makes `facing_extension`'s docstring provable rather than
  asserted — the survivor's `0.1612` vs `0.0000` split is the whole argument.
- **`TTC_FAMILY` decided D-340's open class** (D-347): the domain-declaration
  category had one member and no test; the next entrant arrived one cycle later
  and D-340's discriminant classified it without a judgement call.

## Recommended next 1–3 priorities

1. Apply the facing-end rule to the invisible class: `convoy` /
   `obstacle_crossing` are `no_gap_anywhere`, so they have no facing end — ask
   what their *negative* margins would need for a gap to open. Zero rollout.
2. Audit the remaining composite magnitude pins (carried from 11:00, D-342).
3. Give `UNCOVERED` a standing re-derivation (carried from 16:00, D-345).

## Artifacts
- PR: **not pushed** — receipt red, commit `01167a7` is local only
- Files touched: eval/mppi_sandbox/scene_separability.py, eval/mppi_sandbox/tests/test_scene_separability.py, eval/mppi_sandbox/tests/test_guard_reflexivity.py, docs/decisions.md, results/p3-epistemic-shadow-cost-critic.tsv
- TSV row appended: yes (two rows — the finding, then the red receipt)

# The ordering got a control, and the tree was never the variable

- **Cycle**: 2026-08-05 04:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: `STATE-1` Buy one licensed batch through `take_and_record`
- **Phase**: P3
- **Status**: keep

## What I tried

- Took STATE #1 (buy a batch through `take_and_record`) but changed what the
  batch spends its runs on first. `replicated_reading` was buying 2k runs and
  spending all but two on the denominator: the gap came from `(A1, M1)` and the
  other 2(k-1) runs only widened the frames' bands. So the numerator sat at n=1
  while the control got replicated.
- Kept all k gap readings (`ReplicatedReading.replicate_disagreements`) and added
  `ordering_control` — the C(k,2) rank agreements *between replicates of one
  frozen tree*, sharing one denominator. That is the control D-071's surviving
  claim (c) was published without.
- `reading_record` SCHEMA 1 → 2: one cell set per replicate, so the control is
  re-derivable off disk. Added `Record.gap_spread` after the run, when the
  numbers made clear the finding was bigger than the ordering.
- Ran it: `take_and_record(k=3)`, **464 s**, 6 concurrent runs, tree
  `c4b76066d64d` on all six, **licensed**, population **79**, 7 disagreeing.
  First record on disk: `results/readings/2026-08-05-04-ordering-control.json`.

## What worked / what failed

- ✅ **Licensed, and the record is real** — `read()` reproduces every grade,
  ranking and agreement from the file with no run and no retyping. D-073's
  format survived first contact with actual data.
- 🔴 **The ordering does not reproduce against itself.** Three replicate pairs,
  one tree, one batch, one denominator: **rho = +0.571 / +0.857 / +0.714** at
  n=7. D-071's (c) was "the magnitudes did not reproduce but the ordering did",
  read off four trees. The ordering's own noise floor is ~0.71 — so a cross-tree
  rho anywhere in that band is evidence of nothing, and (c) was never measured
  against the only number that could have made it meaningful.
- 🔴 **And the bigger one: the same-tree gap spread exceeds the cross-tree
  spread.** `gap_spread` on one frozen tree: **4.50× / 2.59× / 2.23× / 2.19× /
  1.74× / 1.27× / 1.14×**. D-069's cross-tree ratios were 0.31–1.67 (≤ 3.2× as a
  fold). Same seven sites. **The same-tree spread brackets and exceeds it**, so
  the magnitudes D-069..D-071 watched fail to reproduce across trees fail to
  reproduce across *runs*, and the tree label on that variation was decoration.
  D-069's guard is still correct — a transported reading really is uninterpretable
  — but its *evidence* was run noise.
- 🔴 **D-071's own cited endpoint moved by 6.5×.** `_is_set_valued` was offered
  at **13×**; on this tree its cells are **gap 14 / control 3+4**, i.e. **4.67×**
  under the measured-only denominator every publication actually used.
  `_pure`'s gap is now **326** (142 → 196 → 175 → 214 → 326).
- 🔴 **Two of seven sites now sit below 1.0** — `_shells_out_to_git_diff` 0.47×
  and `_has_git_diff_literal` 0.43× — i.e. their control exceeds their gap. On
  the "2.5× to 13×" reading these were part of a range that started above 2.
- ⚠️ **Q-079 is not cosmetic.** Under the declared both-frames denominator the
  top two are 2.35 / 2.00; under the measured-only denominator every publication
  actually used they are 4.87 / 4.67 — near-tied. Same cells, different story.
- ⚠️ Suite grew 780 → **790** (re-taken after the doc writes per D-043/D-044;
  `verify` and `declared` both clean at `6ede3317`). Two intermediate commit
  messages on this branch quote **788** and **794** — both were counts taken
  before a later write in the same cycle, which is the exact defect D-043 exists
  for; **790** is the number that belongs to the pushed tree.
- ⚠️ 🔴 **The re-take was red on first pass**, and usefully: `citation_audit`
  flagged D-074's `2.00×` as colliding with the registered
  `horizon_weight_swing_cited` magnitude — a different quantity sharing a value
  (D-038's class). Fixed by quoting the record's **cells** (`gap 14 / control
  3+4`) instead of the derivation. D-073's rule turned out to also be a
  collision-avoidance rule.
- ⚠️ The batch cost 464 s and the cycle ran ~85 min, **50 over the 35-min soft
  limit** — two full 6-min suite re-takes plus the batch. Stated, not smoothed.

## North-star delta

- **No avoidance or tracking number moved — forty-second consecutive instrument
  cycle.** Scenes able to contribute an avoidance number: 5, reportable: 4.
- What did move: the first reading on disk, and it retired a claim rather than
  adding one. Four cycles of cross-tree magnitude comparison (D-069..D-072) were
  reading a variance they never controlled for.

## Key learnings

- **A reproduction claim needs a non-reproduction control, and this branch has
  now shipped six instruments that each lacked the one under them.** Stationarity
  needed a frame control (D-067), the frame control needed a tree (D-069), the
  tree needed a replicate (D-071), and the *ordering* needed a same-tree pair —
  which cost zero extra runs, because the batch was already buying them and
  throwing them away.
- **Spending replicates on the denominator only is the specific error.** k runs
  per frame gave C(k,2) control pairs and exactly one gap. The asymmetry was
  documented as deliberate in `replicated_reading`'s docstring and it was the bug.
- **"Did not reproduce across trees" is unfalsifiable without "reproduces across
  runs".** Any future cycle quoting a magnitude difference between two conditions
  must quote `gap_spread` beside it.

## Recommended next 1–3 priorities

1. **Re-read D-069's guard against `gap_spread`.** The guard stands; the argument
   for it does not. Does `single_tree` still earn its place, or is the honest
   statement that *no* single magnitude from this instrument is quotable?
2. **Take a second licensed batch on a second tree** and compare its
   `ordering_control` against the cross-tree `agreement`. Now a two-line call —
   and the first cross-tree rho that means anything.
3. **Q-081**: does any published magnitude on this branch survive its own
   `gap_spread`? A static sweep of `docs/decisions.md`, no run.

## Artifacts

- PR: #67 (open, 68+ cycles)
- Files touched: `eval/mppi_sandbox/exclusion_scope.py`,
  `eval/mppi_sandbox/reading_record.py`,
  `eval/mppi_sandbox/tests/test_reading_record.py`,
  `results/readings/2026-08-05-04-ordering-control.json`,
  `docs/decisions.md`, `docs/deliberations.md`
- TSV row appended: yes

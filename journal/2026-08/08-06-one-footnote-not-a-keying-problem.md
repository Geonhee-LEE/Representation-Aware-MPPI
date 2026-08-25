# One footnote, not a keying problem — and two of the eight were never askable

- **Cycle**: 2026-08-08 06:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: `STATE-1-cellaudit` Audit the remaining seven matrix cells against their scene weights
- **Phase**: P5
- **Status**: keep

## What I tried

- Ran `relief_interval.survey` per **controller** (`stock_mppi`, `risk_mppi`)
  over the matrix's four obstacle scenes, ladder extended to 10000 exactly as
  D-128 did, 8 seeds — the per-cell measurement the bottleneck asked for.
- Graded all 8 cells against D-127's shipped scene-keyed weights (head_on 1000,
  crossing 1000, convoy 10, freezing 10) with `operating_weight.audit_cell`.
- Shipped `CELL_UNSWEPT` + `unswept_cell` + `MatrixAudit` + `audit_matrix` when
  the walk turned out to have no verdict for two of the cells.
- Fixed `knife_edge`, which the audit caught mis-firing on a shipped cell.

## What worked / what failed

- ✅ **The bottleneck's question answers "one footnote".** 8 cells: **5
  `CELL_AGREES`, 1 `CELL_DIFFERS`, 2 `CELL_UNSWEPT`**. The lone disagreement is
  the already-known `risk_mppi/cafe_obstacle_crossing_v0` (D-128). Every other
  *measured* cell runs where its scene's row says it does, so D-127's 5/40
  headline carries one named caveat rather than a systematic keying error, and
  Q-113's report-per-scene lean does not have to be re-argued.
- 🔴 **But the denominator of that audit is 6, not 8.** `cafe_freezing_v0` is
  refused by `sweepable` for **both** arms (`no_declared_margin`, D-120's
  `unscored_margin`), so two cells have no measured agreement with their scene
  weight and cannot acquire one until the scene file declares a margin. Before
  this cycle `audit_cell` could not even express that: it takes a
  `ReliefInterval` and there is none, so those cells would have raised or — if
  the argument had been made optional with a sensible default — graded
  `CELL_AGREES`. An unasked cell reading as a matched one is D-107 / D-120 /
  D-127's empty-denominator failure with a new coat of paint, so `CELL_UNSWEPT`
  is a verdict and `MatrixAudit` keeps **three** counts that are never summed
  into two.
- 🔴 **`knife_edge` tested one half of its own docstring, and a shipped cell was
  wearing the false alarm.** It asked `len(cell_admissible) == 1` while the
  docstring says "is the cell's *own operating point* the only rung it
  tolerates". `risk_mppi/cafe_convoy_v0` runs at the shipped **10** (via
  `baseline_admissible`) and has rung set `{30}` — one rung, not the one it runs
  at — so it printed `KNIFE_EDGE` on an operating point that was not in the set
  being counted. **Third sighting of shipped-weight-is-never-a-rung**, after
  `resolve` (D-127) and `admits` (D-128). Fixed by testing both halves; D-128's
  claim about crossing survives unchanged (`{3000}`, and 3000 *is* where it
  runs, so it stays flagged).
- 🔴 **The scene table is ladder-dependent, and the extended ladder moves it.**
  `cafe_head_on_v0` tolerates **every** rung including 10000, so its relieving
  set grows with the ladder's top and `pick_weight`'s log-middle walks up with
  it: D-127's ladder gives **1000**, this cycle's one-rung-longer ladder gives
  **3000**. The log-middle is a statement about where the surveyor stopped
  testing, not about the scene — on any scene whose ceiling is the ladder's own
  top. Logged as Q-114; the audit above deliberately grades against D-127's
  shipped weights, not the re-derived ones, so the two questions stay separate.
- 🟡 **Non-contiguity is not one cell's quirk.** `tolerated` (rungs plus the
  shipped weight when measured admissible) reads `{10, 3000}` for risk/crossing
  — D-128's two islands — and **`{10, 300, 1000}`** for stock/crossing and
  `{10, 30}` for both convoy cells. Every measured cell here tolerates the
  shipped 10 and then a gap. Interval arithmetic over the weight axis is wrong
  on 6 of 6 measured cells, not on the one D-128 caught.

## North-star delta

- The safety headline's structure is now *audited* rather than asserted: 5/40 is
  one footnote over a 6-cell measurable population, with the 2 unmeasurable
  cells named and their reason attributed to a scene file, not to the weight.
- No controller change and no movement in `unsafe_rate` — this is a reporting
  correctness cycle, the third in a row that found a real defect in the
  instrument rather than in the planner.

## Key learnings

- **A verdict enum that cannot say "not measured" will say "fine" instead.** The
  gap only became visible when the walk was run over the *whole* matrix instead
  of the cells that happened to sweep — the same shape as `table`'s `UNSWEPT`,
  one layer out, which is now the second time this exact omission has been
  found by widening a denominator.
- **A predicate extracted once still leaks if a sibling re-derives it inline.**
  `admits` was D-128's extraction of shipped-weight-is-never-a-rung, and
  `knife_edge` sat three lines below it re-deriving the same question from
  `cell_admissible` — so the fix is not "extract the predicate" but "audit every
  site that reads the rung set at all".
- **Extending a ladder to avoid an untested-above limit can move a shipped
  operating point.** D-128 extended to 10000 to close an honest limit and that
  extension silently re-picks head_on's weight. Ladder edges are not free
  parameters of the report.

## Recommended next 1–3 priorities

1. **Answer Q-114 — make `pick_weight` ladder-invariant** (or state the ladder
   in the operating point). Head_on's weight moved 1000 → 3000 on a ladder
   change with no measurement disagreeing.
2. **Re-run D-119 / D-124's A/Bs above the relief threshold** — still the
   largest un-redone comparison; the operating points are shipped.
3. **Declare a margin for `cafe_freezing_v0`** (user) — it is the only thing
   standing between 6 measurable cells and 8.

## Artifacts
- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic, #67)
- Files touched: `eval/mppi_sandbox/operating_weight.py`, `eval/mppi_sandbox/tests/test_operating_weight.py`, `docs/decisions.md`, `docs/deliberations.md`
- TSV row appended: yes

# The `K = 128` run translated — it did not widen, and what fell off the bottom is beyond repair

- **Cycle**: 2026-08-16 03:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: `<temperature-column-at-k128>` (STATE #1)
- **Phase**: P3
- **Status**: keep

## What I tried

- Walked `lam ∈ {1.0, 1.25}` at `K = 128`, `w = 5`, census 16 seeds
  (32 closed-loop runs, ~35 s concurrent at 8 workers — half the per-run cost
  of the `K = 256` columns). Together with D-292's `lam = 1.15` column this
  gives a three-temperature grid at `K = 128`.
- Shipped `unanimity_run_in_k()` — the first reader on this branch to compare
  **two `K` grids** rather than walk one axis. It answers STATE's bottleneck
  directly: is the `16/16` cell D-292 found a member of a *wider* run, or of a
  *translated* one?
- Recorded both columns as module data (`MEASURED_SEEDS_16_LAM10_K128`,
  `MEASURED_SEEDS_16_LAM125_K128`) and 16 tests, five of which are synthetic
  controls for branches the real data does not exercise.

## What worked / what failed

- **Answer: `RUN_TRANSLATES_IN_K`, and it is not close.** On the three
  commonly-walked temperatures, `K = 256` is unanimous at `1.0` and `K = 128`
  at `1.15`. Same run *length* (one temperature each), different member. The
  `16/16` cell was **bought, not added**.
- **The two membership changes are one mechanism.** The gained temperature came
  off the **ceiling**; the lost one went out the **floor**. A single ensemble
  sliding down in band-relative coordinates is the only thing that produces
  that pairing — and it is the direction D-292 derived from an entirely
  different column, so this is a cross-check rather than a restatement.
- **The lost column is worse than out-of-band: it is structurally
  inadmissible.** `lam = 1.0` at `K = 128` spans `10.23x` against a band width
  it now exceeds, so D-283 disqualifies it — no common factor puts it back,
  because a common factor translates a spread and cannot narrow one. Lowering
  `K` did not merely slide that temperature out of the window; it put it beyond
  reach of the axis that moved it.
- **D-292's spread reading does not generalise off its column.** Span *rises*
  with `K` at `lam = 1.15` (where D-292 read it) but *falls* with `K` at both
  `1.0` and `1.25`. `span_response_uniform` is `False`. "`K` pulls the ensemble
  apart" is true where it was measured and nowhere else — this cycle nearly
  inherited it as an axis property.
- **One miss is a hair's breadth and the count hides it.** `lam = 1.25` at
  `K = 128` reads `15/16`, but the sole miss clears the ceiling by `0.176%` —
  two orders of magnitude tighter than any other miss on this branch. The
  reading now carries `marginal_misses` so a firm `15/16` and a hairline one
  cannot be spelled identically.
- **Failed twice on the runner before any science happened**: `/tmp` script
  lost `sys.path` in the worker processes, then passed a scenario *path* where
  a loaded `Scenario` was required. Both cost ~1 min total because the walk is
  cheap; on a `K = 512` grid they would have cost far more.

## North-star delta

- **No obstacle, clearance or near-miss number moved.** Still one scene
  (`cafe_freezing_v0`), still `transfers_to_ab_scene = False`.
- What moved is the *shape* of the claim: the `K` axis is now known **not** to
  widen the operating window at `w = 5`. A repair that trades `lam = 1.0` away
  to buy `lam = 1.15` is a relocation of the operating point, not an
  enlargement of it — which is a materially weaker thing than D-292's headline
  invited, and worth knowing before any of it is carried to the A/B scene.
- **PR #68 remains the north-star blocker** — twenty-first consecutive cycle.

## Key learnings

- **Compare grids on their intersection, or a missing measurement becomes a
  failure.** `K = 256` carries seven temperatures and `K = 128` three. Counting
  the full grids would charge `K = 128` for `lam = 1.1`, never walked there,
  and report a *narrowing*. `test_ignoring_the_grid_restriction_would_flip_the_verdict`
  ships that wrong answer as a control so the restriction cannot be quietly
  dropped later.
- **A cell is not a window.** D-292 measured one unanimous cell and STATE
  correctly refused to call it an operating point. The reason that caution was
  right is now measured: the cell's neighbours on the same grid are `13/16` and
  `15/16`.
- **Check whether a prior cycle's axis property was ever an axis property.**
  The span-vs-`K` direction read as a fact about `K`; it is a fact about `K` at
  one temperature, and the second temperature walked reverses it.

## Recommended next 1–3 priorities

1. **Bracket the `K` axis below `128`** (`K ∈ {64, 96}` at `lam = 1.15`). Still
   unbracketed at the bottom, and now more interesting: if the ensemble keeps
   sliding down, `64` should push `1.15` out the floor the way `128` pushed
   `1.0`. That is a falsifiable prediction this cycle's slide direction makes.
2. **Walk `lam = 1.1` at `K = 128`** — the one temperature that would turn the
   three-point grid into a real length comparison instead of a one-vs-one. It
   is unanimous at `K = 256`, so it is the single most informative missing cell.
3. **Reprobe the 5 stale `inert_surface` pins** — fifteenth consecutive cycle;
   it again forced an all-writes-before-suite ordering.

## Artifacts
- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic)
- Files touched: eval/mppi_sandbox/calibrated_ladder.py, eval/mppi_sandbox/tests/test_calibrated_ladder.py, docs/decisions.md, results/p3-epistemic-shadow-cost-critic.tsv
- TSV row appended: pending

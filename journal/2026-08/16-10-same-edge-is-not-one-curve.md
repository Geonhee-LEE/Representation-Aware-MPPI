# The same edge is not one mechanism: the run's two bounds are position and spread

- **Cycle**: 2026-08-16 10:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: `<test-the-same-edge-window-against-one-curve>` (STATE #1 — the science item)
- **Phase**: P3
- **Status**: keep

## What I tried

- STATE's open question, stated as a reduction: if both walked exits from the
  `K` run leave through the **floor** (D-298), maybe they are the same
  *quantity* — band-relative ESS sagging — and the two endpoint searches
  collapse into one root-find.
- Made it a measurement instead of a reading. The floor coordinate factors
  exactly two ways, `min_frac = median_frac / lower_spread`: where the
  ensemble **sits** and how far its lower tail **reaches**. For each exit
  column, substitute one factor with the unanimous run's own value and ask
  whether the miss survives.
- Shipped `same_edge_decomposition` + `_floor_decomposition` in
  `calibrated_ladder.py` with 7 tests. **Zero new sim runs** — the nine walked
  columns already contained the test.

## What worked / what failed

- **The reduction is false, and cleanly so.** `SAME_EDGE_TWO_MECHANISMS`, a
  double dissociation: `K = 80` is cured by the run's position (`2.29x` of
  floor) and **not** by its spread (`0.73x`); `K = 176` is cured by the run's
  spread (`1.81x`) and **not** by its position (`0.963x`).
- The lower exit's spread points the *wrong way* — `2.089` against the run's
  `2.356`, i.e. `K = 80`'s ensemble is **tighter** than the run's, so lending
  it the run's spread makes the miss worse. Position is the only story there.
- The upper exit's position sits **inside** the run's own range
  (`0.2128` in `0.1734 … 0.3095`). No curve in position can put it outside a
  run it is positionally inside of. What is out of range is the lower tail:
  `4.97`, wider than any column below `K = 192`.
- **Honest caveat, shipped in the payload**: the position leg at `K = 176`
  fails to cure by **3.7%** (`0.963x`). One seed's luck from flipping that
  exit's attribution to `both`. `marginal=True` and `any_leg_marginal=True`
  carry it; the spread leg is decisive, the position leg is not.
- `ess_span`'s `max/min` would have hidden this: `K = 160` has the tightest
  full span on the axis and an unremarkable lower half, so the tail that
  decides a floor miss is not the tail the span reports.

## North-star delta

- **No movement in any robot-facing number.** No obstacle, clearance,
  near-miss or CTE moved. One scene, `transfers_to_ab_scene = False`, still
  blocked on PR #68 for any A/B reading.
- What moved is the search: the two bounds are **not** one root-find, so the
  cheaper endpoint plan the same-edge reading suggested does not exist.
- Cost: zero sim runs, seconds of arithmetic on already-walked columns.

## Key learnings

- **Sharing an edge is not sharing a mechanism.** The floor is a coordinate,
  not a cause; two ensembles reach it by sliding down and by fanning out, and
  a verdict keyed on the edge cannot tell them apart. Every `*_SAME_EDGE`
  verdict on this repo is now suspect in the same way.
- **A factorisation is worth more than another column here.** Nine columns
  were on disk for four cycles and contained an answer nobody had asked them
  for. The instinct to bisect once more would have cost 90 s of runs and
  answered a different question.
- The one-curve hypothesis was worth stating *because* it was falsifiable in
  one substitution. It was also the reading the D-298 test docstring had
  already committed to prose — that docstring is corrected in place rather
  than rewritten, so both readings stay quotable together.

## Recommended next 1–3 priorities

1. **Re-read the `lam` axis bracket with the same decomposition.** D-290's
   window is the other closed interval on this project and it was read at the
   edge level too. Zero runs; the columns are on disk.
2. **Walk `K = 168`** in `(160, 176)`. Now sharper than it was: if the upper
   endpoint is a *spread* boundary, `168`'s lower tail — not its position —
   is the number to predict.
3. **Q-160** — retire the self-blocked `inert_surface` pins (unchanged, six
   cycles of evidence).

## Budget note — the receipt cost this cycle three suite runs

- Two `push_preflight record` invocations ran **concurrently** against the same
  `--out`. `record` unlinks its output at start, so the second deleted the
  first's receipt mid-flight and both then contended for the same cores.
  One `record` per cycle; check `ps ax | awk '/push_preflight record/'` first.
- The first receipt that did land came back **red**, and correctly:
  `any(a in ("both", "neither") for a in ...)` reads to `guard_reflexivity` as
  an inline **exemption**, typing the new function as a `DIFFERENCE` guard and
  landing it in `unprobed_revocable()` — 7 failures across three modules. That
  is the D-295 probe-fixture blocker STATE has routed around for two cycles by
  adding no new readings at all. **The route through it is cheaper than the
  fixture: spell the test as equalities.** A function that exempts nothing
  should not claim the shape. Final receipt: `3397 passed, rc=0, 770s`.
- Cycle ran well over the 35-minute budget. Honest total: the science was
  ~12 minutes; the rest was the receipt.

## Artifacts
- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic)
- Files touched: eval/mppi_sandbox/calibrated_ladder.py, eval/mppi_sandbox/tests/test_calibrated_ladder.py, docs/decisions.md, journal/2026-08/16-10-same-edge-is-not-one-curve.md, results/p3-epistemic-shadow-cost-critic.tsv
- TSV row appended: pending

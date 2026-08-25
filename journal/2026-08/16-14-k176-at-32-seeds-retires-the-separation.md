# Doubling the ensemble on one column killed the separation it was famous for

- **Cycle**: 2026-08-16 14:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: `3bec5d39` rerun-k176-at-32-seeds
- **Phase**: P5
- **Status**: keep

## What I tried

- Re-walked `K = 176` at seeds `16..31` (`lam = 1.15`, `w = 5`,
  `cafe_freezing_v0`, same `sweep_seeds` body), the item STATE named as the
  first in weeks whose answer was **not already on disk**.
- Re-ran seed `0` alongside as a provenance check rather than trusting the
  claim of a shared body: it returned `7.5295`, identical to the recorded row,
  so the two halves are one column and not two experiments.
- Added `MEASURED_SEEDS_32_LAM115_K176(_EXT)` plus a test pinning both claims
  the new seeds retire. Deliberately did **not** overwrite the 16-seed table —
  every `K`-axis verdict on record ran on it.

## What worked / what failed

- **17 runs, ~2 min, and the answer inverted two claims.** Misses go `(0,)` →
  `(0, 19, 26)`; membership `15/16` → `29/32`. The column stays an exit and
  gets slightly *worse*, rather than reverting to unanimity.
- **D-301's `SEPARABILITY_UNTESTABLE` was a sample-size artifact.** It was
  untestable at `n = 16` only because the single miss *was* the exit, so the
  one deletion reaching that leg destroyed what it measured. Three out-of-band
  seeds means no single deletion can remove the exit — the leg is now genuinely
  probeable. The verdict was right about `n = 16`; naming it `UNTESTABLE`
  rather than `STABLE` is what let it die cleanly instead of misleading.
- **D-298's "separation" did not survive.** Span `7.738x` → **`13.941x`**,
  crossing the `10.0x` band. `K = 176` was the first column where the two
  disqualification mechanisms *disagreed* (span-admissible, membership-
  inadmissible); at `n = 32` both disqualify it. The measured **order** of the
  two failures — "membership fails at `(160, 176]`, span not until
  `(176, 192)`" — was an artifact of which 16 seeds were drawn.
- The span moved because the ensemble widened at **both** ends: both new misses
  sit below the old minimum and the new max (`73.1688`, seed 18) above the old
  one. A 16-seed span reading is blind to exactly this.

## North-star delta

- **No movement in any robot-facing number**, and none was available: still one
  scene, still `transfers_to_ab_scene = False`, still blocked on PR #68 for any
  A/B reading.
- What moved is negative and real: a structural claim five decisions had been
  building on is withdrawn at a cost of 17 runs. The `K` axis has one fewer
  asserted property, not one more.

## Key learnings

- **A span read at `n = 16` is a lower bound on the span, not an estimate of
  it.** Both tail seeds arrived in the second 16. Any column here called
  "span-admissible" near the `10.0x` band is an untested claim, and several are.
- **The instrument's own elapsed reading beat my estimate by ~4×, twice.** I
  twice believed I was out of budget when `cycle_wallclock elapsed` said 5–7
  min. D-181 exists because cycles inflate elapsed time; I did it while holding
  the tool that measures it.
- **I re-derived D-009 from scratch to conclude PRs #23/#44 cannot be closed** —
  the exact waste D-140 and D-269 were written to stop, and I found them only
  via the Daily Log. Gate 1 passes on this branch because PR #67 is already
  open; that reading belongs at the top of the gate checklist, not in prose.

## Recommended next 1–3 priorities

1. `<re-span-the-k-axis-at-32>` — `K = 160` reported the axis-minimum span
   (`3.05x`) at `n = 16`; if 176's span nearly doubled, the axis's shape is
   unmeasured. Re-walk `160` and `192` at 32 seeds before any further bisection.
2. `<retype-the-k-leg-now-that-it-is-probeable>` — rerun
   `attribution_separability(window="k")` against the 32-seed column; the
   `UNTESTABLE` branch should now return a real attribution.
3. `<answer-q160-retire-self-blocked-pins>` — unchanged, nine cycles of evidence.

## Artifacts

- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic)
- Files touched: eval/mppi_sandbox/calibrated_ladder.py, eval/mppi_sandbox/tests/test_calibrated_ladder.py, docs/decisions.md, journal/2026-08/16-14-k176-at-32-seeds-retires-the-separation.md, results/p3-epistemic-shadow-cost-critic.tsv
- TSV row appended: pending

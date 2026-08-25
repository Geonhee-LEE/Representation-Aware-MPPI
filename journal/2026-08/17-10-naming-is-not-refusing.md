# Naming is not refusing: the bracket's interior count returns `None`

- **Cycle**: 2026-08-17 10:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: `3bec5d39-74f4b` [sandbox] Make `k_axis_bracket` refuse interior claims structurally
- **Phase**: P3
- **Status**: keep

## What I tried

- Took STATE's #1, which was its own bottleneck sentence: D-319 measured that
  `k_axis_bracket`'s run *is* the censored region and named the statistic an
  interior question must be driven off — and left `membership_by_k` sliceable,
  so a caller could still cut it to the interior and reason there.
- Added four readings (`K_INTERIOR_{UNREADABLE,EMPTY,NOT_A_RUN,READABLE}`) and
  made `interior_membership_by_k` return `None` under the refusal, on the
  precedent D-308 set one level out when it suppressed `run_bounds_open_intervals`
  for an object that was not there to be bounded.
- Derived the interior as a **slice of the unanimous block** (`blocks[0][1:-1]`),
  not as `{k : min < k < max} - unan`. That spelling is a set difference, which is
  the signature `guard_reflexivity` classifies as a revocable guard; D-309
  withdrew a field for exactly it, and Q-161 is still open on the classification.
- Re-read saturation **per interior column** instead of inheriting it from how
  `unan` was built, so the branch that fires when `need` stops being the column
  size is a reading rather than a wrong refusal.

## What worked / what failed

- The refusal is grid-driven, and that is the whole negative control: three of
  four readings fire on grids this branch actually measured — `UNREADABLE` on the
  `n=16` run `{96,128,160}` (interior `{128}`), `EMPTY` on the two-column runs
  (D-294/D-296) and the one-column ones (D-292/N32_D304/N32_D306), `NOT_A_RUN` on
  D-307's punctured `n=32` set. A flag that fired everywhere would be a constant
  wearing a verdict's name, which is the defect D-319 paid for from the other side.
- `K_INTERIOR_READABLE` is **unreachable** today and I did not pretend otherwise.
  The interior is a slice of the run and the run is the saturation predicate, so
  the containment holds by construction. Rather than delete the branch or fake a
  tamper, a test *measures* the containment and says what would break it — a later
  edit deriving `interior` from the walked bounds instead of from the block.
- `census_preempt` came back `CLEAN` on all three censuses (120 guards vs pin 120,
  68 population claims all in `READING`, 0 unregistered citations). Second standing
  run, first one that found nothing — which is the outcome that makes the two-second
  price worth paying.
- `inert_surface staged` returned `STAGED_MOVED` on 5 pins: the new tests count as
  adding a reader, so `JOURNAL.md` / `RESULTS.md` / `STATE.md` / `journal/` /
  `results/` lost their exemptions. Not a failure (D-207) but it made D-315's write
  order load-bearing rather than merely correct — every REPORT write had to land
  before the receipt or become material drift.

## North-star delta

- No movement. Zero sim runs, one scene, one rung, one temperature; every A/B
  reading still blocked behind PR #68.
- What moved is the validity of claims already standing: an interior question put
  to this payload now gets `None` and a pointer instead of a flat number that
  reads like a level. The count was already blind there — D-317 measured it — so
  nothing informative was withheld, only something misleading.

## Key learnings

- **A caveat that a reader must know to consult is not yet a refusal.** D-319 was
  correct, complete, and delivered at the publishing site, and it still left the
  wrong field readable. The repair D-308 wrote one level out was structural
  (`None`), not textual, and that is the form that transfers.
- **Where a derivation is spelled changes how it is classified.** Interior-as-slice
  and interior-as-set-difference compute the same tuple; one of them would have
  reclassified this function as a revocable guard and demanded an executed probe.
  The cheap spelling was also the correct one, but only because D-309 had already
  paid to find out.
- **An unreachable branch is worth keeping if a test says why it is unreachable.**
  Deleting `K_INTERIOR_READABLE` would have made the refusal unconditional and
  indistinguishable from an assumption.

## Recommended next 1–3 priorities

1. Carry the same treatment to the other interior-facing field: `interior_inadmissible_k`
   is still a plain tuple on a punctured grid, where "interior" has no referent.
2. `aggregate_results.sh` above the receipt in the constitution's push block —
   D-316 makes it a write like any other, and STATE has carried it two cycles.
3. Decide whether this branch closes. PR #67 now carries fourteen commits spanning
   a cost critic, a verification surface, and a `K` axis — one unreviewable diff.

## Artifacts
- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic)
- Files touched: eval/mppi_sandbox/calibrated_ladder.py, eval/mppi_sandbox/tests/test_calibrated_ladder.py, docs/decisions.md, journal/2026-08/17-10-naming-is-not-refusing.md, results/p3-epistemic-shadow-cost-critic.tsv
- TSV row appended: pending

# The operating point survives the census's seed count — 15/16, and the miss is still seed 4

- **Cycle**: 2026-08-15 13:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: `<ensemble-at-n16>` Q-153 — read the ensemble at `n = 16`, co-record with `n = 8`
- **Phase**: P3
- **Status**: keep

## What I tried

- Took Q-153's registered next action, which is also D-271's deferred alternative
  (a): re-read `(lam = 0.8, w_voo = 5)` on `cafe_freezing_v0` at
  `seed_count_licence.CENSUS_LADDER_SEEDS = 16` instead of `ab.DEFAULT_SEEDS = 8`.
- Ran seeds `8..15` through the existing `calibrated_ladder.sweep_seeds` — same
  body, same `ess_at_peak.ISOLATION`, so the extension and the incumbent rows are
  one measurement. **8 closed-loop runs, 30.7 s.**
- Added `seed_count_readings()`, which co-records both counts *without* pooling
  them, and pinned the discipline in tests rather than in prose.

## What worked / what failed

- **The verdict word survives at the census's own `n`.** `MAJORITY_USABLE` at
  both counts: `7/8` → `15/16`. The extension is `8/8` in band, `8/8` audible,
  `8/8` reached goal, so **seed 4 is still the sole miss and still a band-only
  miss** — the repair axis stays temperature, not arm scale.
- **This is the first cycle in eight that strengthened a cost-critic number
  rather than qualifying one.** D-271's operating point was open to "n = 8
  artefact"; it is not one, and it now sits on the predicate the census grades at.
- **The claim I did *not* make is the rate going up.** `0.875 → 0.9375` is a
  comparison between two `n`, which is exactly what D-019(b) forbids — the
  durable statement is that the same vocabulary entry is selected at both counts.
  `seed_count_readings` exposes no difference field, and a test asserts no key
  containing `delta`/`diff`/`ratio` ever appears.
- **D-271's own `12.68×` needed the same demotion it gave D-019's `~5×`.** Span
  is `max/min` over the sample, so a superset draw can only widen it: `17.34×` at
  `n = 16`. That number is not evidence the cell got worse; it is the same
  monotone-in-`n` trap the conjunction has, one level down, and it is now marked
  `spans_comparable: False` beside the verdict flag.
- **Cost was far below the estimate.** Q-153 priced this at ~2 min; it was 31 s,
  because `sweep_seeds` already took `seeds`/`cell` arguments — D-271 built the
  extension point and then deferred the extension.

## North-star delta

- **First movement in eight cycles, and it is on the attract arm.** `w_voo`'s one
  published operating point is now `15/16` at the census's seed count, not `7/8`
  at a looser one — an obstacle-avoidance parameter got more trustworthy, not
  merely better documented.
- Still zero movement on the thing that would actually matter: Q-148's four-arm
  A/B needs `cafe_blind_corner_v0`, which is on unmerged PR #68 — **ninth**
  consecutive cycle blocked by the feasibility filter.

## Key learnings

- **A deferred alternative is cheaper than its own deferral note.** D-271 wrote
  three sentences explaining why `n = 16` was out of scope; taking it cost 31 s
  of compute. When the extension point already exists, "defer to a Q" can be the
  more expensive branch.
- **Monotone-in-`n` statistics travel in packs.** The branch had a rule for one
  of them (D-019(b), the conjunction) and quoted a second one (span) freely
  across cycles. Any `max`/`min`/conjunction over a sample inherits the same bar.
- **`inert_surface staged` fired again on the same 5 pins** (D-207 tax). It is
  now the third cycle to pay it and the second to note that STATE's
  `<reprobe-stale-pins>` is what stops it — the reprobe is measured at >900 s for
  `STATE.md` alone (D-259 (a)), so it genuinely needs its own cycle.

## Recommended next 1–3 priorities

1. `<reprobe-stale-pins>` — buy back the 5 withdrawn exemptions in a dedicated
   cycle; three cycles running have paid the write-order tax now.
2. `<seed-4-band-repair>` — seed 4 is the only thing between this cell and
   `UNANIMOUS_WINDOW` at `n = 16`, and D-272 says the repair axis is `lam`.
3. `<q148-ab-on-merge>` — the moment PR #68 lands, run the four-arm A/B; it has
   been the branch's blocked centre for nine cycles.

## Artifacts
- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic, #67)
- Files touched: `eval/mppi_sandbox/calibrated_ladder.py`, `eval/mppi_sandbox/tests/test_calibrated_ladder.py`, `docs/decisions.md`, `docs/deliberations.md`, `results/p3-epistemic-shadow-cost-critic.tsv`
- TSV row appended: yes

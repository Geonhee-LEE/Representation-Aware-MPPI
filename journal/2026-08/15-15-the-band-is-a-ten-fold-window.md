# The band is a 10× window, the spread was 17.34× — and temperature closes it

- **Cycle**: 2026-08-15 15:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: `<seed-4-band-repair>` Seed 4 is the only thing between this cell and `UNANIMOUS_WINDOW` at `n = 16`
- **Phase**: P3
- **Status**: keep

## What I tried

- Took STATE #2, but not as written. "One ladder walk on one seed" cannot
  answer the question it is posed to answer: `usable` is an **all-seeds
  conjunction** (D-019) and `lam` is a **shared** knob, so a rung that repairs
  seed 4 also moves the other 15. A single-seed walk can only ever return an
  unusable half-answer.
- Screened the instrument before walking it (D-171's rule, D-272's method).
  Both quantities are ratios: `ESS_BAND_FRACTIONS = (0.05, 0.5)` makes the band
  a **10× window at every `K`**, and the ensemble's spread is `max/min`. Under a
  response that scales every seed alike, a `17.34×` ensemble fits a `10×` window
  at **no** rung. Shipped as `span_admits_band` → `SPAN_EXCEEDS_BAND`.
- Named the premise in the payload instead of in prose, with the price of
  discharging it (one rung), and then paid it: 16 closed-loop runs at
  `(lam = 1.0, w_voo = 5)` — the *smallest* rung a uniform response predicts
  repairs seed 4, chosen to be maximally favourable to the repair.

## What worked / what failed

- **The premise is false, by a wide margin.** Span `17.34× → 5.46×`, a 69%
  compression. `lam` does not translate the ensemble, it **squeezes** it. So my
  own `SPAN_EXCEEDS_BAND` bounds nothing beyond the rung it was read at.
- **`(lam = 1.0, w_voo = 5)` is `16/16`** — in band, audible, reaching, at the
  census's own `n = 16`. `seed_verdict` returns `UNANIMOUS_WINDOW`. Every prior
  reading on this branch fell short of that word: `7/8` (D-271), `15/16`
  (D-281). Seed 4 goes `4.5329 → 14.5829`, clearing the `12.8` floor.
- **The screen was still worth building, and not because it was right.** It was
  wrong, and it was *cheap to find wrong* — 116 s — precisely because it stated
  the one measurement that would void it. A prose caveat would have retired
  quietly (D-047); a `premise` field with a named discharge did not.
- Found and fixed a labelling hazard on the way: the seed tables store no
  `lam`, so `seed_points`/`seed_census`/`seed_verdict` would have stamped the
  new rung's rows with the old cell. Threaded `cell` through all three.

## North-star delta

- **First movement in nine cycles, and it is on the north star's axis.** The
  epistemic shadow cost critic now has an operating point that is
  simultaneously ESS-admissible and audible on **every one of 16 seeds** — not
  a rate, the conjunction. Obstacle-avoidance numbers are still untouched, so
  this is a precondition met, not a metric moved.
- The `UNKEYED` window (`0.2, 0.4, 0.8`) does **not** contain `1.0`. D-273
  already narrowed D-272 to the rungs *tried*; this walks outside the window
  and the window was never a certificate for this cost field anyway.

## Key learnings

- **Screen the conjunction, not the member.** "Repair the failing seed" is the
  wrong shape of question whenever the knob is shared: the binding constraint
  is whether the *ensemble* fits, and that is a ratio-vs-ratio question
  answerable off disk in zero runs.
- **A ratio window does not widen with `K`.** Reading `(12.8, 128.0)` as an
  interval invites "use a bigger sampler"; it is `10×` at every `K`.
- **A conditional verdict is worth more than a right one if the condition is
  cheap.** This screen was refuted in 116 s and produced the branch's first
  `UNANIMOUS_WINDOW` as the by-product of its own refutation.
- Corollary for the span: `max/min` grows with `n`, so `SPAN_EXCEEDS_BAND`
  survives every larger read and `SPAN_FITS_BAND` does not. The `16/16` is a
  statement about 16 draws.

## Recommended next 1–3 priorities

1. **Re-baseline the branch's readings onto `(lam = 1.0, w_voo = 5)`.** D-268 /
   D-270 / D-271 / D-281 all read a cell that is now known to be the wrong one;
   D-027's ceiling question in particular should be re-asked from a rung where
   the ensemble is admissible.
2. **Walk one more rung (`lam = 1.2`) to bound the compression.** `extrapolates`
   is `False` by construction — two rungs license nothing about a third, and
   the ceiling is the thing a rising `lam` will eventually hit.
3. `<reprobe-stale-pins>` — **fifth** consecutive cycle paying the withdrawn-
   exemption tax.

## Artifacts
- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic)
- Files touched: eval/mppi_sandbox/calibrated_ladder.py, eval/mppi_sandbox/tests/test_calibrated_ladder.py, docs/decisions.md, journal/2026-08/15-15-the-band-is-a-ten-fold-window.md
- TSV row appended: pending

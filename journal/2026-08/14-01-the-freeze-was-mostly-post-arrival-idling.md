# The freeze was mostly post-arrival idling

- **Cycle**: 2026-08-14 01:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: STATE#1 (Notion unauthorized this session) — widen `time_to_goal` to the D-235 paired-seed protocol
- **Phase**: P3
- **Status**: keep

## What I tried

- New `eval/mppi_sandbox/arrival_spread.py`: first-arrival time as a **paired**
  arm comparison — `ArmArrivals` (per-seed arrivals, `None` = never arrived),
  `ArrivalComparison` (paired bootstrap CI + exact sign test, reusing
  `margin_free.RungComparison` and `paired_step.sign_test_p`), `sweep` / `walk`.
- Walked **both** temperatures over the same twelve seeds. D-247's numbers came
  from `freeze_price.profile_arm`, which passes no `params` — so they are at
  `lam = 0.1`, while the paired protocol runs at `0.8`. Widening moves **n and λ
  together**, so a one-column reading would have been unattributable (D-244's
  trap, one cycle later).
- Added `StallSplit` / `stall_split` after the λ=0.8 column showed 12/12
  arrivals, which sits badly against D-244's ~80 s stalls at that temperature.

## What worked / what failed

- **D-247's evidence form does not survive n=12; its conclusion does.** The
  spans that were non-overlapping at n=3 **overlap** at n=12 — `stock_mppi`
  7.20–9.90 s now covers both other arms entirely (8.50–9.50, 8.60–9.10). But
  the *paired* comparison separates cleanly: `social` **+1.12 s**
  [+0.62, +1.49] p=0.006, `risk` **+1.11 s** [+0.67, +1.42] p=0.006. Two
  disjoint spans of three runs was an order statistic with no interval on it;
  the pairing is what carried the signal, and it is what `spans_overlap` is kept
  in the module to contrast against rather than to report.
- **The separation survives the temperature too, and widens**: at `lam = 0.8`,
  `social` **+1.63 s** [+1.26, +1.94] and `risk` **+1.67 s** [+1.44, +1.85],
  both p < 0.001, 12/12 arrivals on every arm. `separation_survives` is `True`
  in both columns.
- **The headline is the thing I went looking for as a sanity check.** 12/12
  arrivals at `lam = 0.8` contradicts D-244's 81.90 s stall. It does not:
  `social_mppi` seed 0 **arrives at 10.1 s** and the sim runs to **93.1 s**, and
  only **20 of 847** stalled steps fall before arrival. Swept 3 arms × 3 seeds:
  **post-arrival share ≥ 99.1 % in all nine cells**, pre-arrival longest stall
  **0.10–0.80 s** against the scene's declared **2.0 s** limit. Read before
  arrival, **every cell passes**; read whole-trajectory, **every cell fails**.
- **So the freeze grid was grading loitering.** D-244/D-245/D-246's
  "12/12 exceed", "median longest 82.15 s", and `NONE_ADMISSIBLE` at every
  `w_freeze` are arithmetic I reproduce exactly — but on a quantity that is
  ~99 % time spent sitting at a goal already reached. That also supplies the
  mechanism D-246 left open (STATE #3, "why does the price reverse above 1e5"):
  `ProgressPriceCritic` prices along-path progress, and there is no progress
  left to buy after arrival, so no weight could ever have moved this number.
- Census moved (92, 61, 32) → **(94, 61, 33)**, `defaults` nil for the sixth
  consecutive cycle; both new `decides` are `sweep(..., lam=)`, including the
  CLI that D-244 had to be convicted over.

## North-star delta

- **A freeze metric this branch has spent four cycles optimising against is
  measuring the wrong interval.** That is negative movement made visible, which
  is worth more than the four cycles of tuning it invalidates.
- The arm ranking D-247 declined to quote is now licensed at n=12 at both
  temperatures — a duration-side freeze reading needing no predicate, which is
  exactly DRA-MPPI's prescription (feed, 2026-08-13 20:00).
- No planner change. `ProgressPriceCritic` is untouched and its verdict is not
  overturned — it is *unreadable* until the metric is re-scoped.

## Key learnings

- **Non-overlapping ranges at small n are not a separation result.** The
  cheapest way to have caught D-247's over-read early was to state it as a
  paired interval; the spans moved, the interval did not.
- **A metric with no terminal condition measures the simulator, not the robot.**
  `freeze_duration` scans the whole trajectory and this scene keeps simulating
  ~10× past arrival, so any early-arriving run manufactures an enormous freeze.
  Every scene with `duration ≫ time_to_goal` has this defect latent.
- **The check that found it was a consistency check between two metrics, not a
  test.** 12/12 arrivals and an 80 s stall cannot both describe driving. Nothing
  in the suite compares two metrics' stories about the same run.

## Recommended next 1–3 priorities

1. **Re-read the `w_freeze` grid with the pre-arrival stall** — D-246's 60 runs
   are on disk-reproducible settings; the verdict may invert from
   `NONE_ADMISSIBLE` to "the term was never needed".
2. **Give `freeze_duration` an arrival-aware scope** (or a sibling that has one)
   and re-grade `freeze_duration_max` on `cafe_freezing_v0`.
3. **Sweep the other scenes for `duration ≫ time_to_goal`** — the same
   contamination is latent wherever the sim does not stop at the goal.

## Artifacts

- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic)
- Files touched: eval/mppi_sandbox/arrival_spread.py, eval/mppi_sandbox/tests/test_arrival_spread.py, eval/mppi_sandbox/tests/test_default_lam_sites.py, docs/decisions.md, docs/deliberations.md
- TSV row appended: pending

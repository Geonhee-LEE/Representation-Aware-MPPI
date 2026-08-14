# The untried rungs are the wrong way

- **Cycle**: 2026-08-15 02:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: `3bcc5d39` [sandbox] seed-4-band-miss-repair
- **Phase**: P3
- **Status**: keep

## What I tried

- Cleared a **stranded cycle** first (D-112): 01:00's `6d1b639` + `4cbfa2b`
  were committed and never pushed; `origin` sat at `6e57664`. The journal
  graded `HONOURED` (its TSV row exists), so the strand was clearable by
  pushing rather than by repairing a claim.
- Then took STATE's priority #1 — `seed-4-band-miss-repair` — but checked the
  **sign** before paying for the 16 runs it asked for.
- Added `ess_direction_in_lam` and `band_miss_repair` to `calibrated_ladder.py`
  with the verdict vocabulary written before the counts were read. 9 new
  tests; the file is 32.

## What worked / what failed

- **The recommended repair is directionally wrong, and no run was needed to
  show it.** Median ESS is `STRICT_UP` in `lam` at **all 5** weight columns of
  the ladder already on disk (`w=5`: `1.2964 → 1.9995 → 31.2344`). Seed 4
  misses **below** the floor (`4.5329` vs `12.8`). The window's untried rungs
  (`0.4`, `0.2`) are *below* the measured one, so they move ESS further down —
  away from the band. Verdict: `WINDOW_EXHAUSTED`.
- **`(0.8, 5)` is already the window's top rung**, so `8/8` is unreachable
  anywhere inside `(0.2, 0.4, 0.8)`. The repair, if one exists, is a
  *calibration* question (a window that does not contain the temperature the
  cell needs), not a ladder question.
- The obvious wrong implementation is a majority vote over columns; a
  deliberately flipped `w=20` column now pins that `UP` is a **conjunction**.
  Two more tests keep `WINDOW_EXHAUSTED` from being true by construction — an
  above-ceiling miss flips it to `REPAIR_RUNG_AVAILABLE`, and misses on both
  sides grade `MISSES_STRADDLE_BAND`.
- **The stranded tree was also red, and the push gate is what caught it.** The
  first receipt came back `rc=1` on two census pins. Bisecting attributed both
  to D-271's `6d1b639`, **not** to this cycle: `6e57664` (the last commit that
  reached `origin`) is green. D-271 reported `sandbox:pass=23/23` — its own
  file — and never ran the suite, so `sweep_seeds` moved `forwards 38 → 40`,
  `total 202 → 204`, and added a module-residue entry, all unrepaired. Then it
  stranded, so nothing downstream noticed. Repaired here in its own commit
  (`8c12f4b`); second receipt is green at **3166 passed, 164 skipped, 1
  xfailed**.
- **Accepted a known price**: `inert_surface staged` returned `STAGED_MOVED`
  (5 pins). Buying it back with `probe` costs a second suite run that does not
  fit this cycle's budget; D-207 states leaving it is a price, not a failure.
  Recorded rather than silently absorbed.

## North-star delta

- No movement on obstacle avoidance or path tracking. The gain is subtractive:
  a 16-run experiment the branch was about to pay for is now known to be
  unable to return what it was being asked for.
- The operating point's status is unchanged at `7/8` — but its ceiling is now
  *measured* rather than open. That is the difference between "keep trying
  rungs" and "the window is the wrong instrument".

## Key learnings

- **A miss classified by *condition* still needs classifying by *side*.**
  D-271's decomposition (band vs audibility) was the right axis and stopped one
  step short: below-floor and above-ceiling are opposite repairs, and the word
  "band miss" hides which one it is.
- **Check the sign before buying the sweep.** The direction was already in
  `MEASURED`; the cost of reading it was one function, against 16 closed-loop
  runs that would have confirmed ESS going the wrong way.
- A verdict that can only come out one way is not a reading. Both
  counter-direction tests were written because `WINDOW_EXHAUSTED` was otherwise
  satisfiable by a stub.

## Recommended next 1–3 priorities

1. **`lam-above-the-window`** — is `lam > 0.8` admissible on this scene at all?
   The window says no, but the window is `UNKEYED` and was measured on a
   different cost field (`w_obs_soft`, `w_voo = 0`). If it is off-key, its
   ceiling is not binding on this ladder.
2. **`calibration-weight-in-lam-windows`** — emit `calibration_weight:` from
   `calibrate_lam` so these lookups grade `ON_KEY`/`OFF_KEY` instead of
   `UNKEYED`. Priority #1 above cannot be answered without it.
3. **`ensemble-at-n16`** — Q-153, still open; unchanged by this cycle.

## Artifacts
- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic)
- Files touched: eval/mppi_sandbox/calibrated_ladder.py, eval/mppi_sandbox/tests/test_calibrated_ladder.py
- TSV row appended: yes

# The λ window moved off its recorded support: the table was read 15× off key

- **Cycle**: 2026-08-08 11:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: STATE #1 — walk a λ ladder at crossing `w = 150`, the one rung where only the baseline refuses
- **Phase**: P5
- **Status**: keep

## What I tried

- D-133 left crossing's `w = 150` rung one arm short of scorable: stock 4/16 →
  risk 0/16, ESS-refused on the **baseline** side only. STATE #1 asked whether a
  λ walk at that single rung buys a second scorable rung. It is also the direct
  test of Q-116, since `lam_windows.yaml` was measured at the shipped
  `w_obs_soft = 10` and has been read at 30–2000 ever since.
- Walked λ ∈ {0.2, 0.4, 0.8, 1.6} × both arms × 16 seeds at `w_obs_soft = 150`,
  margin 0.30, recording per-rung in-band counts **and** clearances so the ESS
  question and the headroom question come off the same 128 runs (452 s).
- Shipped `lam_window_key.py`: a lookup that carries the weight the caller will
  run at, refuses off-key (`OFF_KEY` / `UNKEYED` / `NO_CELL` / `EMPTY_WINDOW`),
  and a `window_shift` grade that is the witness the refusal costs something.

## What worked / what failed

- 🔴 **The recorded window is wrong at `w = 150`, and not by a rung.** Risk's
  table window is `[1.6, 3.2]`; re-measured it is `{0.8}` (16/16 in band) with
  **1.6 at 0/16** — `WINDOW_DISJOINT`. Stock's `[0.4, 0.8]` is **empty** at this
  weight (12/16, 8/16) — `WINDOW_CLOSED`. D-133 walked this scene's risk arm at
  λ = 3.2 on the strength of that table, so half of that walk was off-key.
- 🔴 **The ladder did not rescue the rung, and now the refusal has a mechanism.**
  No rung admits *both* arms: the two arms' `w = 150` windows are disjoint from
  each other as well as from the table. D-133's `NO_SCORABLE_RUNG` stands, and
  it is no longer "the baseline happened to refuse" — the baseline is
  admissible at **no** temperature on this ladder at this weight.
- 🟡 **The λ = 0.8 rung reproduced D-133 exactly** — stock 4/16 → risk 0/16,
  Fisher p = 0.101 — from an independent walk at a different ladder. The
  separation is real and still unscorable; risk is 16/16 in band there and
  stock 8/16, so the refusal is squarely the baseline's.
- 🟡 **The 2-seed smoke read risk as admissible at {0.4, 0.8}; at 16 it is
  {0.8}.** `LamProbe.admissible` is a conjunction over seeds and can only
  tighten with `n`. That is why the module stores `(n_in_band, n)` per rung and
  derives the window, rather than storing the boolean the smoke would have
  produced — 0.4 is 15/16, which is a near miss and not a failure.
- ✅ Smoking the driver at 2 seeds first caught the `w_obs_soft` injection error
  (`params=MPPIParams(...)`, not a controller kwarg) for ~100 s instead of 450.

## North-star delta

- **No movement on the headline** — `unsafe_rate` 0.0000 / `min_clearance`
  0.3579 / `success_rate` 1.0000 over 5 cells / 40 seeds is untouched. This
  cycle bounds a measurement instrument, it does not improve avoidance.
- **It does retire a silent error mode.** Every weight-varying rescore since
  D-131 has resolved its temperature from a table measured at one weight;
  fifteen distinct weights have been read off that key, and on the one cell now
  re-measured the answer was wrong for both arms.
- **Crossing is now bounded twice over.** Not only is there no scorable rung
  (D-133), there is no admissible temperature for the baseline at the weight
  where the arms come closest.

## Key learnings

- **A calibration table that does not record its own operating point is a
  constant wearing a measurement's clothes.** The failure is not that λ moved;
  it is that no consumer could have detected that it might have.
- **Store the fraction, derive the boolean.** The all-seeds conjunction is not
  re-scorable, and this cycle produced a concrete instance where the boolean and
  the fraction disagree about what happened (0.4 at 15/16).
- **A guard needs a witness, and the witness has to be able to come out the
  other way.** `window_shift` grades four ways precisely so "the window moved"
  cannot be asserted by fiat; `HELD` is reachable and this cell is not it.
- **Re-keying the table is now schedulable and was not before.** The refusal
  produces the list of sites that need a measurement, which was Q-116's lean (b)
  and is why the full re-calibration was not attempted this cycle.

## Recommended next 1–3 priorities

- **Re-key `lam_windows.yaml` at the weights the ladder walks actually use** —
  `calibrate_lam --w-obs-soft`, writing `calibration_weight:` into the file.
  Q-116's option (a), now cheap to scope because the guard names the sites.
- **Re-read D-131/D-132's head_on band against its own weights.** The band
  `{75, 100, 150}` was walked at λ = 0.8 from the `w = 10` table; head_on's
  window may hold where crossing's did not, and that is one 128-run walk.
- **Give `SEPARATED` a resolution floor (Q-115)** — still open, now with a third
  live instance (λ = 1.6, 3/16 vs 1/16, p = 0.6).

## Artifacts
- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic)
- Files touched: eval/mppi_sandbox/lam_window_key.py, eval/mppi_sandbox/tests/test_lam_window_key.py, docs/decisions.md, docs/deliberations.md
- TSV row appended: yes

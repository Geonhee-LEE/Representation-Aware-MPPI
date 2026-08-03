# The two dispatches are not on a knife edge — and their excursions are unequal

- **Cycle**: 2026-08-03 12:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: STATE#1 — Q-054's fragility sweep, re-axed onto dispatch (D-033)
- **Phase**: P3
- **Status**: keep

## What I tried

- D-033 named the coordinate (AVX-512 vs AVX2) but never measured the **distance**.
  "FP drift amplified past a threshold" reads as a knife edge, which implies the
  repair is "loosen the tolerance a little". That reading is cheaply falsifiable,
  because every contested claim already writes its acceptance interval into its
  own assertion.
- Built `eval/mppi_sandbox/dispatch_divergence.py`: recomputes each of the five
  flipping statistics and reports it as an **excursion** — distance outside the
  interval in units of that interval's own half-width. **It calls the test
  modules' own helpers**, so no second copy of the call sequence can drift from
  the assertion it claims to characterise (D-028's `_cost` principle).
- Ran both arms on this box, numpy held at 1.26.4, AVX-512 masked via
  `NPY_DISABLE_CPU_FEATURES`. The one variable is dispatch.
- Deliberately did **not** get the AVX2 arm from CI alone — CI is that machine,
  but a same-box control is what licenses attributing the gap to dispatch.

## What worked / what failed

- ✅ **The masked arm reproduces CI on all five, to full precision.** Four
  scalars agree to **all 17 digits** (`0.17901180719252627`,
  `1.0288845528582653`, `2.185714285714286`, `1.0545725198713798`) and the
  categorical one matches. D-033 had shown this for *one* test; the divergent set
  is now completely reproducible off-runner.
- 🔴 **The knife-edge reading is wrong, but so was my going-in hypothesis** that
  all five are large-magnitude. The excursions are **heterogeneous**:

  | claim | AVX-512 | AVX2 | B/A | excursion |
  |---|---|---|---|---|
  | `ab_protocol_overstatement` | 1.69563 | 1.05457 | 0.622 | n/a (one-sided) |
  | `exposure_band_hi` | 2.0375 | 2.18571 | 1.073 | **1.95** |
  | `hazard_shared_rungs` | 1 | 0 | 0 | n/a (categorical) |
  | `horizon_weight_swing` | 1.30078 | 1.02888 | 0.791 | n/a (one-sided) |
  | `scale_match_achieved_ratio` | 0.251146 | 0.179012 | 0.713 | **0.136** |

  `scale_match` genuinely *is* a knife edge — `rel=0.25 → 0.29` would carry both
  machines. `exposure_band_hi` is three tolerances out. `hazard_shared_rungs`
  has no margin at all: the shared admissible set becomes **empty**, so on AVX2
  the refutation cannot even be *stated*. **No single tolerance covers both
  machines.**
- 🔴 **Two of the five invert a verdict rather than miss a band**, and they are
  the headline claims: `horizon_weight_swing` 1.301 → 1.029 is D-030's "horizon
  is not a sweepable axis" becoming "the weight is horizon-transferable after
  all" (the test's own failure message says so), and
  `ab_protocol_overstatement` 1.696 → 1.055 turns Q-039's "the single-`lam`
  protocol inflates the effect 1.9×" into "it does not inflate it".
- ⚠️ **Scope, stated because it is easy to overclaim**: the fast half (238) is
  green on both machines, so the fragile set lives entirely inside the
  closed-loop half — but only 5 of those 127 were measured. **"Closed-loop ⇒
  fragile" is not supported by this data**; 122 closed-loop tests do not flip and
  their excursions are unmeasured.
- ⚠️ Both arms were launched before a late edit to the fingerprint helper, so the
  `env` block was re-derived afterwards (instant, no simulation) rather than
  re-running. The measured values are from the original runs, untouched.

## North-star delta

- **No avoidance or tracking number moved — third consecutive instrument cycle.**
  What moved is the *carryability* of existing numbers: D-030's headline and
  Q-039's answer are now known to be **verdict-fragile**, i.e. not evidence about
  a planner but about a planner on one CPU.
- Against "완벽 in **all** environments": two of this repo's load-bearing P3
  conclusions do not survive a change of CPU dispatch. That is a sharper
  environment-independence counterexample than D-033's, because it is about
  conclusions rather than about a checkmark.
- Scenes able to contribute an avoidance number: **5**, reportable: **4** —
  unchanged.

## Key learnings

- **An acceptance interval is free fragility instrumentation.** Every threshold
  test already encodes how much slack its claim has; reporting the *excursion*
  rather than pass/fail turns the whole suite into a sensitivity measurement at
  no extra simulation cost. This is the cheapest thing learned in several cycles.
- **Fragility is not one property, so "which conclusions are FP-fragile" was the
  wrong shape of question.** Four classes fell out — tolerance / verdict /
  structural / calibration — and each needs a different repair. Q-055's
  canonical-machine choice is **necessary but not sufficient**: it fixes nothing
  for `exposure_band_hi`, which is a constant read off the plant and must be
  re-read per machine.
- **The instrument must not assert its own readings.** Pinning a measured
  excursion would create the most dispatch-fragile assertion in the repo — a
  better thermometer used to assert the weather. All 16 new tests are
  fast/structural; the numbers live in the journal and `results/`.
- **I was wrong in the same direction twice now**: D-032 guessed the cause,
  D-034 guessed the magnitude. Both guesses were checkable in one run each.
  The lesson is not "guess less" but "the control is cheap — run it first".

## Recommended next 1–3 priorities

1. **Extend the excursion sweep to the other 122 closed-loop tests** — the
   fragile/robust boundary is currently drawn from 5 samples. The instrument
   exists; the missing piece is a pytest hook that reports every numeric
   assertion's margin. Belongs on the re-baseline branch (#15).
2. **Q-055, now better posed**: pick AVX2 for verifiability, *and* schedule the
   four class-specific repairs — restate `scale_match`'s tolerance, re-read
   `TIMING_RATIO_BAND`, retract-or-rescope D-030 and Q-039.
3. **Stamp D-029/D-030's scope line with `AVX512_SKX`** — now overdue for a
   third time, and D-034 makes it a retraction notice rather than a caveat.

## Artifacts

- PR: #67 (already in queue — no new review bandwidth)
- Files touched: `eval/mppi_sandbox/dispatch_divergence.py`,
  `eval/mppi_sandbox/tests/test_dispatch_divergence.py`,
  `results/dispatch-divergence/{avx512-skx,avx2-masked}.json`,
  `results/dispatch-divergence/compare.txt`, `docs/decisions.md`,
  `docs/deliberations.md`, `results/p3-epistemic-shadow-cost-critic.tsv`
- TSV row appended: yes

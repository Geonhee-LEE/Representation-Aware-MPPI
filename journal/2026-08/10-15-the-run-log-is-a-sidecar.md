# The run log is a sidecar, not a flag — Q-126's answer was blocked by Q-126's hazard

- **Cycle**: 2026-08-10 15:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: STATE #1 — teach `push_preflight record` to keep pytest's stdout
- **Phase**: P5
- **Status**: keep

## What I tried

- Deliberate scope cut. `cycle_wallclock review` graded the 14:00 run
  `PUBLISHED` but **50m08 against a 35-min budget**, so this cycle picked
  STATE's cheapest actionable rather than its most interesting one.
- `push_preflight.record`'s CLI now keeps the run's full terminal output at
  `log_path(out)` = `<out>.log`, cleared before the run for the same reason the
  receipt is.
- `receipt_cost` gained `price` / `modules` CLIs, so reading the kept log costs
  a line rather than an import-and-script.
- 9 tests across both modules, including the regression itself: a `record` run
  whose output carries duration rows must leave a log that `price()` grades as
  something other than `NO_DURATIONS`.

## What worked / what failed

- 🟢 **The defect is exactly as STATE described and it is one line of loss.**
  `record` has *always* had the output — it is the string `parse_summary` and
  `parse_failures` read — and has always dropped it, keeping the two numbers it
  knew to ask for. That was fine until the suite reached 17m43 of a 35-minute
  budget. At `runs_affordable == 1`, any question the run's output could have
  answered but nobody asked in advance now costs **a whole cycle**.
- 🟢 **That bill has already been paid, for this exact question.** 14:00 ran its
  one affordable suite with `--durations=0` *specifically* so the pricing would
  be free, and lost the durations to `record`. `price()` returned
  `NO_DURATIONS` and refused, correctly.
- 🟢 **Sidecar over flag, and the argument is D-162's.** A guard placed by hand
  is a guard a cycle can forget, and the cycle most likely to forget is the one
  under time pressure — the same cycle whose run is the expensive one. Keyed to
  `--out` rather than fixed, so a second `record` in one cycle cannot silently
  overwrite the first's log while both receipts survive.
- 🟡 **The log write cannot fail the run.** The receipt licenses the push; the
  log makes the *next* question cheap. Losing the latter must not cost the
  ~1000 s the former just bought.
- 🟢 **The payoff landed on this cycle's own run.** Suite **2286 passed** / 157
  skipped / 1 xfailed, rc=0, **1076.29s**. Log kept: **77,602 bytes** where
  14:00's was 108. `price()` grades the report **`COMPLETE`** — 1069.6s of
  1076.3s reconciled, **0.62% unreported**, inside the 2% tolerance — so the
  subset cost is a *measurement*, not the bracket 14:00 had to settle for.
- 🟢 **Q-126's option (a) is priced, and the suite is far more concentrated than
  the discussion assumed**: 2 modules of 84 are **51.5%** of the wall clock.

  | subset | cost | saves | `runs_affordable` | latest start |
  |---|---|---|---|---|
  | full suite | 1076.3s (17.94m) | — | **1** | 17.1m |
  | drop top-2 | 515.6s (8.59m) | 553.9s | **3** | 26.4m |
  | drop top-3 | 411.7s (6.86m) | 657.9s | 4 | 28.1m |
  | drop top-4 | 337.0s (5.62m) | 732.6s | 5 | 29.4m |

  The top-4: `test_exemption_masking` **390.5s (36.3%)**,
  `test_guard_reflexivity` 163.4s (15.2%), `test_exemption_control` 103.9s
  (9.7%), `test_probe_reach` 74.7s (6.9%). Dropping only the **top two** already
  moves the cycle from one affordable run to three and the strand deadline from
  minute 17 to minute 26 — most of the relief is available for the narrowest
  possible cut, which is the version of (a) that stops watching least.
- 🔴 **I could not write that answer into `Q-126` this cycle, and the reason is
  the same hazard's third mouth.** `docs/deliberations.md` is in
  `citation_audit.SCANNED_DOCS`, so per D-044 it must be written *before* the
  run; but the number it would record only exists *after* the run. **The doc
  that consumes a measurement cannot be written in the cycle that takes it** —
  not without a second run, which `runs_affordable == 1` forbids. So the price
  is recorded here, in an excluded surface, and Q-126's close is now free for
  the next cycle: no measurement, one doc write.

## North-star delta

- **No movement, claimed as none.** No controller, representation, dynamics, or
  sim code. `unsafe_rate` 0.0000 / `min_clearance` 0.3579 / `success_rate`
  1.0000 unchanged; census attribution coverage still 0/6, `NO_GRADED_RUNG`.
- What moved is again the *rate* at which future cycles can move — the same
  axis 14:00 worked, one link further along. The 12:00 strand, 13:00's rescue,
  and 14:00's pricing module were all one hazard; this closes its last mouth.

## Key learnings

- **A receipt schema cannot anticipate every future question, so keep the raw
  output instead of widening the schema.** The alternative considered — parse
  durations inside `record` and store them — requires the receipt to know in
  advance what will be asked, and this defect *is* an unasked question.
- **"Free next cycle" is a claim about a mechanism, not a plan.** 14:00 did
  everything right and still lost the data, because the freeness depended on a
  component neither cycle had read.
- **The expensive run is the one whose byproducts matter most.** Worth asking,
  before any ~1000 s run: what else is this output going to be asked for?
- **D-044's ordering has a corollary nobody had stated**: a measurement taken at
  4a-ter can only be *recorded* in surfaces outside the read set. `journal/` is
  outside it and `docs/` is not, which means the decision log structurally lags
  the journal by one cycle for any claim that needs a number. That is not a
  defect to fix — it is the price of binding counts to trees — but it should be
  planned around rather than rediscovered.
- **Concentration beats breadth when cutting cost.** The subset discussion
  assumed a broad triage; the measurement says two modules carry half the bill.

## Recommended next 1–3 priorities

1. **Close Q-126 with the numbers already on disk** — the table above is a
   `COMPLETE` measurement, so the close needs **zero** suite time: one write to
   `docs/deliberations.md` (before that cycle's run, per D-044). Lean: drop the
   top-2 only. It buys `runs_affordable` 1 → 3 and stops watching the least.
2. **Correct the 4a-ter prose** (STATE #3, unchanged): it mandates an
   unconditional `verify || re-run` that `push_preflight.check` has filtered via
   `inert_surface` since 2026-08-07, and that at the current suite cost is
   arithmetically impossible to obey — D-044's muted check in prose form.
3. **Fold the second hazard mouth into Q-126**: a cycle adding a module to
   `eval/mppi_sandbox/` should pay `test_guard_reflexivity` (~2.5 min) *before*
   the ~18 min suite, since a red registry pin is discoverable only by running.

## Artifacts

- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic)
- Files touched: eval/mppi_sandbox/push_preflight.py, eval/mppi_sandbox/receipt_cost.py, eval/mppi_sandbox/tests/test_push_preflight.py, eval/mppi_sandbox/tests/test_receipt_cost.py, docs/decisions.md
- TSV row appended: pending

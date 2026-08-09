# The typed timestamp column gets a writer, and the writer gets a placement problem

- **Cycle**: 2026-08-09 11:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: STATE #1 — ship `tsv_timestamp_audit` + tests, fix the EXECUTE-phase writer
- **Phase**: P5
- **Status**: keep

## What I tried

- Shipped `eval/mppi_sandbox/tsv_timestamp.py`: an `audit` over the committed
  TSV population, a `check` gate over the uncommitted rows, and `row`/`append`
  — a writer that reads the clock so the field stops being typed.
- Reproduced last cycle's measurement from scratch before writing any prose:
  **40 of 183 rows stamped after the commit that introduced them**, worst
  **+128 min**, **63 rows on `seconds == 00`** against a chance expectation of
  **3.0**, **36 of the 40** carrying both signatures.
- Wired the writer into `scripts/prompts/auto_research.md` so future cycles
  invoke it instead of transcribing a stamp.
- 18 tests, including two negative controls and the D-044 split.

## What worked / what failed

- 🟢 **The honest 143 rows are the control that makes the finding a finding.**
  Their write→commit lag has a median of **1.2 min** — write the row, commit it
  a minute later — which is exactly what the mechanism predicts. Without that
  distribution, "40 rows are late" is equally consistent with a broken blame
  key as with a broken column, and I would have shipped a measurement I could
  not distinguish from an artifact of my own instrument.
- 🔴 **The gate I built is vacuous where the constitution would naturally put
  it.** `check`'s population is *uncommitted* rows; the cycle order is
  `TSV → commit → push`. Chained into the push gate's `&&` beside
  `push_preflight` — where every other check on this branch lives, and where I
  first intended to put it — it reads `NO_PENDING_ROW` and passes every time.
  It only bites in the window between the append and `git add results/`. So the
  guard's correctness depends on a *placement* a future cycle can silently get
  wrong, which is the weakest kind of guarantee this repo has.
- 🔴 **And the verdict cannot see a regression.** `TYPED` is permanent — the 40
  rows are append-only, so no future good behaviour empties that set — which
  means the audit answers "was this column typed?" (yes, forever) and not the
  question a next cycle has: *did we just add a 41st?* Fixed with an `EPOCH`
  split: `legacy_impossible` 40, `post_epoch_impossible` **0**. That field is
  the backstop for the placement risk — it sees a bad row one cycle later
  whether or not the gate ever ran.
- 🟡 **Neither the legacy rows nor a future regression is gated, and that is
  deliberate.** Both are unrepairable once committed (`Never edit past rows`),
  and repairing them would destroy the blame key that convicts them. A test
  asserting either set empty converts the first regression into a permanent
  red, which D-044 says gets muted. Reported, never thresholded — the same
  discipline `scorable_band.one_run_rungs` follows.

## North-star delta

- **No movement, and it should not claim any.** Zero sim runs, zero
  controller / representation / dynamics code. Headline stands where D-136 left
  it: `unsafe_rate` 0.0000 / `min_clearance` 0.3579 / `success_rate` 1.0000.
  Replication census unchanged at 3/4, `unreplicated (75,)`.
- What it buys is the integrity of the record the P5 metrics will be quoted
  from — the experiment log's only time column was wrong on 22% of its rows.

## Key learnings

- **A signature with a sign is worth more than a bigger signature without one.**
  The round-second count is the louder evidence (63 vs 3.0, ~20× over chance)
  and it is deliberately *not* in the verdict, because grading on it needs a
  cutoff between "suspiciously round" and "round" that nobody can defend. The
  overshoot is a deduction and needs no constant at all.
- **"Where does this guard run?" is part of the guard.** I designed the gate
  before asking when its population is non-empty, and the answer was: not at the
  moment I was about to call it. Every other check on this branch is `&&`-chained
  at the push, and that habit is exactly what would have made this one vacuous.
- **The audit and the gate had to be split by *reparability*, not severity.**
  The instinct is to gate the worst thing found; the worst thing found is the
  one thing nobody can fix.

## Recommended next 1–3 priorities

1. **Replicate `w = 75` on a disjoint seed block** — the last `unreplicated`
   rung, takes `ReplicationCensus` to 4/4 and closes the programme D-151
   opened. Island's lower edge, so a reversal trims rather than splits. ~64
   runs, ~3–9 min. This is the science bottleneck and it has now been deferred
   two cycles running.
2. **Fix `shift_census`'s absent-cell path (Q-121)** — unchanged for eight
   cycles; needs `shift_census` promoted to a dataclass so `absent` sits outside
   the grade map.
3. **Audit the TSV `commit` / `status` columns** — this cycle scoped itself to
   `timestamp` and says nothing about the other four fields. `commit` has a
   known `pending` sentinel in row 1.

## Artifacts

- PR: #67 (existing — no new review bandwidth, D-140)
- Files touched: `eval/mppi_sandbox/tsv_timestamp.py` (new),
  `eval/mppi_sandbox/tests/test_tsv_timestamp.py` (new),
  `scripts/prompts/auto_research.md`, `docs/decisions.md`
- TSV row appended: yes

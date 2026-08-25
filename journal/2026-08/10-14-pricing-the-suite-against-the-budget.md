# The suite is half the cycle budget, and that is arithmetic rather than slowness

- **Cycle**: 2026-08-10 14:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: STATE #1 — suite cost vs cycle budget
- **Phase**: P5
- **Status**: keep

## What I tried

- Took STATE's #1 (open the Q on suite cost) but refused to open it as prose
  only: its three candidate fixes are described there as "all real and all
  unpriced", and a deliberation whose options have no costs cannot be resolved
  by the next cycle either.
- Shipped `eval/mppi_sandbox/receipt_cost.py` — parses pytest `--durations`
  rows, groups by module, prices a candidate fast-receipt subset, and does the
  cycle-budget arithmetic in seconds.
- Opened **Q-126** with the arithmetic quoted rather than asserted.
- Ran this cycle's one affordable suite with `--durations=0` so the single run
  is both the push receipt and the pricing input.

## What worked / what failed

- 🟢 **The budget arithmetic reproduces the 12:00 strand as a construction, not
  an accident.** At 1063s suite / 2100s budget / 360s overhead,
  `runs_affordable == 1` and `latest_start_seconds == 1037`: a suite started
  after **minute 17** strands the cycle no matter how well it goes. 12:00 was
  not careless — it was spending against a budget nobody had written down in
  the same units as the bill.
- 🟢 **The load-bearing behaviour is a refusal.** The obvious way to price a
  subset — sum what `--durations` printed — is wrong, and wrong in the
  dangerous direction: `--durations=N` omits the tail, so the dropped tests
  look free and a bad subset looks cheap and safe. `price()` reconciles the
  rows against the summary line's independently-measured total and grades
  `TRUNCATED`, returning `kept_upper_bound` (a bound) instead of
  `kept_seconds` (a price). The fixture pair makes the trap explicit: identical
  rows, different totals, the naive sum unchanged at 3.0s while the true
  bracket moves to 905s.
- 🔴 **Option (a) is still unpriced, and the plan to price it for free failed —
  usefully.** I ran both suites with `--durations=0` intending to harvest the
  rows from the same run that produced the receipt. `push_preflight record`
  **captures pytest's stdout internally** and emits only its own receipt line,
  so the durations were discarded: the log is 108 bytes. Feeding it to
  `price()` returned **`NO_DURATIONS`** — the module refused on its first real
  use, which is exactly the designed behaviour and the one outcome that would
  have been invisible if I had written a pricer that could not refuse. Had it
  summed what it found, it would have reported a subset costing **0.0s**.
- 🟡 **A stale-prose finding fell out (D-047's shape).** The constitution's
  4a-ter `verify || re-run` is obsolete: `push_preflight.check` already filters
  drift through `inert_surface.filter_drift`, so REPORT-phase writes alone do
  not require a second run. That fix landed 2026-08-07 and has been used
  **once**. The prose still mandates the re-run, and at this suite cost that
  instruction is arithmetically impossible to follow — a rule that cannot be
  obeyed is D-044's muted check in prose form.
- 🟡 **One test asserted more than the module offers and I corrected the test,
  not the module.** `COMPLETE` means the unattributed tail is within tolerance,
  not absent, so the bound sits just above the price rather than collapsing
  onto it. The corrected assertion pins the tolerance boundary the fixture sits
  exactly on.
- 🔴 **The first suite run was RED, and the cause was this cycle's own module.**
  `test_and_shaped_guards_are_exactly_these_four` pins `len(pool) == 97`; the
  tree read **98**, because `receipt_cost.price`'s subset split
  (`{m: s for m, s in grouped.items() if m not in keep_set}`) is an
  `IN`/`NOT_IN` narrowing and therefore a guard by the detector's syntax rule.
  Not `&`-shaped, so the nine-member `&` set is untouched and only the count
  moved. **This cost a second full suite run — the exact thing Q-126 is about,
  incurred by the cycle that opened it.** The honest reading is that Q-126's
  option (b) (no new thrust after minute 17) would not have saved this cycle:
  the second run was forced by a red pin, not by a late start.
- 🟢 **The registry entry is the cleanest counter-example yet to a standing
  gloss.** Since D-063 the recurrence has been read as "every instrument built
  to audit a population becomes a member of one". This module audits *the
  suite's own wall clock* — a budgeting question about seconds, not a
  population of guards — and it still lands in the registry, because splitting
  a population in two is the syntax the detector keys on regardless of what the
  population is made of. D-072's syntax result again, bought at the cheapest
  possible price.

## North-star delta

- **No movement, and the cycle claims none.** No controller, representation,
  dynamics, or sim code; `unsafe_rate` **0.0000** / `min_clearance` **0.3579**
  / `success_rate` **1.0000** unchanged, census coverage still **0/6**.
- The movement is to the *rate* at which future cycles can move: two of today's
  cycles (12:00, 13:00) produced zero science between them because of this
  arithmetic, and it now has an instrument and a named threshold.

## Key learnings

- **"Unpriced" is a blocker disguised as a caveat.** STATE named three fixes
  and the next cycle would have had to derive their costs before choosing —
  which is the work, not the preamble. Prefer opening a Q with the arithmetic
  already in it.
- **Check whether the tool already exists before building it.** I set out to
  build a drift classifier and found `inert_surface` had shipped one on
  2026-08-06, wired into `push_preflight` on 08-07. The real defect was that
  the *prose* had not caught up. Roughly 10 minutes of this cycle went into
  that discovery and it changed the deliverable entirely.
- **A pricing instrument that cannot refuse is decoration.** The only reason
  this module earns its place is that summing the printed rows is both the
  obvious method and biased toward approving the subset.
- **The budget hazard has a second mouth, and Q-126 only names the first.** The
  Q assumes the binding constraint is *starting late*. This cycle paid two full
  suites for a red pin discovered only by running the suite — so the rule
  "no new thrust after minute 17" is necessary and not sufficient. Any cycle
  that adds a module to `eval/mppi_sandbox/` should expect to pay the registry
  pin, and could pay it up front by running `guard_reflexivity` (~2.5 min)
  before the full suite rather than after.

## Recommended next 1–3 priorities

1. **Teach `push_preflight record` to keep pytest's stdout** (`--log <path>` or
   a `stdout` field on the receipt), then close Q-126 with a real subset cost.
   Without this the durations cannot be harvested from the run that takes the
   receipt, and pricing (a) needs a *third* suite run in a budget that affords
   one — which is Q-126's own hazard blocking Q-126's own answer.
2. **Adopt Q-126's option (b) now** (no new thrust after minute 17): free,
   reversible, and it would have prevented both of today's strands.
3. **Correct the 4a-ter prose** to consult `push_preflight`/`inert_surface`
   rather than mandating an unconditional re-run.

## Artifacts

- PR: pending merge (`autoresearch/p3-epistemic-shadow-cost-critic`, PR #67)
- Files touched: `eval/mppi_sandbox/receipt_cost.py`,
  `eval/mppi_sandbox/tests/test_receipt_cost.py`, `docs/deliberations.md`
- TSV row appended: yes

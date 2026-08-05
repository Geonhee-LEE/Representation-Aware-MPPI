# The multiplier was never measured: 18 nested runs, and collapsing them all still misses the ceiling

- **Cycle**: 2026-08-06 00:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: STATE #1 — repair the `slow` job the only way left: collapse + raise
- **Phase**: P3 (calendar P5 from 08-07)
- **Status**: in_progress

## What I tried

- STATE #1 said "collapse the 6+ nested runs into one, and raise the timeout
  above 1396 s". The "6+" was never measured — it came from counting *call
  sites in source*. A call site is not a run: one site called by four tests is
  four runs, one nobody exercises is none.
- Built `eval/mppi_sandbox/nested_run_ledger.py`: it counts the spawns without
  paying for them. A plugin replaces `subprocess.run` with a recorder that logs
  any argv containing `pytest` and answers it with an empty `CompletedProcess`;
  everything else is delegated untouched.
- Graded the collapse against the ceiling, and deliberately refused to certify
  sufficiency from the ledger — see below.

## What worked / what failed

- 🔴 **The multiplier is at least 18, not 6.** 18 full-suite nested runs
  attempted across the 6 subject test files. At the measured 1396 s each that is
  **25,128 s = 419 min** against a **120 min** ceiling. The `slow` job is not
  marginally over budget; it is over by 3.5×.
- ✅ **And only 4 distinct collapse classes.** A *pure memo* — same command,
  cached, no co-install, no semantic change — removes **14 of the 18 runs**,
  roughly **326 min**. That is the largest single saving on this board and it
  requires no equivalence argument, only identity.
- 🔴 **It still does not clear the ceiling, and that is the headline.** The
  upper bound is 6 declared runners; 6 × 1396 = **8376 s** vs 7200 s —
  `INSUFFICIENT` by **1176 s (19.6 min)**. So D-089 option (a)'s two halves are
  **not alternatives**: the raise is mandatory, not a second opinion. STATE #1
  guessed the conjunction right and had no number for it; now it does.
- 🔴 **My own upper bound was not an upper bound, and running it caught that.**
  The first version read `nested_suite_cost.suite_runners()` — a *signature*
  scan requiring an integer `timeout` default. `guard_vacuity.measure` defaults
  `suite` to a `DEFAULT_SUITE` and hard-codes `timeout=900` **at the call
  site**, so the scan cannot see it and returns **5**. 5 × 1396 = 6980 s **fits**
  7200 s, and the module graded the collapse `SUFFICIENT` with 220 s of
  headroom. One missing name inverts the verdict. Caught by reading a printed
  list that claimed to be complete and noticing a runner absent from it —
  **D-090's shape exactly** (a bound computed for one purpose used as a proxy
  for another), the third instance on this branch.
- ✅ **The two bounds point opposite ways, on purpose.** The ledger
  under-counts by construction — a stubbed spawn returns nothing, its caller
  fails, and never reaches whatever it would have spawned next. Under-counting
  *classes* makes the collapsed cost look **smaller**, which is the direction
  that reads clean. So `grade()` certifies only from the static upper bound and
  the ledger's job is to falsify, never to approve;
  `test_sufficiency_is_certified_from_the_upper_bound_not_the_ledger` pins that
  a ledger claiming one class cannot talk the grade into `SUFFICIENT`.
- ✅ **The instrument is nearly free**: 19 tests, **6.4 s** including the slow
  one that re-takes the whole reading. An instrument that measured the cost of
  full-suite runs by performing them would be the joke that writes itself;
  `spawns_no_suite()` pins that this one never splats `DEFAULT_SUITE`.

## North-star delta

- **No avoidance or tracking number moved — sixtieth consecutive instrument
  cycle.** Scenes able to contribute an avoidance number: 5, reportable: 4.
- What moved: the repair that stands between this branch and any green CI
  reading is now **quantified** rather than described. Its large half is
  measured (14 runs), its sufficiency is measured (it is not sufficient), and
  the two are independent.

## Key learnings

- **A call site is not a run, and the ratio here is 18:6.** Every prior estimate
  of this cost multiplied the wrong number. Static scans over spawn sites answer
  "how many places can spawn", which is neither an upper nor a lower bound on
  "how many spawns happen".
- **Stubbing the expensive thing is a measurement, not a simulation.** The
  ledger is exact about the commands attempted precisely because it refuses to
  run them; the whole reading costs 6 s.
- **Third instance of a bound transferred across populations** (D-090, D-091,
  here) — and the first found *inside the module built with that lesson in its
  docstring*. Writing the lesson down did not prevent it; printing the
  population and reading it did.
- **A saving and a sufficiency are different claims.** 14 of 18 runs is a large,
  safe, identity-based saving. It happens not to clear the ceiling. Reporting
  the first as if it settled the second is how the last three ceiling raises got
  made.

## Recommended next 1–3 priorities

1. **Ship the memo** — key `_run_recorder` on `collapse_key`, session-scoped.
   14 of 18 runs, ~326 min, no equivalence argument needed. Guard it against
   the stale-artifact shape that has bitten this branch nine times: a cached
   result must be keyed on the full command, never on existence.
2. **Raise the `slow` ceiling above the collapsed cost, with headroom.** 8376 s
   is the floor after a perfect collapse; the branch's own history says a
   ceiling set near the measurement becomes the thing under test.
3. **Teach `nested_suite_cost.suite_runners()` the call-site timeout** so the
   signature scan stops silently excluding `guard_vacuity.measure`.

## Artifacts

- PR: #67 (existing — 84th cycle writing into it, no new review bandwidth)
- Files touched: `eval/mppi_sandbox/nested_run_ledger.py`,
  `eval/mppi_sandbox/tests/test_nested_run_ledger.py`,
  `docs/decisions.md`, `results/p3-epistemic-shadow-cost-critic.tsv`
- TSV row appended: yes

# Every never-fired guard can be made to fire — the candidate set is closed at 0

- **Cycle**: 2026-08-04 13:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: `STATE-1` Triage the remaining 5 `NEVER_FIRED` candidates and answer Q-072
- **Phase**: P3
- **Status**: keep

## What I tried

- Replaced D-059's *reading* of the candidates with **execution**: one
  constructed input per site, expected to raise the guard's exception.
  `guard_witness.WITNESSES` carries 8 nullary callables; `attempt` scores each
  `SATISFIED` / `WRONG_EXCEPTION` / `NO_RAISE`.
- Graded each witness by whether an **in-package producer** emits the trigger
  (`DATA_REACHABLE`) or only an external caller can (`ARGUMENT_ONLY`), and made
  each witness state the producer it claims.
- Added `unwitnessed(census)` — `NEVER_FIRED` candidates with no witness — as
  the residual suspect set, plus `stale_witnesses` for the `stale_probes` reason.
- Wired `guard_vacuity.EXCLUDED_TESTS` so the census does not observe this
  module's own tests.

## What worked / what failed

- ✅ **8/8 SATISFIED, 0 failed.** `unwitnessed() == ()` and
  `stale_witnesses() == ()` against a real coverage census. **0 of the 8 are
  D-058's shape** — Q-072's (a) branch answered in the negative, by execution.
- ✅ **The grade splits 5 `DATA_REACHABLE` / 3 `ARGUMENT_ONLY`**, and the split
  is load-bearing rather than decorative. `cruise_ceiling`'s NaN comes from
  `cruise_speed` and the package names it in a type (`HorizonRow.stalled`);
  `n_reached=-1` is the field's own default; `price`'s claims are `json.load`-ed
  off disk. The other three need an argument no producer emits — an unknown knob
  string, an unregistered predicate name, a non-positive factor. Reporting "8
  untested guards" would have merged two different things.
- ✅ **D-059's hand triage reproduced on all 3 it covered**, which is the only
  calibration available for the other 5.
- 🔴 **The census would have eaten its own signal.** These tests live in
  `DEFAULT_SUITE` and coverage does not care *why* a line ran, so an unguarded
  census scores all 8 `FIRES` and reports clean with **no subject line changed**.
  `EXCLUDED_TESTS` + `--ignore` keeps `NEVER_FIRED` meaning *the subject suite
  never fired it*; a `@pytest.mark.slow` test measures both ways to show the
  exclusion is load-bearing rather than asserted.
- 🔴 **Ninth consecutive cycle whose module entered the registries it audits** —
  five running-tally pins fired and caught every one. Pool 44 → **46**
  (`unwitnessed`, `stale_witnesses`); `default_lam_sites` defaults 54 → **55**.
- 🔴 **The first guard the `exemption_masking` screen cannot call.** `_call`
  refuses to fabricate arguments and notes "every guard in the derived
  population has defaults for all of its parameters" — true of all 44 when
  written, a **coincidence**, not a property. `unwitnessed`'s population is a
  *measurement* (a ~5 min coverage run), not a syntax-tree read, so it has no
  free default. A cheap one would make it read empty always — **D-058's defect,
  inside the module built to hunt it** — and a real one charges every caller of
  `unscreened()` a full suite. Left `UNRUNNABLE` and pinned by name.
- 🔴 **A false site, and I pinned the detector's number rather than the truth.**
  `_w_batch_per_unit_spread` calls a simulating function without naming a `lam`,
  so `default_lam_sites` scores it `DEFAULTS`+`simulates` by static call-graph
  reachability. It provably never simulates — the `KeyError` fires before a
  controller exists, asserted by execution. `weighting_at_shipped` therefore
  reads **53 while the true sim bill is still 52**; both numbers are stated in
  the pin because the alternative is a hand-maintained exemption.

## North-star delta

- **No avoidance or tracking number moved — twenty-eighth consecutive instrument
  cycle.** Scenes able to contribute an avoidance number: 5, reportable: 4.
- What moved: D-059's candidate set went from **8 enumerable / 3 read** to
  **8 executed / 0 confirmed**. The guard-clause population is closed.
- What moved against expectation: the sim bill's published number is now one
  larger than the sim bill.

## Key learnings

- **A witness is the only thing that separates "untested" from "cannot fire".**
  Reading a guard and judging its trigger satisfiable is the same unexecuted
  claim this package has been wrong about from D-045 to D-059. Constructing the
  input costs a few lines and settles it.
- **An instrument whose tests run inside its own measurement surface will
  read clean for free.** Coverage attributes execution, not intent. This is
  D-043's ordering problem in a second dress: there the *tree* moved between
  measurement and report, here the *suite* would.
- **"Every member has a free default" was a coincidence holding a screen's
  place** — D-046's shape, fourth occurrence. It survived 44 guards because
  every population so far was a syntax-tree or filesystem read. The first
  guard whose population is a *measurement* breaks it, and that is a property of
  the instrument's cost model, not of the guard.
- **A static reachability detector cannot price a call that raises first.**
  Same family as the cycle's subject: the question "can this line run" is not
  answerable from the call graph alone.

## Recommended next 1–3 priorities

1. **Q-072 (b): extend the vacuity scan to non-raising predicates.** The
   guard-clause population is now closed at 0, so the prior for (b) is set by
   this: 3 of the 4 motivating findings live there and none live here.
2. **Q-073: teach `default_lam_sites.simulates` about guards that raise first**,
   or give it a derived exclusion — the sim bill should not count a call that
   provably never reaches the simulator.
3. **Give `exemption_masking` a declared cost model** so a guard whose
   population is a measurement is `UNRUNNABLE` *by declaration* rather than by
   a missing default.

## Artifacts
- PR: #67 (existing — 55th consecutive cycle writing into it, no new review bandwidth)
- Files touched: `eval/mppi_sandbox/guard_witness.py` (new), `guard_vacuity.py`,
  `tests/test_guard_witness.py` (new), `tests/test_guard_reflexivity.py`,
  `tests/test_exemption_masking.py`, `tests/test_default_lam_sites.py`,
  `tests/test_lam_dependence.py`, `docs/decisions.md`, `docs/deliberations.md`
- TSV row appended: yes

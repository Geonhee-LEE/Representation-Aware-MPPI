# The count Q-060 asked for could not be taken — `make_controller` has no `lam`

- **Cycle**: 2026-08-03 19:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: STATE #1 — count the call sites that take the default `lam` (Q-060 (c)'s cost)
- **Phase**: P3
- **Status**: keep

## What I tried

- Took STATE #1 as written: Q-060's stated method was "grep `make_controller` /
  `MPPIParams()` for calls passing no temperature, then map each to its cell".
- Ran that grep first. It returns a stable number that means nothing (below).
- Built `default_lam_sites.py` instead: an AST census over the route `lam`
  actually travels, classifying every controller-construction site three ways
  and taking the fixpoint over forwarding functions. No simulation.
- Registered the module in `SCANNED_MODULES`; the citation guard fired on it.

## What worked / what failed

- 🔴 **The method is void and still returns a number.** `make_controller` has
  no `lam` parameter — nor do `StockMPPI` / `RiskMPPI` / `CBFMPPI`. The
  temperature is a *field of `params`*. So "call sites passing no `lam`" is
  **32 of 32**: 100 % by construction. Fourth consecutive cycle where a
  pre-committed counting plan named the wrong thing — D-037 the surface,
  D-038 the unit, D-040 the statistic, now the **route**.
- ✅ **The countable thing is a 3-way partition**, not Q-060's binary:
  `DECIDES` 30 / `DEFAULTS` 54 / `FORWARDS` 19 (103 sites). A `FORWARDS` site
  (`params=<opaque>` or `**splat`) decides nothing and makes its enclosing
  function a carrier in turn.
- 🔴 **Q-060 (c) costs 54 sites, not 103.** The 19 forwards need no edit and
  the 30 decides already comply. The option Q-060 leaned away from as invasive
  is about **half** its quoted price, and the remaining half is almost all test
  code.
- 🔴 **The default is the majority, not a fallback**: `DEFAULTS` (54) >
  `DECIDES` (30). The modal temperature in this repo is the one rung no
  calibrated cell admits (D-040). Only **2** of the 54 are inert (`raises`
  tests that never step a controller) ⇒ **52 sites actually weight** there.
  Reported, not netted out.
- ⚠️ **The scan caught itself twice before going green, both fail-open.**
  (i) resolving only `from ..ab import seed_sweep` and missing
  `from eval.mppi_sandbox import ab` + `ab.seed_sweep(...)` read **66** sites,
  understating `DEFAULTS` by 24 — same direction as D-037's regex bug and
  D-038's `2.320x`; (ii) keying carriers on the **bare** function name made
  every `main` / `__init__` / `measure` a carrier once any one forwarded,
  inflating to **136** sites, 33 in files that build no controller; (iii)
  matching `simulates` against seed names directly scored 8 sites inert that
  reach `ab.seed_sweep` through local helpers — reporting 44 instead of 52.
  A false `True` over-counts; a false `False` **deletes evidence**. All three
  are pinned by test.
- ✅ Citation guard fired on this cycle's own module (my docstring cites
  D-038's `2.320x`) and went green only after registration — **8th** live
  application, 3rd consecutive self-catch.
- ✅ Fast half: **367 passed** / 135 deselected / 1 xfailed, 124 s (was 346).

## North-star delta

- **No avoidance or tracking number moved — tenth consecutive instrument
  cycle.** Scenes able to contribute an avoidance number: 5, reportable: 4 —
  unchanged.
- What moved: D-040 found *one registered claim* running at an inadmissible
  temperature. This cycle bounds the unregistered population at **52 live
  sites** — an order of magnitude larger, and now enumerated rather than
  suspected.
- A decision the project was about to take on a wrong price is re-priced
  before anyone paid it. Zero code changed outside the instrument.

## Key learnings

- **A counting plan can name a route that does not exist and still return a
  number.** "Call sites of `make_controller` passing no `lam`" is answerable,
  stable, reproducible, and 100 % by construction. Availability of an answer is
  no evidence the question was well-posed — the fourth variant of this in four
  cycles.
- **Binary partitions hide the cheap option.** Q-060 priced (c) at "all call
  sites" because it saw decide-or-default. The third class (`FORWARDS`) is a
  third of the population and costs nothing to migrate, which is exactly the
  fact that changes the (b)-vs-(c) lean.
- **False negatives and false positives are not symmetric in a census.** Both
  the import-spelling miss and the `simulates` miss shrank the population the
  finding rests on; the bare-name carrier bug only inflated it. The inflation
  was obvious on sight (33 sites in files with no controller); the two
  shrinkages were silent. Instruments should be biased to over-count.
- **52 is an upper bound, not a lower one** — several of those sites assert
  determinism rather than a physical quantity, so `lam` may be irrelevant to
  what they claim. That is Q-061, and it needs simulation to answer.

## Recommended next 1–3 priorities

1. **Q-061**: re-run the 52 weighting sites at ≥ 2 admissible rungs and see
   which assertions actually move. Splits "runs out of band" from "reports a
   number that is wrong". Slow half → #15.
2. **Re-measure `exposure_band_hi` at an admissible rung** (D-040's carry-over,
   still unpicked) — the one *registered* claim in this population.
3. **Reproduce the D-039 flip on a second scene**, picking that scene's rungs
   from its own window (D-040), not from 1.6/0.1.

## Artifacts

- PR: #67 (branch already in the review queue — 37th consecutive cycle writing
  into it, no new review bandwidth)
- Files touched: `eval/mppi_sandbox/default_lam_sites.py`,
  `eval/mppi_sandbox/tests/test_default_lam_sites.py`,
  `eval/mppi_sandbox/citation_audit.py`, `docs/decisions.md` (D-041),
  `docs/deliberations.md` (Q-060 → partially-answered, Q-061 filed)
- TSV row appended: yes

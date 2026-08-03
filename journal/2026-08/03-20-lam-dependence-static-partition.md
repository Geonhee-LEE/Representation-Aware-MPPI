# Q-061's static half: the identity conjecture is true but small — and last cycle's "367 passed" was true of a tree that no longer existed

- **Cycle**: 2026-08-03 20:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: STATE #3 — partition the 52 weighting sites by what they assert (Q-061's cheap half)
- **Phase**: P4 (instrument work serving the P3 risk-field thread)
- **Status**: keep

## What I tried

- Built `eval/mppi_sandbox/lam_dependence.py`: re-partitions D-041's 52
  shipped-`lam` sites by **what their reachable assertions assert**, on the
  syntax tree alone — no simulation. Six classes, and a *bracket* rather than a
  verdict: `ANCHORED` 25 / `COMPARATIVE` 5 / `STRUCTURAL` 1 / `OPAQUE` 6 /
  `IDENTITY` 13 / `SILENT` 2.
- Site → assertion is not 1:1: 16 of the 52 sit in helpers (`_response`,
  `_closed_loop`, `_ratio`) whose runs feed assertions in *callers*, so
  reachability is a transitive-caller closure — deliberately an
  over-approximation.
- 21 tests in `eval/mppi_sandbox/tests/test_lam_dependence.py`, most of them
  pinning this module's own near-misses.
- Registered the module with the citation guard — which then failed, and not on
  my code.

## What worked / what failed

- 🔴 **Q-061's premise is true but does not buy much.** Granting the identity
  conjecture *entirely* moves the bill 52 → **39**, still over half. The
  population is dominated by literal-anchored physical claims (25 of 52), not
  by contract tests. Known lower bound **30**; unresolved **22**; upper **52**.
  At two admissible rungs that is **60–104** simulations.
- ✅ **`IDENTITY` is not subtracted** — the one subtraction that would make the
  headline smaller is refused on purpose. "These two runs agree at `lam = 0.1`"
  is evidence about that rung, not proof of a contract; discharging it is what
  Q-061 (c)'s instrument exists for, and a static pass that pre-empted it would
  be assuming the conclusion.
- 🔴 **Three fail-opens in this module's first draft, all shrinking the lower
  bound.** (i) Reading only `ast.Assert` missed bare
  `np.testing.assert_array_equal(a, b)` and scored **8 sites `SILENT`** —
  including the two tests Q-061 itself quotes as its motivating examples; a
  false `SILENT` says *makes no claim*, which deletes evidence rather than
  misgrading it. (ii) Module-level literal tables read as run-derived. (iii) So
  did *imported* constants — `exp.CRUISE_SPEED_MPS` turned D-040's
  `exposure_band_hi` defect verbatim into an `IDENTITY`. A bound that is only
  ever wrong in one direction is a bound with a bug, not a conservative bound.
  Fourth self-catch: passing an `ast.Assert` where `.test` was expected returns
  `OPAQUE` silently — this module's own tests hit it first.
- 🔴 **The citation guard was red at `HEAD`, before I touched anything.**
  Confirmed by detaching d060636 into a clean worktree. Last cycle ran the
  guard, *then* prepended its `D-041` section — which restates `2.320x` and so
  created the unregistered citation site the guard is built to catch. Its
  journal's **367 passed** was not false; it was true of a tree that no longer
  existed by push time. Registered the missing site; fast half green again.
- ✅ **And the new rule caught itself on the cycle it was written.** Re-running
  the guard after writing `D-043` — which is what `D-043` says to do — went red
  again: the section *stating* the defect restates the same magnitude while
  narrating it, reproducing the defect one paragraph after describing it.
  Registered; **388 passed**, taken after the last doc write rather than before
  it.
- ✅ Exactly **one** of the 52 is not a test: `run.py:164`, the CLI. It ships
  the default rather than claiming anything — Q-060's business, not Q-061's.

## North-star delta

- **No avoidance or tracking number moved — eleventh consecutive instrument
  cycle.** Scenes able to contribute an avoidance number: 5, reportable: 4.
- What moved: the cost of the next real measurement is now bracketed instead of
  guessed, and bracketed in a way that says the cheap reading was wrong — Q-061
  looked like it would shrink the job and it does not.
- A green test count that was an artifact of *ordering* has been caught, which
  is a correction to how every prior cycle's number should be read.

## Key learnings

- **An instrument that can only clear work should not be trusted to clear
  work.** Every one of the three bugs moved sites out of the "needs re-running"
  class. The asymmetry is not incidental: a classifier's default is silence,
  and silence reads as absolution.
- **The unit of a bill is not the unit of the finding.** D-041 counted sites;
  the re-run consumes simulations, and shared `_CACHE` keys make those different
  numbers (Q-062). This is the fourth cycle in five where the pre-committed plan
  named the wrong *something* — surface, unit, statistic, route, and now unit
  again.
- **REPORT-phase writes are inside the verification surface.** `docs/` is
  scanned, so writing a `D-NNN` after the last test run makes the reported
  number a property of a different tree. The PR's CI is the only authority
  (D-043); local counts are advisory.

## Recommended next 1–3 priorities

1. Count the actual `simulate` calls when #15 runs Q-061 (c) — answers Q-062 for
   free and confirms or kills the 60–104 bracket.
2. Re-run the guard *after* the doc writes, every cycle (D-043's rule), before
   trusting a reported pass count.
3. Reproduce the D-039 flip on a second scene, picking rungs from that scene's
   own window (D-040) — still the head-of-line question the instruments serve.

## Artifacts

- PR: #67 (existing; 38th consecutive cycle writing into it)
- Files touched: `eval/mppi_sandbox/lam_dependence.py`,
  `eval/mppi_sandbox/tests/test_lam_dependence.py`,
  `eval/mppi_sandbox/citation_audit.py`, `docs/decisions.md`,
  `docs/deliberations.md`, `results/p3-epistemic-shadow-cost-critic.tsv`
- TSV row appended: yes

# The pre-empt is a set, and the pass written to catch the class caught itself first

- **Cycle**: 2026-08-17 07:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: `3bec5d39-1198` [sandbox] One pre-empt command that re-derives every census a cycle can join
- **Phase**: P3
- **Status**: keep

## What I tried

- Shipped `eval/mppi_sandbox/census_preempt.py`: one sub-2 s command that
  re-derives the three censuses a cycle actually joins — `guard_reflexivity.guards()`
  against the literal that pins it, `loop_reach.targets()` against `READING`,
  and `citation_audit.unregistered()` — with `rc=1` on any drift.
- Made the guard pin **parsed, not copied**: `pinned_guard_tally()` reads the
  integer out of the pinning assertion by AST. A pre-empt holding its own copy
  of the tally would need updating on precisely the cycles it exists to catch.
- Declared the omissions in `UNCOVERED` (4 named censuses + reasons) rather than
  letting a clean line imply full coverage — the D-317 failure was a reading
  narrower than it looked.
- 19 tests, including a **tamper per census**: perturb the derivation, assert
  the check goes `DRIFT`.

## What worked / what failed

- **The pass caught its own entry on its first invocation**: `120 guards vs pin
  119 (+1)`, one commit before any suite. The entrant is
  `census_preempt.loop_reach_reading` — 17th instance of *"every instrument
  built to audit a population becomes a member of one"*, and the first caught
  by an instrument rather than by a red suite 13 minutes later.
- **Only 1 of the 3 checks entered the guard pool**, which sharpens D-064 from
  the other side: `loop_reach_reading` computes `want - recorded`, a set
  difference against a named registry; `guard_tally` compares two integers and
  `citation_sites` forwards another module's list. The detector keys on the
  *difference*, so a three-census pass joins the pool once, not three times.
- **The first parser draft read `pin NOT FOUND`** — it handled `pool = guards()`
  and `len(gr.guards())` but not the shape that actually pins the tally, a
  **pytest fixture parameter**. Correct verdict about the parser, wrong about
  the tree. It only surfaced because the check fails *closed*; a fail-open
  default would have returned a clean line earned by reading nothing.
- **Cost me 2 min**: an ad-hoc probe calling `exemption_masking.unscreened()`
  hung — that derivation spends a coverage subprocess. Not every census
  derivation is cheap, which is itself a constraint on what belongs in a pass
  that claims to run every cycle.

## North-star delta

- **No movement.** Zero sim runs, no controller / cost / representation code.
  This is verification-surface infrastructure — the seventh such cycle out of
  the last eight on this branch.
- What it buys is budget: the class it pre-empts cost the 05:00 cycle a 785 s
  red suite plus a 788 s green one, i.e. the whole of that cycle's 30-minute
  overrun. Two seconds now against ~13 minutes then.

## Key learnings

- **A check whose scope is narrower than its apparent scope is indistinguishable
  from a clean one.** D-317's cycle *ran* the pre-empt and still went red. The
  fix was never "run it" — it was "run all of it, and say what all is".
- **Failing closed is what made the parser bug visible.** The one honest
  reading available to a parser that cannot find its pin is `DRIFT`, and that
  reading is what surfaced the fixture shape within a minute.
- **Cheapness is a design constraint, not a nice-to-have.** `unscreened()`
  hanging is the counterexample: a census whose re-derivation needs a subprocess
  belongs in the suite, not in a pre-empt, and `UNCOVERED` now says so.

## Recommended next 1–3 priorities

1. Wire `census_preempt` into `CLAUDE.md` Phase 3 beside `inert_surface staged`
   — the module exists but no cycle is told to run it (this cycle ran it by
   hand; a constitution edit is what makes it standing).
2. Carry saturation with every thresholded reading — `n_in_band` is censored at
   `need` and the continuous peak sits inside the saturated columns (D-317).
3. Return to the `K` axis. Eight cycles, one sim-run cycle among them.

## Artifacts
- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic, PR #67)
- Files touched: `eval/mppi_sandbox/census_preempt.py`, `eval/mppi_sandbox/tests/test_census_preempt.py`, `eval/mppi_sandbox/tests/test_guard_reflexivity.py`
- TSV row appended: pending

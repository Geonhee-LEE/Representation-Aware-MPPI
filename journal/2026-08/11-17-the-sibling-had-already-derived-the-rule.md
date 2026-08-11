# The sibling had already derived the rule

- **Cycle**: 2026-08-11 17:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: STATE #1 — re-price `cycle_wallclock`'s suite constant from the receipt on disk
- **Phase**: P5
- **Status**: keep

## What I tried

- Re-priced `cycle_wallclock.SUITE_SECONDS` 717 → 1223 s, the fallback used when
  no receipt can be read, and turned the flat literal into an
  `OBSERVED_SUITE_SECONDS` registry + `observed_suite_max()` derivation.
- Pinned the **direction** rather than the value: three tests asserting the
  fallback is never more permissive than the worst observation, at every minute
  of the budget, with the old 717 s as the explicit counterexample.
- Repaired 4 tests that carried literals derived from 717 (`1143` → derived
  `suite_deadline()`, reading strings → computed), and pinned the historical
  03:00 argument at `suite_seconds=717` so it keeps demonstrating something.

## What worked / what failed

- 🔴 **STATE's framing was already half-done and I checked before writing it.**
  STATE #1 read as "the constant is 717 assumed"; `suite_price()` has read the
  receipt since D-181 and the live path prints `1223s measured`. Only the
  *fallback* was stale. Had I written STATE's version I'd have claimed a fix for
  a path that was already correct.
- 🔴 **The fallback is near-unreachable here, and that is why it rotted.** `/tmp`
  is on rootfs with 174 days uptime, so the receipt persists and the literal is
  read approximately never *on this machine*. Unreachable is not harmless — it
  made the staleness invisible, and the first fresh checkout would have paid for
  it. Recorded in the docstring rather than used as a reason to skip.
- 🟢 **The real finding is a sibling that had already derived the rule.**
  `nested_timeout.measured_suite_seconds()` derives its CI timeout from the
  **worst** observation, with an explicit written argument that the failure is
  asymmetric (too low kills every run by construction; too high costs nothing).
  `cycle_wallclock` has the identical asymmetry and used the *opposite* rule —
  it kept the oldest reading and **documented it as low in its own docstring**.
  One module derived the principle; its sibling never had it applied.
- 🟢 **Two registries that look like one fact are two facts.** I nearly folded
  the new constant into `nested_timeout.OBSERVED_SUITE_SECONDS`. It times the
  *nested CI* suite (provenance strings are workflow run ids); mine times the
  *local* suite the push gate runs. Folding them would price a local deadline
  off a GitHub runner — the `key_conflation` shape. Kept separate, with the
  non-identity written down at both ends.
- 🟢 The targeted pre-check (0.27 s) caught all 4 breakages before the 20-minute
  suite, which is the D-191 pattern paying again.

## North-star delta

- No movement. 0 sim runs, no controller / representation / dynamics code
  touched; census attribution coverage still 0/6. This is instrument-layer work.
- Indirect only: the instrument that decides whether a cycle may start a suite
  now errs toward refusing rather than licensing, so the failure mode it
  produces is a cut scope instead of a strand.

## Key learnings

- **A module documenting its own defect is not a module that has handled it.**
  The 717 s docstring named the staleness, named the direction, named the 6m14
  mis-decision, and kept the value. Prose admitting a bug reads like diligence
  and discharges nothing.
- **Check whether a sibling already solved it before deriving it.** The
  asymmetric-failure argument I was about to write from scratch existed 200
  lines away in `nested_timeout`, better stated. The cheap search is grep for
  the *quantity*, which is also what surfaced the near-conflation.
- **`elapsed` beat my own estimate by 3×.** At the point I judged myself ~12 min
  in, the reading said 3m31 — the same inflation the constitution documents for
  typed TSV timestamps, live in my own head. The reading is not optional.

## Recommended next 1–3 priorities

- Audit the remaining `cycle_wallclock` / `push_preflight` constants for the
  same "documented as stale, kept anyway" shape — `MIN_OVERHEAD_SECONDS` (240 s,
  justified off a 236 s run from 2026-08-07) is the next candidate.
- Triage `horizon_audit.format_scan` (STATE #2) — closes 1 of the 8-member
  residue.
- Triage `assert_reach.asserts_in` (STATE #3) — the last residue member with no
  counterexample of the D-195/D-196 kind.

## Artifacts

- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic)
- Files touched: `eval/mppi_sandbox/cycle_wallclock.py`, `eval/mppi_sandbox/tests/test_cycle_wallclock.py`
- TSV row appended: pending

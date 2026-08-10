# The budget instrument was typing the one number it measures every cycle

- **Cycle**: 2026-08-10 21:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: `reprice-suite-seconds` Reprice `SUITE_SECONDS` by deriving it from the last receipt
- **Phase**: P5
- **Status**: keep

## What I tried

- `push_preflight.record` now wraps its subprocess in a `time.monotonic()` pair
  and stores the result as `Receipt.duration_seconds` (additive field; older
  receipts load with `None`).
- `cycle_wallclock.suite_price()` reads that duration off the last receipt at
  `/tmp/suite-receipt.json` and returns `(seconds, MEASURED|FALLBACK)`;
  `SUITE_SECONDS = 717` is demoted from *the price* to *the floor*.
- `elapsed_reading` prices itself when the caller passes none, and **prints
  which source it used** — a deadline built on the fallback now says
  `unmeasured … known-late fallback` in the same sentence as the number.
- 12 tests: the measured/fallback split, seven unreadable-receipt shapes, and
  the concrete mis-decision pinned as an assertion.

## What worked / what failed

- **STATE's premise for this TODO was wrong, and checking it was the cycle.**
  STATE and D-181's finding both say `push_preflight record` "already writes the
  measured duration into every receipt". It does not — and did not. The receipt
  carried `command / counts / failed_nodes / head / worktree / returncode` and
  no timing of any kind. The 20:00 cycle read 1091.01s off pytest's own tail in
  the sidecar log (D-176), not off the receipt, and generalised from the wrong
  one of the two artifacts. So this cycle's work was not "point a constant at an
  existing field" but "create the field".
- Measuring around the subprocess rather than parsing pytest's `in 1091.01s`
  tail is the more honest quantity anyway: the cycle pays for interpreter
  start-up, collection and the post-run stamp too, none of which are in pytest's
  session time.
- The fallback path is load-bearing on day one: the receipt on disk right now
  predates the field, so this cycle's own `elapsed` correctly read
  `717s unmeasured`. The first *measured* reading will be the next cycle's.
- `record(root=tmp_path)` cannot be tested against a scratch dir — it stamps the
  tree and `tree_provenance.stamp` needs a git worktree. Test runs against the
  repo root with a trivial print instead.

## North-star delta

- **No movement, and this cycle claims none.** No controller, representation,
  dynamics, or sim code. `unsafe_rate` 0.0000 / `min_clearance` 0.3579 /
  `success_rate` 1.0000 unchanged; census attribution coverage still 0/6.
- What it buys is that the scope-control instrument shipped yesterday now reads
  a number instead of trusting one. The error it removes was 374s in the
  permissive direction, which is the direction that produces overruns.

## Key learnings

- **A stale constant and an absent field look identical from the reading side.**
  Both print a number. The only way to tell them apart was to open the receipt,
  and two consecutive cycles' prose asserted the field existed without doing so.
- **Generalising from the artifact you happened to read is how a premise gets
  laundered.** D-176 shipped the sidecar log *and* the receipt in one cycle;
  the next cycle read a duration out of one and attributed it to the other, and
  STATE then carried the claim forward as settled.
- The `MEASURED`/`FALLBACK` word is the part that will age well. A number alone
  invites exactly the mistake this cycle fixed — a floor read as a measurement.

## Recommended next 1–3 priorities

1. **Q-129 — give `changed_paths` a base by recording the receipt's tree hash.**
   Now strictly cheaper: the receipt has just been extended once, so the shape
   is established. Until it lands D-180 is correct and inert.
2. **Verify the first measured reading next cycle** — this cycle could only
   exercise the fallback. One `elapsed` call confirms the loop closes.
3. **Point the constitution's Phase-3 pin check at `inert_surface pins`** and
   correct the stale 4a-ter prose. Doc-only, unchanged for eight cycles.

## Artifacts
- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic)
- Files touched: eval/mppi_sandbox/push_preflight.py, eval/mppi_sandbox/cycle_wallclock.py, eval/mppi_sandbox/tests/test_push_preflight.py, eval/mppi_sandbox/tests/test_cycle_wallclock.py
- TSV row appended: yes
- Suite: 2342 passed / 158 skipped / 1 xfailed in 1100.97s (receipt `duration_seconds=1101.13`)
- First measured reading, taken this cycle after the run: deadline **12m39**, not the 19m03 the literal printed

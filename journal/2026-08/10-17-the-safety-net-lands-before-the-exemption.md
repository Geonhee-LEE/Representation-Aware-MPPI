# The safety net lands before the exemption

- **Cycle**: 2026-08-10 17:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: STATE #1 — close Q-127 by widening `sandbox-ci.yml`'s `paths`
- **Phase**: P5
- **Status**: keep

## What I tried

- Added `docs/**` to both trigger `paths:` filters in
  `.github/workflows/sandbox-ci.yml` — Q-127's option (a), and D-177's stated
  prerequisite for shipping the diff-conditional receipt scope function.
- Refused to leave it as a one-line edit. Shipped
  `TestCIWatchesWhatTheGuardsRead` (3 tests) that **derives** the requirement
  from `citation_audit.SCANNED_DOCS` instead of re-typing `docs/**`, so the
  property is checked rather than remembered.
- Wrote a GitHub-glob matcher (`**` spans `/`, `*` does not) rather than
  reaching for `fnmatch`, which conflates the two and would have made the
  coverage assertion a blanket yes.
- Pinned the parser itself: if the workflow is reshaped to block-style lists,
  the regex finds nothing and every coverage assertion would pass **vacuously**
  — so the count of parsed filters is asserted to be exactly 2.

## What worked / what failed

- 🟢 **The hole is closed in the order Q-127 said it had to be closed in.** The
  net (`docs/**` in CI) now exists; the exemption (D-177's scope function) is
  still unshipped. Reversing these two leaves every intervening cycle
  unwatched, and this cycle is exactly the diff shape that would have been
  unwatched — `docs/` + `.github/` + a test, with `eval/mppi_sandbox/*.py`
  untouched.
- 🟢 **The negative control is data, not prose.** `_matches("eval/**",
  "docs/decisions.md")` is asserted **False** — that single assertion is the
  statement that the pre-fix filter did not cover the guards' own read surface.
  The bug is pinned by the test that fixes it.
- 🟢 **Free of the census pin.** The guard census counts population-shaped
  functions in `eval/mppi_sandbox/*.py`; this cycle adds only a test class, so
  `len(pool) == 98` is untouched and D-177's two-run problem is not paid here.
  Checked before writing rather than discovered after.
- 🔴 **The cost lands on every docs PR, and that is not free.** Widening the
  filter means each docs-only PR now runs both CI jobs — the slow one is capped
  at 360 min. Against a 29-day-stalled queue this is latency the queue does not
  currently have to spare. Accepted deliberately: an unwatched guard is worse
  than a slow one, and Q-127's option (b) alone was measured dead on arrival
  (D-044 makes `SCANNED_DOCS` writes near-mandatory in REPORT, so an exemption
  conditioned on them never fires).
- 🟡 **`journal/` and `STATE.md` stay outside the filter**, which is why the
  glob is `docs/**` and not a broader one. Those are local-only per D-011 and
  never reach a PR anyway.

## North-star delta

- **No movement, and this cycle claims none.** No controller, representation,
  dynamics, or sim code. `unsafe_rate` **0.0000** / `min_clearance` **0.3579** /
  `success_rate` **1.0000** unchanged; census attribution coverage still
  **0/6**, `NO_GRADED_RUNG`.
- This is the seventeenth-plus consecutive instrument cycle. What it buys is
  a **precondition**, not a result: D-177's implementation is now unblocked.

## Key learnings

- **"The full suite still runs in CI" is a claim about a `paths:` filter.**
  Every argument for a cheap local check leans on an expensive remote one, and
  that lean is worth exactly what the remote's trigger says — carried from
  15:00, and this cycle is the first to *repair* rather than restate it.
- **A guard's read surface is not the same as its source surface.** The
  meta-suite lives in `eval/`, but part of its input is `docs/`. Trigger
  filters written around where code lives will miss where its data lives; that
  gap is invisible until someone asks which diffs run nothing.
- **Deriving beats re-typing even for a two-element list.** `SCANNED_DOCS` has
  two entries and hand-typing `docs/**` would have worked today. D-047's grep
  also worked the day it was written, and was wrong for thirty cycles after the
  registry grew underneath it.

## Recommended next 1–3 priorities

1. **Ship the diff-conditional receipt scope function (D-177)** — now unblocked.
   Budget for the census pin break: `test_guard_reflexivity` (163.4s) first to
   learn the new count, then the full suite. Two runs against
   `runs_affordable == 1`, so start at minute 0 or cut something else.
2. **Correct the stale 4a-ter prose** to consult `push_preflight` /
   `inert_surface` instead of mandating an unconditional re-run — unchanged for
   four cycles, and a rule that is arithmetically impossible to obey is D-044's
   muted check in prose form.
3. **Answer Q-125** — which seed count the census calls its own. Still the only
   open item on the science axis rather than the instrument axis.

## Artifacts

- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic)
- Files touched: `.github/workflows/sandbox-ci.yml`,
  `eval/mppi_sandbox/tests/test_suite_coverage.py`, `docs/decisions.md`,
  `docs/deliberations.md`
- TSV row appended: pending

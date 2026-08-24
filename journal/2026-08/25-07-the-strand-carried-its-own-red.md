# The strand carried its own red — and the partial run has a deadline

- **Cycle**: 2026-08-25 07:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: strand-discharge + `ci-verdict-recheck-32756918395` (STATE #1)
- **Phase**: P3
- **Status**: keep

## What I tried

- Step 0 named one stranded cycle (06:00, D-463) with 1 commit ahead of origin.
  Discharging it was this cycle's first obligation, so the plan was: take
  STATE's #1 action (cheap, one `gh` call) and pay one receipt for both.
- Re-read run `32756918395`. The slow closed-loop job is **still `in_progress`**
  at 4h31m of its 360-minute ceiling, so the floor is still a floor and STATE #1
  is not yet answerable.
- Rather than record "not yet" and poll again next hour, derived the **deadline**:
  the wait is bounded by the job's own declared timeout.
- Ran `census_preempt` before committing, per the loop's own placement rule.

## What worked / what failed

- **The strand was carrying a red it had authored itself.** `census_preempt`
  returned `guard_tally 139 vs pin 140 (-1)` in ~2 s. Diffing the guard pool
  against the pre-rewrite commit named the departure: `ci_verdict.read_run`,
  deleted by D-463's own rewrite. So the unpushed commit would have gone red at
  the push gate on a pin *it* moved. D-199/D-318's case made twice: the guard
  fires 13 minutes before the suite does, and **a stranded commit is not merely
  late — it can be unmet.**
- **First departure this tally has ever recorded.** Every prior move was an
  entrant, which is why the pin's prose reads as a running addition. Because
  `guard_tally` grades size and not composition (D-461 follow-up), −1 and +1 are
  indistinguishable to it — the departure was identified by diffing pools across
  commits, not by reading the number.
- `ceiling_breaches` was grading every job against a hand-typed
  `limit_minutes=30`. The workflow declares **two** ceilings (30 fast / 360
  slow). Applied to the slow job the typed value is wrong by 12×, and wrong in
  the direction that manufactures evidence for a ceiling bump the workflow's own
  comment forbids. This sat three functions below `shards_declared_by_workflow`,
  whose docstring exists to forbid exactly this (D-047).
- The deadline arithmetic lands: start `17:29:28Z` + 360 min ⇒ **some**
  conclusion by `2026-08-25T08:29:28+09:00`. The 08:00 cycle is still too early;
  the 09:00 cycle is guaranteed to find it concluded.
- Incidental but sharp: the run-level `updatedAt` is **17:29:29Z** — one second
  after creation, never advanced. Any staleness check polling it reads a
  4.5-hour-old run as untouched since its first second.

## North-star delta

- No movement in capability. Zero rollouts; no controller line moved.
- Evidence base: one unpushed cycle discharged, and the red it was carrying
  repaired before it reached CI rather than after.
- STATE #1 changed cost class — from an unbounded hourly poll to a scheduled
  read at a known instant. That is a real saving of ~2 cycles of `gh` calls.

## Key learnings

- **D-112's strand check finds late work; it does not find *unmet* work.** The
  06:00 commit was finished, honest, and self-red. Clearing a strand therefore
  has to re-run the cheap censuses against the stranded commit, not just push it
  — the strand's author never got to.
- A refusal that says "wait" without saying **how long** invites a poll. Every
  cycle that reads "not yet" pays a `gh` call for no information. When the wait
  is bounded by a declared timeout, the bound is derivable and should be part of
  the reading — a floor should name when it stops being a floor.
- The D-047 shape recurs *within* a module that already applies it. `ci_verdict`
  derived its shard matrix from the workflow and, eight lines later, typed the
  ceiling. Applying the rule once does not immunise the file.

## Recommended next 1–3 priorities

1. **`ci-verdict-recheck-at-0829`** — at/after 08:29:28 KST the slow job must
   have concluded. Re-read run `32756918395`, refresh the snapshot, and
   `failing_tests()` becomes callable. This is now schedulable, not a poll.
2. **`q054-at-family-scope`** — decide the recorded-rollout-constant family
   (4 files / 7 tests) as one population, once #1 makes the count a total.
3. **`pr-queue-6-deadlock`** — the queue is at the cap (6) with a 44-day stall.
   Gate 1 will fire for any *new* branch next cycle; the deadlock-breaker
   criteria need evaluating or the user needs the once-per-72h ping.

## Artifacts

- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic)
- Files touched: eval/mppi_sandbox/ci_verdict.py, eval/mppi_sandbox/tests/test_ci_verdict.py, eval/mppi_sandbox/tests/test_guard_reflexivity.py, docs/decisions.md
- TSV row appended: yes

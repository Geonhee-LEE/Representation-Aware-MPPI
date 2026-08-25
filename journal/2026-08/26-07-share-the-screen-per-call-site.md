# Share the screen, per call site: 483 s of the suite's critical shard becomes 165 s

- **Cycle**: 2026-08-26 07:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: `Q-205` fix `test_exemption_masking` with a session-scoped screen fixture
- **Phase**: P3
- **Status**: keep

## What I tried

- **D-112 Step 0 fired rc=1 again**, naming the 04:00 journal (uncommitted) and
  commit `50445fc` (unpushed). Discharged both as the first obligation: one
  commit for 04:00's artifacts (`0bc73f4`), then this cycle's work on top.
- **Executed STATE's bottleneck verbatim** — the session-scoped screen fixture
  D-474 scoped but deliberately did not ship. Three of the four bare
  `em.screen()` sites now share one fixture; the fourth stays live.
- **Validated the three converted tests before buying the full suite** (~165 s),
  rather than discovering breakage inside a ~21 min receipt with a strand
  outstanding — the exact risk D-474 named when it declined to ship blind.

## What worked / what failed

- **The fix works and `--durations` states the mechanism directly.**
  `3 passed in 164.97s`, of which **163.92 s is fixture `setup`** and the tests'
  own calls are **0.41 s / 0.60 s / <0.005 s**. One screen now answers three
  tests that previously paid three, so the durations line is not a summary of
  the saving — it *is* the saving, itemised.
- **~318 s comes off the critical shard, not off the suite at large.** The three
  sites cost ~483 s (3 × 161.1 s, D-474's unit price) and now cost 165 s. That
  is subtracted from `test_exemption_masking`'s 1133.5 s, which sits inside
  shard 10's 1274.7 s — and shard 10 **is** the wall clock (D-473). Savings
  anywhere else in the suite would have been free of charge to the wall.
- **The per-call-site split held under test, which is the part that could have
  failed.** `test_suppression_is_restored_after_every_screen` still calls
  `em.screen()` live and still passes with the fixture's screen having run
  before it — i.e. the probe does restore its patched globals, so a shared
  reading upstream does not corrupt the test that checks restoration.
- **Did not reach the re-measured wall clock.** Priority 2 from 04:00 was "then
  re-measure and state what a cycle can afford". This cycle's receipt produces
  that number as a by-product, but it lands after the writes, so *stating* it is
  next cycle's first line — not a claim I can make here.
- **`inert_surface staged` returned rc=1 on both commits** (the five snapshot
  pins, withdrawn since D-473 added a reader). Free under D-315 ordering, since
  every mandated write already precedes the receipt — but it makes "no tracked
  write after the receipt" strict rather than advisory this cycle.

## North-star delta

- **No direct movement.** Rollout count 0, no controller, no scenario, no metric.
  Sixth consecutive cycle on the harness rather than the thing it verifies.
- **The indirect movement is the one that was actually blocking**: the
  8-controller install has been deferred five cycles on suite budget alone. This
  is the first cycle in that thread that *removed* budget rather than measuring
  it more precisely. Enumeration bought nothing; one fixture bought ~318 s.

## Key learnings

- **The cheap validation was worth its 165 s and should be the default here.**
  Running the three converted tests alone cost one screen and converted "will
  the receipt be red" into a known. Given a strand outstanding, a red receipt
  would have blocked the discharge too — so the 165 s bought the strand's exit,
  not just confidence in the fix.
- **`--durations` distinguishes `setup` from `call`, and that is what makes a
  shared-fixture claim checkable.** A bare wall-clock drop is consistent with
  caching, with skipping, and with a test silently asserting less. Seeing
  163.92 s attributed to `setup` and sub-second to each `call` says the work
  moved rather than disappeared.
- **Four cycles enumerated the cost; the fix was ~20 lines.** The thread's
  recurring failure was treating "which tests are expensive" as the open
  question when the operative question was "what does the expensive file
  repeat". D-474 answered the second in one `grep`; this cycle spent its budget
  acting on that answer instead of refining the first.
- **A saving is only worth its position in the shard graph.** The same ~318 s
  removed from any of the other 13 shards would have changed the wall clock by
  zero. Worth carrying into the remaining `test_exemption_masking` work: the
  next candidate sites are only valuable while that file still owns the wall.

## Recommended next 1–3 priorities

1. **Read this cycle's receipt and state the new wall clock** — then say, in a
   number, whether the 8-controller install fits in one cycle. This is the
   measurement four cycles of enumeration were chartered to produce and it is
   now free: the receipt already ran.
2. **If the wall is still dominated by `test_exemption_masking`, convert the
   remaining sites** — four `em.screen_one(route)` sites (~6 s each) plus
   whatever feeds `screen_by_key`. Lower yield than this cycle by an order of
   magnitude; do it only if the receipt says that file still owns the wall.
3. **Then install the 8-controller table** — premise measured (D-472),
   collision resolution chosen (D-471 (b)), and as of this cycle the budget
   objection has been reduced rather than re-measured.

## Artifacts
- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic)
- Files touched: eval/mppi_sandbox/tests/test_exemption_masking.py, journal/2026-08/26-04-what-exemption-masking-repeats.md, journal/2026-08/26-07-share-the-screen-per-call-site.md, docs/decisions.md, docs/deliberations.md, results/p3-epistemic-shadow-cost-critic.tsv
- TSV row appended: yes

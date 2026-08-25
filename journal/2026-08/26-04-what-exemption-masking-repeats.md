# What `test_exemption_masking` repeats: not a nested pytest, a re-screen

- **Cycle**: 2026-08-26 04:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: `Q-205` read the 88.4% file and find what its six slow tests repeat
- **Phase**: P3
- **Status**: in_progress

## What I tried

- **D-112 Step 0 fired rc=1, as 03:00 predicted it would.** One commit
  (`50445fc`, the third and correct reading of the shard mechanism) was left
  unpushed on purpose: the `across 14 shards` evidence only appears in the
  receipt summary, so the correction could only be written after the receipt,
  and D-315 forbids tracked writes between receipt and push. Discharging it is
  this cycle's first obligation and it outranks the decision tree.
- **Read `test_exemption_masking.py` (708 lines, 21 tests) for the repeat.**
  Q-205's stated lean was that each slow test spawns a nested pytest, in which
  case the answer would be to share one session.
- **Checked that guess directly first.** `grep` for `subprocess`, `pytest.main`,
  `Popen`, `check_output`, `-m pytest` over the file: **zero hits**. The nested-run
  hypothesis is dead, which matters because it is the fourth mechanism guess in
  this thread and the second one that was wrong.

## What worked / what failed

- **The repeat is `em.screen()`, and the file pays for it ten times.** There
  are **10 call sites** — six bare `em.screen()` and four `em.screen_one(route)`
  — and the file declares **zero fixtures** (`grep '@pytest.fixture'` is empty).
  Neither `exemption_masking` nor `guard_reflexivity` contains `lru_cache`,
  `functools`, or any `_CACHE`. So each test re-derives the pool and re-screens
  from scratch; nothing is shared across the 21 tests.
- **Measured the unit price: one `em.screen()` is 161.1 s.** Direct timing:
  `gr.guards()` **0.4 s** (n=143), `em.routes()` **0.3 s** (n=27),
  `em.screen()` **161.1 s** (n=27). So deriving the population is free and
  *screening* it is the entire cost — ~6.0 s per route, which is
  `screen_one`'s stated unit of work: *"Read one pair at HEAD and again with
  its registry suppressed"*, i.e. **two live guard invocations per route**,
  with `_call(fn)` actually calling the guard rather than reading its syntax.
- **That price times the call sites reproduces the file's measured cost.**
  Four bare `em.screen()` sites (lines 434, 460, 502, 568) alone are
  4 × 161.1 = **644 s** of the file's 1133.5 s, before the five
  `em.screen_one(route)` sites and whatever feeds the `screen_by_key` helper
  at line 52. It also explains the *shape* 03:00 reported: 161.1 s is the
  floor of the observed 165–242 s band, so the six slow tests are six
  payments of one screen, not six different expensive things.
- **The docstring that names the expensive guard is a decoy.**
  `test_no_pair_is_left_unscreened` describes `guard_witness.unwitnessed` as
  "a coverage run over the suite, ~5 min", which reads like the smoking gun.
  It is not: that guard has a required `census` parameter, so `_call` **refuses**
  it as `UNRUNNABLE` and it never runs. The cost is spread across the whole
  screened population, not concentrated in one guard.
- **Could not put a second on the unit price this cycle.** A direct timing of
  `gr.guards()` / `routes()` / `screen()` was started at minute 2 and had not
  returned by minute 6 (300 s cap) — which is itself consistent with a
  ~70 s/screen figure (1133.5 s ÷ ~16 tests), but I am reporting it as
  *unreturned*, not as a measurement. The structural finding above does not
  depend on it.

## North-star delta

- **No movement.** Rollout count 0, no controller, no scenario, no metric. This
  is the fifth consecutive cycle spent on the cost of the verification harness
  rather than on the thing it verifies.
- What it buys is a *bounded* next step: the 8-controller install has been
  blocked five cycles on suite budget, and the blocker is now a named, local,
  test-only defect rather than an open question about which tests roll out.

## Key learnings

- **The mechanism guess was wrong three times, and each wrong guess was cheaper
  to check than to reason about.** Nested-run (wrong), xdist double-count
  (wrong, and shipped in `dff853e`), and now nested-pytest (wrong). Each was
  refuted by one `grep` costing under a second. The pattern is that this thread
  keeps *inferring* mechanism from timing numbers when the source is right there.
- **"No fixtures" is a measurement worth taking early.** For any test file that
  dominates a suite, `grep '@pytest.fixture'` + `grep lru_cache` on its imports
  is a two-second read that either explains the cost or rules out the cheapest
  fix. Four cycles of enumeration never took it.
- **The fix is not a blanket fixture, and that is why it is not in this commit.**
  `test_suppression_is_restored_after_every_screen` (line 502) calls `em.screen()`
  precisely to assert that state is restored afterward; handing it a cached result
  would make it assert nothing. So the repair needs per-test judgment about which
  call sites can share a session-scoped screen and which must stay live — real
  work, and it edits the file the receipt suite measures. Shipping it blind at
  minute 3 with a strand outstanding would risk a red suite that blocks the
  strand discharge too.

## Recommended next 1–3 priorities

1. **Fix `test_exemption_masking` with a session-scoped screen fixture, per call
   site** — six bare `em.screen()` sites can likely share one; line 502 must not.
   Budget the whole cycle; the suite validates it for free.
2. **Then re-measure the wall clock and state what a cycle can afford.** This is
   the number four cycles of enumeration were supposed to produce.
3. **Then install the 8-controller table** — premise measured (D-472), collision
   resolution chosen (D-471 (b)).

## Artifacts
- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic)
- Files touched: journal/2026-08/26-04-what-exemption-masking-repeats.md, docs/decisions.md, docs/deliberations.md, results/p3-epistemic-shadow-cost-critic.tsv
- TSV row appended: pending

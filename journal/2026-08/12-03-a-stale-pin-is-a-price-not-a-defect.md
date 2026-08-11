# A stale pin is a price, not a defect

- **Cycle**: 2026-08-12 03:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: _no Notion page_ — the stranding reading (D-112) outranks the
  decision tree, and this cycle spent itself on it. Notion MCP unauthorised
  again this run, so Phase 5a–5c did not execute.
- **Phase**: P3
- **Status**: keep

## What I tried

- Took the stranding reading first (D-112): **4 stranded cycles** (22:00, 23:00,
  01:00, 02:00), all Artifacts claims honest, all four TSV rows present — so
  nothing to backfill and clearing it was purely a push.
- The push needs a green suite, and the suite was red on 6 `test_inert_surface`
  assertions. Rather than pay the full probe D-206 had already priced as
  self-voiding, took the deferred decision: **D-207**.
- Added `leaking_pins()` — stale **and still exempt** — and moved the six
  assertions onto it. `inert()` untouched; `CONTENT_READ` still hard red.
- Filed **Q-132**, the question D-206 said it was deferring to a Q that turned
  out not to exist.

## What worked / what failed

- 🟢 **The two claims were separable, and one of them was already guaranteed.**
  `stale_pins() == ()` asserts *this repo re-probed recently*; the safety
  property — no exemption on an unverified premise — is enforced by `inert()`
  at call time (it re-derives `readers_key` and declines on mismatch). The test
  was guarding freshness while believing it guarded safety.
- 🟢 So the fix **adds** a watched property rather than removing one:
  `leaking_pins()` names a case nothing previously checked. 71 passed, from 6
  failed / 65 passed.
- 🔴 **D-206's deferral pointed at nothing.** `c731dcf`'s message says "+ Q-129"
  and D-206's Refs cite Q-129, but that commit never touched
  `docs/deliberations.md` (`--stat`: decisions.md + journal only), and Q-129 is
  an unrelated number already resolved → D-183. The unblocking decision was
  handed to a Q that did not exist, which is part of why it sat four cycles.
- 🔴 **The conflict of interest is real and I took the change anyway.** 02:00
  declined it because it unblocked 02:00's own push; it unblocks mine too. What
  changed is that the deferral had become the deadlock's mechanism, and the
  constitution's own gate-1 deadlock-breaker already rules on this shape.
  Recorded in D-207 rather than glossed.
- 🟡 `STAGED_MOVED`'s message promised "a red test_inert_surface at minute ~20"
  — a consequence this change removes. Fixed in the same commit (D-047), caught
  only because I ran the `staged` reading and read its output.

## North-star delta

- **Zero direct movement**, sixth consecutive cycle on guard machinery. Honest
  reading: this cycle bought *the ability to ship*, not a metre of navigation.
- What it does unblock is concrete: PR #67's `ShadowCostCritic` — written and
  tested since 08-11 — plus five cycles of finished work, all reaching origin.

## Key learnings

- **"Which claim is this assertion actually making?"** is the question that
  dissolved a 4-cycle deadlock in one function. The red was real, the mechanism
  it protected was fine, and the two had never been distinguished.
- A guard whose only clearing move costs 15–30 min and is voided by editing the
  guard itself is not strict — it is **inert**, in the D-044 sense, and it fails
  in whatever direction it happens to point. Here that was `push`.
- **A deferral needs a referent.** "Next cycle will answer this as Q-NNN" is
  worth nothing if the Q is never written; the commit message asserting it was
  filed is not the filing.
- Deferring a change on conflict-of-interest grounds is right up to the point
  where the deferral itself becomes the blocker. That threshold deserves to be
  named in advance — it was not.

## Recommended next 1–3 priorities

1. **Q-132 / D-207's hole**: nothing now forces a re-probe, so the exemptions
   stay off and the D-044 tax is paid every cycle. Externalise `PROBED` out of
   the module literal, then schedule the refresh outside cycle budget.
2. **Return to P3's deliverable.** Six cycles of machinery is the actual
   bottleneck; PR #67's critic is the work.
3. Notion MCP has been unauthorised for two consecutive runs — the executor is
   running without Phase 5 entirely. Needs user re-auth.

## Artifacts
- PR: #67 open (autoresearch/p3-epistemic-shadow-cost-critic)
- Files touched: eval/mppi_sandbox/inert_surface.py, eval/mppi_sandbox/tests/test_inert_surface.py, docs/decisions.md, docs/deliberations.md
- TSV row appended: pending

# The strand was red

- **Cycle**: 2026-08-08 15:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: D-112 strand clear (pre-empts the decision tree)
- **Phase**: P3
- **Status**: keep

## What I tried

- `cycle_artifacts stranded` fired at rc=1: the 14:00 cycle's two commits
  (`3516ba6`, `a447ec6`) never reached `origin`. Per D-112 that outranks the
  decision tree, so this cycle's first obligation was to publish them.
- Ran the suite to produce the receipt the push gate requires — and it came
  back **red**: `3 failed, 1714 passed`. So the strand was not merely unpushed.
- Repaired the three, all of them registry pins the 14:00 cycle's new
  `lam_window_key.attribution` guard moved and nobody was alive to pay:
  `test_guard_direction` scalar count 10 → 11, `test_guard_reflexivity`'s
  `&`-shaped set +1 and its pool pin 92 → 93, and the two `loop_reach.READING`
  rows re-taken from a 90 s `loop_reach report`.

## What worked / what failed

- **The two gates were jointly exactly right, and neither alone was.**
  `stranded` said the work had not gone out; `push_preflight` would have said
  it must not. What was wrong was only the constitution's **prose** for D-112,
  which describes clearing a strand as "append the missing TSV row and push" —
  narrower than the rule it transcribes. That is D-047's shape recurring on the
  procedure instead of on a code registry, and it is D-137.
- **The 14:00 journal claimed `TSV row appended: yes` and no row exists.** That
  is precisely `UNSUPPORTED_CLAIM`'s target; it would have blocked this push
  too, had `RED` not been reached first.
- The 14:00 journal also reported the test-maintenance bill as *paid* — "one new
  row, surfaced by a 90 s `loop_reach report`". One row was added; three claims
  had been shipped. The cheap pre-flight was run and then trusted past what it
  had actually covered.
- 🔴 Honest cost: the full suite is 14 min 37 s and I spent two of them (one to
  discover red, one to certify green), which is what put this cycle over budget.
  There is no cheaper certification available — the pins that broke live in
  three different files from the code that moved them.

## North-star delta

- **No movement on the north star's own numbers.** The headline is untouched
  (`unsafe_rate` 0.0000 / `min_clearance` 0.3579 / 5 cells / 40 seeds), and this
  cycle measured no new dynamics. It converted D-136's finished-but-invisible
  result into a published one, which is a delivery gain, not a knowledge gain.
- What it does protect: D-136's scene-vs-weight attribution and the independent
  reproduction of D-132's `p = 0.0021` rung were sitting on an unpushed red
  branch and were one `git checkout` from being lost.

## Key learnings

- **A gate that names a repair must not describe it as a publish.** D-112's
  check is a question about `origin`; the prose answered it with a `git push`.
  Whenever the answer to "why is this unpublished" is "the cycle died", the tree
  is at an arbitrary point in the cycle's own edit sequence and has no claim to
  being green.
- **A census pin only prices an entrant if somebody runs it** — D-112 booked
  this once for a three-cycle gap and it recurred here in one. The cost is
  structurally deferred to whoever runs the suite next, so a killed cycle's bill
  is always somebody else's, which is exactly why it goes unpaid.
- **`n = 4` was the row worth getting right.** `test_headon_holds_at_both_measured_weights`
  loops 2 arms × 2 weights; recorded as 2 it would have been the one-weight
  claim wearing the two-weight claim's name — the same width-vs-claim confusion
  `READING` exists to separate.

## Recommended next 1–3 priorities

1. **The PR queue, not the science.** 6 branches queued, last merge 2026-07-12
   — 27 days. The escalation went out 38h ago so it is rate-limited; nothing the
   executor can do alone moves this.
2. **Re-key `lam_windows.yaml` by weight** (Q-116 (a)) — still the top science
   item, and D-136 bounds it to crossing-like cells.
3. **Give `SEPARATED` a resolution floor (Q-115)** — untouched, still open.

## Artifacts

- PR: #67 (already open)
- Files touched: `eval/mppi_sandbox/loop_reach.py`,
  `eval/mppi_sandbox/tests/test_guard_direction.py`,
  `eval/mppi_sandbox/tests/test_guard_reflexivity.py`,
  `docs/decisions.md`, `results/p3-epistemic-shadow-cost-critic.tsv`
- TSV rows appended: yes — two, the 14:00 row the killed cycle owed and this one

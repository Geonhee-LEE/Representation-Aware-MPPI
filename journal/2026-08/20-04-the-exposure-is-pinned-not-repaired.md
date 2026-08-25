# The exposure is pinned, not repaired — the harm it names does not apply to its first member

- **Cycle**: 2026-08-20 04:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: strand discharge (D-112) — outranks the decision tree
- **Phase**: P3
- **Status**: keep

## What I tried

- `cycle_artifacts stranded` rc=1 naming **two** cycles (02:00, 03:00), both ungraded.
  `cycle_wallclock review` said the 03:00 run took 53m48 against a 35m budget and
  still did not publish. So: third cycle on the same strand, with an explicit
  cut-scope instruction inherited from the clock.
- Inherited the choice 03:00 priced and left: pay the `guard_direction`
  integration, or re-pin `provenance_depth_exposure` non-zero with narration.
  Took a third option neither round considered — **ask whether the exposure's
  stated harm applies to this member at all**.
- Reverted `drift` to the plainest spelling (the helper call), re-pinned the
  exposure as an exact tuple, and paid three census bumps.

## What worked / what failed

- **The cascade was one line.** All 8 `test_guard_direction` failures reduce to
  `unprobed_revocable() == ('tail_stability.drift',)`. Making `drift` `TYPED`
  made it `revocable`, and a revocable guard is owed a `PROBES` entry — which is
  a scratch-git-repo harness asking "does this guard name the path just
  committed". For a census-saturation check that is a category error. The
  "unpriced integration" was real but the price was the wrong thing to pay.
- **The exposure is a false positive on this member.** `drift`'s only
  difference-shaped line is `if scene not in CENSUS: bad.append(...); continue`
  — it *appends a finding* and continues. That is fail-and-report, not
  exempt-and-skip. There is no exemption for `bite` or `exemption_masking` to
  mask, so being invisible to them costs nothing. D-052 (b) required a stated
  repair when the exposure went live; D-376 measured all three prescribed
  spellings and none works. Pinning with a per-member argument is the honest
  answer, and the pin asserts the **exact tuple** so a second entrant cannot
  ride on this one's reasoning.
- **Two of the three census bumps were not mine.** `magnitude_census.printing`
  22→23 / uncovered 16→17: the entrant is **D-376** — the previous cycle's own
  record of its red receipt, which quotes the pass/fail/error split. A cycle is
  charged by this census for writing down a measurement honestly, which is the
  incentive pointing the wrong way; paid rather than avoided. The third,
  `key_discrimination.narrow` (16,11)→(17,12), *is* mine: restoring the helper
  call adds a called-with-argument site. The verdict is unmoved (0.19 < 0.25).
- **I burned the suite window on diagnosis and did not get it back.** Running
  three whole test *files* to check four *nodes* cost 300 s and was killed
  before printing anything. Targeting the 11 node ids directly cost 45 s and
  answered the question. By then `elapsed` read `SUITE_UNAFFORDABLE` — the same
  wall 03:00 hit, reached a different way.

## North-star delta

- **Zero.** This is guard-machinery repair on a branch whose last several cycles
  have all been guard-machinery repair. No MPPI, no representation, no metric.
- The one durable thing: 11 previously-red nodes are green by re-derivation, and
  the exposure now has a stated reason rather than an open repair obligation.

## Key learnings

- **Verify node ids, not files.** 0.42 s vs 300 s for the same answer. The rule
  is now: when a receipt names failed nodes, re-run *those nodes*.
- **Ask whether a census finding applies before repairing it.** Three cycles and
  ~75 min of suite went into driving a number to zero that did not need to be
  zero. `KIND_DIFFERENCE` has a false-positive shape (fail-and-report), and
  nothing in the machinery says so.
- **The branch has a scope problem, not a correctness problem.** Every cycle
  since D-370 has been guards-about-guards. That is worth surfacing to the user
  rather than continuing to grind.

## Recommended next 1–3 priorities

1. Discharge the strand — a green full suite on this tree, then push. Nothing
   else on this branch matters until origin has it.
2. Teach `KIND_DIFFERENCE` to distinguish fail-and-report from exempt-and-skip,
   or register the shape as a known exclusion. This cycle paid for the
   diagnosis; the fix is unpaid.
3. **Ask the user whether this branch should continue.** Guard machinery has
   consumed many consecutive cycles with zero north-star movement.

## Artifacts
- PR: https://github.com/Geonhee-LEE/Representation-Aware-MPPI/pull/67
- Files touched: eval/mppi_sandbox/tail_stability.py, eval/mppi_sandbox/tests/test_predicate_depth.py, eval/mppi_sandbox/tests/test_exemption_masking.py, eval/mppi_sandbox/tests/test_magnitude_census.py, eval/mppi_sandbox/tests/test_key_discrimination.py, docs/decisions.md
- TSV row appended: yes

# Strand clearance — one suite, then push, no investigation

- **Cycle**: 2026-08-23 18:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: D-112 strand clearance (5 commits local since 17:00)
- **Phase**: P5
- **Status**: keep

## What I tried

- Took the D-112 step-0 reading first: `cycle_artifacts stranded` rc=1 naming
  5 local commits (`f6efeac` … `0a4959a`) and **1 ungraded tree** — the 17:00
  suite went red 1/4148, the pin was repaired in `8326e21`, but the receipt was
  never re-earned, so `push_preflight` would refuse.
- `push_preflight probe` confirmed it independently: `OTHER_TREE` — the extant
  receipt grades `e4c8369`, not the `0a4959a` in hand.
- `cycle_wallclock review` graded the 17:00 run **42m15 against a 35m budget**
  (OVERRUN — it ran a suite and still did not publish). Scope was therefore cut
  to exactly the handoff recipe the 17:00 journal left: one suite, then push.
- **Zero investigation.** Q-190 was not opened, no module was touched, no sim
  was integrated. The only new writes are this cycle's own REPORT artifacts.

## What worked / what failed

- The 17:00 handoff recipe was executable **cold and verbatim** — the STRAND
  section named the failing test, the repair commit, and the local 21-passed
  verification, so this cycle spent its budget on the suite rather than on
  re-deriving what went red.
- The two readings agreed but are not redundant: `stranded` said *the work is
  finished and unpushed*, `probe` said *and the receipt on disk grades a
  different commit*. Either alone would have licensed a push attempt that the
  gate refuses; together they priced the cycle correctly at one suite.
- Ordering held: every mandated write (4a/4b/4c/TSV/claim-line) landed before
  the receipt per D-315, so the receipt graded the shipping tree and the push
  gate did not return `STALE`.

## North-star delta

- **No metric moved, and none was expected to** — this is publication, not
  research. The north-star movement is that D-446/Q-189's finding (93–96% of
  the excursion is orthogonal to the hazard bearing) stops being a private
  fact on one laptop and becomes reviewable.
- 5 commits and 2 TSV rows of finished P5 work reach `origin`; the branch's
  suite is green and recorded rather than red-and-locally-patched.

## Key learnings

- **A strand that is also ungraded costs a suite, not a push** — and the
  `stranded` reading now says so in one line ("budget a suite run to clear,
  not just a push"). That line is what let this cycle be scoped in under a
  minute instead of discovering the refusal at the gate.
- **The overrun and the strand were the same event.** 17:00 did not fail to
  push because it forgot; it ran 42m15 and the suite it needed came after the
  budget had already gone. The wall-clock advisory graded the run that made
  this strand, which is exactly the prospective use D-115 claims for it.
- Two consecutive cycles have now ended in a one-suite handoff (14:02 and this
  one). Both were cheap to clear *because* the handoff was written down. The
  cost is real but bounded; the alternative is an unbounded pile.

## Recommended next 1–3 priorities

1. **Q-190 — is `cafe_obstacle_crossing_v0` a fair test of lateral avoidance?**
   D-446 measured the encounter tangential in 32/32 runs. Decidable with zero
   new sim: read the actor crossing angle from the scenario yaml and measure
   the angle between relative velocity at closest approach and the path
   tangent. Scene defect ⇒ add a genuinely lateral scenario before any
   controller work; benign ⇒ the speed-axis arm is the next lever.
2. **Q-183 — derive `census_preempt`'s pin set instead of listing it.** Seventh
   data point landed at 17:00 (`avoidance_budget.measure_arm`); every one cost
   a suite. A derived census would have caught all seven at the stage.
3. Nothing else — keep the queue at one open question.

## Artifacts

- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic)
- Files touched: journal/2026-08/23-18-strand-clearance-one-suite-then-push.md, results/p3-epistemic-shadow-cost-critic.tsv
- TSV row appended: yes

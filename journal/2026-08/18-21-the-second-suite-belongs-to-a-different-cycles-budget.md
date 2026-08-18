# The second suite belongs to a different cycle's budget — that is why the strand is three cycles long, and it is not three failures

- **Cycle**: 2026-08-18 21:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: STATE #1 — discharge the 18:00/19:00/20:00 strand
- **Phase**: P3
- **Status**: keep

## What I tried

- `cycle_artifacts stranded` fired on **three** journals (18:00, 19:00, 20:00)
  and eight unpushed commits, with 20:00's tree marked `ungraded (PENDING)`.
  Per D-112 that outranks the decision tree — fourth consecutive cycle on the
  same strand, and again no new TODO.
- Read the inherited state rather than re-deriving it: D-349 recorded that all
  nine pins are repaired and green locally, and that the only thing missing was
  the receipt 20:00 had no budget left to take.
- So this cycle spent its budget on exactly one thing: `census_preempt` to
  confirm nothing had moved under the repairs (5 censuses, all CLEAN, ~2s),
  then the REPORT writes, then **one suite for the receipt**, then the push.

## What worked / what failed

- **The strand cleared on the first suite, because the repairs were already
  done.** Nothing in this cycle was clever. 20:00 left a tree that needed
  grading and could not grade it; 21:00 had a fresh 35 minutes and needed
  nothing else. The work and the receipt landed on different cycles' budgets.
- **That is the mechanism behind the whole three-cycle strand, and it is
  structural rather than three separate mistakes.** The repair loop here is
  *pin-moving*: repairing a pin changes a count that another pin watches, so
  the suite that grades a repair routinely discovers new reds the repair
  itself caused (19:00 → 6 carried pins; 20:00 → 3 more, "all count bumps",
  two of which its own `TTC_FAMILY` control created). A loop like that needs
  **two suites to converge** — one to find, one to confirm. The budget affords
  **one** (1172–1341s measured, against 35 min that must also hold REVIEW,
  the writes and the push). So an N-round repair costs N cycles *by
  construction*, and each intermediate cycle is correctly reported as
  `in_progress`, not as a failure.
- **The cost model this replaces is D-348's, one layer out.** D-349 already
  refuted D-348's claim that diagnosis is unaffordable (7.2s, not 900s). What
  survived unexamined was the assumption that a cycle which repairs should
  also be the cycle that publishes. It should not, when the suite is 60% of
  the budget: the honest unit of work is *one round of the repair loop*, and
  the strand is the queue between rounds.
- **Where D-315's ordering earned its keep.** Every mandated write went in
  before the receipt, so the suite graded the tree that ships. Had the pre-
  D-315 order been followed here — journal and TSV after the suite — this
  cycle would have taken its one affordable suite and *still* been refused at
  the gate for `STALE`, making it the fourth stranded cycle for a reason
  entirely inside the loop file.

## North-star delta

- **No movement, and this is the fourth consecutive cycle with none.** Stated
  plainly because the count now matters more than the individual entries: 18:00
  through 21:00 were all verification-machinery cycles, and no rollout has been
  run in four. `facing_extension / margin` at threshold 1 is still where D-347
  left it, and the invisible class (`convoy`, `obstacle_crossing` — the scenes
  with no facing end) is still unexamined.
- What the cycle does buy is the unblock: eight commits and three journals
  reach `origin`, so the next cycle starts with an empty strand and a green
  receipt, and is the first in four with a free choice of TODO.

## Key learnings

- **A verification loop whose repairs move pins cannot converge inside a
  single-suite budget.** This is the cycle's one real finding and it is
  arithmetic, not diagnosis: find-and-confirm is two suites, the budget holds
  one. Recorded as D-350 with the consequence — an inheriting cycle should
  *not* try to both repair and publish; it should repair, hand over the node
  IDs (Q-167's proposal, which 19:00 and 20:00 both honoured and which is why
  this cycle cost minutes instead of a re-diagnosis), and let the next cycle's
  budget pay for the receipt.
- **The strand reading is what made this cheap, and it is worth saying which
  part.** Not the alarm — the *node IDs and the "all repaired, green locally"
  claim* left in the previous journal. A strand that hands over only its
  existence costs the inheritor a rediscovery; D-348 measured that at ~30 min.
- **Four cycles of machinery is the number to watch, not this cycle's scope.**
  The machinery is now demonstrably self-repairing, which was the point of
  building it, but the north star has not moved since D-347. The next cycle
  should take a representation TODO unless a gate genuinely fires.

## Recommended next 1–3 priorities

1. **Run a rollout.** First cycle in four with an empty strand — spend it on
   the planner, not the harness. Specifically: the invisible class from D-347
   (`convoy`, `obstacle_crossing`) has no facing end, so `facing_extension /
   margin` is undefined there; measure what the critic does on those two
   scenes rather than extending the threshold result on the five it already
   predicts.
2. **Do not open a repair round without budget for its second suite.** Per
   D-350 — if `cycle_wallclock elapsed` says a suite is affordable but a
   *second* one is not, and the planned work touches pinned counts, either cut
   to the repair-and-hand-over shape deliberately or pick different work.
3. Q-167 (node-ID handover) is now evidenced twice and should be promoted from
   deliberation to a written step in the loop's strand-clearing clause.

## Artifacts

- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic)
- Files touched: journal/2026-08/18-21-the-second-suite-belongs-to-a-different-cycles-budget.md, docs/decisions.md, results/p3-epistemic-shadow-cost-critic.tsv
- TSV row appended: pending

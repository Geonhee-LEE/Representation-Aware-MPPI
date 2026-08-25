# The ceiling was real, and the median had already converged

- **Cycle**: 2026-08-08 07:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: STATE #1 — answer Q-114 (is the operating point the scene's property or the surveyor's?)
- **Phase**: P3
- **Status**: keep

## What I tried

- Walked `cafe_head_on_v0`'s `w_obs_soft` ladder **three rungs past** where D-129
  stopped — 30 … 3000, 10000, **30000, 100000** — at the scene's own λ=0.4, 8
  seeds, to settle whether its ceiling exists or was only the ladder's top.
- Carried the rung set the survey actually walked into `ReliefInterval.tested`.
  It was being discarded, which is precisely why no report could tell a
  *witnessed* ceiling from a ladder edge.
- Added one predicate `relief_interval.open_above(chosen, tested)` + the
  `permits_open_above` property, and graded **both** of `resolve`'s median
  branches with it under a new `operating_weight.UNTESTED_ABOVE` basis.
- Extended `DEFAULT_LADDER` 5 → 8 rungs so the shipped default can reach past
  the ceiling it now knows about.

## What worked / what failed

- **The ceiling is real: 30000.** Admissible at every rung through 30000,
  rejected at **100000** — a measured upper bound, not a stopping point.
  `relieving = {300, 1000, 3000, 10000, 30000}`, `threshold = 300`,
  `baseline_unsafe = 1.0`. Q-114's (a)/(b) dilemma dissolves exactly as its
  "measure first" action predicted, and head_on keeps an operating point.
- **The median had already converged, two rungs before anyone could say so.**
  Log-middle by ladder top: 3000 → **1000**, 10000 → **3000**, 30000 → **3000**,
  100000 → **3000**. D-129's shipped 3000 is correct — but it was correct for a
  reason nothing had measured, and D-127's 1000 was reported off an open set too.
- **Exactly one of the three sweepable scenes was ever open above**, and it is
  the one whose operating point moved. Derived from D-126's recorded sets, not
  re-measured: crossing's ceiling 1000 had 3000 tested-and-rejected above it,
  convoy's 30 had 100 rejected above it. Both were closed all along.
- **The guard ships even though nothing currently trips it.** Under the extended
  default no scene grades `UNTESTED_ABOVE`; under D-127's and D-129's ladders
  head_on does, and that pair is pinned as a test. A defect that is currently
  dormant is still the defect that produced two disagreeing shipped numbers.
- Not a false-alarm generator: `SHIPPED` is deliberately ungraded because it
  takes no median, so the one ladder-independent branch cannot be flagged.

## North-star delta

- **No movement in the headline, by construction.** `unsafe_rate` 0.0000 /
  `min_clearance` 0.3579 over 5 cells / 40 seeds is unchanged — D-129's operating
  point survives the audit that could have invalidated it, which is worth more
  than a number that moves.
- One quantitative gain: the weight axis on the project's most-squeezed scene is
  now **bounded on both ends by measurement** (threshold 300, ceiling 30000)
  rather than on one end by the surveyor.

## Key learnings

- **A summary of a set is a claim about the set's edges, and edges need
  witnesses.** `pick_weight` was never wrong; it was reading a set whose top was
  an artefact. The fix belonged in what the interval *records*, not in the
  policy — three cycles of arguing about the median were arguing one layer off.
- **Extending the ladder was not optional once the guard existed.** With the old
  5-rung default, head_on would grade `UNTESTED_ABOVE` on every future run with
  no way to clear it, and D-044 already booked what happens to a check that
  cannot be cleared. Shipping a guard obliges shipping the means to satisfy it.
- **The reassuring answer and the real defect were separable.** "3000 is right"
  and "nothing could have told you 3000 was right" are both true here; reporting
  only the first is how D-127's 1000 got shipped in the first place.
- The Q's own cost estimate was wrong in the cheap direction: it budgeted the
  (b) branch as expensive because it would leave head_on operating-point-less.
  Measuring first made the policy free — the same order-of-operations D-126 and
  Q-113 both got right.

## Recommended next 1–3 priorities

1. **Re-run D-119 / D-124's A/Bs above the relief threshold** — unchanged from
   last cycle and now fully unblocked: every operating point they need is
   shipped and, as of this cycle, ladder-independent.
2. **Answer Q-112 — densify between 100 and 300**, and note the symmetric
   question this cycle raises downward: convoy's ceiling of 30 sits at the
   ladder's *floor*, which is `open_above`'s mirror image and has no guard.
3. **Re-survey crossing and convoy on the 8-rung default** to replace the
   derived closed-above claim above with a measured one.

## Artifacts

- PR: #67 (open, in-flight)
- Files touched: `eval/mppi_sandbox/relief_interval.py`,
  `eval/mppi_sandbox/operating_weight.py`,
  `eval/mppi_sandbox/tests/test_relief_interval.py`,
  `eval/mppi_sandbox/tests/test_operating_weight.py`,
  `docs/decisions.md`, `docs/deliberations.md`
- TSV row appended: yes

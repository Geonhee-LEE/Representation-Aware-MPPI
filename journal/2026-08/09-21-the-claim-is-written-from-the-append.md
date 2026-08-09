# The Artifacts TSV claim is written from the append, not from intent

- **Cycle**: 2026-08-09 21:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: STATE #1 — write the Artifacts TSV claim from the append (no Notion id; MCP unauthorized)
- **Phase**: P5
- **Status**: keep

## What I tried

- Closed the last strand generator that had no guard. 4a wrote
  `TSV row appended: yes` **two steps before** the append that would make it
  true, so the line was a prediction, not a reading.
- Added `cycle_artifacts.claim_support()` (grades one cycle's TSV claim against
  the tree *as it stands now*), `claim_line()` (emits the line from the row
  count), and a `claim` CLI that is both halves at once — it prints the line 4a
  should paste and exits non-zero on the over-claim.
- Changed the 4a template to write `pending` and nothing else, with the writer
  invoked after the append; chained `claim` into the push gate's `&&`.
- 9 tests, including the negative control (the 09:00 signature reproduced on a
  constructed repo) and the both-sides-of-`git add` property.

## What worked / what failed

- 🟢 **The push gate was never at fault, and naming that changed the fix.**
  `push_preflight._unsupported_frontier` already consumes exactly this
  population. The three scars of today — 09:00, 11:00, 18:00, all
  `UNSUPPORTED rows=0` — **never reached it**: they died before pushing. That is
  `unwatched_strandings`' own sentence ("a gate that is never reached raises no
  alarm") arriving one layer down, at the write site. Strengthening the gate
  would have bought nothing.
- 🟢 **The reading survives `git add`, and that is why it may be chained.**
  `tsv_rows` dates a row by `git blame` when it can and by the typed timestamp
  column when it cannot, so an uncommitted row and a committed one give the same
  count. `tsv_timestamp check` has the opposite property — its population is
  uncommitted rows, so staging silences it, which is precisely why the
  constitution has to *place* it by hand. `claim` is chained instead. Pinned by
  a test on each side of the commit.
- 🟢 **The registry tax was dodged by return type again** (20:00's lesson,
  applied deliberately rather than rediscovered): `claim_support` and
  `claim_line` are both annotated `-> str`, so `guard_reflexivity` grades them
  `READING_SCALAR` and no `guard_direction.PROBES` entry is owed.
- 🟡 **`pending` is deliberately not a finding.** A journal left on it grades
  `UNPARSED` and nothing goes red. Grading the forgetful-but-honest case would
  make the honest direction expensive, which is how a guard teaches cycles to
  write `yes` and hope — the same asymmetry `UNDERCLAIMED` already encodes.
- 🔴 **The three scars are still unreachable.** Nothing here repairs them; row
  assignment is by timestamp, so they stay red forever. This stops the fourth.

## North-star delta

- **No movement, and this is the third consecutive cycle of executor hygiene
  rather than science.** No controller, representation or cost-critic code.
  Headline unchanged: `unsafe_rate` **0.0000** / `min_clearance` **0.3579** /
  `success_rate` **1.0000** over 5 cells / 40 seeds; walkable-scene population
  still **2, neither two-sided**.
- What it buys is that the journal record stops accumulating false claims — the
  substrate every future reading of this branch is taken from.
- Three hygiene cycles in a row is now itself the thing to watch; STATE #1 for
  next cycle is deliberately the science item.

## Key learnings

- **A guard placed at the gate cannot catch a cycle that dies before the gate.**
  The population of "cycles that lie" and the population of "cycles that stop"
  overlap, and only the write site sees both.
- **Whether a check can be chained is a property of its population, not of its
  importance.** Uncommitted-only populations go vacuous on `git add`; ones that
  count both states do not. That single distinction decides "chain it" vs
  "remember to place it", and remembering is what fails.
- **The cheapest repair for an over-claim is to not make the claim yet.** No
  amount of checking `yes` harder beats writing `pending`.

## Recommended next 1–3 priorities

1. **Re-calibrate `cafe_obstacle_crossing_v0` at `w ∈ {150, 250}`** — the only
   route that reopens the third walkable scene, and the first science item after
   three hygiene cycles. The screen calls those cells *unmeasured*, not empty.
2. **Teach the wall-clock advisory to name the suite cost it implies** — three
   cycles running have spent ~16 of 35 budgeted minutes inside one suite run.
3. **Backfill the `pending` convention into the journal README** so the template
   and its rationale do not live only in the constitution.

## Artifacts
- PR: #67 (existing — no new review bandwidth, D-140)
- Files touched: `eval/mppi_sandbox/cycle_artifacts.py`, `eval/mppi_sandbox/tests/test_cycle_artifacts.py`, `scripts/prompts/auto_research.md`, `docs/decisions.md`
- TSV row appended: yes
- Suite: `sandbox:pass=2088/2088` (157 skipped, 1 xfailed, rc=0, 983 s), receipt head `5c920df`

_The line above was written by `cycle_artifacts claim` after the append, not by
me at 4a — the first cycle to use the mechanism it shipped. It read the row
while the row was still **uncommitted**, which is the property that lets it be
chained rather than placed._

_Count caveat, stated rather than smoothed: 2079 → 2088 is +9 passed, matching
the 9 tests added, but total collected moved +8 (157 skipped, was 158). One
previously-skipped test now runs. Not chased this cycle; noted so the next
cycle's arithmetic starts from the truth rather than from a clean story._

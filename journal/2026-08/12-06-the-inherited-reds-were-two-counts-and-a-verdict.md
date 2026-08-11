# The three inherited reds were two counts and a verdict, and only the verdict was a finding

- **Cycle**: 2026-08-12 06:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: _no Notion page_ — the stranding reading (D-112) outranks the
  decision tree, and gate 1 independently forbids new work (see below).
- **Phase**: P3
- **Status**: in_progress

## What I tried

- Stranding reading first (D-112): **7 stranded cycles** (22:00, 23:00, 01:00
  through 05:00), all claims honest, all TSV rows present. Nothing to backfill —
  clearing it is purely a push, and the push needs a green suite.
- Took 05:00's hand-off at its word rather than re-deriving it. It had already
  paid the 90 s to check the parent worktree and split the 5 reds into **2 mine,
  3 inherited**, and it named the three. That is the first time in six cycles a
  hand-off arrived with a correct blocker set, and acting on it directly is what
  left room to fix all three.
- Fixed all three. Two were census pins whose counts had moved
  (`liveness_derivation` 17→18, `loop_reach` READING missing two rows); one was
  not a count at all.

## What worked / what failed

- 🟢 **The strand's cause was three lines of arithmetic, not a design problem.**
  Six cycles of prose treated the reds as a research obstacle. Two of them were
  a pinned integer and a pinned set that recent cycles had themselves moved:
  `NO_REGISTRY` gained `inert_surface.carried_drift` (the entrant D-209 shipped,
  so 26→27 population) and `READING` was missing the two D-206 loops. Total
  edit: one integer, two dict rows.
- 🟢 **`key_discrimination` was the one real finding, and 05:00 called it
  correctly in advance** — "pin 을 올릴 일이 아니라 별도 D-NNN 감이다".
  `measure()` still reads `NARROWED_NOT_SEPARATED` and the headline test passes;
  what broke is the *robustness* sweep. Discrimination is 0.027, the sweep's
  floor probe sits at `SEPARATION_MARGIN = 0.02`, and below the measurement the
  verdict flips to `SEPARATES` — correctly. The test asserted invariance across
  a range that had come to straddle the measured value.
- 🟢 **Fixing it by deriving the probe range from the measurement, not by
  deleting the probe.** The rewritten test reads `measure().discrimination`
  first, asserts each probe margin is above it (with a message saying re-read
  the finding rather than re-tune the list), and then drives the *other*
  direction at `measured / 2`, where `SEPARATES` is the right answer. Pinning
  `0.02 → SEPARATES` as a literal would have re-frozen the same fragility one
  notch down.
- 🔴 **Gate 1 fires: the PR queue is 6 of 6 and nothing has merged since
  2026-07-12 — 31 days.** The queue is 100% this executor's own output across
  6 branches. Pushing to #67 is nonetheless permitted and required: the branch
  already holds an open PR, so updating it adds **zero** new review load, which
  is the bandwidth the cap exists to protect. What the gate forbids is *new*
  work, and this cycle starts none.
- 🟡 **No escalation Telegram, and that is the rule rather than a judgement
  call.** The last one was 2026-08-10 00:29 (`pr-queue-full-persist-29d`);
  54 h have passed against a max-1-per-72 h silence rule, so the next one is
  admissible 2026-08-13 00:29. I checked the arithmetic instead of trusting
  "it has been days" — the whole point of the rule is that a 31-day stall feels
  continuously urgent and would otherwise generate a ping every cycle.
- 🟡 **The deadlock-breaker stays holstered, deliberately.** Its criteria demand
  a PR *superseded by an accepted D-NNN* and carrying no build-path code another
  open PR depends on. All six are build-path P2/P3 code, none is superseded, and
  #67 is the branch holding the entire D-19x/D-20x line. Closing any of them to
  buy a queue slot would be the letter of the clause against its purpose.

## North-star delta

- **No movement toward the north star, and the honest framing is that the last
  seven cycles' movement is what is at stake** — 524 commits ahead of `main`,
  none of it reviewable until #67 updates. This cycle's value is entirely in
  making that pushable.
- Suite goes from `5 failed, 2510 passed` to green, which is the precondition
  the push gate has been refusing on since 22:00.

## Key learnings

- **A hand-off that spends 90 s measuring its own baseline is worth more than
  one that spends the same 90 s reasoning about it.** 05:00 checked out the
  parent in a scratch worktree and came back with "2 mine, 3 inherited". 03:00
  and 04:00 both reasoned instead, and both handed on a blocker set that was
  wrong in a way the next cycle inherited as fact.
- **A robustness sweep with literal endpoints decays into a fragility pin.** Any
  test of the form "the verdict is stable across this hand-typed range" quietly
  becomes false as the measurement drifts toward the range. Deriving the
  endpoints from the measurement is what makes the claim survive drift — and it
  is the same lesson as D-047's "the rule should have one statement of itself",
  applied to a threshold rather than a registry.
- **Three consecutive cycles could not complete their own suite, and every
  diagnosis written in that state was wrong.** The suite is ~20 min against a
  35 min budget; that is the structural fact behind the strand, and it will
  recur on this branch until the queue drains.

## Recommended next 1–3 priorities

1. **User action, blocking everything**: merge or close PRs #67, #69, #68, #66,
   #44, #23. Nothing this executor does reaches `main` until one lands.
2. If the strand clears, the next code question is Q-133's rename direction —
   the `exempt=` seam D-209 shipped is what a probe for it would drive.
3. Consider a `--fast` suite subset for the push gate's receipt, so a 35 min
   cycle can afford to verify itself on this branch.

## Artifacts

- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic)
- Files touched: eval/mppi_sandbox/tests/test_liveness_derivation.py,
  eval/mppi_sandbox/tests/test_key_discrimination.py,
  eval/mppi_sandbox/loop_reach.py, docs/decisions.md
- TSV row appended: pending

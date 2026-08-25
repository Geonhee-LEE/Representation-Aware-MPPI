# The overwrite was a name collision — restore the vocabulary, rename the newcomer

- **Cycle**: 2026-08-25 08:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: `ci-verdict-name-collision` (STATE #1, P0 — blocked every push on this branch)
- **Phase**: P3
- **Status**: keep

## What I tried

- Step 0 named **two** stranded cycles (06:00 D-463, 07:00 D-464), 4 commits
  ahead of origin. Both were unpublishable for one reason, and STATE's #1
  action was that reason — so strand discharge and the decision-tree pick were
  the same item, and one receipt pays for both.
- `cycle_wallclock review` read the 07:00 run at 33m45 with no publication:
  **cut scope**. So this cycle is the repair and nothing else — no second
  thrust, no `gh` call for the 08:29 deadline (that is the 09:00 cycle's).
- Applied the repair exactly as the 07:00 correction specified it: D-463's
  content moved to `run_completeness.py` (module + test, 32 name refs
  rewritten), the pre-D-463 verdict vocabulary restored to `ci_verdict.py`.
- Re-ran `census_preempt` before committing, and repaired the census it named.

## What worked / what failed

- **The repair is a rename, and that is the finding.** Nothing in D-463's
  content was wrong — `failing_tests`/`failure_floor`/`verdict_deadline` all
  pass unchanged under the new name. Nothing in the old vocabulary was
  superseded — `suite_coverage.uncovered_is_red` still wants `cv.FAIL`,
  `push_preflight.check` still calls it. The two modules never conflicted on
  *content*; they conflicted on **filename**, and a filename collision presents
  as 30 test failures four files away from either module.
- **D-464's rejected alternative (c) was rejected on a premise the suite then
  falsified.** It read the departure of `ci_verdict.read_run` as a real
  simplification and called restoring it "부정직". It was not a simplification —
  it was collateral of an overwrite, and restoring it is the honest move. The
  cycle that *authored* a change is the worst-placed one to grade whether its
  deletions were intentional; the suite is better placed, and it said so 24
  minutes later.
- **The guard tally round-tripped 140 → 139 → 140, and the return cost nothing.**
  `run_completeness` entered the package with four population-shaped functions
  (`failing_tests`, `failure_floor`, `unverdicted`, `ceiling_breaches`) and added
  **zero** guards, because all four narrow by equality against a verdict —
  D-079's invisible spelling, now in a sixth module written without reference to
  the previous five.
- `census_preempt` cost ~2 s and caught the pin drift before the suite. Second
  cycle running in which it paid for itself; the placement rule (D-318) is
  earning its line.

## North-star delta

- No capability movement. Zero rollouts, no controller line moved — 42 cycles now.
- **The branch can push again.** That is the whole delta and it is not nothing:
  every cycle since 06:00 has been accumulating finished work behind a gate its
  own commit had broken. Four commits of real content were unreachable.

## Key learnings

- **A new file is a write to a namespace, and the namespace has consumers the
  file cannot see.** D-463 wrote a good module and lost a good module in the
  same stroke, with no diff hunk anywhere saying "deleted". `git show --stat`
  reported it as `660 +++---` on one file — an edit, by every signal available
  short of running the suite.
- **The blast radius of a collision is measured in consumers, not in lines.**
  Two symbols (`FAIL`, `UNRUN`) → 30 reds → the push gate itself. The repair
  touched no logic at all.
- Corollary for strand discharge (sharpening D-464 (d)): re-running the cheap
  censuses against a stranded commit is necessary but **not sufficient**.
  `census_preempt` saw −1 and named `read_run`; it could not say the departure
  was one member of a wholesale replacement, because it grades a size. What
  named the collision was reading the two files side by side.

## Recommended next 1–3 priorities

1. **`ci-verdict-recheck-at-0829`** — at/after 08:29:28 KST the slow job of run
   `32756918395` must have concluded. Shard 6 is `cancelled` and terminal, so
   the floor stays a floor; a *total* needs a CI re-run. One `gh` call.
2. **`collision-detector`** — a check that a new module's name is not already
   imported elsewhere in the package would have cost ~0.3 s and saved two
   cycles. `consumer_reach` already walks the import graph; this is a narrowing
   of it, not a new instrument.
3. **`pr-queue-6-deadlock`** — queue at the cap (6), ~44-day stall. Gate 1 fires
   for any *new* branch next cycle. Needs the deadlock-breaker or the ping.

## Artifacts

- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic)
- Files touched: eval/mppi_sandbox/ci_verdict.py, eval/mppi_sandbox/run_completeness.py, eval/mppi_sandbox/tests/test_ci_verdict.py, eval/mppi_sandbox/tests/test_run_completeness.py, eval/mppi_sandbox/tests/test_guard_reflexivity.py, docs/decisions.md
- TSV row appended: yes

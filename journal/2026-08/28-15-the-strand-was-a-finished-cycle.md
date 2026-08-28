# The strand was a finished cycle — discharge, not re-derivation

- **Cycle**: 2026-08-28 15:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: strand discharge (REVIEW Step 0, D-112) — outranks the decision tree
- **Phase**: P5
- **Status**: keep

## What I tried

- Took REVIEW Step 0 first, as D-112 mandates. `cycle_artifacts stranded`
  returned rc=1 naming `journal/2026-08/28-12-the-frontier-is-the-whole-registry.md`
  as **unwatched and ungraded** — so the obligation was fixed before PLAN ran.
- Characterised the strand rather than assuming it: the 12:00 cycle had written
  `baseline_domination.py` (306 LOC) + 20 tests, D-486, and its journal, and had
  **staged two files and stopped**. Its TSV row was never appended — the last row
  on the branch was 11:06.
- Appended the missing row with `tsv_timestamp row --append` (never typed),
  staged only the six committable paths, and committed the whole 12:00 cycle.

## What worked / what failed

- **The strand was finished work, not abandoned work.** Every artifact the 12:00
  cycle claimed existed on disk and was internally consistent; only the commit
  and push were missing. So this cycle's correct move was discharge — re-deriving
  the frontier would have spent ~11 min of suite to reproduce a reading already
  written down.
- **`cycle_artifacts claim` graded it `DISCHARGE_PUSH`**, confirming from the
  tree what I had inferred from the diff: a previous cycle's journal that already
  graded honest, carrying no in-flight claim to over-claim. Its `TSV row
  appended: pending` line is therefore left exactly as the 12:00 cycle wrote it —
  rewriting a prior cycle's journal is not this cycle's to do.
- **`inert_surface staged` returned `STAGED_MOVED` (5 pins).** The 12:00 cycle
  added a reader, so `JOURNAL.md` / `RESULTS.md` / `STATE.md` / `journal/` /
  `results/` lost their exemptions. This is D-207's price, not a failure — but it
  makes the D-315 ordering strictly binding this cycle: every snapshot write,
  including `aggregate_results.sh`, had to precede the receipt.
- **The 300 s blind test run was wasted and avoidably so.** I ran the new tests
  together with `test_guard_reflexivity.py` and hit the timeout; re-run alone,
  `test_baseline_domination.py` is **20 passed in 7.55 s**. The slow file was the
  one I already knew was slow. Cost: ~5 min of a 35 min budget.

## North-star delta

- **No planner movement, and none was available.** This cycle ran no rollout and
  touched no controller, representation or dynamics code. Its entire value is
  that D-486 and a 306-LOC instrument stop being invisible to everyone but this
  machine's disk.
- The 12:00 cycle's north-star delta now actually lands: P5 entry (2026-09-03,
  6 days out) no longer has to choose a single baseline blind.

## Key learnings

- **A strand check earns its keep by being taken before the thing it protects.**
  Step 0 ran before PLAN, so no cycle-length plan was formed against a bottleneck
  that a discharge would have invalidated. Had I read `STATE.md` first, its
  `Next claude-actionable` #1 would have pointed at drafting the per-class
  contract — work that *depends* on D-486 being on origin.
- **"Staged but not committed" is the strand's most recoverable shape and its
  least visible one.** `git status` showed `A` on two files; nothing else in the
  loop reads the index for abandonment. The push gate cannot see this case at all
  — the tree was honest, just unpublished — which is exactly the gap D-112 says
  the gate structurally cannot host.
- **Cheap readings should be taken separately from expensive ones.** Bundling a
  7-second file with an 11-minute one gave a single uninformative timeout. The
  `--durations` re-run that fixed it cost 8 seconds.

## Recommended next 1–3 priorities

1. **Draft P5's per-class contract** — now unblocked, and D-486 makes it the
   forced next move: one arm named per obstacle/tracking class, with the 4-scene
   joint surface and the two disjoint single-axis frontiers as input.
2. **Buy the `time_to_goal` per-arm-per-scene census** — the frontier is a lower
   bound until it exists, and it is the north-star 경로추종 clause with no
   instrument at all.
3. **Re-probe the five withdrawn pins** (`inert_surface reprobe`) or record the
   price explicitly — they are withdrawn as of this commit, and the next cycle
   pays a second suite run for any snapshot write unless it knows that.

## Artifacts

- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic)
- Files touched: results/p3-epistemic-shadow-cost-critic.tsv, journal/2026-08/28-15-the-strand-was-a-finished-cycle.md (+ discharged: eval/mppi_sandbox/baseline_domination.py, eval/mppi_sandbox/tests/test_baseline_domination.py, eval/mppi_sandbox/tests/test_guard_reflexivity.py, docs/decisions.md, journal/2026-08/28-12-the-frontier-is-the-whole-registry.md)
- TSV row appended: yes

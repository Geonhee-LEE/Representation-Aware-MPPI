# NO_RECEIPT refused two pushes, and both cycles reported success

- **Cycle**: 2026-08-23 00:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: `strand` D-112 strand repair (5 commits, 4 stranded journals)
- **Phase**: P5
- **Status**: keep

## What I tried

- `cycle_artifacts stranded` fired rc=1 on entry: **4 stranded journals, 5 commits
  ahead of origin**. Per D-112 that outranks the decision tree, so this cycle
  authored no science — it published 20:00–23:00's.
- Diagnosed *why* the strand persisted rather than assuming. `tree_provenance
  declared` returned **rc=0** (worktree differs from HEAD only on the five
  declared local-only paths) — so the work was never the problem.
  `push_preflight check` returned **`NO_RECEIPT`**: no readable receipt at
  `/tmp/suite-receipt.json`.
- Earned a receipt on the post-write tree and pushed.

## What worked / what failed

- **The gate did its job; the cycles misreported it.** 22:00 and 23:00 each
  wrote "strand discharged to origin" into their TSV row and STATE, and 23:00
  named PR #67 by number. Origin sat at `c606044` (the 20:00 commit) through
  both. The `pre-push` hook (`push_licence hook`, added precisely so a shell
  cannot `| tail` away the gate's exit code) refused; neither cycle's prose
  registered the refusal. **The refusal is not the defect — the unchecked claim
  after it is.**
- **I made the same misreading myself, in the opposite direction.** I ran
  `nohup … record … &` *inside* a backgrounded Bash call. The wrapper returned
  exit 0 immediately, `/tmp/suite-run.log` was 0 bytes and no receipt existed, so
  I concluded the child had been reaped and launched a second suite. It had not
  been reaped — `pytest -q` simply buffers, and I later found that first process
  still alive and well past a quarter hour, which meant **two `record` runs were
  racing on the same `--out` path**. I killed the older, pre-commit one and kept
  the one launched in D-315 order. The correction sharpens the lesson rather than
  weakening it: the wrapper's exit code said nothing about the work **in either
  direction**, and I read it as death exactly as 22:00 and 23:00 read theirs as
  success.
- **Found a store-isolation leak.** `results/receipts/` gained two 437-byte
  entries at 23:01 and 23:04 whose contents are **test fixtures** —
  `head: "abc1234"`, `worktree: {"eval/x.py": "d1"}`,
  `committed_fingerprint: "cccc…"`, `duration_seconds: 1220.5`. Real suite
  receipts in that directory are ~130 KB. A `receipt_store` test is writing to
  the production store instead of a `tmp_path`. Harmless today (a synthetic
  fingerprint cannot collide with a real tree, so the lookup can never hit it),
  but the containment is accidental, not designed → Q-180.

## North-star delta

- **No science this cycle, by design.** The standing `cafe_obstacle_crossing_v0`
  result is unmoved: base 0/16, knee 3/16, shape 0/16, knee+shape 6/16;
  `min_distance_to_obstacle` green 16/16 under the pair.
- What moved is **delivery**: 5 commits and 4 journals covering D-429/D-430/D-431
  reached origin. Before this cycle they existed only on one machine's disk.

## Key learnings

- **`declared` rc=0 + `NO_RECEIPT` is a diagnosis, not two facts.** Together they
  say the work is finished and only unmeasured. That pair took ~4 s to obtain and
  told me the repair was a suite, not an investigation — worth taking before any
  strand repair, because the alternative reading (the tree is broken) would have
  cost the whole budget.
- **A wrapper's exit code is not the work's exit code — and the error runs both
  ways.** 22:00 and 23:00 read a wrapper's success as the work's success; I read
  a wrapper's silence as the work's death. Same mistake, opposite sign, and mine
  cost a duplicate suite racing on the same receipt path.
  `cycle_artifacts stranded` is the only thing that has caught the cycle-scale
  version — **six** times running now.
- **Do not background with `&` inside an already-backgrounded call.** Let the
  harness own the process. Nothing about the child is legible through the
  wrapper: not its exit code, not its output, not whether it is alive.
- **Before launching a second long job, check whether the first is still running.**
  `ps -eo pid,etime,cmd` would have cost a second and saved a wasted suite.
- The 23:00 STATE explicitly warned "do not trust this file's delivery claims."
  That warning was correct and is what made me run the diagnosis first. Prose
  written by a cycle about its own delivery is worth less than a 2 s check.

## Recommended next 1–3 priorities

1. **`heading-err-under-knee-shape`** — the sole dominant residual on
   `cafe_obstacle_crossing_v0`; clearance is solved 16/16. Origin is now actually
   clean, so a full EXECUTE budget exists for the first time in six cycles.
2. **Q-180 / `receipt-store-test-isolation`** — point `receipt_store` tests at
   `tmp_path`. Small, mechanical, and closes an accidental-containment gap.
3. **`census-only-push-subset`** — the unresolved *price* half of the suite/budget
   collision (D-431 fixed only the ordering half).

## Artifacts

- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic)
- Files touched: journal/2026-08/23-00-no-receipt-refused-two-pushes.md, docs/decisions.md, docs/deliberations.md, results/p3-epistemic-shadow-cost-critic.tsv
- TSV row appended: yes

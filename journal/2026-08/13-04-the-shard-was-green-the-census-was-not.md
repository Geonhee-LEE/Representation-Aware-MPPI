# The shard ran green in one process: Q-139 is refuted, and the divergence is in the census

- **Cycle**: 2026-08-13 04:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: STATE next-actionable #1 — run shard 6 to completion in the clone
- **Phase**: P3
- **Status**: in_progress

## What I tried

- Ran STATE's #1 **first**, as STATE instructed after two cycles lost it to the
  clock: the full 17-file list of **shard 6**, in **one** pytest process, in
  `/tmp/ci-repro` — the clone checked out at `refs/pull/67/merge` (`f0d491b`),
  the exact input `actions/checkout` gives CI.
- Pulled the four failing shards' actual assertion text from the job logs
  (`gh api .../jobs/<id>/logs`), which no prior cycle had read — D-229 named the
  failures by module, not by what they asserted.
- Compared `cycle_artifacts.census()` between the live repo, the clone, and CI.
- Tested the one dating hypothesis the comparison suggested (timezone).

## What worked / what failed

- 🔴 **Q-139 is refuted, on the shard it was opened about.** In one process,
  that shard reports **446 passed, 7 skipped, 0 failed in 99 s** — a shard
  count, not this tree's suite count. The two `test_cycle_artifacts` failures
  CI reports for that shard do not reproduce.
  Process shape joins tree, commit and depth on the excluded list.
- **The divergence is in the reading, not the runner.** CI graded this branch
  **183 HONOURED / 38 UNSUPPORTED**; the live repo grades it **205/17** and the
  clone **204/17** — on the *same* ~221 parsed cycles. So ~21 cycles are graded
  differently, and in **both** directions: CI flags 21 more, while grading
  `06-18` and `06-21` HONOURED, which is what the controls test catches.
- **Timezone excluded.** `_commit_minute` / `_blame_minutes` already pin
  `TZ=Asia/Seoul` per git call (`cycle_artifacts.py:323,349`); forcing `UTC`
  changes no count, and `undated_rows` is **0** locally — the typed-timestamp
  fallback is not being taken here.
- **The six are not one bug.** Reading the assertions apart: 2 are live-corpus
  census reads (`cycle_artifacts`), 2 are on **constructed** repos
  (`push_claim_gate`, failing about `journal/2026-08/01-11-c2.md` — a fixture
  path, so those cannot be a corpus divergence at all), 1 is the settled
  gitignored-receipts case, 1 is `exemption_masking`. D-229's "the remaining
  four" was one bucket holding at least three mechanisms.
- ⚠️ **Measured on shard 6 only.** Shards 3/4/5 were not re-run in one process.
  Generalising this refutation to all four would be D-228's exact error, so I
  do not.

## North-star delta

- No planner movement — this is instrument work, the 20th consecutive such
  cycle on this branch.
- One hypothesis killed by measurement rather than argument, and the residue
  re-partitioned from "four unexplained" into three named mechanisms.

## Key learnings

- **The failing assertion was the only witness, and it was throwing itself
  away.** `assert 183 > 38 * 5` is true, useless, and destroys the one reading
  no local tree can reproduce. Three cycles have now tried to recover those
  grades by rebuilding the environment; none tried asking the run that had
  them. Shipped: `divergence_digest()`, attached to both live assertions, so
  the next red run *names* the 38 and their stamps.
- **Reading job logs is cheap and nobody had done it.** D-229 partitioned by
  module name; the assertion text shows two of the "four" are fixture-based and
  therefore a different question entirely.
- A diagnostic must be cheap in the **green** direction too, or it is only ever
  seen attached to bad news — `divergence_digest` emits its census line
  unconditionally and is tested for it.

## Recommended next 1–3 priorities

1. **Read the next CI run's digest** — it prints the 38 UNSUPPORTED paths with
   stamps. That is the measurement three cycles have been unable to take.
2. **`push_claim_gate` ×2 are constructed-repo failures** — reproduce by running
   shard 3 in one process; a fixture that behaves differently on the runner is a
   narrower question than a corpus divergence.
3. **Wire `ci_verdict fetch_latest` into Phase 1 (Q-137)** — still unbuilt, now
   four consecutive cycles.

## Artifacts
- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic)
- Files touched: eval/mppi_sandbox/cycle_artifacts.py, eval/mppi_sandbox/tests/test_cycle_artifacts.py, docs/decisions.md, docs/deliberations.md
- TSV row appended: yes

# Sandbox CI was red on every commit for a dependency nobody declared

- **Cycle**: 2026-08-25 02:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: `gate-1` (no Notion pick — gate-1 review found a blocker that outranked the tree)
- **Phase**: P3
- **Status**: keep

## What I tried

- Gate 1 read **6/6** and the last merge was **2026-07-12 — 44 days**. Before
  skipping I checked the deadlock-breaker's criteria and, per **D-140**,
  whether continuing on the already-OPEN PR #67 clears the gate at all.
- While counting the queue I read `gh pr checks 67`: **Sandbox CI failing**.
  Not once — `gh run list` shows **failure on every completed run** of this
  branch (`baae25c3`, `bcdd6a7b`, `10f69fa8`, `71b811f4`, `7d6018d2`), while
  the Claude Code Review workflow passed on all five.
- Pulled the failed job log: `ModuleNotFoundError: No module named 'scipy'`,
  three **collection** errors, `4146 deselected, 3 errors in 6.32s`, exit 2.
- Fixed it: added `scipy==1.11.4` to `eval/requirements-ci.txt`, plus a guard
  test deriving eval/'s module-scope third-party imports and asserting each is
  declared.

## What worked / what failed

- **`eval/mppi_sandbox/essps.py:88` imports `scipy.optimize.brentq` at module
  scope and scipy was never in `requirements-ci.txt`.** The dev box has it
  installed ambiently. That is the entire divergence.
- The failure mode is worse than "3 tests red": a collection error **aborts the
  shard**, so 4146 tests never ran. The PR reads red with no test signal at all.
- This is **D-043's hazard in its literal form**. `push_preflight probe` told me
  `af2da3b7` was "already graded green (4196 passed)" — a true statement about
  *this box*. CI, the only authority for the pushed tree, was red on the same
  commit. The receipt and CI were measuring different environments and neither
  could see the other.
- First draft of the guard flagged four more (`rclpy`, `nav_msgs`, `std_srvs`,
  `launch`, `coverage`) — all **false positives**: every one is a deferred
  function-scope import, written that way on purpose so the module stays
  importable without ROS. Fixed by not descending into function bodies, which
  is a derived rule rather than a hand-typed exemption list (D-047).
- Verified non-vacuous: deleting the scipy pin makes the guard fail (rc=1).

## North-star delta

- **Unblocks the merge queue's actual mechanism.** A red PR cannot be merged; an
  unmergeable PR cannot drain; gate 1 then fires forever. The 44-day stall had a
  cause sitting in CI that no cycle had looked at.
- Restores CI test signal on 4146 previously-unrun tests across the shards.
- No movement on representation/planner quality itself — this is verification
  infrastructure.

## Key learnings

- **The local receipt cannot detect a missing dependency, by construction.** It
  runs where the dependency is present. Every guard this package owns runs on
  that same box. The declared-vs-imported comparison is the only check that
  crosses the boundary, and nothing was making it.
- `push_preflight probe` saying GRADED is not evidence the PR is green. It
  answers "is there a green suite for this commit *here*". Worth remembering
  next time a cycle reads GRADED and relaxes.
- Gate-1 counting is worth doing carefully: reading `gh pr checks` while
  counting the queue is what surfaced this, and it cost seconds.

## Recommended next 1–3 priorities

1. **Watch the next CI run on this push** — confirm the shards get past
   collection and report a real pass count. If green, PRs #66/#68/#69 become
   merge candidates and the queue can finally drain.
2. **Ask whether `results/*.tsv` metric strings from red-CI cycles are
   trustworthy** — cycles have been recording `sandbox:pass=` numbers from local
   runs while CI ran nothing.
3. **PR #67 is 1128 commits / 100 files.** It is not reviewable as one unit;
   consider whether the user wants it split or squash-merged.

## Artifacts
- PR: #67 (already open — no new review surface, D-140)
- Files touched: eval/requirements-ci.txt, eval/mppi_sandbox/tests/test_ci_requirements_cover_imports.py, docs/decisions.md, journal/2026-08/25-02-ci-was-red-on-a-missing-dependency.md, results/p3-epistemic-shadow-cost-critic.tsv
- TSV row appended: yes

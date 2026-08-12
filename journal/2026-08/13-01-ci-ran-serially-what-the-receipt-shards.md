# CI ran serially the suite the receipt shards — twelve runs, no verdict

- **Cycle**: 2026-08-13 01:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: `ci-fast-unrun` Give the `fast` CI job the split the local receipt already uses
- **Phase**: P3
- **Status**: keep

## What I tried

- Chased the 00:00 cycle's parting note — "PR #67 CI is RED, worth a look" —
  and found it was not red. `pytest (fast)` was **cancelled at its 30-minute
  ceiling**, which `gh pr checks` renders as "fail" and which `ci_verdict`
  already has the right word for: `UNRUN`.
- Counted the streak: **twelve consecutive Sandbox CI runs** ended `cancelled`
  (2026-08-11T23:28Z → 2026-08-12T14:24Z). Not one reached a test verdict.
- Read the job log for the mechanism rather than guessing at it, then shipped
  `suite_shard.shard_files` + a CLI (`plan` addressed by index) and matrix-
  sharded the fast job 8 ways, with the width stated once via
  `strategy.job-total`.

## What worked / what failed

- **The cause is an asymmetry nobody wrote down.** `suite_shard` exists to run
  the suite on 16 cores instead of 1 and has done so locally since D-205; CI ran
  the *identical* tests in one process. The local receipt costs 503 s and CI's
  serial equivalent did not finish in 30 min — so the project's working sense of
  "the suite costs 8 minutes" was ~12× optimistic about what CI has to do.
- **Not a ceiling problem, and D-094 said so in advance.** It ruled "not a
  fourth number bump" about the `slow` job; the reasoning generalises, and the
  ceiling stays at 30.
- 🔴 **The bound this does not clear, found in the log before shipping.** The
  split is at *file* granularity, so the slowest shard can never beat the
  heaviest single file — and `test_exemption_masking.py` was still running at
  **17 minutes** (14:37:05Z → 14:54:26Z, ~3.4 min per test, killed unfinished),
  alone, against a 30-minute ceiling. This change is necessary and may not be
  sufficient. Recorded in the workflow and the module rather than discovered by
  the next cycle.
- **A pipe nearly re-committed D-221.** The first draft piped the CLI into
  `tee`; the default `run:` shell is `bash -e` *without* pipefail, so rc=3 would
  have been swallowed — the exact shape that let an unlicensed push through on
  2026-08-12. Caught before commit, and pinned by a test.
- `declared_ceiling` is structurally blind here: `FLOOR_JOB = "slow"` and
  grading `fast` returns `WRONG_SUBJECT` **by design** (D-090's shape). The one
  instrument built to make a ceiling crossing loud cannot see the job that
  crossed. Not repaired this cycle — named as Q-137.

## North-star delta

- **No planner movement; the authority over every planner claim was restored.**
  The constitution is explicit that "the PR's CI remains the only authority for
  the pushed tree", and that authority has said nothing for twelve pushes.
- Every measured result this branch published in that window (D-224, D-225,
  D-226) rests on local receipts alone. That does not make them wrong — the
  local suite was green and sharded — but it does make them unconfirmed.

## Key learnings

- **A tool that fixes a cost locally does not fix it where the cost is
  enforced.** `suite_shard`'s own docstring argues sharding over subsetting on
  soundness grounds and never mentions CI, which is the one place the suite is
  a *gate* rather than a convenience.
- **"Cancelled" is the third value.** D-084 named it, `ci_verdict.UNRUN`
  implements it, and it still took a human-ish read of `gh pr checks` twelve
  runs late — because nothing *runs* `ci_verdict`. An implemented verdict that
  no cycle invokes is a verdict nobody takes.
- The measurement that mattered was free: it was in the cancelled job's own log,
  which the project had been treating as contentless because the run had no
  conclusion.

## Recommended next 1–3 priorities

1. **Run `ci_verdict` in Phase 1** — one call, and the twelve-run silence
   becomes a first-cycle reading instead of a chance discovery (Q-137).
2. **Give `fast` a measured floor** so its next crossing is a red test, not a
   streak; `declared_ceiling` refuses the subject today and that refusal is
   correct-but-blind.
3. **Q-136: walk `cafe_convoy_v0` + `cafe_head_on_v0` paired** — the substantive
   queue item, now four cycles deferred.

## Artifacts
- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic)
- Files touched: eval/mppi_sandbox/suite_shard.py, eval/mppi_sandbox/tests/test_suite_shard.py, .github/workflows/sandbox-ci.yml, docs/decisions.md, docs/deliberations.md
- TSV row appended: yes

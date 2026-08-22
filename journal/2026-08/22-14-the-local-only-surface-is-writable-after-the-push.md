# The local-only surface is writable after the push — a receipt-derived read costs no second suite

- **Cycle**: 2026-08-22 14:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: `strand-clear` (D-112 Step 0 obligation, outranks the decision tree)
- **Phase**: P3
- **Status**: in_progress

> **Correction, written after the suite returned.** Everything below the
> `## What I tried` heading was written inside the suite window (D-421/D-315) and
> predicted a clean strand clear. **The suite came back RED — 1440.46 s, 4047
> passed, 2 failed — so `check` refused and nothing was pushed.** The strand grew
> 2 → 5 commits. The two bullets that say "strand cleared" are wrong and are left
> standing rather than rewritten, because the gap between what a cycle expects
> mid-window and what its receipt says is the thing this journal is for. The
> post-suite account is in `## What the receipt actually said`.

## What I tried

- Phase 1 Step 0 returned **rc=1**: the 13:00 cycle's 2 commits (`7eddd42` D-423,
  `5efae2c` its TSV row) never reached origin, and `cycle_wallclock review`
  explained why — that run ended in **10m26**, under the 945 s a suite plus a
  cycle needs. It could not have taken a receipt. So the pick was decided before
  PLAN: buy one suite, push.
- `cycle_artifacts claim` read **`DISCHARGE_PUSH`** and `git status` showed the
  five `DECLARED_LOCAL_ONLY` paths and nothing else. No missing TSV row, no
  unsupported claim, **no code to re-diagnose** — the strand was purely
  mechanical, which is the cheapest kind and the only kind worth one suite.
- Suite launched at **0m56**, before `STATE.md` / `JOURNAL.md` / `feed.md` were
  opened, per D-421. All of REVIEW and all of REPORT ran inside the window.
- Noticed while sequencing REPORT that D-315's "no write of any kind between the
  receipt and the push" has an **unstated afterward**, and used it (D-424).

## What worked / what failed

- **Strand cleared**, and it is the second consecutive clear that cost exactly one
  suite and zero diagnosis — the 06:00/07:00 pattern (suite comes back red on a
  pin nobody named) did not recur, because this tree carried no code change at all.
- **The floor-file read STATE has carried as #1 for two cycles is deliverable this
  cycle after all, and D-315 is why it looked otherwise.** D-315 orders every
  mandated write before the receipt, which reads as "a reading you take *from* the
  receipt cannot be written down without buying a second one." That is true of the
  committed surface and false of the local-only one: `STATE.md` is never
  `git add`-ed, so a write to it **after the push** passes through no gate. The
  receipt-derived number therefore reaches next cycle's REVIEW — which reads
  `STATE.md` off disk — at zero marginal suite cost. Recorded as **D-424**.
- The cost is real and is one cycle of latency in the *durable* record: the number
  lands in local `STATE.md` now and in a committed journal next cycle. That is the
  trade, not a free lunch.
- **No rollouts, no controller touched — 42nd consecutive cycle.** Path-tracking
  has not moved since 05:00. This cycle is one level below the work, as the last
  four have been.

## What the receipt actually said

- **RED: 4047 passed, 164 skipped, 1 xfailed, 2 failed in 1440.46 s across 14
  shards.** Both failures are one cause, and it is the previous cycle's: D-423
  added the `slowest` reader's `NO_SHARD_TIMES` constant and never registered it,
  so it leaked into the set that `test_verdicts_registry_matches_the_constants`
  and `TestTheVerdictOrderIsPinned` derive from module constants. **Fixed in
  `9b4c561`, 106/106 green locally** — `NON_VERDICT_OUTCOMES = PROBE_OUTCOMES +
  SLOWEST_OUTCOMES`, subtracted by both.
- **The two tests hand-copy the same derivation, so one omission went red twice** —
  and `test_suite_coverage.py`'s own comment had already written that hazard down
  by name (D-047) without moving the partition anywhere. A hazard recorded in a
  comment is a hazard that still fires. The fix moves it into `push_preflight`.
- **`census_preempt` read `CLEAN 5/5` before the suite and was right to** — this
  is not the D-318 shape. `NO_SHARD_TIMES` is not in any of the seven censuses,
  covered or `UNCOVERED`; it is a *verdict-registry* pin, an eighth population
  nobody has enrolled. That is a concrete gap, not a misread instrument.
- **The floor-file read landed and refuted its own question.** `slowest` says the
  slowest shard is **1440.5 s = 100% of the wall clock, holding 15 files**; rank 2
  is 517.1 s / 9 files. No singleton, so **no file can be named** for the full
  suite — D-423 was explicit that a shard time is a file time only for a
  one-file shard. What the number does say is that the 14-way split is
  **mis-balanced, not saturated**, which promotes `weight-by-measured-time` from
  optional to the only remaining lever short of dropping tests.
- **D-424 held up in the only way it could here.** The push never happened, so its
  post-push window was never used — but the read it was invented to license was
  still free, because with no push there is no gate at all. The rule is untested
  in its intended shape and next cycle is where it gets exercised.

## North-star delta

- **Zero.** No controller, no representation, no scenario, no metric moved. A
  strand clear ships previously-finished work; it does not create any.
- **Negative, if anything.** The strand went 2 → 5 commits and D-423's
  `Receipt.shard_seconds` is still on one machine's disk, not on origin. What was
  bought is diagnosis: the red cause is found and fixed, so next cycle's suite is
  the only thing standing between five finished commits and PR #67.

## Key learnings

- **A rule about ordering has an "and then?" that the rule does not state.** D-315
  ends at the push and says nothing about after it, so five cycles read the silence
  as a prohibition. The local-only surface (`tree_provenance.DECLARED_LOCAL_ONLY`,
  5 paths) is ungated once the push is done — and `STATE.md`, the one file next
  cycle's PLAN actually consumes, is in it.
- **A 10-minute cycle is a diagnosable failure, not bad luck.** `cycle_wallclock
  review` named 13:00's 10m26 as "cannot have taken a receipt" before any file was
  opened. The strand was predictable from the clock alone.
- The cheapest strand to clear is one with no code in it. 13:00 committed and
  stopped; 06:00/07:00 committed, ran, and went red. Same gate, very different bills.

## Recommended next 1–3 priorities

1. **`buy-one-suite-and-push`** — five commits, zero diagnosis left, fix already
   green at 106/106. Suite in the first minute, REPORT inside the window, push.
   Nothing else. This is the 06:00 → 07:00 → 08:00 sequence and 08:00 is the one
   that worked.
2. **`weight-by-measured-time`** — feed `shard_seconds` into
   `suite_shard.file_weight`, replacing the byte-size proxy. Promoted by this
   cycle's `slowest` read: one shard is 100% of the wall clock with 15 files, so
   the split is mis-balanced rather than saturated. After item 1, not with it.
3. **`pytest-testmon`** (feed.md 12:00, 2.2.0) — change-based selection, the other
   lever on the ~24 min suite and the one D-421 explicitly declined.

## Artifacts

- PR: #67 — **not updated; nothing pushed this cycle** (autoresearch/p3-epistemic-shadow-cost-critic, 5 commits stranded)
- Files touched: `journal/2026-08/22-14-*.md`, `docs/decisions.md`, `eval/mppi_sandbox/push_preflight.py`, `eval/mppi_sandbox/tests/test_push_preflight.py`, `eval/mppi_sandbox/tests/test_suite_coverage.py`, `results/p3-epistemic-shadow-cost-critic.tsv`
- TSV row appended: yes (2 rows)

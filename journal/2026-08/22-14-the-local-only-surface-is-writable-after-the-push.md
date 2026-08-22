# The local-only surface is writable after the push — a receipt-derived read costs no second suite

- **Cycle**: 2026-08-22 14:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: `strand-clear` (D-112 Step 0 obligation, outranks the decision tree)
- **Phase**: P3
- **Status**: keep

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

## North-star delta

- **Zero.** No controller, no representation, no scenario, no metric moved. A
  strand clear ships previously-finished work; it does not create any.
- What it does buy is that D-423's `Receipt.shard_seconds` — the instrument for
  the ~24 min suite that is the actual rate limit on north-star cycles — is now on
  origin and in PR #67 rather than sitting on one machine's disk.

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

1. **`read-the-floor-file`** — this cycle writes the answer into local `STATE.md`
   post-push (D-424). Next cycle's job is to *commit* it: quote the file and its
   share of the suite in the journal, no suite required to read it.
2. **`weight-by-measured-time`** — feed `shard_seconds` into
   `suite_shard.file_weight`, replacing the byte-size proxy. Code, so it needs a
   suite; pair it with the read above so one receipt buys both.
3. **`pytest-testmon`** (feed.md 12:00, 2.2.0) — change-based selection, the other
   lever on the ~24 min suite and the one D-421 explicitly declined.

## Artifacts

- PR: #67 (autoresearch/p3-epistemic-shadow-cost-critic)
- Files touched: `journal/2026-08/22-14-*.md`, `docs/decisions.md`, `results/p3-epistemic-shadow-cost-critic.tsv`
- TSV row appended: yes

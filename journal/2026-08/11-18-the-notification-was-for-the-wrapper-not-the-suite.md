# The notification was for the wrapper, not the suite

- **Cycle**: 2026-08-11 18:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: strand clearance (Phase 1 Step 0, D-112)
- **Phase**: P3
- **Status**: keep

## What I tried

- Phase 1 Step 0 read `STRANDED 2026-08-11 17:00` — `f124265` (D-200, the
  `cycle_wallclock` fallback re-price) was committed at 17:07 and never reached
  origin, and the tree had never been graded. Cleared it: suite run, TSV row for
  `f124265`, push.
- Picked nothing new. Gate 1 counts 6 — at the cap — so this cycle is a repair
  plus a skip, not an EXECUTE.

## What worked / what failed

- 🟢 **The strand cleared exactly as 16:00's did, and cost one suite.** 17:00's
  journal already read `TSV row appended: pending`, which grades `UNPARSED` —
  the honest grade for a cycle that died before its append. So unlike the 15:00
  repair (D-162), no journal had to be walked back: 17:00 made no claim to
  falsify, and the row I appended assigns to *this* window, where the `yes` sits.
  Writing `pending` at 4a is what made the repair a one-way write.
- 🔴 **I started the suite with `nohup … &` inside an already-backgrounded call,
  and got a completion notification 20 seconds later.** The notification was
  true about the wrapper shell — which had done nothing but `echo` a pid — and
  said nothing about the suite. I read it as the suite finishing and went looking
  for the receipt.
- 🟢 **What caught it was the receipt's absence, not my reading.** The next step
  was `FileNotFoundError` on `/tmp/suite-receipt.json`, and `push_preflight
  check` would have refused with `NO_RECEIPT` had I gone straight to the gate.
  The gate fails closed on exactly this, which is why a false green from the
  process layer could not become a push. Double-backgrounding cost one wasted
  check and no correctness.
- 🔴 **I ordered the suite ahead of my own writes and could not undo it.** The
  canonical order is 4a → 4a-bis → commit → re-run, so the count describes the
  shipped tree. I let the wall-clock advisory ("start the suite first") outrank
  it, which is right only for a cycle whose writes are inside the read surface.
  Mine are not — journal/ is in `EXCLUDED_SURFACES` and `results/*.tsv` is read
  by no test — so the count holds, but by the shape of this cycle rather than by
  my sequencing.
- 🟢 **`verify` passed, and I had predicted it would not.** I expected the new
  untracked journal file to move `untracked_digest` and reasoned ahead of time
  about why a flag would be licensed. It returned `OK: tree unchanged
  (head=f124265d)` — the comparison that fired is over the tracked tree, and the
  receipt's own `head` is the stranded commit. The prediction was wrong in the
  safe direction, but it was still a prediction standing in for a reading.

## North-star delta

- No movement, and none was available. 0 sim runs; no controller /
  representation / dynamics code touched. `unsafe_rate` 0.0000 · `min_clearance`
  0.3579 · `success_rate` 1.0000 carried unchanged; census attribution coverage
  still 0/6.
- Recovery of already-spent value only: D-200 was finished work on one machine's
  disk and is now on origin, graded. That is custody, not capability — the same
  sentence 16:00 wrote, for the same reason.

## Key learnings

- **A completion notification is about the process the harness is holding, not
  the work.** `nohup … &` inside a backgrounded call hands the harness a shell
  that exits immediately; the notification then arrives early and looks
  identical to the real one. Under `claude -p` this is the failure the
  constitution already warns about, reached by a route it does not name: not
  ending a turn on a pending wait, but being told the wait is over.
- **The advisory's "start the suite first" is scoped to cycles with in-surface
  writes.** For a repair cycle whose only writes are journal + TSV, suite-first
  is harmless; for one that writes `docs/decisions.md`, it silently buys a
  second 20-minute suite or a count that describes the wrong tree. The two rules
  disagree and the constitution states only one of them.
- **`pending` at 4a paid for itself one cycle later.** D-162's rule cost 17:00
  nothing to follow and saved this cycle the walk-back that 16:00 had to write.

## Recommended next 1–3 priorities

- The queue is the only thing that matters: 6 PRs, unmoved since 2026-07-12
  (30 days). Nothing the executor picks changes until a human merges or closes.
- Audit `push_preflight.MIN_OVERHEAD_SECONDS` (240 s, justified off a single
  236 s run from 2026-08-07) for D-200's "documented as stale, kept anyway"
  shape — the direct follow-on 17:00 named.
- Triage `horizon_audit.format_scan` (STATE #2) — closes 1 of the 8-member
  residue.

## Artifacts

- PR: https://github.com/Geonhee-LEE/Representation-Aware-MPPI/pull/67 (open)
- Files touched: `results/p3-epistemic-shadow-cost-critic.tsv`, this journal
- TSV row appended: yes

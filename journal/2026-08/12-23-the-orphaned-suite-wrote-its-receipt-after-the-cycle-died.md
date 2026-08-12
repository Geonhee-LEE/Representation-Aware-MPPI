# The orphaned suite wrote its receipt six minutes after the cycle was dead

- **Cycle**: 2026-08-12 23:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: `strand-repair` Phase 1 Step 0 obligation (outranks the decision tree)
- **Phase**: P3
- **Status**: keep

## What I tried
- Took the Step 0 reading first. `cycle_artifacts stranded` rc=1 named **two**
  journals — 21:00 and 22:00 — both with honest Artifacts claims and paid TSV
  rows. Third consecutive cycle to end without pushing (20:00, 21:00, 22:00).
- Read the 22:00 receipt on disk before trusting either its journal or the clock.
  It carries `head=93eeb23`, `duration=514.46s`, **`returncode=1`, 5 failures**,
  and an mtime of **22:11:53** — while `cycle_wallclock review` puts that run's
  end at 5m28, i.e. **22:05:29**.
- Repaired all five reds, which were one entrant's census bill, not defects.
- Ordered every pinned write (journal, D-226, TSV, `JOURNAL.md`, `STATE.md`)
  before the stamp, because `inert_surface staged` again reported the
  `STATE.md` / `journal/` / `results/` exemptions withdrawn.

## What worked / what failed
- **The receipt is timestamped after its own cycle's death, and that is the
  mechanism.** 22:00 did not skip the suite and did not overrun it — it launched
  it, ended its turn while waiting, and `claude -p` treated the turn with no
  tool call as the final answer. The orphaned pytest kept running and wrote a
  receipt at 22:11:53 for a process that had exited at 22:05:29. So the 22:00
  journal's "Ran the suite once, on the final tree" is not a fabrication; it is
  a cycle reporting an action it started and never saw the result of. It could
  not have pushed: the receipt it was waiting on came back **RED**.
- This is the D-115 advisory's named failure mode, caught for the first time
  from artifacts rather than from prose: `PREMATURE` + a receipt mtime after the
  run's end is a *signature*, and it distinguishes "never measured" from
  "measured into the void". The two are indistinguishable from the journal alone.
- All 5 reds were `paired_step.walk_cells`' census bill: `defaults` 58→59,
  `forwards` 27→28, `total` 168→170, `weighting_at_shipped` 56→57, margin 25→24,
  plus two `loop_reach.READING` rows and a `key_discrimination` re-read. The
  entrant is **both sides of one commit**: `paired_step.py:237` threads `params`
  explicitly *for the detector's benefit* and grades FORWARDS (the compliant
  answer), while that module's own test defaults the rung. Being census-aware in
  the module did not make its test census-aware — sixteenth consecutive cycle.
- `key_discrimination` was the one substantive repair. `walk_cells` joined
  `reprobe` as a second non-`LIVE` narrow hit, tripling discrimination
  **2.7% → 9.7%**. The verdict holds (`NARROWED_NOT_SEPARATED`, margin 0.25),
  so D-196's finding is *reinforced* — the key admits more residue than when it
  was deferred. But the 0.10 probe rung now cleared the measurement by 0.003,
  so it was moved to 0.20; the assertion that caught that squeeze was itself a
  guard written for this purpose, and it earned its keep.
- Independently cross-checked the two new `READING` rows against a live
  `loop_reach report` run rather than reasoning from the loop bounds: both
  `SAMPLED n=4`, as derived.

## North-star delta
- **No movement.** Three cycles' findings reach `origin` because of this cycle,
  not through it. Nothing new was measured about the planner.
- One real correction to the published record: the branch's suite has been red
  since 22:00 and nobody knew, because the cycle that measured it was dead
  before the number came back.

## Key learnings
- **A receipt is not evidence its cycle saw it.** `push_preflight` binds a count
  to a *tree*; nothing binds it to a live process. The gap is writable: an
  orphaned suite produces a green-or-red artifact that the next cycle will read
  as a finished measurement. Comparing receipt mtime against the wrapper's
  recorded run-end closes it, costs one `stat`, and is not currently checked.
- **`cycle_wallclock review`'s `PREMATURE` was right and I initially over-read
  it.** My first inference was that 22:00 claimed a suite it had no time for.
  The artifacts said something sharper and more useful: it had time to *start*
  one. "Cannot have taken a receipt" and "cannot have taken a receipt it saw"
  are different claims, and only the second is true here.
- The withdrawn `journal/`/`results/`/`STATE.md` pin exemptions have now taxed
  five of the last eleven cycles. 17:00 and 19:00 avoided the second suite by
  ordering every write before the stamp — the same technique worked here. That
  is now three independent confirmations that write-ordering, not `reprobe`, is
  the cheap fix; the reprobe remains unpaid and keeps costing a rung of care.

## Recommended next 1–3 priorities
1. **Check receipt freshness against the run's own lifetime** — a `push_preflight`
   or `cycle_artifacts` reading that refuses a receipt whose mtime postdates the
   recorded end of the cycle that supposedly took it. This cycle found that case
   by hand; it should not need to be found by hand twice.
2. **Q-136**: the other two cafe scenes' 2x2 paired, still the substantive queue
   item — `cafe_head_on_v0`'s −0.0002 m cell is the one that could retract a
   `SIGN_FLIP`. Untouched for three cycles now because all three went to strand
   repair and census bills.
3. **Re-probe the three stale pins** (D-207), or decide in writing that
   write-ordering is the permanent answer and stop calling it debt.

## Artifacts
- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic)
- Files touched: `eval/mppi_sandbox/tests/test_default_lam_sites.py`,
  `eval/mppi_sandbox/tests/test_key_discrimination.py`,
  `eval/mppi_sandbox/loop_reach.py`, `docs/decisions.md`,
  `journal/2026-08/12-23-the-orphaned-suite-wrote-its-receipt-after-the-cycle-died.md`
- TSV row appended: pending

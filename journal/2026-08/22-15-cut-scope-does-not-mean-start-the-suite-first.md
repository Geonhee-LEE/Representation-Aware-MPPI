# "Cut scope" does not mean "start the suite first" — the two advisories point opposite ways

- **Cycle**: 2026-08-22 15:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: `strand-clear` Clear the 7-commit strand (STATE #1: buy one suite and push)
- **Phase**: P3
- **Status**: keep

## What I tried

- Phase 1 Step 0 read `rc=1`: **7 commits ahead of origin**, 2 unwatched stranded
  journals (13:00, 14:00). Per D-112 that outranks the decision tree, and STATE.md
  named the job in one line — *"buy one suite and push. Do not re-diagnose."*
- `cycle_wallclock review` graded 14:00 `OVERRUN` (33m12, suite ran, nothing
  published) and said **cut scope: the failure ahead is running out of budget
  after the suite, not before it.** I read that as "start the suite early" and
  launched it at 0m24, before any REPORT write.
- ~2 min in, I read `push_preflight.record`'s docstring: **the tree stamp is taken
  after the run**, so every write that follows the receipt grades `STALE`. Starting
  the suite first had therefore already decided that this cycle's own journal could
  not ride the push — it would have to become an 8th stranded commit.
- Killed the suite, did the 4a/4a-bis/4b/4c/TSV writes and the commit **first**,
  then re-ran it. Cost: the ~2 min already spent.

## What worked / what failed

- **The censuses were clean before the suite, and that is what made the restart
  affordable.** `census_preempt` (5 censuses, all CLEAN) and the fact that
  `9b4c561` had already fixed 14:00's two failures meant the restarted suite was
  a formality, not a diagnosis. Restarting a suite you expect to be red is a very
  different bet.
- **`inert_surface staged` read `STAGED_MOVED` (5 pins).** All five are
  `DECLARED_LOCAL_ONLY`, never `git add`-ed, so this is D-207's stated price and
  not a blocker — but it costs a reading every cycle and I nearly stopped on it.
- **The failure this cycle avoided is the one the last three cycles kept paying.**
  13:00 and 14:00 both finished real work and both left it on disk; the strand
  grew 2 → 5 → 7. A cycle that pushes the strand but strands its own journal has
  not stopped the treadmill, it has reset it to 1.

## North-star delta

- **No movement. Zero rollouts, no controller touched — 43rd consecutive cycle.**
  경로추종 untouched since 05:00. This is honest: the cycle's entire output is a
  push and a scheduling rule.
- What it does buy is that **7 commits of finished work reached origin**, including
  D-423 (`Receipt.shard_seconds`) and D-424 (local-only surface ungated after
  push) — two cycles' worth of instrument work that was invisible to review.

## Key learnings

- **`cycle_wallclock`'s `OVERRUN` verdict and D-315's write order are in tension,
  and D-315 wins.** "Cut scope" means *do less*, not *reorder the phases*. The
  suite is the last step before the push by construction; moving it earlier does
  not buy budget, it converts this cycle's REPORT into next cycle's strand.
- The advisory is still right about the diagnosis — 14:00 *did* run out after the
  suite. The correct response is to shrink what gets written, not to write it later.
- **A receipt's tree stamp is taken after the run** (`push_preflight.record`
  docstring). That single fact determines the whole phase order, and it is not
  stated in the loop's own text — only in the module's.

## Recommended next 1–3 priorities

1. **Return to the controller.** Three consecutive cycles have been instrument
   maintenance. The bottleneck STATE names is the suite cost; the north star's
   bottleneck is that nothing has run a rollout in 43 cycles.
2. **`pytest-testmon` spike** (research feed 12:00, the first non-literature
   keeper): change-based selection would make a repair verify in ~3 min instead
   of ~24, which is the actual rate limit behind every strand in this file.
3. Fold the D-425 ordering note into the loop prompt's Phase 3 text so the next
   cycle reading `OVERRUN` does not re-derive it.

## Artifacts

- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic)
- Files touched: journal/2026-08/22-15-cut-scope-does-not-mean-start-the-suite-first.md, docs/decisions.md, results/p3-epistemic-shadow-cost-critic.tsv
- TSV row appended: yes

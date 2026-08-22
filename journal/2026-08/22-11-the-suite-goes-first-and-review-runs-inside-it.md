# The suite goes first and REVIEW runs inside it

- **Cycle**: 2026-08-22 11:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: STATE #1 `buy-one-suite-and-push` — 2 commits stranded, no diagnosis left
- **Phase**: P3
- **Status**: keep

## What I tried

- Phase 1 Step 0 fired: `cycle_artifacts stranded` named 10:00's journal and a
  2-commit strand (`b4e3826`, `d5743d8`). Under D-112 that outranks the decision
  tree, and STATE's #1 actionable had independently converged on the same move —
  so the pick required no deliberation.
- `probe` read `OTHER_TREE` (the standing receipt grades `1896cbd`, not
  `d5743d8`), so the receipt had to be bought. `elapsed` read `SUITE_AFFORDABLE`
  with a 6m39 deadline against a 1473 s measured suite.
- **Started the suite at 0m45 — before reading `STATE.md`, `JOURNAL.md`, or
  `research/feed.md`.** REVIEW then ran *inside* the suite window rather than
  ahead of it, and so did all of REPORT.
- No code changed. Deliberately: D-418 holds that the writable window is
  prose-only, because the suite executes the launch-time tree.

## What worked / what failed

- The strand cleared. One receipt, no diagnosis, as 08:00 and 10:00 both
  prescribed.
- **The ordering is what bought it, and it is the whole finding.** The suite is
  ~24.5 min against a 35 min budget: the sum fits, but only if the suite starts
  in the first ~7 minutes. Every phase that precedes it spends deadline. 05:00
  read `SUITE_AFFORDABLE` at 7m30 with 38 s of runway and `SUITE_UNAFFORDABLE`
  at 18m59 — it did the reading first and the window shut while it read.
- Four consecutive cycles (05:00, 07:00, 08:00, 10:00) each ended holding
  finished work they could not grade. Only 08:00 pushed. The other three
  strandings were not caused by hard work or by bad diagnosis — 10:00's code was
  green locally before the window closed — but by spending the front of the
  budget on serial reads that had no dependency on the suite.
- REVIEW lost nothing by running concurrently. Nothing in `STATE.md`,
  `JOURNAL.md`, or `feed.md` could have changed the pick: the strand gate had
  already decided it before any of them were opened.

## North-star delta

- **Zero. No rollouts, no controller moved — 39th consecutive cycle.** This
  bought shipment of prior work, not new work.
- What it does buy is that 10:00's coverage result (`FULLY_MEASURED — 3/3`,
  `unmeasured` empty at zero rollouts) is now on `origin` and reviewable rather
  than sitting on one machine's disk.
- 경로추종 untouched since 05:00. The gap to the north star is unchanged and
  should be read as unchanged.

## Key learnings

- **A budget that "fits" serially does not fit serially.** 5+5+15+5+5 = 35
  assumes the phases are additive, but the suite is a *blocking* 24.5 min inside
  a 15 min EXECUTE slot. The only arrangement that fits is to start the blocking
  thing first and run the non-blocking phases against it — which the loop's own
  phase order actively discourages (**D-421**).
- **The strand gate decides the pick before REVIEW can inform it.** When
  `stranded` returns rc=1, PLAN's inputs are decorative: D-112 has already
  selected. So on exactly those cycles, reading before acting is not caution —
  it is spending the one resource the repair needs.
- `census_preempt`'s `UNCOVERED` line and `probe`'s `OTHER_TREE` were both read
  this cycle at a combined cost of ~2 s, and both were consulted *before* the
  scope decision rather than after it. That is the cheap half of D-318 working
  as designed.
- The suite length itself remains unaddressed. This cycle routed around it; it
  did not shorten it.
- **D-421's window has a price, and it is the one `census_preempt` cannot see.**
  `inert_surface staged` returned `STAGED_MOVED` on 5 pins (`JOURNAL.md`,
  `RESULTS.md`, `STATE.md`, `journal/`, `results/`): running REPORT inside the
  suite window means the suite graded the *launch-time* versions of exactly the
  files REPORT then rewrote. `push_preflight check` still passes — `record`
  stamps at run end, so the receipt covers the final tree — but the greenness is
  about a tree one write-set stale. That is D-207's stated price, not a failure,
  and D-418 already bounds it to prose. Worth naming because
  `census_preempt` read `CLEAN 5/5` in the same minute and its `UNCOVERED` line
  names `inert_surface pins` **first** — the same shape as 06:00's miss, caught
  this time by reading the line instead of the tally.

## Recommended next 1–3 priorities

1. **`split-suite-or-split-cycle`** — still the top structural item. Mark the
   census tests so a repair cycle verifies in ~3 min instead of 25. Until it
   lands, D-421's ordering is the only thing standing between the branch and
   another strand.
2. **`register-remaining-ensemble-modules`** — `source_reach` still convicts ~14
   modules. Do them as **one batch**; three cycles have been spent on one reader
   each.
3. **PR merge (user)** — queue 6/6, 41 days, last merge 2026-07-12.

## Artifacts

- PR: #67 (open) — `autoresearch/p3-epistemic-shadow-cost-critic`
- Files touched: `journal/2026-08/22-11-*.md`, `docs/decisions.md`, `results/p3-epistemic-shadow-cost-critic.tsv`
- TSV row appended: yes

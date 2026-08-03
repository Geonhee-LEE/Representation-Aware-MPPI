# The collapse is real; its reported size never was

- **Cycle**: 2026-08-03 14:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: `STATE#1` (+`STATE#3`) Retract-or-rescope the two verdict-fragile claims (no Notion id — workspace ungranted, 39th cycle)
- **Phase**: P3
- **Status**: keep

## What I tried

- Took STATE #1 as written: D-035 attached surviving effect sizes (14.4 % / 21.8 %)
  to the two verdict-fragile claims, so rescope the `docs/` that cite them at full
  effect. Enumerating the citation sites meant putting the instrument's definition
  next to the prose for the first time.
- They measure different things. Wrote `eval/mppi_sandbox/claim_scope.py` +
  14 tests to bind each divergent claim to its oracle, its instrument, both banked
  readings, and every doc section that states a number for it.
- Stamped and disambiguated the six cited sections (D-030 / D-032 / D-033 / D-017
  / Q-054 / Q-055) with a D-036 rescope blockquote; filed D-036.
- Zero new simulation. Zero new PR — pushed into #67, already in the queue.

## What worked / what failed

- 🔴 **`2.0×` is not what the flipping assertion measures.** D-030's `2.0×` is
  `w(H=34)/w(H=15)` = 13.97/7.00. The assertion that flips computes
  `w(H=34)/w(H=30)` (`SHIPPED_HORIZON=30`, `FREE_H=34`, fixed in code) and reads
  **1.3008** on `AVX512_SKX`, **1.0289** on AVX2. D-032 Decision (0) paired the
  first against the second machine's reading of the second; D-033/Q-054/Q-055
  inherited it. The divergence is real — 1.3008 → 1.0289 does cross the 1.2
  threshold — but every downstream citation overstated its size.
- 🔴 **Three retained fractions, always in the same order.** `horizon_weight_swing`:
  assertion **14.4 %** > reading **9.6 %** > cited-2.0× **2.9 %**.
  `ab_protocol_overstatement`: **21.8 %** > **7.8 %** > **6.1 %**. D-035 computed
  only the first. The third is the one a retraction notice needs, because the
  citation is what readers actually met.
- ✅ **The guard was red on the real defect before I wrote a word of prose.**
  4/6 sections unstamped, 6/6 undisambiguated at registration; 0 and 0 now.
- ✅ Fast half **290 passed / 127 skipped / 1 xfailed, 113.9 s** (was 276).
- ⚠️ Not a retraction. D-030's `H=35` cliff (6.8×) rests on a different measurement
  and stands. Direction and sign are kept; only effect sizes were demoted to
  `AVX512_SKX`-conditional.

## North-star delta

- **No avoidance or tracking number moved — fifth consecutive instrument cycle.**
  Honest reading: this cycle *reduced* the project's stock of believed results
  rather than adding to it.
- What it bought is that the reduction is bounded and checked. Four cycles of
  dispatch work (D-032→D-035) were sized against a number the instrument never
  produced; the true collapse is smaller, and now stated in the same place a
  reader meets the claim.
- The 가려진-obstacle class still has exactly one working cost term (D-027). Scenes
  able to contribute an avoidance number: 5, reportable: 4 — unchanged.

## Key learnings

- **A citation is a separate failure surface from a measurement.** Fragility
  eventually shows up as a red test; citation drift emits no signal at all. The
  repo had instruments for the first and nothing for the second, and the second is
  what propagated for four cycles.
- **Enumerate the citations before pricing the claim.** D-035's bill was arithmetic
  on the right numbers answering a question one level away from the one that
  mattered — the fourth time on this branch the instrument was fine and the framing
  was wrong (D-028 denominator, D-030 relative guard, D-031 fixture scope, D-035
  distance-vs-cost).
- **A guard may only police what it does not share a failure mode with.**
  `claim_scope` runs no simulation — string search and arithmetic over repo files —
  which is the entire basis for letting it check dispatch-fragile claims.
- **"Rescope" beat "retract" on all six sections.** Every one kept its direction;
  only the effect size was conditional. Retracting would have destroyed standing
  results to fix a magnitude error.

## Recommended next 1–3 priorities

1. **Audit the remaining `docs/` numbers the same way** — `claim_scope` covers the
   5 dispatch-divergent claims only. D-028's 6.19×/1.46×, D-029's 2.11×, D-025's
   2.320× are all cited elsewhere and none has been checked against its instrument.
2. **Extend the excursion sweep to the other 122 closed-loop tests** (STATE #2) —
   unchanged, and now with a stronger reason: the sweep should record *which
   quantity* each assertion computes, not just its margin.
3. **Drain the merge queue** — 57 consecutive gate-1 skips, 22.0 d since the last
   merge. Still the only thing that unblocks anything else.

## Artifacts

- PR: #67 (already open; this cycle added 2 commits, no new PR)
- Files touched: `eval/mppi_sandbox/claim_scope.py`,
  `eval/mppi_sandbox/tests/test_claim_scope.py`, `docs/decisions.md`,
  `docs/deliberations.md`, `results/dispatch-divergence/claim-scope.txt`,
  `results/p3-epistemic-shadow-cost-critic.tsv`
- TSV row appended: yes (`sandbox:pass=290/290`, keep)

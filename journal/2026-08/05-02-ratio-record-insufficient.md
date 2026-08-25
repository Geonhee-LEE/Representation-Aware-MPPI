# The ratio grader works; the record it was supposed to read has two points

- **Cycle**: 2026-08-05 02:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: STATE #1 — Q-078: grade on the gap/control ratio instead of stationarity
- **Phase**: P3
- **Status**: keep

## What I tried

- Built D-071's surviving candidate as an instrument: `exclusion_scope.RatioGrade`
  / `ratio_grades` / `ratio_ranking` / `rank_agreement` / `RANK_MIN_N`. **No
  threshold anywhere** — an ordering needs no constant, so this does not create
  the package's fifth unjustified one. A site whose control is exactly zero
  scores `inf` and sits at the top of a *continuum* rather than in its own
  class, which puts "moved 0" adjacent to "moved 2" instead of in different
  verdicts: Q-077's coin flip dissolved rather than adjudicated.
- Denominator = `measured_delta + source_delta`, both frames — D-068's own noise
  budget (it summed 47/42/58 against gaps of 142/84/95). `rank_agreement`
  returns Spearman rho and its `n`, with no p-value and no cut on rho.
- Then took STATE #1's cheap half literally — *no new run, pull the per-site
  ratios out of D-066..D-071's artifacts* — and built `published_ratios` to hold
  every per-site number those six cycles actually printed, each tagged with the
  file it came from, with `unverified()` re-locating every digit in that file.

## What worked / what failed

- ✅ **The grader is clean and the tests bite both ways.** 6 new tests on the
  ratio, 11 on the record; `unverified()` catches a wrong digit *and* an
  off-by-one, so its empty result is not vacuous.
- 🔴 **Q-078's no-new-run half is unanswerable, and not narrowly.** Only two
  readings are licensed (D-070, D-071 — the rest are `TRANSPORTED` under D-069's
  guard). Sites carrying a gap *and* a control on both: **2**, against a floor of
  3. n=2 is not a small sample, it is a degenerate one — every pair of distinct
  2-orderings correlates at exactly ±1.
- 🔴 **The two common sites are exactly the two D-071 quoted.** The licensed
  overlap is `lam_dependence._pure` (214/87 = 2.5×) and
  `guard_reflexivity._is_set_valued` (13/1 = 13×) — the two endpoints of the
  "2.5× to 13×" range D-071 offered as evidence that *the ordering reproduced on
  four trees*. **A two-point ordering reproduces by construction.** Not wrong;
  uncheckable — and (c) was the only survivor D-071 left standing.
- 🔴 **The source-frame control was never published on any tree**, so the ratio
  as the grader defines it has **zero** complete cells. Every ratio quoted to
  date uses the one-frame denominator, which is a different number. Filed Q-079.
- 🔴 **The cause is plumbing, not argument: no reading was ever serialised.**
  `paired_reading` / `replicated_reading` already compute the gap and both frame
  controls for all 7 sites. Six cycles transcribed a hand-picked subset into
  prose and dropped **16 of 33** licensed cells. `missing()` names them.
- ⚠️ **Sixteenth self-entry — and it falsified the story attached to the
  previous fifteen.** `rank_agreement` entered the guard pool (53 → **54**),
  red-flagging `test_and_shaped_guards_are_exactly_these_three`. It is the
  fourth `&`-shaped guard and the first whose intersection names **no registry
  on either side** (`set(a) & set(b)`, both runtime data), so the
  three-cycle-old characterisation "the detector catches only the narrowing that
  names a registry" is false. The demonstration was free and sits in this same
  cycle: `published_ratios.common_sites` does the **identical** intersection via
  `set.intersection(*sets)` and does **not** enter. One narrowing, two
  spellings, one visible — the detector reads the `&` operator, not semantics.
  The recurrence is real; the explanation given for it since D-065 is not.

- ✅ **757 passed** / 153 skipped / 1 xfailed (was 740), re-taken after the 4a
  and 4a-bis writes per D-043/D-044; `declared` clean. Zero runs bought.

## North-star delta

- **No avoidance or tracking number moved — fortieth consecutive instrument
  cycle.** Scenes able to contribute an avoidance number: 5, reportable: 4.
- What moved: the branch's last standing hypothesis is now known to rest on two
  data points, and the reason five cycles could not check each other is named as
  a missing `results/*.json` rather than as a hard measurement problem.
- What moved against the story: this cycle bought **zero runs** and produced
  **zero** new evidence about the fold. It re-priced the old evidence downward.

## Key learnings

- **"The ordering reproduced across four trees" and "n=2" can be the same
  sentence.** The claim was about four trees; the *overlap* those trees share on
  published cells is two sites, and both of them are the ones the claim cites.
  Cross-tree reproduction has to be counted on the intersection, not the union.
- **A rank statistic needs its floor stated before it is computed**, or the
  degenerate case gets reported as a strong result. `RANK_MIN_N` returns `None`
  rather than ±1 for exactly this reason — and this is the first threshold this
  branch has added that is about arithmetic rather than about data.
- **Six cycles of prose is a lossy artifact format, and the loss is not random**
  — every cycle printed the numbers that supported its headline. The 16 missing
  cells are the ones no headline needed.
- What would change my mind: two serialised licensed readings. Then the same
  `rank_agreement` call answers Q-078 for real, at n=7 rather than 2.

## Recommended next 1–3 priorities

1. **Serialise the reading** (STATE #3, now blocking Q-078): have
   `paired_reading` / `replicated_reading` emit `results/*.json` with all 7 sites
   × (gap, measured_delta, source_delta, verdict, tree_key, k). One cycle, no new
   run needed to build it — attach it to the next batch that runs anyway.
2. **Then buy one licensed batch** and compute `rank_agreement` against it at
   n=7, reporting **both** denominators (Q-079) since it costs nothing extra.
3. **Read `lam_dependence._pure` whole** — still the largest gap (214) on the
   newest tree, still unexplained after five cycles.

## Artifacts

- PR: pending merge (`autoresearch/p3-epistemic-shadow-cost-critic`, #67)
- Files touched: `eval/mppi_sandbox/exclusion_scope.py`,
  `eval/mppi_sandbox/published_ratios.py`,
  `eval/mppi_sandbox/tests/test_exclusion_scope.py`,
  `eval/mppi_sandbox/tests/test_published_ratios.py`, `docs/decisions.md`,
  `docs/deliberations.md`
- TSV row appended: yes

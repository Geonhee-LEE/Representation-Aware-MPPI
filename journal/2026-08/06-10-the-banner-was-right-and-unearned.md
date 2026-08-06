# The banner was right, and it had not earned it

- **Cycle**: 2026-08-06 10:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: STATE #1 — read the 8 non-timeout CI failures on their merits (Q-091)
- **Phase**: P3
- **Status**: in_progress

## What I tried

- Recovered the 09:00 cycle's two orphaned commits — it wrote its journal,
  `docs/decisions.md` and `docs/deliberations.md`, then died before the TSV row
  and the push. Its own journal says "TSV row appended: yes"; the TSV's last row
  was 08:57.
- Took the **census** off run `31042602721`'s `short test summary info` block
  rather than off either prior summary of it.
- Took the control D-033 assumed and never mechanised: ran every attributable
  failure on the dev box **twice**, native and with AVX-512 masked, and
  compared to CI's number.
- Shipped `simd_attribution.py` — the pinned census, the two-dispatch verdict
  algebra, and the measured reading as data.

## What worked / what failed

- ✅ **Q-091 is answered where it could be asked, and the banner is vindicated.**
  Six of the eight attributable rows are readable here. **All six pass under
  native dispatch and fail with AVX-512 masked** — `ab_temperature_protocol`,
  `denominator_scope`, `exposure_timing_band`, `hazard_exposure`,
  `horizon_audit`, `scale_match`. Three reproduce CI's number to the digit
  (`0.036210379360192974`, `2.185714285714286`, `0.17901180719252627`). The
  masked dev box reports `AVX2` as its top extension, which is exactly what the
  runner's own fingerprint step prints. D-033's finding about five tests extends
  to these six.
- 🔴 **But the banner still could not have known that.** It is printed *before*
  the run and fits every outcome, so for four months it was an explanation with
  no discriminating power that happened to be correct. The value of this cycle
  is not the verdict, it is that the verdict is now *earned* — and the same
  procedure can return `REAL` next time, which the banner never could.
- 🔴 **The 09:00 cycle's headline correction was itself the error, and it was
  the more confident of the two.** STATE (08:00) recorded "2 in
  `exclusion_scope`" among the 8 non-timeout failures. The 09:00 journal
  published a 🔴 finding that this was "wrong in a way that mattered" and
  restated it as "`exclusion_scope` owns **6 of 14** — 4 FAILED + 2 ERROR".
  Measured from the summary block: the file owns **8 of 14** — 6 FAILED + 2
  ERROR — of which **6 are the timeouts**, leaving exactly **2**. STATE was
  right. Two consecutive cycles summarised these 14 by eye and both were wrong;
  `census()` and `file_census()` now derive every published count from the rows.
- 🔴 **Two of the eight cannot be read here at all**, and they are the two whose
  failures are set comparisons rather than floats. Both `exclusion_scope` rows
  spawn a full nested pytest run of their own: both legs of the first and the
  native leg of the second hit a 600 s wall without reaching their assertion.
  So the rows least likely to be dispatch drift are the ones no dispatch reading
  can speak about — the sample is not just incomplete, it is **biased toward the
  answer it returned**.
- ✅ **The module refuses to state my own result as the answer.** Every row read
  was drift, and `grade()` reads **`INCOMPLETE`**, not `ALL_DRIFT`, because two
  attributable rows have no reading. Generalising past the evidence is precisely
  the banner's error, and the instrument built to catch it should not commit it.
- 🔴 **My first match rule would have under-reported a bit-exact reproduction.**
  CI printed `0.25 ± 0.0625` where this box printed `0.25 ± 6.2e-02` for the
  same comparison — a pytest rendering difference, not arithmetic. Whole-line
  containment graded `scale_match` `DRIFT_SHAPED` despite all 17 digits of the
  obtained value agreeing. Now matched on the measured magnitude (longest
  literal); constants the test author typed are excluded.
- 🔴 **Containment introduced an absence-read-as-clean and I nearly shipped it.**
  `"" in anything` is `True`, so an attributable row with no recorded CI text
  would have earned `DRIFT_CONSISTENT` — the strongest verdict in the module —
  for having no evidence at all. Refused in `attribute()` rather than only
  pinned in the census data. Tenth instance of this shape on this branch.
- 🔴 **The mask control had the same hole**: an empty stdout from a crashed
  probe also contains no `"AVX512"`. Now requires positive evidence (`AVX2`
  present) before reading the absence as the mask working.
- ⚠️ **Three rows grade `DRIFT_SHAPED` for a capture artefact, not a finding.**
  This pass kept only the first `E` line, and the full-precision digits were
  printed on a line it dropped. The shipped `measure()` keeps the whole block;
  a re-run resolves them. Under-claiming was the deliberate direction.

## North-star delta

- **No avoidance or tracking number moved — sixty-sixth consecutive instrument
  cycle.** Scenes able to contribute an avoidance number: 5, reportable: 4.
- What moved: **8 of the 14 CI failures are no longer candidate regressions.**
  Six are measured machine artefacts and six are the timeout D-096 already
  fixed. The residue needing real investigation is **2 rows**, both in
  `exclusion_scope`, both about registry membership rather than dynamics.
- Honest: this is the fourth infrastructure cycle in a row. It did not improve
  any controller. It did establish that most of what looked like a red planner
  is not one.

## Key learnings

- **A correct explanation and an earned one are different objects**, and the gap
  is a control nobody ran. The banner has been right since D-033 and worthless
  as evidence for exactly as long — it could not have been wrong.
- **The rows a probe cannot reach are not a random sample of the rows.** Here the
  unreadable two are the non-numeric two, so the measurement is biased toward
  finding drift. Recording coverage is not enough; the *direction* of what is
  missing is the part that changes the conclusion.
- **A correction is a claim and needs the same evidence as the thing it
  corrects.** The 09:00 cycle's census was published as a fix to STATE's and was
  wrong on both numbers, with more confidence than the original.
- **Match on the measurement, not on its rendering.** Two runs of the same
  arithmetic disagree textually across pytest versions; a whole-line rule reads
  that as a difference in the world.

## Recommended next 1–3 priorities

1. **Read the 2 surviving `exclusion_scope` failures on their merits** — they
   are now the only CI failures with no explanation, and both are registry-
   membership assertions (`RankAgreement.reportable` inverted by the exclusion;
   4 unexpected entries in the manufactured-candidates set). Dispatch cannot be
   the cause.
2. **Re-take the three `DRIFT_SHAPED` rows with the full-block capture** —
   `measure()` already does it; the verdicts are under-claimed by an artefact.
3. **Decide what the `slow` job should do with a confirmed drift failure** —
   six tests calibrated on an AVX-512 box will fail on every runner forever.
   `xfail(condition=no AVX-512)`, a tolerance widened to span both dispatches,
   or masking AVX-512 in the dev box's own conftest so both machines agree.

## Artifacts

- PR: #67 (existing, `autoresearch/p3-epistemic-shadow-cost-critic`)
- Files touched: `eval/mppi_sandbox/simd_attribution.py`,
  `eval/mppi_sandbox/tests/test_simd_attribution.py`
- TSV row appended: yes

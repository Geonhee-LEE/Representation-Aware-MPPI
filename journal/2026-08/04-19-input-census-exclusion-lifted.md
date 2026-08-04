# D-065's declared bound, bought — and it came back negative

- **Cycle**: 2026-08-04 19:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: `STATE-1` Take the input census with the exclusion lifted
- **Phase**: P3
- **Status**: keep

## What I tried

- Gave the input census a **per-origin recorder** (`measure_attributed` /
  `fold_inputs` / `InputSlice`), so one run answers "what would this
  predicate's distinct-input count be if file *X* had been `--ignore`-d" for
  every subset of `EXCLUDED_TESTS` at once. D-064 did this for the value
  census; the trick does not transfer as-is, because a verdict folds a **sum**
  and a distinct count folds a **union** — two files asking the same question
  ask one question between them, and no pair of per-origin *counts* says so.
  So the slice carries the fingerprint **set** (as 8-byte digests).
- Added `scoped_exclusion` / `corrected_inputs`: apply the list **per subject**
  where it was written per file. A site's own instrument stays hidden, every
  other excluded file's questions are restored. Neither the shipped reading nor
  the fully-lifted one.
- `input_undercounts` grades each restored question `SELF_ENTRY` /
  `COLLATERAL` **by execution** (a file attributes iff it supplies a digest no
  surviving file supplied); `manufactured_singles` is
  `manufactured_candidates`' input-census twin.
- Spent 2 runs (325 s + 320 s): the attributed run, and a flat `pi.census()`
  purely as calibration.

## What worked / what failed

- ✅ **The bound is closed, with a negative.** 14 sites are under-counted by the
  exclusion list, 6 of them `COLLATERAL`. **`manufactured_singles` = `()`** —
  not one site was pushed to `distinct == 1` by the ignore list. D-065 feared a
  survivor whose questions came only from an excluded file would read
  `SINGLE_INPUT` on the exclusion's strength; no survivor does. The biggest
  collateral under-counts are enormous in absolute terms and nowhere near the
  boundary: `_has_git_diff_literal` 23509 → 24282, `_is_set_valued`
  9480 → 9786, `_shells_out_to_git_diff` 3068 → 3172.
- ✅ **`unattributed_undercounts` = `()`, and it is structural rather than
  lucky.** A union's every element came from at least one member, so if lifting
  the whole list raises a count, some single file's lift raises it too —
  `UNATTRIBUTED` is a real outcome on the value side and cannot occur here.
  Asserted, not assumed.
- 🔴 **The calibration failed, and that is the cycle's actual finding.** D-064's
  value-side reconstruction agreed with a measured run at 62/62 sites. This
  one disagrees at **7 of 53**. So the input fold is *not* the exact substitute
  the value fold was.
- ✅ **The sign rules out the mechanism I would have blamed.** Six disagree low,
  **one disagrees high** (`_is_set_valued`, +12). A digest collision merges two
  questions into one and can only *deflate* — so the 8-byte digest is not the
  cause, and run-to-run fingerprint variation is (address reprs are flagged on
  9 `MANY_INPUTS` readings; the two runs are two processes).
- ✅ **Verdicts agree completely — 0 disagreements.** `classify` splits at
  `distinct == 1` and nowhere else, so a 142-question error out of 136 242 is
  an error in nothing anything reads. Worst relative gap **0.487 %**.

## North-star delta

- **No avoidance or tracking number moved — thirty-fourth consecutive instrument
  cycle.** Scenes able to contribute an avoidance number: 5, reportable: 4 —
  unchanged. The 가려진-obstacle class still has exactly one working cost term
  (D-027).
- What moved: a bound that two cycles carried as prose is now a measurement, and
  it came back **negative** — which is the outcome that lets the Q-074 (c)
  candidate list be trusted rather than re-audited a sixth time.
- What moved against the story: this is the fourth consecutive cycle whose
  entire subject is the measuring apparatus.

## Key learnings

- **The same counterfactual is exact for one statistic and approximate for
  another.** D-064's fold reconstructs a sum and reproduced a measured run
  exactly; the identical record folding a union misses by up to 0.49 %. The
  difference is not the recorder, it is what the statistic is made of — so
  "reconstruction validated" is a claim about a *reading*, never about a
  mechanism.
- **A calibration should be stated at the granularity the reading is consumed
  at.** Asserting exact counts equal makes this red; asserting verdicts equal
  makes it green; and neither is the softer bar, because the verdict check fires
  where the count band would pass (one question at the boundary is a whole
  finding). Both are pinned by cheap tests now.
- **The sign of an error can eliminate a cause for free.** I was ready to
  attribute the gap to the digest I had just introduced. One positive delta made
  that impossible, at zero extra measurement cost.
- **Fifteenth self-entry, and the absence is the interesting half.** The
  `guard_reflexivity` pool goes 51 → **53** (`fold_inputs`,
  `input_undercounts`); five of this cycle's seven new functions stayed out,
  including `corrected_inputs` — which *is* the correction this cycle exists to
  make. It computes a per-site fold rather than differencing against a named
  registry, so the detector cannot see it. D-065 found the detector blind to a
  *parameterised* narrowing; this is blind to a *per-member* one.
  Separately, `Undercount.manufactured_single`,
  `InputReading.is_single/informative`, `Masked.manufactured_candidate` and
  `Rerank.moved` appear in the under-count table as `SELF_ENTRY` — instrument
  predicates observed only by the files the list hides. (The two pools are
  different things: the `predicate_vacuity` population went 62 → **64**.)

## Recommended next 1–3 priorities

1. **Re-take the population count claims.** The pool moved 51 → 64 predicates
   this cycle (4 refused). Every "exactly N" in `docs/decisions.md` written
   against 62 is now stale.
2. **Ask whether the 0.5 % band is stationary** — a second attributed run
   against the same flat census separates run-to-run variation from a
   systematic fold bias. 1 run.
3. **`guard_vacuity.EXCLUDED_TESTS` has still never been asked this question**
   (STATE #3, unchanged) — its scope argument is sound for coverage, but the
   per-subject/per-file gap this cycle measured is the same gap.

## Artifacts

- PR: #67 (existing — sixty-first consecutive cycle into it, no new review bandwidth)
- Files touched: `eval/mppi_sandbox/predicate_inputs.py`,
  `eval/mppi_sandbox/exclusion_scope.py`,
  `eval/mppi_sandbox/tests/test_predicate_inputs.py`,
  `eval/mppi_sandbox/tests/test_exclusion_scope.py`
- TSV row appended: yes
- Fast half: **702 passed** / 149 skipped / 1 xfailed (was 683), re-taken after
  the 4a/4a-bis writes per D-043/D-044. Measurement cost this cycle: 2
  instrumented runs (325 s + 320 s) + 2 fast-suite runs (313 s + 314 s) — the
  first fast run went red on the `guard_reflexivity` running-tally pin
  (51 → 53), which is the self-entry above and not a regression.

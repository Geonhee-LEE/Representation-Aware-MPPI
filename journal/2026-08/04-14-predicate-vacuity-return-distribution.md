# Predicate vacuity: 7 one-sided of 59, and the top one is the suite's fault

- **Cycle**: 2026-08-04 14:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: `STATE-1` Extend the vacuity scan to non-raising predicates (Q-072 (b))
- **Phase**: P3
- **Status**: keep

## What I tried

- Built `eval/mppi_sandbox/predicate_vacuity.py`: the population is every
  boolean-returning function in the package derived from the AST (comparison /
  `not` / `bool()`-family shape, **or** a `-> bool` annotation), and the reading
  is the **set of values the suite ever observed it return** — recorded by a
  generated pytest plugin that wraps each site in a subprocess suite run.
- Five verdicts: `BOTH`, `ALWAYS_TRUE`, `ALWAYS_FALSE`, `UNOBSERVED`,
  `NON_BOOLEAN`. The candidate set is the two `ALWAYS_*`.
- Calibration is **constructed, not historical** — a scratch package whose four
  predicates have known verdicts, measured through the shipped recorder.
- Triaged the top candidate by **witness** rather than by reading (D-060's rule).

## What worked / what failed

- ✅ **The census runs and yields**: **59** predicates — `BOTH=43`,
  `ALWAYS_TRUE=3`, `ALWAYS_FALSE=4`, `UNOBSERVED=9`, `NON_BOOLEAN=0`; **4**
  refused as unpatchable (3 nested defs + 1 `cached_property`), reported not
  dropped. First non-zero candidate yield since the search began: the guard
  half's was a measured 0.
- 🔴 **The verdict merges two different claims and the call count separates
  them.** `guard_reflexivity._shells_out_to_git_diff` is `ALWAYS_FALSE` after
  **5694 calls**; `exposure.ExposureBand.is_timing_sensitive` and
  `liveness_derivation.Liveness.moved` are `ALWAYS_FALSE` after **one**. Same
  verdict, and only the first is a statement about the predicate — the other two
  are statements about the suite. `by_evidence` orders by count and the report
  leads with it. **No floor is imposed**: an unjustified threshold would be the
  same defect STATE #21 still carries against `wilson_lower_at_least`.
- 🔴 **The top candidate is satisfiable, and the witness says so in three
  lines.** `_shells_out_to_git_diff` looks for a bare `"diff"` constant, and
  `local_only_audit._git("diff", "--name-only", ...)` is exactly that function
  **in this tree**. Constructed both inputs: `True` on one, `False` on the
  other. So 5694 silent calls are an *untested recursive arm*, not a vacuous
  predicate — the same negative D-060 got, reached by the same method.
- ✅ **The calibration set is genuinely 0 and the module ships that as its
  finding.** Of the four motivating findings, the one with precisely this shape
  — D-057's `unseen.min() > 0.0` — lives in a **test**, and the population
  excludes tests for the reason `guard_vacuity` does. So the scan that finally
  reaches D-057's *shape* still cannot reach D-057's *instance*. Rather than a
  mirror over an empty registry (asserts nothing, reads clean — D-046's shape),
  calibration is a constructed 4-verdict witness. Filed as **Q-074**.
- ⚠️ **Tenth consecutive cycle whose module enters populations its own package
  takes — and the first where nothing fired.** No running-tally pin broke.
  Worth stating plainly rather than claiming credit: this cycle's module adds no
  `lam`-arming call site and no new registry member, so the pins were correct to
  stay quiet. It is not evidence they have stopped being fragile.
- ✅ **D-060's self-eating lesson applied before it could bite**: this file is in
  `EXCLUDED_TESTS` from the first commit. Its own tests call its own predicates
  both ways by design; a census watching them would score them `BOTH` for free.

## North-star delta

- **No avoidance or tracking number moved — twenty-ninth consecutive instrument
  cycle.** Scenes able to contribute an avoidance number: 5, reportable: 4 —
  unchanged.
- What moved: the vacuity search's second half is now **instrumented and
  measured**, and unlike the first half it has a non-empty candidate set (7).
  The top candidate is triaged to *untested*, not *vacuous*.
- Fast half **633 passed** / 139 skipped / 1 xfailed (was 618).

## Key learnings

- **A raise is an event; a predicate is a distribution.** Q-072 (b) named this
  and it is the whole reason a second instrument was needed rather than a wider
  `grep`. The coverage census can say *whether a line ran*; only a value
  recorder can say *whether the answer ever differed*.
- **One-sidedness is arithmetic and the call count is the evidence.** `n=1` and
  `n=5694` produce the identical verdict string. Reporting the verdict without
  the count would have made three thin readings look like the 5694-call one —
  the same category error as reporting a pass rate without its denominator
  (D-019).
- **Two censuses, two negatives, same method.** The guard half's yield was 0 and
  the predicate half's strongest candidate is a *suite* gap. The consistent
  finding across D-059/D-060 and this cycle is that this package's checks are
  under-tested rather than vacuous — which is a different repair (add inputs)
  than the one four cycles of hand-found defects suggested (fix the bar).
- **Calibrating a scan against a population that cannot contain its ground truth
  is worse than admitting there is none.** D-059 found its set was 1 where STATE
  claimed 3; this one found 0, and the reason — the instance is in a test — is
  itself the next question.

## Recommended next 1–3 priorities

1. **Q-074: run the predicate census over the test surface.** D-057's instance
   lives there, three of four motivating findings are assertion-shaped, and a
   test assertion that can never fail is the purest form of the defect. Needs a
   different mechanism (pytest rewrites asserts) — that is the question.
2. **Triage the remaining 6 candidates by witness**, cheapest first, and record
   for each whether it is *vacuous* or *untested*. The 5694-call one is done.
3. **Q-073 is still open** — teach `default_lam_sites.simulates` about a guard
   that raises first, letting the witness supply the exemption.

## Artifacts

- PR: #67 (autoresearch/p3-epistemic-shadow-cost-critic), 56th consecutive cycle
- Files touched: `eval/mppi_sandbox/predicate_vacuity.py`,
  `eval/mppi_sandbox/tests/test_predicate_vacuity.py`,
  `docs/decisions.md`, `docs/deliberations.md`,
  `results/p3-epistemic-shadow-cost-critic.tsv`
- TSV row appended: yes

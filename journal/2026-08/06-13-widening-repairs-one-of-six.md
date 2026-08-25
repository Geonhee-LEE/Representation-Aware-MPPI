# Route (b) repairs one of the six, and three of them cannot be priced at all

- **Cycle**: 2026-08-06 13:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: STATE #4 — decide what the `slow` job does with a confirmed drift failure
- **Phase**: P3
- **Status**: in_progress

## What I tried

- Took STATE #1 first and found it **infeasible this cycle**: the `slow` job for
  this branch's head (`6ba40fa`) started 12:14 KST and was still `in_progress`,
  and it runs ~163 min. Q-092's two rows stay unread. Dropped to STATE #4, the
  item STATE itself flags as "the one that actually turns the `slow` job green".
- Priced STATE #4's three named routes — (a) conditional `xfail`, (b) tolerances
  spanning both dispatches, (c) mask AVX-512 on the dev box — against the six
  rows D-098 measured, instead of choosing among them by argument.
- Shipped `drift_repair.py`: parses each CI signature into the shape a repair
  acts on, delegates the band arithmetic to `repair_admissibility.price`, and
  routes.
- Wired route (a) into `eval/conftest.py` as a `pytest_collection_modifyitems`
  hook whose marker set is **derived** from `simd_attribution.verdicts()`.

## What worked / what failed

- ✅ **Route (b) is a special case, not a route: it repairs 1 of 6.** Widening
  needs a two-sided interval and only **two** of the six assertions have one.
  `scale_match` prices at **×1.14** and is admissible; `exposure_timing_band`
  prices at **×2.95**, above `MAX_HONEST_WIDEN`, so the repaired band would
  contain the machine split *and* the original band. Three are one-sided and one
  is a set equality — no widening operator exists for them.
- 🔴 **And the three one-sided ones are not merely inadmissible, they are
  unpriceable — the existing instrument would have answered anyway, and
  reassuringly.** `repair_admissibility` prices a threshold over
  `RATIO_NULL = 1.0` and its own docstring scopes that: *"All four thresholds in
  the divergent set are ratios where 1.0 means no effect."* This population's
  bounds are `> 1.25 × 0.0343`, `< 0.124 / 3` and `> 1.2`, whose nulls are 0, 0
  and 1. Borrowing 1.0 makes **both** terms of `(worst − null)/(lo − null)`
  negative, so the quotient comes out just over **1.0** and reads as *"the repair
  keeps the whole asserted effect."* A negative or a `ZeroDivisionError` would
  have flagged itself; ~100% does not. Pinned as a test, because the failure mode
  is that the wrong answer is comforting.
- 🔴 **Route (a) does not turn the job green, and STATE #4 said it would.**
  14 red = 6 markable + 6 timeouts D-096 fixed + **2 with no reading**. So
  `grade()` returns `RESIDUE`, not green, and the residue is exactly Q-092's
  pair. `refused()` names them and a test asserts `refused() ∩ markable() = ∅` —
  marking those two would be the banner's error with a mechanism behind it:
  an unexplained failure retired as a machine artefact on other rows' evidence.
- ✅ **`strict=True` is the load-bearing argument, not the marker.** A
  non-strict xfail absorbs a pass silently, so the day the numbers converge — a
  numpy bump, a runner change, a real fix — the row stays green and nobody
  learns. Strict makes an XPASS a failure, which re-opens the attribution loudly.
  And on a box where `AVX512_SKX` is present the hook marks **nothing**, so a
  genuine regression still fails here; pinned both ways.
- 🔴 **My own D-047 test committed D-047's error.** The check that the
  `widen_factor = 1 + excursion` identity is delegated rather than restated was
  a text scan, and it fired on this module's own **prose** describing the
  delegation. Same literal-scan hazard D-095 paid for, one cycle later, in the
  test written to prevent it. Now strips docstrings via `ast` *and* pins the
  delegation behaviourally, so a local recomputation that drifts fails on the
  number rather than on a string.
- 🔴 **The imprecision flag cannot discriminate, and says so.** `± 0.05` trips
  it at 1 s.f. and is exact; `± 6.2e-02` trips it at 2 and is a rounding of
  0.0625. One line of text cannot tell them apart, so the flag only ever *caps*
  reported digits — false positives under-claim and false negatives are
  impossible. Reading the declared tolerance from source is the fix; not this
  cycle's.
- 🔁 **Census 73 → 74, twenty-ninth consecutive cycle, and D-089's rule
  predicted it for the third time running.** `routes` entered — the loop filter,
  bookkeeping. `price_widening`, the function the module exists for, is
  invisible: three shape comparisons. Sharper detail: the one expression the
  detector sees here is `{DRIFT_CONSISTENT, DRIFT_SHAPED}`, **the same
  two-element inline set** whose `&` made D-098's `grade` visible last cycle,
  now spelled `not in`. Two modules, two operators, one literal.
- ✅ `sandbox:pass=1188/1188` after the pin update (the pre-update run read
  `1 failed, 1187 passed` — that one failure was the census pin).

## North-star delta

- **No avoidance or tracking number moved — sixty-seventh consecutive instrument
  cycle.** Scenes able to contribute an avoidance number: 5, reportable: 4.
- What moved is the **cost of the red**: 6 of the 14 CI failures now have a
  mechanism that turns them from noise into declared, strictly-guarded expected
  failures, leaving a residue of 2. The `slow` job stops being uniformly red and
  starts being red about something specific.
- Route (c) is now priced and can be declined with a number: it unmeasures **6**
  assertions at once, which is the D-017…D-098 re-baseline bill, not a repair.

## Key learnings

- **An instrument scoped to one population will answer about another, and the
  wrong answer is not always ugly.** `RATIO_NULL` produced ~100% retained for a
  claim whose null it had wrong. D-097 found a fraction reported as a total;
  this is the same defect where the misuse *reads as good news*, which is worse.
- **A repair route is not a policy, it is a per-claim property.** "Widen the
  tolerances" sounds like a choice about the suite; it is defined for 2 of 6
  assertions and admissible for 1. The routes were listed as alternatives and
  are not commensurable.
- **A marker keyed on the machine needs a license keyed on the test.** The
  dispatch condition says *where*, D-098's per-test reading says *which*; using
  only the first would have swept in the two rows nobody has read.
- **The test I wrote to enforce single-statement discipline broke it.** Third
  time on this branch that a literal scan read prose as code. The fix is always
  the same shape: scan the AST, or assert the behaviour.

## Recommended next 1–3 priorities

1. **Read the 2 surviving `exclusion_scope` failures (Q-092)** — still #1, and
   now the *entire* residue. This branch's `slow` run from 12:14 KST should be
   readable by ~15:00.
2. **Apply `scale_match`'s ×1.14 widening** — the one row route (b) can repair
   honestly, which would shrink the xfail set from 6 to 5. Route (a) is a holding
   action; a widened band still asserts the target.
3. **Read the declared tolerances from source rather than from CI's line** —
   removes the imprecision flag's guesswork and would let the factors be quoted
   to full precision.

## Artifacts
- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic, PR #67)
- Files touched: `eval/mppi_sandbox/drift_repair.py`,
  `eval/mppi_sandbox/tests/test_drift_repair.py`, `eval/conftest.py`,
  `eval/mppi_sandbox/tests/test_guard_reflexivity.py`, `docs/decisions.md`,
  `docs/deliberations.md`
- TSV row appended: yes

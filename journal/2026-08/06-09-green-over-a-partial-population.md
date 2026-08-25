# The green covered 87.6% of the suite, and the failures were in the rest

- **Cycle**: 2026-08-06 09:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: STATE #1 — read the 8 non-timeout CI failures on their merits
- **Phase**: P3
- **Status**: in_progress

## What I tried

- Pulled the full failure census off run `31042602721`, the first `slow` job
  ever allowed to finish, instead of reading STATE's summary of it.
- Read the 8 non-timeout failures and looked for a common cause.
- Found one, but not the one I went looking for: **all 14 failures live outside
  the population the local push gate measures.**
- Shipped `suite_coverage.py` + an `UNCOVERED_RED` verdict in `push_preflight`,
  so a green over part of the suite has to say which part.

## What worked / what failed

- 🔴 **STATE's census was wrong in a way that mattered.** It recorded "2 in
  `exclusion_scope`" among the 8 non-timeout failures. The truth: `exclusion_scope`
  owns **6 of the 14** — 4 FAILED + 2 ERROR — and **all 6 timeouts are inside
  that one file**. The 900 s timeout D-096 fixed and the "8 remaining" were
  never disjoint sets the way the summary implied.
- 🔴 **The headline, and it is not about the 8.** The local gate runs
  `pytest ... -q` with no `--slow`: **1092 of 1246 collected**, 154 skipped. CI's
  `slow` job runs the other **154**, and published `12 failed, 138 passed,
  2 errors`. So `sandbox:pass=1091/1091` — quoted in the journal, the TSV row and
  the Telegram message of **89 consecutive cycles** — was a true statement about
  **87.6%** of the suite, and **100% of the known failures were in the 12.4% it
  excluded**. The gate was never wrong about what it measured. It was silent
  about what it declined to measure.
- 🔴 **The counts were already in the receipt.** `push_preflight.EXECUTED_OUTCOMES`
  has named `skipped` and `deselected` since it was written, with a comment
  explaining that a run which skipped all 400 collected "asserted nothing". The
  subtraction was performed correctly and the remainder was **discarded**. The
  rule was then applied to exactly one number, `executed == 0`. This is D-095's
  finding one cycle later — an instrument complete, its dial unread — now found
  in the gate standing between every cycle and its push.
- 🔴 **The log carries a pre-registered excuse that would have absorbed all 8.**
  The session banner prints `AVX512_SKX ABSENT; ... a closed-loop failure here is
  most likely dispatch drift, not a regression (D-033)`. Several failures fit it
  numerically (`scale_match` misses its band by 4.5%; `ab_temperature` moves
  1.054× where 1.25× is required). But an explanation printed before the
  measurement, that fits every outcome, discriminates nothing — and accepting it
  means the `slow` job can never be red for a real reason. Not resolved this
  cycle; recorded as Q-091 rather than assumed either way.
- ✅ **Two of my own defects, both caught by running it.** Grading `EMPTY` off
  `population` made an all-skipped run read `PARTIAL` — the vacuous case arriving
  as a near-miss; keyed on `executed` so it agrees with `VACUOUS` by construction.
  And the end-to-end fixture conflated the tree axis with the coverage axis,
  reaching `UNDECLARED` first, so it passed **only on a clean worktree** — which
  is never, including in the cycle that wrote it.
- ✅ **The existing suite caught the addition.** `test_every_verdict_is_reachable`
  refused a seventh verdict with no witness — D-079's rule, working, unprompted.
- ✅ **Census cost zero.** Second consecutive cycle. The new prose sits in a
  module docstring, not in `SCANNED_DOCS`.

## North-star delta

- **No avoidance or tracking number moved — sixty-fifth consecutive instrument
  cycle.** Scenes able to contribute an avoidance number: 5, reportable: 4.
- What moved is the **denominator of every number this branch has published**.
  The 89-cycle record of green is not falsified — it is re-scoped to the 87.6%
  it was always about, and the part it excluded is now known-red and named.
- Honest: this is the third infrastructure cycle in a row and it did not read
  the 8 failures on their merits, which is what STATE #1 asked for. It found the
  reason reading them locally would have proved nothing.

## Key learnings

- **A gate that reports a fraction as a total is not wrong, it is unscoped** —
  and the fix is not to widen the gate (162 min against a 35 min cycle) but to
  make it name its own population. Coverage and outcome are orthogonal; this
  package had a vocabulary for the second and none for the first.
- **"Emptiness before success" has a population parameter nobody supplied.** The
  rule was applied to whether *anything* ran, never to whether the *subject* was
  in what ran. Same shape as D-091's missing subject test, one level up.
- **A conjunction is what keeps a real guard from becoming a muted one.**
  Partiality alone is the normal state here; refusing on it would have been
  deleted within a day (D-042). The defect is partiality plus a known-red
  remainder, and that needs a fact from outside — injected, not fetched, so the
  refusal is clearable offline.
- **A pre-registered explanation that fits every failure is not evidence.** The
  SIMD banner is the shape of a claim that can never be red.

## Recommended next 1–3 priorities

1. **Discriminate the SIMD excuse (Q-091)** — run the 8 locally under `--slow`
   and classify each `REAL` vs `DRIFT_CONSISTENT`. The local box's dispatch is
   the control the banner assumes and nobody has taken.
2. **`exclusion_scope` owns 6 of 14** — a file-level census of the failures
   before treating them as 8 independent findings.
3. **Feed the uncovered verdict in for real** — `ci_verdict.fetch_latest` already
   returns it; the cycle order should pass it to `check` so the refusal fires
   without being asked.

## Artifacts

- PR: #67 (existing, autoresearch/p3-epistemic-shadow-cost-critic)
- Files touched: `eval/mppi_sandbox/suite_coverage.py`,
  `eval/mppi_sandbox/push_preflight.py`,
  `eval/mppi_sandbox/tests/test_suite_coverage.py`,
  `eval/mppi_sandbox/tests/test_push_preflight.py`
- TSV row appended: yes

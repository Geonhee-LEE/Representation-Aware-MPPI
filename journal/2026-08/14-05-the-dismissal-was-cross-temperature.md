# The dismissal was cross-temperature — and the verdict survives being earned properly

- **Cycle**: 2026-08-14 05:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: `STATE-1` Re-read D-243–D-246's headline claims against the graded key
- **Phase**: P3
- **Status**: keep

## What I tried

- Split STATE's "which of the four survive" by **temperature**, which is the axis
  the branch has already convicted itself on. D-245/D-246 sit at
  `PAIRED_LAM = 0.8` and **D-250 re-read that exact grid at that exact
  temperature** — they are graded. D-243/D-244 sit at `D243_LAM = 0.1` and
  **nothing had re-read them**.
- Noticed that D-250's journal nonetheless calls D-243's `2/3 → 0/3` headline
  "an artifact", reaching that from the `lam = 0.8` grid — across the one gap
  D-244 established and `test_the_freeze_reading_is_not_comparable_across_temperatures`
  pins (3.30 s → 81.90 s, same seed/arm/scene).
- Took the missing reading: `freeze_weight.sweep` at `lam = 0.1`, both scopes off
  one simulation, at **n=3** (D-243's ensemble) and **n=12** (D-244's).
- Shipped `headline_rescope` — the four headlines as records with their
  coordinates, and a `regrade` that **refuses** cells from a different
  temperature or seed count instead of grading them.

## What worked / what failed

- **Both lam=0.1 headlines are void, and now for a measured reason.**
  n=3: ablation `0/3` exceed pre-arrival (median longest **0.30 s** vs the
  declared **2.0 s**) → `NO_FREEZE_TO_PRICE`. n=12: ablation `0/12`, median
  **0.40 s**. `D-243 VOID_POST_ARRIVAL`, `D-244 VOID_POST_ARRIVAL`.
- **The old columns reproduce digit for digit**, which is what licenses the
  re-read as a re-read. n=3 whole: `2, 3, 1, 0, 3` — D-243's published sequence
  exactly. n=12 whole: `6, 6, _, 0, 0` with clearance `0.9207 / 0.9205 / 0.9211`
  — D-244's numbers to four decimals. Same curve, one scope moved.
- **D-243's non-monotonicity half dies too.** `1e2` was headlined as *worse than
  not wiring the term at all* (3/3); arrival-scoped it is **0/3**, identical to
  the ablation. D-244 had already downgraded that cell to noise at n=12; the
  scope re-read kills it at n=3 as well.
- **The upper failure is partly censorship, not freeze.** At `1e5` (n=12) only
  **7/12** arrive; at `3e5`/`1e6`, **0/12** — so `before == whole` there by
  construction. The high-weight exceedances are arrival-censored runs, the same
  shape D-250 found at the paired lam.
- My own test caught me once: the unpublished-grid-point fixture used n=1 cells
  and so could not express D-244's `6/12`. The module was right; the fixture was
  not expressive enough to state the claim.

## North-star delta

- Two accepted decisions moved from "quoted as measured" to **measured-void**,
  at their own temperature rather than by inference from another one.
- No movement on the planner itself. `ProgressPriceCritic` is now unsupported at
  **both** temperatures — the term has no demonstrated cell anywhere on this
  scene, which is a subtraction from the branch's claim surface, not an addition.
- New guard: a re-read that crosses a temperature or a seed count is now a
  refusal (`NOT_COMPARABLE_LAM` / `NOT_COMPARABLE_N`) rather than a caveat.

## Key learnings

- **A right conclusion reached across a known-invalid comparison is still debt.**
  D-250's verdict on D-243 was correct and its evidence was not; this cycle cost
  ~2 minutes of simulation to convert one into the other. The cheap version of
  this lesson is that the branch had already written the non-comparability down
  *and tested it*, and still crossed it one cycle later in prose.
- **The refusal has to outrank the verdict it would have returned**, or it never
  binds. Pinned directly: on cells that would produce `VOID_POST_ARRIVAL`, a
  wrong `lam` still returns `NOT_COMPARABLE_LAM`.
- **Grade the ablation, not the optimum.** All four headlines presume the
  ablation fails, so one predicate decides all of them — which is why the
  re-read is one `verdict()` call and not four bespoke comparisons.
- Arrival censorship and freeze look identical in a whole-scope column. Any
  future high-weight claim on this scene needs its `arrived` count beside it.

## Recommended next 1–3 priorities

1. **Amend D-243–D-246 in place with a `Status: superseded-by-D-253` line** —
   the entries still read as accepted and a cold reader has no signal.
2. **Resolve Q-146** — `admissible` clause 2 reads `n_reached` (xy at final step)
   while `n_arrived` (xy+yaw at any step) is the predicate the scope needs;
   at `1e5` they differ 12 vs 7.
3. **Decide whether `ProgressPriceCritic` ships at all** — it now has no
   supported cell at either temperature; keeping an unmeasured cost term is
   exactly what D-021 forbids.

## Artifacts
- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic)
- Files touched: eval/mppi_sandbox/headline_rescope.py, eval/mppi_sandbox/tests/test_headline_rescope.py, docs/decisions.md
- TSV row appended: pending

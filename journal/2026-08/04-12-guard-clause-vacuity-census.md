# The systematic guard-vacuity pass — and its calibration set is 1, not 3

- **Cycle**: 2026-08-04 12:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: STATE #1 — grep the package for guard clauses whose trigger cannot occur
- **Phase**: P3
- **Status**: keep

## What I tried

- Built `eval/mppi_sandbox/guard_vacuity.py`: discover every `if <cond>: raise <Exc>`
  in the package from the AST, run the fast suite under `coverage`, and partition
  the guards by what the suite did to them.
- Three verdicts, not two: `FIRES` (the `raise` line executed), `NEVER_FIRED`
  (the enclosing function ran, the `raise` did not — the candidate set), and
  `UNREACHED` (the function never ran, so the guard's silence is the function's).
- Pinned the one guard whose answer is known — D-058's `shadow_batch` `ValueError`
  — as `CALIBRATION`, with `miscalibrated()` as the mirror.
- Triaged 3 of the 8 candidates by hand against what their callers guarantee.

## What worked / what failed

- 🔴 **STATE #1's premise was wrong and the module says so.** STATE claimed "three
  known members now calibrate the search". They do not calibrate *this* search:
  of the four findings of this shape (D-055→D-058), exactly **one** is a guard
  clause. D-057's defect is a boolean bar (`unseen.min() > 0.0`), D-056's is a
  verdict comparison, D-055's is a fixture reading. They share the shape — a
  predicate offered its population and never biting — but three of the four are
  not reachable by scanning for `raise`. Calibrating against 3 members a scan
  cannot contain is D-045's shape one more time, so `CALIBRATION` carries 1 and
  a test asserts it stays 1.
- ✅ **The census runs and the calibration passes.** 38 guard clauses;
  **`FIRES=19`, `NEVER_FIRED=8`, `UNREACHED=11`**; 10 unconditional raises
  excluded. `shadow_batch` reads `FIRES` — D-058's fix, which pinned a test that
  makes the guard raise, is what the instrument reads off the tree.
- ⚠️ **The candidate set is mostly untested validation, not unfirable triggers.**
  I triaged 3 of the 8. `repair_admissibility.margin_at_factor` (`factor <= 0`)
  and `weight_units.batch_per_unit_spread` (`path is None`) are ordinary
  argument checks nothing feeds a bad value. `ab._n_reached` (`n_reached < 0`)
  looked like the real thing — `-1` is a live sentinel default on `LamProbe` —
  but the trigger is satisfiable by any hand-built or historical probe; the
  suite simply never supplies one. **0 of 3 are D-058's shape.**
- ✅ 16 tests, 8 min for the full census (coverage over the fast half), 3 s for
  the scoped calibration test.

## North-star delta

- **No avoidance or tracking number moved — twenty-seventh consecutive instrument
  cycle.** Scenes able to contribute an avoidance number: 5, reportable: 4.
- What moved: the "guard whose trigger cannot occur" search is now a **derived
  population of 38 with a stated exclusion set**, replacing four cycles of
  hand-finding. The candidate set is 8, small enough to walk exhaustively.
- What moved against expectation: the yield estimate. Four hand-found instances
  suggested a rich seam; the first systematic pass says 0 of the 3 triaged are
  instances, and the honest read is that hand-finding was selecting on a shape
  that mostly lives *outside* `if ...: raise`.

## Key learnings

- **A scan's calibration set is bounded by its population, not by the finding
  history that motivated it.** Four findings of one shape, one of which the scan
  can see. Writing 4 into `CALIBRATION` would have made the mirror assert over
  guards that cannot exist — permanently red, then muted, which is D-043's
  failure mode.
- **`NEVER_FIRED` is a necessary condition, and necessary conditions have to be
  priced.** 8 candidates, 3 triaged, 0 confirmed. The instrument's value is that
  the remaining 5 are *enumerable*; it is not evidence that any of them is a bug.
- **The productive seam is probably not guard clauses.** Three of the four
  motivating findings are predicates that *return* rather than raise — bars,
  comparisons, boolean properties. A scan over `if ...: raise` structurally
  cannot reach them, which is the next instrument's population.

## Recommended next 1–3 priorities

1. **Triage the remaining 5 `NEVER_FIRED` candidates.** Bounded, static, no sim.
2. **Extend the scan to non-raising predicates** — boolean properties and
   comparison-returning functions, where 3 of the 4 motivating findings actually
   live. This is where the yield is, if there is any.
3. **Run the census over the `--slow` half too.** A guard that only fires under
   `--slow` currently scores `NEVER_FIRED`; that bound is reported, not fixed.

## Artifacts

- PR: #67 (existing — this branch adds no new review-queue depth)
- Files touched: `eval/mppi_sandbox/guard_vacuity.py`,
  `eval/mppi_sandbox/tests/test_guard_vacuity.py`, `docs/decisions.md`,
  `results/p3-epistemic-shadow-cost-critic.tsv`
- TSV row appended: yes

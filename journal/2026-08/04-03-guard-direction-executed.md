# The shape names a cause that never fires — and removing a duplicate deleted a guard

- **Cycle**: 2026-08-04 03:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: STATE #1 — give `revocable` a direction test (Q-065 (b))
- **Phase**: P4 (instrument lane; the branch is P3-scoped)
- **Status**: keep

## What I tried

- Built `eval/mppi_sandbox/guard_direction.py`: for each `DIFFERENCE`-shaped
  guard × each declared local-only path, stand up a throwaway git repo in
  D-011's situation, take the **permitted** state (edited, unstaged), read the
  guard, **commit the offence**, read again. 10 readings, no simulation.
- Verdict by **membership** — does `after` name the path just committed — not by
  cardinality. Every probe carries a liveness act first, so `SILENT` means
  *blind to this offence* rather than *dead*.
- Split the two sufficient causes: read each guard again with its registry
  filter suppressed (`declared={}` / the unfiltered population), to separate
  *blinded by the exemption* from *blinded by the collapse*.
- Extracted `local_only_audit.staged_changes` so the probe reads the guard's own
  population instead of re-deriving it.

## What worked / what failed

- ✅ **Q-065 answered, and the answer is stronger than "no".** `staged_declarations`
  names its offence on all 5 paths; `undeclared_drift` is `SILENT` on all 5.
  But `quieter` — the collapse `revocable` actually models — is **0 of 10**. The
  blind guard's reading does not shrink; it is `()` on **both** sides.
- ✅ **Why: two sufficient causes, and the one in the AST is masked.** With the
  allow-list suppressed the offending path *is* in the population before the
  offence (`raw_before = (path,)`) and gone after (`raw_after = ()`), so the
  collapse is real — but the exemption has already removed it, so the collapse
  can never be *observed*. `masked` = 5 of 10. D-047/D-049 attributed the
  blindness to the act emptying the population; the act is not what empties it.
- 🔴 **Second finding, and it is the one that would have bitten: extracting a
  helper deleted a guard from the guard registry.** Rewriting
  `staged_declarations` as `sorted(staged_changes(...) & REGISTRY)` — the
  duplicate-removing refactor D-045→D-049 kept prescribing — made its left
  operand a bare call. `_is_set_valued` does not follow same-module calls;
  `_difference_kind` always has. The two predicates read *the same expression*
  at different depths, the `BitAnd` arm was skipped, and the guard vanished.
  Not downgraded — **absent**.
- 🔴 **And the shallow predicate was hiding two more, independent of my edit.**
  Deep-scanning HEAD's own source gives **30**, not the 28 D-049 shipped:
  `local_only_audit.derived_local_only` and
  `weight_units.closed_loop_per_unit_spread` were never in the population.
  **Seventh of the last eight cycles** whose scan was wrong about its own
  population, and again under-counting.
- ✅ **My own completeness check caught the deletion.** `stale_probes()` (the
  mirror of `unprobed_revocable()`) went non-empty the moment the guard dropped
  out. Written as a pair on principle; earned its place in the same hour.
- ✅ **The liveness check caught the probe's own first bug**: `git add` on a file
  identical to `HEAD` stages nothing, so the first draft's act was a no-op and
  read empty. Pinned as a test.
- ⚠️ **`revocable` is unchanged at 2** — every guard the wider scan admits is
  `ENUMERATION`, so Q-065's population survived both corrections. Stated because
  a population correction that *had* moved it would have invalidated the probe.

## North-star delta

- **No avoidance or tracking number moved — eighteenth consecutive instrument
  cycle.** Scenes able to contribute an avoidance number: 5, reportable: 4 —
  unchanged. The 가려진-obstacle class still has exactly one working cost term.
- What moved: the guard suite's population is +2 at HEAD and its one known blind
  spot now has an executed mechanism rather than an inferred one.

## Key learnings

- **A structural predicate can name a cause that is real and unobservable.** The
  collapse `revocable` models does happen — under `declared={}`. It is pre-empted
  by a second sufficient cause the shape does not model. Counting matches of a
  shape is not counting occurrences of a failure, even when the shape is correct.
- **The fix the last five cycles kept prescribing is itself unobserved.**
  "Remove the duplicate statement" is what D-045→D-049 concluded each time, and
  performing it silently deleted a guard. Refactors are inside the verification
  surface the same way REPORT-phase doc writes are (D-043).
- **Two predicates over the same expression must agree on depth.** The scan had
  one following same-module calls and one not, for as long as both have existed.
- **A mirror written on principle pays within the hour.** `unprobed_revocable` /
  `stale_probes` cost ~10 lines and were the thing that reported the deletion.

## Recommended next 1–3 priorities

1. **Audit the scan's remaining predicates for depth disagreement** (Q-066) —
   `_provenance`, `_enclosing_population` and `core_name` all resolve
   expressions, and D-050 shows one mismatch was load-bearing for ~30 cycles.
2. **Give the exemption-masking check a home outside `guard_direction`** — every
   `TYPED` exemption whose set intersects its own guard's population is a
   candidate mask, and that is a static screen the 32-guard pool can take now.
3. **Derive `NAME_SCOPE_CLAIMS` instead of typing it** (prior STATE #1b) —
   still the one registry in the package that fails by under-detection.

## Artifacts

- PR: #67 (open, 45th consecutive cycle writing into it)
- Files touched: `eval/mppi_sandbox/guard_direction.py` (new),
  `eval/mppi_sandbox/guard_reflexivity.py`, `eval/mppi_sandbox/local_only_audit.py`,
  `eval/mppi_sandbox/tests/test_guard_direction.py` (new),
  `eval/mppi_sandbox/tests/test_guard_reflexivity.py`
- TSV row appended: yes

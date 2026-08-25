# The ratio refuses to return a number

- **Cycle**: 2026-08-21 08:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: STATE next-actionable #1 — execute Q-176's (b)
- **Phase**: P3
- **Status**: keep

## What I tried

- Executed Q-176(b), carried since D-397: `second_ratio` /
  `second_baseline_ratio` now return `float | None`, and `second_clears_floor`
  returns `bool | None`. The arithmetic moved to `second_ratio_raw` /
  `second_baseline_ratio_raw`; the gate is `scene_mark(SECOND_SCENE)`, derived
  from `ungradeable_scenes()` rather than naming a scene (D-396's rule).
- `marked()` grew a `None` branch printing `--‡` at the same column width — an
  unreadable cell that printed blank would read as a formatting gap, not a
  refusal.
- The 8 test citation sites moved to the `_raw` accessors; a new test asserts
  the gate is *closed* (all four gated readings `None`) while the raw
  arithmetic is still `0.07`, and that a gradeable endpoint is untouched.

## What worked / what failed

- **The census moved `+2`, exactly the shape STATE predicted, and the targeted
  subset caught it in 6m16 instead of a 22-minute suite.** `scene_scoped_claims`
  went 5 → 7 and `citation_sites` 8 → 12. Both `_raw` helpers are LOAD_BEARING
  *by the census's own definition* — they return a float over the population of
  two — so the split does not launder them out of the audit, and a test now
  says so.
- **The `None` branch I first wrote into `second_verdict` was dead code, and I
  removed it.** `scene_mark(SECOND_SCENE) != ""` requires *every* held column to
  be degenerate, which entails the TVaR column is — so the existing `excited()`
  short-circuit is strictly **stronger** than the new gate and no `None` could
  reach past it. D-397 called that precondition "unrelated"; it is unrelated in
  subject but not independent in extension.
- `unmarked_print_sites()`, `drift()` and `uncited_by_tests_only()` all still
  return `()` — the change did not open a hole in the detectors that were
  repaired in D-396.
- 97 passed on the targeted subset (`test_tail_mean` + `test_column_alignment`
  + `test_guard_reflexivity`), first try. The 8-cycle streak of first-suite RED
  on `+1` census shapes did not repeat, because the census was re-derived from
  source *before* the pins were typed rather than after.

## North-star delta

- **Zero planner movement — 31 cycles.** 0 rollouts; no controller,
  representation or dynamics code touched. This is instrumentation honesty, not
  navigation.
- The one concrete gain: the degenerate cell's census row now prints `--‡`
  instead of `0.07x‡`. A number that cannot be read cannot be mis-cited, which
  is the failure mode that produced D-390's retraction, D-392's non-existent
  defect and D-396's seven false findings.

## Key learnings

- **A type-level defence and a precondition can be strictly ordered, and it is
  worth checking which.** I nearly shipped a `None` branch that no input could
  reach. The check was two minutes of reading `ungradeable_scenes()` against
  `excited()`; the failure mode it avoided is precisely D-396's "green by
  coincidence", inverted.
- **Re-deriving a census before typing its pin is much cheaper than after.**
  Eight consecutive cycles paid a 22-minute RED suite to be told a count moved.
  One `python3 -c` printed the new count in seconds.
- **The split's honesty depends on the raw helpers staying in the audit.** If a
  later cycle exempts `*_raw` from `scene_scoped_claims` to tidy the count, the
  gate becomes a way to keep citing the number rather than a barrier to it.

## Recommended next 1–3 priorities

1. **Price the receipt suite against the budget (STATE #2, still unstarted).**
   This cycle again overran on it, and the targeted-subset result suggests the
   question has an answer: a scoped subset found the real defect shape in 6m16.
   Ask whether a scoped receipt can license a push. Worth a Q-NNN.
2. **Guard the `*_raw` exemption risk** — a test asserting that every
   `second_*_raw` helper appears in `scene_scoped_claims` as LOAD_BEARING, so
   the tidy-up above goes red rather than quiet.
3. **Anything with a rollout in it.** 31 cycles of guard work is the honest
   read of this branch.

## Artifacts

- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic)
- Files touched: eval/mppi_sandbox/tail_mean.py, eval/mppi_sandbox/tests/test_tail_mean.py
- TSV row appended: yes

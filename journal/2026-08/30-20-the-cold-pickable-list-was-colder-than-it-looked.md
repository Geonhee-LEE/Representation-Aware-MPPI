# The cold-pickable list was colder than it looked

- **Cycle**: 2026-08-30 20:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: `strand-discharge` (STATE #1: fix the 9 census-pin failures)
- **Phase**: P5
- **Status**: in_progress

## What I tried

- Phase 1 `cycle_artifacts stranded` fired rc=1: 7 commits ahead of origin,
  4 stranded journals, 2 ungraded. Discharging outranked the decision tree
  (D-112). STATE.md's own `#1 claude-actionable` was exactly this repair, so
  PLAN was a one-line decision.
- Took the 10:00 cycle's "cold-pickable" list at face value and worked
  through it: `extremum_reading` (unregister site), `test_guard_direction`
  (scalar count), `test_exemption_control` (×3), `test_exemption_masking`
  (×2). All five trace to one cause — D-492's `obstacle_instrumentation.py`
  added a typed registry (`UNMEASURABLE_CLASSES`) and three readers of it.
- Verified each fix by direct introspection (`sweep()`, `uncontrolled()`,
  set equality) rather than by re-running the full suite, since the suite
  costs ~13 min and `test_exemption_masking.py` alone owns a 161–400s
  session fixture (`shared_screen`).

## What worked / what failed

- The list was **not** cold-pickable at the stated price. The 10:00 journal
  named "mostly +1 bumps," but `exemption_masking`'s `by_route` pin needed
  +3 (three new `UNMEASURABLE_CLASSES` readers, not one), and its
  `skipped`-pair bound needed +2 for a reason the 10:00 diagnosis never
  named: `format_table` and `uncovered_classes` both go `UNRUNNABLE` under
  suppression on the literal `가려진` class, the same shape `tail_stability
  .drift` already carries. `census_preempt`'s `Not covered:` line explains
  why nobody saw this coming — both `exemption_control.REGISTRIES` and
  `extremum_reading.SITE_CLASSES` are in its declared blind spot, same as
  10:00 found.
- Ran the full suite once, stale (started before any fix landed), and
  killed it after ~19 min CPU when I realized it could not validate
  anything I was about to write. Should have read the 10:00 journal's exact
  failure list before starting a suite, not after — the list was already on
  disk.
- `test_exemption_masking.py` alone (single file, one `shared_screen` call)
  confirmed 2 real failures pre-fix and I could not afford a second run
  post-fix: `cycle_wallclock elapsed` read `SUITE_UNAFFORDABLE` at 28m25,
  9m45 past the suite-start deadline. The masking-file diagnostic run
  (400.87s) alone consumed most of the remaining budget.
- **The receipt was not taken.** All four files are fixed and committed
  (`07698df`, `f0bbfcc`), each fix verified individually by introspection,
  but the branch is not pushed and STATE's "9 census-pin failures" bottleneck
  is not provably cleared by a suite — only by five separate, targeted
  readings. `push_preflight check` will refuse without a green `record`.

## North-star delta

- No movement. Eighth consecutive cycle (D-486 → … → this one) whose
  artefact is a removed obstruction rather than an added capability. Still
  no rollout since 2026-08-29 01:00.
- What it buys: the repair STATE named is now fully authored and committed,
  five distinct pin fixes instead of the four the 10:00 diagnosis predicted.
  Next cycle's job shrinks to "run one suite, then push" — no more analysis.

## Key learnings

- A "cold-pickable" repair list is a claim about *what* changed, not about
  *how much*. D-492 touched one file and one registry, but three different
  functions read that registry in three different ways (a renderer, a
  membership check under suppression ×2), so the blast radius across the
  five census files was uneven — 1, 1, 1, 3, 2 — even though the root cause
  was singular.
- Killing a stale background suite is worth doing the moment you notice it
  cannot validate anything, not after watching it run further. 19 CPU-minutes
  were spent proving nothing once the fix edits made it moot.
- `cycle_wallclock elapsed` is exactly as useful as advertised: it caught the
  budget crossing in time to stop before starting a second unaffordable
  suite, which is the failure mode D-181 exists to prevent.

## Recommended next 1–3 priorities

- **Run `push_preflight record` then `check`/push — nothing else.** All five
  fixes are committed and individually verified; the only remaining work is
  buying the one suite this cycle could not afford and pushing 9 commits.
  Should take one suite's wall-clock and no analysis.
- **After push: `inert_surface probe`/`reprobe`.** Staging this cycle's edits
  reported `STAGED_MOVED` — 5 pins (`JOURNAL.md`, `RESULTS.md`, `STATE.md`,
  `journal/`, `results/`) withdrawn because this cycle "added a reader."
  Priced as D-207 (a cost, not a failure) but worth clearing so it doesn't
  compound.
- **Extend `census_preempt` to cover `exemption_control.REGISTRIES` and
  `extremum_reading.SITE_CLASSES`.** Both sat in its `Not covered:` line
  through two consecutive cycles (10:00 and this one) while carrying the
  actual failures. The tool's whole value is turning a 13-minute suite into
  a 2-second check; two of five files that just broke are exactly the two
  it disclaims.

## Artifacts
- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic) — **not pushed this cycle**
- Files touched: `eval/mppi_sandbox/extremum_reading.py`, `eval/mppi_sandbox/tests/test_exemption_control.py`, `eval/mppi_sandbox/tests/test_exemption_masking.py`, `eval/mppi_sandbox/tests/test_guard_direction.py`, `results/p3-epistemic-shadow-cost-critic.tsv`
- TSV row appended: yes

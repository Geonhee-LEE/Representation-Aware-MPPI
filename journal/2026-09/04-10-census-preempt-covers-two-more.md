# census_preempt now covers exemption_control.REGISTRIES + extremum_reading.SITE_CLASSES

- **Cycle**: 2026-09-04 10:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: `3c1c5d39` census_preempt 를 자기가 UNCOVERED 로 선언한 4개 census 까지 넓히기
- **Phase**: P3
- **Status**: in_progress

## What I tried
- REVIEW's Step 0 checks all came back clean (no strand, receipt already
  graded green for prior HEAD, bottleneck LIVE, tree drift all declared
  local-only) — first cycle in a while to start EXECUTE immediately.
- Notion hygiene audit first: all 6 `Doing` TODOs on this branch were
  fetched and checked against `git merge-base --is-ancestor` for their
  cited commits. 4 of 6 were already shipped weeks ago (Q-180 receipt_store
  tmp_path fix, Q-189 deviation decomposition, Q-203 durations park, D-402
  DECLARED_SUITE `SCOPED` verdict) but never flipped from Doing → Done —
  flipped all four with a one-line note citing the ancestor commit. Left
  2 genuinely open: this TODO and `[stuck]` heading_err_rms_max.
- Picked this one (decision tree step 1, resume in-flight): added
  `exemption_control_registries()` (reuses `_ints_compared_in` against the
  `len(ec.REGISTRIES) == 15` pin in `test_exemption_control.py`) and
  `extremum_site_sweep()` (calls `extremum_reading.sweep()` directly,
  measured well under 1s) to `census_preempt.CENSUSES`, removed both
  names from `UNCOVERED`.

## What worked / what failed
- Both new entries read CLEAN on the first run — no drift introduced by
  adding them. `census_preempt` itself: 12 censuses, all clean.
- `test_census_preempt.py`'s 53 tests all pass unmodified (its assertions
  are `>=` bounds on `CENSUSES`/`UNCOVERED`, not exact counts) — no pin
  updates needed in that file.
- `inert_surface staged` reported `STAGED_MOVED` (5 pins withdrawn) as
  expected under D-207/D-199 — this diff adds a reader over
  `exemption_control`/`extremum_reading`, so the standard price applies.
- Ran out of D-181 budget window (`SUITE_AFFORDABLE` closed at 16m46
  elapsed) before a full-suite receipt could be bought this cycle —
  deliberate strand rather than a rushed suite. TSV row and TODO both
  marked `in_progress`/`Doing` for the next cycle to discharge.

## North-star delta
- Zero direct movement — pure verification-infra change, no rollout,
  no controller/representation code touched.
- Indirect: closes a gap named by D-318/D-330 that has cost multiple past
  cycles a red suite discovered only at suite time; a future cycle whose
  actual work happens to touch either registry now gets a ~1s pre-empt
  warning instead of a 12-minute-in red.

## Key learnings
- The Notion `Doing` bucket had drifted badly: 4 of 6 items were dead
  weight, all resolved in their own page body weeks ago but never
  status-flipped. `git merge-base --is-ancestor <cited-commit> HEAD` is a
  cheap, reliable way to verify a TODO's own "published" claim rather than
  trusting the prose — worth doing whenever REVIEW finds more than one
  stale `Doing` item, not just the one STATE explicitly flags `[stuck]`.
- `census_preempt`'s two remaining `UNCOVERED` gaps that had real
  "no cheap derivation exists" excuses continue to (`inert_surface pins`,
  `tsv_timestamp audit`) — those are placement problems, not coverage
  gaps, and are correctly handled elsewhere in the loop already.

## Recommended next 1–3 priorities
1. Discharge this strand: run `push_preflight record` for a full-suite
   receipt and push (`bdb920e` + the TSV/journal commit) — no
   investigation needed, the diagnosis is already done.
2. `[stuck]` heading_err_rms_max — the one remaining genuinely open Doing
   item; localize which phase of the 10/16 failing seeds' heading error
   originates in (avoidance maneuver vs. recovery vs. steady driving).
3. `key_discrimination narrow-key composition` remains the last named-only
   `UNCOVERED` entry with no cheap derivation (needs the full
   `consumer_reach` walk) — still correctly excused, not a to-do.

## Artifacts
- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic, PR #67)
- Files touched: `eval/mppi_sandbox/census_preempt.py`,
  `results/p3-epistemic-shadow-cost-critic.tsv`
- TSV row appended: yes

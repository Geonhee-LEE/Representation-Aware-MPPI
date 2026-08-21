# Four pins, one ampersand, and a deadline I chose to miss

- **Cycle**: 2026-08-22 07:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: STATE #1 `pin-repair-then-push` — move four pins, one suite, push
- **Phase**: P3
- **Status**: in_progress

## What I tried

- Phase 1 Step 0 fired again: `cycle_artifacts stranded` named **2 journals and
  4 commits** that never reached `origin`. Per D-112 that outranks the decision
  tree, so the pick was STATE #1 — decision-tree step 1 (resume in-flight).
- Did **not** re-diagnose. 06:00 left exact assertion deltas and a log at
  `/tmp/suite-receipt.json.log`; this cycle read them and went straight to the
  repair, which is the whole value 06:00's red suite bought.
- Repaired the four pins as one root cause and wrote the missing control:
  - `exemption_control._vocabulary` — new `Tamper` for `source_reach.VOCABULARY`,
    registered in `TAMPERS`. This is the real fix; the other three are literals.
  - `test_guard_reflexivity` — added `source_reach.vocabulary_gap` to the
    AND-shaped set **and corrected D-417's note**, which had argued in prose
    that it would not join.
  - `test_guard_direction` — 18 → 19, `test_exemption_masking` — 26 → 27.
- Confirmed the fifth failure needs no repair: `test_receipt_store::
  test_cli_recall_reports_miss_then_hit` **passes in isolation** (1.32 s),
  confirming 06:00's hypothesis that it was state-coupled to that run archiving
  its own receipt mid-suite. Nothing was changed for it.

## What worked / what failed

- **The tamper had a vacuous spelling and the registry told me which.** The
  obvious `_vocabulary` control drops the sorted-first element; measured, that
  moves `vocabulary_gap` **0 → 0**. Only `ENSEMBLE` moves it (0 → 2), because
  every clearance-token source carries `ENSEMBLE` too. A generic shrink would
  have been green and measured nothing — the exact shape `test_no_control_is_
  vacuous` exists to catch. Three seconds of measurement chose the spelling.
- **D-417's prose lost to the tree, and that is the finding.** It reasoned that
  `vocabulary_gap`'s `&` "screens a name token rather than exempting a
  population member" and concluded it would not join the AND set. The scan
  derives that set from what the `&` *is*, not what it means. D-072's syntax
  result once more: an argument for why a construct is *morally* not AND-shaped
  has no purchase on a census matching on shape.
- **I missed the suite deadline and started one anyway — deliberately (D-419).**
  `cycle_wallclock elapsed` read `SUITE_UNAFFORDABLE` at 10m29, 2m58 past the
  7m31 cutoff. D-181 says cut scope at that moment. I did not, and the reason is
  that the advisory and the strand gate point opposite ways here: cutting scope
  strands a **5th** commit and hands the next cycle the same suite cost plus a
  longer pile. This is a chosen overrun with eyes open, not a discovered one —
  which is the failure mode D-181 actually exists to prevent.
- **`census_preempt` was clean again and again it was not the tree.** All four
  pins that moved sit in its printed `UNCOVERED` line. STATE #2 remains the
  right follow-up and this is now its second consecutive confirmation.

## North-star delta

- **Zero. No controller moved, no rollout ran, no coverage number changed.**
  This is the second consecutive cycle spent entirely on the verification
  surface. The honest framing: 05:00 shipped one `&` and it has now cost two
  full cycles and roughly 45 minutes of suite time.
- What is bought, if the suite is green, is the **push** — 4 commits of finished
  work reaching `origin` and the strand returning to zero.

## Key learnings

- **A vacuous control and a working one are indistinguishable without measuring
  the tamper.** The direction (`grows`/`shrinks`) is asserted by hand in the
  `Tamper`, so nothing in the type catches a shrink that moves no reading. Three
  lines of measurement before writing the control is the cheap habit.
- **Prose in a pin is a claim, not an exemption.** D-417 wrote a careful
  paragraph explaining why a guard would not join a census; the census disagreed
  and the census shipped. Where a note and a scan disagree, the scan is the
  artifact under test.
- **An advisory pointing away from a gate is a decision, not a conflict to
  resolve silently.** D-181 said stop; D-112 said clear the strand. Both are
  right about their own question. What was needed was to pick one *and record
  why* — hence D-419 rather than a quiet overrun.

## Recommended next 1–3 priorities

1. **`census-preempt-widen`** — third consecutive cycle where its `UNCOVERED`
   line named exactly what went red. Cover the four censuses or D-318 lands
   again. This is now the highest-value item on the list.
2. **`register-scene-transfer`** — unchanged in value, unblocked once this
   branch is green.
3. **Pre-write tamper measurement as a habit** — consider a `--dry-run` on
   `exemption_control` that reports each tamper's reading delta, so a vacuous
   control is caught at authoring time rather than by a pin.

## Artifacts

- PR: #67 (open) — no new PR (D-140; queue at 6/6, 41 days since last merge)
- Files touched: `eval/mppi_sandbox/exemption_control.py`,
  `eval/mppi_sandbox/tests/test_guard_reflexivity.py`,
  `eval/mppi_sandbox/tests/test_guard_direction.py`,
  `eval/mppi_sandbox/tests/test_exemption_masking.py`
- TSV row appended: yes

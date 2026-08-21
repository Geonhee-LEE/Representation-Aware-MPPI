# Four pins, one ampersand, and a deadline I chose to miss

- **Cycle**: 2026-08-22 07:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: STATE #1 `pin-repair-then-push` — move four pins, one suite, push
- **Phase**: P3
- **Status**: in_progress — **suite RED on a fifth pin, push refused, strand 6 commits**

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

- **The suite came back RED and the overrun bought nothing.** `4044 passed,
  1 failed` in 1699 s. The failure was **not** one of the four I repaired — it
  was `test_every_declared_control_bites`, whose two literals (`len(TAMPERS) ==
  15`, `[VERDICT_BITES] * 15`) are the *fifth* pin the same `&` moved. My
  control bit correctly; the tally simply had to say 16. Fixed and verified
  locally (30 s), but by then the cycle was 75 min in, so **no second suite was
  bought and nothing was pushed**. The strand is now **6 commits**.
- **This is the exact shape of the thing I chose against, arriving from the side
  I did not guard.** D-419 reasoned that the overrun was worth it because the
  repair was verified pin-by-pin. It was — all four targets plus
  `census_preempt` were green before the suite. What that verification could not
  see is a pin *nobody had named yet*, and the only instrument that would have
  named it cheaply is `census_preempt`, which lists `exemption_control.
  REGISTRIES` in its own `UNCOVERED` line and returned CLEAN 5/5 twice.

## North-star delta

- **Zero, and negative on the strand.** No controller moved, no rollout ran, no
  coverage number changed. 05:00 shipped one `&`; it has now consumed **three
  full cycles and ~73 minutes of suite time**, and the strand grew 4 → 6.
- The one durable gain is that the population is now believed complete: five
  pins moved by that `&`, all five repaired and locally green, with
  `census_preempt` clean. Next cycle owes **exactly one suite and no
  diagnosis**.

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
- **…and the overrun still lost, which is the part worth keeping.** Choosing it
  openly did not make it correct. The bet was "the repair is verified, so one
  suite converts 4 stranded commits into a push"; it failed on a pin outside the
  verified set, and a bet on completeness is only as good as the instrument that
  bounds the population. Here that instrument (`census_preempt`) *prints its own
  blind spot* and I read CLEAN as the verdict — the same misread 06:00 recorded
  and I repeated with its journal open in front of me.
- **The cheap reading was available and structurally unreachable.** No amount of
  care inside this cycle would have surfaced the fifth pin, because nothing
  derives that tally except the pin itself. That is what makes STATE #2 a
  tooling fix rather than a discipline fix — and why it now outranks the
  representation work on the list.

## Recommended next 1–3 priorities

1. **`buy-one-suite-and-push` — the only pick, and it needs no thinking.** All
   five pins are repaired and locally green; `census_preempt` is CLEAN 5/5. Do
   **not** re-diagnose and do **not** edit code. Start the suite as the first
   EXECUTE action (~28 min), write prose in its window (D-418), push. If it is
   green the strand of 6 clears in one move.
2. **`census-preempt-widen`** — third consecutive cycle in which its own
   `UNCOVERED` line named exactly what went red, and this time it cost a 28-min
   suite to learn a two-literal count bump. Cover `exemption_control.REGISTRIES`
   and `extremum_reading.SITE_CLASSES` or D-318 lands a fourth time.
3. **`tamper-dry-run`** — a `--dry-run` on `exemption_control` reporting each
   tamper's reading delta, so a vacuous control is caught at authoring time.
   From this cycle's `_vocabulary` near-miss (0 → 0 on the idiomatic spelling).

## Artifacts

- PR: #67 (open) — **nothing pushed**; strand is now `76b4fee`, `29fc5e1`,
  `2c5dbc2`, `27159c3`, `7481bbc`, `40e845c`, `9f91892`
- Receipt: `results/receipts/3c63227435228b2f.json` — **RED**, 4044/1/164, 1699 s
- Suite log (keep for next cycle): `/tmp/suite-receipt.json.log`
- Files touched: `eval/mppi_sandbox/exemption_control.py`,
  `eval/mppi_sandbox/tests/test_guard_reflexivity.py`,
  `eval/mppi_sandbox/tests/test_guard_direction.py`,
  `eval/mppi_sandbox/tests/test_exemption_masking.py`,
  `eval/mppi_sandbox/tests/test_exemption_control.py`
- TSV row appended: yes

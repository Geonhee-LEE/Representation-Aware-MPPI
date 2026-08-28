# An acknowledged exclusion is not a retired bottleneck

- **Cycle**: 2026-08-28 11:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: `bottleneck-scope-precision` (authored this cycle, PLAN step 4)
- **Phase**: P5
- **Status**: keep

## What I tried

- Ran the REVIEW gates. `bottleneck_scope` — wired into the loop only yesterday
  (D-481) — returned rc=1 `RETIRED cafe_cut_in_v0` on its **first live reading
  under a caller**. Cleared the gate as instructed by re-aiming STATE's
  bottleneck, then examined why it fired.
- The firing is a **false positive**. STATE 10:00's bottleneck asks a live
  question ("which controller does P5 report as its baseline") and names
  `cafe_cut_in_v0` only in the clause stating it *"is excluded on geometry"* —
  the screen's own verdict, quoted by a cycle that had already read it.
- Shipped `ACKNOWLEDGED`: a named-and-excluded scene whose **census reason code**
  the sentence quotes is not a finding (rc=0). Reason codes come from
  `scene.exclusions`, never typed — the D-047 rule the module already applies to
  scene names, one level in.
- 12 new tests (27 total, all passing), including the two that fence the change:
  the 2026-08-21 motivating sentence still retires, and a bare code with no
  scene named cannot launder an unnamed one.

## What worked / what failed

- **The discriminator is real, not a fudge.** The two sentences the module must
  separate differ exactly on this artifact: 08-21 wrote "fails `goal_reached` at
  every collision margin" (re-derived from closed-loop runs, no code), 08-28
  wrote "excluded on geometry" (consulted the screen, still no code). Requiring
  the code splits them, and the existing `test_the_motivating_sentence_is_retired`
  passes unchanged.
- **Legibility over sincerity, deliberately.** "Excluded on geometry" is true and
  still grades `RETIRED`. Accepting paraphrase would need a typed synonym list —
  precisely the defect this module exists to catch. So the acknowledgement costs
  one token in a sentence a cycle writes anyway.
- **What failed is the alternative I rejected.** The gate's only pre-existing
  remedy was deleting a true clause from STATE, which is what I did at 11:04 to
  clear it — STATE's bottleneck is now *less* informative than at 10:00. A check
  whose honest remedy degrades the artifact is D-044's mute shape; this one would
  have fired on every well-informed bottleneck for the six days to P5 entry.
- `inert_surface staged` reports `STAGED_MOVED` on the five snapshot pins
  (exemptions withdrawn, D-207's price). No consequence this cycle: D-315 already
  puts every one of those writes before the receipt.
- Notion gates 2 and 4 (stuck-TODO, empty-backlog) could **not** be evaluated —
  `notion-query-data-sources` is still unpermitted under cron. Proceeded on
  STATE's `Next claude-actionable` as the pool, which is the documented fallback.

## North-star delta

- **No planner movement.** No rollout, no controller, no representation touched.
  Pure instrument-precision work on the loop's own gating.
- Indirect and specific: PLAN's candidate pool is read through this screen, and
  for the next ~36 cycles to P5 entry the screen would have either mis-fired on
  every bottleneck that cites the excluded scene, or been muted. Both cost more
  than the 40 LOC.
- The P5 baseline question is **unmoved** and stays #1 next-actionable — but it
  can now be stated with the scene named, which is how STATE will carry it below.

## Key learnings

- **A gate's first live reading is its real test, and it should be budgeted as
  one.** `bottleneck_scope` shipped 08-21 with 15 green tests and no caller
  (D-481); it got a caller 08-28 05:00 and produced a false positive by 11:00.
  Fixture coverage graded the machinery, not the question — the same D-318 shape
  the project keeps re-finding, now at the moment of wiring rather than shipping.
- **Screening on a name screens the wrong thing.** What makes a bottleneck
  misdirected is the scene's *grammatical role* — proposed as the thrust vs cited
  as closed. No static screen parses that, so the honest move is to find an
  artifact that is present in one case and absent in the other, rather than to
  widen the match and hope.
- **The remedy a gate leaves is part of its design.** If clearing it requires
  making an artifact worse, cycles will learn to clear it that way — and STATE's
  bottleneck is the one sentence next cycle's PLAN consumes.

## Recommended next 1–3 priorities

1. **Choose P5's baseline controller, or prove none is non-dominated** — unmoved
   from 10:00, still the only item on the P5 critical path, now 6 days out.
2. **Audit the other REVIEW-step screens for the same false-positive class** —
   `cycle_artifacts stranded`, `cycle_wallclock`, `push_preflight probe` each fire
   on a derived reading; ask of each what remedy it leaves and whether that
   remedy degrades anything.
3. **Sweep the remaining consumers of the 72** — unmoved for two cycles, cheap.

## Artifacts

- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic)
- Files touched: eval/mppi_sandbox/bottleneck_scope.py, eval/mppi_sandbox/tests/test_bottleneck_scope.py, docs/decisions.md, results/p3-epistemic-shadow-cost-critic.tsv
- TSV row appended: yes

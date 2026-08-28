# The other class's question is ill-posed, and that is the answer

- **Cycle**: 2026-08-29 07:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: STATE #2 — run the conjunctive record over 물체회피
- **Phase**: P5
- **Status**: keep

## What I tried

- Took STATE's second open question literally: 물체회피's `cbf_mppi` holds a 5/5
  total order on one clause, so run D-490/D-491's clause-widening machinery over
  its own class's full clause set.
- Read the two north-star lines in `CLAUDE.md` before porting the machinery, to
  find out what "its own clause set" names.
- Shipped `obstacle_instrumentation` + 39 tests when the answer turned out to be
  that the machinery does not transfer.

## What worked / what failed

- **The question is ill-posed, and the constitution says so in two adjacent
  lines.** 경로추종 names four **metrics**, conjoined ("동시 만족") — widening
  adds a *column*. 물체회피 names six **populations** ("모든 클래스") — widening
  adds a *scene*. There is no second obstacle column to conjoin, so a
  conjunctive record over 물체회피 presupposes columns the constitution never
  asked for. `clause_kinds_differ()` derives this rather than asserting it: it
  goes False the moment any obstacle class gains a reader in
  `path_tracking_metrics`, and a tamper test drives it there.
- **The honest question in its place — class coverage — answers 3/6.**
  `cbf_mppi`'s five-scene sweep sits inside `dynamic`, `다중`, `가까운`. The
  5/5 total order is real; its *scope* is half its class.
- **`static` — the class the constitution names first — has zero scenes.**
  Every obstacle in the measured surface moves (`schedule` non-empty on all of
  them). That is an authoring gap, not a build: derivable, simply unpopulated.
- **가려진 / 의외 are unmeasurable, and this is the asymmetry that matters.**
  Both need to know what the robot *knew* at a time, and the sandbox obstacle
  model is full-state. So the two north-star halves have differently-shaped
  debts: tracking's gap is **unbought** (32 rollouts, under a minute); the
  obstacle gap is a **build** (a visibility model). A P5 report quoting "one
  class has a line" without that would price two unlike debts the same way.
- **My own complement test caught a real bug.** Written as a plain complement,
  `test_non_close_scenes_have_every_arm_above_budget` failed — `cafe_freezing_v0`
  declares no `min_distance_to_obstacle`, so it was reading as a *non-close*
  scene when it had never been asked. Fixed to return `None`, and the unasked
  count now ships beside the coverage (`close_askable 3/4`). That is the feed's
  Nav2 finding #3 applied to my own census on the day it arrived.
- **`census_preempt` fired for the 15th consecutive cycle** — 3 of 10 drifted
  (`guard_tally` 164→167, `loop_reach` 2 unrecorded rows, `UNMEASURABLE_CLASSES`
  entering the typed-registry population), all repaired pre-suite in ~4 min
  instead of a red suite ~12 min later.

## North-star delta

- The only contract line P5 has is now **scoped**: `cbf_mppi 3/6` classes, not
  an unqualified 5/5. The number did not get better; it got *stated*.
- Two of the six obstacle classes are pinned as needing a **build**, with the
  artefact named per class — the first time this tree has priced the 물체회피
  gap at all.
- Zero new rollouts, zero controller/representation/dynamics movement.

## Key learnings

- **Symmetry between the two north-star classes was assumed, and it is false.**
  Three cycles of clause-widening machinery (D-490, D-491) do not port, and the
  reason is in the constitution, not in the data. Checking what a question means
  before running it cost ~6 min and saved porting a module that would have
  measured nothing.
- **A coverage census must distinguish "answered no" from "not asked".** The
  distinction is worth a `None` in the API, not a `False` — and the way to find
  the collapse is to write the complement test, which fails loudly.
- The fourth consecutive cycle where buying a measurement **removed** a claim
  rather than adding one (D-486 → D-487 → D-491 → D-492).

## Recommended next 1–3 priorities

- **Author a static-obstacle scene** — the one uncovered-but-derivable class,
  fixable with a yaml and no model work. It is the cheapest coverage the
  contract line can gain.
- **Decide whether a visibility model is in P5's scope or defers to P4** — two
  of six classes are unmeasurable without one, and P5's report needs to say
  which.
- **Buy `heading error`** (32 rollouts) — still unbought, still the only way
  the tracking record could move; now clearly the *cheap* half of the debt.

## Artifacts
- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic)
- Files touched: eval/mppi_sandbox/obstacle_instrumentation.py, eval/mppi_sandbox/tests/test_obstacle_instrumentation.py, eval/mppi_sandbox/exemption_control.py, eval/mppi_sandbox/loop_reach.py, eval/mppi_sandbox/tests/test_guard_reflexivity.py, docs/decisions.md, results/p3-epistemic-shadow-cost-critic.tsv
- TSV row appended: yes

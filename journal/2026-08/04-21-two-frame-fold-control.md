# The fold has two inputs; D-067 controlled one — and the verdict survived anyway

- **Cycle**: 2026-08-04 21:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: `STATE#1` Explain the 12 at `guard_reflexivity._is_set_valued`
- **Phase**: P3
- **Status**: keep

## What I tried

- STATE #1 asked *why* the fold misses by 12 at the one site D-067 graded
  `FOLD_IMPLICATED`. Before reading the site, asked whether that grade was
  licensed. It was not: a reconstruction disagreement is
  `fold(measure_attributed run) != measure(exclusion run)`, and D-067's control
  ran `measure()` twice — the **right-hand** side only.
- `predicate_inputs.fold_drift` — the missing half. Two `measure_attributed`
  runs, folded under the same exclusion, so the left-hand run gets the control
  the right-hand one had.
- `exclusion_scope.attribute_two_frame` + `SOURCE_COVERS` / `SOURCE_UNDERSHOOTS`
  grades a disagreement against both frames, exclusion frame **first** so every
  D-067 grade stands and only `FOLD_IMPLICATED` can move.
- `unlicensed_fold_verdicts` — the free reading, no run: a `FOLD_IMPLICATED`
  verdict at an **address-repr** site is not licensed by a one-frame control,
  because the attributed run is a second process over a *larger file set* and
  its `<C object at 0x…>` fingerprints are drawn from a different heap.
- Paid it: two attributed runs, concurrent, frozen tree, **348 s**.

## What worked / what failed

- 🔴 **The objection is correct and the retraction did not fire.**
  `unlicensed_fold_verdicts` returns exactly `_is_set_valued` — the evidence
  did not isolate the fold. Then the measurement licensed it: the attributed
  frame reproduces that site **exactly**, `9600 → 9600` distinct on `10239 →
  10239` calls. Both of the fold's inputs repeat, and the fold still misses by
  12. Under `attribute_two_frame` it is `FOLD_IMPLICATED` again, now earned.
- 🔴 **The source frame is noisier than the frame D-067 measured** — band
  **0.227 %** vs 0.195 %, 6 of 50 sites moving, `address_confined` = True,
  `work_repeated` = True. And it is *systematically* noisier at the three sites
  D-067 graded `DRIFT_UNDERSHOOTS`: `_pure` moves **40** here against 7 there,
  `_is_structural` **41** against 1, `_has_git_diff_literal` **28** against 30.
- ⚠️ **Still undershoots.** Even summing both frames' deltas — 47 / 42 / 58 —
  none of the three gaps (142 / 84 / 95) is covered. The instrument's own noise
  budget grew ~6× and explains no more of the residual than before.
- ✅ **Zero self-entries — the first cycle in sixteen.** Population held at
  **69**: every function added returns a tuple or an int, so none is a
  predicate. The recurrence D-045→D-067 kept pinning is a property of building
  *predicates*, not of building instruments.

## North-star delta

- **No avoidance or tracking number moved — thirty-sixth consecutive instrument
  cycle.** Scenes able to contribute an avoidance number: 5, reportable: 4.
- What moved: D-067's single hard claim is now supported by a control in the
  frame it is about, rather than by one in the adjacent frame. What moved
  against: the 12 is still unexplained *mechanically* — it is now correctly
  **attributed** to the fold, which is a different thing from being understood.

## Key learnings

- **A control has a frame, and a two-run comparison has two of them.** D-067
  wrote "the fold does not appear in this control" and read that as sufficient;
  what makes a control sufficient is covering every varying term, and the
  attributed run varies. The check that generalises: for each side of the
  compared pair, name the control that fixed it.
- **The asymmetry is what makes the objection a finding rather than a
  complaint.** A value-fingerprinted site's source term is zero by
  construction — same question, same fingerprint, any frame — so one control
  was always enough there. The objection bites exactly the 7 address sites, and
  those are exactly the disagreements.
- **A correct objection can leave the conclusion standing.** Same shape as
  D-062: the conceptual argument survives, the empirical retraction is
  withdrawn. Worth stating because the cheap move would have been to report
  "D-067 retracted" from the free reading alone and skip the 348 s.
- ⚠️ **Transport, again.** D-066's gap of 12 was measured on the **64**-predicate
  tree; this control is on the **69**-tree. Both folds read 9600 here, so a
  *single* exclusion-frame `measure()` on this tree would close the gap
  end-to-end on one tree. That is the direct follow-on and it is 1 run.

## Recommended next 1–3 priorities

1. **One `measure()` under the exclusion on the 69-tree.** Both attributed
   folds read `_is_set_valued` = 9600; one run gives the measured side on the
   same tree and retires the 64-vs-69 transport caveat entirely. ~6 min.
2. **Read `_is_set_valued` whole** — the question STATE #1 actually asked. Now
   worth doing, because the attribution is licensed.
3. **Take a third and fourth run in each frame.** Two bands now exist (0.195 %,
   0.227 %) and both are point estimates of spreads nobody has bounded.

## Artifacts

- PR: #67 (autoresearch/p3-epistemic-shadow-cost-critic) — 63rd cycle on branch
- Files touched: `eval/mppi_sandbox/predicate_inputs.py`,
  `eval/mppi_sandbox/exclusion_scope.py`,
  `eval/mppi_sandbox/tests/test_exclusion_scope.py`,
  `docs/decisions.md`, `journal/2026-08/04-21-two-frame-fold-control.md`
- TSV row appended: yes

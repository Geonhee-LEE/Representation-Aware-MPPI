# The first licensed reading — and the fold is implicated nowhere

- **Cycle**: 2026-08-05 00:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: `STATE-1` One frozen batch of 4 concurrent runs — gap + both frame controls
- **Phase**: P4
- **Status**: keep

## What I tried

- Built `exclusion_scope.paired_reading` — two `measure_attributed` and two
  `measure`, submitted to one thread pool, graded through `attribute_two_frame`
  with all four `tree_key`s supplied. The smallest set that supplies a gap plus
  a control for **each of its two frames** with none of them transported.
- Closed the hole `single_tree` still had. It takes one key per run, which
  assumes a run is instantaneous; these are five-minute runs and a batch of four
  spans long enough for an edit to land mid-way. `_stamped` stamps both sides of
  each run and issues the **empty** key when they disagree — reusing the refusal
  `single_tree` already has rather than inventing a second spelling.
- Ran it: **397 s**, tree `5eb5123d…` on all four frames, population **71**,
  50 observed sites, **7** disagreeing.

## What worked / what failed

- ✅ **Licensed, first time in five cycles.** `licensed=True`,
  `work_repeated` True in **both** frames, bands 0.106 % (exclusion) and
  0.162 % (attributed), `address_confined` True in both. Every precondition the
  reading needs holds, and no verdict is `TRANSPORTED`.
- 🔴 **`fold_implicated` is empty.** D-068's `FOLD_IMPLICATED` at
  `guard_reflexivity._is_set_valued` — withdrawn by D-069 pending exactly this
  batch — **does not reproduce**. Its exclusion frame moved **2**, not 0. On a
  licensed reading the fold is the last suspect standing at *no* site.
- 🔴 **But "not the fold" is not "explained".** 6 of 7 grade
  `DRIFT_UNDERSHOOTS`, the grade written to be deliberately weak, and the
  undershoots are enormous: `_pure` gap **175** / control **13**; `_numeric`
  **79** / **5**; `_is_pure_literal` **77** / **30**; `_is_structural` **66** /
  **2**. The controls move in the right direction and nowhere near far enough.
- 🔴 **The grading scheme is knife-edge, and that is the cycle's real finding.**
  `FOLD_IMPLICATED` requires *exact* stationarity in both frames. At a 0.1 %
  band over 50 sites, whether a site moves by 0 or by 2 out of ~9600 is close
  to a coin flip — and that one bit is the whole difference between "the fold is
  the last suspect" and "a control excuses it, weakly". Three cycles of argument
  hung on that bit: `_is_set_valued` moved 0 in D-067 and in D-068, and 2 here.
- 🔴 **Third tree, third set of magnitudes.** `_pure` 142 → 196 → **175**;
  `_has_git_diff_literal` 95 → 29 → **30**; `_is_set_valued` 12 → 20 → **15**.
  D-069's "stable to about a factor of three" survives its own re-test.
- 🔴 **The "same 7" claim was never checkable from the record.** Membership
  reproduces again — 7 of 50 — and this cycle names all seven. D-066 through
  D-069 named only **five** of them in any published artifact;
  `lam_dependence._is_pure_literal` and `lam_dependence._numeric` appear in
  none. The claim three cycles called exactly reproducible rested on an
  in-cycle comparison whose artifact was not kept.
- ⚠️ **Seventeenth self-entry**: population 70 → **71**. Observed sites still 50.

## North-star delta

- **No avoidance or tracking number moved — thirty-eighth consecutive instrument
  cycle.** Scenes able to contribute an avoidance number: 5, reportable: 4.
- What moved: the residual D-066 opened is, for the first time, read on a tree
  that licenses it, and the answer retires a suspect (the fold) rather than
  naming one.
- What moved against: the retirement is carried by a grade the instrument's own
  docstring calls too weak to rank, and the thing that separates it from the
  opposite verdict is a 2-count movement.

## Key learnings

- **A binary grade over a noisy quantity is not a binary finding.** The whole
  `FOLD_IMPLICATED` / `DRIFT_*` split is thresholded at *exactly zero movement*,
  which is the one threshold that cannot survive a 0.1 % band. This is the same
  defect as STATE #21's unjustified `wilson_lower_at_least` floor, arrived at
  from the other side — there a threshold was picked without justification, here
  one was picked *because it needed no justification* and is worse for it.
- **The record has to carry the set, not the count.** "The same 7 of 50" was
  published three times and was never verifiable, because seven names were never
  written down. A membership claim's artifact is the membership.
- **A control that undershoots by 13× is evidence about the control.** Six sites
  where the gap is 5–13× the drift is not six weak excuses; it is a signal that
  neither frame's run-to-run variation is the mechanism, and the next question
  is what else differs between a folded record and a measured one.

## Recommended next 1–3 priorities

1. **Replace the zero-movement threshold with a band.** Grade against the
   frame's measured drift band rather than exact equality — the reading above
   inverts on a 2-count movement and nothing justifies that cut.
2. **Read `lam_dependence._pure` whole** — gap **175**, the largest, control
   **13**, and it has now missed by 142 / 196 / 175 on three trees.
3. **Persist the disagreeing set as an artifact** (`results/` json), so the next
   cycle's membership claim is checkable rather than asserted.

## Artifacts

- PR: #67 (open, sixty-fifth consecutive cycle writing into it)
- Files touched: `eval/mppi_sandbox/exclusion_scope.py`,
  `eval/mppi_sandbox/tests/test_exclusion_scope.py`
- TSV row appended: yes

# Q-081's static half: 8 of 23 published gap movements clear their own noise floor — and 0 of them are `_pure`'s

- **Cycle**: 2026-08-05 05:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: STATE #2 — Q-081's static half, no new run
- **Phase**: P3
- **Status**: keep

## What I tried

- Joined `published_ratios.PUBLISHED` (every per-site digit D-066..D-071 printed)
  against the D-074 record's same-tree band, off disk. Zero new runs.
- Split the question in two, because they are not the same question.
  **Containment** (is a published gap inside the band?) is nearly uninformative:
  a gap *outside* a band measured on another tree is the transported reading
  D-069 forbids, not a survivor. **Movement** (does the fold between two
  published readings of one site exceed that site's spread?) is the graded one —
  both endpoints are the same quantity from the same instrument, so a fold below
  the instrument's own reproducibility is evidence of nothing.
- Added `Record.ratio_spread()`, the gap band's twin on the ratio, defaulting to
  the **exclusion frame alone** because that is what every published ratio
  divided by (Q-079). Gaps and ratios both go through one `Movement` grader.
- Excluded one number by name: D-074 published `_pure`'s gap as **326**, which
  *is* `_pure`'s band `hi` in this record. `SELF_DEFINING` pins the exclusion.

## What worked / what failed

- 🔴 **`_pure` — the most-quoted site on this branch — has 0 of 6 surviving
  movements.** Its gap was published as 142 → 196 → 175 → 214 across four
  decisions, each step written as though the tree had moved. Widest fold among
  all four: **1.51×**. Same instrument, unchanged tree: **1.74×**. The entire
  published series fits inside its own noise.
- 🔴 **Gaps: 8/23 movements survive (35%), on 3 of 6 sites** — and the 8 is
  soft. Three of them clear their band by **1.009× / 1.023× / 1.047×**, i.e.
  inside the resolution of a fold estimated from k=3. The defensible number is
  **5 of 23**, and `test_three_gap_survivors_are_inside_the_bands_own_resolution`
  exists so the 8 is never quoted without the 5. All three marginals are pairs
  containing **D-069** — the one reading whose gaps were published with no
  control at all.
- ✅ **Ratios: 4/5 survive (80%)** — the first control on this branch to
  *support* a prior claim instead of retiring one. D-071 kept the ratio over
  stationarity; graded against a same-tree band, the ratio is the sturdier
  quantity, and by a wide margin (80% vs 35%).
- 🔴 **But half of that 80% rests on a control of 1 or 2.** `_is_structural`
  (controls 1, 2) and `_is_set_valued` (1, 2) are one or two counts from
  `ATTR_FOLD`, i.e. from infinite. `FRAGILE_CONTROL = 2` reports them next to
  the rate rather than subtracting them — they are not refuted, their
  denominators are just unshown. The two survivors that *don't* rest on a tiny
  control are both `_pure`'s. Same site whose gap movements all failed: the two
  quantities are not the same claim.
- 🔴 **The join's own license is contested and the module says so instead of
  picking.** The band is tree `c4b76066`; no published magnitude is. D-069-as-
  written grades this whole join `TRANSPORTED`; D-074-as-measured says D-069's
  premise is false. `license_status()` returns the tension, not a boolean, and
  `report()` prints it first. Scope claimed: "below the instrument's own noise
  floor" — **not** "wrong".
- My first cut of the marginal-survivor test asserted 2 sites; the measurement
  said 3 (`_is_set_valued` 15 vs 20 at 1.047×). Fixed the test, not the code.
- 🔴 **The D-043 re-take went red — 4 failed, 798 passed — and it was right to.**
  Not a regression: this module entered the guard pool it does not audit.
  **56 → 60**, the **eighteenth** consecutive cycle and the largest single-cycle
  addition since D-051's six. The split matters more than the count:
  `standings` / `unbanded` / `movements` all narrow against `banded`, a **local
  dict** from a same-module call two lines up — no registry, no typed constant,
  no module scope — while only `published` (against `SELF_DEFINING`) reaches a
  module global, taking `exemption_masking`'s route count 15 → 16. So D-072's
  syntax result holds at full strength: the detector keys on the `in` / `not in`
  operator and nothing else. And the standing gloss since D-063 — "every
  instrument built to audit a population becomes a member of one" — **breaks
  here**: `if site in banded` audits nothing, it skips sites the band cannot
  grade. Shape is a guard; intent is not.
- 🔴 **`SELF_DEFINING` arrived unwatched** (three → four), repeating D-073's
  second-order cost one cycle later. Declined to write a fifth watcher: unlike
  `CARRIED_FIELDS`, this set's one member is there because the value *equals its
  own band endpoint*, which is recomputable from the record. Watching a typed
  copy is the wrong repair; deriving it is the right one. Filed as **Q-082**.

## North-star delta

- **No avoidance or tracking number moved — forty-third consecutive instrument
  cycle.** Scenes able to contribute an avoidance number: 5, reportable: 4.
- What moved: the branch now has a **mechanised answer to "is this magnitude
  quotable"**, and applied to its own back catalogue it retires the single most
  cited series on it. Cheaper than the retraction it replaces.

## Key learnings

- **A published series is a stronger claim than a published number, and this
  branch only ever checked the numbers.** Six cycles quoted `_pure` four times
  and read the differences as signal; the differences were smaller than the
  instrument's own spread the whole time. The check costs one join once a band
  exists.
- **Gap and ratio are different claims about the same site and can disagree in
  opposite directions.** `_pure` fails on gaps and is the *only* sturdy survivor
  on ratios. Any future "the magnitude reproduced" has to name which quantity.
- **A survival count needs its margin distribution reported with it.** 8/23
  and 5/23 are the same measurement; only the second is defensible, and nothing
  but a test keeps the first from being the one that gets quoted.
- **The instrument's noise floor is itself an n=3 estimate.** Three of eight
  verdicts sit inside that. A second batch would not add precision so much as
  tell us which side those three are actually on.

## Recommended next 1–3 priorities

1. **Q-082: derive `SELF_DEFINING` instead of typing it.** Static, ~1 cycle,
   and it takes `unwatched_exemptions` back to three without adding a watcher.
2. **Re-run the batch at k=5+ and re-grade the three marginals.** ~8 min of
   compute; it is the only thing that moves 8-vs-5 to a single number.
3. **Apply `movements` to the counts, not just the magnitudes** — the "exactly
   N" bounds (predicate population 62→79, guard pool 48→**60**, observed sites
   53→50) are a published series nobody has graded against any band.
4. **Q-081's remaining half**: does any *cross-site ordering* claim survive?
   D-074 answered it for one tree (rho +0.571/+0.857/+0.714); the published
   spans (D-071's "2.5× to 13×") have not been graded.

## Artifacts
- PR: #67 (existing, 70th consecutive cycle writing into it)
- Files touched: eval/mppi_sandbox/magnitude_survival.py (new), eval/mppi_sandbox/reading_record.py, eval/mppi_sandbox/tests/test_magnitude_survival.py (new), docs/decisions.md, docs/deliberations.md, eval/mppi_sandbox/tests/test_guard_reflexivity.py, eval/mppi_sandbox/tests/test_exemption_masking.py
- TSV row appended: yes

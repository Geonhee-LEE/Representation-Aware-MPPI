# Both frames on one tree: the 7 sites are the same 7, and not one of the magnitudes is

- **Cycle**: 2026-08-04 23:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: `STATE#1` One exclusion-frame `measure()` on one tree
- **Phase**: P3
- **Status**: keep

## What I tried

- Found the 22:00 cycle's work uncommitted in the worktree (no commit, no cron
  line): `predicate_inputs.tree_key` + `exclusion_scope.single_tree` +
  `ATTR_TRANSPORTED` + 4 tests. Resumed it per the decision tree's step 1,
  verified it (88 passed on the two touched files), and committed it as the
  guard D-066/D-067/D-068 each needed and each wrote a 한계 paragraph instead.
- Then bought what STATE #1 asked for: **one** `measure_attributed` and **one**
  `measure` run, concurrent, on the **same** frozen tree — `2c4e0f04…` before
  and after, **366 s**, population **70**.
- Compared the resulting 7 disagreements against D-066's 7, site by site, on
  membership / magnitude / sign.
- Put the new gap through `attribute_two_frame(trees=…)` against the only
  controls that exist (D-067's and D-068's, both 69-tree) — the guard's first
  use on real data rather than fixtures.

## What worked / what failed

- ✅ **The membership is exactly reproducible.** The same **7 of 50** sites
  disagree on the 64-tree and on the 70-tree — same names, no additions, no
  drops. Whatever the fold gets wrong, it gets wrong at a *fixed* set of sites.
- 🔴 **Not one magnitude reproduced.** Ratios one-tree ÷ D-066, over the same
  seven: **0.31, 0.60, 0.87, 1.38, 1.54, 1.59, 1.67**. `_has_git_diff_literal`
  is 95 → **29**; `_pure` is 142 → **196**. The quantity three cycles argued
  over is stable to about a factor of three.
- 🔴 **`_is_set_valued`'s 12 is 20.** Same site, both frames on one tree, calls
  identical on both sides (**10239 = 10239**): folded **9602**, measured
  **9582**. D-068's shape reproduces — same work, different distinct count —
  and the gap it reasoned about is **1.67×** larger than reported.
- 🔴 **A sign flipped.** `_shells_out_to_git_diff` was **low** by 15 in D-066
  and is **high** by 9 here. D-066's argument that ruled the digest out of the
  causal set was "collisions can only push low, and one site is high"; that
  premise is now known to be a per-*run* property, not a per-*site* one. The
  conclusion still holds — `_is_set_valued` is high in both readings, so there
  are two witnesses now — but it held by luck as much as by structure.
- 🔴 **The guard immediately de-licensed the cycle's own headline.** All 7
  grade `TRANSPORTED` and `fold_implicated_two_frame` is `()`, because the gap
  is 70-tree and both controls are 69-tree. D-068's `FOLD_IMPLICATED` is not
  refuted — it is **unlicensed again**, for the third distinct reason in three
  cycles.

## North-star delta

- **No avoidance or tracking number moved — thirty-seventh consecutive
  instrument cycle.** Scenes able to contribute an avoidance number: **5**,
  reportable: **4** — unchanged.
- What moved: the transport caveat D-066/D-067/D-068 each declared and each
  waved through is now **priced** (up to 3.3× on a magnitude, and a sign) and
  **mechanised** (`single_tree` refuses rather than caveats).
- What moved against: three cycles of attribution rested on numbers that do not
  survive their own re-measurement, and the 가려진-obstacle class still has
  exactly one working cost term (D-027).

## Key learnings

- **"Same set, different sizes" is a real and useful shape.** Perfect
  membership stability plus factor-3 magnitude instability says the fold has a
  *structural* defect at 7 known sites whose *size* is dominated by run-to-run
  fingerprint variation. That splits the question in two, and only the first
  half was ever answerable from these runs.
- **A caveat is a promise to be wrong later.** All three prior cycles wrote the
  transport down honestly and reasoned past it anyway. Writing it down is not
  the control; refusing is. The guard cost ~40 LOC and voided seven verdicts on
  its first contact with data.
- **Do not build an argument on the sign of a single-run difference.** D-066's
  digest exclusion happened to survive; `_shells_out_to_git_diff` shows the same
  reasoning applied one site over would have inverted.
- ⚠️ **The instrument keeps growing under its own measurement.** Population 64 →
  69 → **70**: `single_tree` is itself a predicate. Two consecutive cycles now
  where the tree the answer is about is not the tree the question was asked on.
  A *paired* run (gap and both controls in one frozen batch) is the only shape
  that closes this, and it is 4 runs, not 2.

## Recommended next 1–3 priorities

1. **One frozen batch: gap + both frame controls, 4 runs concurrent.** ~6–7 min
   on 16 cores, and it is the only configuration `single_tree` will license.
   Everything published about these 7 sites is currently `TRANSPORTED`.
2. **Read `_is_set_valued` whole**, now with the sharper fact: 10239 identical
   calls, 20 distinct apart. The structural half of the split above.
3. **Re-derive every "exactly N" bound in `docs/decisions.md`** — predicate
   population 62 → 64 → 69 → **70**, guard pool → 53, and D-066's 7/53 is 7/50
   here (the *observed-site* count moved too, 53 → 50, and nobody has explained
   that either).

## Artifacts

- PR: #67 (autoresearch/p3-epistemic-shadow-cost-critic) — 64th cycle on branch
- Files touched: `eval/mppi_sandbox/predicate_inputs.py`,
  `eval/mppi_sandbox/exclusion_scope.py`,
  `eval/mppi_sandbox/tests/test_predicate_inputs.py`,
  `eval/mppi_sandbox/tests/test_exclusion_scope.py`,
  `docs/decisions.md`, `journal/2026-08/04-23-one-tree-gap.md`
- TSV row appended: yes

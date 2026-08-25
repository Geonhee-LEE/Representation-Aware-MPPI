# The reconstruction band is not stationary — and drift does not cover it either

- **Cycle**: 2026-08-04 20:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: STATE #1 — is the 0.5 % reconstruction band stationary?
- **Phase**: P4 (instrument lane; subject is the P3 census)
- **Status**: keep

## What I tried

- D-066 left one question open and named two candidate causes for it: its
  input-fold reconstruction disagreed with a measured run on 7 of 53 distinct
  counts, and it could not say whether the fold is approximate or the
  *measurement* simply does not repeat across processes. Both predicted the
  same evidence; the sign only ruled out the 8-byte digest.
- Built the control that has **no fold in it**: `predicate_inputs.drift` over
  two independent flat censuses of the same tree, plus `unstable` /
  `drift_band` / `address_confined` / `work_repeated`.
- Added `exclusion_scope.attribute_disagreements` — puts each of D-066's 7 to
  the control and grades it `FOLD_IMPLICATED` (control reproduced the site
  exactly, so only the fold is left) / `DRIFT_COVERS` / `DRIFT_UNDERSHOOTS` /
  `UNCONTROLLED` — with `fold_implicated` as the empty-able reading.
- Also took the free half first: `disagreements_address_confined`, a join of
  D-066's own two artifacts needing no new run.

## What worked / what failed

- ✅ **The free reading landed before any run was spent.** All 7 disagreeing
  sites carry `address_reprs=True`; all 44 value-fingerprinted sites agreed
  exactly. There are only 9 address sites in the population, so the
  disagreements sit inside them 7/9 — the instability has a named mechanism
  (`<C object at 0x…>` renders differently in a second process) and it is not
  arithmetic.
- 🔴 **I voided my own control on the first attempt, by writing it.** Runs A and
  B bracketed my edits: `pv._scan()` found **64** predicates on the first and
  **69** on the second, and 5 sites' call counts moved because run B's suite
  included the new tests. The D-043 discipline — measure one tree, not two —
  applies to the *control*, not just the pass count. Re-ran the pair against a
  frozen tree, concurrently, ~6 min.
- ✅ **Clean pair, precondition met**: `work_repeated` = **True** — all 50 sites
  reproduced their call count exactly, so the two runs are two samples of one
  measurement and everything below is about fingerprints.
- 🔴 **The measurement is not stationary.** 6 of 50 sites move,
  `address_confined` = **True**, and the measurement's own band is
  **0.195 %** — against the 0.487 % D-066 attributed to its reconstruction.
  The band was never purely a property of the fold.
- 🔴 **But drift does not explain the gaps.** 6 of the 7 grade
  `DRIFT_UNDERSHOOTS`: `lam_dependence._pure` fold off by **142**, control
  moved **7**; `_is_structural` off by **84**, control moved **1**;
  `_has_git_diff_literal` off by **95**, control moved **30**. Drift is real,
  confined to the right sites, and an order too small.
- 🔴 **One site is `FOLD_IMPLICATED`**: `guard_reflexivity._is_set_valued` —
  control moved **0**, fold off by **12**. That is the site that disagreed
  *high* in D-066, i.e. the one whose sign exonerated the digest. The sign
  argument that cleared one suspect now points at the only site where the fold
  is provably the defendant.

## North-star delta

- No avoidance or tracking number moved — thirty-fifth consecutive instrument
  cycle. Scenes able to contribute an avoidance number: 5, reportable: 4.
- What moved: D-066's residual is no longer one undecided lump. It splits
  **6 partly-drift / 1 fold**, with a measured instrument band to read future
  reconstruction claims against.
- Honest cost: the subject is again the measuring apparatus, and 가려진-obstacle
  avoidance still has exactly one working cost term (D-027).

## Key learnings

- **A control has a tree too.** I stamped the tree for the pass count and then
  ran a two-process control across an edit boundary. Population 64 → 69 is the
  same defect D-043 names, in an instrument nobody had thought to apply it to.
- **"Which of two causes" can be the wrong question.** The answer here is
  *both, in measurable proportions* — and only the site where the control is
  **exactly** stationary licenses a hard claim. Magnitude comparisons from one
  pair rank a spread nobody estimated; `DRIFT_UNDERSHOOTS` is kept separate from
  `DRIFT_COVERS` for that reason and is not counted as exonerating.
- **Cross-tree magnitudes, same-site mechanism.** D-066's gaps were measured on
  the 64-predicate tree and this control on the 69-predicate one, so the
  *binary* (does this site reproduce?) transports and the arithmetic does not.
  Stated in the docstring rather than papered over.

## Recommended next 1–3 priorities

1. **Explain the 12 at `guard_reflexivity._is_set_valued`** — the one site the
   control cannot excuse, and small enough to read whole.
2. **Take a third and fourth flat census** to turn the 0.195 % point estimate
   into a spread, which is what `DRIFT_UNDERSHOOTS` currently lacks.
3. **Re-derive every "exactly N" bound in `docs/decisions.md`** — the predicate
   population is now **69** (was 62 → 64 two cycles ago).

## Artifacts
- PR: pending merge (`autoresearch/p3-epistemic-shadow-cost-critic`, #67)
- Files touched: `eval/mppi_sandbox/predicate_inputs.py`,
  `eval/mppi_sandbox/exclusion_scope.py`,
  `eval/mppi_sandbox/tests/test_predicate_inputs.py`,
  `eval/mppi_sandbox/tests/test_exclusion_scope.py`, `docs/decisions.md`
- TSV row appended: yes

# The screen's `INERT` was a claim about the exemption; the fact was about the subject

- **Cycle**: 2026-08-05 18:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: STATE #1 — fix `exemption_masking`'s surface-dependent `INERT` (the single remaining CI failure)
- **Phase**: P3
- **Status**: keep

## What I tried

- Took STATE's #1 priority: the **one** remaining CI failure on this branch,
  `test_screen_refinds_d050s_mask` asserting `'INERT' in ('CANDIDATE','UNRUNNABLE')`.
- Reproduced it on the surface that decides rather than reading the code —
  a `--depth 1` clone graded the pair `INERT` with `head=0 supp=0 reg=5`.
- Diagnosed it as D-086's vocabulary poverty one module over, exactly where
  D-087 predicted, and fixed the **vocabulary** rather than the assertion:
  added `UNPOPULATED` for a guard that read nothing, and put it in `unscreened()`.
- Re-gated the two tests that had pinned environment facts as if they were
  properties of the package, by **constructing** the conditions instead.

## What worked / what failed

- **The diagnosis was right and smaller than the finding.** `VACUOUS` already
  existed for "the registry is empty, so suppression cannot change anything and
  `INERT` would mean nothing". The identical argument for an empty **reading**
  was never made, so a guard whose subject was empty was reported as an
  exemption that removes nothing. Locally that was **3 of 18 pairs**, not one.
- **The module's central prose was attached to a verdict it cannot produce.**
  `masking_candidates` and one test both said `staged_declarations` "screens
  `INERT`: it narrows *down to* the registry ... so suppression empties its
  population instead of growing it." Measured with a staged file: **`DIVERGES`,
  1→0** — the described mechanism exactly. `INERT` (0→0) is what it reads when
  the index is empty, i.e. when that mechanism does *not* run. The prose and the
  number had never been about the same event, and nothing caught it because a
  git index is empty in every ordinary run.
- **The old test gated on the wrong axis, and the axes co-varied.** It branched
  on `_DECIDABLE` (can this clone answer *history* questions) while its own
  comment correctly noted `undeclared_drift` needs no remote. What decides the
  verdict is whether a **declared path is drifting in the worktree**. A fresh
  checkout is both blind and clean, so the wrong gate looked right until the
  axes came apart — D-046's coincidence-holding-a-place, holding a *gate's*
  place this time.
- **My first re-gate was also wrong, and copying files into a clone caught it.**
  I branched on "is anything drifting", which graded `INERT 2→2` in the clone —
  correct, and not `CANDIDATE`. Fixed by dropping environment branching
  altogether: both cells of the drift row are now **synthesised** via a
  `tree_provenance.Stamp`, so the screen must re-find D-050's mask on any tree.
- **Verified where it counts**: 24/24 on a `--depth 1` clone with a *clean*
  worktree — the exact CI condition, previously 1 failed.

## North-star delta

- **No avoidance or tracking number moved — fifty-sixth consecutive instrument
  cycle.** Scenes able to contribute an avoidance number: 5, reportable: 4.
- What moved: this branch's CI goes **1 failure → 0** if nothing else regressed,
  which would be the first green authority reading on it. That is the last
  procedural thing between the branch and a mergeable state.
- A real weakening of a published claim: the masking bound "by measurement over
  all 12 typed pairs" was never that. Two pairs were unprobed on the dev machine
  and **both `DIFFERENCE` guards** — the entire population a second mask could
  come from — are unprobed on a clean checkout. The bound of one stands; its
  warrant is narrower than stated and now says so.

## Key learnings

- **Fifth instance of absence-read-as-clean, and the first inside the module
  built to hunt that shape.** `push_preflight.VACUOUS`, `git_surface.NO_REMOTE_BRANCHES`,
  `local_only_audit`'s inversion, `ci_verdict`'s late aggregate — and now a
  screen reporting "0 candidates, 0 skips" on a checkout where it had probed
  neither `DIFFERENCE` guard. Naming a pattern four times did not stop it from
  recurring in the instrument written for it.
- **A verdict that varies with the working tree must say so in its name.** The
  same pair reads `CANDIDATE` here and `INERT` on CI, and no verdict disclosed
  that the difference was the tree rather than the exemption.
- **Prose describing a mechanism is not evidence the mechanism ran.** The
  `staged_declarations` gloss was internally coherent, cited a real narrowing,
  and quoted a number produced by the opposite situation. Only calling it with a
  synthetic subject separated the two.
- **A test that branches on the environment asserts a property of somebody's
  checkout.** I wrote one of those this cycle and had to remove it — the fix is
  to construct the condition, not to detect it.

## Recommended next 1–3 priorities

1. **Re-read this branch's CI with `ci_verdict` once the push lands** — if `fast`
   is green this is the first green authority reading on the branch, and STATE's
   #1 for four cycles is discharged.
2. **Redesign the fast/slow split — do NOT raise 120 to 240.** Unchanged and now
   more urgent: this cycle added 3 tests, two of which call `screen()`.
3. **Apply the `UNPOPULATED` question to the other seven registries' verdicts** —
   ask of each: does this verdict distinguish "the guard said no" from "the
   guard had nothing to read"? D-080 rec #1's sweep, with a sharper predicate.

## Artifacts
- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic, PR #67)
- Files touched: `eval/mppi_sandbox/exemption_masking.py`, `eval/mppi_sandbox/tests/test_exemption_masking.py`, `docs/decisions.md`
- TSV row appended: yes

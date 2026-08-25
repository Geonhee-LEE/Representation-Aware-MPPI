# The mark was held up by an unrelated precondition

- **Cycle**: 2026-08-21 06:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: STATE next-action #1 — grep `second_ratio` / `second_baseline_ratio` for module-external callers
- **Phase**: P3
- **Status**: in_progress

## What I tried

- Took the measurement Q-176 blocked its own answer on: module-external callers
  of the LOAD_BEARING claims scoped to the ungradeable `city_curved_v0`.
- Did it twice — once by hand-typed grep (the literal instruction), once by
  deriving the claim census from `scene_scoped_claims()` and scanning every
  `*.py` in the tree. The two disagreed, and the derived one was right.
- Landed the derivation as `citation_sites()` / `uncited_by_tests_only()` plus
  two tests, rather than answering Q-176 in prose and moving on.
- Answered Q-176 as **(b)** in D-397 but did **not** execute the float→`None`
  conversion — `cycle_wallclock elapsed` said the suite had to start by 9m01
  and the conversion touches 4 production functions, 8 test sites, and
  `marked()`.

## What worked / what failed

- **The hand grep undercounted its own population.** It found 7 sites for the
  two helpers Q-176 named. The derived census found **8** across two test
  files, because `aligned_second_is_gradeable` is equally LOAD_BEARING and has
  an external caller in `test_column_alignment.py`. Q-176 named two members of
  a three-member population. D-072 has now billed for this three times.
- **The answer to the question as asked is clean**: `uncited_by_tests_only()`
  is `()` — zero non-test callers. Q-176's stated precondition for (b) being
  cheap holds on production code.
- **The interesting finding is not the count.** `second_clears_floor` is the
  citation path D-393 explicitly declined to catch. Its only reader,
  `second_verdict()`, short-circuits on `excited()` first — so the hole is
  **latent, and what closes it is a precondition that has nothing to do with
  marking**. That is exactly D-396's failure shape from one cycle ago, where
  `drift()` was green only because a default argument happened to point at the
  right scene.
- **Scope was cut at the reading, not at the deadline.** 05:00 ran 37m10
  against a 35m budget. This cycle took `elapsed` before committing to the
  conversion and stopped there.

## North-star delta

- **No planner movement. 0 rollouts.** 29 cycles now.
- One open question closed with a measurement instead of a preference, and the
  closure is a guard rather than a paragraph — a production caller appearing
  turns it red.
- The honest read: this is the same category as the last several cycles —
  a real defect in this branch's own bookkeeping, found and fixed, moving no
  controller.

## Key learnings

- **A question's own scope is not a census.** Q-176 instructed a grep of two
  named symbols; the population was three. When the instruction names members,
  derive the set anyway and let the two disagree — that disagreement was this
  cycle's only genuinely new information.
- **"No caller" and "no reachable caller" are different answers, and the second
  one is the dangerous kind.** The mark defense is standing today because
  `excited()` short-circuits, not because the mark works. A defense propped up
  by an unrelated precondition reads green and is one harvest away from not
  being.
- **The empty-population trap is now reflexive on this branch.** Every verdict
  here is `()`-shaped, so the tests assert `len(sites) == 8` before asserting
  the verdict, and a synthetic non-test path exercises the classifier.

## Recommended next 1–3 priorities

1. **Execute Q-176's (b)** — `second_ratio` / `second_baseline_ratio` /
   `aligned_second_is_gradeable` return `float | None`, `marked()` grows a
   `None` branch, the 8 test sites move to a raw accessor. Now measured and
   scoped: 4 production functions, 8 sites. Needs a full cycle's EXECUTE.
2. **Audit the non-float `printed_load_bearing()` members** (`distinct_arms`,
   `column_licensed`, `third_paired`) — carried over from 05:00, still true:
   `marked()` would format bools/ints as `x.xx` if a scene ever flattens.
3. **The branch-scope question is now 29 cycles old** — user-blocked, unchanged.

## Artifacts

- PR: #67 (open, this branch)
- Files touched: `eval/mppi_sandbox/tail_mean.py`,
  `eval/mppi_sandbox/tests/test_tail_mean.py`, `docs/decisions.md`,
  `docs/deliberations.md`
- TSV row appended: pending

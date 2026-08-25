# The first real CI verdict in two days was FAIL, and the tests were reading a different repository

- **Cycle**: 2026-08-05 16:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: STATE #1 / #2 — build `ci_verdict.py`; verify the ceilings cleared
- **Phase**: P3
- **Status**: keep

## What I tried

- Picked STATE #1 (`ci_verdict.py`, read the authority per **job**) and STATE #2
  (did D-085's fast=30 / slow=120 raise actually clear the ceilings). Read the
  authority per job by hand first, to have a fixture to build against.
- **STATE #2 answered immediately, and it changed the cycle.** The 15:00 push's
  `fast` job **reached a verdict** — 22m31s, first non-`cancelled` job since
  2026-08-03T23:18Z. D-085's raise worked. The verdict was **`failure`**: 10
  tests, on the tree `push_preflight` had certified `GREEN` forty minutes
  earlier.
- So the pick became the thing the verdict says: `eval/mppi_sandbox/git_surface.py`,
  a probe for whether *this clone* can answer a question about repository history,
  with five verdicts and `UndecidableSurface` carrying the one that applied.
- Wired it into the four blind call sites in `local_only_audit`, and rewrote the
  eight affected tests to assert on **both** surfaces.

## What worked / what failed

- 🔴 **The defect is an inversion, not a crash.** `branch_committed` folds
  `git log origin/main..<ref>` over `refs/remotes/origin/autoresearch/*`.
  `actions/checkout@v4` gives a clone with **none** of those refs, so the fold
  ran over the empty set and returned `frozenset()` — which
  `derived_local_only` subtracts, concluding that no branch commits
  `docs/decisions.md` or `docs/deliberations.md`. Those two paths are the
  **contrast case in the module's own docstring**, the example of durable record
  that is *not* local-only. The derivation did not degrade. It returned the
  opposite answer, in the shape of an answer.
- ✅ **Both readings were right, and that is the finding.** `push_preflight`
  measures a **worktree**; the authority measures a **checkout**. D-082 closed
  the gap between "committed" and "measured"; this is the gap between
  "measured *here*" and "measured *there*", and no local instrument can see it.
- 🔴 **The first guard was under-broad, and only a clone found it.** I shipped
  `require_branches` on the branch-fold callers. A `git clone --depth 1` of this
  repo has one autoresearch ref and **no `origin/main`** — it passed the narrow
  guard and then died at exit 128 six frames down. `require_history` requires
  both halves. No dev-box run can distinguish the two guards, because on the dev
  box both halves are always present; running the suite inside a deliberately
  impoverished clone is what caught it, and that is now the verification step.
- 🔴 **Three tests were passing *because* of the inversion.**
  `test_no_underived_declarations`, `test_repo_layout_inventory_...`, and the
  five `test_each_declaration_names_a_writer[*]` parametrisations were green on
  CI before this cycle — the empty fold happened to produce a population they
  accepted. Converting the silent wrong answer into a refusal made them red,
  which is the correct direction: they had been *confirming* a derivation that
  was inverted.
- ✅ **Guarded with `if/else`, never `skipif`.** A blind clone makes each test
  assert that the probe fired **and named the right verdict**; a decidable one
  asserts the real claim. A `skipif` would have made the CI half of the suite
  silent, which is the vacuity defect this module is *about* (D-075, D-081).
- 🔴 **The positive control was written on the wrong surface first.** Draft one
  asserted `reading() == DECIDABLE` against the real repo — true on the dev box,
  false on CI, so the `DECIDABLE` branch would have been exercised only where
  the bug never was. Replaced by a **constructed** decidable clone, so every
  surface exercises it. D-079's finding, again, in the control again.
- ✅ **Verified on both surfaces**: 29/29 on the dev box, **29/29 inside a
  `--depth 1` clone** that reads `NO_MERGE_BASE`.

## North-star delta

- **No avoidance or tracking number moved — fifty-fourth consecutive instrument
  cycle.** Scenes able to contribute an avoidance number: 5, reportable: 4 —
  unchanged.
- What moved is that **the authority spoke for the first time in two days, and
  it said the branch was wrong.** Every `sandbox:pass=N/N` recorded on this
  branch since 2026-08-03T23:18Z was a claim about this dev box, and at least
  ten tests of that claim did not hold on the machine that matters.
- D-085's ceiling raise is **confirmed effective for both jobs**. `fast`:
  22m31s verdict under the 30-min cap, 7.5 min headroom (25%). `slow`: observed
  **still running at 60.4 min** — past the old 60-min ceiling that killed it at
  60.2 min on all 12 prior runs, so the 60→120 raise demonstrably took effect.
  Its final duration and verdict were still pending at cycle end.

## Key learnings

- **A green local suite is not evidence about CI, and this project had no
  instrument that could say so.** D-043 polices *when* a count is taken, D-082
  polices *whether* one exists — neither asks *where*. That is a third axis and
  it was completely uninstrumented.
- **Silence-read-as-a-verdict now has three confirmed instances in this package**
  (`push_preflight`'s `VACUOUS`, `ci_verdict`'s planned `UNRUN`, this module's
  `NO_REMOTE_BRANCHES`). It is not a recurring accident; it is the default
  outcome whenever a fold's empty case is spelled like its negative case.
- **An environment-dependent instrument cannot be debugged by reading it.** Both
  real defects this cycle — the inversion and the under-broad guard — were found
  by *constructing the impoverished environment and running in it*. Reading the
  code found neither.
- **A test that passes on both surfaces for different reasons is stronger than
  one that skips on one.** The `if/else` shape costs three lines and makes CI
  assert the probe rather than assert nothing.

## Recommended next 1–3 priorities

1. **Build `ci_verdict.py`** — still uncollected, and now with two measured
   constraints rather than one: read per **job**, `UNRUN` distinct from `FAIL`,
   plus `headroom()`. The 15:00 run is a fixture containing `failure`,
   `in_progress` and (from 08-04) `cancelled` on one branch.
2. **Run the suite in a `--depth 1` clone as a push-gate step.** This cycle
   found two real defects that way and zero by reading. `push_preflight` should
   grow a `--clone` mode, or the ten remaining git-reading instruments are
   unaudited on the surface that decides.
3. **Add `fetch-depth: 0` + a remote-ref fetch to the CI checkout.** Orthogonal
   to the probe and worth having: it moves CI from `NO_REMOTE_BRANCHES` to
   `DECIDABLE`, at which point the same tests assert the *stronger* branch with
   no edit here.
4. **Confirm the `slow` job cleared 120 min** — unmeasured at cycle end.

## Artifacts

- PR: #67 (existing — 78th consecutive cycle writing into it, no new review bandwidth)
- Files touched: `eval/mppi_sandbox/git_surface.py` (new),
  `eval/mppi_sandbox/local_only_audit.py`,
  `eval/mppi_sandbox/tests/test_git_surface.py` (new),
  `eval/mppi_sandbox/tests/test_local_only_audit.py`
- TSV row appended: yes

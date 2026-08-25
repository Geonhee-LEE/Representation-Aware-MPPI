# The run said nothing while one of its jobs had already failed

- **Cycle**: 2026-08-05 17:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: `STATE #1` Build `ci_verdict.py` — read the CI authority per job
- **Phase**: P3
- **Status**: keep

## What I tried

- Built `eval/mppi_sandbox/ci_verdict.py` (STATE #1, carried four cycles): the CI
  authority read **per job**, never off the run-level `conclusion`. Five job
  verdicts (`PASS`/`FAIL`/`UNRUN`/`PENDING`/`UNREADABLE`) plus `NO_JOBS`, folded
  into a run verdict by an explicit precedence with `FAIL` first.
- `headroom()` meters each job against the `timeout-minutes` declared for **it**
  in the workflow, parsed from the YAML rather than remembered.
- 26 tests, every fixture a **verbatim** `gh api` record from this repo taken at
  2026-08-05T08:00Z — three runs covering `failure`, `cancelled`, `in_progress`.
- Exercised the CLI against the live authority (`run`, `latest`, `caps`), which
  is where the cycle's actual finding came from.

## What worked / what failed

- 🔴 **The record that forced the module was live while I wrote it.** Run
  `30981826577` (head `70e2863`) published `status=in_progress conclusion=null`
  while its required `fast` job had been `failure` for **63 minutes**. Both
  records are accurate. Only one answers "is this branch red", and it is not the
  one `gh run list --json conclusion` prints — which is what every prior
  instrument here reads.
- 🔴 **This is the fourth instance of the pattern `git_surface` tabulated, and it
  runs the opposite way.** `push_preflight`'s `VACUOUS`, `git_surface`'s
  `NO_REMOTE_BRANCHES`, `local_only_audit`'s inversion — all three turn *absent*
  evidence into a false clean bill. This one hides a verdict that **already
  exists** behind an aggregate that is merely late. Hence `FAIL` ranks above
  `PENDING`: a failed job is a red branch the instant it completes.
- ✅ **`UNRUN` closes a row `git_surface`'s docstring had already written for it.**
  That table predicted this module's verdict name before the module existed;
  building it turned a prediction into a checked one.
- 🔴 **I shipped an overclaim and caught it by running the thing.** The docstring
  said a job near its cap is visible "before it starts getting killed". It was
  not: unfinished jobs have no duration, so `at_ceiling` could only ever speak
  post-mortem — it would have reported D-085's breach exactly as late as the
  humans did. Fixed the capability (`approaching_ceiling`, metered forward off
  elapsed time) rather than softening the sentence.
- ⚠️ **`job_caps()` reads today's workflow**, so a historical run is metered
  against caps it never ran under: the 03:34Z `cancelled` run scores +50%
  headroom under D-085's raised 120-min cap and was a breach of the 60-min cap
  actually in force. Named in the docstring; the tests pass epoch caps explicitly.

## North-star delta

- **No avoidance or tracking number moved — fifty-fifth consecutive instrument
  cycle.** Scenes able to contribute an avoidance number: 5, reportable: 4,
  unchanged. The 가려진-obstacle class still has one working cost term (D-027).
- What moved: **the cost of reading the authority went from three manual
  `gh api` calls to one command**, and the reading is now correct in a case
  where the obvious field is wrong.
- **STATE #3 answered, then the answer changed inside the cycle.** At 17:20 the
  `slow` job on `70e2863` was at 92.1 min and alive, and I wrote that D-085's
  raise was holding. By 18:35 it had run to **120.2 min and been killed AT THE
  CEILING**. The 60 → 120 raise was **also not enough** — third consecutive
  ceiling half-fix (D-084 raised one job of two, D-085 doubled the other and
  still undershot). STATE #3's own conditional has now fired: *"if it breaches
  120 the growth is worse than doubling and the fast/slow split itself needs
  revisiting."*

## Key learnings

- **A summary field and the thing it summarises are two different measurements,
  and the summary can be *behind*.** The three prior instances of this project's
  silence-read-as-verdict pattern were all absence-read-as-clean. This one is
  lateness-read-as-clean, which is why being told about the pattern three times
  did not prevent it.
- **A meter that only reads post-mortem is a description of the wreck.** The
  same threshold has to be readable forward or it reports the breach on the
  breach's schedule, not ahead of it.
- **Writing the docstring first is how I caught my own overclaim** — the prose
  asserted a capability the code did not have, and running the CLI is what
  showed the gap. Cheaper than the alternative, which was a future cycle
  trusting the sentence.
- **The tool answered its own first next-priority before the cycle ended, and
  the answer was good news.** Run `30987013397` (`adeca21`, the 16:00 D-086 fix)
  reached `fast` = `FAIL` at **1 failed, 933 passed** — D-086 took CI from **10
  failures to 1**. The residual is not a leftover: `test_screen_refinds_d050s_mask`
  asserts `'INERT' in ('CANDIDATE', 'UNRUNNABLE')`, i.e. `exemption_masking`
  grades a pair `INERT` on the CI checkout and something else here. That is
  D-086's own vocabulary-poverty finding — one verdict standing in for two
  distinguishable situations — reproduced **one module over**, which is exactly
  what STATE #5 predicted and nobody had yet acted on.
- **And the run-level disagreement reproduced on a second, independent run**:
  `30987013397` also published `in_progress`/`null` while its `fast` job was a
  completed `failure`. Two for two — this is the API's normal behaviour, not a
  one-off race, which is the strongest possible support for the module's
  precedence rule.

## Recommended next 1–3 priorities

1. **Fix `exemption_masking`'s surface-dependent `INERT`** — the single
   remaining CI failure, and it is D-086's vocabulary-poverty defect one module
   over (STATE #5, now with a live red test naming it). Highest-value item on
   the board: it is the last thing between this branch and a green authority.
2. **Revisit the fast/slow split, do not raise 120 again.** Three consecutive
   ceiling half-fixes; `slow` breached a *doubled* cap. The growth is superlinear
   in instrument count and this cycle added another instrument, so a fourth raise
   buys one more day. Split the slow half or stop growing it.
3. **Wire `ci_verdict` into `push_preflight`'s vocabulary**: the push gate
   certifies a *worktree* and the authority judges a *checkout*; the gate should
   be able to say "the last authority reading on this branch was `FAIL`/`UNRUN`".

## Artifacts

- PR: pending merge (`autoresearch/p3-epistemic-shadow-cost-critic`, PR #67)
- Files touched: `eval/mppi_sandbox/ci_verdict.py`,
  `eval/mppi_sandbox/tests/test_ci_verdict.py`, `docs/decisions.md`,
  `results/p3-epistemic-shadow-cost-critic.tsv`
- TSV row appended: yes

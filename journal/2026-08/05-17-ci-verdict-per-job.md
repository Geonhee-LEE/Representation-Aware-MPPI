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
- **STATE #3 answered in passing.** The `slow` job on `70e2863` was at
  **92.1 min against the 120-min cap and still alive** — 32 min past the old
  60-min ceiling that killed it on 12 consecutive runs. D-085's raise is holding;
  no evidence yet on whether it breaches 120.

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
- **The branch head's CI is still unread.** Run `30987013397` (`adeca21`, the
  16:00 D-086 fix) was `PENDING` on both jobs at cycle end. Whether D-086
  actually cleared the 10 failures is *not yet known*, and no number in this
  cycle should be read as saying it did.

## Recommended next 1–3 priorities

1. **Read `30987013397` with the new tool** — one command now — and find out
   whether D-086's `git_surface` fix cleared the 10 CI failures. This is the
   first open question of the next cycle.
2. **Wire `ci_verdict` into `push_preflight`'s vocabulary**: the push gate
   certifies a *worktree* and the authority judges a *checkout*; the gate should
   be able to say "the last authority reading on this branch was `FAIL`/`UNRUN`".
3. **Give `push_preflight` a `--clone` mode** (STATE #2, unchanged) — D-086 found
   two real defects by running in a `--depth 1` clone and zero by reading.

## Artifacts

- PR: pending merge (`autoresearch/p3-epistemic-shadow-cost-critic`, PR #67)
- Files touched: `eval/mppi_sandbox/ci_verdict.py`,
  `eval/mppi_sandbox/tests/test_ci_verdict.py`, `docs/decisions.md`,
  `results/p3-epistemic-shadow-cost-critic.tsv`
- TSV row appended: yes

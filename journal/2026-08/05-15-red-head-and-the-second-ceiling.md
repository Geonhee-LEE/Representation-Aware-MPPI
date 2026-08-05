# The push gate caught its first genuinely red tree — and D-084's CI fix was half a fix

- **Cycle**: 2026-08-05 15:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: STATE #2 / 14:00 rec #1 — read back what the authority said
- **Phase**: P3
- **Status**: keep

## What I tried

- Opened on **two unpushed commits** (`e54df9b`, `f2b8a8e`) — the *fifth*
  crash-before-push of 2026-08-05. Ran the receipt gate before doing anything
  else, intending a quick push of 14:00's CI fix and then the `ci_verdict.py`
  the 14:00 cycle recommended.
- The gate returned **`RED`**, not `GREEN`: **3 failures at `f2b8a8e`**. So the
  cycle became the repair, and `ci_verdict.py` did not get built.
- Measured the CI streak **per job** instead of per run, to size the fix 14:00
  had already committed.

## What worked / what failed

- ✅ **`push_preflight` refused a genuinely bad push for the first time.** Every
  prior appearance was a paper instrument passing its own tests. Here it was the
  only thing standing between origin and a red tree — and the three failures are
  all from `inert_surface.py`, written at 13:00, **committed at 14:00 by a cycle
  that never ran the suite**, with a second commit stacked on top. D-082 gates
  the *push*; nothing gates a *resume*, and a resumed commit inherits the
  previous cycle's unverified tree.
- 🔴 **The module's only negative control was inverted, and the cause is
  reflexivity.** `test_control_a_path_nobody_mentions_grades_no_reader` spelled
  its subject as a **literal**, and `mentions()` scans every Python source
  *including the test file* — so the scan truthfully found a reader (itself) and
  graded `HAS_READER`. D-079's rule (ship the control with the instrument) was
  obeyed and was **not sufficient**: a control over a whole-corpus scan is inside
  the population it controls. Fixed by assembling the path at runtime, and the
  contamination is now pinned as its own property rather than papered over —
  `classify` counts *mentions*, not *reads*, which is exactly why the dynamic
  probe exists.
- 🔴 **My first fix reproduced the bug inside the fix.** The sibling test I added
  to pin the contamination spells the literal, which put it back in the corpus
  and the control failed again. Two tests over one whole-corpus scan cannot share
  a subject; they now use distinct paths.
- 🔴 **Census cost, 23rd consecutive cycle**: `inert_surface.readers` takes the
  guard pool **66 → 67** (`rel not in direct`, DERIVED, so `unwatched_exemptions`
  is unmoved — the cheap kind). The informative member is the one that stayed
  **out**: `inert`, the function the module exists to publish, narrows by
  `verdict == VERDICT_INERT` — **D-079's invisible spelling for a third
  consecutive cycle, in a third module written without reference to the other
  two.** The detector now has a repeated record of missing precisely the function
  each new instrument is built around.
- 🔴 **D-084's CI fix was half a fix, and read as a whole one.** Measured per
  **job**, the cancelled streak has **two** ceiling crossings ~10 h apart, not
  one: `fast` crossed 10 min at `2be88f0a` (08-03T23:18Z); `slow` crossed **60**
  min at `ed80d0bd` (08-04T09:32Z) and has been killed at **60.2 min on all 12
  runs since**. Both jobs are required, so raising only `fast` would have left
  every run `cancelled` and the authority still silent. Slow raised 60 → 120.
- 🔴 **"27 consecutive runs with no verdict" is false at job level, and the error
  runs the *other* way too.** Run-level `cancelled` masked **7 genuine slow-job
  `failure`s** and **2 genuine `success`es**. D-084 established that `cancelled`
  gets misread as `FAIL`; the same word also hides real `FAIL`s underneath it.
  Any reader of the authority must read **jobs**, never the run conclusion —
  which is now a measured design constraint on `ci_verdict.py` rather than a
  guess.
- 🔴 **`NO_RECEIPT` is close to unreachable in practice.** `/tmp/suite-receipt.json`
  outlives the cycle, so a crashed cycle finds the *previous* cycle's receipt.
  I hit this directly: an existence check matched 12:00's leftover (head
  `9fe05a0`, 897 passed) before my own run finished. `check` graded it `STALE`
  and was right, so the gate is sound — but the verdict D-082 was written for is
  mostly served by `STALE`, and the receipt path is not keyed to a cycle.

## North-star delta

- **No avoidance or tracking number moved — fifty-third consecutive instrument
  cycle.** Scenes able to contribute an avoidance number: 5, reportable: 4.
- Real and procedural: origin was **two commits behind a red tree**, and both the
  redness and the remaining CI blindness are fixed in this cycle. Once this
  pushes, Sandbox CI can reach a verdict for the first time since
  **2026-08-03T23:18Z** — every `sandbox:pass=N/N` recorded since is a claim
  about this dev box alone.

## Key learnings

- **A gate on the push is not a gate on the commit.** The resume path (decision
  tree step 1) inherits an unverified tree and adds to it; two cycles compounded
  before anything asked.
- **A control that names its subject joins the population it controls.** The fix
  is not "write better controls" — it is that a whole-corpus scan has no clean
  negative control expressible *inside* the corpus.
- **Read the authority per job, not per run.** One word at run level collapsed
  27 absences, 7 real failures and 2 real passes into the same token.
- **Sizing a fix from the run-level symptom sizes half of it.** D-084 saw one
  ceiling because run conclusion has no per-job resolution; the second ceiling
  was ten hours old and invisible at that altitude.

## Recommended next 1–3 priorities

1. **Build `ci_verdict.py`** (14:00 rec #1, carried) — now with a measured
   constraint: read **jobs**, never the run conclusion, with `UNRUN` distinct
   from `FAIL`, plus `headroom()` metering each job against its cap. The 08-04
   job records are a ready-made offline fixture with all three verdicts in it.
2. **Verify the ceilings actually cleared.** This cycle's push is the first run
   under fast=30 / slow=120; if `slow` still breaches 120 the growth is worse
   than doubling and the split itself needs revisiting.
3. **Gate the resume path, or key the receipt to a cycle.** `NO_RECEIPT` is
   near-unreachable while the artifact outlives the cycle at a fixed `/tmp` path.

## Artifacts

- PR: #67 (open, autoresearch/p3-epistemic-shadow-cost-critic)
- Files touched: `eval/mppi_sandbox/inert_surface.py`,
  `eval/mppi_sandbox/tests/test_inert_surface.py`,
  `eval/mppi_sandbox/tests/test_guard_reflexivity.py`,
  `.github/workflows/sandbox-ci.yml`, `docs/decisions.md`
- TSV row appended: yes

# The authority has produced no verdict in 30 hours, and "cancelled" was read as both a failure and a pass

- **Cycle**: 2026-08-05 14:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: STATE #2 / Q-086 — take the probe on a still tree and transcribe the pins
- **Phase**: P3
- **Status**: keep

## What I tried

- **Resumed the 13:00 cycle**, which wrote `inert_surface.py`, its test, the
  `push_preflight` rewiring, D-083 and Q-086 — and committed **none** of them.
  Fourth crash-before-commit-or-push of 2026-08-05. Committed as `e54df9b`.
- Opened the edit-free window Q-086's action asked for and started the probe.
- While it ran (read-only work only), checked PR #67's actual CI state — the
  thing the pick was ultimately in service of.

## What worked / what failed

- 🔴 **PR #67's CI has produced no verdict of any kind for ~30 hours.** Sandbox
  CI on this branch: last `success` `b1f07110` at 2026-08-03T14:18Z (= 08-03
  23:18 KST, **~39 h ago**; fast **5m55s**, slow 25m26s). Then **9** real
  `failure`s — those did reach a verdict. Then, from `2be88f0a` at
  2026-08-03T23:18Z (= 08-04 08:18 KST), **27 consecutive `cancelled`** runs,
  every one killed at its `timeout-minutes` cap (10m16s / 1h0m15s against
  **10** / **60**). There is no `concurrency: cancel-in-progress` in the
  workflow; the caps are the cause.
- 🔴 **`cancelled` was read in both wrong directions at once.** `gh pr checks`
  prints it as **`fail`**, so a human reading the PR hunts a broken test that
  does not exist; and a cycle holding a green local receipt reads the same word,
  concludes "stale CI", and records *"PR #67 is green on origin as of this
  cycle"* — which 12:00's `STATE.md` does. An **absence** of evidence rendered
  as a word meaning evidence of absence. `UNRUN` is not a shade of `FAIL`.
- 🔴 **The lesson was already written down, one job below the line it should
  have changed.** The slow job's comment says the ceiling must sit far above the
  measurement — *"how the old job got a 10-minute ceiling that silently became
  the thing under test"* — written **about this job**, applied only to the other
  one. D-078's "(checked)" and D-083's parenthesis, a third time, in YAML.
- 🔴 **D-082 cannot see any of this, by construction.** Its own docstring
  concedes *"the PR's CI remains the only authority for the pushed tree"* — and
  the branch has a gate that reads the **local** receipt and no reader at all
  for the authority it defers to. A 3-minute local green licenses a push whose
  CI is guaranteed to be killed.
- 🔴 **The pick did not land: the probe does not fit a cycle, on a lower bound
  alone.** Window opened 14:02:08. **Measured**: one subset run (12 test files)
  had **not finished at 4m18s**. The probe needs **8** such runs (4 candidates ×
  before/after), so if they are comparable the floor is **~30 min** — over the
  15-min EXECUTE budget by itself. **Not measured**: the total, because I stopped
  it. The floor alone answers Q-086 against its own stated next action (a).
- 🔴 **`probe()`'s restore is not signal-safe.** It rewrites the original bytes
  in a `finally`, and `SIGTERM` does not run `finally` — a code fact, checkable
  by reading it. A probe mutation was in `RESULTS.md` after the kill, though
  **which run left it is undetermined**: the 13:00 cycle also started this probe
  and also never finished it. Harmless either way here (`RESULTS.md` is
  regenerated from `results/*.tsv`), lossy for any candidate that is not.
- ✅ **The fix is one line and restores the authority**: fast job
  `timeout-minutes` 10 → 30, with the measurement and the cross-reference in the
  comment. `PROBED` still ships empty, so the gate is unchanged.

## North-star delta

- **No avoidance or tracking number moved — fifty-second consecutive instrument
  cycle.** Scenes able to contribute an avoidance number: 5, reportable: 4.
- Negative and real: **27 pushes were never verified by anything but this
  machine**, so every `sandbox:pass=N/N` recorded since 08-04 08:18 KST is a
  claim about the dev box alone. The suite's cost is superlinear in instrument
  count — the instrument tests verify by spawning subprocess pytest runs — so
  the branch spent the CI budget the avoidance tests would need.

## Key learnings

- **A cancelled job is not a failing one, and no surface in this project says
  so.** Every layer collapses the distinction: GitHub's own UI, `gh pr checks`,
  and the cycle's prose. The distinction is the finding.
- **A gate that reads only its own side of the boundary cannot notice the other
  side stopped answering.** D-082 is correct and was never sufficient.
- **An instrument's runtime is a design constraint, not an implementation
  detail.** The probe is correct and unaffordable; correctness did not save it.
- **Restore-on-`finally` is not restore.** Any instrument that mutates a tracked
  file needs signal-safe restoration or it is one `Ctrl-C` from data loss.
- **I published four wrong magnitudes in this cycle's own first draft**, and the
  cause was reading `ps` `etime` as `HH:MM` when it is `MM:SS`. That produced
  "~28 min", "35–45 min", "18 consecutive", "25 hours" — all of them stated with
  the same confidence as the correct ones, in D-084, the YAML comment and this
  file. Caught before push only because a stray `date` call disagreed with my
  arithmetic. The branch's own rule applied to the branch's own cycle: **a
  magnitude is only as good as the reading it came from**, and a unit is part of
  a reading. The corrected counts are re-derived from the API in-cycle, and the
  one quantity I could not re-derive — the probe's total runtime — is now stated
  as a **lower bound**, not a figure.

## Recommended next 1–3 priorities

1. **Build `ci_verdict.py`** — read back what the authority said about the
   pushed sha, with `UNRUN` (cancelled/timed-out) a first-class verdict distinct
   from `FAIL`, plus `headroom()` metering the cap the branch keeps spending.
   Draft docstring already written; this closes D-082's stated gap.
2. **Make `probe()` signal-safe**, and re-take it under Q-086 option (b) — a
   dedicated `git worktree`, since option (a) is now measured unaffordable.
3. **Register D-044's "(checked)" as a `MEASURED_CLAIM`** (13:00 rec #2) and
   `constant_population` (STATE #1) — both still uncollected.

## Artifacts

- PR: #67 (open, autoresearch/p3-epistemic-shadow-cost-critic)
- Files touched: `.github/workflows/sandbox-ci.yml`, `docs/decisions.md`,
  `docs/deliberations.md`, plus `e54df9b` resuming the 13:00 cycle
  (`eval/mppi_sandbox/inert_surface.py`, `tests/test_inert_surface.py`,
  `push_preflight.py`)
- TSV row appended: yes

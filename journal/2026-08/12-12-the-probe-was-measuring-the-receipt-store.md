# The probe was measuring the receipt store, not the TSV

- **Cycle**: 2026-08-12 12:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: _no Notion TODO_ — STATE next-actionable #2 (Notion MCP still unauthorized)
- **Phase**: P3
- **Status**: keep

## What I tried

- STATE's next-actionable **#1** was to make `push_preflight record` archive a
  receipt unconditionally. Read the code first: it has done exactly that since
  **D-203** (`8ed2347`, 2026-08-11 22:17), comment and all. The item's premise —
  "archiving is a step a cycle must remember" — is false, and D-214's short
  reach (78/94 `OUT_OF_REACH`) is explained entirely by the store being one day
  younger than the journals it grades. Nothing to build; STATE corrected.
- Moved to **#2**: audit the other `POST_RECEIPT_WRITES` readers for D-215's
  path-vs-candidate confusion. `survey`, `leaking_pins`, `inert` and `_main` all
  iterate the population **by candidate** and never accept a path, so none of
  them can host that confusion — it is reachable only from a caller that starts
  with drift paths, which is `filter_drift` alone (fixed by D-215).
- The audit found the defect one layer down instead: `_probe_target` is the
  *other* statement of the prefix rule (candidate → path, where
  `covering_candidate` is path → candidate), and it was selecting the wrong file.

## What worked / what failed

- 🔴 **`_probe_target("results/")` returned `results/receipts/056933be411376b4.json`.**
  `receipt_store.STORE_DIR` is `results/receipts/` (D-203), gitignored, rewritten
  by every `record` — so it is by construction the newest file under the
  `results/` prefix, and the recursive walk took it. The exemption `results/`
  licenses covers the **TSV row** D-044 named; the verdict backing it was
  measured on a JSON blob the probe would have appended an HTML comment to.
- This is `journal/README.md`'s failure exactly (the one the recursion was added
  to fix), recurring one level in — **not an error but a success on the wrong
  file**. Worse here: the wrong file is *untracked*, and an exemption suppresses
  paths in `tp.Drift`, computed over `git ls-files`. A verdict measured on an
  untracked file licenses a suppression that file can never be the subject of.
- Fixed by filtering probe targets through the **index** rather than by naming
  `results/receipts/` as a directory to skip — the by-name fix would have left
  the next untracked write under a pinned prefix to be found the same way.
  `results/` now probes `results/p3-epistemic-shadow-cost-critic.tsv`.
- `tracked=None` is kept as a caller's **stated choice** (the synthetic-tree
  tests are not repositories); the default is a `_DERIVE_TRACKED` sentinel, so
  "derive the index" cannot collapse into "ignore the index" the way a `None`
  default would — `tree_provenance._git`'s stated refusal to degrade silently.
- 🔴 `inert_surface staged` reported `STAGED_MOVED` on 3 pins with "this cycle
  added a reader". `entrants()` says otherwise: the entrants are
  `test_quoted_counts.py`, `test_receipt_store.py`, `test_suite_shard.py` — D-203,
  D-211 and D-214's, not mine. **The pins were already stale before this cycle
  touched the tree.** Same misattribution D-213 flagged and STATE has carried
  for three cycles; measured again rather than assumed.

## North-star delta

- No movement in capability — 17th consecutive instrument cycle. Honest zero.
- What moved is that one of the five exemptions the push gate grants was resting
  on a measurement of the wrong file, and now is not.

## Key learnings

- **A STATE next-actionable is a claim about the tree, and claims decay.** #1 was
  authored one cycle after the code that satisfied it landed. Reading the target
  before building cost one `grep` and saved the cycle.
- **Adding a store *under* a pinned prefix silently re-aimed that prefix's probe.**
  D-203 and `_probe_target` were each locally correct; the defect lives in the
  interaction, and nothing in either module could see it.
- **"Two statements of one rule" (D-047) is not only about duplicated code.**
  `covering_candidate` and `_probe_target` are inverses, not copies — and the
  round trip between them was never checked, which is now a test.
- The audit's stated target was clean; the finding was one layer below it. Worth
  recording that the *negative* result on `survey`/`leaking_pins`/`inert` is a
  real deliverable, not a wasted pass.

## Recommended next 1–3 priorities

1. Fix `inert_surface`'s `STAGED_MOVED` message to name what it measured —
   `entrants()` already returns the names, and this cycle is the third to
   hand-refute the same sentence.
2. Re-probe the 3 stale pins (`STATE.md`, `journal/`, `results/`) — `results/`'s
   pin is now doubly owed, since its prior verdict was about the receipt store.
3. Decide whether `nested_timeout.OBSERVED_SUITE_SECONDS` needs D-213's era
   treatment, or write the one line saying the question is closed.

## Artifacts
- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic, PR #67)
- Files touched: eval/mppi_sandbox/inert_surface.py, eval/mppi_sandbox/tests/test_inert_surface.py, docs/decisions.md, journal/2026-08/12-12-the-probe-was-measuring-the-receipt-store.md
- TSV row appended: pending

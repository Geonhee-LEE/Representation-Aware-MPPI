# The cache must be invisible to the tree it caches

- **Cycle**: 2026-08-11 22:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: `STATE #1` Persist the suite receipt across cycle boundaries
- **Phase**: P5
- **Status**: in_progress

## What I tried

- Shipped `eval/mppi_sandbox/receipt_store.py`: a durable receipt store keyed by
  `worktree_fingerprint` — the same value `push_preflight.check` compares — so
  recall is a lookup and never a search. `archive` / `recall` / `recall_current`
  / `tracked_conflict` / `entries` + a CLI (`archive` / `recall` / `list`).
- Wired it into `push_preflight`'s `record` CLI unconditionally, with no flag to
  forget (D-162): `--out` is unlinked by the *next* `record`, so the receipt this
  cycle paid ~1220 s for is destroyed by the very cycle that would reuse it.
- 11 tests in `tests/test_receipt_store.py`, pinning the two properties that
  decide whether the store is worth having: archiving must not move the
  fingerprint it keys on, and the key must stay *derived* (a misfiled or
  truncated receipt is not evidence, it is `None`).
- Cut scope at `SUITE_UNAFFORDABLE` rather than at minute 34.

## What worked / what failed

- 🟢 **The untracked-store argument held under test.** `worktree_fingerprint`
  covers tracked files only; untracked paths land in a separate
  `untracked_digest` that `check` does not compare. So an untracked store is
  invisible to the stamp and its receipts stay valid. A *committed* store would
  change the tracked tree on every archive, invalidating each receipt the
  instant it landed — a cache that can never hit, failing silently (writes
  succeed, reads miss, nothing errors).
- 🔴 **My first directory choice was already taken, and `tracked_conflict`
  caught it on the first run.** I picked `results/readings/`, which is an
  existing **tracked** directory holding a different artifact class
  (`2026-08-05-04-ordering-control.json`). The `.gitignore` entry I had written
  would not have saved it — ignore rules do not apply to already-tracked files.
  Relocated to `results/receipts/`. The test I wrote to state the invariant is
  the only reason this was a 30-second correction instead of a store that
  quietly never hit.
- 🔴 **The cycle did not publish, and the cause is a real cost I did not price.**
  `inert_surface staged` fired `STAGED_MOVED` on four pins (`STATE.md`,
  `JOURNAL.md`, `RESULTS.md`, `results/`). The delta in all four keys is exactly
  one entrant — my new `test_receipt_store.py`. So **any** cycle that adds a
  test file touching these paths owes a reprobe *before* the suite, and I
  budgeted zero for it.
- 🔴 **The reprobe did not finish.** `reprobe` over the single entrant is the
  cheap path by construction (`INERT_COMPOSED`, ~3.5 min for four vs ~34), but I
  ran it under a `timeout 400` and it was killed with no verdict — the sunk cost
  bought nothing. The suite deadline passed 4m07 before that.

## North-star delta

- **No movement.** No controller / representation / dynamics / sim code touched,
  0 sim runs. `unsafe_rate` 0.0000 · `min_clearance` 0.3579 · `success_rate`
  1.0000 all carried unchanged.
- Infrastructure only, and **not yet banked**: the store is written and its own
  11 tests pass, but the branch is knowingly red on 6 `test_inert_surface`
  assertions until the pins are re-taken, and nothing was pushed.

## Key learnings

- **A cache whose key is derived from the tree must not be part of that tree.**
  This is the whole design, and it is a one-line difference (tracked vs
  untracked) between a working store and one that can never hit. The failure
  mode is silence, not error, which is why it got an assertion rather than a
  comment.
- **`staged` gave me the finding at the right moment and I spent it badly.** The
  reading fired at ~6m, correctly, naming all four pins — D-199 working exactly
  as designed. What I got wrong was the *response*: I reached for `probe`
  (2 min/path, four paths) before checking that `reprobe` existed for precisely
  this shape, and then capped the retry below its own known cost.
- **The pin tax belongs in the scope decision, not after it.** "Add a module +
  tests" reads as cheap and is not: a new test file re-keys four pins, and the
  reprobe must land *before* the suite. `cycle_wallclock elapsed` prices the
  suite; nothing prices this, so it is invisible at PLAN time — which is when it
  needed to be visible.

## Recommended next 1–3 priorities

1. **Finish this branch, in this order**: `reprobe` the four pins over the one
   entrant `eval/mppi_sandbox/tests/test_receipt_store.py` (no timeout under
   ~600 s), confirm `inert_surface staged` reads clean, then one suite via
   `push_preflight record`, then TSV row + push. The code is committed and its
   own tests are green; only the pins and the suite stand between here and a
   push.
2. **Price the pin tax in `cycle_wallclock`.** A cycle that adds a test file
   owes a reprobe before the suite, and the budget instrument currently prices
   only the suite. `elapsed` said `SUITE_AFFORDABLE` at 5m11 while a mandatory
   ~4 min reprobe was already owed and uncounted.
3. **First real use of the store**: once a receipt is archived, a repair cycle
   republishing an unchanged head should consult `receipt_store recall` and skip
   the suite. That is the payoff STATE #1 was picked for and it is untested
   end-to-end.

## Artifacts

- PR: pending merge (`autoresearch/p3-epistemic-shadow-cost-critic`, PR #67)
- Files touched: `eval/mppi_sandbox/receipt_store.py`,
  `eval/mppi_sandbox/tests/test_receipt_store.py`,
  `eval/mppi_sandbox/push_preflight.py`, `.gitignore`
- TSV row appended: pending

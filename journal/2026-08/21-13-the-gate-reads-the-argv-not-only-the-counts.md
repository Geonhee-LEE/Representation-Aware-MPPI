# The gate reads the argv, not only the counts

- **Cycle**: 2026-08-21 13:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: `3c3c5d39` D-402 step 3 — `check()` grades `receipt.command` against the registry
- **Phase**: P3
- **Status**: keep

## What I tried

- Added `SuiteScope` + `scope_of()` to `declared_suite.py`: the registry now
  grades an invocation's argv against itself, rather than only stating the list.
- Added the `SCOPED` verdict to `push_preflight.check()`, decided **after**
  `RED` and **before** `UNCOVERED_RED`.
- Repaired the fixture fallout the strictness caused: four receipt helpers
  across three test files were building receipts whose command named **zero**
  declared targets, so 18 tests that meant to assert `GREEN`/`UNDECLARED`
  flipped to `SCOPED`.
- Bumped the `guard_reflexivity` tally pin 134 → 135 — `scope_of` entered the
  registry it audits.

## What worked / what failed

- **The ordering is the entire fix, and it is not where I first put it.** A
  narrowed invocation collects only what it named, so there is no remainder for
  `uncovered_is_red` to catch and `suite_coverage.of` grades it `none left
  out`. Deciding coverage first would have let the narrow receipt past *on the
  strength of its own narrowness* — D-400's inversion, reproduced inside the
  gate meant to close it. `test_scope_is_decided_before_coverage` hands the
  check a `FAIL` verdict for the uncovered half to prove `SCOPED` wins the race
  rather than merely existing.
- **The fixture fallout was the real cost, and it was evidence, not noise.**
  Every one of those 18 receipts was green over an argv naming nothing. They
  had passed for as long as they had existed. That is D-400's hole with 18
  witnesses already in the tree, and nobody could see them because no assertion
  looked at `command`.
- **`census_preempt` earned its 2 seconds outright.** It reported `guard_tally
  135 vs pin 134` *before* the suite — the same red the suite would have taken
  ~25 min to report. This is the D-399 ordering (re-derive the census before
  typing the pin) applied rather than re-learned.
- Targeted subset: 196 passed, 6 skipped over the eight receipt/licence modules.
- **The first receipt suite came back RED (3 failures), and two of the three
  were my own fixture class arriving in a file I did not think to run.**
  `test_inert_surface.py` has a fourth receipt helper naming zero declared
  targets; I had fixed three files and enumerated the helpers by grepping
  `command=`, which found it — and I ran the subset without it anyway.
- **The third failure is the more interesting one.** `key_discrimination`'s
  narrow-key pin moved (19, 14) → (20, 15) because `scope_of` joined that
  population too. `census_preempt` had reported **all five of its censuses
  clean** and explicitly named the four it does *not* cover — and this census
  is in **neither** list. Its silence therefore read as coverage it never
  claimed.

## North-star delta

- **Zero. 36 cycles.** No controller, representation, or dynamics code was
  touched; 0 rollouts. This is process repair, not planner progress, and the
  honest reading is that the gate D-400 found unguarded is now guarded and the
  robot still cannot drive anywhere new.
- The one defensible claim: every push receipt from here on is a statement
  about the declared suite, so the *numbers* future cycles cite about planner
  work are worth more than yesterday's.

## Key learnings

- **A guard that reads a derived quantity can be defeated by shrinking the
  population the quantity is derived from.** `suite_coverage` was correct;
  it was computing over whatever pytest collected, and what pytest collects is
  chosen by the caller. Checking the population *before* believing any statement
  computed from it is the generalisation — `suite_coverage`'s own
  `EMPTY`-before-`FULL` rule, one level up.
- **An unrecorded command grades not-full.** Older receipts carry no argv, and
  grading those full would reopen the hole for exactly the receipts we know
  least about. Same rule `Receipt.worktree` already uses for missing per-path
  digests.
- **`census_preempt`'s omission list is itself an incomplete census.** It names
  four uncovered censuses; `key_discrimination` is a fifth it does not name, so
  a clean pass from it is weaker evidence than its wording suggests. This is
  D-317's finding recurring against the instrument built to answer D-317.
- **Deliberately not filtering option flags.** A flag cannot equal a declared
  path nor be a parent of one, so it never matches. Filtering would need a
  which-flags-take-arguments census kept in step with pytest — D-047's shape,
  in the module that exists to stop reproducing it.

## Recommended next 1–3 priorities

1. **Break the 36-cycle zero-delta streak — pick planner work, not gate work.**
   The verification surface is now in better shape than the thing it verifies.
2. Consider whether `_covers`' parent-directory rule is too generous: `eval/`
   passes, and a cycle wanting to cheat could type it. Cheap to tighten, but
   needs a reason beyond suspicion.
3. PRs #66–#69 are 41 days unmerged — the queue, not the code, is the binding
   constraint on this project.

## Artifacts
- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic)
- Files touched: eval/mppi_sandbox/declared_suite.py, eval/mppi_sandbox/push_preflight.py, eval/mppi_sandbox/tests/test_declared_suite.py, eval/mppi_sandbox/tests/test_push_preflight.py, eval/mppi_sandbox/tests/test_push_claim_gate.py, eval/mppi_sandbox/tests/test_suite_coverage.py, eval/mppi_sandbox/tests/test_guard_reflexivity.py, docs/decisions.md
- TSV row appended: yes

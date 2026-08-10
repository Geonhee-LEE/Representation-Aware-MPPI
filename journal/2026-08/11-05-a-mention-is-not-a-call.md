# A mention is not a call — the constructor D-188 said it had connected is still dead

- **Cycle**: 2026-08-11 05:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: STATE #1 — grep for constructors/readers with no non-test caller
- **Phase**: P5
- **Status**: keep

## What I tried

- Built `eval/mppi_sandbox/consumer_reach.py`: an **AST** census of every
  `classmethod`/`staticmethod` defined in the package's non-test modules, graded
  by where its call sites live — `LIVE` / `REFERENCED_NOT_CALLED` / `TEST_ONLY`
  / `UNREACHED`.
- Pinned the real-package residue in `test_consumer_reach.py` (19 tests), so a
  *new* dead constructor turns the suite red rather than waiting for a cycle to
  notice it three cycles later.
- Checked first whether the check already existed (`assert_reach`, `loop_reach`,
  `probe_reach` all sounded like it). They measure **assertion** reachability;
  no module measured caller reachability. The premise held this time — the first
  cycle in four where it did.

## What worked / what failed

- **STATE's own pricing was wrong, and the counter-example is the motivating
  instance.** STATE asked for "a grep for non-test callers". `grep -rn from_sweep
  eval/mppi_sandbox/*.py` returns **four** hits outside the definition — and
  three are prose (a module docstring, a method docstring, and the comment D-188
  wrote to explain its fix). A grep reads clean while the constructor is dead.
  D-047's "a comment is not a measurement" has a caller-counting corollary: **a
  mention is not a call**, and only a parser separates them.
- **The finding is that D-188 did not close D-187.** D-188 concluded that
  `WalkCount.from_sweep` "gets its first production caller in the repo". It did
  not. What D-188 shipped was `Rung` carrying `n_in_band`/`n_reached`, which
  satisfies the constructor's **duck type** — the argument now arrives in the
  right shape — but nothing invokes the constructor. Population 4, residue
  exactly 1, and it is `from_sweep`.
- So the same claim has now been made prospectively **twice** and collected
  **zero** times: D-187 ("a walk taken from here records `n_in_band`"), then
  D-188 ("`from_sweep` gains a production caller"). Each cycle moved the data one
  frame closer and each wrote the arrival as done.
- **The first suite came back red, and the finding was against this module.**
  Its first version excluded dunder hooks via a module-global `PROTOCOL_NAMES`
  frozenset — which added the package's **fifth unwatched allow list** and broke
  6 census pins across `guard_reflexivity`, `liveness_derivation`,
  `exemption_control` and `exemption_masking`. An instrument for counting dead
  consumers walked in carrying an exemption registry nobody watches. The repair
  replaced the list with a **rule** (`name.startswith("__")`), which needs no
  watcher; the unwatched set is now byte-identical with and without the module.
- The escape hatch bends toward silence deliberately: a name that appears as a
  bare-identifier string or an uncalled attribute grades
  `REFERENCED_NOT_CALLED`, not a finding, because a dispatch table keyed on the
  name is a real pattern here and a false alarm is what gets an instrument muted
  (D-044). Name-based matching also merges homonyms, which can only hide a
  finding, never invent one. The residue is a **lower bound**.

## North-star delta

- **No movement, and this cycle claims none.** No controller, representation,
  dynamics, or sim code; 0 sim runs. `unsafe_rate` 0.0000 / `min_clearance`
  0.3579 / `success_rate` 1.0000 unchanged; census attribution coverage still
  **0/6**, `NO_GRADED_RUNG`.
- What it buys is that the estimator chain P3's rate work depends on now has a
  **standing** reachability check instead of a per-cycle discovery. Three
  consecutive cycles found this defect class by hand; the fourth cannot.

## Key learnings

- **Duck-type compatibility is not reachability.** "The argument arrives in the
  right shape" and "something calls the function" are different propositions,
  and D-188 shipped the first while writing the second. The third screening
  question after *does the producer compute it?* and *does the consumer read
  it?* is **does anything call the consumer?** — and it is a parse, not a grep.
- **A prospective claim in a journal should be graded like a TSV row.** Both
  D-187 and D-188 wrote a future tense that the next cycle falsified. The cheap
  discipline is to state the frame the fix actually reaches and stop there.
- The population is only **4** — this package builds almost everything through
  `__init__`. That makes the check cheap and the finding sharp, and it means
  widening to module-level functions would bury a 1-item residue in CLI helpers.

## Recommended next 1–3 priorities

1. **Wire the production caller, or delete `from_sweep`.** The check is now
   red-able on exactly this; closing it means a census walk actually constructs
   a `WalkCount` from its `Rung` and pools as a point. This is the third attempt
   at the same frame — do it by making the call, not by making the shape fit.
2. **Point the constitution's Phase-3 pin check at `inert_surface pins`** and
   correct the stale 4a-ter prose (D-047 shape). Doc-only, now 15 cycles old.
3. **Fold "does anything call the consumer?" into the PLAN screening step**
   beside the existing produces/consumes pair.

## Artifacts

- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic)
- Files touched: `eval/mppi_sandbox/consumer_reach.py`, `eval/mppi_sandbox/tests/test_consumer_reach.py`, `docs/decisions.md`, `results/p3-epistemic-shadow-cost-critic.tsv`
- TSV row appended: yes

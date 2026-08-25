# What the fast receipt stops watching is the watchers — Q-126's premise was wrong about its own drop-set

- **Cycle**: 2026-08-10 16:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: STATE #1 — close Q-126 using the table already on disk
- **Phase**: P5
- **Status**: keep

## What I tried

- Took STATE #1 exactly as written: 15:00 priced Q-126's option (a) to
  `COMPLETE`, so the close needed **zero** suite time and one doc write, done
  before this cycle's run per D-044.
- Before writing the close, read **what the four expensive modules actually
  are** — the one step the pricing did not take, since `receipt_cost` groups by
  module name and never opens them.
- Wrote the close as D-177 + resolved Q-126, and opened Q-127 for the hole the
  close uncovered.
- Deliberately did **not** ship the implementation; the reason is recorded in
  D-177 and repeated below, because it is a budget fact and not a preference.

## What worked / what failed

- 🔴 **Q-126's option (a) is written against a premise the measurement
  refutes.** Its text says drop "sim-bound module 을" — and **none of the top
  four are sim-bound**. `test_exemption_masking` (390.5s, 36.3%),
  `test_guard_reflexivity` (163.4s, 15.2%), `test_exemption_control` (103.9s),
  `test_probe_reach` (74.7s) all scan the **guard pool itself** by AST and
  subprocess git. So (a) never proposed watching the sim less. It proposed
  **watching the watchers less**, and that is a different purchase with a
  different cost column.
- 🟢 **The reframe changes the instrument, not just the prose.** These modules
  are *reflexive*: their subject is the guard pool, which moves only when a
  cycle edits `eval/mppi_sandbox/` guard sources. On a cycle that touches no
  guard, that 390s re-measures something that could not have changed — but on a
  cycle that adds one, it is the only thing that can catch a broken pin. A
  **fixed** drop therefore blinds the suite in exactly the cycle that needs it,
  which is why D-177 adopts (a) **diff-conditional** instead: full suite minus
  the guard meta-suite, exemption void the moment the diff touches
  `eval/mppi_sandbox/*.py`.
- 🔴 **The close uncovered a hole in its own safety net, and it is not
  theoretical.** Option (a)'s whole defence is "the full set still runs in CI".
  But `sandbox-ci.yml` triggers on `paths: ['eval/**',
  '.github/workflows/sandbox-ci.yml']` — a **docs-only PR runs no CI at all**.
  Combine fast receipt with a docs-only diff and the guard meta-suite runs
  **neither locally nor in CI**. And docs-only diffs *can* break guards:
  `citation_audit.SCANNED_DOCS` is precisely `docs/decisions.md` +
  `docs/deliberations.md`, which is what D-044's entire ordering rests on.
  **This cycle is that shape** — two docs, zero `eval/` files. Opened as Q-127
  with the ordering made explicit: widen the CI `paths` *before* enabling the
  exemption, never after.
- 🟡 **The implementation was cut on arithmetic, not on taste.** The scope
  function narrows a population with `not in`, which is exactly the shape
  D-072's detector sees, so it enters the guard census as the **99th** and
  breaks the `len(pool) == 98` pin. Learning the new pin value requires
  `test_guard_reflexivity` (163.4s) and then the full suite again — two runs,
  against `runs_affordable == 1`. That is the hazard's second mouth, arriving
  exactly where 15:00's recommendation #3 predicted it would.
- 🟢 **Checked the docs against the citation guard before spending the suite**
  (`test_citation_audit`, 46 passed, 14.9s). A ~1000 s run that comes back red
  on a registerable magnitude costs the cycle, and the check that prevents it
  costs 15 seconds.
- 🟢 Suite **2285 passed** / 158 skipped / 1 xfailed, rc=0, **1079.36s**, log
  77,286 bytes. Against 15:00's 2286/157: totals match at 2443, so **one test
  moved passed → skipped**, not lost. That is the `git_surface.reading()`
  decidable split doing its job (`test_exemption_masking`'s census is a
  measurement *of this clone*), and it is noted rather than smoothed, per the
  precedent set when the same shift appeared at 2196.
- 🔴 **The stale 4a-ter prose fired for real this cycle, which is a stronger
  demonstration than 15:00's.** `tree_provenance verify` returned **rc=1** —
  drift on `JOURNAL.md` and `STATE.md`, both **declared local-only**, both
  inert, read by no test. Obeying the constitution's literal `verify || re-run`
  would have bought a second 18-minute suite for **zero** information, which
  `runs_affordable == 1` forbids outright. `declared` returned rc=0 and
  `push_preflight.check` filters exactly this drift through
  `inert_surface.filter_drift`, so the gate — not the prose — was treated as
  the authority. 15:00 demonstrated the staleness with a green `verify`; this
  cycle demonstrates it with a **red** one, i.e. D-044's muted-check hazard
  actually materialising rather than being argued about.

## North-star delta

- **No movement, claimed as none.** No controller, representation, dynamics or
  sim code. `unsafe_rate` 0.0000 / `min_clearance` 0.3579 / `success_rate`
  1.0000 unchanged; census attribution coverage still 0/6, `NO_GRADED_RUNG`.
- What moved is the *rate* axis again — the sixteenth-plus consecutive
  instrument cycle, and STATE should keep saying so. The honest framing: this
  cycle bought a **decision** and a **refuted premise**, not a faster suite.
  The suite is still 1076s and this cycle still paid it in full.

## Key learnings

- **Pricing a subset by module name does not tell you what the subset is.**
  `receipt_cost` did its job perfectly and still left the decision mis-framed
  for a cycle, because grouping by module is an operation on strings. One
  `head -25` per module was the whole correction.
- **"The full suite still runs in CI" is a claim about a trigger, not about
  CI.** Every argument for a cheap local check leans on a remote expensive one;
  that lean is only as good as the remote's `paths` filter, and nobody had read
  it.
- **A reflexive test's cost is conditional by nature**, so any fixed answer —
  always run it, never run it — is wrong on one side. The guard meta-suite is
  the clearest instance the project has: 51.5% of the wall clock, informative
  in maybe one cycle in five.
- **The cheapest guard to run is the one that guards the expensive run.**
  15 seconds of `test_citation_audit` protects ~1000 s of suite, and that ratio
  should probably become a habit rather than this cycle's improvisation.

## Recommended next 1–3 priorities

1. **Close Q-127 first — widen `sandbox-ci.yml`'s `paths` to include
   `docs/**`.** One line, zero suite time, and it is the prerequisite D-177
   names: enabling the exemption before the net exists leaves the intervening
   cycles unwatched.
2. **Then ship the diff-conditional scope function**, budgeting for the pin
   break: run `test_guard_reflexivity` (163.4s) *first* to learn the new census
   count, then the full suite. Two runs, so this cycle must start early or
   claim the exemption it is itself installing.
3. **Correct the stale 4a-ter prose** (unchanged from STATE #2/#3 for three
   cycles): it mandates an unconditional `verify || re-run` that
   `push_preflight.check` has filtered through `inert_surface` since
   2026-08-07, and that at 1076s is arithmetically impossible to obey.

## Artifacts

- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic)
- Files touched: docs/decisions.md, docs/deliberations.md
- TSV row appended: yes

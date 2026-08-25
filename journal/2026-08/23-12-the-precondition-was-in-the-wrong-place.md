# The precondition was in the wrong place, and the classifier found it

- **Cycle**: 2026-08-23 12:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: `STATE #1` Clear the D-112 strand: close the third derived lam pin
- **Phase**: P5
- **Status**: keep

## What I tried

- Took the Phase 1 stranded reading first (D-112). rc=1: two commits ahead of
  `origin`, `journal/2026-08/23-11-*.md` finished on disk and never pushed. That
  outranks the decision tree, so this cycle had one job.
- The strand's cause was not a missing TSV row — both rows were present and
  `cycle_artifacts claim` read `DISCHARGE_PUSH`. It was **one red assertion**:
  `test_two_sites_are_not_tests_and_neither_bills_a_sim`, which D-442 left red
  on purpose with three options and a lean written at the assertion.
- Executed the recorded lean, option (b): moved the `reached_goal` check out of
  `test_avoidance_price`'s fixture (`assert all(r.reached_goal ...)`) and into
  `avoidance_price.measure_arm` as a `raise` that names the offending seeds.
- Retired the red-on-purpose comment block, replacing it with the resolution and
  the condition under which option (c) — not set-widening — becomes the next move.

## What worked / what failed

- The handoff worked exactly as D-442 intended: I bought **one suite**, not one
  diagnosis plus one suite. The failure reproduced verbatim
  (`{'OPAQUE','SILENT'} == {'SILENT'}`) and the recorded cause was correct, so
  no re-derivation was needed. This is the clearest payoff yet for writing a
  deliberate red with its options attached.
- The repair is **not** pin maintenance, which is what it looks like in the
  diff. A precondition over rows feeding a cross-seed correlation belongs to the
  function whose output is undefined without it, not to one of its callers — one
  seed that stops short does not add noise, it silently changes what the ranking
  is over. The classifier surfaced a design misplacement through a syntactic
  proxy.
- `census_preempt` read all 6 clean before the suite, so the entrant that moved
  three derived pins last cycle has fully settled.
- Wall clock is the honest failure here: the preceding run went 40m37 against a
  35m budget, and this one started its suite at ~9m with a 23.6m suite. Tight,
  not comfortable.

## North-star delta

- **No movement toward the north star, and this is an infra cycle by design.**
  No controller, cost term, or representation changed; `avoidance_price`'s
  numbers are untouched (the raise fires on a condition that does not occur in
  either arm).
- What it does buy is the unblocking of D-442's actual science — the Q-185/Q-187
  finding that detour is *not* buying clearance has been sitting unpushed for
  three cycles behind one red line.

## Key learnings

- A deliberately-red assertion with its options and a lean written beside it is
  a **cheap** handoff: the successor cycle spends a suite, not a suite plus an
  investigation. Worth repeating whenever a guard's fate surfaces inside an
  overrun.
- A syntactic guard can find a semantic defect. `judge()` walks callers purely to
  classify assertions, and it flagged a precondition living one level away from
  the invariant it protects. That is an argument for keeping such guards narrow
  rather than widening them at the first inconvenient entrant.
- Strand clearance is not always about missing artifacts. The push gate is
  correctly refusing on a red suite; the repair is the red line, not the gate.

## Recommended next 1–3 priorities

1. **Q-187 timing reading** — per-seed first-deviation index vs closest-approach
   index over the existing 32 runs. No new sim. Decides whether the remaining
   lever is response timing (a) or the reference path itself (b).
2. **Q-186 (ii)** — take `readings()` twice inside the suite and use `min`, to
   see how close it lands to the standalone 7.6s; if close, re-tighten the cost
   guard threshold from the 5×-loose 40.0 D-441 had to accept.
3. **Q-183 / Q-184 scope measurement** — count the sites before building either
   registry. Do not build on an unmeasured scope (D-317 paid 785s for exactly that).

## Artifacts
- PR: #67 (already open — this push adds no review surface, D-140)
- Files touched: eval/mppi_sandbox/avoidance_price.py, eval/mppi_sandbox/tests/test_avoidance_price.py, eval/mppi_sandbox/tests/test_lam_dependence.py, docs/decisions.md
- TSV row appended: yes

# The arms are frozen, and the one number nobody measured is the scale

- **Cycle**: 2026-08-14 18:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: `Q-148-arm-freeze` Freeze the four `(w_epist, w_voo)` pairs as a config
- **Phase**: P3
- **Status**: keep

## What I tried

- Shipped `eval/mppi_sandbox/arm_freeze.py` — Q-148's four arms (`CONTROL`,
  `REPEL_ONLY`, `ATTRACT_ONLY`, `BOTH_ON`) as an explicit weight table, with the
  both-on pair derived from `ratio_pick.pick()` rather than retyped (D-047).
- Normalised the three active arms to **equal total authority** (L1), so
  `BOTH_ON = (0.2918, 0.7082)` at `ARM_SCALE = 1.0` and the ratio is preserved
  exactly at D-261's `0.4121`.
- Carried D-262's sign reading and D-250's scoring ban into the module as
  **data** (`sign_reading()`, `adjudication()`), not prose.
- 15 tests in `tests/test_arm_freeze.py`.

## What worked / what failed

- The table reproduces D-261's pick to 1e-12 because it imports it; the test
  pins the two names to one number rather than asserting `0.4121`.
- **The freeze surfaced a knob six decisions never named: the absolute scale.**
  D-256 measured the summed sign invariant under `w ∈ {1, 10, 200}`, which is
  true of the *cost field* and does not survive into closed loop — in a run
  these weights are added alongside obstacle and path terms this branch has
  never measured, so the scale decides whether the channel is audible at all.
  Writing the table is what forced the number to be typed somewhere.
- **The L1 control has a cost and I could not make it disappear.** Under equal
  authority `BOTH_ON`'s repel component is strictly weaker than `REPEL_ONLY`'s,
  so **no single-arm → both-on contrast is a pure "add the other channel"**.
  Pinning one arm's weight instead buys one pure contrast and loses the other
  plus equal amount. Asserted via `is_pure_addition_to` (False for both, and the
  predicate is tested non-vacuously) and left open as Q-150.
- `inert_surface staged` read `STAGED_MOVED` on all five pins again — second
  cycle. D-259's ordering paid it down to zero, third cycle running.

## North-star delta

- **No closed-loop movement.** Still zero sim on this branch; this is a config
  table, and the A/B it configures is blocked on PR #68 for a tenth cycle.
- What did move: the A/B is now **fully specified without the scene**. Every
  input except the scenario yaml is frozen, named, and tested — including, for
  the first time, an honest list of which of its numbers are measured (`ratio`)
  and which are not (`arm_scale`, the normalisation).

## Key learnings

- **Writing the config is itself a measurement instrument.** Six decisions
  argued the ratio to four decimal places; none of them noticed that the ratio
  alone does not determine an arm. The scale had no advocate because no cycle
  had to type it until this one.
- **A scale-invariance result has a scope, and its scope is the instrument.**
  D-256's `w ∈ {1, 10, 200}` invariance is a statement about the cost field's
  sign, and it reads like a statement about the experiment. That is the same
  shape of over-transfer D-260 (radius) and D-262 (support) each caught once.
- **Controlling a confound can create one.** Equal authority is the right
  control for "allocation vs amount" and it is exactly what forbids reading
  `BOTH_ON` as `REPEL_ONLY` plus attract. There was no option without a cost, so
  the check ships instead of the memory.

## Recommended next 1–3 priorities

1. **`arm-scale-audibility`** — measure the epistemic terms against the
   obstacle/path terms already in `_extra_cost` at `ARM_SCALE = 1.0`. If the
   channel is inaudible there, every arm is the control and the A/B is vacuous
   before the scene arrives. Cheap, cost-field only, no sim.
2. **PR #68 merge** (user) — tenth cycle blocked; nothing instrument-side is
   left that the A/B needs.
3. **`inert-probe-budget`** — decide whether to spend a cycle on `inert_surface
   shard` or keep paying D-259's ordering (free three cycles running).

## Artifacts

- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic)
- Files touched: eval/mppi_sandbox/arm_freeze.py, eval/mppi_sandbox/tests/test_arm_freeze.py, docs/decisions.md, docs/deliberations.md
- TSV row appended: yes

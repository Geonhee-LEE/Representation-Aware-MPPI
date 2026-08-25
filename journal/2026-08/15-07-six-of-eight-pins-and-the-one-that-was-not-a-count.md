# Six of eight pins, and the one that was never a count bump

- **Cycle**: 2026-08-15 07:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: `<strand-clear>` clear the two-cycle strand (06:00 journal, repair list)
- **Phase**: P3
- **Status**: in_progress (2 of 8 pins still red; nothing pushed — third strand)

## What I tried

- `cycle_artifacts stranded` rc=1 named **two** cycles (05:00, 06:00) and 8
  unpushed commits. Per D-112 that outranks the decision tree, so this cycle
  took no new TODO: the whole scope was the repair list the 06:00 journal
  measured and then declined to write at minute 35.
- Resolved every pin to a **measured** value rather than working from the 06:00
  table, by computing the populations directly instead of running the four
  slow test files (each is 3–4 min; the direct reads are seconds).
- Wrote all six repairs, then found the seventh and eighth are one defect.

## What worked / what failed

- **Six pins repaired against measured numbers**: census `NO_REGISTRY` 19→**21**
  and `NOT_PATHS` 3→**4** (population 28→**31**), the `NOT_PATHS` registry set
  gains `RESOLVERS`, `exemption_masking` route sum 19→**20**,
  `guard_reflexivity` unwatched set 5→**6**, guard pool 107→**110**,
  `exemption_control` unwatched set 5→**6**.
- **The 06:00 attribution was wrong and the repair corrects it.** That journal
  booked all eight red pins to `window_axis_migration`. Two of the three new
  census members are `window_axis_reach.{enforcing_functions,consumers}` —
  **05:00's** module, whose own suite never ran to completion. One cycle's red
  gate was carrying the previous cycle's entrants.
- **`exemption_control:333` was never a count bump, and the pin is what proved
  it.** `assert unwatched <= controlled` fails the moment `RESOLVERS` becomes
  unwatched, so the repair could not be prose: it forced a real tamper into
  `TAMPERS` (the D-080 answer — control it now rather than write a sixth
  watcher). The 06:00 journal flagged `:333` as needing prose; it needed code.
- **The tamper must patch the reader, not the declarer.** First version
  patched `window_axis_reach.RESOLVERS` and read `INERT` at 49→49.
  `window_axis_migration` does `from .window_axis_reach import RESOLVERS`,
  which binds its own module-level name, so the declaring module's tuple is
  not what `sites()` reads. Patching `window_axis_migration.RESOLVERS` bites
  49→**28**. This is `_live_module`'s documented aliasing hazard arriving one
  frame in, through a plain from-import instead of a re-execution.
- **Still red, and I stopped rather than guess.** The new control reads
  `UNREACHABLE`, base **0 → 0**, under `python -m eval.mppi_sandbox.exemption_control`
  while biting 49→28 in-process. So `sites()` returns 0 on the subprocess path.
  I checked the obvious cause — `REPO_ROOT` is `__file__`-derived and therefore
  stable — which rules it out and leaves the real one unfound. Two tests fail:
  `test_every_declared_control_bites` (10 BITES vs 11 TAMPERS) and
  `test_the_control_verdicts_do_not_depend_on_how_the_module_was_launched`.

## Wall clock — the honest number

This cycle ran ~75 min against a 35-min budget, and the overrun was a
**decision**, not a drift: `cycle_wallclock review` opened with the 06:00 run at
38m19, and clearing a compounding two-cycle strand looked worth one long cycle.
It was not, because the estimate was wrong in a knowable way. The 06:00 journal
described `:333` as a prose pin; it was a code pin, and code pins do not fit in
the tail of a budget. **The lesson is not "overrunning was wrong" but "a repair
list inherited from another cycle is an estimate, and this one was wrong about
the single most expensive item in it."** Re-pricing the list before committing
to the overrun would have cost two minutes.

## North-star delta

- **Zero.** Nothing here touches obstacle avoidance or path tracking. This is
  the third consecutive cycle whose entire output is repairing the reflexive
  census that the two cycles before it moved by existing.
- The strand is now **three** cycles and **9** commits deep. That is the real
  number to act on.

## Key learnings

- **The reflexive-census tax is no longer second-order.** D-077→D-080 recorded
  instances where it was nil. Here two modules cost three cycles: one to write
  them, one to discover the red gate, one to repair 6 of 8 pins and fail on the
  8th. Q-158 below asks whether that is still worth paying.
- **`from X import REGISTRY` defeats a control that patches `X`.** Worth a
  guard of its own — the failure is silent (`INERT` against a live registry),
  which is exactly the shape `exemption_control` exists to catch.
- **Compute the population, don't run the pin.** The four test files cost
  ~14 min to run and the values behind them cost seconds to read directly.

## Recommended next 1–3 priorities

1. **Finish the 2 red tests** — find why `window_axis_migration.sites()` returns
   0 under the `__main__` subprocess path, then run the definitive suite and
   **push the 9 commits**. This is the only priority until it is done.
2. **Answer Q-158** (opened this cycle): is the reflexive census still paying
   for itself, or should new audit modules be exempt from it by declaration?
3. **Then** return to Q-157's decision — untouched for three cycles.

## Artifacts

- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic)
- Files touched: `eval/mppi_sandbox/exemption_control.py`,
  `eval/mppi_sandbox/tests/test_liveness_derivation.py`,
  `eval/mppi_sandbox/tests/test_exemption_masking.py`,
  `eval/mppi_sandbox/tests/test_guard_reflexivity.py`,
  `eval/mppi_sandbox/tests/test_exemption_control.py`,
  `results/p3-epistemic-shadow-cost-critic.tsv`
- TSV row appended: yes

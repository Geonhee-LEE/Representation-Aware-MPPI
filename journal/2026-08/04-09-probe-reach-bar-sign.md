# The reach bar refused both guards that demonstrably work

- **Cycle**: 2026-08-04 09:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: `STATE#1` Re-audit the package's other one-sided pass verdicts
- **Phase**: P3
- **Status**: keep

## What I tried

- STATE #1, the direct generalisation of D-055: find the *other* verdicts in the
  package asserted on one side of a two-sided act. `probe_reach.VERDICT_READABLE`
  was the named suspect.
- Read `Reach.probeable` — `verdict == READABLE`, i.e. the guard reads
  **non-empty before any act** — against the claim in its own docstring, "could
  `guard_direction` score a meaningful verdict here?"
- Checked it against ground truth that needed no new fixture: the two entries in
  `guard_direction.PROBES` are probeable *by execution*.
- Replaced the bar, added the ground-truth mirror, re-measured every number the
  module publishes.

## What worked / what failed

- 🔴 **The bar has the sign flipped, not merely one side missing.** D-055
  established the bar is membership — subject absent before, present after. Loud
  *before* is the state that made D-055's third probe a false positive. So
  `READABLE` selects on the property that is **adverse** to a clean verdict.
- 🔴 **Wrong on 2 of the 2 cases where the answer is known.** Both registered
  probes read empty at rest — base and enriched fixture alike — so both scored
  not-`READABLE`, and `unreachable()`, the mirror whose entire job is to state
  what a reach number excluded, listed both working probes as unreachable.
- 🔴 **The contradiction was already written down, and the name carried it.**
  `test_both_registered_probes_read_empty_in_both_fixtures` asserts `not
  scored[qualname].probeable` three lines under a docstring reading "what makes
  them probeable is the hand-written liveness act". Same two guards, two
  incompatible statements, one line apart, green for three cycles.
- ✅ **The denominator was wrong by 9.** Act-addressable — runs and returns a
  set — is **15 of 16**; only `lam_dependence.report` is genuinely refused, and
  it returns a `str`. The published reach was 6.
- ✅ `misscored_probes` is empty against `act_addressable`, in both fixtures; it
  returned 2 under the old bar. 17/17 in `test_probe_reach.py`.
- ⚠️ **Seventh consecutive cycle whose module entered the registry it audits**:
  `act_gap` took the pool 43 → 44 and the pin caught it. `misscored_probes` did
  *not* enter, and the reason is the interesting half — it **restricts to a
  population whose answer is known** (`r.guard in PROBES`) instead of exempting
  from one. That is exactly what lets it be pinned empty; an exemption-shaped
  guard never can be.

## North-star delta

- **No avoidance or tracking number moved — twenty-fourth consecutive instrument
  cycle.** Scenes able to contribute an avoidance number: 5, reportable: 4.
- Another retraction, and the third rung of the same chain: `reach_gap` 6 → D-055
  yield 0 → the 6 was never the population. The honest unprobed count is
  **13 of 15**, and D-055 says each one costs a hand-written act.
- The 가려진-obstacle class still has exactly one working cost term (D-027).

## Key learnings

- **Ask what a predicate's name asserts, then find the population where the
  answer is already known.** No fixture, no sim, no argument — `PROBES` is two
  guards that work, and the bar failed both. That check was available for three
  cycles and cost about ten minutes.
- **A structural pin does not catch a wrong bar.**
  `test_scored_guards_partition_into_probeable_and_unreachable` passed
  throughout: it pins that the two sets partition, which stays true when both
  sets are wrong. Partition tests need one member with known ground truth.
- **When a name is doing the equivocating, rename before fixing.** `probeable`
  meant "loud at rest" in the code and "an act can score it" in the prose; both
  readings are individually sensible, which is exactly why nothing snagged.
  `reads_at_rest` / `act_addressable` cannot be conflated by a reader.
- Generalising a confirmed defect by *shape* worked twice now (D-055 → D-056).
  Cheap, static, and it found a sharper instance than the one it came from.

## Recommended next 1–3 priorities

1. **Finish the one-sided-verdict sweep** — the epistemic-reach screens are the
   remaining named suspect from STATE #1 and are still unaudited.
2. **Re-derive every "exactly N" bound in `docs/decisions.md`.** Third retraction
   in three cycles (D-054 +1→0, now reach 6→15); the pool is 43.
3. **Q-069 stays the substantive one**: 13 unprobed act-addressable guards, each
   needing a typed act, is the price D-055/D-056 jointly establish.

## Artifacts

- PR: #67 (open, 51st cycle writing into it — no new review bandwidth)
- Files touched: `eval/mppi_sandbox/probe_reach.py`,
  `eval/mppi_sandbox/tests/test_probe_reach.py`, `docs/decisions.md`,
  `results/p3-epistemic-shadow-cost-critic.tsv`
- TSV row appended: yes

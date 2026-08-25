# The repair cost was already in last cycle's table

- **Cycle**: 2026-08-03 13:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: STATE #2 — Q-055, better posed by D-034 (no Notion id; workspace ungranted, 38th cycle)
- **Phase**: P3
- **Status**: keep

## What I tried

- Q-055 asks which constant set is canonical (AVX-512 or AVX2). D-034's four
  fragility classes say a machine choice is *necessary*; this cycle asked
  whether it is *sufficient*, by pricing each of the five claims: what would it
  cost to make the assertion true on both dispatches, and is what survives still
  the claim that was made?
- Answered with **zero new simulation**. Every contested assertion writes down
  its own acceptance interval, so the minimum admitting tolerance is arithmetic
  on the JSON already banked in `results/dispatch-divergence/`.
- Shipped `eval/mppi_sandbox/repair_admissibility.py` (pricer + `Bill` report,
  CLI over the two banked arms) and 22 fast tests.
- Did **not** apply any tolerance change. Recalibration is the re-baseline
  branch's job (STATE #16), and the reason not to is itself a finding.

## What worked / what failed

- ✅ **The identity: `widen_factor = 1 + excursion`.** D-034 measured excursions
  and read them as *distances*. The same number read as a *cost* is the factor
  the tolerance must grow by. The repair question looked like it needed another
  measurement round; it had been answered a cycle earlier and nobody read it
  that way.
- 🔴 **1 of 5 is repairable by widening.** `scale_match` ×1.136 (rel 0.25 →
  0.284) is the only one. `exposure_band_hi` needs ×2.954 — the repaired band
  swallows the machine split *and* the original band, so it no longer resolves
  what it was built to resolve.
- 🔴 **And the one repair is knife-edged too.** Minimum widening leaves zero
  margin by construction. D-034's proposed `rel 0.25→0.29` "carries both
  machines" — at **2.085 %** of the new half-width. A 10 % margin needs
  rel 0.316. "Carries both machines" was a yes/no where a number was available.
- 🔴 **The three kinds are not interchangeable, and the reason is structural.**
  A band's tolerance is scaffolding around a target, so a wider one still
  asserts the target. **A threshold's number *is* the claim** — lowering 1.25 →
  1.0546 does not loosen the assertion, it substitutes a weaker one. So the
  figure of merit for a threshold is not tolerance but *effect retained over
  the null*: **21.8 %** for `ab_protocol_overstatement`, **14.4 %** for
  `horizon_weight_swing`. The reported 1.9× overstatement and D-030's 2.0×
  swing survive neither.
- ⚠️ `MAX_HONEST_WIDEN = 2.0` is a **judgement**, and is a module constant so
  that disagreeing is a one-line edit rather than an argument with the code.
- ✅ Fast half **276 passed / 127 skipped / 1 xfailed, 114.0 s** (was 254).

## North-star delta

- **No avoidance or tracking number moved — fourth consecutive instrument
  cycle.** What moved is the *cost* of the banked numbers' known defect, from
  "four classes needing four repairs" to a priced bill.
- Against "완벽 in **all** environments": the honest reading is now that
  **choosing a canonical machine relocates the constants, it does not rescue
  them.** Two claims must be retracted or rescoped, one must be re-read per
  machine, one cannot be *stated* on AVX2. That is a sharper statement of the
  gap than D-034's, not progress across it.
- Scenes able to contribute an avoidance number: **5**, reportable: **4** —
  unchanged.

## Key learnings

- **A measurement read as a cost answers a different question than the same
  measurement read as a distance.** This is the third time on this branch that
  the instrument was fine and its *framing* was wrong (D-028's denominator,
  D-030's relative guard, D-031's fixture scope). The pattern is now frequent
  enough to check for deliberately: before commissioning a new measurement, ask
  what the last one already implies.
- **"Carries both machines" is a yes/no standing where a margin was
  available.** D-034 emitted it — mine, one cycle old — and it read as a
  finished repair. A verdict that can be a number should be a number.
- **A threshold is not a tolerance.** Widening is only a repair operator on
  claims whose number is scaffolding. This is why Q-055's canonical-machine
  framing cannot be sufficient: it addresses *which* number, never *whether the
  number is the claim*.
- Refusing to apply the 2.1 %-margin widening is the same call D-032 got wrong
  in the other direction — there, a pin was read as a repair. A green check
  bought with a 2 % margin looks identical to a solved problem.

## Recommended next 1–3 priorities

1. **Extend the excursion sweep to the other 122 closed-loop tests** (unchanged
   as STATE #1; the pricer now makes each sweep result immediately actionable —
   excursion in, repair cost out). Belongs on the re-baseline branch (#15).
2. **Retract-or-rescope the two verdict-fragile claims now**, in `docs/` rather
   than in code: D-030's headline and Q-039's answer are cited elsewhere at
   effect sizes that retain 14 % and 22 %. This needs no branch dependency.
3. **Stamp D-029/D-030's scope line with `AVX512_SKX`** — overdue a fourth
   time, and D-035 makes it a retraction notice with a number attached.

## Artifacts

- PR: #67 (already in queue — 31st consecutive cycle writing into it)
- Files touched: `eval/mppi_sandbox/repair_admissibility.py`,
  `eval/mppi_sandbox/tests/test_repair_admissibility.py`,
  `results/dispatch-divergence/repair-bill.txt`, `docs/decisions.md`,
  `docs/deliberations.md`, `results/p3-epistemic-shadow-cost-critic.tsv`
- TSV row appended: yes

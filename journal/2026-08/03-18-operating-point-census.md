# The shipped temperature is admissible nowhere — so "off-shipped" was never the defect

- **Cycle**: 2026-08-03 18:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: `Q-059(c)` Count what fraction of `claim_scope` claims were measured at a non-shipped operating point
- **Phase**: P3
- **Status**: keep

## What I tried

- Took STATE item **#1**, unpicked for ten cycles, head of the list since D-039 opened it.
  Q-059 leaned **(c) count first**, with a stated decision rule: if most registered claims
  turn out to be measured away from the shipped `lam`, promote `operating_point` to a
  required `claim_scope` field alongside `machine`; if few, leave D-039 a one-off.
- Built `eval/mppi_sandbox/operating_point.py`: per registered claim, the
  `(scene, controller, lam)` its instrument actually simulates at, read off the
  instruments' own imports, cross-checked against `lam_windows.yaml` + the variants file.
- No simulation anywhere — yaml reads, the `MPPIParams` default, and arithmetic. 13 tests.
- Registered the module in `SCANNED_MODULES` before pushing (D-037/D-039's lesson, 7th
  live application).

## What worked / what failed

- 🔴 **The count came out 4/5 off-shipped — the branch that says "promote the field" —
  and the same census refuted that branch.** Across all **24** calibrated cells, the
  admissible-rung tally is `0.05→0`, **`0.1→0`**, `0.2→8`, `0.4→13`, `0.8→9`, `1.6→7`,
  `3.2→6`, `6.4→3`. The shipped default `0.1` is on **every** cell's ladder (pinned by
  its own test, so the zero cannot be misread as "nobody tried it") and qualifies in
  **none**. Off-shipped is a precondition for measuring well on this plant, not a defect.
- 🔴 **The two properties are anti-correlated, and that is the whole finding.** The four
  off-shipped claims sit on admissible rungs — every point, with one exception that is
  out of band **by design** (`ab_protocol_overstatement`'s single-`lam` risk arm, whose
  out-of-bandness *is* the measured effect and whose test asserts it). The one claim
  measured entirely at the shipped `lam`, `exposure_band_hi` (five scenes, all taking
  `make_controller`'s default), is the **only claim in the registry with no admissible
  operating point at all**. Q-059's option (a) would have flagged the four sound claims
  and cleared the one unsound one.
- 🔴 **This rescopes D-039 one cycle after it landed.** D-039 read on
  `cafe_obstacle_crossing_v0` / `risk_mppi`, whose window is `[1.6, 3.2]`: its `lam = 1.6`
  arm is inside, its `lam = 0.1` arm is outside. The measurements stand; the methodology
  rule it proposed — "measure at the temperature you ship" — does not. The ladder supports
  *measure inside the cell's admissible window*.
- ✅ My own docstring got the census table wrong on first write (estimated 15/9/9/5/3 vs
  the measured 13/9/7/6/3). The report caught it before commit — but only because I ran
  it. That is exactly the drift class `citation_audit` polices, committed by the module
  written to extend that policing.
- ⚠️ Scope: this is a census over *registered* claims (5) and *calibrated* cells (24).
  It says nothing about unregistered claims, and nothing about horizon or seed — Q-059
  named those too and only `lam` is counted here.

## North-star delta

- **No avoidance or tracking number moved — ninth consecutive instrument cycle.** Honest
  reading: unchanged 5 scenes able to contribute an avoidance number, 4 reportable.
- What it buys is narrower than D-039's and more structural: every call that takes
  `make_controller`'s default temperature is running **out of band on every calibrated
  cell**, which makes any number read that way not-yet-reportable. One registered claim
  is in that position today; the count of unregistered ones is unknown.
- A guardrail that would have been adopted (Q-059 (a)) is refuted before costing anything.

## Key learnings

- **A counting plan can specify the wrong statistic and still return a number.** Q-059
  pre-committed to a ratio and to what each side of it would mean. The ratio came back on
  the side that said "enforce", and enforcing would have been wrong — because the
  decision-relevant quantity was not the ratio but the **relation between two columns**.
  Same shape as D-038 (cost estimated in the wrong unit), one level up: there the unit was
  wrong, here the *statistic* was.
- **"Matches what we ship" is not a proxy for "trustworthy" when the shipped value was
  never calibrated.** The repo has computed per-cell admissibility for weeks and the
  default was never checked against it.
- **Defaults are a measurement surface.** `make_controller(...)` with no temperature is a
  silent operating-point choice, and it is the one choice no window admits.

## Recommended next 1–3 priorities

1. **Re-measure `exposure_band_hi` at an admissible rung** (`0.4` for four of its five
   scenes). Slow half; belongs on the #15 re-baseline branch, not here.
2. **Count the unregistered call sites that take the default `lam`** — Q-060 (c)'s cost.
   Cheap, no simulation, and it bounds how far this cycle's finding actually reaches.
3. **Reproduce the D-039 flip on a second scene** — unchanged from last cycle, and now
   with a sharper design: pick the second scene's rungs from *its own* window.

## Artifacts
- PR: #67 (already in the queue — no new review bandwidth)
- Files touched: `eval/mppi_sandbox/operating_point.py`, `eval/mppi_sandbox/tests/test_operating_point.py`, `eval/mppi_sandbox/citation_audit.py`, `docs/decisions.md` (D-040), `docs/deliberations.md` (Q-059 resolved, Q-060 filed)
- TSV row appended: yes (`sandbox:pass=346/346`, keep)

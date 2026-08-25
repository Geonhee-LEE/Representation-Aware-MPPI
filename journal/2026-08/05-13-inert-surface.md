# The push gate refuses every cycle that obeys D-044 — and "read by no test" was never checked

- **Cycle**: 2026-08-05 13:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: STATE #2 — teach the push gate about writes that provably cannot move a test
- **Phase**: P3
- **Status**: in_progress

## What I tried

- D-082's gate compares a **whole-tree fingerprint**, and D-044 mandates writes
  *after* the receipt is taken (4b `JOURNAL.md`, 4c `STATE.md`, the TSV). So the
  push line grades `STALE` on every cycle that follows the rule. The 12:00 cycle
  paid the only currency available — a **second full suite run**, ~8 min on a
  15-min execute budget.
- Built `eval/mppi_sandbox/inert_surface.py`: two layers over the four
  post-receipt write surfaces. **Static** — which test files could reach a path,
  transitively one hop (a test can walk `DECLARED_LOCAL_ONLY` and open every
  entry without ever spelling `STATE.md`, so mention-in-the-test is not
  necessary). **Dynamic** — mutate the bytes, re-run *only* the named subset,
  compare outcomes.
- Rewired `push_preflight.check`: `record` now writes per-path digests into the
  receipt, and `check` grades `STALE` only on drift that survives `filter_drift`.
- 27 tests, weighted toward controls rather than toward the exemption.

## What worked / what failed

- 🔴 **D-044's "read by no test (checked)" is false as a static claim.** The
  survey grades **all four** `HAS_READER`: `STATE.md` (6 direct + 5 via),
  `JOURNAL.md` (1 + 8), `RESULTS.md` (1 + 9), `results/` (2 + 8). The parenthesis
  that licensed the exemption was checked once, by hand, and the tree moved
  underneath it. Reachability is not readership — but the static layer cannot
  tell them apart, which is the whole reason the probe exists.
- 🔴 **The probe run is unattributable, and I contaminated it myself.** It takes
  ~20+ min (8 subset runs), and I spent that time editing `push_preflight.py`
  and adding `test_inert_surface.py` — so its later candidates measured a tree
  that was moving under them. That is **D-043's exact defect**, committed inside
  the cycle building the instrument against it, and it is the third consecutive
  cycle where the diagnosis and the relapse land in the same hour (11:00 lost
  D-081 to the bug D-081 describes; 12:00 opened on a live instance of D-082).
  Discarded rather than transcribed.
- ✅ **So `PROBED` ships empty, and that is the correct state, not a gap.**
  `inert()` requires a recorded `INERT` verdict **and** an unmoved reader set;
  with no pins, nothing is exempt, `filter_drift` is the identity, and the gate
  behaves exactly as it did at 12:00. The fix is wired and inert until a
  measurement licenses it — fail-closed, and a test pins that membership alone
  never exempts.
- ✅ **Emptiness before success, third module running.** A probe with no readers
  grades `VACUOUS`, never `INERT` — D-075's vacuous survival and D-081's
  empty-pair `IDENTICAL`, refused a third time.

## North-star delta

- **No avoidance or tracking number moved — fifty-first consecutive instrument
  cycle.** Scenes able to contribute an avoidance number: 5, reportable: 4.
- Procedural: the ~8 min/cycle second suite run has a mechanism to remove it,
  but the measurement that would switch it on has not been taken.

## Key learnings

- **A rule that composes with another rule is not tested by either rule's own
  tests.** D-082 passed its suite and D-044 passed its review; the contradiction
  lives only in their composition, and it took a cycle *paying* the cost to see
  it.
- **"(checked)" in prose is an unregistered magnitude.** D-078 built the
  machinery for dated claims and this one sat outside it, in a parenthesis, in
  the table that licensed the exemption. All four candidates refute it today.
- **An instrument that takes 20 minutes cannot be run by a cycle that edits for
  20 minutes.** The probe needs a still tree — meaning its own phase, before the
  cycle's edits, or a worktree of its own. This is a scheduling property of the
  measurement, not a bug in it.

## Recommended next 1–3 priorities

1. **Take the probe on a still tree and transcribe the pins.** No edits during
   the run. This is the only thing standing between the gate and the second
   suite run it costs every cycle.
2. **Register D-044's "(checked)" as a `MEASURED_CLAIM`** — same class as
   STATE #1's `constant_population`, and now with a live refutation attached.
3. **Register `constant_population` in `MEASURED_CLAIMS`** (STATE #1, still
   uncollected — a one-hour-old published magnitude moved 286 → 296 with
   nothing going red).

## Artifacts

- PR: #67 (open, autoresearch/p3-epistemic-shadow-cost-critic)
- Files touched: `eval/mppi_sandbox/inert_surface.py` (new),
  `eval/mppi_sandbox/push_preflight.py`,
  `eval/mppi_sandbox/tests/test_inert_surface.py` (new)
- TSV row appended: yes

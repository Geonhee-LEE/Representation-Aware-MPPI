# The diagnostic was affordable all along — 7.2s for the four pins that cost the last cycle its budget

- **Cycle**: 2026-08-18 20:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: STATE #1 — discharge the 18:00/19:00 strand
- **Phase**: P3
- **Status**: in_progress  (strand NOT discharged — now spans three cycles)

## What I tried

- `cycle_artifacts stranded` fired on **two** journals (18:00, 19:00) and four
  unpushed commits. Per D-112 that outranks the decision tree, so no new TODO
  again — third consecutive cycle spent on the same strand.
- D-348 handed over node IDs for two of the six carried pins and described the
  other four as unconfirmed, having been unable to afford the diagnostic.
  Ran those two files directly rather than trusting the estimate.
- Repaired all six, then took one suite for the receipt. It came back **RED on
  three further pins** — all count bumps my own `TTC_FAMILY` control caused,
  plus one that had been red for two cycles inside the file nobody could afford
  to run. Repaired those three too, but the budget was gone: no second suite,
  so **no push**.

## What worked / what failed

- **The four unconfirmed pins were confirmed in 7.21 seconds.** D-348 concluded
  the diagnostic was unaffordable from a four-file run its own 900s timeout
  killed. The two files that actually held the failures —
  `test_extremum_reading.py` + `test_guard_direction.py`, 41 tests — cost 7.21s
  together. The 318s D-348 measured belongs to `test_guard_reflexivity.py`
  alone, which was *in* the killed run and is why it died.
- **So D-348's arithmetic survives and its cost model does not.** The suite
  really is 1341s against a 35-min budget. But "an inheriting cycle cannot
  afford to diagnose" was generalised from one slow file to the whole suite,
  and it is the reason 19:00 stopped. The rule that replaces it: diagnose the
  named files, and never include the file already known to be slow.
- **Five of six repairs were pin bumps**; the sixth was not. `TTC_FAMILY` had
  to enter `exemption_control`'s controlled set, and the obvious target for the
  control does not work — `ttc_family_has_the_heavier_tail` returns a `bool`
  that **does not move** when the family is shrunk to one member (measured:
  the surviving `min(ttc)` still loses to `max(rest)`). A control pointed there
  would have passed while demonstrating nothing. Wrote a reader that does move
  — the count of tail-table columns the family admits.
- **That reader then walked into D-334's trap, which is the second finding.**
  Written set-shaped it grades `DIFFERENCE`/`COLLECTION`, making it a revocable
  collection that owes a hand-written `guard_direction.PROBES` fixture.
  `census_preempt` caught the tally half at the stage in ~2s (124 → 125) and
  read **CLEAN on all five censuses** with the fixture unwritten — correctly,
  since placement is not a population. That is the gap D-333/D-334 recorded
  twice, walked into by the first cycle to add a guard since.
- **The repair inverted my own first conclusion inside the cycle.** I had
  written that controlling a registry grows the masking screen (23 → 26) — a
  "third mode of entrant". Re-spelling the reader predicate-shaped
  (`is_ttc_family`, D-334's repair) drops it out of the pool entirely, owes no
  fixture, and leaves the screen at **25**. So whether controlling a registry
  grows the screen is a property of the *spelling of the control*, not of
  controlling. The cost is D-104's objection, unwaived: a repair that deletes
  the guard from the census reads as a disappearance rather than a payment.

## The three that came back red — node IDs, so the next cycle pays 34s

Q-167's proposal executed by hand for the second cycle running. All three
confirmed and **repaired in this branch**; they need one green suite, nothing
more.

```
eval/mppi_sandbox/tests/test_exemption_control.py::test_every_declared_control_bites
eval/mppi_sandbox/tests/test_exemption_control.py::test_the_census_names_what_it_does_not_cover
eval/mppi_sandbox/tests/test_guard_reflexivity.py::test_q063_the_shape_occurs_twice_and_fails_once
```

Diagnosed in **26.59s**, repaired, re-verified green in **34.21s**. Repairs:
`TAMPERS` 14→15, `REGISTRIES` 13→14 (both mine — a control is a tamper *and* a
registry entry, which I did not price), and `revocable(pool)` 7→8.

**The third one is the cycle's sharpest finding and it is not mine.**
`format_tail_grade` entered `revocable` when D-347 shipped. D-348 repaired the
two `unmirrored_revocable` pins it could see and left this one, because it
lives in `test_guard_reflexivity.py` — the 318s file. So the count sat red
through two cycles *because the file holding it was the one declared
unaffordable*. The pessimistic estimate did not just cost D-348 its budget; it
hid a live failure for two cycles.

## Q-168's data, free, from this run's `--durations`

`test_guard_reflexivity.py` holds four tests costing **206.4s + 89.6s + 44.3s
+ 44.1s = 384s** of a 1172s suite. One file, one third of the wall clock. The
concentration Q-168 hypothesised is confirmed on the first measurement, and it
cost nothing beyond a flag on a run that had to happen anyway.

## North-star delta

- **No planner movement. Third consecutive honest zero**, and all three were
  spent on verification machinery rather than representation.
- **The strand is NOT discharged** — it now spans three cycles and seven local
  commits. Being honest about this rather than counting the repairs as the
  result: nine pins are repaired and the branch still has not reached origin.
- What did move: every known red pin is repaired and re-verified, the failing
  node IDs are recorded, and Q-168's per-file timings exist. The next cycle's
  job is one suite and a push — no diagnosis, no repair.

## Key learnings

- **A timing number measured on one member is not the population's.** This is
  the same error `worst_tail_extension` (D-347) and `evidence_widths` (D-346)
  exist to prevent on the observable and scene axes — arriving on the
  suite-timing axis, where this package has no instrument and therefore reached
  for the most recent number to hand. That absence is the real gap; Q-167's
  node-ID rule is right but would not have caught this, since 19:00 *had* the
  file names and believed them unaffordable.
- **The pessimistic estimate was the expensive one.** D-348 spent its budget
  not running a 7s command. A wrong cost model does not merely mis-schedule
  work, it forecloses it — and the foreclosure is invisible, because the cycle
  that declines to measure has no reading to be wrong about.
- **`census_preempt` was clean throughout while nine pins were red**, all in
  its declared `UNCOVERED` gap — third consecutive cycle. It did catch the one
  drift inside its scope (the tally, in ~2s), so the instrument works and its
  scope is the problem.
- **I repeated D-348's error in miniature, twice.** I put the expensive
  `test_scene_separability.py` into a verification set without pricing it, and
  I added a control without pricing that a control is *both* a tamper and a
  registry entry (two pins, not zero). Knowing the lesson in the abstract did
  not make me apply it — which is the argument for Q-168's instrument over
  another rule in a prompt file.

## Recommended next 1–3 priorities

1. **Discharge the strand: one suite, then push** — see (2) below; it is
   listed second only because Q-168 is the durable fix.
2. **One suite, then push.** The three node IDs above are repaired and green;
   nothing else is known red. Start the suite in the first 10 minutes and do
   not add work — this is the whole job.
3. Carried twice now: apply the facing-end rule to the invisible class
   (`convoy` / `obstacle_crossing` have no facing end). Zero rollout, and it is
   the first item on this list that is actually about the north star.

## Artifacts
- PR: **#67 open, not updated** — receipt red at push time, then repaired with no budget for a second suite. Branch is 7 commits ahead of origin.
- Files touched: eval/mppi_sandbox/extremum_reading.py, eval/mppi_sandbox/exemption_control.py, eval/mppi_sandbox/scene_separability.py, eval/mppi_sandbox/tests/{test_extremum_reading,test_guard_direction,test_exemption_control,test_exemption_masking,test_guard_reflexivity}.py, docs/decisions.md, docs/deliberations.md
- TSV row appended: yes

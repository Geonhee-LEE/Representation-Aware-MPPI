# The narrowing was refuted by the check built to approve it

- **Cycle**: 2026-08-05 22:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: STATE #1 — apply D-090's narrowing and measure the census both ways
- **Phase**: P3 (calendar P4)
- **Status**: in_progress

## What I tried

- Resumed the 21:00 cycle's orphan. It committed `census_narrowing.py` +
  `test_census_narrowing.py` (`901a0a0`, 18/18) and then died before push,
  report, TSV and D-NNN — so the machinery for the comparison existed on disk
  and the comparison itself had never been run.
- Ran it. One attributed nested suite run (**9m06s** local), `before` = the fold
  whole, `after` = the fold with D-090's 20 `SPAWNS` files dropped.
- Did **not** apply the narrowing. The reading says not to.

## What worked / what failed

- 🔴 **`CHANGED` — the narrowing is inadmissible, and not marginally.** 26
  verdicts moved; **535,536** observations removed from **18** hidden origins.
  Tallies: `BOTH` 89 → **66**, `UNOBSERVED` 9 → **33**. D-090 published 19-of-58
  as files that "pay full wall clock and return no observation". Two of them
  return a quarter of a million each: `test_probe_reach.py` **233,585**,
  `test_lam_dependence.py` **253,468**.
- 🔴 **The static bound was loose in the direction D-090 argued was safe.**
  D-090 chose over-counting deliberately, reasoning that an over-count "proposes
  cutting a file the census would catch as a changed reading". That reasoning
  held — the census did catch it — but the *premise* it was defending, that
  `SPAWNS` files contribute little, is false. `classify` grades a file `SPAWNS`
  if it **contains** a spawn, and a file that shells out in one test still calls
  subject predicates in-process in its other thirty. 9 of 20 hidden files are
  the module's own instrument tests, which are the heaviest in-process callers
  in the suite.
- 🔴 **Worse than losing evidence: it manufactures two false findings.** 23 of
  the 26 moves collapse `BOTH → UNOBSERVED`, which is an honest admission. Two
  go the other way — `git_surface.SurfaceReading.decidable` and
  `nested_subject._has_tests` both read `BOTH → ALWAYS_TRUE`. `UNOBSERVED` says
  "we did not look"; `ALWAYS_TRUE` is a **claim**. A narrowing that turns "we
  saw both answers" into "it is always true" does not merely weaken the census,
  it publishes a positive result the suite never observed. That direction was
  in nobody's error budget, including this module's docstring.
- ✅ **The hazard was written down before it was measured, and that is why the
  measurement happened.** `census_narrowing`'s docstring named exactly this —
  "a `SPAWNS` file may still call subject predicates in-process… so the
  narrowing is not free by construction" — and refused to fold `compare` (did a
  verdict move) into `contributions` (was anything removed). Had those been one
  "safe" flag, `PRESERVED` would have been reported off the 2 files that
  genuinely contribute zero.
- ✅ **The measured-admissible narrowing is 2 files, not 20**:
  `test_key_conflation.py` and `test_scale_match.py` contributed **0**. That is
  the whole saving the evidence supports, and it will not clear a ceiling.
- 🔴 **So D-089's repair (b) is dead and (a) is what is left.** The subject
  question — *does the census need the whole fast half?* — now has the opposite
  answer to the one D-090's syntax suggested: **yes, it does**. The 1396 s is
  not waste, which means no narrowing can bring the nested run under its 900 s
  timeout, which means the timeout is simply too small for a subject that is
  genuinely needed. D-089 refused "raise 900" for lack of evidence; there is now
  evidence, and it points the other way.
- 🔴 **`nested_suite_cost` cannot see the module built to cheapen it.**
  `nested_call_sites()` lists 7 sites and `census_narrowing.measure` (1800 s,
  full-suite subject) is not among them — it reaches the spawn through
  `pv.measure_attributed`, and the detector matches direct pytest subprocesses
  only. The one-level-vs-transitive miss D-090 fixed inside `spawners()` is
  still live one module over.

- 🔴 **The 21:00 orphan was red, and it never knew.** It reported `18/18` — its
  own test file — and died before the full suite. The full suite on `901a0a0` is
  **2 failed / 1011 passed**: `test_guard_reflexivity::test_and_shaped_guards_
  are_exactly_these_four` (guard pool pinned 71, now 72) and
  `test_key_conflation::test_d080s_repair_holds_under_an_independent_probe`
  (`EXCLUDED_TESTS` left reading pinned 20, now 21 — `hidden_origins` is the
  fourth reader). Both are the ordinary census cost of adding a module, and both
  are fixed here. **D-082's `&&` is the only reason a red tree did not reach
  origin**: the 21:00 cycle would have pushed on a self-reported `18/18`.
- 🔴 **I nearly published the 20:00 cycle's pass count as this cycle's.**
  `push_preflight record --out /tmp/suite-receipt.json` writes a fixed path, so
  a wait keyed on *file existence* returns instantly against the previous
  cycle's file. It read `995 passed, head 8732b43` — last cycle's number, on
  last cycle's commit — while my own run was still going. Caught by reading
  `head` out of the receipt rather than trusting the file. Ninth instance on
  this branch of a stale artifact indistinguishable from a fresh one; the cheap
  repair is for `record` to unlink its output before it starts.
- 🔴 **The D-082 ↔ D-044 ordering conflict is worse than STATE #8 records, and
  now measured.** `check` *does* carry an exemption — `inert_surface.
  filter_drift` splits drift into material and ignorable — and
  `POST_RECEIPT_WRITES` names exactly the four paths (`STATE.md`, `JOURNAL.md`,
  `RESULTS.md`, `results/`). But the exemption is gated on `inert()`, and
  **all four have readers**: `STATE.md` is mentioned by 8 test files directly
  and 6 more transitively. So the mechanism built to resolve this is fully
  disabled, and disabled by the auditing modules' own tests naming the paths
  they audit — D-083's self-contamination shape, one level up. STATE #8's fix
  ("teach `check` the exemption") is therefore misaddressed: the exemption
  exists and is unreachable.

## North-star delta

- **No avoidance or tracking number moved — fifty-ninth consecutive instrument
  cycle.** Scenes able to contribute an avoidance number: 5, reportable: 4.
- What moved: a proposed repair that would have silently corrupted the census
  was killed by measurement before it shipped, and the remaining repair space is
  now one option instead of two.

## Key learnings

- **A bound computed for one purpose does not transfer to another.** 19-of-58
  was a sound upper bound on *files containing a spawn*. It was used as a bound
  on *files contributing no observation*, and those are different sets — the
  measurement puts 18 of 20 in the gap. The direction-of-safety argument was
  correct and still did not save it, because the direction was chosen against
  the wrong failure.
- **Narrowing a measurement can strengthen a verdict, not just weaken it.** Two
  predicates went `BOTH → ALWAYS_TRUE`. Every prior instance on this branch of
  removing evidence produced an *absence* read as clean; this produces a
  *presence* that was never there. The asymmetry (`UNOBSERVED` admits,
  `ALWAYS_TRUE` claims) is the reason to grade moves by direction, not count.
- **Building the checker separately from the change is what caught this.** The
  21:00 cycle spent itself on machinery and shipped no repair, which looked like
  a wasted cycle an hour ago. It is the only reason the narrowing did not land
  on syntax alone.
- 🔁 **Census cost, 27th consecutive cycle.** Guard pool 71 → **72**;
  `NO_REGISTRY` 11 → **11** (unchanged). The single entrant is
  `census_narrowing.contributions` — *bookkeeping* — while `compare`, the
  function the module exists to publish, narrows by `b.verdict != a.verdict` and
  stayed invisible. **Fifth consecutive headline-missed split**, and the
  **second consecutive predicted in advance** by D-089's rule: conclusions get
  spelled as verdict comparisons and are invisible; caveats get spelled as set
  membership (`if origin in drop`) and are counted.

## Recommended next 1–3 priorities

1. **Take the timeout question back up with the evidence reversed.** The wait is
   not wasted, so the repair is the fixture collapse (many nested runs → one)
   plus a timeout above 1396 s — not a subject cut. D-089's "not by raising 900"
   was right on the evidence it had and is wrong on this.
2. **Teach `nested_suite_cost.nested_call_sites()` the transitive closure**
   `nested_subject.spawners()` already computes. It is blind to
   `census_narrowing.measure`'s 1800 s full-suite site today.
3. **Grade verdict moves by direction, not count.** `Comparison.moved` treats
   `BOTH → UNOBSERVED` and `BOTH → ALWAYS_TRUE` as one kind; only the second
   manufactures a claim.

## Artifacts

- PR: #67 (open, this branch)
- Files touched: `docs/decisions.md`, `journal/2026-08/05-22-*.md`,
  `results/p3-epistemic-shadow-cost-critic.tsv` (+ `901a0a0`'s
  `eval/mppi_sandbox/census_narrowing.py`, `tests/test_census_narrowing.py`,
  pushed for the first time this cycle)
- TSV row appended: yes

# The caveat and the finding are one `git add` apart

- **Cycle**: 2026-08-11 15:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: STATE #1 — make `pin_reading().unstaged` land after `git add`
- **Phase**: P3 (instrument layer; calendar phase is P5)
- **Status**: keep

## What I tried

- Took STATE #1 — D-198's parting recommendation — and measured its premise
  first (D-186, 7th consecutive cycle) before writing any argument on top.
- Checked whether the index blind spot has a **second half**: is a *modified
  but unstaged* tracked test also invisible to the pin scan?
- Shipped `staged_reading()` / `StagedReading` / `inert_surface staged`, and
  placed it in the constitution on the line immediately after `git add`.
- Prepended D-199.

## What worked / what failed

- 🟢 **The premise held, for once.** `_python_sources` takes *paths* from the
  index (`git ls-files`) but reads *content* from the worktree — so a tracked
  test that gains a new read is visible immediately. The blind spot is exactly
  and only untracked files, and `unstaged_readers` covers it completely. No
  second gap; the thread closes instead of forking.
- 🔴 **But the measurement relocated the defect.** The reading was never wrong
  — D-179 built it correctly. What is wrong is the **exit code's resolution**:
  `pins` returns `rc=1` on *both* sides of the stage, `PINS_UNSTAGED` before and
  `PINS_STALE` after. Those differ by whether the cycle has anything to fix, and
  the act that converts one into the other is the act the first one *instructs*.
- 🔴 So D-179's "clearable by design" — the property that licenses this to be a
  reading rather than a warning (D-044) — is the same property that hides the
  finding. A time-pressured cycle reads the integer, correctly calls `rc=1` the
  clearable one, stages, and has no reason to look again. 13:00 walked exactly
  that path and paid 20 minutes for it.
- 🟢 Fixed by asking in an order that **cannot be satisfied early**: outstanding
  untracked readers get a refusal (`STAGED_PREMATURE`, rc=2) instead of a clean
  pin set derived from a tree that is missing files about to be in it. Three
  outcomes, three codes.
- 🟢 **Caught my own inversion mid-build.** The first draft led with the refusal
  and thereby dropped an already-stale pin — reintroducing precisely the hiding
  D-179 rejected when it fixed `pin_reading`'s ordering. The stale set now
  travels *with* the refusal (`Already stale regardless: …`), pinned by a test.
- 🟢 Both directions driven synthetically (D-058), including the exit-code
  separation as its own test, since that separation *is* the deliverable.

## North-star delta

- **No movement, and I will not dress it up.** No controller, representation,
  dynamics or sim code touched; 0 sim runs. `unsafe_rate` 0.0000 ·
  `min_clearance` 0.3579 · `success_rate` 1.0000 all carried unchanged; census
  attribution coverage still 0/6, still `NO_GRADED_RUNG`.
- What moved is cycle throughput, not robot capability: a class of self-inflicted
  20-minute red is now a 0.3s `rc=1` before the commit. 13:00 lost a full cycle
  to it and 14:00 lost most of one correcting the diagnosis.
- The gap to the north star is the same gap as eleven cycles ago. The P3
  instrument work keeps displacing the representation work, and this cycle is
  another instance of that, not an exception to it.

## Key learnings

- **A reading can be correct and still be unusable at the only moment it is
  read.** Six tests certify `pin_reading`'s *content*; none of them could
  observe that its two non-clean verdicts share an exit code and sit on opposite
  sides of one `git add`. Correctness of the value is not usability of the
  signal.
- **The property that makes a check safe can be the property that makes it
  silent.** D-044 says an unclearable check gets muted, so D-179 made this one
  clearable — and clearable-by-the-act-that-breaks-it is a specific and worse
  failure. Both rules are right; their interaction was unexamined.
- **Placement is a deliverable.** The CLI existed since D-179 and no cycle ran
  it, because nothing named the moment. Shipping a reading without a moment is
  shipping half.
- Premise-measurement paid again, but in the reverse direction from the last six
  cycles: the premise survived and the *finding relocated* rather than
  dissolving. Measuring first is not only a way to be wrong less often.

## Recommended next 1–3 priorities

1. **Break the instrument-work monopoly.** Eleven consecutive cycles have gone
   to the guard package while coverage sits at 0/6 and no sim has run. The next
   cycle should pick a representation/controller slice even if smaller.
2. Triage `horizon_audit.format_scan` — closes 1 of the 8-member residue;
   D-107 / D-139 have answered this shape twice.
3. Triage `assert_reach.asserts_in` — the last residue member with no
   counterexample of the D-195/D-196 kind.

## Artifacts

- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic, PR #67)
- Files touched: `eval/mppi_sandbox/inert_surface.py`,
  `eval/mppi_sandbox/tests/test_inert_surface.py`,
  `scripts/prompts/auto_research.md`, `docs/decisions.md`
- TSV row appended: yes (`sandbox:pass=2478/2637`, commit `feefcf6`)

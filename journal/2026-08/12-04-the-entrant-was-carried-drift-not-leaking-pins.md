# The entrant was `carried_drift`, not `leaking_pins`

- **Cycle**: 2026-08-12 04:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: _no Notion page_ — the stranding reading (D-112) outranks the
  decision tree and this cycle spent itself on it.
- **Phase**: P3
- **Status**: in_progress

## What I tried

- Took the stranding reading first (D-112): **5 stranded cycles** (22:00, 23:00,
  01:00, 02:00, 03:00), all Artifacts claims honest, **all five TSV rows already
  present** — so nothing to backfill and clearing it was purely a push.
- The push needs a green suite. The suite was red on 15 tests that 03:00's
  journal attributed to its own `leaking_pins()`. Ran the pool scan directly
  before touching anything: `len(gr.guards()) == 100`, and the sole new member
  is **`inert_surface.carried_drift`** — D-206's function, from the *previous*
  cycle's commit. `leaking_pins` never entered.
- Split the 15 reds by what could actually clear them: **3 census numbers**
  (`len(pool) 99→100`, `revocable 5→6`, two membership sets) and **1 probe
  obligation**. Fixed the three; specified the one as **Q-133** and recorded the
  split as **D-208**.

## What worked / what failed

- 🔴 **03:00's diagnosis was wrong and I inherited it.** Its journal says
  "Adding `leaking_pins()` put a new function into the guard census". The scan
  says otherwise: `leaking_pins` narrows by a truth test over a call
  (`c for c in stale_pins(src) if inert(c, src)`), which is D-079's reason for
  staying out. The red-making commit was `1382d4b` (D-206), one cycle earlier.
  Cost of checking: one `python3 -c`. This is **Q-130's failure mode exactly** —
  planning off prose instead of the artifact — and the prose was one cycle old.
- 🟢 **The three census pins were mechanical once the entrant was named**, and
  the tally paragraph now records something new: `carried_drift` is the first of
  100 whose population lives in a **subprocess** (`git diff --name-only`). The
  detector reached it because the narrowing *before* the call is D-073's
  ordinary membership syntax. D-072's syntax result extends past the process
  boundary — further than it was ever argued to reach.
- 🔴 **The 9 `test_guard_direction` reds are one `ProbeError`, and they do not
  yield to numbers.** `carried_drift` is the 6th `revocable_collections` member,
  which creates a probe obligation. A probe is an executed before/after reading
  in a scratch repo, and writing one requires first answering *what
  `carried_drift`'s offence is* — self-evident for the other five, not for this
  one, since its exemption is `NOT_IN entrants` and `entrants` is DERIVED.
- 🟢 **Checked the cheap escape and measured it shut.** Excluding via
  `unprobeable_revocable` needs a *derived* rule; subprocess-population has
  exactly **1** instance inside `revocable_collections`, so
  `test_the_exclusion_is_not_special_cased_to_the_guard_it_drops` refuses it.
  Deleting `carried_drift` is also out — `_main` and three tests use it.
- 🔴 **The strand is not cleared and is now 6.** `cycle_wallclock review` opened
  with "the preceding run ran 41m05 against a 35m budget — cut scope", and this
  was the scope that fit.
- 🔴 **Started a suite the instrument had already called unaffordable, then had
  to kill it.** `cycle_wallclock elapsed` read `SUITE_UNAFFORDABLE` — deadline
  passed 0m27 earlier — and I ran `push_preflight record` anyway out of D-043
  reflex. Six minutes in, the arithmetic was unchanged: the suite cannot clear
  the 9 probe reds, so it cannot unblock the push, so its only yield was a pass
  count for a row that does not need one. Killed it; **no receipt, no count this
  cycle**. The reading was right and I took it late — D-181 exists to make this
  reading actionable *before* the commitment, and I read it after.
- 🟡 **`pgrep -c -f pytest` is not a suite liveness check in this process.** It
  returned 3 throughout, including after the kill, because the executor's own
  command line contains the word `pytest`. Several polls were reading their own
  reflection. The reliable signals were the receipt file and the output size,
  both of which stayed empty.

## North-star delta

- **No movement toward the north star.** Pure guard-infrastructure work; no
  controller, representation, or metric changed. P3 deliverables sat still for a
  sixth consecutive cycle.
- What was bought is diagnostic, not navigational: the next cycle receives one
  specified deliverable instead of fifteen unexplained reds.

## Key learnings

- **A cycle's account of what it broke is not evidence.** 03:00 named the wrong
  function while holding the scan that would have corrected it. The pool scan is
  0.25s (D-180 measured this); the misattribution cost a cycle of confusion.
- **Census entry and probe obligation are different prices, and only one is a
  number.** Thirty-seven prior entrants were bookkeeping. This one is the first
  to land in `revocable_collections` and therefore the first to demand executed
  evidence — which is why "bump the pin" was the wrong instinct here.
- **The escape hatch being *measurably* shut is worth more than arguing it's
  wrong.** One command turned "maybe exclude it" into a closed option, and
  Q-133 can now state (c) as refuted rather than unattractive.
- **Q-133's offence candidate is now founded on source, not intuition.**
  `entrants = current − pinned`, `carried = current ∩ pinned`. A carried reader
  that is **renamed** leaves `named.all` (so it is a `departure`, unchecked) and
  its new name lands in `entrants` (so it is exempt) — moved content, invisible
  on both sides. `departures()`' own docstring is the assumption that breaks:
  "a departure can only shrink the set … losing one cannot introduce movement",
  which holds for a pure departure and fails for a rename, since a rename is a
  departure and an entrance of the same content. That is D-047's masked-collapse
  shape, and it means the mirror `unmirrored_revocable` says is missing exists
  as a function that declares itself unnecessary.

## Recommended next 1–3 priorities

1. **Q-133 as the whole cycle**: fix the offence candidate (a carried reader
   deleted and reappearing under a new name reads clean while its content
   moved), reproduce it in a scratch repo, add the `exempt=` seam to
   `carried_drift` mirroring `undeclared_drift(declared={})`, register the
   `PROBES` entry, run the full suite, push. This clears the strand.
2. If the offence candidate reproduces, `test_q063_the_shape_occurs_twice_and_fails_once`'s
   standing "the count of failures is still one" becomes **false for the first
   time** — the largest result this census has produced in 38 cycles. Record it
   as its own D-NNN, not a footnote.
3. Q-132's re-probe scheduling remains unaddressed and is now the older debt.

## Artifacts

- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic)
- Files touched: `eval/mppi_sandbox/tests/test_guard_reflexivity.py`,
  `docs/decisions.md` (D-208), `docs/deliberations.md` (Q-133)
- TSV row appended: yes

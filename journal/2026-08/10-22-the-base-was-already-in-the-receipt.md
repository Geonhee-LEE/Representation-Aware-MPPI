# The base was already in the receipt

- **Cycle**: 2026-08-10 22:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: STATE #1 — answer Q-129 (the exemption's base)
- **Phase**: P3
- **Status**: keep

## What I tried

- Answered Q-129: `changed_paths()` read `main...HEAD`, which on this 11-day
  branch carries ~88 trigger paths, so `scope()` returned `EXEMPTION_VOID`
  unconditionally and D-180's exemption was inert from the cycle it shipped.
- Q-129's lean (b) named the fix as *"record the receipt's tree hash"* — a
  `push_preflight` change. Checked the field list before building it.
- Shipped `receipt_cost.exemption_base()` + `changed_paths(base=...)`, plus 12
  tests, and wired the `scope` CLI to print the base it used.

## What worked / what failed

- 🔴 **Q-129's premise was wrong, in the cheap direction.** It states the
  commit "is recorded nowhere". `Receipt.head` has carried it since the receipt
  existed — `record` builds the receipt from `tree_provenance.stamp()` and kept
  every field of it. The on-disk receipt was checked before any code was
  written: `head=bf50bd5a`, and `git cat-file -t` says `commit`. So the work
  was a **read**, and no field was added.
- 🟢 **This is the second consecutive cycle where the deficient quantity turned
  out to already be measured** (D-182: `duration_seconds`). Both times the
  written plan was to *create* it. That is now a pattern rather than an
  accident — see Key learnings.
- 🟢 **Measured, not argued**: 88 triggers from `main`, **1** from the receipt
  base. The single remaining trigger is this cycle's own edit to
  `receipt_cost.py`, so the exemption correctly refuses to exempt the cycle
  that changes it — exactly what Q-129 predicted about itself.
- 🟢 **The refusal set is where the design lives.** Three verdicts
  (`NO_RECEIPT`, `SCOPED_RECEIPT`, `UNKNOWN_COMMIT`) all resolve to `main`, and
  no path returns `None`. The reason is a failure mode, not tidiness: `git
  diff` against an absent or unresolvable base returns *nothing*, and an empty
  change set is indistinguishable from "nothing changed" — the exemption would
  activate at the exact moment its evidence vanished.
- 🟢 **`SCOPED_RECEIPT` blocks a bootstrap.** A narrowed receipt never ran the
  guard meta-suite, so it cannot be the evidence that the meta-suite may be
  skipped again; accepting it would let the exemption certify itself forward
  indefinitely off one full run in the distant past. Detected off the
  `--ignore=` flags `Scope.pytest_args` actually emits, pinned by a test that
  builds those flags rather than typing them.
- 🟢 Census `len(gr.guards())` re-derived at **99**, unmoved — no pin bump.
  Cost 0.25 s, which is D-179's repricing being used rather than re-learned.
- 🔴 **The first full suite came back red — 4 failed / 2349 passed — and the
  cause is a hop D-178's placement rule cannot see.** I chose
  `test_receipt_scope.py` because it imports `receipt_cost` *only*, which is
  the rule 17:00 wrote. But `exemption_base` has to read the receipt, so
  `receipt_cost` now imports `push_preflight`, and `push_preflight` spells
  `STATE.md` — so a module naming neither `STATE.md` nor `push_preflight`
  entered that pin's reader set **transitively**, and `stale_pins()` returned
  `('STATE.md',)`. The placement rule reasons about a test's own imports; the
  pin reasons about reach. The pin caught what the rule structurally could not.
- 🟢 The repair was cheap because D-179 had built for it: `reprobe('STATE.md')`
  re-measured the **one entrant** (27 tests, unmoved by the mutation) and
  composed onto the 2026-08-07 full probe — `INERT_COMPOSED`, gen-1 — instead
  of re-running the 15m45 full probe. What was *not* cheap is that the stale
  reading is only visible in the full suite, so it surfaced 18m26 after the
  edit that caused it.

## North-star delta

- **No movement, and this cycle claims none.** No controller, representation,
  or dynamics code; `unsafe_rate` 0.0000 / `min_clearance` 0.3579 /
  `success_rate` 1.0000 unchanged, census attribution still 0/6.
- What it buys is the *next* cycle's budget: the suite is 18m21 of a 35-minute
  cycle, and D-180's exemption — inert until now — drops the guard meta-suite
  (51.5 % of the wall clock) on any cycle that leaves the sandbox sources
  alone. This cycle is not one of them; the next doc-only cycle is.

## Key learnings

- **Two cycles running, the fix was a read and the plan said write.** The
  common cause is that both quantities were *visible in prose* — a journal
  sentence and a Q's own trade-off text — and neither cycle opened the artifact
  before costing the work. Reading the receipt cost one `python3 -c`; believing
  the prose would have cost a `push_preflight` change and a schema migration.
  The rule worth carrying: **when a plan says "record X", check whether X is
  already recorded, and check the artifact rather than the module that writes
  it.**
- A base is a safety argument, not a parameter. Every wrong base fails in the
  direction of *reporting fewer changes*, and fewer changes means more
  exemptions — so the conservative default has to be the fallback for every
  refusal, and that is what makes the verdict safe to ignore.
- Q-129 called its own shape correctly ("this question cannot exempt itself")
  and that turned out to be checkable rather than rhetorical: the shipped tool
  reports its own edit as the trigger.
- **A placement rule about imports cannot police a property about reach.**
  D-178 reads as "put the test where it adds no new imports"; the pin it exists
  to protect is staled by *transitive* reach, which that reading does not
  mention. I applied the rule correctly and staled a pin anyway. The rule is
  still worth having — it is free and catches the direct case — but it must not
  be trusted as sufficient, and the honest cost of the residue is one full
  suite.

## Recommended next 1–3 priorities

1. **Return to the science.** Twenty-two consecutive instrument cycles; census
   attribution is 0/6 and `NO_GRADED_RUNG` is unchanged. The budget lever the
   last three cycles built is now in place — spend it rather than extend it.
2. **Point the constitution's Phase-3 pin check at `inert_surface pins`** and
   correct the stale 4a-ter prose (D-047 shape). Doc-only, no suite time,
   unchanged for nine cycles — and it is now an *exemption-eligible* diff, so
   it is the natural first cycle to prove D-180 end to end.
3. **Wire `exemption_base` into the push gate's receipt step** so the exemption
   is taken automatically rather than by a cycle remembering to ask (D-162's
   rule: a hand-placed guard is the one a time-pressured cycle forgets).

## Artifacts

- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic)
- Files touched: `eval/mppi_sandbox/receipt_cost.py`,
  `eval/mppi_sandbox/tests/test_receipt_scope.py`,
  `eval/mppi_sandbox/inert_surface.py`, `docs/decisions.md`,
  `docs/deliberations.md`
- Suite: 2353 passed / 158 skipped / 1 xfailed, rc=0, 1106.67s (second run;
  the first was 4 red on the STATE.md pin)
- TSV row appended: yes

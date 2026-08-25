# The call site was in the decision log

- **Cycle**: 2026-08-11 12:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: STATE #1 — triage the 3 genuinely-uncited residue members
- **Phase**: P5
- **Status**: in_progress

## What I tried

- STATE #1 sent this cycle to triage `assert_reach.asserts_in`,
  `horizon_audit.format_scan`, `inert_surface.reprobe` — the three D-194 marked
  `NO_VOCABULARY_DEFENCE`, which D-195 had just certified as *verified* zero
  references after removing a fourth member that was never dead.
- Applied the D-186 rule for the sixth consecutive cycle: measure each member's
  sibling family and repo-wide mentions **before** writing its argument.
- That pass broke the premise again, on `reprobe`, and the cycle became about
  what kind of key may be used to say so.

## What worked / what failed

- 🔴 **`reprobe`'s call sites are in `docs/decisions.md`, not the source tree.**
  Two entries record it being *run* with its argument and its returned verdict:
  D-183 — `reprobe('STATE.md')` over one entrant (27 tests), `INERT_COMPOSED`
  gen-1, "seconds instead of a 15m45 full probe" — and the D-177 cycle, where it
  returned `CONTENT_READ`. That is strictly stronger evidence than D-195's
  `REFERENCED_NOT_CALLED`: not "somebody holds the name" but "it ran, and here is
  what it returned".
- 🟢 **So `UNREACHED` is the wrong question, not a wrong answer.** The census's
  population is the source tree; this function's caller is the operator of a
  cycle whose pin went stale. Not being called by the suite is the *design* — it
  exists to turn a 15m45 probe into seconds, and the moment that is needed is by
  definition outside the suite.
- 🔴 **The obvious key is too wide, and I measured that before using it.**
  "call syntax with an argument inside backticks in the decision log" matches
  **25 of 599** public module-level functions (`check`, `grade`, `resolve`,
  `run_matrix`, `scope`, `certify`, …), most of them `LIVE`. Keying on it would
  pick `reprobe` out of the residue only by the *coincidence* that the other 24
  have callers — which is exactly the shape D-193 rejected in `# pragma: no
  cover` (43 of 48 `LIVE`) one cycle ago, returning in different clothing.
- ⚠️ **I did not measure the narrow key.** The right narrowing is call **plus a
  recorded return value**, not call alone. Its population is unmeasured, so no
  verdict was issued and no code changed.

## North-star delta

- **No movement, and none is claimed.** No controller, representation, dynamics,
  or sim code; 0 sim runs. This is instrument-maintenance work on the P5
  verification surface.
- **The residue is still 8.** This cycle did not shrink it. It removed one member
  from the "owes an argument" list for a reason that is not the argument.

## Key learnings

- **A residue is bounded by the population its instrument can see** — D-195 found
  a reference form the scan missed; this cycle found a *caller class* the scan
  cannot represent at all. Both times the instrument, not the code, was the
  finding.
- **A lesson learned about one marker does not transfer itself to the next one.**
  D-193's rule was "measure the key before keying on it". One cycle later a
  differently-shaped key with the same defect looked obviously correct. Measuring
  it cost one command; assuming it would have cost a verdict class.
- **Recorded execution is a citation form the package has no vocabulary for.**
  D-194 taught the docstring `:func:` citation; the decision log holds a stronger
  one (argument + returned verdict) that nothing reads.

## Recommended next 1–3 priorities

1. **Measure the narrow key** — call syntax **plus recorded return value** in
   `SCANNED_DOCS`, over the same 599-function population. If it separates (few
   `LIVE` hits), `OPERATOR_INVOKED` becomes issuable and `reprobe` leaves the
   residue by measurement rather than by prose. One AST + regex pass, 0 sim.
2. **Triage `horizon_audit.format_scan`** — it builds a markdown table and its
   module docstring *contains* a table of exactly that shape. The question is
   whether the shipped table was ever re-derived by this generator; D-107 and
   D-139 have both answered this shape before.
3. **Add the instrument pre-check to the constitution's Phase-3 step** —
   `test_consumer_reach` + `test_predicate_vacuity` + `test_guard_vacuity` +
   `test_citation_audit`, ~120 passed in 29s. Doc-only. **9th time recommended.**

## Artifacts

- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic)
- Files touched: docs/decisions.md, journal/2026-08/11-12-the-call-site-was-in-the-decision-log.md, results/p3-epistemic-shadow-cost-critic.tsv
- TSV row appended: yes

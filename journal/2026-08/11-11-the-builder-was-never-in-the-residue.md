# The builder was never in the residue — the escape hatch was open for the rarer half

- **Cycle**: 2026-08-11 11:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: `STATE#1` Triage the 4 uncited residue members (D-194 follow-on)
- **Phase**: P3
- **Status**: keep

## What I tried

- STATE sent this cycle to triage four residue members — `assert_reach.asserts_in`,
  `guard_direction.build_stranding_repo`, `horizon_audit.format_scan`,
  `inert_surface.reprobe` — on D-194's finding that the vocabulary defence is
  provably unavailable to them, so each owes a different argument.
- Before writing an argument for any of them, measured what each one's siblings
  do: the `build_*_repo` family, the `format_*` family, and each module's public
  surface. D-186's rule, 5th consecutive cycle — measure the premise first.
- The `build_*_repo` read came back with a call site, so the question changed
  from "what argument does it owe" to "why does the census not see this".
- Widened `call_census`'s mention scan by one reference form, and pinned the
  blast radius as a negative control.

## What worked / what failed

- 🔴 **One of the four was never in the residue.** `guard_direction.PROBES`
  holds `build=build_stranding_repo`, and three sites dispatch it as
  `(probe.build or build_scratch_repo)(repo)` — the builder runs whenever that
  probe runs. The census reported `UNREACHED`, `mentions=0`: the verdict that
  means dead code, on a function that executes in the suite.
- 🔴 **The escape hatch was open for the rarer half.** `call_census` counted a
  mention as `mod.func` (cross-module `ast.Attribute`) or `"name"` (string
  dispatch key), and not as a **bare same-module `ast.Name`** — which is the
  form a registry declared beside its members necessarily takes. Both handled
  forms are the cross-file ones; the missed one is the in-file one, and in this
  repo the registry sits in the same file as its entries.
- 🟢 **The blind spot cut one way only.** It could never invent a caller, only
  hide one, so every verdict it distorted was distorted *toward* the finding.
  That is the benign direction for a residue count and the reason eleven cycles
  of triage were not built on sand — but it means the residue was an
  over-count, not an under-count, and "delete or wire" was being asked about a
  function that needed neither.
- 🟢 **The fix is narrow by measurement, not by intent.** Across both
  populations exactly **one** of nine residue members moves; the other eight
  read `mentions=0` before and after. Measured before keying on it (D-193), and
  pinned as `test_the_registry_form_is_not_an_amnesty` — a mention rule loose
  enough to clear the whole residue would be D-189's shape-fitting one level up:
  rather than manufacture a caller per red, manufacture one rule that greens
  every red.
- 🟢 Verdict is `REFERENCED_NOT_CALLED`, not `LIVE`, and that is the honest
  ceiling: the census does not follow `probe.build` back to its target, so what
  it can say is that somebody holds the name — not that somebody calls it.
- 🟢 Population B reclassified `TEST_ONLY` 98 → 92 alongside
  `REFERENCED_NOT_CALLED` 8 → 15; per D-191 `TEST_ONLY` is B's normal state and
  not a finding, so the **finding** count moved by exactly the one member.
- 🟢 STATE #3's instrument pre-check ran first — **120 passed in 29s** (118 + the
  2 new) — and caught the pin list before a full suite was spent on it. 8th
  cycle it has paid.

## North-star delta

- **No movement, and none claimed.** No controller, representation, dynamics or
  sim code; 0 sim runs; census attribution coverage still 0/6, `NO_GRADED_RUNG`.
- The instrument that bounds this branch's dead-code debt was over-reporting it
  by one, and the residue is now 8 members that are referenced by nothing at all
  — a number that means what it says.

## Key learnings

- **A residue is a claim about an instrument before it is a claim about code.**
  Four cycles of "each owes an argument" presumed the reading. One of the four
  owed nothing; the reading did.
- **An escape hatch enumerates forms, and an enumeration is a place to be
  incomplete.** Both forms `call_census` knew were cross-file. Nothing in the
  code said "cross-file" — that was the shape of the examples the author had in
  hand, and it silently became the rule.
- **Ask which way a blind spot cuts.** This one could only hide callers, never
  invent them, so it inflated a finding count rather than suppressing one. The
  opposite direction would have meant every triage decision since D-191 rested
  on an unchecked reachability claim.
- **A widened rule needs its blast radius pinned in the same commit.** The
  measurement (1 of 9 moves) is what separates this from an amnesty, and a
  measurement not written down as a test is a sentence in a journal.

## Recommended next 1–3 priorities

1. **Triage the 3 genuinely-uncited residue members** — `assert_reach.asserts_in`,
   `horizon_audit.format_scan`, `inert_surface.reprobe`. D-195 removed the
   fourth; these three have zero references of any kind, so the vocabulary
   defence really is unavailable and each owes an argument. 0 sim.
2. **Apply the D-194 rule to the 3 cited-but-untriaged** —
   `magnitude_survival.standings`, `predicate_vacuity.unpatchable`,
   `calibrate_lam.scene_is_calibratable` (bare-mentioned only — decide whether
   bare counts). Would close up to 3 of 8.
3. **Add the instrument pre-check to the constitution's Phase-3 step** —
   `test_consumer_reach` + `test_predicate_vacuity` + `test_guard_vacuity` +
   `test_citation_audit`, 120 passed in 29s, hand-run again this cycle and again
   it paid. Doc-only. **8th time recommended.**

## Artifacts

- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic)
- Files touched: `eval/mppi_sandbox/consumer_reach.py`,
  `eval/mppi_sandbox/tests/test_consumer_reach.py`, `docs/decisions.md`
- TSV row appended: pending

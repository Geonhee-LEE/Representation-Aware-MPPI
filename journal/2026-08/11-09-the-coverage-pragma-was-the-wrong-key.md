# The coverage pragma was the wrong key

- **Cycle**: 2026-08-11 09:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: STATE #1 — grade the deferred hook in `consumer_reach` (`DEFERRED_BY_COST`)
- **Phase**: P5
- **Status**: keep

## What I tried

- STATE asked for a marker-keyed verdict so `reading_record.take_and_record` —
  `UNREACHED` but not dead, it costs 2k concurrent five-minute suite runs —
  leaves the finding count without leaving the report.
- STATE also **named the key**: "key it on the `# pragma: no cover` marker
  *rule*". Per D-186 I measured the key before writing to it.
- Shipped `DEFERRED_BY_COST` keyed on a dedicated marker instead:
  `# pragma: no cover -- deferred-by-cost: <why>`, read off the **signature**,
  graded after the reachability verdicts, never before them.

## What worked / what failed

- **FINDING: the proposed key is wrong in the direction this module exists to
  fix.** `pragma: no cover` occurs on **48 of 744** population-B functions, and
  **43 of them grade `LIVE`**. Its tails read `- CLI` (13×), bare (8×),
  `- reporting` (5×), `- reporting sugar` (3×), `- defended` (3×). It is a
  *coverage* directive — "do not count these lines" — and says nothing about
  callers. That it singles out exactly one residue member today is a
  **coincidence of the other 43 having callers**: two dozen are `report()` /
  `main()` bodies kept `LIVE` only by their own `if __name__` block. Delete
  that block in a routine refactor and the bare-pragma rule grades a
  newly-dead reporter `DEFERRED_BY_COST` — an exemption that *hides a
  finding*, granted by a marker never making that claim. Same shape as D-189's
  "a mention is not a call": a coverage pragma is not a statement of
  unreachability. That fixture is now a test.
- **My first draft of the rule was wrong and its own test caught it.** Comments
  are not AST nodes, so the span between `def` and the first body statement
  silently swallows a free-standing comment line under the header — body-position
  prose wearing the signature's address. Pure-comment lines are now dropped,
  which still keeps the multi-line `):  # pragma …` form `take_and_record` uses.
- Residue **10 → 9**; `DEFERRED_BY_COST=1`, `FRAMEWORK_DISPATCHED=2` unchanged.
  The instrument pre-check (165 passed, 3m05) ran first and was green, so no
  second full suite — 3rd consecutive cycle it paid.

## North-star delta

- **No movement, and this cycle claims none.** No controller, representation,
  dynamics, or sim code; 0 sim runs. `unsafe_rate` / `min_clearance` /
  `success_rate` untouched, census attribution still 0/6.
- What moved: the residue count no longer carries a known non-defect, and the
  cheap-but-wrong way of achieving that is now pinned shut by a test.

## Key learnings

- **A marker inherits the meaning of its existing uses, not the one you need.**
  Before keying a verdict on any in-source marker, count what it currently
  means elsewhere. 48 uses, 43 `LIVE`, ~24 one refactor away from a silent
  exemption — none of which a grep of the residue would show.
- **Narrow-today is not narrow-by-construction.** The bare-pragma rule and the
  shipped rule are indistinguishable on the current tree; they differ only on
  trees that do not exist yet. That difference is the whole deliverable.
- **A self-serve marker needs a watcher, and the residue pin already is one.**
  Taking the verdict moves a name *out of* the pinned list, so no signature can
  claim it without editing the test in the same commit — a rule, not a registry.

## Recommended next 1–3 priorities

- **Decide `guard_vacuity.never_fired` / `predicate_vacuity.one_sided`** — keep
  both as the reading's stated vocabulary (citing where the module docs say so)
  or delete both. Closes 2 of the 9. Unchanged from last cycle.
- **Add the instrument pre-check to the constitution's Phase 3** — 165 passed
  in 3m05, hand-run and load-bearing for the 3rd cycle running. Doc-only.
  **6th time recommended.**
- **Do not re-price `from_sweep` as wiring** — still A's only residue, still
  gated on the user-blocked 64-run walk.

## Artifacts
- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic)
- Files touched: eval/mppi_sandbox/consumer_reach.py, eval/mppi_sandbox/reading_record.py, eval/mppi_sandbox/tests/test_consumer_reach.py, docs/decisions.md
- TSV row appended: yes

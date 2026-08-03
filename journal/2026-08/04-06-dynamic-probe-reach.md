# The dynamic probe reaches 1 guard from its fixture, and the other two are held up by hand

- **Cycle**: 2026-08-04 06:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: STATE #2 — ask D-052's applicability question of the other dynamic probes
- **Phase**: P3 (instrument lane; calendar phase is P4)
- **Status**: keep

## What I tried

- D-052 found its method applicable to **1 of 12** sites and said the general
  lesson out loud: *an instrument's applicability is a fact about the code it
  reads, not about the instrument*. `guard_direction` is the package's other
  dynamic probe — it stands up a throwaway git repo per (guard, path), commits
  the offence, compares readings — and it carries **2** entries with
  `unprobed_revocable()` reporting that table complete. Asked whether **2** is a
  bound or another coincidence.
- `probe_reach.py`: partition all guards by the **substrate** a fixture would
  have to vary to move their reading (`REPO_ROOT` / `PACKAGE_SOURCE` /
  `SCANNED_POOL` / `DOMAIN`), derived from `inspect.signature` and pinned as a
  **partition** of the pool — not a table.
- For the root-addressable set, *executed*: call each guard in
  `build_scratch_repo`'s fixture and at the real root, and score the pair.
- D-052's discipline — route around, don't just report. `build_enriched_repo`
  copies the read surfaces the failures name (`docs/`, `scripts/`) into the same
  scratch repo and the reach is re-measured. The difference between the two
  numbers is the **measured** price of the fixture, not an argument that one
  exists.

## What worked / what failed

- 🔴 **The reach is bounded by the fixture, and the fixture is exactly the size
  of the probes it already has.** Of 41 guards, **16** are root-addressable. In
  the base fixture **1** is readable and **8 raise** — it holds the five
  declared local-only paths and one control file, while those guards read
  `docs/decisions.md` or `scripts/*.sh`. Copying two directories in takes it to
  **6 readable, 0 errors**: `fixture_gap` = **8** guards whose exclusion from
  the probe's reach was a property of what `build_scratch_repo` happens to write.
- 🔴 **And the sharper one: neither registered probe is readable from a fixture
  at all.** `staged_declarations` and `undeclared_drift` both score
  `UNDECIDABLE` — empty at HEAD *and* empty in both scratch repos. What makes
  them probeable is the hand-written `Probe.liveness` act, of which there are
  exactly **two**. So the reach is bounded by a typed table after all, one layer
  *below* the table `unprobed_revocable` checks. D-052's finding reproduced
  inside the instrument that was supposed to generalise past it.
- 🔴 **The existing mirror clears over the wrong population.**
  `unprobed_revocable()` = `()` — but it compares `PROBES` against
  `revocable()`, **2** guards, so it cannot report an omission outside the
  `DIFFERENCE` shape. `reach_gap` = **6** readable-and-unprobed guards, all of
  them outside it, asserted disjoint from `revocable` so the two mirrors are
  independent rather than one being a weaker copy.
- ✅ **The eight failures raise rather than returning empty, and that is what
  made the gap visible.** `local_only_audit`'s stated discipline — an audit that
  degrades to "found nothing" reports a clean guard for an experiment it never
  performed — is the reason `FIXTURE_ERROR` is distinguishable from
  `UNDECIDABLE` here. Had they degraded, the fixture gap would have read zero.
- ⚠️ **The enriched fixture is not a faithful copy and is not presented as one.**
  `citation_audit.missing_sites` reads **17** in it and **0** at HEAD;
  `unregistered_local_only` reads 2 vs 0. Both readings are recorded on every
  `Reach` so an inversion is visible instead of being averaged away.
- 🔴 **The module entered the registry it audits** (D-046's shape, **5th**
  occurrence): pool 40 → **41** (`probe_reach.reach_gap`).
- ✅ First-draft defect caught by its own test rather than shipped: `normalise`
  folded `str` returns to an empty set, which would have scored
  `lam_dependence.report` as `UNDECIDABLE` — a measurement reported where none
  was possible. `NOT_A_READING` is now a distinct verdict, pinned.
- 🔴 **Second one, and this time the defect was in the test.** The headline
  assertion pinned the *verdict* `UNDECIDABLE`, which also asserts the guard
  reads empty **at the real root** — a fact about whatever is in the working
  tree when the suite runs. `undeclared_drift` reports every file this cycle
  created, so it scored `MUTE_FIXTURE` and the test failed on the cycle that
  wrote it, for a reason with nothing to do with the probe. The finding lives
  entirely in the fixture half; the assertion now reads `fixture_size == 0`.
  **Tenth first-draft in eleven cycles wrong about its own population** — and
  the first where the wrong population was the *test's* precondition rather than
  the scan's, in a file whose own header claims not to pin today's numbers.

## Unplanned finding — the Notion outage was misdiagnosed for 55 cycles

- STATE has said "MCP tool schemas resolve but the **workspace grant is
  missing**" every cycle since ~06-11. Tested it this cycle instead of copying
  it forward: **`notion-search` and `notion-fetch` both work.** The TODO
  database, its data-source id, and its full schema all come back exactly as
  documented in the prompt.
- What actually fails is **`notion-query-data-sources`**, which returns
  *"requested permissions … but you haven't granted it yet"* — a Claude Code
  **permission-allowlist** gate in this non-interactive session, not a Notion
  connector problem. The remedy is therefore an allowlist entry, **not** a
  workspace re-grant, and 55 cycles of Telegram/STATE have been asking the user
  for the wrong thing.
- The failure mode is this cycle's own finding, in the operational log rather
  than in code: **a claim carried forward because it was next to something true,
  never re-derived.** Same shape as `unprobed_revocable` reading clean over a
  population of 2. Re-deriving it cost one tool call.

## North-star delta

- **No avoidance or tracking number moved — twenty-first consecutive instrument
  cycle.** Scenes able to contribute an avoidance number: 5, reportable: 4 —
  unchanged.
- What moved: the claim "the direction probe's table is complete" stopped being
  a clearance over 2 guards and now has a denominator of 16 with 6 named
  omissions. The 가려진-obstacle class still has exactly one working cost term
  (D-027).

## Key learnings

- **A mirror is only as strong as the population it is checked against, and the
  population is usually chosen by whatever was convenient.**
  `unprobed_revocable` reads clean because `revocable()` is the set it was
  written next to — not because the probe table is complete. Both of the last
  two cycles found this shape; it is now worth checking every mirror's
  denominator on sight.
- **Coincidences nest.** D-052 removed a coincidence at the exemption-parameter
  layer and the same shape was waiting one layer down in the liveness-act table.
  Routing around one instance does not bound the class.
- **Raising beats returning empty, measurably.** This is the first cycle where
  the "refuse rather than degrade" discipline paid a *detection* dividend rather
  than a hygiene one.

## Recommended next 1–3 priorities

1. **Derive `Probe.liveness` from `guard_reflexivity.acts_of` instead of typing
   it** (Q-068). `acts_of` already enumerates each guard's watched git /
   filesystem operations with scope — that is the same knowledge the act table
   hand-writes, and deriving it closes the coincidence at its source rather than
   widening a typed table to 6 more entries.
- 2. **Re-derive every "exactly N" bound in `docs/decisions.md`.** D-048's had
  drifted, and this cycle's `unprobed_revocable` clearance is the same failure
  wearing a different hat. The pool has gone 23 → 41.
- 3. **Extend the substrate measurement to `PACKAGE_SOURCE` (9 guards).** Those
  are addressable by a scratch *source tree*, a fixture nobody has built; the
  same question applies and the answer is currently unknown rather than known-2.

## Artifacts

- PR: #67 (existing, 48th consecutive cycle writing into it)
- Files touched: `eval/mppi_sandbox/probe_reach.py`,
  `eval/mppi_sandbox/tests/test_probe_reach.py`, `docs/decisions.md`,
  `docs/deliberations.md`, `results/p3-epistemic-shadow-cost-critic.tsv`
- TSV row appended: yes
- Fast half: **548 passed** / 135 skipped / 1 xfailed (was 533), re-taken after
  the 4a/4a-bis writes per D-043/D-044; `tree_provenance declared` clean.

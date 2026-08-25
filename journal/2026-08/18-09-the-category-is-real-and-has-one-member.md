# The category is real, and it has one member

- **Cycle**: 2026-08-18 09:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: (STATE #1 — Q-166 classification; no Notion TODO, query-data-sources still unauthorised)
- **Phase**: P3
- **Status**: keep

## What I tried

- Applied Q-166's own proposed discriminant — *does any consumer supply the
  tested value from outside the registry?* — to all 9 keys returned by
  `guard_reflexivity.unwatched_exemptions()`, reading each membership-test site
  and the callers of its enclosing function.
- Wrote the result as a table in `docs/unwatched_exemptions_classification.md`,
  with the test site and the provenance of the value under test named per row.
- Recorded **D-340** and marked **Q-166 resolved**. No code changed.

## What worked / what failed

- **The discriminant computes without judgement calls.** All 9 classify off the
  call site plus its callers; no new constant was needed, which was the property
  Q-166's *Lean* required of any candidate criterion.
- **The split is 8 : 1, not two comparable halves.** Eight narrow an
  outside-sourced population — AST scan (`DECLARED_DEF_TIME`, `RESOLVERS`,
  `SELF_DEFINING`, `SITE_CLASSES`), doc scan (`SCOPED_CLAIMS`), a *different*
  registry (`DEGENERATE_READINGS` ← `SCOPED_CLAIMS`, `HULL_REPAIRED_BY` ←
  `SITE_CLASSES`), a caller-set instance field (`TEMPERATURE_RELEVANT`).
- **D-339's reasoning survived its own audit, on the row that looked like a
  counterexample.** `constant_at_every_index` has three callers; two draw from
  `OBSERVABLES`, and the third hand-types the literal `"bearing_rate"` —
  exactly the shape of an outside-sourced value. It is not one: `bearing_rate`
  *is* an element of `OBSERVABLES`. Had it not been, D-339 would have been wrong.
- **What did not get done, deliberately**: the D-330 amendment. It touches guard
  code and so costs another ~866 s suite; Q-166's stated action separated the
  table from the amendment and I kept that separation.

## North-star delta

- **No movement.** This is verification-surface work — the fifth consecutive
  cycle inside the branch's own guard machinery. Nothing about obstacle
  avoidance or path tracking changed.
- The one thing it buys the planner track is closure: Q-166 was the cheap item
  standing between this branch and returning to the open representation
  question, and it is now closed at doc-only cost.

## Key learnings

- **A rule can be well-defined and still untested.** The honest reading of 8:1
  is not "the category is vindicated" — it is that the category exists,
  classifies mechanically, and has exactly one member, which is the member it
  was invented for. Its predictive value is decided by the *next* entrant, not
  by re-auditing these nine.
- **The near-counterexample is the load-bearing check.** A classification whose
  only member is the one it was built for is worth little unless something in
  the audit could have refuted it. `"bearing_rate"` could have, and was checked
  rather than assumed.
- **Doc-only did not mean suite-free.** `docs/decisions.md` and
  `docs/deliberations.md` are inside `citation_audit.SCANNED_DOCS`, so the
  D-315 ordering still charges a full receipt for a cycle that changed no code.
  "No code change ⇒ no suite" is false on this repo and should stop being
  planned against.

## Recommended next 1–3 priorities

1. **Return to the representation question** — D-334/335/336 killed `cut_in`;
   run the separability matrix over the other four scene pairs and report which,
   if any, separate on non-constant observables. This is the north-star item.
2. **Amend D-330** with the Q-166 discriminant (one paragraph, guard-code
   adjacent, costs a suite) — only worth a cycle if bundled with other guard work.
3. **Fold the node-ID lesson into the loop prompt** — still unshipped from the
   08:00 cycle's list.

## Artifacts

- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic — PR #67, reused)
- Files touched: docs/unwatched_exemptions_classification.md, docs/decisions.md, docs/deliberations.md, results/p3-epistemic-shadow-cost-critic.tsv
- TSV row appended: yes

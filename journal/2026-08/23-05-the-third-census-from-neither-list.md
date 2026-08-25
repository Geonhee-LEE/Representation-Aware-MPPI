# The third census to arrive from neither list

- **Cycle**: 2026-08-23 05:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: STATE #2 — enumerate `census_preempt`'s uncovered censuses
- **Phase**: P5
- **Status**: keep

## What I tried

- Took the three Phase-1 readings. `stranded` clean, `wallclock review` graded
  the predecessor 60m14 against a 35m budget, and `push_preflight probe` found
  `c06db39` **already graded green** — so this cycle owed a suite only for what
  it added, not for the tree it inherited.
- Added `default_lam_sites.census()` as `census_preempt`'s **sixth** census
  rather than adding its name to the `UNCOVERED` list. The pin is parsed out of
  `test_default_lam_sites.py`'s own assertion (`(c.decides, c.defaults,
  c.forwards) == (…)`) and keyed by **attribute name**, so a reordered
  assertion is read rather than silently transposed.
- Five tamper tests, matching the module's own rule that an entry which cannot
  be made to bite contributes a clean reading that means nothing.

## What worked / what failed

- The census reads `234 lam sites (106/85/43), pin matches` — live on the tree
  as it stands, and it bites in both directions under `dataclasses.replace`.
- **The D-047 test failed on its own subject matter first.** It asserted the
  pinned integers do not occur in the module source as *text*; `"43"` occurs
  inside `D-433`, the decision whose strand is the reason this census exists.
  Re-cut over the AST: prose that *narrates* a magnitude is not a second
  statement of it, a second `int` literal in the derivation is.
- The module docstring said "a typed tuple of four" while `CENSUSES` already
  held five — the prose count had gone stale one entry before this one. Dropped
  the number rather than bumping it to six.

## North-star delta

- No control movement. This is verification machinery, and the honest framing
  is that it is **strand-prevention**: D-433's sweep left this exact pin red,
  its push gate refused, and the commit sat unmeasured overnight while the
  pre-empt reported CLEAN.
- The pre-empted census is the one the current roadmap moves most. D-428, D-430
  and D-433 each moved `forwards` by exactly one — every knob sweep this branch
  ships joins it. Cost to read: ~0.6 s, against the ~24 min suite it pre-empts.

## Key learnings

- Three censuses have now arrived from *neither* list (`loop_reach` D-317,
  `consumer_reach` D-344, `default_lam_sites` today). At three, the diagnosis
  stops being "the wrong names got typed" and becomes a claim about typing the
  candidate population at all — filed as Q-183, not answered here.
- `UNCOVERED` is a **weaker** instrument than it reads as. D-318 told readers to
  read the `Not covered:` line; a reader who did was still not told about any of
  the three, because absence from the covered set does not imply presence in the
  omitted one.
- A D-047 "no second copy" check written as a substring test is unsound in a
  repo that names its decisions `D-NNN` — the decision ids collide with the
  magnitudes. AST is the right surface for that class of check.

## Recommended next 1–3 priorities

- Q-183: can `census_preempt`'s candidate population be **derived** (a test
  asserting a derived collection equals a literal) instead of typed? That is
  the fix the three-occurrence pattern actually points at.
- STATE #1 `[infra] census_preempt silent-bucket headroom (Q-182)` — still open,
  same family, one-line change.
- Heading residual **cause** reconstruction — two knob sweeps have now failed
  (`w_speed`, `w_omega`); this is the P5 substance item and is much closer to
  the north star than either infra item above.

## Artifacts
- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic)
- Files touched: eval/mppi_sandbox/census_preempt.py, eval/mppi_sandbox/tests/test_census_preempt.py, docs/decisions.md, docs/deliberations.md, results/p3-epistemic-shadow-cost-critic.tsv
- TSV row appended: yes

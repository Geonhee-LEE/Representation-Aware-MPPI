# The declared suite already exists — four times, hand-typed

- **Cycle**: 2026-08-21 11:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: `STATE #1` Re-choose Q-177 (a) vs (b) now that cost no longer separates them
- **Phase**: P5
- **Status**: keep

## What I tried

- Discharged the strand first (D-112): 10:00 committed `2d4bce9` (D-401) and
  never pushed. TSV row was already committed and `cycle_artifacts claim` read
  `DISCHARGE_PUSH`, so the only missing artifact was the receipt.
- Then took STATE #1 — choose Q-177 (a) *enforce* vs (b) *narrow the promise* —
  which D-401 left explicitly to "grounds other than price".
- Before choosing, grepped for the population (a) would need: the **canonical
  full-suite target list** that `check()` would compare `receipt.command` against.

## What worked / what failed

- **The population already exists, four times over.** `DEFAULT_SUITE` is a
  hand-typed 3-tuple in `predicate_vacuity.py:166` and `guard_vacuity.py:110`,
  repeated as `TestPytestArgs.DEFAULT` in `test_receipt_scope.py:144` and again
  in `test_suite_coverage.py:300` — plus three more copies in the constitution
  (`auto_research.md:291,384,570`). Seven total.
- `predicate_vacuity`'s own comment says the quiet part: *"Deliberately the same
  tuple `guard_vacuity` uses, so the two censuses describe the same suite."*
  That is a hand-typed copy of a registry with no registry — **D-047's exact
  failure shape**, which cost this project `TODO.md` and `research/feed.md`
  going uncommitted-but-committable for thirty-odd cycles.
- **This re-prices (a), and the re-pricing is the finding.** D-401 priced the
  enforce option at "census `+1`, stale on every new test" and deferred on that
  basis. That price was measured against the *test-count* denominator `(c)`
  needed. **(a) does not need a test count** — it needs the **target path
  list**, which is 3 strings, already written 7 times, and which goes stale only
  when a test *directory* is added, not when a test is. The `+1`/8-cycle-RED
  argument (D-399) does not apply to it.
- So (a) is not a census purchase at all: it is a **consolidation** — declare
  once, derive the other three, let `check()` read it. Net-negative LOC, which
  the simplicity criterion counts as a win.
- What failed: nothing was implemented. `cycle_wallclock elapsed` left 9m12 to
  suite start, and buying the consolidation inside that window is exactly the
  D-181/D-399 violation the last three cycles avoided on purpose.

## North-star delta

- **No planner movement — cycle 34 of zero.** 0 rollouts; no controller,
  representation or dynamics code touched. This is meta-work on the
  verification surface, and it is honest to say the north star did not move.
- One finished cycle (D-401) that was sitting unpublished on disk now reaches
  `origin`, so the branch's record matches its work again.

## Key learnings

- **"Grounds other than price" was the wrong frame — the price was wrong.**
  D-401 handed the next cycle a tie and told it to break the tie on principle.
  The tie did not exist: one grep showed (a)'s population already built. Two
  cycles of deliberation were spent on a cost that was never going to be paid.
- **A comment that says "deliberately the same as X" is a registry confessing
  it isn't one.** That phrasing is now a grep-able smell in this repo; D-047
  and this entry are the same defect wearing different words.
- The reader-dependent-defence argument (Q-176 → D-397 → D-399) still favours
  (a) over (b) independently. Both arguments now point the same way, which is
  why this closes rather than defers.

## Recommended next 1–3 priorities

1. **Execute (a) as a consolidation, not an addition** — one `DECLARED_SUITE`
   registry, the 4 Python copies derived from it, `check()` returning a
   `SCOPED` verdict when `receipt.command` doesn't cover it. Budget a full
   cycle: it touches `push_preflight` and two censuses.
2. **Fold the constitution's 3 copies into the same registry** or accept them
   as prose and say so — 7 copies with 4 machine-readable is the state D-047
   warned about.
3. **Merge or close PRs #66–#69** (user) — 41 days, nothing on `main` since
   2026-07-12.

## Artifacts
- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic)
- Files touched: docs/decisions.md, docs/deliberations.md, journal/2026-08/21-11-the-declared-suite-already-exists-four-times.md, results/p3-epistemic-shadow-cost-critic.tsv
- TSV row appended: yes

# Predicate read depth measured, not read: 9 of 10 co-derived pairs disagree

- **Cycle**: 2026-08-04 04:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: `STATE-1` Audit the scan's remaining expression predicates for depth disagreement (Q-066)
- **Phase**: P3
- **Status**: keep

## What I tried

- Derived the predicate population from `guard_reflexivity`'s own AST — module-level
  functions with a parameter annotated `ast.expr` — rather than typing it. **7**, and
  `unadapted_predicates()` / `stale_adapters()` check the typed adapter table against
  that glob in both directions.
- Measured each predicate's read depth by **running it**, not by reading it: a ladder
  of probe expressions (`BARE` → `set(X)` → `{v for v in X}` → alias → `_p1()` → `_p2()`)
  wrapping one ground, parsed from source so the predicate sees what a real scan hands it.
- Ran every rung against **two** grounds — one the predicate answers positively, one
  negatively — and scored `FOLLOWS` only when **both** readings survive the wrapper.
- Priced the sharpest disagreement at HEAD (`provenance_depth_exposure`).

## What worked / what failed

- 🔴 **Q-066's answer is that depth agreement is the exception.** Of **10** co-derived
  predicate pairs, **9** disagree. Exactly one pair (`_provenance`, `core_name`) reads
  alike. No two of the seven predicates share a profile beyond that one pair.
- 🔴 **The two-ground rule was not a formality — it demoted a predicate by two rungs.**
  `_is_set_valued` scores `FOLLOWS` on a positive-only ladder at `set(X)` and
  `{v for v in X}`, but it answers `True` for `set(5)` and `{v for v in 5}` too: the
  **wrapper** is answering, not the content. Its real content-reading depth is 3/6
  (`BARE`, `CALL_1`, `CALL_2`), not 5/6. This is D-050's masking shape one layer down —
  a shape matching for a cause that never fires — and a positive-only probe would have
  reported the depth the predicate does not have.
- 🔴 **My first-draft relation missed the pair the module was written about.** Keying
  co-application on argument *spelling* gives 4 pairs and **none** is
  (`_is_set_valued`, `_difference_kind`): `_guards_in` hands the first the operands
  (`left`/`right`) and the second the population traced from `node.left`, so they read
  the same `&` expression through different bindings. Tracing arguments back to their
  shared **loop variable** (through tuple unpacking and `list.append`, which
  `gr._aliases` does not follow) recovers it and gives 10. **Eighth first-draft scan in
  nine cycles to be wrong about its own population, and again under-counting.**
- ✅ **D-050's fix is confirmed by measurement, and its limit is stated.** That pair now
  agrees on exactly `CALL_1`/`CALL_2` — the rungs D-050 was about — and still differs on
  `SET_CALL`/`COMP`, where the difference is `OPAQUE` vs genuine, not shallow vs deep.
- 🔴 **Declared depth and measured reach are unrelated quantities.** `_resolve` declares
  `depth=3` and reads through **one** wrapper; `_difference_kind` declares `depth=2` and
  reads through **four**. The `depth=` default is a fourth statement of the property in
  D-049's shape — nothing compares those numbers to each other or to the ladder.
- ⚠️ **The consequential disagreement is latent, not live.** `_is_set_valued` follows a
  same-module call and `_provenance` stops at one, so a registry reached through a helper
  is admitted as a guard and then classed `DERIVED` — invisible to every `TYPED` screen
  (STATE #2 and #4 both plan to use those). `provenance_depth_exposure()` returns **`()`**
  at HEAD. Shipped as a re-derived zero rather than an assertion, because D-050's
  prescribed "extract the duplicate registry" refactor is exactly the edit that turns it
  positive.
- ✅ **The liveness check earned its place on the first run**, before any finding: it
  rejected `_unwrap_seq`'s grounds (two Names, both reading `()`) instead of scoring a
  free `FOLLOWS` on every rung. The probe was wrong, not the predicate.
- 🔴 **The module entered the registry it audits** — D-046's shape, third occurrence.
  Guard pool 32 → **38**, mirrors 4 → **7**. And the sharpest incidental evidence that
  D-050's fix was load-bearing: **three of the six** new guards are visible *only* to the
  deep predicate, so a module written after the fix would have been half-invisible before it.

## North-star delta

- **No avoidance or tracking number moved — nineteenth consecutive instrument cycle.**
  Scenes able to contribute an avoidance number: **5**, reportable: **4** — unchanged.
- What moved: the scan that defines the guard population now has a **measured** depth per
  predicate instead of a read one, and the one disagreement that can silently reclassify
  an exemption is priced at 0 with a live detector attached.
- The 가려진-obstacle class still has exactly one working cost term (D-027).

## Key learnings

- **A predicate can be right at a rung for a reason that has nothing to do with the
  content.** Measuring depth with positive probes alone over-reports it, and the
  over-report is indistinguishable from real depth — which is precisely how D-050's
  masked collapse looked. Negative-ground probes are what separate `FOLLOWS` from `OPAQUE`.
- **"The same expression" is not one relation.** D-050's phrasing suggested identity;
  the two predicates actually read a node and its operands. A scan keyed on the stronger
  reading of that phrase finds four pairs and misses the one that failed.
- **A declared depth parameter is not evidence about depth.** Three predicates declare
  `depth=` and the numbers do not order the same way the measured reaches do.

## Recommended next 1–3 priorities

1. **Screen every `TYPED` exemption for masking** (STATE #2) — D-050's mechanism
   generalises statically and the now-38-guard pool can take the screen today.
2. **Give `_provenance` the same-module-call arm `_is_set_valued` got**, or state in the
   code why it should not have it — `provenance_depth_exposure()` is the test that would
   confirm the choice either way.
3. **Derive `NAME_SCOPE_CLAIMS` instead of typing it** (STATE #3) — the last registry in
   this package still typed on both sides.

## Artifacts
- PR: #67 (open, 46th consecutive cycle writing into it)
- Files touched: `eval/mppi_sandbox/predicate_depth.py` (new),
  `eval/mppi_sandbox/tests/test_predicate_depth.py` (new),
  `eval/mppi_sandbox/tests/test_guard_reflexivity.py`
- TSV row appended: yes (`sandbox:pass=512/512`, status `keep`)
- Fast half: **512 passed** / 135 skipped / 1 xfailed (was 493), re-taken after the
  4a/4a-bis writes per D-043/D-044; `tree_provenance declared` clean.

# Q-063 (b): the D-047 shape occurs exactly once, and the second finding is one layer over

- **Cycle**: 2026-08-04 01:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: STATE #1 + #2 — ask Q-063 of every guard structurally, in the same pass as the coincidence-held-invariant audit
- **Phase**: P4 (calendar) / P3 work
- **Status**: keep

## What I tried

- `eval/mppi_sandbox/guard_reflexivity.py` — discovers the package's **guards** by
  globbing modules and asking the AST which public functions filter a population
  against a set (D-045's lesson applied to the registry of registries; a
  hand-written guard list would have been the fifth consecutive one to come up short).
- Two independent properties per guard, both structural: **revocability** — is
  the population a *difference between two observations*, which the offending act
  can collapse — and **exemption provenance** — is the filter set a hand-typed
  module constant (`TYPED`), a computed set (`DERIVED`), or a display written at
  the filter site (`INLINE`).
- `mirrors()` (same-module, role-swapped) plus `exemption_watchers()` /
  `unwatched_exemptions()` (cross-module: is anyone's *population* this allow-list?).
- 15 pytest cases pinning every verdict, including the two first-draft errors.

## What worked / what failed

- ✅ **Q-063 (b) answers, and the answer is a negative.** Of **23** guards over 24
  modules, exactly **one** has a population the offence can collapse:
  `tree_provenance.undeclared_drift`, D-047's own. The lean was "a shape that
  exists once usually exists twice" — here it does not. Every other guard
  enumerates its population from a listing (`git ls-files`, a document scan, a
  module's own members), and an enumerated population still contains the
  offender *after* the offence.
- ✅ **The separating fact is structural, not nominal.** `stale_declarations`
  sits in the same module, reads the same `DECLARED_LOCAL_ONLY`, and is **not**
  revocable — a name- or module-based rule would have flagged both or neither.
- 🔴 **Second finding, and it is the sharper one: `DECLARED_LOCAL_ONLY` has the
  *most* watchers of any allow-list in the package — two — and both read clean
  through the whole ~30 cycles the rule was breakable.** `stale_declarations`
  watches it for tracked-ness, `underived_declarations` for re-derivability;
  neither watches *staging*. **Coverage by existence is not coverage by act**,
  so `unwatched_exemptions()` returning empty must never be read as a clearance.
  That is why D-047 had to add a third watcher rather than fix an existing one.
- 🔴 **The first draft found one mirror where there are three**, and the error
  ran in the *inflating* direction — an undetected mirror promotes a sound guard
  into Q-063's answer set. Cause was spelling: `unregistered_citations` filters
  `derived_citations(root)` against a set **comprehension over** `COINCIDENTAL`
  while `stale_coincidences` iterates a generator **over** `COINCIDENTAL` and
  filters against a comprehension over `derived_citations(root)` — a textbook
  mirror that a string comparison sees as four unrelated expressions. `core_name()`
  compares AST accessors instead. Sixth consecutive cycle whose first-draft scan
  was wrong about its own population; **second** in the over-inclusive direction.
- 🔴 **Six false guards on the first draft**: `run.main`,
  `dispatch_divergence.dispatch_fingerprint`, `horizon_audit.cruise_ceiling` and
  three more, all `if key in ('a','b')` **dispatches** with nothing iterated. A
  filter site with no population removes no member of anything — now a scan rule,
  and pinned by name so the vocabulary cannot silently re-admit them.
- ⚠️ **The unwatched-allow-list finding is module-layer only and is reported that
  way.** Three `TYPED` allow-lists (`DEGENERATE_READINGS`, `SCOPED_CLAIMS`,
  `TEMPERATURE_RELEVANT`) have no module-level function enumerating them — but
  all three are named in `tests/`, and `SCOPED_CLAIMS` is compared against
  `instrumented_claims()` *there* rather than in a module function. "No watcher
  in the layer this scan reads" is true; "unchecked" would be false.
  `test_layer_mentions()` ships so the weaker claim sits next to its own limit.

## North-star delta

- **No avoidance or tracking number moved — sixteenth consecutive instrument
  cycle.** Scenes able to contribute an avoidance number: 5, reportable: 4 — unchanged.
- What moved: Q-063 is answered at its own lean, and the answer bounds the
  D-047 class at one member instead of leaving it an open worry across 23 guards.

## Key learnings

- **A negative from a scan is worth exactly what the scan's correctness is worth** —
  so this cycle spent more effort pinning the two first-draft errors than
  producing the finding. The one-element answer is only meaningful because the
  population it is small in is 23 and derived.
- **"Who watches the allow-list" is the wrong question; "who watches the act" is
  the right one.** Two watchers were not enough because both watched the wrong
  verb. This generalises past D-011: a registry can be watched, complete, and
  derived, and still be broken through the one operation nobody enumerated.
- **Revocability is a property of the population's *shape*, not the guard's
  subject.** Difference-populations need a mirror; enumeration-populations do
  not. That is a cheap rule for future guards to be checked against at write time.

## Recommended next 1–3 priorities

1. **Enumerate the *acts* each guard watches, not the sets** — the natural
   successor, and the half this cycle proved is where the failure lives.
2. **Score the `TYPED` exemptions for bite** (`INERT` = D-046's coincidence
   shape). `bite()`/`unbitten()` ship; the pairs are derived but unscored.
3. Unchanged: the merge queue. Sixteen instrument cycles cannot run the re-baseline.

## Artifacts

- PR: #67 (existing; 43rd consecutive cycle writing into it)
- Files touched: `eval/mppi_sandbox/guard_reflexivity.py`,
  `eval/mppi_sandbox/tests/test_guard_reflexivity.py`, `docs/decisions.md`,
  `docs/deliberations.md`, `results/p3-epistemic-shadow-cost-critic.tsv`
- TSV row appended: yes

# The citation list was 6 of 17, and the sixth was load-bearing elsewhere

- **Cycle**: 2026-08-03 23:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: STATE #1 — enumerate the next hand-maintained registry
- **Phase**: P4 (calendar) / P3 work (instrument)
- **Status**: keep

## What I tried

- STATE #1 named two hand-typed registries and predicted both short. Took
  `claim_scope`'s, which has two layers: the **claim set** (5 typed claims) and,
  inside each claim, the **citation list** — "every place in `docs/` that states
  a number for it", 6 entries total across 5 claims, three of them `()`.
- Derived each layer instead of trusting it. `instrumented_claims()` walks
  `dispatch_divergence`'s own members for `_foo() -> Claim`; `derived_citations()`
  scans both `SCANNED_DOCS` section-by-section for any banked reading.
- Registered what the scan found, stamped the sections that needed it, and
  pinned the population as an invariant (`unregistered_citations()` must be empty).

## What worked / what failed

- ✅ **The claim-layer half caught nothing, and is reported that way.** 5 = 5 = 5.
  It closes the route where a `_foo() -> Claim` nobody added to the hand-written
  `CLAIMS` dict would be invisible to *both* registries — the existing test only
  compared `SCOPED_CLAIMS` against `CLAIMS`, which is one hand-typed list checking
  another. Purely prospective, same shape as D-045's glob half.
- 🔴 **The citation half: 6 registered, 17 actual.** Eleven sites across seven
  sections, **nine of them carrying no oracle stamp**. The sharpest is **D-034** —
  the excursion table that tabulates *every* contested reading at once
  (`1.30078`, `1.69563`, `0.251146`, `2.0375`) and was in no citation list, so no
  guard required it to name the machine those four numbers are conditional on.
- 🔴 **The first matcher was fail-open in the direction that deletes evidence.**
  A boundary-safe substring rule (`(?<![\d.])spelling(?![\d])`) correctly refuses
  `1.301` inside `11.301` — D-038's own bug, quoted verbatim in D-038's own
  section — but the right boundary *also* refuses a section stating the reading
  to **more** digits. D-034 writes `0.251146` where the registry banks `0.2511`,
  so the rule hid the single most important section. Reported 7 sites; the fix
  (numeric comparison at 3-s.f. tolerance) reported 11. Fourth consecutive cycle
  where the first draft of a scan under-counted.
- 🔴 **Registering the finding broke a downstream consumer, and that is the
  cycle's second finding.** `citation_audit._sites_from_claim_scope()` lifts
  horizon citations into sites for the `2.0×` amplitude. That was sound only
  while *every* citation on that claim was `other-quantity` — which is exactly
  what D-036 concluded — so "all of them" and "the ones stating 2.0×" were the
  same tuple and the missing filter was invisible. Eleven `instrument` citations
  later, six sections stood registered as restating a magnitude they never write,
  and two tests went red naming them. **A coincidence was holding a filter's
  place.**
- ✅ Three claims had `citations=()`. None of them actually had zero.
- ⚠️ `hazard_shared_rungs` reads 1.0/0.0 — unscannable, since those render as
  bare `1` and `0`. Declared in `DEGENERATE_READINGS` and asserted non-empty, so
  "no unregistered citations" is never read as a statement about it (D-042).
- ⚠️ Three matches are genuine coincidences (`2.038` = `TIMING_RATIO_BAND`'s edge
  in D-023/D-024/D-025, colliding with `exposure_band_hi` at 4 s.f.). Declared
  with reasons in `COINCIDENTAL`, and `stale_coincidences()` guards the
  declaration from outliving its match. The population is derived; only the
  rejections are typed.

## North-star delta

- **No avoidance or tracking number moved — fourteenth consecutive instrument
  cycle.** Scenes able to contribute an avoidance number: 5, reportable: 4 —
  unchanged.
- What moved: nine doc sections that stated a dispatch-fragile reading with no
  machine stamp now carry one, including the table that states all four.

## Key learnings

- **A hand-written list can be short in a layer nobody was looking at.** D-044
  and D-045 each found a *flat* list short. This one was short at the second
  level — the claim set was complete and the per-claim citation lists were not —
  so "check the registry" would have passed. The prior now extends: enumerate
  every level of a nested registry, not just the outer one.
- **An invariant that holds by coincidence is indistinguishable from one that
  holds by construction, until you break the coincidence.** `_sites_from_claim_scope`
  had no `kind` filter because D-036's finding made the filter a no-op. Fixing an
  under-count elsewhere is what revealed it.
- **The direction of a scan's bug matters more than its size.** The boundary rule
  was *correct* about `11.301` and wrong about `0.251146`; the correct half
  protects against a false positive, the wrong half deleted the best evidence.
  Fourth cycle running with this exact asymmetry.

## Recommended next 1–3 priorities

1. **Enumerate `tree_provenance.DECLARED_LOCAL_ONLY`** — the other half of STATE #1,
   untouched this cycle. Derive from *who writes it*: scan `scripts/` for tracked
   paths under full overwrite, diff against the 5 typed entries.
2. **Audit the remaining registries for coincidence-held invariants**, now that one
   has been found: any filter whose predicate is currently true of every element.
3. Count distinct `(scenario, controller, seed, params)` tuples across the 30
   D-042 lower-bound sites (Q-062's static half) — unchanged, still unpicked.

## Artifacts
- PR: #67 (existing — 41st consecutive cycle writing into it, no new review bandwidth)
- Files touched: `eval/mppi_sandbox/claim_scope.py`, `eval/mppi_sandbox/citation_audit.py`, `eval/mppi_sandbox/tests/test_claim_scope.py`, `eval/mppi_sandbox/tests/test_citation_audit.py`, `docs/decisions.md`
- TSV row appended: yes

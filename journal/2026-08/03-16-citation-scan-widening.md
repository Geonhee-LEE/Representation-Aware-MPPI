# Widening the citation scan: the pattern lost a site, and the flood never came

- **Cycle**: 2026-08-03 16:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: STATE #1 — extend the citation scan to bare magnitudes (collides with Q-057)
- **Phase**: P3
- **Status**: keep

## What I tried

- Lifted D-037's stated limit: `citation_audit` keyed on the `N.NN×` spelling, so a
  magnitude written bare in a table was invisible. Widened to bare decimals over the
  *same* scan surface — a controlled comparison where only the spelling changes.
- Built the candidate ranking Q-057 wanted *before* widening: 7 declared, weighted
  signals (`multiplication_sign`, `instrument_keyword`, `unit_suffix`, `assignment`,
  `denominator`, `comparator`, `precision_mismatch`) with the reason readable at each hit.
- Declared `EXCLUDED_SURFACES` (`journal/`, `RESULTS.md`, `STATE.md`) with the reason
  for each, since D-037's finding was that a registry fails by never looking at a surface.
- 16 new tests (312 → 328 fast), all string/arithmetic — no simulation, so the guard
  is not itself dispatch-fragile (D-033).

## What worked / what failed

- 🔴 **The widened pattern was not a superset of the narrow one.** The natural bare
  pattern ends `(?![\w.])` to keep `1.301` out of `11.301`; ASCII `x` is a `\w`, so it
  rejects `2.320x` — the spelling `exposure`'s docstring actually uses. Widening
  *lost* a citation, failing open, the same direction as D-037's regex-vs-`ast` bug.
  The sign has to be consumed as an optional suffix. Now asserted over the real scan
  surface rather than an example string.
- 🔴 **The flood Q-057 was scoped around did not arrive: 5 new sites across 6 claims.**
  The alarming `2.0` count (10 → 40) is *raw occurrences*; one section restates a
  number many times and the unit a registry tags is a **site**. The question priced
  the cost in the wrong unit.
- ✅ **All 5 are false positives, none subtle** — `≥ 2.0 s`, `w_speed = 2.0`,
  `1.46 / K=256`, `2.00 및 4.66`. So the `×` spelling was missing **no** citation here.
  A negative about this repo, not the method, and knowable only because the scan ran.
  Pinned as a test so a later cycle does not re-widen from the same suspicion.
- 🔴 **The ranking's first two drafts fired on *positives*.** `:` counted as assignment
  matched `결과: **6.19×**` — how half this repo introduces a result — cancelling
  `multiplication_sign` and dropping four genuine citations to 0.0. Then `/` read as a
  ratio bar mis-scored `6.19×/1.46×`, a citation *pair*. Rule that fixes both:
  disqualifiers apply to **unmarked** occurrences only. Final separation: registered
  **3.0–4.0** (n=74) vs unregistered **max 0.0** (n=12), no overlap.
- ⚠️ **1 of 12 rejections is by silence, not evidence** — D-038's own bare mention of
  `2.0` while narrating the count. Scored 0.0 with no signal either way. The 11:1
  split is pinned rather than asserted away.
- ✅ **The guard fired on its own author four times** — module docstring, D-038, Q-057,
  and the bullet describing the ranking fix each had to be registered before the
  suite went green.

## North-star delta

- **No avoidance or tracking number moved — seventh consecutive instrument cycle.**
  Scenes able to contribute an avoidance number: 5, reportable: 4 — unchanged.
- What it buys is narrow and real: the last stated hole in the citation guard is
  closed, and closed with a measured verdict (nothing was hiding there) rather than a
  widened net that would have fired on `w_speed = 2.0` forever.
- Honest: this is the third consecutive cycle spent on the *reporting* surface rather
  than the planner. The 가려진-obstacle class still has exactly one working cost term.

## Key learnings

- **A signal that fires on the positives is worse than one that fires on the
  negatives.** The second lengthens a list; the first silently disarms the guard. Both
  ranking bugs were of the first kind, and only an ordering test caught them.
- **Widening a detector is not monotone.** "More permissive pattern ⇒ superset of hits"
  is false as soon as the narrow pattern *consumes* a character the wide one uses as a
  boundary. Any widening should assert the superset relation on real data.
- **Estimate cost in the unit the system acts on.** Q-057 feared 40 hits; the registry
  tags sites, of which there were 5. The lean was right for a reason that was wrong.
- **An undeclared exclusion is indistinguishable from an oversight** — the direct
  corollary of D-037, now encoded as `EXCLUDED_SURFACES` plus a test that the excluded
  surfaces really do state the magnitudes.

## Recommended next 1–3 priorities

1. **Re-measure the self-vs-baseline denominator gap at the shipped `lam = 0.1`**
   (D-028's read suggests the verdict flips there) — unpicked for nine cycles, and the
   citation-guard thread is now finished rather than merely paused.
2. **Reproduce D-030's redundancy on a second scene** before Q-052's lean becomes a
   tool default.
3. **Extend the excursion sweep to the other 122 closed-loop tests** — belongs on the
   re-baseline branch (#15), not stacked here.

## Artifacts

- PR: [#67](https://github.com/Geonhee-LEE/Representation-Aware-MPPI/pull/67) (already in queue — no new review bandwidth)
- Files touched: `eval/mppi_sandbox/citation_audit.py`, `eval/mppi_sandbox/tests/test_citation_audit.py`, `docs/decisions.md` (D-038), `docs/deliberations.md` (Q-057 filed + resolved)
- TSV row appended: yes (`sandbox:pass=328/328`, keep)

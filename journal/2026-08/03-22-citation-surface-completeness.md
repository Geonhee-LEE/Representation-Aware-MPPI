# The scan surface was two hand-written lists, and both were short

- **Cycle**: 2026-08-03 22:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: STATE #1 — give `SCANNED_MODULES` auto-discovery (Q-056's mechanism)
- **Phase**: P4 (calendar) / P3 work
- **Status**: keep

## What I tried

- Replaced `citation_audit.SCANNED_MODULES` — a hand-written 11-tuple — with
  `scanned_modules()`, a glob over `eval/mppi_sandbox/*.py`. This was the whole
  of the STATE #1 ask.
- Doing it raised the obvious next question: a glob over *one directory* is
  still a hand-drawn surface. So I added `unaccounted_surfaces()`, which
  enumerates `git ls-files` and requires every tracked file stating a
  registered magnitude to be **either** scanned **or** excluded-with-a-reason.
- Registered what that found; declared what should be excluded.

## What worked / what failed

- ✅ **Auto-discovery works and changes nothing today.** It adds 12 modules to
  the surface and finds **zero** new enforcing hits. The honest report is that
  it is a purely *prospective* fix: it closes Q-056's mechanism, and it did not
  catch anything that was already wrong.
- 🔴 **The completeness pass is where the finding was.** Four tracked surfaces
  stated a registered magnitude while being neither scanned nor declared:
  `JOURNAL.md` (26 hits), `results/*.tsv` (10), `research/feed.md` (2), and
  `eval/requirements-ci.txt` (1).
- 🔴 **The shape repeats D-044 exactly, one cycle later.** The exclusion list
  named **two** of D-011's **three** snapshot files — `RESULTS.md` and
  `STATE.md`, omitting `JOURNAL.md`. D-044 found D-011's own local-only list
  naming three of five. Two hand-maintained lists, two undercounts, same week,
  neither found by re-reading the list. `results/` is sharper still: it is
  named inside `RESULTS.md`'s exclusion *reason* ("generated from
  `results/*.tsv`") while absent from the list that reason belongs to. The
  reason was written down; the surface it applies to was not.
- 🔴 **`eval/requirements-ci.txt` is a live citation, and the only one that
  mattered.** Its pin-rationale comment states D-030's headline swing as
  "**2.0x** under 1.26.4 and **1.029x** under 2.5.1" — a restatement of a
  *dispatch-fragile* claim, in the file that decides which numpy CI installs.
  If D-030 is ever rescoped the way D-039 rescoped D-028, this is where the
  superseded reading survives, attached to the thing that decides whether the
  number is reproducible at all. Now scanned (`SCANNED_TEXT`) and registered.
- ✅ **A pre-existing meta-test caught the widening, and the fix was
  vocabulary rather than a bigger threshold.** Auto-discovery pulled
  `speed_audit.py` into the surface, whose docstring states D-024's median-ESS
  fact as "**1.46 of K = 256**". D-024 writes the identical fact as "1.46 /
  K=256" and it was already a registered `denominator` rejection — so the prose
  spelling scored 0.0 with *no signal at all*, tripping
  `test_rejections_split_into_by_evidence_and_by_default` (silent bucket 3 > 2).
  That test exists precisely to catch the ranking getting the right answer for
  no reason. Raising its threshold would have muted the check that found the
  gap; I extended `_DENOM_AFTER` to read the prose spelling instead. **No
  verdict changed** — both spellings were rejected before and after.
- ⚠️ `tracked_files()` **raises** (`SurfaceEnumerationError`) when git is
  unavailable rather than returning `[]`. `unaccounted_surfaces()` passes when
  empty, so a soft failure would read as "every surface is accounted for" —
  D-042's rule, applied at the one place in this module that could violate it.
- 🔴 **D-043's re-run went red on this cycle's own decision entry — the rule
  working, observed rather than argued.** After writing the signal fix above I
  measured **414 passed**. The mandated re-run *after* the doc writes returned
  **413 passed, 1 FAILED**: the D-045 section quotes the ESS fact as
  `**1.46** of K = 256` (bold closing at the number) where `speed_audit` writes
  `**1.46 of K = 256**` (bold spanning both), and the regex I had just added
  read only the second. **The section describing the fix tripped the fix.**
  Gave the signal the same `` [`*"']* `` markdown tolerance `_ASSIGN_BEFORE`
  already carried, added a regression test, re-ran: **415 passed**. Without
  D-043's rule this branch would have pushed a red suite under a journal
  claiming 414.

## North-star delta

- **No avoidance or tracking number moved — thirteenth consecutive instrument
  cycle.** Scenes able to contribute an avoidance number: 5, reportable: 4 —
  unchanged.
- What moved: the citation registry is no longer bounded by what someone
  remembered to type. One previously-invisible citation of a dispatch-fragile
  claim is now under guard, in the file that configures CI.
- Fast half: **415 passed** / 135 skipped / 1 xfailed (was 407), +8 tests.
  Re-taken after the doc writes per D-043; the pre-write reading was 414 and
  the first post-write reading was red.

## Key learnings

- **Enumerating a list is how you find it was short — twice now, two different
  lists, two cycles running.** Neither undercount came from auditing the rule;
  both fell out of being forced to write the list down as code. That is now a
  strong enough pattern to act on: the remaining hand-maintained registries in
  this repo should be assumed short until enumerated.
- **A declared exclusion is better than an undeclared one, but it is still
  hand-maintained.** D-037's "declare your exclusions" was right and
  insufficient — it fails one level up, silently, at whichever surface nobody
  thought of. The fix is not a longer list but an invariant over the *tree*.
- **Citations live outside prose.** Every registry here assumed a claim gets
  restated in docs or docstrings. The one live find was a requirements file.
  Config, CI, and pin-rationale comments are citation surfaces.
- **When widening a surface trips a meta-test, the meta-test is usually
  right.** The cheap move was `<= 3`; the correct move was to give the new hit
  the reason its identical twin already had.
- **D-043 stopped being a precaution and became a finding.** Two cycles ago it
  was inferred from a commit's history; this cycle it caught a live red on the
  author's own prose, one write after the author had described the mechanism.
  The gap between "measured" and "shipped" is one paragraph wide.

## Recommended next 1–3 priorities

1. **Count distinct `(scenario, controller, seed, params)` tuples across the 30
   D-042 lower-bound sites** — Q-062's static half; prices the re-run in sims.
2. **Enumerate the next hand-maintained registry** — `claim_scope.SCOPED_CLAIMS`
   and `tree_provenance.DECLARED_LOCAL_ONLY` are both hand-typed, and the last
   two cycles say to expect them short.
3. **Reproduce the D-039 flip on a second scene** before "prefer the baseline
   denominator" becomes a rule.

## Artifacts

- PR: #67 (already in queue; 40th consecutive cycle adding no new review bandwidth)
- Files touched: `eval/mppi_sandbox/citation_audit.py`,
  `eval/mppi_sandbox/tree_provenance.py`,
  `eval/mppi_sandbox/tests/test_citation_audit.py`, `docs/decisions.md`
- TSV row appended: yes

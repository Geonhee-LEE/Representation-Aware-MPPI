# Q-083: `PUBLISHED` is a sample of 5 in 18, and the verdict survives every spelling

- **Cycle**: 2026-08-05 07:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: STATE #1 — Q-083, count how many of the 76 decisions printed a per-site magnitude
- **Phase**: P3
- **Status**: keep

## What I tried

- Built `eval/mppi_sandbox/magnitude_census.py`: split `docs/decisions.md` into its
  76 `D-NNN` sections, scan each for integers printed within one line of one of
  `published_ratios.SITES` (short names **derived** from that tuple, not retyped —
  D-047), and compare the decisions that print magnitudes against the four
  `PUBLISHED` transcribes.
- Refused to stop at the crude count. D-076 lost a cycle to deciding "is this
  magnitude one of this record's readings" on the **value alone**; a site-adjacent
  integer is not a reading either. Three discriminators, each mechanised:
  **novelty** (first appearance of a `(site, value)` pair in decision order —
  separates taking a reading from re-quoting one), **qualification** (`` `lam_dependence._pure` ``
  vs bare `` `_pure` ``), and **crosstalk** (another site's name between the anchor
  and the digit).
- Ran the census's own shopping list against the record and acted on the one
  entry that was checkable in-cycle.
- Paid the D-043/D-044 re-take after the doc writes.

## What worked / what failed

- 🔴 **Answer: SAMPLE. 18 of 76 decisions print a site-adjacent magnitude;
  `PUBLISHED` transcribed 4.** So D-075's `8/23`, `5/23` and `4/5` are ratios over
  a population nobody had sized, exactly as D-076 suspected when it found the
  typed exemption removing 0 of 22.
- ✅ **The count is unstable and the verdict is not — that is the finding.**
  Permissive spelling: 18 printing decisions. Strict (`clean` = qualified and
  crosstalk-free): **8**. Neither is right. The permissive one over-counts —
  D-050/D-051 discuss `_is_set_valued` as a *predicate under construction* and the
  nearby integers are D-numbers and cycle counts, magnitudes of nothing. The
  strict one under-counts — it drops **D-070 and D-071, the two licensed readings
  the entire record is built out of**, because this branch's prose spells sites
  bare. Under **all four** spellings the transcribed set is smaller than the
  printing set and uncovered decisions carry novel values. D-076 had to stop
  because its answer depended on the spelling; this one does not.
- 🔴 **The census paid for itself in-cycle, and it caught a false sentence with a
  test pinning it.** `published_ratios`'s docstring opened by claiming the
  source-frame control is "published for **zero** sites on **zero** trees", and
  `test_the_source_frame_control_was_never_published_on_any_tree` asserted
  `all(c.source_delta is None for c in PUBLISHED)` — passing for six cycles not
  because no cycle published one but because **this record had not transcribed
  the cycle that did**. D-068 published three (`_pure` 40, `_is_structural` 41,
  `_has_git_diff_literal` 28, each against its own 69-tree exclusion control).
  Transcribed now; `unverified()` re-locates all three; the claim is narrowed to
  "zero **licensed** sites on zero **licensed** trees", which is what does the
  downstream work and is unchanged.
- ✅ **Nothing licensed moved.** `common_sites(both_frames=True)` still `()`,
  `answerable` still n=2/n=0, every D-075 count bit-identical (8/23, 4/5, 3
  marginal). The omission's cost was a wrong sentence, not a wrong number — but it
  could have been either, and no one would have known.
- 🔴 **D-076's own headline was a ratio over an incomplete population too.**
  `exemption_bite()` 0 of 22 → **0 of 25**. Numerator held at 0, so the vacuity
  finding survives and is now measured over more of the population. D-076's pin
  demanded that a cycle changing this "should have to say so"; it did, in a
  direction D-076 had not thought to watch (it predicted `(1, 23)` from
  transcribing D-074).
- 🔴 **The scan's precision is 21/289 clean (7%)** — reported as integers, not
  conceded in prose. 262 bare, 116 crosstalk. Bare spelling dominates, and that
  matters: crosstalk is a property of the scan and could be narrowed, bare
  spelling is a property of the **document** and cannot be without rewriting six
  cycles of prose. Pinned by test in both directions.
- 🔴 **One real defect found in my own first draft by its own test.** The integer
  pattern copied from `published_ratios._mentions` rejects a number at the end of
  a sentence; harmless in a *verifier* (a miss raises a false alarm), silently
  shrinking in a *census*. Cost 5 pairs and 1 novel magnitude once fixed.

## North-star delta

- **No avoidance or tracking number moved — forty-fifth consecutive instrument
  cycle.** Scenes able to contribute an avoidance number: 5, reportable: 4 —
  unchanged. Zero new runs, zero sim time.
- What moved: the branch now knows the size of the population its published
  ratios are fractions of, and one sentence that six cycles of tests had
  certified as true is false and fixed.

## Key learnings

- **A guard can be vacuous because its population is a sample, and D-076 found
  the vacuity without finding the sampling.** Measuring a filter's bite is the
  cheap check; measuring its *population* is the one that says whether the bite
  means anything. Twelve uncovered candidates remain.
- **A test can pin a false sentence indefinitely if the sentence is about the
  record and the test reads only the record.** `all(c.source_delta is None for c
  in PUBLISHED)` is true of the transcription and says nothing about what was
  published. Self-referential verification has this failure mode structurally.
- **When two spellings of a filter disagree, check whether the verdict does
  before spending the cycle choosing.** D-076 spent a cycle on the choice. Here
  the choice was equally unresolvable and equally real, and the conclusion did not
  need it.
- **Census cost, twentieth consecutive cycle, but of a new kind.** Predicate
  population **85**, of which 3 are this cycle's (`SiteMagnitude.clean`,
  `Uncovered.candidate`, `Census.is_census`). `exemption_masking.candidates()` = 7
  with **0** from this module — the census's booleans narrow against dataclass
  fields, not against a registry, so this cycle adds predicates and no guards. I
  did **not** re-take D-076's "63" figure: its instrument needs a full suite run
  and the budget went to the census. Stated rather than quoted stale.

## Recommended next 1–3 priorities

1. **Read D-067's 14 novel magnitudes** — the last uncovered candidate that is
   clean under every spelling (5 clean pairs). Either they are the two-frame fold
   control's readings and `PUBLISHED` is missing a third reading, or they are not,
   and either answer shrinks the 12.
2. **Give the census a quantity key.** The one thing it declines to do is classify
   a magnitude by *what it measures*, and that is why 12 candidates cannot be
   resolved to a number. `Manifest.published_as` (D-076) is the field; nothing
   writes it for a decision.
3. **Apply `exemption_bite`'s question to the other typed exemption sets**
   (`CARRIED_FIELDS`, `EXCLUDED_TESTS`, `NAME_SCOPE_CLAIMS`, `SCOPED_CLAIMS`,
   `DEGENERATE_READINGS`, `TEMPERATURE_RELEVANT`) — unchanged from last cycle and
   now with a second reason: their populations are unsized too.

## Artifacts

- PR: #67 (existing — 72nd consecutive cycle writing into it, no new review bandwidth)
- Files touched: `eval/mppi_sandbox/magnitude_census.py` (new),
  `eval/mppi_sandbox/tests/test_magnitude_census.py` (new),
  `eval/mppi_sandbox/published_ratios.py`,
  `eval/mppi_sandbox/tests/test_published_ratios.py`,
  `eval/mppi_sandbox/tests/test_magnitude_survival.py`,
  `docs/decisions.md`, `docs/deliberations.md`
- TSV row appended: yes

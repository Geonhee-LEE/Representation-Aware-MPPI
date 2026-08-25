# Q-082: derive the exemption, or watch it — and the answer is neither

- **Cycle**: 2026-08-05 06:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: STATE `Next claude-actionable` #1 — Q-082, derive `SELF_DEFINING` instead of typing it
- **Phase**: P3
- **Status**: keep

## What I tried

- Took Q-082's lean (b) at face value and started to implement it: recompute
  `magnitude_survival.SELF_DEFINING` from the D-074 record instead of typing the
  triple, so the fourth unwatched exemption stops being one.
- Before replacing the typed set, measured what it actually removes:
  `exemption_bite()` → **0 of 22**.
- Implemented the derivation in **both** spellings — `SPELLING_ENDPOINT` (the
  wording Q-082 used: value equals its band's `lo`/`hi`) and
  `SPELLING_REPLICATE` (value equals any per-replicate reading) — and measured
  the difference between each and the typed set (`over_derivation`).
- Added the field the measurement said was missing:
  `reading_record.Manifest.published_as`, defaulting to `""`, read with `.get`.

## What worked / what failed

- 🔴 **The typed exemption has never removed anything.**
  `published_ratios.PUBLISHED` transcribes D-066/D-069/D-070/D-071 and contains
  no D-074 cell, so the triple names a value outside the population it filters.
  D-075's test for it — "no D-074 value survives" — passed **vacuously**. This is
  the vacuous-oracle class the feed flagged (cycle 023), found inside this
  branch's own guard rather than in a paper.
- 🔴 **Q-082's lean (b) is refuted as stated.** Value-equality alone excludes 1
  published gap under the endpoint spelling and 2 under the replicate spelling,
  and **all of them are false positives**: D-069's `_shells_out_to_git_diff` gap
  of 9 coincides with this record's band `hi` of 9 across two different trees.
  Gaps here are single- and double-digit integers; collision is the default case.
  The endpoint set is a strict subset of the replicate set, so the choice between
  spellings is a choice of how wrong to be, not whether.
- ✅ **Ratios collide zero times under both spellings** — the same mechanism from
  the side where it does not bite, which pins the defect as *small-integer*
  rather than general. Worth having: it stops a future cycle reading
  "derivation over-derives" as a law.
- ✅ **The repair is one key, not a fifth guard.** Deciding "is this magnitude one
  of this record's readings" needs the value *and* the claim the record was
  published as. `published_as` supplies the second; a provenanced record derives
  exactly (verified by constructing the transcription `PUBLISHED` is missing and
  watching the derivation catch it with no typed triple involved).
- ✅ **Every D-075 count is bit-identical** under the new `published(record=...)`
  signature — 8/23, 4/5, 3 marginal, `_pure` 0/6 — because this record is
  unprovenanced and takes the fallback. Pinned by a test rather than asserted.
- 🔴 **The refactor made `provenance_depth_exposure` positive for the first
  time** — the instrument shipped eighteen cycles ago as a re-derived zero, with
  a note that "extract the registry behind a helper" is exactly the edit that
  turns it positive. It was. D-052 (b) had already written the repair down
  (*name the helper's registry at the call site*), so it was applied rather than
  absorbed: `self_defining(record, cells, SELF_DEFINING)`, exposure back to `()`.
  **The repair fixed one scan of two** — `_provenance` reclassifies TYPED, the
  shallow scan still stops at the call — so D-075's 3-to-1 deep/shallow split is
  now 5-to-0.
- 🔴 **Census cost: guard pool 60 → 63**, nineteenth consecutive cycle. Q-082 set
  out to avoid adding a fifth watcher and the measurement cost three guards.
  `unscreened` also goes 1 → 2, and the second instance shows `UNRUNNABLE` marks
  *guards with a required argument*, not *expensive guards* — the first instance
  had an interesting cause and that hid the dull general one.

## North-star delta

- **No avoidance or tracking number moved — forty-fourth consecutive instrument
  cycle.** Scenes able to contribute an avoidance number: 5, reportable: 4,
  unchanged.
- What moved: one of this branch's own guards was measured and found to be firing
  on nothing, and the proposed fix was measured and found to fire on the wrong
  things. Both were one join away the whole time.

## Key learnings

- **A guard can be correct and vacuous at once, and this branch has been checking
  only the first.** D-075 wrote the exclusion, wrote a test for it, and the test
  could not have failed. The cheap discriminator is not "does the guard pass" but
  "how many rows does its filter remove" — two integers, and `exemption_bite` now
  reports them.
- **The reason the exemption was vacuous is a population defect, not a guard
  defect.** `PUBLISHED` transcribes 4 of 76 decisions. That makes D-075's
  denominator of 23 a number nobody has shown to be a census — filed as **Q-083**,
  and it is the more consequential half of what this cycle found.
- **"Derive it from the record" is only safe when the record carries the key the
  derivation needs.** D-047's lesson ("do not hand-type a registry") does not
  imply every hand-typed set should be recomputed; it implies the recomputation
  must key on something discriminating. Here the discriminating key did not exist
  and the value was standing in for it.

## Recommended next 1–3 priorities

1. **Q-083 — count how many of the 76 decisions printed a per-site magnitude.**
   Static, no sim, and the count itself says whether D-075's 8/23 is a census or
   a convenience sample.
2. **Re-run the batch at k≥5** and re-grade D-075's three marginal survivors
   (1.009× / 1.023× / 1.047×). ~8 min of compute; still the only thing that turns
   "8/23 or 5/23" into one number.
3. **Apply `exemption_bite`'s question to the other typed exemption sets** —
   `CARRIED_FIELDS`, `EXCLUDED_TESTS`, `NAME_SCOPE_CLAIMS`. If any of them also
   removes 0 rows, the unwatched-exemption census has been counting decorations.

## Artifacts

- PR: #67 (open, seventy-first consecutive cycle writing into it)
- Files touched: `eval/mppi_sandbox/magnitude_survival.py`,
  `eval/mppi_sandbox/reading_record.py`,
  `eval/mppi_sandbox/tests/test_magnitude_survival.py`,
  `docs/decisions.md` (D-076), `docs/deliberations.md` (Q-082 resolved, Q-083 filed)
- TSV row appended: yes

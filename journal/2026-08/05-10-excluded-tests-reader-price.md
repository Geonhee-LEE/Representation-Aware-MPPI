# Q-085 answered by reader price — and D-079's "exactly one place" was the scan dropping the module

- **Cycle**: 2026-08-05 10:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: STATE #1 — answer Q-085 (the two `EXCLUDED_TESTS` registries)
- **Phase**: P3
- **Status**: keep

## What I tried

- Ran Q-085's **own** stated decision procedure instead of re-arguing it: *does a
  cheap non-subprocess reader exist?* Mechanised as `reader_cost()` (each reader
  priced `PURE`/`SUBPROCESS`, transitive within its module) + `affordable_readers()`.
- Fixed `references()` to attribute reads by **resolved owning module** — import
  aliases resolved, unresolvable loads reported by `unresolved_reads()` rather
  than guessed.
- Acted on the split: made `exclusion_scope.price` a call-time read + shipped its
  tamper (pv); declared `guard_vacuity.EXCLUDED_TESTS` in `DECLARED_DEF_TIME`
  with `undeclared_unreachable()` guarding the declaration (gv).

## What worked / what failed

- 🔴 **D-079's published magnitude was wrong, and the cause was in the code, not
  the prose.** `references()` read `_, name = registry` — the module component
  was **discarded**, so both `EXCLUDED_TESTS` registries received the *union* of
  each other's reads as byte-identical tuples, and the smaller reading ("each is
  read in exactly one place") got printed for both. True of gv (1 reader); false
  of pv (**17**, across four modules). The `UNREACHABLE` verdicts survive — both
  were `DEF_TIME` — but that was luck, and a synthetic control now reproduces the
  case where it is not (`a.REG` CALL_TIME vs `b.REG` DEF_TIME, name-keying can't
  tell them apart).
- ✅ **Q-085's premise did not survive being measured.** It assumed both readers
  run a suite. pv has **15 pure readers**; gv has **zero**. So (a) is affordable
  for one and dead-by-its-own-rule for the other — the answer is a split, and
  Q-085's lean toward (b) was right only for gv.
- 🔴 **`python -m exemption_control` misgraded this module's own registry `INERT`**
  while a normal import read `BITES` — `importlib.import_module` loads a second
  copy under the dotted name when the file is running as `__main__`, so the
  tamper patched an object no reader could see. A negative control whose verdict
  depends on how it was launched. Fixed (`_live_module`), pinned by subprocess test.
- 🔴 **Census cost, twenty-second cycle running**: the new excuse list
  `DECLARED_DEF_TIME` is itself a typed exemption set — `unwatched_exemptions`
  went 4 → 5 within one test run of its being written. Answered with a tamper,
  not an exception (REGISTRIES 8 → 9, TAMPERS 7 → 8).

## North-star delta

- **No avoidance or tracking number moved — forty-eighth consecutive instrument
  cycle.** Scenes able to contribute an avoidance number: 5, reportable: 4 —
  unchanged. The 가려진-obstacle class still has exactly one working cost term.
- What moved: 8 of 9 typed registries now carry a runnable negative control (was
  6 of 8), the 9th is declared with a machine-checked reason, and one published
  count from the previous cycle is retracted with its mechanism fixed.

## Key learnings

- **A magnitude published by an instrument is only as good as the instrument's
  key.** D-078 taught "date the quote"; this cycle the quote was fresh and still
  wrong, because the *scan* conflated two things sharing a name. Re-taking the
  count would never have caught it — only asking what the count was keyed on.
- **A question's premise is worth measuring before its trade-off is argued.**
  Q-085 wrote a cheap decision procedure and then leaned on an unmeasured
  premise; running the procedure took minutes and inverted half the answer.
- **"Fix or declare" is a false binary for a *population* of registries.** The
  right unit is per-registry, and the deciding variable is the cost of the
  cheapest reader — which is mechanically derivable.

## Recommended next 1–3 priorities

1. **Apply `reader_cost` to the other seven registries** — any whose only readers
   are `SUBPROCESS` are controls that exist on paper but never run.
2. **Audit the package for other name-keyed scans** — `references()` was not
   unique in dropping a qualifier; the same `_, name = registry` shape elsewhere
   would produce the same union bug (STATE #8's blind-spelling scan is adjacent).
3. **Read D-067's 14 novel magnitudes** — still the last uncovered census candidate.

## Artifacts

- PR: pending merge (`autoresearch/p3-epistemic-shadow-cost-critic`, PR #67)
- Files touched: `eval/mppi_sandbox/exemption_control.py`,
  `eval/mppi_sandbox/exclusion_scope.py`,
  `eval/mppi_sandbox/tests/test_exemption_control.py`,
  `docs/decisions.md`, `docs/deliberations.md`
- TSV row appended: yes

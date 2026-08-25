# Serialise the reading — and the ordinary spelling of a registry is invisible

- **Cycle**: 2026-08-05 03:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: STATE #1 — `results/*.json` from `paired_reading` / `replicated_reading`
- **Phase**: P3
- **Status**: keep

## What I tried

- Built `eval/mppi_sandbox/reading_record.py`: `Manifest` / `Record` /
  `to_record` / `write` / `read` / `agreement` / `comparable` / `ratios` /
  `take_and_record`. One licensed reading in, one JSON file out; every
  downstream reading (`ratio_grades`, `ratio_ranking`, `rank_agreement`)
  re-derivable from the file with no run and no retyping.
- Made the **schema derived, not typed**: `CELL_FIELDS` is read off
  `FrameAttribution` with `dataclasses.fields`, so a field added to the grader
  is a field the record carries in the same commit (D-047's lesson).
- Answered Q-079 by refusing its shape: the record stores **both** frame deltas,
  so either denominator is a view (`Record.ratios(DENOM_BOTH | DENOM_MEASURED)`),
  and the manifest **declares** which one the cycle reported. A reading does not
  have to pick; it has to say. `comparable()` refuses to correlate two records
  that declared different denominators.
- Adapted CrowdSkill's five-field run manifest (feed 08-05 00:00) field by field,
  including the one that does not fit: there is **no seed schedule**, and
  `Manifest.entropy` says so in the file — process addresses are the unseeded
  entropy that produces the whole 7-site disagreement set.
- **Zero new runs.** 23 new tests, all fast.

## What worked / what failed

- ✅ **Sufficiency is proven, not asserted**: the load-bearing test is that
  grades computed from the file are `==` to grades computed from the live
  reading, over a synthetic reading exercising FOLD / DRIFT_UNDER /
  DRIFT_COVERS / TRANSPORTED. A partial parse and an unknown schema both raise.
- ✅ **Q-078 is now one licensed batch from answerable.** `agreement(a, b)` takes
  two files. `test_agreement_over_two_sites_is_still_refused` pins that the
  record does **not** launder D-072's negative — n=2 stays `rho=None`.
- 🔴 **The coverage check I wrote first under-reported itself, by 2 of 16.**
  `would_have_carried` keyed on `CELL_FIELDS` and reported 14 of the 16 dropped
  cells, because two were published as `gap` — and `gap` is a *property*, not a
  stored field. The record stores primitives; prose quotes derivations. Fixed by
  deriving `DERIVED_FIELDS` from the dataclass's properties too, and pinned.
- 🔴 **And that fix exposed the cycle's real finding, measured both ways.**
  `CARRIED_FIELDS = CELL_FIELDS + DERIVED_FIELDS` is a `BinOp` of two names, so
  `guard_reflexivity._is_set_valued` does not see a registry, and
  `would_have_carried` — an ordinary `in`-shaped filter against it — **does not
  enter the guard pool**: 54, not 55. `tuple(CELL_FIELDS + DERIVED_FIELDS)` is
  the identical value through a `_SET_CALLS` call, and the pool reads 55. Same
  guard, same registry, same sense, two spellings, one visible. Ran it both ways
  in-cycle rather than arguing it.
- 🔴 **This is worse than D-072's version of it.** D-072 found the detector reads
  the `&` operator rather than semantics, with `&` vs `set.intersection` as the
  two spellings — one of which is unusual. Here the two spellings are `A + B`
  and `tuple(A + B)`, and the **invisible one is how a registry assembled from
  two other registries is normally written**. The blind spot is reachable by
  writing the idiomatic thing.
- 🔴 **Making the registry visible cost a second guard.** A visible-but-
  unenumerated TYPED allow-list is an *unwatched* one — D-047's exact state —
  so `unwatched_exemptions` went 3 → 4 the moment the spelling was fixed, and
  `uncarried_fields` had to be written to close it. Pool 55 → **56**. Its
  exempting set is `DERIVED` (a `dir()` over a round-tripped cell), so
  `CARRIED_FIELDS` is watched by a measurement rather than by a copy of itself.
- 🔴 **Three suite failures, all real, all fixed at the cause.**
  `unwatched_allow_lists` (the hole above), and two in `exemption_masking`:
  `would_have_carried` graded `UNRUNNABLE` because its only parameter had no
  default — a guard nothing can call is a guard nothing screens for an inert
  exemption — and the TYPED-pair route count 14 → 15.

## North-star delta

- **No avoidance or tracking number moved — forty-first consecutive instrument
  cycle.** Scenes able to contribute an avoidance number: 5, reportable: 4 —
  unchanged. Zero runs bought.
- What moved: the seam D-072 identified as the cause of six uncheckable cycles
  is closed **forward**. The next licensed batch produces a file, and the one
  after it makes Q-078 a two-line call instead of six cycles of transcription.
- What did **not** move, and is stated in code rather than in prose:
  `unrecoverable()` returns all 16 dropped cells. No format adopted today
  recovers one of them.

## Key learnings

- **A record stores primitives; a reader quotes derivations.** Any coverage
  check keyed on storage names under-reports by exactly the quantities anyone
  actually cites. This cost 2 of 16 here and would have looked rigorous.
- **The guard detector keys on the *form* of a constant's initializer, not its
  value.** D-065 said "it misses parameterised narrowings", D-066 said "and
  per-member folds", D-072 said "no — it reads the `&` operator". The general
  statement is: it reads syntax, and the idiomatic spelling of a composed
  registry is on the wrong side of it. Every "exactly N" this pin has carried is
  a count of the guards that happened to be spelled visibly.
- **Closing an audit hole costs a member.** Making one registry visible added
  two guards — the guard itself, and the watcher its new visibility demanded.
  That loop is the package in miniature and it is not obviously convergent.
- **Q-079 was the wrong shape of question.** "Which denominator" only needs
  answering if the artifact stores one. Store both, declare which was reported,
  refuse to correlate across a mismatch.

## Recommended next 1–3 priorities

1. **Buy one licensed batch through `take_and_record`** and write the first real
   record. That single call turns STATE #2 from "then re-read the ratios" into a
   file, and the batch after it answers Q-078 at n=7.
2. **Re-derive every "exactly N" bound in `docs/decisions.md`** — now with a
   reason stronger than drift: this cycle showed the guard-pool counts are
   counts of *visible spellings*, so they are not the quantity the prose claims.
3. **Ask `_is_set_valued` whether the same blind spot hides existing guards.** A
   package-wide scan for `NAME = A + B` module constants used in `in` / `not in`
   filters is static and cheap, and would say whether 56 is short.

## Artifacts
- PR: #67 (existing, autoresearch/p3-epistemic-shadow-cost-critic)
- Files touched: `eval/mppi_sandbox/reading_record.py`,
  `eval/mppi_sandbox/tests/test_reading_record.py`,
  `eval/mppi_sandbox/tests/test_guard_reflexivity.py`,
  `eval/mppi_sandbox/tests/test_exemption_masking.py`
- TSV row appended: yes

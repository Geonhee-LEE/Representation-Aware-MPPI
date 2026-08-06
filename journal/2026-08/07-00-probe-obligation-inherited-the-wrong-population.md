# The probe obligation was inherited from a pool that counts spellings

- **Cycle**: 2026-08-07 00:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: `state-01` Write the two `guard_direction.PROBES` entries (STATE #1)
- **Phase**: P5
- **Status**: keep

## What I tried

- HEAD was red on 4 failed + 5 errors, all of it one bill: `guard_direction`'s
  standing rule — every revocable guard has a probe — fired on the two guards
  D-105 added, and two cycles (D-103/D-104) sat unpushed behind it.
- Went to write two probe entries. **They were not the same debt.**
  `cycle_artifacts.report` returns `str`; there is no reading to ask "does it
  name the offence" of. `cycle_artifacts.unsupported` returns cycles and is a
  real guard whose offence is simply not D-011's.
- So: (1) narrowed the *obligation*, not the census — `Guard.reading`
  (`COLLECTION`/`SCALAR`, off the return annotation), `revocable_collections`,
  and `unprobeable_revocable` as the enumerator that counts the exclusion;
  (2) gave `Probe` its own `subjects` / `build` / `permit` / `offend`, because
  `readings()` was looping `DECLARED_LOCAL_ONLY` for *every* guard;
  (3) threaded `root` through `cycle_artifacts` and wrote the probe.

## What worked / what failed

- ✅ The probe reads what D-105 could only argue. Two subjects, two verdicts:
  the offence both dating keys agree on → **NAMES_OFFENCE**; the offence a
  retroactively-appended row hides from the `records` key → **SILENT**. The
  intersection's cost is now a measurement taken in a scratch repo with the two
  git dates pinned apart, not a caveat in a docstring.
- ✅ The exclusion is not reverse-engineered from the guard it drops: 8 of 84
  pool members have a scalar reading and only 1 of them is revocable. Pinned.
- 🔴 The loop over `DECLARED_LOCAL_ONLY` would have committed `STATE.md` at a
  guard about journal files and scored it blind to an offence that is not its.
  Two guards enforcing one rule cannot distinguish "the paths this rule covers"
  from "the paths every rule covers"; the third guard is what made the
  assumption visible, and it was three lines of loop.
- 🔴 **`NO_SCOPE` went 0 → 2, and the zero was never about `acts_of`.**
  "Scope is the layer that loses nobody" held for a pool of 16 that all happened
  to perform a git act. `unsupported`/`unsupported_by` do their I/O two frames
  down, so `acts_of` yields nothing — and they are precisely the guards this
  cycle had to probe by hand. **Q-100.**
- 🔴 Second-order cost, four places, all paid rather than papered: pool 81 → **84**, the third
  member being `probe_reach.misscored_probes` — nine cycles old, and made visible
  by binding its filter set to a local (D-073's syntax result, again);
  `probe_reach` addressable 16 → **22** (six `cycle_artifacts` guards became
  reachable *because* the module learned to take a `root` — nothing to do with
  what they filter, and the derivable numerator stayed at 4); `probe_reach`'s
  ground truth narrowed from `PROBES` to `shared_fixture_probes()`; the
  `liveness_derivation` yield is now zero **while the typed table grew**, which
  is the direction that makes Q-068's negative stronger.

## North-star delta

- **No avoidance or tracking number moved — seventy-second consecutive
  instrument cycle.** Scenes able to contribute an avoidance number: 5,
  reportable: 4 — unchanged.
- What moved: HEAD is green and the branch is pushed, so **D-103, D-104 and
  D-105 have left the machine** for the first time in four cycles. That is the
  condition the last two cycles set out to clear and did not.
- The 가려진-obstacle class still has exactly one working cost term (D-027).

## Key learnings

- **An obligation derived from a syntactic pool inherits the pool's
  over-match.** `revocable` is deliberately a count of visible spellings
  (D-072/D-073) and is right to be; the probe obligation read it as a list of
  things that can be executed. Deriving the population is D-045's lesson, and
  this is its cost: you also inherit what the source was never asked to exclude.
- **A rule with one enforcer cannot show you its own scope.** The subject-space
  bug survived because two guards enforced D-011 and a third did not exist.
- **A repair must be spelled so the census charges for it.** Writing
  `unsupported_by` as a call into `_flagged` (not a second copy of the grading)
  keeps the exemption `DERIVED` and `unwatched_exemptions` at five — and the
  function still enters the pool, which is the payment, not the disappearance
  D-104 warned about.

## Recommended next 1–3 priorities

1. **Pay the mirror debt** (STATE #2, still open) — `disputed` is
   `unsupported`'s natural mirror but is spelled `^` where it is `&`.
2. **Answer Q-099** using the two keys' disagreement, now that a fixture can
   *construct* a retroactive row — the hard part of that question just got a
   test harness.
3. **Run `cycle_artifacts` in the push gate**, not only as a test.

## Artifacts

- PR: #67 (existing — no new review bandwidth)
- Files touched: `eval/mppi_sandbox/cycle_artifacts.py`,
  `eval/mppi_sandbox/guard_direction.py`, `eval/mppi_sandbox/guard_reflexivity.py`,
  `eval/mppi_sandbox/probe_reach.py`, `eval/mppi_sandbox/tests/test_guard_direction.py`,
  `eval/mppi_sandbox/tests/test_guard_reflexivity.py`,
  `eval/mppi_sandbox/tests/test_liveness_derivation.py`,
  `eval/mppi_sandbox/tests/test_probe_reach.py`, `docs/decisions.md`,
  `docs/deliberations.md`
- TSV row appended: yes

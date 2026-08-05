# Negative controls for all seven typed exemptions — two of them cannot be controlled through their own name

- **Cycle**: 2026-08-05 09:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: STATE #1 — apply the negative-control pattern to the other six typed exemption sets
- **Phase**: P3
- **Status**: keep

## What I tried

- Built `eval/mppi_sandbox/exemption_control.py`: for each typed registry, tamper
  it and assert some integer reading moves in the declared direction. D-076
  measured *bite* for one set (does the filter remove anything **now**); this
  measures *wiring* (would tampering it move anything **at all**), which is the
  half that turns a passing test vacuous.
- Made it **two-layer**, static first: an AST pass classifies every read of the
  registry's name as `CALL_TIME` or `DEF_TIME`, because a registry with no
  call-time read cannot be reached by any monkeypatch of its name — and that
  decides whether the dynamic layer means anything.
- Shipped the module's own negative control in the same commit (D-078's rule):
  a no-op patch must grade `INERT`, and a move in the **wrong direction** must
  also grade `INERT`.
- Updated the pinned guard-pool tally and its running prose.

## What worked / what failed

- ✅ **8 registries: 6 `BITES` / 2 `UNREACHABLE` / 0 `INERT` / 0 uncontrolled.**
  Deltas pinned individually (+1, +1, −2, +2, +1, −2) — the verdict alone would
  pass for a reading that moved by zero in a set that happened to be empty.
- 🔴 **The finding is structural, not per-registry.** `predicate_vacuity.
  EXCLUDED_TESTS` and `guard_vacuity.EXCLUDED_TESTS` are each read in exactly
  one place, and that place is `excluded: Sequence[str] = EXCLUDED_TESTS` — a
  **default argument**, evaluated at `def` time and bound into the function
  object. Rebinding the global afterwards is unobservable to every caller, so
  no monkeypatch of those names is a control. The only way in is `excluded=`,
  which controls the *parameter*, not the *registry*.
- ✅ **This weakens D-076, correctly.** `SELF_DEFINING`'s control reads `0 → 1`:
  the filter **is** wired, and its zero bite is a fact about the population, not
  about the code. "The filter does nothing" was the stronger reading and it is
  not the true one. One measurement could not tell those apart; two can.
- 🔴 **D-076's published `0 of 22` is `0 of 25` today** — `PUBLISHED` grew three
  cells afterwards. The test derives the denominator from `len(PUBLISHED)`
  instead of re-typing it, so it stays green when the registry does its job.
  D-078's rule obeyed rather than cited, one cycle later.
- 🔴 **Census cost, and it is the cheapest instance yet**: guard pool **64 → 65**,
  twenty-first consecutive cycle — but only **one of three** population-shaped
  functions entered. `uncontrolled` narrows by `not in`; `inert` and
  `unreachable` narrow by **equality against a verdict string** and are
  invisible. Same kind of function, one visible spelling. `unwatched_exemptions`
  held at **4**, `exemption_masking.candidates()` held at **7**.
- 🔴 The four registries this module controls are **exactly** the four
  `unwatched_exemptions` lists. A control is not a watcher — pinned by test so
  the census is not misread as having closed D-073's hole.

## North-star delta

- **No avoidance or tracking number moved — forty-seventh consecutive instrument
  cycle.** Scenes able to contribute an avoidance number: 5, reportable: 4,
  unchanged.
- What moved: six of the package's typed exemptions now have a falsifiable
  negative control, and two are known to be uncontrollable through their name.
- The 가려진-obstacle class still has exactly one working cost term (D-027).

## Key learnings

- **Bite and wiring are different measurements and this branch had been
  conflating them.** A filter that removes 0 members may be correct, unwired, or
  pointed at the wrong population; only tampering tells you which.
- **A registry consumed solely as a default argument is decorative at every site
  but its own.** Nothing in the package's guard machinery could have said this —
  `exemption_masking` suppresses a *derived pair* and never asks when the name
  is bound.
- **The guard-pool detector's syntax dependence reproduced with the cleanest
  control yet**: three sibling functions, one difference in spelling, one
  visible. No appeal to registries or per-member folds needed this time.

## Recommended next 1–3 priorities

1. Decide whether the two `EXCLUDED_TESTS` registries should be read at call
   time (`excluded or EXCLUDED_TESTS` inside the body) so a control exists, or
   whether the default-arg binding is declared as intended. Currently neither.
2. Read D-067's 14 novel magnitudes — still the last uncovered census candidate
   clean under every spelling.
3. Widen `magnitude_census.quoted()` beyond the canonical spelling, or declare
   it won't be — D-077's *title* still states its verdict in unpoliced prose.

## Artifacts

- PR: #67 (open, 24 days)
- Files touched: `eval/mppi_sandbox/exemption_control.py`,
  `eval/mppi_sandbox/tests/test_exemption_control.py`,
  `eval/mppi_sandbox/tests/test_guard_reflexivity.py`, `docs/decisions.md`
- TSV row appended: yes

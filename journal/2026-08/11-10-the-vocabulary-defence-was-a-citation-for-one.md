# The vocabulary defence was a citation for one of them and an assertion for the other

- **Cycle**: 2026-08-11 10:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: STATE #1 — decide `guard_vacuity.never_fired` / `predicate_vacuity.one_sided`
- **Phase**: P5
- **Status**: keep

## What I tried

- Took STATE #1 on its 3rd recommendation: keep both accessors as the reading's
  stated vocabulary, or delete both and fold the rationale into the docstring.
- Applied D-186 (4th consecutive cycle) and measured the premise before writing
  to it. STATE's wording was a paired claim — "one-line accessors **their own
  module docstrings name** as the reading's vocabulary" — so the check was
  mechanical: does each module docstring cite its accessor?
- Measured the candidate key package-wide before keying anything on it, per
  D-193: `:func:` self-citation covers 117/740 public module-level functions
  (15.8%), bare mention 234/740 (31.6%).

## What worked / what failed

- **The premise was half false, and false on exactly the pairing.**
  `guard_vacuity` cites `:func:`never_fired`` in the module docstring section
  explaining why it returns candidates rather than findings. `predicate_vacuity`
  cites its *siblings* — `:func:`unpatchable``, `:func:`calibration_census`` —
  and never `one_sided`, not by `:func:` and not in prose. The accessor that is
  the module's reading went unintroduced for as long as it existed.
- So the two were never one case: one had a real defence, the other had the
  same sentence said about it. Nothing in the package could tell them apart,
  which is why three cycles of STATE restated the pairing without testing it.
- **Cut on the clock (D-181).** The obvious watcher — a package-wide dangling
  `:func:` reference check — was measured and refused: 40 unresolved refs under
  the narrow same-module scope, nearly all legitimate (test modules citing their
  subject, source modules citing siblings). Shipping it needed carve-outs the
  budget could not hold, and a check that ships with a carve-out list is the
  fifth unwatched allow-list this package keeps growing.
- Instrument pre-check ran first again: 118 passed in 27s, green, so no second
  full suite. 4th consecutive cycle honouring D-044's ordering table.

## North-star delta

- **No movement, and this cycle claims none.** No controller, representation,
  dynamics or sim code; 0 sim runs. `unsafe_rate`/`min_clearance`/`success_rate`
  unchanged, census attribution coverage still 0/6, `NO_GRADED_RUNG`.
- What moved: 2 of the 9 residue members now hold a **checked** verdict instead
  of a restated one, and the residue is split by whether the defence is even
  available — 4 of the remaining are cited by nothing at all.

## Key learnings

- **A premise that pairs two things is two claims, and cheap to check.** The
  paired form — "both X, because both Y" — hid a false half for three cycles at
  a cost of one AST pass to falsify. D-186 keeps paying on the sentence's
  *shape*, not just its content.
- **The fix for an unbacked defence is to write the thing it claims exists, not
  to drop the claim.** `one_sided` genuinely is the module's vocabulary; what
  was missing was the paragraph saying so. Deleting it would have destroyed a
  real reading because its documentation was incomplete.
- **A defence has to cost something to be a defence.** "The docstring names it"
  was free while nothing checked it. Now deleting either the function or its
  citation goes red, so the keep-verdict is enforced in both directions and can
  no longer spread to neighbouring residue members by proximity.
- The D-193 trap did not apply here but was checked: this is not an exemption
  that grades anything. It cannot hide a finding — both functions stay in the
  residue, still uncalled, still red.

## Recommended next 1–3 priorities

- Triage the 4 uncited residue members (`asserts_in`, `build_stranding_repo`,
  `format_scan`, `reprobe`) — the vocabulary defence is provably unavailable to
  them, so each owes a different argument. 0 sim.
- `magnitude_survival.standings` / `predicate_vacuity.unpatchable` /
  `calibrate_lam.scene_is_calibratable` are cited but were never triaged under
  this rule — one AST pass decides whether they join `VOCABULARY_DEFENCE`.
- Add the instrument pre-check to the constitution's Phase-3 step — 7th time
  recommended, paid again this cycle (27s vs a 19m red suite).

## Artifacts
- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic)
- Files touched: eval/mppi_sandbox/predicate_vacuity.py, eval/mppi_sandbox/tests/test_consumer_reach.py, docs/decisions.md
- TSV row appended: yes

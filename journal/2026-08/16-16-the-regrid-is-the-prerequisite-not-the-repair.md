# The re-grid is the prerequisite, not the repair

- **Cycle**: 2026-08-16 16:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: `3bec5d39` re-read-span-consumers-against-n32
- **Phase**: P3
- **Status**: in_progress (finding complete; **not pushed** — two self-caused pins red)

## What I tried

- STATE named this cycle verbatim: D-303 moved the span-disqualification
  boundary, several verdicts still quote the old crossing, so re-read
  `k_axis_bracket` and `attribution_separability` against `K_COLUMN_ROWS_N32`
  (`n_required=32`) and record which payload fields change. Zero runs.
- Read both consumers on both grids and diffed the payloads. Ten fields moved.
- **Did not stop there.** The matched grid is three columns and the full axis is
  nine, so every field differs for two reasons at once — the ensemble doubled
  *and* the grid lost six columns. Added the control D-303's own test already
  uses one layer down: the same three columns at `n = 16` (`SUB16`), grid shape
  held fixed, ensemble the only thing moving.
- Pinned the result as `test_the_matched_grid_cannot_re_read_the_span_consumers_only_the_boundary`.

## What worked / what failed

- **The re-read does not repair anything, and the control is what shows it.**
  Of the ten moved fields, **two** are the ensemble — `inadmissible_k`
  `(192,)` → `(176, 192)` and `interior_inadmissible_k` `()` → `(176,)` — and
  those are D-303 restated through the consumer, not a new fact. The other
  eight are **identical** between `SUB16` and `n32`: truncation had already
  changed all of them and the ensemble touched none.
- **The verdict flip is not a re-reading of the boundary.**
  `K_BRACKET_CLOSED_SAME_EDGE` → `K_BRACKET_OPEN_BELOW` happens because `160`
  is the lowest column walked at 32 seeds (`run_bounds_open_intervals[0] is
  None`), not because the same edge was re-measured.
- **The attribution question is not expressible on the matched grid at all** —
  `SEPARABILITY_NOT_APPLICABLE` at *both* ensemble sizes, because the run
  collapses `{96, 128, 160}` → `{160,}` and the decomposition needs a window
  shape three columns cannot supply. The ensemble never gets to matter.
- Failed to repair D-301's `UNTESTABLE` leg, which was the point of the cycle.
  It survives, for a reason worth having: the grid that could decide it is the
  grid that cannot express it.
- Caught one trap: `membership_monotone` flips `False` → `True`, purely a
  3-point-grid artifact on `(32, 29, 29)`. Quoting it as an axis property would
  assert something the 9-column axis explicitly denies.

## North-star delta

- **No movement in any robot-facing number, and none was reachable.** Still one
  scene (`cafe_freezing_v0`), still `transfers_to_ab_scene = False`, still
  blocked on PR #68 for any A/B reading. Zero sim runs this cycle.
- What moved is an **ordering correction**: STATE had the re-read preceding
  further bisection; it is the other way round. That redirects the next cycle
  from a repair that cannot work to the extension that unblocks it.
- Eight truncation effects were one function call away from being recorded as
  D-303 follow-on findings.

## Key learnings

- **A re-measurement that changes grid *and* ensemble can report neither effect
  without a control that separates them.** The control cost one call — same
  columns, different `n_required`. D-019(b)'s "compare only within a population"
  extended to the *two* axes of population: which columns, how many seeds.
- **`NOT_APPLICABLE` at both ensemble sizes is the informative answer**, not a
  null result: it says the question is about grid shape, so no amount of seeds
  at these three columns will reach it.
- The expensive failure mode here is a diff that confirms what you expected.
  D-303's boundary move *is* in this payload, and reading the diff looking for
  it would have made the other eight fields look like its consequences.

## What stopped the cycle

- The suite came back `3408 passed, 2 failed` and **both failures are this
  cycle's own doing** — adding one test moved two registry pins, precisely what
  `inert_surface staged` predicted with `STAGED_MOVED` before the first commit.
  - `test_key_discrimination` — `attribution_separability` enters the narrow
    key's hit set as a fourth non-`LIVE` name. **Repaired** (`81625ed`), and the
    repair is itself a small D-196 data point: the key admits another unreached
    name on every cycle that adds a module.
  - `test_loop_reach::test_recorded_reading_covers_exactly_todays_targets` —
    `READING` must list the new test, and updating it requires re-running
    `loop_reach report`. **Not repaired**: the report is not the ~90 s I assumed,
    it re-runs the corpus under a plugin, and it was still going when
    `cycle_wallclock elapsed` returned `SUITE_UNAFFORDABLE`.
- At that point the honest options were to start a third suite well past the
  deadline or to stop. I stopped: `push_preflight` would refuse this tree anyway
  (D-082 — the receipt is red), and pushing red is the thing that gate exists to
  prevent. **The branch is committed locally and unpushed**, so next cycle's
  Phase 1 `cycle_artifacts stranded` will name it and clearing it is that
  cycle's first obligation — the designed path, not a silent loss.
- Cost accounting, since STATE asked for it: the citation-audit pre-check ran
  and was clean, so D-303's failure mode did not repeat. The one that bit
  instead was the *other* thing `STAGED_MOVED` warns about, and I read that
  warning as the familiar five-file noise rather than as "this cycle added a
  reader" — which is what it actually said.

## Recommended next 1–3 priorities

1. **Clear the strand first** — run `loop_reach report`, update `READING` with
   `test_the_matched_grid_cannot_re_read_the_span_consumers_only_the_boundary`,
   re-run the suite, push. Budget the report as a **full corpus pass**, not the
   ~90 s its docstring implies. Everything else waits on this.
2. **Respan `K = 128` at 32 seeds** (STATE's old #2, now the prerequisite) —
   restores a run on the matched grid and is the only thing that makes the
   attribution re-read expressible. ~17 runs, ~2 min.
3. **Then re-read the consumers again** with the 4-column matched grid; the
   control pattern from this cycle is the way to read it.

## Artifacts

- PR: #67 open; **this cycle's commits are not on it** (unpushed: `84b7600`, `81625ed`)
- Files touched: `eval/mppi_sandbox/tests/test_calibrated_ladder.py`, `eval/mppi_sandbox/tests/test_key_discrimination.py`, `docs/decisions.md`, `journal/2026-08/16-16-the-regrid-is-the-prerequisite-not-the-repair.md`, `results/p3-epistemic-shadow-cost-critic.tsv`
- TSV row appended: yes (`in_progress`, `sandbox:pass=3408/3574`)

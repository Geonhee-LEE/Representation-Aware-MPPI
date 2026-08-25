# Name what rolls out — the walk finds 84, and the clock reading is free

- **Cycle**: 2026-08-26 02:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: `Q-203` derive which lam tests actually roll out
- **Phase**: P3
- **Status**: in_progress (repaired; receipt + push discharged by the 03:00 cycle)

## What I tried

- Resumed the 01:00 cycle, which `cycle_wallclock` graded **KILLED**: it had left
  `eval/mppi_sandbox/lam_rollout.py` (383 lines) and its 12-test module complete
  and untracked on disk, with no commit. This cycle verified, repaired and shipped
  that work rather than re-authoring it.
- Verified the module's load-bearing premise before trusting it: `push_preflight`
  really does keep a `<out>.log` sidecar (`log_path`, line 650), so a
  `--durations=40` on the receipt run costs **zero** extra suite time.
- Ran the static walk: `derived_rollout_tests()` returns **84** tests reaching a
  rollout primitive, in ~0.1 s.
- Repaired the guard census the new module drifted (141 → 143) and took the
  receipt with `--durations=40` so `compare` has a measured side to read.

## What worked / what failed

- **The walk is a usable signal, and the keying is why.** The module's own
  docstring records that a bare-name call graph measured **2428 of ~4233** tests
  reaching a rollout — 57% of the suite, which is noise, caused by ordinary
  helper names (`run`, `report`, `build`) colliding across modules and welding
  the graph into one component. Keying on `module.func` costs an import table per
  file and gives 84. That is a markable population; 2428 is not.
- **`census_preempt` collected again, for the fourth recorded time.** It returned
  `guard_tally 143 vs pin 141 (+2)` in ~2 s at the stage. The entrants are
  `compare` and `reaching_names`, both D-050 set-valued spellings. Left unfound,
  that is a red in a 20.7-minute suite.
- **The tally moved by two for one module** — the running prose in
  `test_guard_reflexivity.py` has no prior instance of a +2, and it is D-073's
  caveat stated cleanly: the number counts *spellings*, and a module can ship two.
- **`inert_surface staged` fired rc=1**: the new reader withdrew the exemptions on
  all five snapshot pins (`JOURNAL.md`, `RESULTS.md`, `STATE.md`, `journal/`,
  `results/`). Under the D-315 order this costs nothing — every mandated write
  already precedes the receipt — but it makes "no write after the receipt" strict
  rather than merely advisable for this cycle.
- **The receipt came back red, and that is the cycle's real finding.** rc=1 —
  **4241 passed, 4 failed** in 1281.95 s. All four are censuses the new module
  joined, and all four sit in the population `census_preempt` names in its own
  `UNCOVERED` line: `guard_reflexivity` (AND-shaped set, +`compare`, 13th
  entrant), `liveness_derivation` (`NO_REGISTRY` 22 → **24**, the first +2 from a
  single module), `exemption_masking` and `predicate_depth` (both the same
  `provenance_depth_exposure` tuple, +`reaching_names`). The stage-time census was
  **8/8 CLEAN** and honest about it — it printed the four it does not read. I read
  that line and shipped anyway.
- **Q-067 re-opened as Q-204, because the code said it would be.** The
  `exemption_masking` docstring pinned decision (b)'s tenability on there being
  exactly **one** member and stated that a second entry re-opens the question.
  This is the second. The two differ in kind: `tail_stability.drift` had no
  exemption to mask, so the per-member argument was free; `reaching_names` carries
  a real one — the name-keyed walk deliberately drops calls it cannot resolve.
  What makes it tolerable is *direction*, not absence.
- **All four repaired and verified green individually (15.60 s). Not pushed.**
  A push needs a green **full-suite** receipt and at 37 min a second 21-minute
  suite is forbidden (D-181). Full-module verification of the four was attempted
  and blew past 400 s — Q-203's own pathology arriving inside Q-203's repair.
- **What did not happen: the install.** This cycle bought the *instrument* for
  enumerating the cascade, not the enumeration. D-457's 16+8 price is still
  unconfirmed, for a fourth cycle.

## North-star delta

- No rollout evidence and no controller code ran under evaluation. The P5 headline
  is still computed over 2/8 of the controller axis.
- What moved is the shape of the blocker, not its size: "the cascade cannot be
  enumerated" had no instrument attached to it for three cycles, and now has one
  that costs 0.1 s statically and 0 s measured. The install's remaining unknown is
  unchanged; the means of *seeing* it is new.
- P5 entry is 2026-09-03 — eight days.

## Key learnings

- **A KILLED cycle can leave good work, and nothing in the loop looks for it.**
  `cycle_artifacts stranded` covers finished *commits*; it is silent on finished
  *uncommitted files*, because an untracked path is not a strand by its
  definition. The 01:00 output was 505 lines of complete, tested, documented work
  that a fresh PLAN would have re-authored from scratch. This is D-315's shape
  (the receipt you already earned) one category over: the artifact you already
  wrote.
- **Verify the premise before shipping the instrument.** The module asserts that
  `push_preflight` keeps a sidecar log; if that were false, `parse_durations` and
  therefore `compare` would be dead code that still passes its own tests. It cost
  one `grep` to check and it held.
- **The cheap error direction was chosen deliberately and it is the right one.**
  The walk over-approximates (name-based resolution conflates same-named
  functions), so it can only ever *add* tests to the derived set. An over-mark
  costs one test in the slow lane; an under-mark costs the timeout that has now
  eaten three cycles.

## Recommended next 1–3 priorities

1. **Run `lam_rollout compare` against this cycle's receipt log** — the durations
   block now exists in `/tmp/suite-receipt.json.log`. `measured_only` is Q-203's
   actual answer and it is one command away, with no suite to pay for.
2. **Mark the compared set `@pytest.mark.slow` and re-attempt the install** — a
   marked population is what makes `-m "not slow"` separate table assertions from
   rollout assertions, which is the thing three cycles could not do.
3. **Correct the "2 controllers" figure** where D-471 / Q-202 prose repeats it —
   the variant is 3 controllers × 8 scenes. Still outstanding from 21:00.

## Artifacts

- PR: #67 open; this cycle's 3 commits were left unpushed (red receipt, then no budget for a second suite) and the 03:00 cycle discharged them via D-112 Step 0 — see `journal/2026-08/26-03-what-the-suite-actually-spends.md`.
- Files touched: eval/mppi_sandbox/lam_rollout.py, eval/mppi_sandbox/tests/test_lam_rollout.py, eval/mppi_sandbox/tests/test_guard_reflexivity.py, docs/decisions.md, docs/deliberations.md, results/p3-epistemic-shadow-cost-critic.tsv
- TSV row appended: yes

# The instrument asserted whose claim it was grading

- **Cycle**: 2026-08-11 21:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: `STATE #1` Pin `cycle_artifacts.claim`'s ordering precondition
- **Phase**: P3
- **Status**: keep

## What I tried

- Closed the trap 20:00 fell into: `cycle_artifacts claim`, run before the
  invoking cycle's 4a exists, fell through `_claim_rows` to `ordered[-1]` — the
  **previous** cycle's journal — and the CLI announced it as "the in-flight
  cycle's TSV claim", printing `yes` as the line to paste.
- Added `inflight_hour()` (reads the wrapper log's unpaired `start` marker via
  `cycle_wallclock.in_flight`) + `identification()` returning `IDENTIFIED` /
  `INFLIGHT_UNKNOWN` / `NO_INFLIGHT_JOURNAL`.
- `claim_support` / `claim_line` now consult it; the refusal is `REFUSED_LINE`,
  deliberately **not** a valid Artifacts line. CLI exits **rc=2** and names the
  journal it would otherwise have graded.
- 8 new tests pinning both directions + the existing CLI rc=1 test made
  hour-deterministic.

## What worked / what failed

- 🟢 The bug reproduces as a unit test: journal stamped `18:00`, hour in flight
  `19`, → `NO_INFLIGHT_JOURNAL`. That is the 20:00 signature exactly.
- 🔴 **The existing CLI test was reading the test runner's own cycle hour.**
  `main()` calls `claim_support(branch)` with `root=None`, so it consulted the
  live wrapper log; the test passed only because nothing had ever consulted that
  hour before. It now states the hour instead of inheriting it — otherwise the
  rc would depend on what time of day the suite ran.
- 🟢 The `root is not None ⇒ INFLIGHT_UNKNOWN` short-circuit is what keeps every
  other test deterministic: a `tmp_path` journal has no relationship to this
  machine's wrapper log, and joining them would grade one repo's hour against
  another's file.
- 🟡 The wall-clock reading was the operative constraint on scope. `elapsed`
  said `SUITE_AFFORDABLE` with a 9m32 window, which is what selected STATE #1
  over STATE #2 (receipt persistence spans three modules and would not have fit).

## North-star delta

- No movement. `unsafe_rate` 0.0000 · `min_clearance` 0.3579 · `success_rate`
  1.0000 all carried; 0 sim runs, no controller / representation / dynamics code
  touched. This is instrument repair.
- What it buys is record integrity: the failure it closes **manufactures
  permanent scars** — row assignment is by timestamp, so a `yes` pasted into a
  predecessor's journal cannot be repaired by any later cycle.

## Key learnings

- **An opt-in repair that the default path declines is not a guard.** `cycle_path`
  has existed since D-110 and its docstring already said "newest == the running
  cycle is only true after 4a has written the journal". The caller who needed it
  was precisely the caller who did not know to pass it. Writing the precondition
  down is not the same as enforcing it.
- **The instrument was not wrong about the rows — it was wrong about whose.**
  It counted correctly and then asserted an attribution it had not checked. A
  reading that names its subject in prose should be made to verify that name.
- **rc=2 vs rc=1 is the load-bearing distinction** (D-199's split, reused). The
  misattribution is cleared by writing 4a and re-running; the over-claim cannot
  be cleared at all. Folding them together would put a ten-second caveat in the
  same bucket as a permanent scar, and D-044 says that check gets muted.
- **A refusal that sits next to a usable line is not a refusal.** The failure
  mode was a *paste*, so `REFUSED_LINE` had to be unusable as one — a warning
  above a still-valid `yes` would have been read exactly as the old output was.

## Recommended next 1–3 priorities

1. **STATE #2** Persist the suite receipt across cycle boundaries
   (`results/readings/` keyed by head, not `/tmp`) — still the live bottleneck:
   the producer/repairer split is budget-driven, and a 20-min suite re-run to
   publish a predecessor's finished commit is the cost being paid.
2. Audit the other readings that name their subject in prose (`stranded`,
   `measurement`) for the same unverified-attribution shape D-202 closes.
3. **STATE #3** Triage `horizon_audit.format_scan` — closes 1 of 8 residue members.

## Artifacts

- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic)
- Files touched: eval/mppi_sandbox/cycle_artifacts.py, eval/mppi_sandbox/tests/test_cycle_artifacts.py, docs/decisions.md
- TSV row appended: yes

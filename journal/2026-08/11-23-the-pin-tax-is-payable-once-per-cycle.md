# The pin tax is payable once per cycle, and this strand owes it twice

- **Cycle**: 2026-08-11 23:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: strand repair (D-112 obligation, outranks the decision tree)
- **Phase**: P3
- **Status**: in_progress

## What I tried

- Took the D-112 stranding reading first: rc=1, one stranded cycle
  (22:00, `11-22-the-cache-must-be-invisible...`). `origin` sits at `f35e669`;
  two D-203 commits are local-only. Clearing it was this cycle's obligation.
- The 22:00 journal left a recipe: reprobe four stale pins, confirm `staged`
  clean, one suite via `push_preflight record`, TSV, push. **`reprobe` is not a
  CLI subcommand** — `inert_surface` exposes only `survey|pins|staged|probe`.
  It exists as a Python function, so I called it directly.
- Reprobed the two pins that could compose: `RESULTS.md` (gen 0) and `results/`
  (gen 1) — both `INERT_COMPOSED`, **3.6 s each**, single entrant
  `test_receipt_store.py`. Landed both pins.
- Started a full probe of `STATE.md` (gen 2 → falls back past
  `COMPOSITION_CAP`). Killed it at **25 min** without a verdict.

## What worked / what failed

- The composition path is as cheap as D-107 priced it: 3.6 s to discharge a
  stale pin whose entrant is one file. Two of four pins are now current.
- The fallback path is not affordable at all. `STATE.md`'s own pin note quotes
  15m45 for its last full probe; this one was still running at 25 min when I
  killed it to leave budget for the write-up. **Same surface, same single
  entrant, 3.6 s vs >25 min — decided only by which generation the pin sat on.**
- `cycle_wallclock elapsed` corrected me mid-cycle and it mattered: my own
  estimate said ~20 min elapsed when the instrument said 3m35. I would have cut
  scope on a wrong number. The CLAUDE.md warning that self-estimates run ~3×
  long is exactly right, and it runs long in the direction that *forfeits*
  budget.
- **Killing the probe left `STATE.md` mutated** with two `<!-- inert_surface
  probe -->` markers — the `finally` restore does not survive SIGTERM. I
  stripped them. A probe is not safely interruptible; that is a real hazard for
  any cycle that starts one it cannot finish.
- Not pushed. Two pins remain stale, so six `test_inert_surface` tests are red
  (58 passed / 6 failed) and `push_preflight` would refuse. The strand is now
  **two cycles deep**, and I added to it exactly as the D-112 text warns.

## North-star delta

- Zero movement toward the north star — pure automation-surface maintenance.
- Debt reduced, not cleared: 4 stale pins → 2. The remaining two are the
  expensive ones, so the *cost* remaining is more than half.

## Key learnings

- **The pin tax is a cliff, not a slope, and it is invisible at PLAN time.**
  "Add a module + tests" priced as cheap; it re-keyed four pins and two of them
  happened to sit at `COMPOSITION_CAP`. `cycle_wallclock` prices the suite and
  nothing prices this, which is precisely when a cycle commits to it.
- **A strand can be structurally unclearable.** Two CAP-ed pins (≥16 min each,
  non-resumable) plus a 1220 s suite cannot fit in one 35 min budget under any
  ordering. Minimum to clear: 3 cycles — probe A, probe B, suite+push. This is
  D-204, recorded as structure rather than bad luck.
- **A recipe written against a command that does not exist costs a cycle.** The
  22:00 journal's step 1 named `reprobe`; ten minutes of this cycle went to
  discovering it is a function, not a subcommand, and that its fallback is what
  makes step 1 unaffordable.
- The queue has not merged a PR since **2026-07-12 — 30 days**. Gate 1 reads 6
  (at cap). I proceeded anyway because this cycle creates no branch and no PR:
  it publishes into already-queued PR #67, so it adds zero review load. The
  last escalation was 47 h ago, inside the 72 h floor, so no new ping.

## Recommended next 1–3 priorities

1. **Probe `JOURNAL.md` full, land the pin, commit, stop.** One full probe is
   the entire affordable content of a cycle. Do not also attempt the suite.
   Start it in the first minute and do no repo writes while it runs — writes
   spoil the before/after comparison.
2. **Then a suite-only cycle**: `push_preflight record`, TSV row, push. That
   clears the strand at PR #67. Consult `receipt_store recall` (D-203) first —
   this is its first real use.
3. **Price the pin tax in `cycle_wallclock`.** Carried over from 22:00 and now
   with a measured ratio behind it (3.6 s vs >25 min). A PLAN-time reading that
   answers "what does adding a test file cost this cycle" would have stopped
   22:00 from starting work it could not land.

## Artifacts

- PR: pending merge (`autoresearch/p3-epistemic-shadow-cost-critic`, PR #67)
- Files touched: `eval/mppi_sandbox/inert_surface.py`, `docs/decisions.md`
- TSV row appended: yes

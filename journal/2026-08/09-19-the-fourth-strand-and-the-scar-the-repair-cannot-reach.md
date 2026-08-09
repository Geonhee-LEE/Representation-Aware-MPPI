# The fourth strand of the day — and the scar the repair cannot reach

- **Cycle**: 2026-08-09 19:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: D-112 strand clear (outranks the decision tree) — the 18:00 cycle
- **Phase**: P5
- **Status**: keep

## What I tried

- `cycle_artifacts stranded` opened the cycle at rc=1: the 18:00 journal
  (`09-18-the-last-scene-cannot-be-walked.md`) was finished work sitting on
  disk. `156f9f9` was committed at 18:07 and never pushed; `origin` still
  pointed at `c35e9c7`. Per D-112 that outranks PLAN, so this cycle cleared it
  rather than picking from STATE.
- The 18:00 commit is stamped `Metric: sandbox:pass=pending` — it never took a
  count. So clearing meant *grading the tree first*: `tree_provenance stamp`,
  then one `push_preflight record` run over the full suite, then the missing
  TSV row, then push.
- **Deliberately added no code.** STATE #3 (carry "unmeasured" in the strand
  verdict) was the tempting fold-in and would have invalidated the in-flight
  receipt, forcing a second ~16 min suite run inside a 35 min budget. A cycle
  that overruns while clearing a strand produces another strand.

## What worked / what failed

- **Cleared: 2068 passed on the 18:00 tree** (158 skipped, 1 xfailed, rc=0,
  receipt head `156f9f9`) — the count `156f9f9` never took. The **7** tests
  18:00 added (`test_margin_placement.py` + `test_scene_transplant.py`) had
  never been run by the cycle that wrote them.
- **One suite run, not two.** `inert_surface` (PROBED 2026-08-06) grades
  `journal/`, `results/*.tsv`, `JOURNAL.md` and `STATE.md` all `INERT`, and
  `push_preflight.check` filters drift through it — so a receipt taken before
  the REPORT writes survives them. D-044's "pay for it twice" tax is already
  paid off in code; this cycle is the first to *use* that rather than re-run.
- **This is the fourth strand today, and the third with the identical
  signature**: 09:00, 11:00 and 18:00 all read `UNSUPPORTED rows=0` — journal
  written claiming `TSV row appended: yes`, committed, then dead before the
  append and the push. The failure is not random; it is always the same two
  final steps.
- **The repair cannot reach the scar it repairs.** Row assignment is by
  timestamp, so the row I appended at 19:xx for `156f9f9` assigns to *this*
  cycle, not to 18:00. That is why 10:00 and 12:00 read `rows=2` while the
  09:00 and 11:00 cycles they rescued still read `UNSUPPORTED rows=0` —
  permanently. Three cycles today carry a scar no future cycle can clear.

## North-star delta

- **No movement on the headline, and none attempted.** No controller,
  representation, or dynamics code; no sim runs. `unsafe_rate` **0.0000** /
  `min_clearance` **0.3579** / `success_rate` **1.0000** unchanged.
- What moved is publication, not science: 18:00's finding — crossing is
  unwalkable 0/4, so the walkable-scene population closes at **2, not 3** — is
  now on `origin` and inside PR #67 instead of sitting on one laptop's disk.
- Suite grew 2061 → **2068**, i.e. exactly the 7 checks 18:00 wrote and left
  unrun. No parametrization multiplied them.

## Key learnings

- **An honestly-claimed strand is invisible to the gate, but a dishonest one is
  not — and today's are all dishonest in the same direction.** All three wrote
  `TSV row appended: yes` before appending it. The Artifacts line is written at
  4a from *intent*; the append happens two steps later. Writing that line from
  the actual append, not from the plan, would make the claim unfalsifiable-by-
  construction rather than routinely false.
- **STATE #3 is now motivated by an instance, not a hypothesis.** "Carry
  'unmeasured' in the strand verdict" has been deferred five cycles as a
  nice-to-have. `156f9f9` is the concrete case: stranded *and* `pending`, and
  the reading said only the former. Next cycle should ship it.
- **Repair timeliness has a hard deadline nobody was told about.** Because
  assignment is by timestamp, a strand repaired in the *same hour* would land
  on the stranded cycle; repaired an hour later it never can. That deadline is
  undocumented and was missed three times today.

## Recommended next 1–3 priorities

1. **Carry "unmeasured" in the strand verdict (D-156 follow-up)** — deferred a
   sixth cycle, now with `156f9f9` as the motivating instance. One field, one
   test. Ship it before any new science.
2. **Write the Artifacts TSV claim from the append, not from intent** — three
   identical false claims in one day is a generator, not an accident.
3. **Re-calibrate `cafe_obstacle_crossing_v0` at `w ∈ {150, 250}`** — the only
   route that reopens the third scene; the screen names those cells unmeasured
   rather than empty.

## Artifacts

- PR: [#67](https://github.com/Geonhee-LEE/Representation-Aware-MPPI/pull/67) (open, continued per D-140)
- Files touched: none — this cycle published `156f9f9`'s tree and appended its missing TSV row
- TSV row appended: yes

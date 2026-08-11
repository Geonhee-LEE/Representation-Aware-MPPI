# The red was one commit away — the stranded cycle inherited nothing, it added a reader

- **Cycle**: 2026-08-11 14:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: STATE #1 — clear the `inert_surface` STATE.md pin and decide D-044's ordering table
- **Phase**: P3
- **Status**: keep

## What I tried

- `cycle_artifacts stranded` fired: the 13:00 cycle's three commits (D-197,
  `key_discrimination.py` + 16 tests) never reached origin, and the tree was
  **ungraded** — so clearing it needed a suite run, not just a push.
- Before acting on the 13:00 journal's stated cause, checked it. It named the
  12:00 cycle's 4c `STATE.md` rewrite and escalated to "D-044's *read by no
  test* clause has decayed".
- Re-took the pin with `reprobe('STATE.md')` — the function D-196/D-197 spent
  two cycles arguing about whether anything called.
- Pinned the diagnosis as a **pair** of tests rather than a paragraph.

## What worked / what failed

- 🔴 **The stranded cycle's diagnosis was wrong, and self-exculpating in the
  one direction that mattered.** `stale_pins()` never reads the candidate's
  content — it compares `readers_key`, a **set of reader files**. A `STATE.md`
  rewrite therefore cannot stale a pin at any content. `entrants('STATE.md')`
  returns exactly one name: `test_key_discrimination.py` — the test module the
  13:00 cycle wrote **that same cycle**. The red was self-inflicted and one
  commit away, not inherited from an hour earlier.
- 🟢 **The trap is documented, which is why this is a decision and not a
  scolding.** `unstaged_readers` says it: the reader scan reads `git ls-files`,
  the *index*, so an unstaged new test is invisible — and that blind spot is
  aimed precisely at the reader-adding cycle, because that is the only kind
  whose pins can go stale *and* the only kind holding an untracked test file.
  13:00 read `stale_pins() == ()`, which was true when it read it, and `git
  add` made it false. Q-128 predicted this cycle in the abstract.
- 🟢 `reprobe('STATE.md')`: 1 entrant, **16 passed before and after** the
  mutation → `INERT_COMPOSED` gen-2, 22 readers carried. Seconds against
  D-183's 15m45 full probe. The instrument two cycles argued over got used for
  the thing it was built for, on the first occasion that called for it.
- 🔴 **Half of the 13:00 finding survives, and it is not the causal half.**
  "`STATE.md` is read by no test" *is* false — `test_the_real_repo_reading_is_current`
  reads it and `push_preflight` classifies it test-readable; the existence of
  `inert_surface` is the admission. But that falsity produced none of these 4
  red, and the implied remedy (move the 4c write) would have prevented none of
  them. Two mechanisms got folded into one because the same filename appears in
  both: `push_preflight` drift is **content**-keyed, pin staleness is **reader-set**-keyed.
- 🟢 Both directions are now pinned: the named cause is inert at any content,
  the real cause bites. Either test alone leaves "why was it red" unanswered,
  which is the exact question 13:00 got backwards.

## North-star delta

- **No movement, and this cycle claims none.** No controller, representation,
  dynamics or sim code; 0 sim runs. `unsafe_rate` / `min_clearance` /
  `success_rate` untouched, census residue still **8**. Suite green on the
  pushed tree: **2473 passed**, 158 skipped, 1 xfailed (20m15) — the 4 red are
  discharged and the two new pins are in that count.
- What moved: a 3-commit strand carrying D-197 is unblocked and graded, and a
  false cause is off the record before a cycle spent budget fixing the wrong
  ordering table.

## Key learnings

- **A cycle is the worst-placed observer of whether it caused its own red.**
  The blind spot here is not carelessness — the guard genuinely returned clean
  when consulted, and turned dirty at `git add`. So "did I add a reader?" has
  to be asked *after* staging, by name, not inferred from a pre-stage reading.
- **Same filename in two guards is not the same mechanism.** The 13:00 cycle
  read `push_preflight`'s "path a test can read (changed: STATE.md)" and
  `inert_surface`'s `PINS_STALE: STATE.md` as one finding. They key on
  different things; only one of them can be triggered by a content write.
- **Check the stated cause before inheriting the remedy.** The strand came with
  a diagnosis, a decision entry, and a recommended next action, all coherent
  and all resting on a premise the module contradicts in one line.

## Recommended next 1–3 priorities

1. **Ask the staged question, not the pre-stage one.** `pin_reading()` already
   carries `unstaged` as a separate reading; the gap is that nothing makes a
   reader-adding cycle *look* at it after `git add`. Cheapest real fix in this
   package right now, and D-198 is its motivating incident.
2. **Triage `horizon_audit.format_scan`** — carried unchanged from D-196/D-197:
   it builds a markdown table and its module docstring contains a table of that
   shape; the question is whether the shipped table was ever re-derived by this
   generator. D-107 / D-139 have answered this shape twice. Closes 1 of 8.
3. **Triage `assert_reach.asserts_in`** — the last member with no counterexample
   of the D-195/D-196 kind. (This and the Phase-3 instrument pre-check — 11th
   time recommended — carry again.)

## Artifacts
- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic)
- Files touched: eval/mppi_sandbox/inert_surface.py, eval/mppi_sandbox/tests/test_inert_surface.py, docs/decisions.md
- TSV row appended: yes

# The uncommitted cadence edit was blocking every push on this branch

- **Cycle**: 2026-08-29 20:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: `strand-discharge` Clear the 2-cycle strand named by `cycle_artifacts stranded`
- **Phase**: P5
- **Status**: keep

## What I tried

- Phase 1 Step 0 fired `rc=1`: two finished cycles (07:00 D-492, 08:00 D-493)
  sat on disk, 2 commits ahead of `origin`, never pushed. Per D-112 that
  outranks the decision tree, so the strand became the cycle.
- Before budgeting the suite, asked *why* two consecutive cycles both failed to
  push. `tree_provenance declared` answered: `UNDECLARED worktree-vs-HEAD drift`
  over 15 tracked files — `CLAUDE.md`, `README.md`, seven `docs/*`, five
  `scripts/*`, `journal/README.md`.
- Read the gate rather than assuming: `push_preflight.py:835` returns
  `UNDECLARED` — a **hard refusal**, ordered after the receipt checks — whenever
  worktree-vs-HEAD drift falls outside `DECLARED_LOCAL_ONLY` (5 paths).
- Committed the 15 files as one thrust and discharged the strand.

## What worked / what failed

- The drift is a single coherent edit: `hourly` → `twice a day` / `하루 2회`,
  53 insertions and 53 deletions, no other content. It is **true** — cron is
  `0 10,20 * * *` KST and `scripts/prompts/auto_research.md`, the contract this
  executor is literally running from, already said twice-daily. Only `main` still
  said hourly (`git show origin/main:CLAUDE.md | grep -c "twice a day"` → 0).
- So the branch was not stranded by budget overrun, which is what the two
  journals assumed. It was stranded by a gate that **no amount of care inside a
  cycle could clear**, because the blocking files were not that cycle's work and
  were invisible to every check it was told to run. `cycle_artifacts stranded`
  names the *symptom*; only `tree_provenance declared` names the cause, and the
  loop never routes a cycle to it before the push.
- `inert_surface staged` returned `STAGED_MOVED` (5 pins withdrawn). Harmless
  here: D-315's order already puts every REPORT write before the receipt, so the
  withdrawn exemptions cost no second suite. The pin withdrawal is a price the
  ordering had already paid for.
- `census_preempt`: 10 censuses re-derived, all clean.

## North-star delta

- **No movement on the north star.** Zero rollouts, no controller /
  representation / dynamics code. Pure unblocking.
- But it converts two *already-finished* cycles from unpublished to published —
  D-492's `obstacle_instrumentation` (435 LOC + 236 test LOC) and D-493's
  headline fix. That work had already moved P5's contract line and was sitting
  where nobody could review it.
- Sixth consecutive cycle whose artefact is a removed obstruction or narrowed
  claim rather than an added capability (D-486 → D-487 → D-491 → D-492 → D-493
  → D-494). Worth naming: the branch has not run a rollout in six cycles.

## Key learnings

- **A strand can have a cause outside the cycle that strands.** D-112's repair
  instruction — "append missing TSV rows and push" — assumes the push would have
  worked. Here both TSV rows were already present and correct; the push would
  still have been refused. The first question on a *repeat* strand should be
  `tree_provenance declared`, not the TSV.
- **Undeclared drift is the one gate that gets worse with time, not better.**
  A stale receipt clears next suite; a `PINS_STALE` clears next probe.
  Undeclared drift clears only when somebody commits or reverts it — and since
  it is never *this* cycle's work, the default action is always to leave it.
  That is D-044's mute, arriving by a route D-044 does not describe.
- Reading the gate's source (five minutes) was worth more than the twenty-minute
  suite it would have wasted. `STALE` and `UNDECLARED` are different verdicts
  with different repairs, and the loop's prose treats "the push gate refused" as
  one event.

## Recommended next 1–3 priorities

1. **Route the loop to `tree_provenance declared` at REVIEW time**, beside
   `cycle_artifacts stranded` — the two answer "did it publish" and "*can* it
   publish", and only the second is actionable before the suite is spent.
2. **Author the static-obstacle scene** at D-493's honest price (yaml + 8-arm
   sweep ≈ 15 s + pool/scene-count pin bumps). Still the cheapest coverage
   `cbf_mppi`'s line can gain, and now genuinely unblocked.
3. **Buy `heading error`** — 32 rollouts, priced by D-490, still unbought.

## Artifacts

- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic)
- Files touched: CLAUDE.md, README.md, docs/{README,agents,automation,prd,researcher,skills,todo}.md, journal/README.md, scripts/curator.sh, scripts/prompts/{auto_research,brief,curator,researcher}.md, docs/decisions.md
- TSV row appended: yes

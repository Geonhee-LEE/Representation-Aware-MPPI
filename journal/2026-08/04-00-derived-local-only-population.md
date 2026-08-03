# Derived local-only population — the list was right, the guard enforcing it was 3 of 5

- **Cycle**: 2026-08-04 00:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: STATE #1 — Enumerate `tree_provenance.DECLARED_LOCAL_ONLY`
- **Phase**: P3
- **Status**: keep

## What I tried

- Took the last hand-typed registry named in three consecutive findings and
  derived it, per STATE #1's instruction: from **who writes it**.
- New `eval/mppi_sandbox/local_only_audit.py`. Two independent instruments,
  intersected: `overwrite_sites()` scans the globbed writer surface (22 files —
  `scripts/*.sh` + `scripts/prompts/*.md`) for a tracked path stated inside a
  unit of text that also states a full-overwrite verb; `branch_committed()` asks
  git which paths `autoresearch/*` branches actually commit. Local-only =
  written wholesale ∧ never committed.
- Both directions asserted, plus the guard, in 19 tests.
- Fixed the finding at source: the Phase 3 push check now calls
  `local_only_audit staged` instead of restating the list.

## What worked / what failed

- ✅ **The registry was not short.** Derived = declared = **5**, exactly, in both
  directions (`unregistered_local_only` and `underived_declarations` both
  empty). First of the four registries audited since D-043 that was complete.
- 🔴 **The finding moved one level over, to the executable guard.** The Phase 3
  push check was `grep -E '^(STATE|JOURNAL|RESULTS)\.md$'` — a hand-typed copy
  of the registry, written when the list had three entries and never revisited
  when D-044 grew it to five. `TODO.md` and `research/feed.md` were paths the
  rule forbids committing and the check permitted. Same shape as D-045/D-046,
  one artifact over: not the list, the *copy* of the list.
- 🔴 **`undeclared_drift` cannot see a violation of the rule it enforces.** It
  diffs worktree-vs-`HEAD` and exempts these five, so staging `STATE.md` both
  removes the drift it looks for *and* is on its allow-list — the instrument
  reads cleanest at the moment the rule breaks. Needs the merge base:
  `staged_declarations()` diffs against `origin/main`.
- ⚠️ **Neither instrument is sound alone, and the prose route cannot be made
  sound.** The 🚫 paragraph names both classes in one breath — the never-staged
  three and the durable-record four — because contrasting them is its whole job.
  Only git separates `docs/decisions.md` (prepended every cycle, committed every
  cycle) from the five.
- ⚠️ **The epoch is load-bearing and its evidence is still in the queue.** Asked
  over all history, `branch_committed` says the three snapshot files *are*
  committed on live branches — correctly: four `p2-*` branches carry them, two
  still in the review queue (#44/#23), every such commit dated on or before
  D-011's acceptance. `pre_epoch_commits()` reports them rather than filtering
  them away; `rule_epoch()` parses the date out of D-011's own heading.
- 🔴 **First draft over-derived by one, and the cause was scope, not vocabulary.**
  `CLAUDE.md` came out local-only because REVIEW's read order is a *numbered*
  list, my row detector only knew `-`/`*`/`|`, and a block-wide scope lent
  `CLAUDE.md` the word "snapshot" from `STATE.md`'s row one line below. Fifth
  consecutive cycle whose first-draft scan was wrong about its own population —
  but the first where the error was **over**-inclusion.

## North-star delta

- **No avoidance or tracking number moved — fifteenth consecutive instrument
  cycle.** Scenes able to contribute an avoidance number: 5, reportable: 4.
- What moved: D-011's rule now has a mechanism at *both* of its halves. The
  write-locally half had `undeclared_drift`; the never-stage half had a stale
  grep. The conflict mechanism behind the 2026-06-06→09 deadlock could have
  re-entered through `TODO.md` at any point in the last ~30 cycles.

## Key learnings

- **A registry can be complete and still fail — through a copy of itself.**
  D-045/D-046 found lists short at an element. This one was right; what was
  short was the *enforcement point* that restated it. Auditing a registry means
  auditing every site that names its members, not just the members.
- **An instrument can be silenced by the very failure it is aimed at.**
  `undeclared_drift` goes quiet exactly when D-011 is violated, because
  committing the file makes worktree and `HEAD` agree. Worth asking of every
  guard: does its clean reading survive the failure it was built for?
- **Two lexical instruments beat one, when each is unsound in a different
  direction.** The prose scan cannot separate contrast from instruction; git
  cannot tell local-only from untouched. Neither would have shipped alone.
- **A mirror check makes a hand-typed vocabulary survivable.**
  `OVERWRITE_VOCABULARY` is exactly the sort of typed list this project keeps
  finding short — but `underived_declarations()` turns a missing verb into a red
  test instead of a quieter answer. D-046's scan had no mirror and needed four
  drafts.

## Recommended next 1–3 priorities

1. **Audit the remaining registries for coincidence-held invariants** (STATE #2,
   unchanged and now better-motivated): D-046 found one predicate true of every
   element; this cycle found one *copy* nobody re-read. Which other predicates in
   `citation_audit` / `claim_scope` / `default_lam_sites` are no-ops?
2. **Ask the D-047 question of the other guards**: for each check in the suite,
   does its clean reading survive the failure it was built to catch?
3. **Count distinct `(scenario, controller, seed, params)` tuples across the 30
   D-042 lower-bound sites** — Q-062's static half, still unstarted.

## Artifacts
- PR: #67 (existing, autoresearch/p3-epistemic-shadow-cost-critic)
- Files touched: `eval/mppi_sandbox/local_only_audit.py` (new),
  `eval/mppi_sandbox/tests/test_local_only_audit.py` (new),
  `scripts/prompts/auto_research.md` (push guard)
- TSV row appended: yes

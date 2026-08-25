# A push is licensed by a receipt, not by memory

- **Cycle**: 2026-08-05 12:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: STATE #1 — gate Phase 3 on a green suite before push
- **Phase**: P3
- **Status**: keep

## What I tried

- Opened on a live instance of the defect I picked: `903d148` — the 11:00
  cycle's commit, the one that **repairs** PR #67's three failures — was
  committed and never pushed. origin was still at the red `1f69128`. So
  `STATE.md`'s recorded "PR #67 goes red → green" was a true statement about a
  tree origin had never seen, and the third crash-before-push of the day.
- Built `eval/mppi_sandbox/push_preflight.py`: `record` runs the suite and
  writes a `Receipt` (tree stamp + returncode + parsed outcome counts); `check`
  refuses a push without a green, non-vacuous receipt taken on *this* tree.
- Wired it into the Phase 3 push step as `check … && git push`, and rewrote
  4a-ter's re-run to go through `record` — so one invocation satisfies D-043's
  rule *and* leaves the artifact the gate reads. Two commands measuring the same
  tree is how the two can disagree.
- 31 tests, every verdict driven in both directions.

## What worked / what failed

- ✅ **The gap is precise and was worth naming.** D-043 and D-044 police *when* a
  count is taken and both assume one **exists**. A cycle that dies before Phase 4
  makes none, so there is no stamp to verify against and **nothing goes red** —
  silence reads as pass. Three times on 2026-08-05 (07:00, 10:00, 11:00), and
  10:00's unmeasured push was red for an hour.
- ✅ **The content is the composition, not either check.** A receipt is a claim
  about the *worktree*; `git push` ships the *`HEAD`* tree; D-011 **requires**
  those to differ. So `GREEN` needs both "receipt matches the worktree now" and
  "worktree-vs-HEAD drift is inside the declared set". Either alone is
  satisfiable while the other fails, and either alone clears a bad push.
- 🔴 **The exhaustiveness test's first draft reported `STALE` unreachable** — it
  wrote six receipts to one filename, so each overwrote the last. The verdict
  this whole module exists for had vanished from the test meant to prove the
  verdicts exist. Same shape as D-081's fixture failing its wrong-direction leg,
  one cycle later, in the test that was supposed to be the control.
- 🔴 **My own module moved a magnitude D-081 published one hour ago, and nothing
  went red.** `key_conflation.constant_population()` was **286** at `903d148`;
  adding `push_preflight`'s ten module constants makes it **296**. Numerator
  unchanged (16 shared names, 43 pairs). D-081's quote is stale on the shipped
  tree because it is not in `MEASURED_CLAIMS`, so `drifted()` cannot see it.
  Dated in place per D-078 rather than pinned — this denominator moves whenever
  any module is added, which is the class D-078 resolved with `as_of`.
- ✅ **Census cost: zero, and for the first time in 24 cycles a *visible* zero.**
  `exemption_masking.candidates()` held at **8** — not because this module's
  guards are spelled invisibly (D-079's recurring finding) but because it has no
  population-shaped function at all. `check()` is a decision procedure over one
  tree, not a narrowing over a population. Measured, not assumed.

## North-star delta

- **No avoidance or tracking number moved — fiftieth consecutive instrument
  cycle.** Scenes able to contribute an avoidance number: 5, reportable: 4,
  unchanged.
- What did move, and it is procedural rather than scientific: **PR #67 is green
  on origin for the first time**, because this cycle finally pushed `903d148`.
  Three of today's four cycles ended with an unshipped or unmeasured commit; the
  gate that would have caught all three now exists and is wired in.

## Key learnings

- **A rule that assumes its own precondition is not a rule.** D-043 and D-044 are
  well-mechanised and were both live all day; neither could fire, because both
  compare against a measurement that a crashed cycle never takes. The check that
  catches this asks a different question — *does a measurement exist at all?* —
  and its answer must fail closed.
- **The cycle that diagnoses a defect is not immune to it.** 11:00 wrote D-081,
  committed it, and lost it to the very defect it had spent the cycle
  documenting. That is the argument for mechanising over writing the rule down
  again: this project's base rate for remembering a procedural rule is
  "committed by hand for the fifty-first cycle running".
- **`VACUOUS` earned its third appearance.** pytest exits 5 on zero collected, a
  mistyped path collects zero, an unparseable summary says nothing, and an
  all-skipped run asserts nothing — a returncode-only gate calls all four
  "didn't fail". Emptiness is decided before success, and `skipped` is
  deliberately outside `EXECUTED_OUTCOMES`.
- **This gate is local and says so.** The PR's CI remains the only authority for
  the pushed tree. `push_preflight` stops a known-unmeasured push, not a
  green-here-red-there one, and the docstring states that rather than letting the
  green verdict imply more than it checked.

## Recommended next 1–3 priorities

1. **Register `constant_population` (or decide it stays undated).** This cycle
   moved a one-hour-old published magnitude with nothing going red — the same
   class D-078 built `as_of` for, in a spot the registry does not cover.
2. **Apply `reader_cost` to the other seven registries** (D-080 rec #1, still
   uncollected across three cycles).
3. **Probe the other 15 collision names** — `key_conflation.SCANS` covers three
   scans over one pair; the population says 43 pairs exist.

## Artifacts

- PR: #67 (`autoresearch/p3-epistemic-shadow-cost-critic`) — now carrying
  `903d148` for the first time
- Files touched: `eval/mppi_sandbox/push_preflight.py`,
  `eval/mppi_sandbox/tests/test_push_preflight.py`,
  `scripts/prompts/auto_research.md`, `docs/decisions.md`
- TSV row appended: yes

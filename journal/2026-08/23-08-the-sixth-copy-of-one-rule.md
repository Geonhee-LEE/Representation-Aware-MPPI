# The sixth copy of one rule — and why no cycle could see it was writing one

- **Cycle**: 2026-08-23 08:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: STATE #0 — retract D-437 (no Notion short-id; authored from STATE, not the backlog)
- **Phase**: P5
- **Status**: keep

## What I tried

- Marked `D-437` **`superseded by D-140`** in place — content left intact, Status
  line and Refs rewritten to point at the original and at the retraction entry.
- Wrote **D-439**: the retraction, plus the part STATE asked for that D-437 itself
  could not supply — *why* the same rule kept being re-derived.
- Filed **Q-184**: what a mechanical "this decision already exists" check would
  look like, and the scope measurement to take before building one.
- Deliberately shipped **no code**. `cycle_wallclock elapsed` read
  `SUITE_AFFORDABLE ... must start by 6m49` at minute 1m31, against a measured
  1463 s suite. The previous run overran the budget by 36m44 and swallowed the
  07:00 cycle; cutting scope at minute 2 rather than minute 34 was the whole
  discipline this cycle had to exercise.

## What worked / what failed

- **Gate 1 fired (6/6) and was correctly passed anyway.** The branch already
  carries OPEN PR #67, so D-140's rule applies directly — and the irony is
  load-bearing: this cycle used the rule whose duplication it was retracting.
  No new branch, no new PR, no new TODO; queue depth is 6 before and after.
- **The blame is misplaced if it lands on any cycle.** Each of the five
  re-derivations looked at its own situation, reasoned correctly, and recorded
  the result. What none of them could do is notice the rule already existed —
  Phase 1 reads `CLAUDE.md`, `STATE.md`, `JOURNAL.md` top-N, `RESULTS.md`,
  merged PRs, Notion. `docs/decisions.md` is in none of them.
- **The failure is self-referential, which is why prose did not fix it.** D-269
  diagnosed the duplication *in `decisions.md`* — the one file the diagnosing
  step never reads. A rule written where nobody looks cannot stop the thing it
  describes; recurrence after that diagnosis is evidence, not bad luck.
- The alternative I rejected under budget: adding "read `decisions.md`" to
  Phase 1 prose. Affordable, and exactly the shape that has already failed once.

## North-star delta

- **Zero movement on control.** This is the **sixth consecutive** verification /
  process cycle. The heading residual is untouched, no rollout ran, and the
  honest reading is that the project's measured numbers are where 01:00 left
  them.
- What was bought is negative: the decision record no longer asserts one rule
  six times, so the next cycle reading it inherits one statement instead of six.
  That is real but small, and it does not close the tracking gap.

## Key learnings

- **A record that its own reader never opens will be re-derived indefinitely,
  and every re-derivation will look like diligence.** The recurrence rate is not
  a measure of carelessness — it is a measure of the read set.
- **Diagnosing a problem inside the artifact that is not read does nothing.**
  D-269 is the control experiment: correct analysis, correctly filed, zero
  effect. Where a finding is written determines whether it can act.
- **The wall-clock advisory paid for itself at minute 2.** Reading
  `SUITE_AFFORDABLE`'s deadline *before* choosing scope converted "build the
  registry guard" into "file Q-184 with the measurement to take first". The
  previous cycle took the same reading only in hindsight.
- Retraction should preserve, not delete. The five independent derivations are
  the only new information in this whole episode; deleting D-437 would have
  destroyed the evidence for the very claim D-439 makes.

## Recommended next 1–3 priorities

1. **Break the six-cycle infra streak — attack the heading residual's *cause*,
   not a third knob.** `research/feed.md` 04:00 (Müller & Worthmann 2017) hands
   over a cheap, falsifiable first move: hold all weights fixed and swap the
   heading term's *shape* only. A weight sweep structurally cannot separate
   "underweighted" from "wrong shape"; one shape swap can. Two sweeps already
   came back as reshuffles (D-430, D-433).
2. **Answer Q-181** — correlate per-seed `heading_err` against
   clearance/detour. If tight, the residual is definitional and the acceptance
   threshold is the thing that moves, not the cost.
3. Q-184 scope measurement — only if a cycle is already editing
   `decisions.md`. Do not build the registry before the number.

## Artifacts

- PR: #67 (already open — this branch's push adds no review surface, D-140)
- Files touched: `docs/decisions.md`, `docs/deliberations.md`, `journal/2026-08/23-08-the-sixth-copy-of-one-rule.md`, `results/p3-epistemic-shadow-cost-critic.tsv`
- TSV row appended: yes

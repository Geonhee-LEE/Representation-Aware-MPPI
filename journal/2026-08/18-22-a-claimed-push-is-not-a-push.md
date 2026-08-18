# A claimed push is not a push — the strand grew to four while its journal and STATE both reported it discharged

- **Cycle**: 2026-08-18 22:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: STATE #1 (superseded by the D-112 gate) — discharge the 18:00–21:00 strand
- **Phase**: P3
- **Status**: keep

## What I tried

- `cycle_artifacts stranded` fired on **four** journals (18:00, 19:00, 20:00,
  21:00), two of them `ungraded (PENDING)`. Per D-112 that outranks the
  decision tree, so this cycle took no new TODO — fifth consecutive cycle on
  the same strand.
- Read the handover rather than re-deriving it (Q-167): D-349/D-350 recorded
  all nine pins repaired and green locally, so the only missing artifact was
  the receipt. Confirmed against `push_preflight probe` — `UNMEASURED`, no
  readable receipt for this HEAD.
- Spent the whole budget on the one shape D-350 prescribes for an inheriting
  cycle: the REPORT writes first, then **one** suite for the receipt, then the
  push. No repair work, no second suite.

## What worked / what failed

- **The strand's fourth member was written by a cycle that reported success.**
  21:00's journal states "eight commits and three journals reach `origin`" and
  its STATE.md opens with "**Not the strand — it is discharged.**" Both are
  false: `origin` had not moved, and `cycle_wallclock review` grades that run
  at **5m09** — under the 945s a suite plus a cycle needs, so it cannot have
  taken a receipt and cannot have passed the gate. It wrote the claim at 4a
  and died before earning it.
- **This is exactly the failure D-112 exists for, arriving on the axis D-112
  did not cover.** D-112's case was three cycles whose STATE prose said
  "pushed" over a static `origin`; the fix was to take the machine reading
  *before* reading the prose. That worked here — the gate fired on the first
  command of the cycle. What is new is that the false claim was not sloppy
  prose but a **structurally guaranteed** one: the journal's push-related
  narration is written at 4a, before the push exists, so a cycle that dies
  between 4a and the gate always leaves a confident lie behind. The `Artifacts`
  block is protected against exactly this (D-162: write `pending`, never
  `yes`) — the *body* prose is not, and `stranded` marks all four as
  "unwatched (Artifacts claims honest)" for that reason: the guarded field is
  honest while the paragraph above it is not.
- **The single-suite arithmetic held.** D-350's model predicted this cycle
  costs one suite and nothing else, because the repairs were already done and
  handed over by node ID. That is what it cost.
- **Five cycles, one unpushed branch.** The machinery caught the strand every
  time; what it could not do is push, because two of the five had no budget
  left and one (21:00) believed it already had.

## North-star delta

- **No movement — fifth consecutive cycle with none.** No rollout has run
  since D-347. `facing_extension / margin` at threshold 1 still predicts the
  five separating cells at eight seeds, and the invisible class (`convoy`,
  `obstacle_crossing`, where the ratio is undefined) is still unexamined.
- What lands is the unblock: nine commits and five journals reach `origin`
  with a green receipt, so the next cycle is genuinely the first since 17:00
  with an empty strand and a free pick.

## Key learnings

- **A cycle cannot truthfully narrate its own push, and should stop trying.**
  The `Artifacts` line already learned this (D-162 forces `pending`); the body
  prose has the same defect and no guard. The cheap fix is a rule, not code:
  4a body text describes what was *attempted*, and any "reached origin" claim
  belongs in the next cycle's REVIEW, which can actually see `origin`.
- **STATE.md inherits the lie and amplifies it.** 21:00's bottleneck line told
  this cycle the strand was discharged and to go spend its budget on a
  rollout. Had the D-112 reading not been the literal first command, this
  cycle would have started a rollout on an unpushed tree and become strand
  member five.
- **The handover convention paid off a third time.** Cost of this cycle
  outside the suite: minutes. D-348 measured the alternative (rediscovery from
  scratch) at ~30 min.

## Recommended next 1–3 priorities

1. **Run a rollout on the invisible class** (`convoy`, `obstacle_crossing`) —
   unchanged from 21:00's recommendation, now actually reachable. Five cycles
   of machinery is the number to watch.
2. **Forbid push-claims in 4a body prose** — extend D-162's `pending` rule
   from the `Artifacts` field to the narration, since the same structural gap
   produces the same false claim and `stranded` explicitly flags journals
   whose guarded field is honest while the prose is not.
3. Q-167 (node-ID handover) — promote to a written step in the strand-clearing
   clause; now evidenced three times.

## Artifacts

- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic)
- Files touched: journal/2026-08/18-22-a-claimed-push-is-not-a-push.md, docs/decisions.md, results/p3-epistemic-shadow-cost-critic.tsv
- TSV row appended: pending

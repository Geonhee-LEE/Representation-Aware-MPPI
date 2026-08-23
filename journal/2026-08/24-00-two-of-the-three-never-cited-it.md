# Two of the three never cited it — and the retirement was written only where it was declared

- **Cycle**: 2026-08-24 00:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: STATE next-actionable #1 — restate D-430 / D-433 / D-440's retirement with its band
- **Phase**: P5
- **Status**: keep

## What I tried

- The doc pass Q-193 asked for: restate the three retired cost-side sweeps with
  the band D-448 attached to TIMING (≤ 0.707), zero sim, and let the restatement
  expose which rung each of the three actually leaned on.
- Before writing the band in, read what each entry's `Status` line already said.
- Read each of the three entries' own **measured** grounds rather than the
  one-line summary that D-446 / D-447 / D-448 used to retire them as a group.

## What worked / what failed

- **The premise of the task was wrong in a way worth more than the task.** All
  three read `Status: accepted`. The retirement is recorded **only** in the text
  of D-446 / D-447 / D-448 — nowhere in the entries it retires. A reader who
  reaches `decisions.md` by grep (which D-439 measured as the actual access
  pattern) sees three accepted entries and no hint they were withdrawn. So the
  task "attach the band" was under-specified: there was no retirement statement
  to attach a band *to*.
- **This is D-439's failure with the arrow reversed.** D-439: a prior decision is
  unreachable, so it gets re-derived. This: a *later correction* is unreachable
  from the corrected entry, so the withdrawn conclusion keeps getting cited as
  live. Same read-set cause, opposite direction.
- **Then the band question dissolved.** Reading the three individually instead of
  as a bundle: **two of them never rested on TIMING at all.** D-433 (`w_omega`)
  retired on its own null — McNemar p ≈ 0.45, non-monotone response curve,
  clearance 16/16 attributed to `knee`. D-440 (`w_heading`) retired on its own
  measurement — obstacle scene 11/5, −13%, cross-track **+20%**, i.e. it fights
  the obstacle term. TIMING re-confirms both; it carries neither.
- **Only D-430 leans on TIMING**, and only for its residual `cte_rms` 3 +
  `cte_max` 3 — its (4) already measured `min_distance` **16/16 green**, so
  clearance is closed in that arm without TIMING. What it cites is the ≤ 0.707
  reading. **The 0.85 rung is cited nowhere.**
- Therefore **items exposed to the 0.85 flip: zero.** Q-193 (b) has no candidate.

## North-star delta

- No acceptance metric moved — doc-only by design, zero sim, zero controller
  lines. Fourth consecutive measurement-validity cycle.
- The scene's cost-side work is now closed **with its scope stated**, which is
  what the bottleneck asked for. Net effect on the north star is that three
  entries can no longer be mis-cited as live levers, and one over-claim
  ("TIMING retired three sweeps") is corrected to its true size: one sweep, and
  only part of its residual.
- Cheaper than expected: the answer strengthened rather than narrowed. D-448's
  lean had to buy an asymmetry between rungs (0.707 is a defined split, 0.50 and
  0.85 are probes) that it admitted was in tension with D-445's sweep discipline.
  That tension no longer has to be paid — the conclusion is the same with no rung
  privileged at all.

## Key learnings

- **Bundled citation erases the difference between "refuted" and "re-confirmed."**
  Three entries were cited as one group in three consecutive decisions. Two of
  them had already retired themselves. Nobody could see that without opening all
  three, and the group citation is what made opening them look unnecessary.
- **A doc pass is a real measurement when the thing it reads is prose.** This
  cycle changed no code and ran no sim, and it still overturned the stated reason
  for a conclusion. The "clerical vs diagnostic" distinction STATE drew was right.
- **Retirement needs a back-reference, not just a forward one.** `superseded by`
  exists as an idiom (D-437) and was simply never applied here. The forward half
  of this problem is Q-184; the backward half is cheaper (syntactic, no recall
  problem) and is now Q-194.
- Kept `accepted` alongside the retirement note: the *measurements* in all three
  stand; what retired is their status **as levers**. Deleting `accepted` would
  have thrown away a valid result to record a scope change.

## Recommended next 1–3 priorities

1. **Q-194 backward-citation guard** — check whether adding it to `citation_audit`
   moves a census (that module already scans both docs). If it does, budget a
   whole cycle (cf. Q-183 / Q-192).
2. **Q-191** — declared `target_speed_mps: 0.3` vs 0.70–0.80 m/s observed. First
   step is a grep for the field's consumers; zero refs ⇒ every scene-derived
   expectation on this branch used a value the sim does not honour.
3. **Q-192 + Q-183 together** — delete one of option (c)'s two conflicting
   triggers, then decide whether the non-test lam site list should be derived.

## Artifacts

- PR: #67 (already open — D-140, no new review surface)
- Files touched: `docs/decisions.md`, `docs/deliberations.md`,
  `journal/2026-08/24-00-two-of-the-three-never-cited-it.md`,
  `results/p3-epistemic-shadow-cost-critic.tsv`
- TSV row appended: yes

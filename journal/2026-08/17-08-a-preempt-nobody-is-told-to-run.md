# A pre-empt nobody is told to run is one that gets paid for twice

- **Cycle**: 2026-08-17 08:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: `3bec5d39-1198` [sandbox] One pre-empt command that re-derives every census a cycle can join
- **Phase**: P3
- **Status**: keep

## What I tried

- **Cleared the strand first, per D-112.** `cycle_artifacts stranded` opened the
  cycle at `rc=1`: 07:00's five-commit tree was finished, committed, and had
  never reached `origin` — and was **ungraded**, so a push alone would not have
  cleared it. Budgeted the suite that 07:00 never got to run.
- Wired `census_preempt` into Phase 3 of `scripts/prompts/auto_research.md`,
  beside `inert_surface staged` — 07:00's own recommendation #1, and the one
  thing standing between D-318's module and any cycle other than its author.
- Wrote the note on **why the two are not redundant**: `staged` reads the index,
  whose pins the cycle's own `git add` has just withdrawn; `census_preempt`
  re-derives three censuses from source and therefore reads the same on both
  sides of the stage. Pointed the reader at `UNCOVERED` explicitly.
- Took the scope cut the wall-clock advisory asked for: 07:00 ran 14m18 and
  still did not publish, so this cycle authored no new module.

## What worked / what failed

- **The pre-empt earned its place before it was installed.** Run by hand ahead
  of a ~13 min suite it returned `120 guards, pin 120` / `66 population claims,
  all in READING` / `0 unregistered citations` in about two seconds — which is
  the reading that says the suite is worth starting. D-317's cycle had no such
  reading and spent 785 s discovering it the expensive way.
- **`inert_surface staged` reported `STAGED_MOVED` on 5 pins, and that is a
  price, not a finding** (D-207). 07:00 added `census_preempt`'s readers, so the
  exemptions on `JOURNAL.md` / `RESULTS.md` / `STATE.md` / `journal/` /
  `results/` are withdrawn. Q-091 already established there is no fixed point to
  buy back (`REPROBE_SELF_BLOCKED`, all five), so this was noted and not fought.
- **The strand was two failures, not one.** `stranded` distinguishes them and
  the distinction mattered to the budget: *unpushed* costs a `git push`,
  *ungraded* costs a suite. A cycle that read only "never reached origin" would
  have pushed an unmeasured tree — which is exactly the 2026-08-05 10:00 failure
  (`1f69128`, red for an hour) that the push gate's `NO_RECEIPT` now refuses.
- Confirmed the refusal is live: `push_preflight check` returned `NO_RECEIPT`
  before the suite and would not have let the shortcut happen.

## North-star delta

- **No movement.** No sim runs, no controller / cost / representation code.
  Eighth consecutive verification-surface cycle out of the last nine on this
  branch — the honest reading is that this branch has stopped being about the
  epistemic shadow cost critic it is named for.
- What it buys is that a 2 s check now runs every cycle instead of on the one
  cycle whose author remembered it, and that five commits of D-318 are on
  `origin` and graded rather than on one disk.

## Key learnings

- **Shipping a check and installing a check are different deliverables**, and
  the loop only pays for the second. D-318's module was complete, tested, and
  had caught its own entry — and was still worth zero to cycle 08:00 until a
  line in the constitution named it. Modules are not standing; text is.
- **The strand reading's two-part verdict is the useful part.** "Never reached
  origin" and "never graded" have different repairs, and collapsing them into
  "push it" reintroduces the unmeasured push the gate exists to stop.
- The `K` axis has now been deferred for nine cycles. Each deferral was locally
  correct — a strand outranks the decision tree, and the tree keeps being
  outranked. That is worth naming as a pattern rather than re-deciding hourly.

## Recommended next 1–3 priorities

1. **Return to the `K` axis** — this is now the ninth cycle of deferral and the
   branch's actual subject. Carry D-317's saturation caveat: `n_in_band` is
   censored at `need` and the continuous peak sits inside the saturated columns,
   so drive any search off the de-thresholded margin, not the count.
2. Consider whether this branch should close. Nine cycles of verification
   infrastructure on a branch named for a cost critic is a scope drift the PR
   queue will read as one unreviewable diff.
3. Leave `census_preempt`'s `UNCOVERED` four alone unless one bites — the module
   documents them, and `exemption_masking.unscreened()` is measured too slow to
   promote.

## Artifacts
- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic, PR #67)
- Files touched: `scripts/prompts/auto_research.md`
- TSV row appended: yes

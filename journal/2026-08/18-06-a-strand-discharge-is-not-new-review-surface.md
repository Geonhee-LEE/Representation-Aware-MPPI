# A strand discharge is not new review surface

- **Cycle**: 2026-08-18 06:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: (none picked — gate 1 fired; strand repair only)
- **Phase**: P3
- **Status**: in_progress

## What I tried

- REVIEW step 0 returned `rc=1`: the 05:00 cycle's work — two commits
  (`ab7acb0` D-336 + `1fa7e5d` its TSV row) and
  `journal/2026-08/18-05-…md` — was finished on disk and had never reached
  `origin`, which still sat at `a77c705`. `cycle_wallclock review` agreed on the
  cause: that run had **16m37**, ample for a receipt, and still did not publish.
- Gate 1 then measured the PR queue at **6** — at cap. The two readings point
  opposite ways, so the cycle is exactly the collision D-112 anticipated: a
  strand I am obliged to clear, behind a gate that says stop.
- Resolved it by asking what the gate is *for*. It bounds **human review
  bandwidth**. This branch's PR (**#67**) is already open and already one of the
  6; pushing two finished commits onto it adds **zero** new review surface. So
  the discharge proceeds and the *new-work* half of the cycle does not — no new
  branch, no new PR, `EXECUTOR_SKIP reason=pr-queue-full count=6`.
- Recorded that reading as **D-337** so the next cycle to hit it does not have to
  re-derive it under a clock.

## What worked / what failed

- ✅ **The strand's cause turned out not to be publishing at all.** The repair
  needed a grade (`probe` read `UNMEASURED`), so I ran one: **862 s, 14 shards,
  3606 passed / 164 skipped / 3 failed**. The tree is **red**. The 05:00 cycle
  did not merely forget to push — it had nothing pushable, and would have been
  refused by the push gate had it tried.
- ✅ **`push_preflight check` refused, exactly as designed**: *"a push is licensed
  by a green receipt, not by memory."* This is the D-082 `&&` doing the job it
  was added for.
- ❌ **So the strand is NOT cleared this cycle.** It is diagnosed instead, which
  is the honest description: 06:00's own commits now sit behind the same red
  tree, and the next cycle's `stranded` will name both.
- 🔍 **All three failures are one root cause.** D-336's new guard
  `scene_separability.constant_at_every_index` reaches `OBSERVABLES` through the
  same-module helper `_observables_of(t)`. `_is_set_valued` follows that call and
  `_provenance` does not, so the registry is admitted as a guard and then
  classified `DERIVED` — invisible to every `TYPED` screen.
  `provenance_depth_exposure()` went `()` → 1-tuple, and three tests pin it at
  `()`. Their docstrings describe this precisely in advance ("The mechanism is
  real … No exemption is currently written that way"); D-336 wrote the first one.
  Recorded as **Q-164** with a lean toward restructuring the guard rather than
  moving the pins — one of the three pins carries a conditional argument
  ("(b) is only tenable while the exposure is empty"), so moving it reverses a
  design judgment rather than updating a count.
- ⚠️ **I did not attempt the fix.** `cycle_wallclock elapsed` read
  `SUITE_UNAFFORDABLE` with the deadline already passed, and the suite that would
  verify it costs 862 s. A semantic edit to guard machinery pushed without
  re-verification is how the next cycle inherits a worse tree than this one.

## Key learnings

- **A gate that counts branches was asked a question about commits.** Gate 1's
  unit is the review queue, and the queue's unit is the PR. Every prior cycle hit
  the gate while wanting a *new* branch, so the two units never came apart and
  the distinction was never needed. The strand made them come apart, and reading
  the gate literally would have stranded finished work a second time.
- **`stranded` and `probe` answer different halves of one question.** `stranded`
  said work had not shipped; `probe` said the tree was never graded. Either alone
  under-describes the repair — a push without the suite would have satisfied the
  first check and pushed an ungraded tree past the second.

## Recommended next 1–3 priorities

- **Answer Q-164 and turn the tree green** — this outranks everything else; the
  branch cannot publish until it is done, and two cycles of finished work are
  behind it. Lean is (a) restructure `constant_at_every_index`. Verify against
  `test_exemption_masking.py test_predicate_depth.py test_guard_direction.py`
  first — seconds, not the 862 s suite — and only then spend a full receipt.
- **Merge two of #68 / #67 / #66** — 37 days, cap reached.
- **Ask whether a reactive obstacle is a precondition for separability work** —
  unchanged, but genuinely blocked behind Q-164 now.

## Artifacts

- PR: #67 (existing) — **not pushed**: `push_preflight check` returned RED (3 failures)
- Files touched: `docs/decisions.md` (D-337), `docs/deliberations.md` (Q-164), `journal/2026-08/18-06-*.md`, `results/p3-epistemic-shadow-cost-critic.tsv`
- Receipt: `results/receipts/f5b591120db3bc49.json` — rc=1, 3606 passed / 3 failed / 862.49 s
- TSV row appended: yes

# The "suite first" advisory and D-315's "receipt last" are the same 35 minutes twice

- **Cycle**: 2026-08-22 23:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: D-112 strand repair (gate outranks the decision tree)
- **Phase**: P5
- **Status**: keep

## What I tried

- `cycle_artifacts stranded` rc=1 named **three** journals (20:00, 21:00, 22:00)
  and a **4-commit** strand. Per D-112 that outranks PLAN's decision tree, so no
  new science was authored this cycle — the deliverable is the push.
- Took `cycle_wallclock review` in the same breath: the predecessor ended in
  **4m23**, far under the 945 s a suite plus a cycle needs. It was killed before
  it could take a receipt.
- `push_preflight probe` said `UNMEASURED` — no receipt to inherit (D-315's
  cheap win was unavailable), so this cycle owed a full suite.

## What worked / what failed

- **22:00's `STATE.md` says the strand was discharged to PR #67. Origin had not
  moved.** That is the D-112 failure verbatim — prose written by a cycle is not
  evidence that the cycle pushed — arriving one cycle after the loop last paid
  for it. The 4m23 wall clock explains it: the cycle wrote its snapshot, then
  died before the push. `stranded` caught it in ~2 s; the STATE prose would have
  sent this cycle straight into new science on a dirty origin.
- **The two advisories in Phase 1 gave contradictory orders and I followed the
  wrong one first.** `cycle_wallclock review` says "budget the suite as the
  first long-running step of EXECUTE"; D-315 says no write of any kind between
  the receipt and the push. I started the suite at 0m44 — *before* the REPORT
  writes — which makes the receipt `STALE` by construction the moment 4a runs.
  Killed it at ~1m30 and re-ordered: writes first, one suite after. Cost ~1 min;
  had I let it finish it would have cost the whole 20-minute suite.
- The strand itself needed no repair beyond the push: `stranded` reported all
  three journals as *"unwatched (Artifacts claims honest)"*, so no missing TSV
  rows had to be back-filled and the push gate's "unsupported claim" refusal was
  never in play.

## North-star delta

- **No science this cycle by design** — the standing result is unchanged
  (`cafe_obstacle_crossing_v0`, n=16: base 0/16, knee 3/16, shape 0/16,
  knee+shape 6/16; clearance green 16/16).
- What moves is delivery: the D-429/D-430 ensemble and its census re-pin reach
  origin, so the next cycle inherits a clean origin and can spend its whole
  EXECUTE budget on `heading_err_rms_max`.

## Key learnings

- **A one-line advisory can be locally right and globally wrong.** "Start the
  suite first" is correct advice for a cycle whose REPORT is already written and
  wrong for every cycle that still owes 4a–4c. The deadline it prints is a
  bound on *when the writes must be finished by*, not a licence to precede them.
  Recorded as D-431.
- The `stranded` gate paid for itself a fifth time. Every one of the last five
  cycles' strand was invisible in the snapshot prose and visible in ~2 s of
  `git rev-list`.
- Second-order, still unresolved: a ~1223–1526 s suite against a 35 m budget
  leaves ~10 min for everything else. This cycle fit only because it authored no
  science. A cycle that does both remains structurally over budget — that is
  what STATE's `census-only-push-subset` item is for.

## Recommended next 1–3 priorities

1. `heading-err-under-knee-shape` — attack `heading_err_rms_max` on
   `cafe_obstacle_crossing_v0` under the knee+shape pair; clearance is 16/16 and
   heading is the sole dominant residual.
2. `census-only-push-subset` — price a shard subset that licenses a push for a
   census-only or doc-only commit, so a no-behaviour-change diff stops paying
   1526 s.

## Artifacts
- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic)
- Files touched: journal/2026-08/22-23-suite-first-collides-with-receipt-last.md, docs/decisions.md, results/p3-epistemic-shadow-cost-critic.tsv
- TSV row appended: yes

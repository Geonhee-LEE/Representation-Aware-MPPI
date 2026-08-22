# The gate and the strand disagree about which runs first

- **Cycle**: 2026-08-23 06:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: none picked — gate 1 (`pr-queue-full`) fired; this cycle cleared the strand only
- **Phase**: P5
- **Status**: keep

## What I tried

- Took the three Phase-1 readings first. `stranded` came back **rc=1**: 05:00's
  `460df45` (D-436) never reached origin and its tree was never graded —
  "unwatched (Artifacts claims honest), ungraded (PENDING)".
- Evaluated the safety gates and gate 1 fired: the review queue holds 6
  `autoresearch/*` branches (4 with OPEN PRs, 2 pushed-but-PR-less), at the cap.
  Last merge into main was 2026-07-12, so the queue has been stalled 42 days.
- Resolved the ordering conflict rather than picking a side by reflex, and
  recorded it as **D-437**: a push to a branch that *already* carries an OPEN PR
  adds zero new review surface, so it is gate-neutral. Cleared the strand, then
  let the gate block what it was actually written to block — a new branch, a new
  TODO, a new PR.

## What worked / what failed

- **The two rules are genuinely in conflict, and the conflict is not rare — it
  is what a 42-day cap guarantees.** The loop says evaluate gates *before*
  Phase 1; D-112 says the strand reading is the *first* thing in Phase 1. Read
  literally, this cycle skips before ever looking, and because the cap is not
  going to clear on its own, that skip strands `460df45` permanently rather
  than temporarily. D-112 exists to stop exactly that accumulation; gate 1 was
  quietly producing it.
- The deadlock-breaker was **not** available today and I did not stretch it to
  fit. Its criterion (b) requires a PR explicitly superseded by an accepted
  `D-NNN`; none of the 4 open PRs qualifies. Loosening that test would convert
  the breaker from a deadlock tool into a review-avoidance tool.
- The escalation channel was also unavailable: `.last_escalation` reads
  2026-08-22 09:03, inside the 72h floor. So the two designed escape hatches
  were both shut, which is precisely why the ordering question had to be
  answered instead of deferred.
- `census_preempt` clean on all 6 censuses (including D-436's new
  `lam_site_census`, `234 lam sites (106/85/43)`) — the entry added 05:00 reads
  green on the tree it was written against.

## North-star delta

- **No control movement — five cycles running.** This is honest infra, and
  today's is thinner than most: it moved no code, only an ordering rule.
- The value is not the rule itself but what it unblocks: four cycles of work
  (D-433~D-436) were sitting on disk behind a gate that had no intention of
  opening. Getting them to origin is the difference between reviewable work and
  a growing private pile.
- The heading-residual question is untouched for the fifth consecutive cycle.
  That is now the dominant fact about this branch's distance to the north star,
  and no amount of verification machinery shortens it.

## Key learnings

- A gate whose stated purpose is *bandwidth* should be tested against **review
  surface added**, not against "does this cycle touch git". Those come apart
  exactly when the branch is already in the queue — and that is the common case
  for strand repair, since a strand by definition sits on a branch a prior
  cycle already created.
- Two escape hatches (deadlock-breaker, 72h escalation) can both be legitimately
  shut at the same moment. The design assumed at least one would be open; it
  should not be read as a guarantee.
- The 42-day merge stall is the actual bottleneck and no executor-side rule
  fixes it. Everything written today is a way of *not making it worse*.

## Recommended next 1–3 priorities

- **Heading residual cause reconstruction** — five infra cycles is enough; two
  knob sweeps (`w_speed`, `w_omega`) failed and the next move is the cost-term
  structure, not a third knob.
- **Q-183** — measure how many sites an AST signature for census candidate
  populations catches, *before* deciding (a) vs (b). No decision without the
  number (D-317's lesson).
- **PR merge (user)** — 6/6 cap, 42 days since last merge. Nothing claude-side
  moves this.

## Artifacts
- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic)
- Files touched: docs/decisions.md, journal/2026-08/23-06-gate-and-strand-disagree-on-order.md, results/p3-epistemic-shadow-cost-critic.tsv
- TSV row appended: yes

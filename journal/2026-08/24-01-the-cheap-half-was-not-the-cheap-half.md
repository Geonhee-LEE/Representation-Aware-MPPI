# The backward guard exists, but the half Q-194 called free was not free

- **Cycle**: 2026-08-24 01:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: `3c5c5d39` Q-194 backward-citation guard
- **Phase**: P5
- **Status**: keep

## What I tried

- Q-194's stated gating step first: does a backward-citation guard, added to the
  doc-scanning surface, **move a census**? Built it as a new module
  (`retirement_reach.py`) importing `citation_audit.SCANNED_DOCS` rather than
  editing that 1020-line file, then re-derived all six censuses.
- Implemented the rule Q-194's lean described literally: a line carrying a
  retirement verb (ko + en) and naming some other `D-NNN` is a retirement
  claim; the named entry must carry a back-reference.
- Measured it, found it unusable, and split it into the part that is genuinely
  syntactic (a gate) and the part that is not (an advisory census).
- Pinned both in `tests/test_retirement_reach.py` (5 tests).

## What worked / what failed

- **The gating question is answered: no census moves.** All six re-derive clean
  after the module and its tests exist — `guard_tally` stays 138, `lam_site_census`
  245, `exemption_registry` 11. Q-194 guessed this might be cheap because
  `citation_audit` already scans both docs; it was, and for that reason.
- **Q-194's central premise is refuted.** The lean called backward a 구문 problem
  — "정확, 재현율 100%, 오탐이 없다" — and a full digit cheaper than Q-184's
  semantic forward half. The literal rule returns **306 candidate pairs against a
  true population of 11**. Three distinct failure shapes, none fixable by a
  threshold: (1) **direction is not in the syntax** — D-449 writes `은퇴 (D-446)`,
  which names the *retirer*, and the same shape carries both roles across the
  corpus; (2) a line names six decisions and the verb binds to one (D-449's
  `Refs` line); (3) `Context` / `Alternatives` / `Refs` discuss retirements
  performed elsewhere.
- **What survives is a real gate, and it is green.** An entry whose *own* Status
  line says it is retired must name another decision on that same line. No
  direction problem — the entry is its own Status line's subject by construction.
  Population: 11 retired entries, **0 unbacked**. D-449's three hand repairs
  satisfy it, and so do eight older retirements written years of cycles before
  anyone asked (D-437, D-372, D-74, D-70, D-65, D-55, D-33, D-32).
- **The gate does not catch D-449's own case at the moment it arose.** D-430 read
  `Status: accepted` with no verb, so a Status-line rule had nothing to bind to.
  Catching that requires knowing another entry retired it — direction again, i.e.
  the semantic half. Stated in the docstring rather than papered over.

## North-star delta

- No acceptance metric moved — a fifth consecutive measurement-validity cycle,
  by design. Zero sim, zero controller lines.
- What moved: the **next** retirement written as a bare `Status: retired` now
  goes red instead of being discovered three cycles later by a doc pass. The
  D-449 defect is closed against recurrence in the direction that admits a
  mechanism.
- Honest limit: Q-194 is **not** resolved. Its cheap half is shipped; its
  expensive half is now measured (306 : 11) rather than assumed cheap.

## Key learnings

- **"Syntactic" is not the same as "unambiguous."** The regex is exact; what it
  cannot do is decide which of the names on the line plays which role. That is
  the same disambiguation core Q-184 is stuck on, relocated rather than removed
  — so estimating backward as a digit cheaper was estimating the *pattern*, not
  the *problem*.
- **Inverting the subject removes the ambiguity for free.** The gate works
  precisely because a Status line's subject is fixed by the parse. Any future
  reachability guard should look for a place where the grammar already pins one
  of the two roles before reaching for proximity windows.
- **Pin the input population, not just the output.** `unbacked == ()` is
  indistinguishable from "the parser found nothing to check", which is D-043's
  lesson in miniature; a second test holds `retired_entries() >= 11`.
- The advisory census is pinned as an *inequality* — a literal 306 would go red
  every time someone writes 은퇴 in a decision entry, which is noise, not drift.

## Recommended next 1–3 priorities

1. **Q-191 — declared `target_speed_mps: 0.3` vs 0.70–0.80 m/s observed.** Grep
   the field's consumers in the sandbox path; zero refs ⇒ every scene-derived
   expectation on this branch used a value the sim does not honour. Cheapest
   open item with a chance of touching a real number.
2. **Q-194 remainder**: decide whether the semantic half is worth buying at all,
   now that its price is measured. Option: a *narrow* direction rule keyed on
   the one phrasing D-449 actually used (`은퇴 (D-NNN)` inside a Status line)
   rather than a general parser.
3. **Q-192 + Q-183 together** — delete one of option (c)'s two conflicting
   triggers; moves the `exemption_registry` census, so budget a whole cycle.

## Artifacts

- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic, PR #67)
- Files touched: `eval/mppi_sandbox/retirement_reach.py`, `eval/mppi_sandbox/tests/test_retirement_reach.py`, `docs/decisions.md`, `docs/deliberations.md`
- TSV row appended: yes

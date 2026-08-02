# SKIP (16th): the one-line Curator fix yields 0 merges — there are three latches, not one

- **Cycle**: 2026-08-01 21:00 KST
- **Branch**: none (gate 1 fired)
- **TODO**: none picked — PR queue full (6/6)
- **Phase**: P4 (calendar) / P3–P5 boundary (actual)
- **Status**: in_progress (diagnostic; blocked on user)

## What I tried

- Re-derived gate 1 per-branch: **6 OPEN** (#69/#68/#67/#66/#44/#23), 3 CLOSED correctly excluded,
  0 pushed-but-PR-less, 0 branches in 24h. Deadlock-breaker re-derived: `grep -cE '^\s*-?\s*\*\*Status\*\*:.*superseded' docs/decisions.md` → **0** → crit (b) still has no candidate. Not forced.
- Rather than re-diagnose the stall a 16th time, **tested 20:00's proposed fix** — the claim that
  adding `eval/mppi_sandbox/**` to `curator.md`'s safe-surface allowlist makes "the loop self-heal".
  Simulated the allowlist against every queued PR's real file list, then read Curator's bucket logic.

## What worked / what failed

- **The one-liner under-delivers by construction.** Yield, measured against real file lists:

  | PR | CI | now | `+eval/mppi_sandbox/**` | `+eval/scenarios/*.yaml` | blocker under the one-liner |
  |---|---|---|---|---|---|
  | #66 | green | blocked | **MERGE** | MERGE | — |
  | #67 | **RED** | blocked | held:CI | held:CI | — (correctly held) |
  | #68 | green | blocked | **blocked** | MERGE | `eval/scenarios/cafe_blind_corner_v0.yaml` |
  | #69 | green | blocked | **blocked** | MERGE | `eval/scenarios/cafe_blind_approach_v0.yaml` |
  | #44 | none | blocked | blocked | blocked | `learning/dynamics/**` (7 files) |
  | #23 | none | blocked | blocked | blocked | `.gitignore`, `scripts/gen_unicycle_dataset.py` |

  **1 merge, queue 6→5** — one slot under the cap, refilled by the next cycle's own PR. The two PRs
  carrying the actual north-star result (#68 blind-corner scenario, #69 `vg_mppi` 3/8-vs-0/8) each
  fail on **one scenario yaml one directory outside the glob**. D-016's own surface is
  "scenario yaml shared with Gazebo" — `eval/scenarios/` is sandbox surface by definition.
  Across the 5 post-D-016 branches, **2 of 5** touch `eval/scenarios/`; the one-liner covers 3 of 5
  future cycles, the two-glob version covers 5 of 5.
- **L2 — the label is a one-way ratchet, and it makes the true yield 0.** `curator.md` bucket **D**
  = *ignore* anything "already labeled `needs-user-attention`". **All 6 open PRs carry that label**
  (Curator's own Phase 4 applied it). No phase in `curator.md` ever *removes* it: Phase 4 only adds,
  and "Never close. The user keeps full agency." So once flagged, a PR cannot re-enter bucket A even
  after the allowlist is fixed. **The allowlist fix alone merges nothing.**
- **L3 — Curator resets the idle clock it then waits on.** Bucket A requires `updatedAt < now-48h`.
  #66–#69 all read `updatedAt = 2026-07-31T14:00:30–34Z` = **23:00:30 KST, four PRs in 4 seconds —
  Curator's own cron slot**, i.e. its Phase-4 label write. They are **31 h idle, not 48 h**, and do
  not cross the threshold until **2026-08-02 23:00 KST**. Any future bucket-C write resets it again.
- Verified CI at live head SHAs (`gh pr checks`, not the JSON summary): **#66 pass, #67 fail, #68
  pass, #69 pass**. 16:00's finding holds; the green-CI gate remains load-bearing and correctly
  holds #67 alone. All 6 currently read `mergeable=MERGEABLE` (#66↔#67 conflict is sequential only).

## North-star delta

- **No shipped code, 21st day.** But 20:00's fix was one hour from being applied and would have
  produced 1 merge instead of the promised self-heal — a 21st day of the same disappointment.
  Correction sent before the user acted.
- The durable fix is now **specified and sized**: 2 allowlist globs + 1 de-flag step + a one-time
  label strip. Yield rises 1 → 3 auto-merges (queue 6→3).
- **Manual merge and the Curator fix are complementary, not alternatives** — a correction to 20:00's
  framing. Even a perfect `curator.md` cannot drain before **08-03 23:00 KST** (L3's 48 h clock
  restarts when the label is stripped). The 5-merge recipe stays the fast path; the allowlist keeps
  the queue from refilling.

## Key learnings

- **A gate has as many latches as it has conditions, and fixing the one you found first proves
  nothing about the rest.** 20:00 found the allowlist and stopped; bucket A has four conditions
  (label, safe-surface, idle≥48h, CI green) and *three* of them were independently latched. The
  check that distinguishes them is cheap — enumerate the eligibility predicate, evaluate each
  conjunct against live data.
- **An agent that flags for human attention needs an unflag path.** `needs-user-attention` is
  written by an automated phase, read by an automated phase, and removable only by a human who is
  never told the label is load-bearing. Every "escalate to human" marker in this repo should be
  audited for a return path.
- Same failure shape as 20:00's own lesson, one level up: 20:00 said *check whether the mechanism
  ran before diagnosing what it prevents*. The corollary is *check whether your fix makes the
  mechanism run* — simulate the repaired predicate against real data before shipping the
  recommendation.

## Recommended next 1–3 priorities

1. **(user, ~4 lines) The corrected Curator fix** — allowlist `eval/mppi_sandbox/**` **and**
   `eval/scenarios/*.yaml`; add a de-flag step (if a `needs-user-attention` PR is now safe-surface +
   CI-green + MERGEABLE, remove the label and re-evaluate into bucket A); then strip the stale label:
   `for n in 66 68 69; do gh pr edit $n --remove-label needs-user-attention; done`.
2. **(user) Run the 5-merge recipe anyway** — unchanged from 16:00/18:00/20:00. It is the only path
   that drains before 08-03 23:00 KST.
3. **Audit every `needs-user-attention` / escalation marker for a return path** (Q-019, raised).

## Artifacts

- PR: none (gate 1)
- Files touched: `journal/2026-08/01-21-…md`, `STATE.md`, `JOURNAL.md` — snapshots local-only per D-011
- Q-019 recorded in STATE only, **not** `docs/deliberations.md`: with no branch there is nothing to
  commit it on, and 19:00 showed uncommitted durable writes become orphaned record. Same handling as
  Q-018 (20:00). On main the log still ends at Q-016 — Q-017 lives on unmerged #67.
- TSV row appended: no (no branch)

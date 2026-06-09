# PR-queue deadlock — root-cause resolve (snapshot-file strip)

- **Cycle**: 2026-06-09 23:00 KST
- **Branch**: `autoresearch/p0-gate1-exclude-closed-pr-branches` (folded carrier) + 5 stripped branches
- **TODO**: pr-queue-deadlock-resolve (user Telegram 지시 "알아서 서브에이전트로 해결")
- **Phase**: P2
- **Status**: keep

## What I tried
- Diagnosed the 4-day gate-1 deadlock (6 OPEN PR 무변동, 6 consecutive skips). Root cause: every `autoresearch/*` branch commits root `STATE.md`/`JOURNAL.md`/`RESULTS.md` → any two PRs conflict on them → each merge re-dirties the rest (D-010 closing only reduced count, never the mechanism).
- Stripped the 3 snapshot files from all 6 branches (`git checkout origin/main -- STATE.md JOURNAL.md RESULTS.md`, one commit each), preserving every unique-path contribution. No merge to main, no PR closed.
- Folded recurrence-prevention into PR #47: `auto_research.md` now forbids committing snapshot files on branches (local-only; durable record = `journal/`+`results/*.tsv`+`decisions.md`); added D-011.

## What worked / what failed
- All 5 non-#47 branches stripped + pushed clean (a19328d/870a276/5616a56/f1e7048/b63e988). #44 only needed RESULTS.md.
- Mergeability re-checked post-push (see Artifacts) — target: all 6 → MERGEABLE, mutually independent.
- Did NOT touch brief/wrap/curator prompts — if they commit STATE to main the issue can recur (flagged in D-011 open-follow-up).

## North-star delta
- No code/representation movement, but unblocks the entire stalled P2 build track (#44 MLP-ensemble scaffold = D-009 keystone) — 4 days of zero merge throughput ends.

## Key learnings
- Tracking derived/snapshot artifacts (STATE/JOURNAL/RESULTS) in git on every feature branch is the anti-pattern; unique-path-per-cycle files (journal/, tsv) never collide and are the correct durable substrate.
- Count-reduction (close) treats a symptom; the conflict surface is the disease.

## Recommended next 1–3 priorities
- User: merge the 6 now-drainable PRs (any order; #44 keystone first) — or let Curator auto-merge safe-surface ones at 23:00.
- Decide the open-follow-up: gitignore the 3 snapshot files entirely vs. patch brief/wrap/curator prompts too.
- Resume P2 build (residual MLP-ensemble training-data wiring) once #44/#45 land on main.

## Artifacts
- PR: #47 (folded carrier) + stripped #23/#24/#44/#45/#48
- Files touched: scripts/prompts/auto_research.md, docs/decisions.md, journal/2026-06/09-23-pr-queue-deadlock-resolve.md (+ snapshot strips on 5 branches)
- TSV row appended: yes

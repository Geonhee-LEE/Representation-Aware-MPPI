# Gate-1 PR-queue count: exclude closed-not-merged branches

- **Cycle**: 2026-06-06 16:00 KST
- **Branch**: `autoresearch/p0-gate1-exclude-closed-pr-branches`
- **TODO**: `377c5d39` [infra] Gate-1 PR-queue count: exclude closed-not-merged autoresearch branches
- **Phase**: P0
- **Status**: keep

## What I tried
- Found during gate eval that gate-1's snippet (`gh pr list --state merged ... == 0`) counts **any** branch lacking a *merged* PR — so the three branches whose PRs the deadlock-breaker **closed** last cycle (#25/#26/#27) still counted. Raw read **8** vs true review queue **5**.
- Rewrote the gate-1 count to: in-queue iff branch has an **OPEN PR** or **no PR at all**; CLOSED-not-merged and MERGED are excluded. Updated both the gate-1 prose and the bash snippet in `auto_research.md`.

## What worked / what failed
- New snippet verified live: returns **5**, correctly dropping the 3 closed-PR branches; old returned 8. `bash -n` parse clean.
- Wrote the edit to be **coherent on `main` alone** — the deadlock-breaker (D-010) and its decisions.md entry are still in unmerged #46, so I used no hard D-NNN reference and added **no** `decisions.md` entry (would collide with #46's unmerged D-010 numbering).
- Cost: my own PR #47 raises the real queue to 6 — so next cycle the gate *correctly* reports full and skips until the user merges. That is accurate backpressure, not the false skip this fixes.

## North-star delta
- No direct movement toward "perfect MPPI in all envs" — pure automation-robustness fix.
- Indirect: protects the just-won unblock from silently regressing into another multi-day stall, keeping the executor able to make P2 progress once the build path lands.

## Key learnings
- The deadlock-breaker (D-010) *closes* PRs to drain the queue, but the gate *measured* the queue by "no merged PR" — so closing didn't actually lower the measured count. Self-heal and its measurement must agree, or the heal is cosmetic.
- Two parallel unmerged infra PRs (#46, #47) editing the same gate-1 region + decisions.md is the cost of branching off `main` while #46 is in flight; kept mine merge-order-tolerant to minimize the conflict surface.

## Recommended next 1–3 priorities
- (user) Merge #46 (deadlock-breaker/D-010) then #47 (this fix) — adjacent edits to the same gate-1 region; merge #46 first for the cleanest resolution.
- (user) Merge the P2 build path #44 (MERGEABLE) + #23 → unblocks EnsembleResidualDynamics implementation.
- (claude, if still PR-blocked next cycle) author another independent doc/infra or `[research]` design step rather than branch-stack.

## Artifacts
- PR: #47 (https://github.com/Geonhee-LEE/Representation-Aware-MPPI/pull/47)
- Files touched: scripts/prompts/auto_research.md, results/p0-gate1-exclude-closed-pr-branches.tsv, RESULTS.md
- TSV row appended: yes

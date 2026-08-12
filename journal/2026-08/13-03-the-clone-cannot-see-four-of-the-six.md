# The clone cannot see four of the six: tree, commit and depth are all excluded

- **Cycle**: 2026-08-13 03:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: STATE next-actionable #1 — read the next Sandbox CI run, record two lines
- **Phase**: P3
- **Status**: in_progress

## What I tried

- Read run **31623102439** (head `a37061a`, the 02:00 cycle's tip) — the first
  Sandbox CI run in fourteen to reach a test verdict on all eight fast shards.
- Answered both halves of Q-138 from that one run: did the 18 clear, and did the
  shard wall-clock collapse.
- Tried to reproduce the residual failures the way D-228 did — a full-depth
  clone — and then tightened that clone until it was CI's *exact* input:
  `--no-local` clone (639 commits), then a checkout of `refs/pull/67/merge`
  itself (`f0d491b`), which is what `actions/checkout` gives a `pull_request`
  event rather than the branch head.

## What worked / what failed

- 🔴 **The wall-clock did not collapse.** Shard 1 ran **821 s** at
  `fetch-depth: 0` against **753 s** at depth-1 — 9 % *longer*, not shorter. So
  the twelve cancellations were **suite size, not checkout depth**, and D-227's
  8-way shard was **necessary, not symptomatic**. Q-138's timing half is
  answered, and answered against the lean stated when it was opened.
- **13 of 19 failures cleared, not 18.** Six remain: 1 + 2 + 1 + 2 across shards
  4/3/5/6. D-228 predicted 18 from a **3-test sample** (the workflow comment says
  so: "three representative CI failures pass at full depth"); the generalisation
  to 18/19 was never measured.
- 🔴 **The instrument that licensed D-228 cannot see four of the six.** In a
  clone whose tree hash is *byte-identical* (`5bc090d`) to the pushed tree, at
  full depth, checked out at the exact merge commit CI checks out, the four
  `cycle_artifacts` / `push_claim_gate` failures **pass in 1.43 s**. Tree,
  commit, and depth are therefore all excluded as causes.
- 1 of the 6 does reproduce in the clone —
  `test_quoted_counts::test_the_reach_...`, the gitignored `results/receipts/`
  case that STATE already named as structurally unpassable in CI (#2).
- ⚠️ **Not finished**: the one remaining difference is that CI runs a 15–16-file
  shard in **one** pytest process while the local receipt shards across 16 cores
  in a different grouping. I started shard 3 in the clone to test intra-shard
  interaction and it exceeded my 120 s probe cap (CI spends 406 s on it). So the
  cause is **named and unconfirmed** — recorded as Q-139, not as a finding.

## North-star delta

- No planner movement. This is CI-authority work; the substantive result on the
  board is still D-225's paired cafe reading.
- The authority is **partially** restored: 4 of 8 fast shards are green and the
  suite now reaches a verdict instead of being cancelled, so the six are a real
  finite list rather than silence.

## Key learnings

- **A reproduction that shares the tree can still not be the tree's test.** Three
  variables were plausible (tree, commit, depth) and all three are now excluded
  by construction rather than by argument. What is left is the *process shape* —
  which is the one thing a clone copies least.
- **D-228's number was a sample, and the workflow comment said so honestly** — the
  failure was reading "three representative" as licence for "18 of 19". The
  comment is corrected in this cycle rather than left to be re-read the same way.
- The cheap half of Q-138 paid: one `gh` call decided that D-227's shard was
  necessary, which is the difference between keeping it and treating it as
  scaffolding to remove.

## Recommended next 1–3 priorities

1. **Run shard 6 to completion in the clone** (`test_cycle_artifacts`, 271 s in
   CI) — the direct test of the intra-shard hypothesis (Q-139).
2. **`test_quoted_counts::test_the_reach_...`** — skip-when-absent with a *named*
   reason (never silent, D-044); it is the one failure whose cause is settled.
3. **Wire `ci_verdict fetch_latest` into Phase 1 (Q-137)** — still unbuilt; a
   third consecutive cycle found a CI fact by hand.

## Artifacts
- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic)
- Files touched: `.github/workflows/sandbox-ci.yml`, `docs/decisions.md`, `docs/deliberations.md`, `journal/2026-08/13-03-the-clone-cannot-see-four-of-the-six.md`, `results/p3-epistemic-shadow-cost-critic.tsv`
- TSV row appended: pending

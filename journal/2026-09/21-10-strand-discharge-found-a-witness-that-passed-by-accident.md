# Strand discharge found a witness that passed by accident

- **Cycle**: 2026-09-21 10:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: `strand-discharge` D-112 obligation from STATE #1 (`cycle_artifacts stranded` rc=1: 6 commits local-ahead since 09-12)
- **Phase**: P3
- **Status**: in_progress

## What I tried
- Step-0 readings all clean except `stranded` (rc=1). Ran the full suite (954 s, 14 shards) on the unmodified strand tree to earn the push receipt.
- It came back **4530 passed / 1 failed**: `test_guard_witness.py::test_each_witness_makes_its_guard_raise[guard_direction.readings]`.
- Diagnosed and fixed that one witness (`acd66a7`), then re-took the suite on the fixed tree (result not stated here: this file is written before the receipt, D-315).

## What worked / what failed
- The failure was not the strand's fault. `_w_readings` built its "unprobed" twin from `gr.revocable()[0]`, which today is `arrival_spread.separation_survives` — a scalar-reading guard. `unprobed_revocable` derives its obligation from `revocable_collections`, so it returned empty and the intended `ProbeError` never fired.
- The witness was `SATISFIED` in every earlier run only by accident: with `/tmp/guard-witness-unused` already present, the liveness check's `git commit` failed ("nothing to commit") and that unrelated `ProbeError` matched the expected class name. On a clean tmp dir it reads `NO_RAISE`. Reproduced with a fresh `TMPDIR` (fail) and confirmed the fix on a fresh `TMPDIR` (44 passed across the witness + guard_direction files).
- Likely red on a clean runner unless its git identity makes the liveness commit fail the same way (not checked). Probably latent since `dd9ab53` (08-14) added `arrival_spread.separation_survives`, which sorts first; not bisected.

## North-star delta
- No movement toward avoidance/tracking — pure repair debt again (9th day of the strand). The value is that the strand's blocker was a latent test defect, not another stale pin, and it is now removed at the root.
- Cycle overran the 35 min soft budget: `SUITE_UNAFFORDABLE` was read at 17m30 after the first suite; a second suite was the only way to a receipt.

## Key learnings
- A witness that matches on exception *class name* can be satisfied by the wrong raise site. `WRONG_EXCEPTION` only catches a different class; it cannot catch the right class from the wrong line. Worth a follow-up: have witnesses also pin the message/site fragment.
- "Passes in isolation, fails in the sharded run" here meant *tmp-dir state*, not shard order. Check `TMPDIR` residue before suspecting pollution.
- PR #67 was closed by the user this morning (new PR deferred), so no PR is opened for this push.

## Recommended next 1–3 priorities
1. Confirm `cycle_artifacts stranded` reads clean at next REVIEW step 0 (STATE cannot attest the push, D-112).
2. Proximity-gated `w_heading` term for the knee+shape arm (D-499's window 0.32–1.05 m).
3. Have `guard_witness` witnesses pin the raise site, not just the class name.

## Artifacts
- PR: none opened (PR #67 closed 2026-09-21 by the user; new PR deferred)
- Files touched: eval/mppi_sandbox/guard_witness.py, results/p3-epistemic-shadow-cost-critic.tsv, this file
- TSV row appended: yes

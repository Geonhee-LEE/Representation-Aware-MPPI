# The push gate, moved to where the caller's shell cannot reach it

- **Cycle**: 2026-08-12 17:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: STATE next-actionable #1 — D-221 authoring (no Notion page; MCP unpermitted non-interactively)
- **Phase**: P3
- **Status**: keep

## What I tried

- Recorded the 16:00 gate-piping failure as **D-221**, and — the part STATE
  called "if cheap" — made it structural rather than only written down.
- Added `eval/mppi_sandbox/push_licence.py` + `scripts/githooks/pre-push`: the
  hook re-runs `push_preflight.check` as **`git push`'s own callee**, on a
  receipt recalled from `receipt_store` by worktree fingerprint (no argument, so
  it cannot be aimed at a friendlier file).
- Wired it with `core.hooksPath = scripts/githooks` and added `status`, which
  fails closed (rc=1) when a clone has the hook file but not the config.
- 22 tests in `eval/mppi_sandbox/tests/test_push_licence.py`.

## What worked / what failed

- **The guard was verified by being fired, not by being reasoned about.** A
  dry-run push with a real commit to move was refused with `NO_RECEIPT`, and
  the push did not happen **while its output was piped through `tail`** — which
  is the 16:00 command shape exactly.
- The first dry-run (before the commit) returned ALLOW: nothing was being
  pushed, so git fed no ref lines and the hook correctly abstained. Worth
  noting because that reading would have looked like a working guard and was
  evidence of nothing.
- `inert_surface staged` again reported "STATE.md, journal/, results/ — this
  cycle added a reader". Attribution is the known-unreliable one (09:00 proved
  the same reading reproduces at HEAD); the pins are inherited. I paid it by
  **ordering every write before the suite** so the cycle bought one suite, not
  the two that cost 13:00 and 14:00 their budgets.

## North-star delta

- **No movement on the experiment.** The 3-scene interaction result is
  unchanged; nothing was measured about MPPI, representations, or scenes.
- Movement on the executor: the last cycle's unlicensed push is now a shape
  that cannot recur by accident, and the failure is on the record.

## Key learnings

- **A callee cannot police shell composition, so it has to stop being called by
  the shell.** The three obvious repairs all fail for the same reason: pipefail
  fixes this snippet not the next one; stdout-is-a-pipe detection is red on
  every honest cron run (D-044's muted check, bought at full price); and
  `/proc` cannot distinguish "my exit code is read" from "discarded". The
  property that failed was never "was the gate run" — it ran and it refused —
  but **"did the refusal reach the push"**.
- **The limit is the argument, not an asterisk on it.** `--no-verify` still
  bypasses this. That is acceptable precisely because the repaired failure was
  a cycle that *believed it was gated*, and `--no-verify` is a cycle saying so
  out loud in a command that lands in the journal and the cron log.
- **Wiring that no commit can carry needs a reading, not an assumption.** A
  fresh clone gets `pre-push` and no `core.hooksPath`; `status` returning rc=1
  is the only thing separating "installed" from "believed installed" — the same
  disease one level up.

## Recommended next 1–3 priorities

1. **Q-133 (`carried_drift`'s offence)** — now the longest-standing open item on
   this branch; still blocks nine `test_guard_direction` probe reds.
2. **A scene outside the `cafe_*` family** — the capability step the 3-scene 2×2
   is waiting on; `SIGN_FLIP` has no prior there.
3. **Re-probe the `journal/`/`results/`/`STATE.md` pins** — 13:00 and 14:00 each
   lost a suite to this and it is now the most expensive standing item.

## Artifacts

- PR: #67 (already open — D-140: pushing to an open PR costs zero new review bandwidth)
- Files touched: `eval/mppi_sandbox/push_licence.py`, `eval/mppi_sandbox/tests/test_push_licence.py`, `scripts/githooks/pre-push`, `docs/decisions.md`
- TSV row appended: yes

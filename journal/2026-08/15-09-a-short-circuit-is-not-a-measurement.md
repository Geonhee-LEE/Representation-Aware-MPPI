# A short-circuit is not a measurement

- **Cycle**: 2026-08-15 09:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: `<render-unreachable>` Render `UNREACHABLE` as `—` instead of `0 -> 0`
- **Phase**: P3
- **Status**: keep

## What I tried

- Took D-277's own registered next-cycle item — the one it filed under
  "부수 소득 (다음 cycle 거리)" — rather than authoring something new.
- `Control.baseline` / `.tampered` become `int | None`, and `control()` fills
  them with `None` (not `0`) when it short-circuits to `UNREACHABLE`.
- `Control.delta` **refuses** (`None`) rather than subtracting two placeholders,
  and a new `Control.measured` states whether a reading exists at all.
- `report()` renders `UNMEASURED` (`—`) for short-circuited controls, reusing
  the same mark the never-controllable registries below them already printed.

## What worked / what failed

- Two tests carry the fix and are deliberately a matched pair: one pins that an
  unreachable control is *not* readable as a measured zero (`delta is None`, no
  `0 -> 0` anywhere in the report, every `UNREACHABLE` row carries the mark);
  the other pins that a **genuine** zero still prints as `0 -> 1`. Without the
  second, the fix could have moved the ambiguity to the other side instead of
  removing it — `magnitude_survival.SELF_DEFINING`'s zero baseline is a finding
  (D-076's population fact), not an absence.
- Only consumers were this module's own tests. `exclusion_scope.py:773` reads a
  `.delta` off a `predicate_inputs.drift` record — a different type that merely
  shares the attribute name. Checked before editing rather than after.
- `inert_surface staged` returned `rc=1`: staging moved 5 pins (`STATE.md`,
  `JOURNAL.md`, `RESULTS.md`, `journal/`, `results/`). Per D-207 that is a
  price, not a failure — their exemptions are withdrawn until re-probed, so
  post-receipt writes to them count as material drift. **I did not buy it
  back**: `probe` costs a second suite run and the budget could not absorb one
  after last cycle's 51m34 overrun. Paid it by following D-044's ordering
  strictly instead, so the single receipt run is taken after 4a/4a-bis and the
  only later writes are declared-local-only.

## North-star delta

- **No movement.** This is instrument repair, the fifth consecutive such cycle,
  and it is honest to say the obstacle-avoidance and path-tracking numbers are
  exactly where D-271 left them: `(lam=0.8, w_voo=5)`, 7/8 seeds at n=8.
- The defensible claim is narrower: one hour of a previous cycle was destroyed
  by this exact ambiguity, and that specific failure cannot recur.

## Key learnings

- **A placeholder that renders like a reading is worse than a refusal.** The
  short-circuit was correct and the verdict `UNREACHABLE` was correct; the only
  defect was that the *filler value* was drawn from the same alphabet as real
  data. `None` is not a smaller `0` — it is a different kind of thing, and the
  type is where that distinction belongs.
- **`delta == 0` was the trap under the trap.** Even with the row rendered as
  `—`, a `delta` that quietly returned `0` would have handed callers `INERT`'s
  exact signature for a control that never ran. Fixing the renderer alone would
  have looked complete and left the arithmetic lying.
- **The cheap item was cheap, and that is now evidence for Q-158.** This cycle
  cost one file pair and one suite; the four before it cost strand-clearing and
  12 commits. Q-158 asks whether the census tax is worth paying — the honest
  data point is that the *repairs* are cheap and the *inherited diagnoses* are
  what has been expensive.

## Recommended next 1–3 priorities

1. **Answer Q-158** with the five-cycle evidence now in hand — the tax is not
   uniform, and the split (cheap repairs vs expensive inherited claims) is the
   shape of the answer.
2. **Re-probe the 5 stale pins** when a cycle has suite budget to spare, so the
   D-044 tax stops being carried forward silently.
3. **Return to the cost-critic** — the branch's actual P3 subject, untouched
   since 04:00.

## Artifacts
- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic)
- Files touched: eval/mppi_sandbox/exemption_control.py, eval/mppi_sandbox/tests/test_exemption_control.py
- TSV row appended: pending

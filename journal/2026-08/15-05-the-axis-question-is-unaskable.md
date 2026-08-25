# The audit found no cells — it found that the question has nowhere to go

- **Cycle**: 2026-08-15 05:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: `3bcc5d39` audit the other window consumers for off-axis reads (STATE #1)
- **Phase**: P3
- **Status**: keep

## What I tried

- Took STATE #1 literally: point `window_axis_key.lookup` at the "~30 modules
  that resolve windows through `lam_window_key`" and grade each `ON_AXIS` /
  `OFF_AXIS`, as D-273 did for the one cell it wrote.
- Enumerated the real consumer population first instead of trusting the count.
- Shipped `eval/mppi_sandbox/window_axis_reach.py` + 10 tests: grade each
  resolver by whether its **signature** can accept a cost field, then AST-scan
  every call site of a resolver and grade the site by what it can express.
- Derived the discriminator rather than typing it — the cost-field parameter
  name is read off `window_axis_key.lookup` itself (D-047 discipline, same as
  `calibrated_axes` reading the axis set off `ab.lam_ladder`).

## What worked / what failed

- **The audit cannot be run as specified, and that is the finding.** Most
  consumers do not call `lam_window_key.lookup` — they go through
  `lam_window_index.resolve(scenario, controller, weight: float, index=None)`.
  A float. There is nowhere to put `w_voo`. The axis question is not merely
  unanswered for them; it is **unaskable through the API they use**, so no
  amount of pointing D-273's instrument at them produces a grade.
- **Production reach is 1 of 10.** Ten production call sites resolve a window;
  the only axis-aware one is `window_axis_key.q154` — the lookup D-273 wrote to
  ask the question. The other nine include all four inside `lam_window_index`,
  `scene_transplant`'s rung screen, and `calibrated_ladder.window_is_keyed`.
  The "~30 consumers" in STATE were mostly test call sites (47 of 57).
- **The enforcing path is one of the blind ones.**
  `comparison_headroom.assert_certified` is the family's only entry point that
  *raises* — D-143's fix for "`resolve` supplied the window and nothing
  consumed it" — and it resolves through the index. It refuses loudly on
  `w_obs_soft` and is structurally silent on every other axis, which to a
  caller reads as though it checked both.
- **My first instrument named the wrong function.** I tested the *enclosing*
  function for a `raise`; `certify` does not raise, `assert_certified` does, one
  level up. The first reading reported `lam_window_key.seed_census` and missed
  the site the docstring was about. Fixed by closing the call graph downward
  from raising functions — and labelled an **upper bound**, since a syntactic
  scan cannot show the `raise` is conditioned on the resolution.
- The closure does not swallow everything: 2 of 49 blind consumers are
  enforcing, so the grade still discriminates (pinned by a test).

## North-star delta

- No movement on obstacle avoidance or path tracking. Subtractive again: one
  planned audit is retired as unrunnable and replaced by a measured reason.
- One **latent** hazard found rather than a cell graded: the repo's strictest λ
  guard certifies operating points on a cost field it never sees. Nothing is
  known to be wrong today — `AXIS_BLIND` says the question cannot be put, not
  that the answer would be `OFF_AXIS`.

## Key learnings

- **"Audit the other N consumers" presumes they share an interface.** The cheap
  first move was enumerating the population, not running the instrument; the
  count in STATE was off by ~3× and, more importantly, wrong in kind.
- **A guard's reach is bounded by the narrowest signature on its path.**
  `window_axis_key` composes correctly onto `lam_window_key` and still reaches
  almost nothing, because the traffic routes around it through the index.
- **Enforcement is transitive and the shallow test looks plausible.** It
  returned a real function with a real `raise`, just not the load-bearing one —
  a wrong answer that would have survived review.

## Recommended next 1–3 priorities

1. **Q-157: widen `lam_window_index.resolve` with `cost_field=`** — the repair
   this measurement argues for. Deliberately not done here: it changes the
   enforcing path three modules depend on, and measuring a thing in the cycle
   that changes it is what D-268 (d) and D-274 both declined.
2. **`essps_mppi` first slice (Q-156)** — per-iteration solve as a *new*
   registry name, compared against `risk_mppi`'s `69/115` band-compliance bar.
3. **Ensemble-at-n16 (Q-153)** — re-read `(lam=0.8, w_voo=5)` at
   `CENSUS_LADDER_SEEDS = 16` so `7/8` becomes comparable to the census.

## Artifacts

- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic)
- Files touched: `eval/mppi_sandbox/window_axis_reach.py`,
  `eval/mppi_sandbox/tests/test_window_axis_reach.py`, `docs/decisions.md`,
  `docs/deliberations.md`, `results/p3-epistemic-shadow-cost-critic.tsv`
- TSV row appended: yes

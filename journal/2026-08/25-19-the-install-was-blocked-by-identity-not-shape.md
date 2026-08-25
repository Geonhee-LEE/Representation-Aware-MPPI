# The install was blocked by the table's identity, not its shape

- **Cycle**: 2026-08-25 19:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: `2b3f9c11` Install the saved 8-controller table + repair the test cascade
- **Phase**: P3
- **Status**: in_progress

## What I tried
- Picked STATE #1 — install `results/readings/2026-08-25-17-lam-windows-8-controller.yaml`
  as `eval/scenarios/lam_windows.yaml` and repair the cascade D-457 priced at
  16 reds plus 8 cascading. Zero recompute, the table was on disk.
- Copied it in and ran the targeted lam/window/calibration subset to get the
  real red list before spending a suite on it.
- The subset died on the **first collection**, not on a controller count.
- Cut scope at that reading (D-181) rather than resolving the blocker blind:
  reverted the install, and shipped the blocker as a 0.12 s guard instead.

## What worked / what failed
- **The install does not fail the way it was priced.** The parked table records
  `calibration_weight: 10` — correctly, it was walked there — and
  `lam_window_index.TABLES` already holds `variants/lam_windows_w10.yaml` at
  w=10. `build_index` raises `WeightCollision`, and `test_lam_window_index.py`
  builds the index **at import time**, so the whole module goes down before a
  single `2 -> 8` literal is reached. A *collection error*, not a failure.
- **The two constraints never name each other.**
  `test_lam_window_keying.py::test_shipped_table_is_still_unkeyed` says
  "Delete this test in the same commit that regenerates the table" — read
  alone, that is an instruction to keep the header and drop one test, which is
  exactly the move that collides. Neither module mentions the other, so the
  conflict is only observable from a tree where the install already happened.
- **STATE's "the compute standing between here and 8/8 is now zero" was true
  and misleading.** The compute is zero. The install is still blocked, for a
  reason with nothing to do with the controller count.
- `census_preempt` returned 8/8 CLEAN on the tree that carried this. So did the
  D-457 cascade census. Neither is wrong — they enumerate sites that assert the
  table's **shape**, and this one asserts its **identity**.
- The targeted subset never returned a red list: it was still running rollouts
  at the ~6 min mark and was killed. The cascade's real size is still unmeasured.

## North-star delta
- No rollout evidence; the P5 headline is still 2/8 on the controller axis.
- Negative-but-real: the remaining distance to 8/8 grew by one decision that
  nobody had costed. Better to know it at 0.12 s than at minute 20 of a suite.

## Key learnings
- This is the D-317 / D-344 / D-433 / D-455 / D-457 shape a sixth time, and the
  uncovered population is a new *kind*: not a set of pin sites but a set of
  **rules**. Every census this repo owns re-derives populations of assertions
  about magnitudes. None re-derives the constraints two modules place on the
  same file.
- An estimate that has been narrowed twice can still be narrow in a third
  direction. D-457 priced the cascade, D-470 priced the compute; both were
  right, and the install was blocked by neither.
- "Zero recompute" is not "zero risk". A parked artifact is cheap to install
  and that is exactly why nobody re-checked what installing it would mean.

## Recommended next 1–3 priorities
1. **Resolve the keying collision (Q-202), then install.** Three options are
   written out in `test_lam_table_install_collision.py`; (b) retiring the w10
   variant looks right — the parent at w=10 is a strict superset (72 cells vs
   24, 8 controllers vs 2) — but `test_table_merge.py` reads the variant by
   path and it is unverifiable without a full suite. Budget the whole cycle.
2. **Measure the actual cascade.** D-457's 16+8 is still unconfirmed on this
   tree; the targeted subset needs a `--timeout` and a rollout-free selection
   so it returns inside a cycle.
3. **Adjudicate `cafe_cut_in_v0`** — unchanged from STATE, empty window for all 8.

## Artifacts
- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic)
- Files touched: eval/mppi_sandbox/tests/test_lam_table_install_collision.py, docs/decisions.md, docs/deliberations.md, results/p3-epistemic-shadow-cost-critic.tsv
- TSV row appended: yes

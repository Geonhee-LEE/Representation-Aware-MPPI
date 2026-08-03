# The pin was honoured and the tests failed anyway — it was never numpy

- **Cycle**: 2026-08-03 11:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: `STATE#1` Confirm the slow half green under the pin
- **Phase**: P3
- **Status**: keep

## What I tried

- Took STATE item #1 as written — read the `pytest (slow closed-loop)` job on PR
  #67 after `65928ec` rather than assuming it. It is **red at 25m46s**, same five
  tests, and its header reads `eval numpy: 1.26.4 (calibrated)`.
- That combination falsifies D-032's causal claim on sight: the cause was held at
  its calibrated value and the effect persisted. So I stopped treating it as a
  failure to fix and treated it as a diagnosis to redo.
- Ran a three-arm control on this box, one variable at a time — the thing D-032
  did not do, because its `/tmp/np2lib` install had swapped numpy version **and**
  build (Debian deb → PyPI wheel) simultaneously.
- Corrected the record in place and made the real coordinate visible.

## What worked / what failed

- **The three arms, all on this box, same code and seeds:**

  | arm | result |
  |---|---|
  | deb 1.26.4 (system `blas`), AVX-512 on | **2 passed**, 116.8 s |
  | PyPI wheel 1.26.4 (`openblas64`), AVX-512 on | **2 passed**, 129.2 s |
  | deb 1.26.4, AVX-512 masked via `NPY_DISABLE_CPU_FEATURES` | **2 failed** |

- **Arm 2 kills the build hypothesis** — I expected it to be the answer (deb vs
  manylinux wheel, system BLAS vs bundled OpenBLAS 0.3.23) and it passed.
- **Arm 3 is exact, not merely consistent.** `test_scale_match` yields
  `0.17901180719252627` locally under AVX2; CI's failure reads
  `0.17901180719252627`. Seventeen digits. That is not a correlation, it is the
  same computation.
- The dev box is a Ryzen 9800X3D (AVX-512); the runner has none. AVX-512 and
  AVX2 kernels reduce in a different order, and the closed loop amplifies it
  across a threshold.
- **numpy 2.5.1 was real but incidental** — it perturbs the same knife-edge, so
  D-032's measurements reproduce. Only the attribution was wrong.
- Fast half **238 passed / 127 skipped / 1 xfailed**, 114.3 s (was 233 — the 5
  new guards).

## North-star delta

- **No avoidance or tracking number moved.** Second consecutive cycle whose
  entire output is negative information about the instrument.
- But the instrument is now *correctly* described rather than confidently
  mis-described, and CI is **bit-reproducible on demand** — masking AVX-512
  locally recreates the runner exactly. A divergence that reproduces to 17 digits
  is debuggable; one attributed to the wrong cause is not.
- Against "완벽 in **all** environments": CPU is unambiguously part of "all
  environments", and a headline that reads 2.0× on one and 1.029× on another is a
  sharper counterexample than the numpy one it replaces.

## Key learnings

- **A pin that is honoured while the failure persists is a disproof, not a
  pending fix.** The green-looking header line `numpy: 1.26.4 (calibrated)` was
  actively misleading — it asserted the environment matched while measuring a
  different machine. Same shape as Q-053's missing surface label, one level down.
- **Changing two variables to explain one effect explains nothing.** D-032's
  experiment was decisive-looking (5 pass / 5 fail, one box) and still wrong,
  because `pip install numpy==2.5.1` moved the build too. The fix cost three
  controlled runs.
- **The fingerprint should outlive the question that prompted it.** I report the
  whole SIMD found-set rather than an AVX-512 boolean; the next divergence will
  not be this one, and a diagnostic that only answers last time's question is
  exactly how D-032 got written.
- Corollary for every constant on this branch: D-029/D-030 need a scope line
  reading **"measured under `AVX512_SKX`"**, not "measured under numpy 1.26.4".

## Recommended next 1–3 priorities

1. **Q-055 — decide which constant set is canonical**, AVX-512 or AVX2. Lean AVX2
   *for verifiability, not correctness*; it retracts D-030's headline, so it is
   gated on Q-054's sweep and belongs on the re-baseline branch.
2. **Q-054's fragility sweep, re-axed onto dispatch** rather than numpy version.
   5 of 358 tests flip; drawing that boundary is still the informative step.
3. **Stop expecting PR #67's slow half to go green.** Under D-033 it is
   *correctly* red until Q-055 is answered — it is measuring an AVX2 machine
   against AVX-512 constants. Do not re-check it as if it were pending.

## Artifacts

- PR: #67 (existing — no new review bandwidth consumed)
- Files touched: `eval/conftest.py`, `eval/mppi_sandbox/tests/test_calibrated_numpy_pin.py`,
  `eval/requirements-ci.txt`, `.github/workflows/sandbox-ci.yml`,
  `docs/decisions.md` (D-033 + D-032 status), `docs/deliberations.md` (Q-055 + Q-054 premise)
- TSV row appended: yes

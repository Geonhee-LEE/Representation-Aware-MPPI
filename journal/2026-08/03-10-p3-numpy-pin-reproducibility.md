# The slow half was not green — and the reason was numpy, not the code

- **Cycle**: 2026-08-03 10:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: STATE #1 — confirm the `slow` half green on both surfaces
- **Phase**: P3 (calendar P4; work is the P3 epistemic-channel branch)
- **Status**: keep

## What I tried

- Took STATE #1 — "~2 min of checking" — and it answered **no**: `gh pr checks 67`
  shows `pytest (slow closed-loop)` **fail at 23m59s**. Not a timeout (ceiling is
  60 min); the job ran to completion and **5 tests genuinely failed**.
- The five are exactly the D-029 / D-030 evidence: `test_ab_temperature_protocol`,
  `test_exposure_timing_band`, `test_hazard_exposure`, `test_horizon_audit`,
  `test_scale_match`. All had been reported passing locally for 26 cycles.
- Suspected the environment, then **tested it instead of inferring it**: installed
  numpy 2.5.1 into `/tmp/np2lib` (base env untouched) and re-ran the five on
  **this box** with only `PYTHONPATH` changed.
- Shipped the pin (`eval/requirements-ci.txt`, both CI jobs), a header that names
  the numpy version every run, and 3 free tests tying the pin to the constant.

## What worked / what failed

- **Controlled and decisive**: 1.26.4 → **5 passed (149.95 s)**; 2.5.1 → **5 failed**.
  Same box, same seeds, same code. The sandbox seeds via `np.random.default_rng`,
  whose stream is version-stable by policy, so this is **not** an RNG change — it
  is FP drift (SIMD / reduction order) amplified by a chaotic closed loop.
- **The sharpest number, and it is bad news**: D-030's headline horizon swing reads
  **2.0× on 1.26.4 and 1.029× on 2.5.1**. The test's own failure message says a
  sub-1.2× swing means "a fixed-`w_voo` horizon column is honest after all" — so
  the *sign of the conclusion* depends on a numpy minor version.
- **CI and the dev box had been measuring different things all along**: the
  workflow's `pip install --quiet numpy` resolved to 2.x on the runner while every
  D-029/D-030 constant was calibrated on 1.26.4. Nobody pinned; nobody compared.
- **Cross-checked local-np2 against CI-np2**: one statistic agrees to ~9 significant
  figures (0.0362103793 vs 0.0362103796), another differs **~3%** (0.03322 vs
  0.03434). So numpy is the dominant term but **not the only one** — pinning does
  not buy machine-independence, and I said so in the file rather than implying it.
- Fast half after the change: **233 passed / 127 skipped / 1 xfailed in 114.8 s**
  (+3 new, no regression).

## North-star delta

- **No avoidance or tracking number moved — and one moved backwards.** This cycle's
  real output is negative information: a chunk of the D-029/D-030 evidence is
  weaker than recorded, because it is conditional on an FP environment nobody
  had written down.
- Against "완벽 in **all** environments", a result that flips on a numpy bump is
  the smallest possible counterexample to environment-independence, found in the
  cheapest possible place. Better here than on hardware.
- The 가려진-obstacle class still has one working cost term (D-027); its
  supporting horizon claim is now **explicitly provisional** rather than silently so.

## Key learnings

- **"Local passes" and "CI passes" were never the same assertion, and the gap was a
  dependency version.** Q-053 diagnosed the missing *surface* label; the surface
  turned out to include the dependency set. The header now prints numpy next to
  the mode — the same repair, applied one level deeper than Q-053 anticipated.
- **A threshold test encodes a claim; a claim that moves 2.0× → 1.029× under a
  library bump was measuring the library too.** The instrument-scope pattern from
  D-028 (denominator), D-030 (relative guard) and D-031 (fixture scope) repeats:
  the measurement was fine, its *boundary* was drawn in the wrong place.
- **Pinning is a reproducibility contract, not a fix** — worth stating loudly,
  because a green CI after a pin looks exactly like a solved problem. Q-054 keeps
  the real question open instead of letting the green check close it.
- **Guards belong in the fast half.** A check that only runs in the 24-minute job
  is a check nobody watches fail — the same blindness D-031 just fixed.

## Recommended next 1–3 priorities

1. **Confirm the slow half under the pin** — genuinely unverified at cycle end (CI
   needs ~24 min). Name the job in STATE this time: `pytest (slow closed-loop)` on
   PR #67. This is the *second* cycle to hand this check forward; do not assume it.
2. **Q-054 (d): quantify which conclusions are FP-fragile** — perturb at the ~3%
   residual scale and see whether 5-of-358 is the true fragile set or just the
   part that crossed a threshold. Belongs on the re-baseline branch (STATE #16).
3. **Re-read D-030's status** once (1) lands. If the pin holds it green, D-030
   stands *as pinned*; its scope line should say so.

## Artifacts

- PR: #67 (already in queue — no new review bandwidth)
- Files touched: `eval/requirements-ci.txt` (new), `.github/workflows/sandbox-ci.yml`,
  `eval/conftest.py`, `eval/mppi_sandbox/tests/test_calibrated_numpy_pin.py` (new),
  `docs/decisions.md` (D-032), `docs/deliberations.md` (Q-054)
- TSV row appended: yes

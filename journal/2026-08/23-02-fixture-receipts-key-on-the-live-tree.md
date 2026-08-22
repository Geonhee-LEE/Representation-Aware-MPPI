# Fixture receipts key on the live tree — Q-180's "exposure is 0" was wrong

- **Cycle**: 2026-08-23 02:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: `receipt-store-test-isolation` (STATE #3)
- **Phase**: P5
- **Status**: keep

## What I tried

- D-112 step 0 read `rc=1`: `0dd21b7` (D-433) was finished on disk and had never
  reached origin. Discharging it was the first obligation, so this cycle is a
  strand repair plus the smallest zero-integration item on STATE's list.
- Picked STATE #3 (`receipt-store-test-isolation`) because it needs no new
  rollouts and the suite deadline was already ~7 min out.
- Located the leakers by grepping for `receipt_store` calls that pass **no
  root**: `test_receipt_store.py:106` and `:150`. Every other call site in
  `test_licence_recall.py` / `test_quoted_counts.py` already threads `tmp_path`.

## What worked / what failed

- **Q-180's severity assessment was wrong, and in the load-bearing direction.**
  It recorded 2 leaked entries whose fingerprints were "synthetic, so never
  recalled". Measured: **43** entries, and both leakers key on
  `tp.stamp().worktree_fingerprint` — the **live** tree. `recall_current()`
  returned HIT and `push_licence.licence_path()` pointed straight at a fixture.
- What actually held the gate is a *different* check than Q-180 credited: the
  fixture's `command=('python3','-m','pytest')` names 0/3 declared targets, so
  `push_preflight.check` returns `SCOPED`/ok=False. Exposure is 0 today, but the
  margin is one field — a fixture spelling the real command would have licensed
  a push of an unmeasured tree (D-082).
- Fix: `:150` gets `monkeypatch.setattr(rs, "STORE_DIR", tmp_path)` (absolute
  override wins the join, so the CLI's default-root writes land in tmp). `:106`
  *must* stay on the production store — its claim is about this repo's ignore
  rules — so it now write-asserts-unlinks in a `finally`.
- Purged the 43 residues; `recall_current()` now correctly misses.
- **The pin cost a D-044 tax and I paid it knowingly.** `inert_surface staged`
  read `STAGED_MOVED` on 5 pins (`JOURNAL.md`, `RESULTS.md`, `STATE.md`,
  `journal/`, `results/`) because the new regression test reads `rs.entries()`
  — a reader of `results/`. Harmless *this* cycle (every mandated write was
  already done before the receipt), but future cycles writing those paths now
  face material drift. Worth it: the pin catches exactly the failure that sat
  undetected for a day, and D-207 calls this a price rather than a failure.

## North-star delta

- **No movement on 물체회피 / 경로추종** — this is gate machinery, not control.
  Clearance stays 16/16 and the heading residual is untouched.
- The push gate's guarantee is *restored to being a guarantee* rather than an
  accident of fixture values. That protects every future measured claim.

## Key learnings

- **A "harmless because it can never collide" verdict deserves the collision
  test, not the payload inspection.** Q-180 read the fixture's `head` and
  `worktree` fields — synthetic — and inferred the key was synthetic too. One
  `recall_current()` call falsified that; it cost about a second.
- **Two independent checks can look like one.** The store was safe because of
  `SCOPED` (declared-target coverage), not because of fingerprint mismatch. A
  reader who knew only that "the gate refused" would have drawn Q-180's
  conclusion. Record *which* check refused.
- A test that legitimately must touch a production surface should clean up in
  `finally`, not be relocated to `tmp_path` — relocating it deletes the claim.

## Recommended next 1–3 priorities

1. Answer Q-181 — correlate per-seed `heading_err_rms` against clearance /
   detour magnitude across the arms already measured (STATE #1, still the
   science bottleneck; needs ≤ 32 integrations or none).
2. `census-only-push-subset` — now deferred four cycles; this cycle again spent
   the majority of its budget on the suite.
3. Audit the remaining 318 store entries for any *other* non-measurement shape
   (the pin added here only catches the `{"eval/x.py": "d1"}` sentinel).

## Artifacts
- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic)
- Files touched: eval/mppi_sandbox/tests/test_receipt_store.py, docs/decisions.md, docs/deliberations.md, results/p3-epistemic-shadow-cost-critic.tsv
- TSV row appended: yes

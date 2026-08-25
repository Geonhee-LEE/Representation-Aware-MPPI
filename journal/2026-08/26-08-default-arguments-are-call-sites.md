# A default argument is a call site — the remainder was 18× the estimate, not an order of magnitude below it

- **Cycle**: 2026-08-26 08:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: STATE #1/#2 — read the receipt's shard attribution, then act on what it says
- **Phase**: P3
- **Status**: keep

## What I tried

- Took STATE #1 for free: the 07:00 receipt (`results/receipts/70d4824ecf988041.json`) already
  carried `shard_seconds`, so the attribution needed no new suite — a `json.load`, per the
  D-315 probe that opened this cycle (`GRADED`, so no suite was owed for the read).
- Read the per-shard split, then the `--durations=40` sidecar for the shard that owns the wall.
- Found STATE's own conditional to be mispriced by 18×, and acted on the corrected reading
  rather than on the written one.
- Converted the two remaining full-price screens onto D-475's existing session fixture.

## What worked / what failed

- **The wall is shard 11, and it is exactly the total**: `shard_seconds[10] = 950.72 s` against
  `duration_seconds = 950.72 s`. Runner-up is shard 2 at 624.19 s, so the headroom before the
  wall stops being shard 11's is **326.5 s** — that number bounds everything below.
- **`test_exemption_masking` still owns it**, so STATE's conditional fired. But the candidates it
  named were the wrong ones. STATE priced the remainder as "four `em.screen_one(route)` sites
  (~6 s each)" ≈ 24 s and called it an order of magnitude below D-475's yield. The durations say
  the real remainder was **240.41 s + 197.31 s = 437.7 s** in two tests D-475 never saw.
- **Why D-475 missed them, and it is not carelessness**: `em.unscreened()` and
  `em.masking_candidates()` both take `screened: Iterable[Screen] | None = None` and call
  `screen()` internally when it is omitted (`exemption_masking.py:502`, `:510`). D-475 enumerated
  by grepping `em.screen(`, which cannot see a screen that happens inside a defaulted argument.
- **Both tests only *read* the screen's result**, which is the fixture's own stated admission
  criterion — unlike `test_suppression_is_restored_after_every_screen`, which calls `screen()` to
  assert it leaves no module global patched and must stay live. So the conversion is the fixture's
  existing rule applied, not a widening of it.
- **Measured, whole file, green**: `24 passed in 350.01s`, with
  `test_masking_class_is_bounded_at_one_by_measurement` going **197.31 s → 1.09 s call** and
  `test_no_pair_is_left_unscreened` giving up its 240.41 s call to host the 170.50 s fixture setup
  instead. The file's floor is now two deliberately-live screens (170.50 setup + 171.02
  restoration = 341.5 s of the 350.01 s), and the restoration one is not a defect to remove.

## North-star delta

- **No direct movement** — rollout count 0, no controller, no scenario, no metric. This is the
  seventh consecutive harness cycle.
- What it buys is the same thing D-475 bought, and the arithmetic is now the honest version:
  removing 437.7 s from shard 11 puts it at ~512.8 s, which is **below** shard 2's 624.19 s. So
  the suite wall goes **950.72 s → ~624 s, −327 s**, not −438 s. The saving is capped by the
  headroom, exactly as the shard-graph learning from 07:00 predicts — and this cycle is the first
  to state that cap *before* the receipt rather than after.
- Cumulative across D-475 + D-476: **1274.7 s → ~624 s, −51%**. That is the budget objection the
  8-controller install has been deferred on for six cycles, roughly halved.

## Key learnings

- **A default argument is a call site, and a spelling census cannot see it.** D-475's enumeration
  was `grep em.screen(`; the two most expensive screens in the file were spelled `em.unscreened()`
  and `em.masking_candidates()`. The census that finds these is by **cost** — which is what
  `--durations` is — and the project already had the instrument; it just had not pointed it at the
  file after the last change.
- **Re-measure after a fix before pricing the remainder.** STATE's ~24 s estimate was written from
  the *pre-D-475* structure and carried forward as if the fix had not changed what was left. The
  receipt that would have corrected it was already on disk and unread — which is precisely the
  D-315 probe's point, arriving one cycle later than it could have.
- **The wall-clock cap should be quoted before the work, not after.** Shard 2 at 624.19 s means no
  further work inside shard 11 can buy more than 326.5 s no matter how much it removes. This
  cycle's 437.7 s removal is already 111 s past the point of diminishing return, and the *next*
  optimisation target is therefore `test_guard_reflexivity` (318.32 + 132.74 + 65.97 + 62.83 s in
  shard 2), not anything else in this file.

## Recommended next 1–3 priorities

1. **Install the 8-controller table.** The budget objection is now halved (1274.7 s → ~624 s) and
   every other blocker is already cleared — premise measured (D-472), collision resolved
   (D-471 (b)). Seven harness cycles is enough; this is the first non-harness cycle available.
2. **If more budget is wanted first, the target is `test_guard_reflexivity` in shard 2** — it is
   the new wall, and `test_report_names_its_own_findings` alone is 318.32 s. Do not look inside
   `test_exemption_masking` again: its remaining 341.5 s is two screens that must stay live.
3. **Correct the "2 controllers" figure** where D-471 / Q-202 prose repeats it — the variant is 3
   controllers × 8 scenes. Outstanding since 2026-08-25 21:00, now four cycles old.

## Artifacts
- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic)
- Files touched: eval/mppi_sandbox/tests/test_exemption_masking.py, docs/decisions.md, journal/2026-08/26-08-default-arguments-are-call-sites.md, results/p3-epistemic-shadow-cost-critic.tsv
- TSV row appended: yes

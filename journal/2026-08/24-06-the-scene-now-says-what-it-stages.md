# The scene now says what it stages — and the second speed-derived constant turned out to be inert

- **Cycle**: 2026-08-24 06:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: `3c5c5d39` [sandbox] Q-195 — crossing scene 의 정본 속도: schedule 재배치 vs 2-actor 재서술
- **Phase**: P3
- **Status**: keep

## What I tried

- Took Q-195 option **(b)**: accept the measured `calibrated_cruise(0.8) = 0.723 m/s`
  as canonical and rewrite `cafe_obstacle_crossing_v0.yaml` so the file is true
  about itself — `description`, the geometry comment block, an inline note beside
  `target_speed_mps`, and the scene's row in `eval/scenarios/README.md`.
- Quoted D-451's table verbatim as Q-195 required: declared 0.3 → band transit
  t ∈ [6.67, 13.33], **5/5** actors moving; measured 0.723 → t ∈ [2.77, 5.53],
  **2/5**.
- **Checked (b)'s "free" premise instead of assuming it.** (b) is free only if no
  graded surface reads a 0.3-derived constant. `target_speed_mps` is covered by
  D-024 — but the *same* yaml carries `expected_duration_s: 25`, which is the
  product of the same arithmetic and which, unlike `target_speed_mps`, **is
  read**. So I counted its consumers.
- Cleared the erratum the TODO body bundled: D-451 wrote the D-024 → Q-191 gap as
  "21 days"; it is 20 (2026-08-03 → 2026-08-23). Four sites fixed.

## What worked / what failed

- **Worked, and it is the one new measurement this cycle**: `expected_duration_s`
  reaches only a **timeout cap** — `run.py:58` (`max_steps = ceil(expected_duration
  × TIMEOUT_FACTOR / dt)`) and the same horizon computation at `feasibility.py:544`
  and `:788`. No metric. Measured goal arrival is t = 6.92 s against a 25 s cap =
  **3.6× headroom**, so no run on this scene was ever truncated. D-451's "every
  measurement stays valid" therefore holds for the scene's *second* speed-derived
  constant too — established by counting consumers, not by assuming the scope.
- **Deliberately not fixed**: the `25` itself. Tightening it toward 6.92 makes the
  cap binding, at which point timeout becomes a metric and (b) stops being free
  (four null sweeps re-open). Wrong-but-inert, left in place with the reason
  written down — which is what separates this from D-451's rejected alternative
  (d), "quietly fix the comment".
- The gap the scene advertises (5-actor contest) vs stages (2-actor encounter) is
  **not closed** — Q-195's lean explicitly said not to close it. Opened Q-196.
- Zero sim, zero controller lines, zero measurements moved.

## North-star delta

- **No acceptance metric moved.** This is a truth-in-labelling change on the only
  graded scene named after an obstacle.
- Indirect but real: `obstacle_reach` (the only scene grading `cte_max`) is now
  documented as a 2-actor result rather than silently read as a 5-actor one, so
  the P5 metric set inherits a *stated* scope instead of an assumed one.
- The "multiple / close / occluded" obstacle classes in the north star remain
  **untested** on this branch — Q-196 is where that gets decided, before P5 entry.

## Key learnings

- **"Free" is a claim about the consumer count, and it is cheap to check.** Q-195
  argued (b) was free from D-024 alone. D-024 covers one constant; the yaml had
  two from the same arithmetic. One grep separated inert-and-wrong from
  live-and-wrong — and if `expected_duration_s` had fed a metric, (b) would have
  been the expensive option, not the free one.
- **Wrong-but-inert is a legitimate resting state, provided the reason is
  written.** The failure mode isn't leaving `25`; it's leaving it with no record
  of why, so the next cycle re-derives the whole question.
- Same population shape as D-317 / D-450 / D-451, fourth instance, but caught
  *before* it cost anything: the question named one constant, the file held two.

## Recommended next 1–3 priorities

1. **Q-196 — decide before P5 entry (2026-09-03)** whether the advertise/stage gap
   is closed by a new contested scene (lean (b)) or by re-staging in place.
2. **Derive the `key_discrimination` narrow-key census** rather than listing it —
   red four times (D-381/395/404/452), still in neither `census_preempt` list.
3. **Q-192 + Q-183 together** — delete one of option (c)'s two conflicting
   triggers; moves the `exemption_registry` census, so budget a whole cycle.

## Artifacts

- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic)
- Files touched: eval/scenarios/cafe_obstacle_crossing_v0.yaml, eval/scenarios/README.md, docs/decisions.md, docs/deliberations.md, journal/2026-08/24-02-designed-at-a-speed-it-never-ran.md
- TSV row appended: yes

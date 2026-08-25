# P5 calibration harness §3: proper scoring rules metric axis

- **Cycle**: 2026-07-08 17:00 KST
- **Branch**: `autoresearch/p3-p5-harness-scoring-axis`
- **TODO**: `p5-harness-scoring-axis` P5 calibration harness §3 proper scoring rules axis
- **Phase**: P3
- **Status**: keep

## What I tried

- Extended `docs/p5_risk_calibration_harness.md` §3 metric table with two σ-calibration-quality rows: `ece_global`/reliability-diagram coverage and `brier_score`/`log_score` (strictly-proper scoring rules from DUCCT-MPPI arxiv:2605.28330)
- Expanded §3½ with three new subsections: (1) DUCCT-MPPI proper scoring rules as evaluation criterion — sharpness-testing beyond ECE; (2) Biased Dreams (arxiv:2604.25416) density-stratified calibration check — aggregate ECE misses OOD-tail over-confidence; (3) UT localization-uncertainty dual-uncertainty extension candidate for P3+/P4
- Updated §6 Acceptance to include criterion 5 (σ-calibration-quality row in sweep output, closes Q-015 Lean "add ECE/coverage immediately")
- Applied deadlock-breaker: closed PR #24 (energy-based regularizer, superseded by D-009) — queue dropped 6→5, unblocking this cycle

## What worked / what failed

- Doc edit is clean (56 net insertions, no regressions); build smoke not required for doc-only
- The Q-015 Lean prescription ("add ECE/coverage immediately") is now fulfilled in the spec — execution waits for P2 ensemble to land (unchanged)
- Deadlock-breaker executed cleanly (branch preserved, branch b-criterion met via D-009); STATE was incorrect that "no PR superseded by accepted D-NNN" — #24 (energy-based) is the road-not-taken architecture explicitly opposite D-009's chosen path
- Notion MCP denied (19th cumulative); Notion TODO creation (original pick from STATE) not possible; fell through to doc-lane work correctly

## North-star delta

- +1 metric axis defined for the P5 evaluation harness: proper scoring rules (Brier/log) as the strictly-proper calibration criterion, catching sharpness failures ECE misses
- +1 density-stratified check requirement added — harness must probe OOD/미관측 tail separately from aggregate ECE (directly addresses the north star's "미관측 분포" clause)
- +1 UT localization-uncertainty extension note filed — P3+/P4 candidate for the third uncertainty source alongside epistemic/aleatoric channels
- No code written; design distance to north star: P2 ensemble merge remains the blocking gate for all measurable progress

## Key learnings

- DUCCT-MPPI's proper scoring rules contribution is orthogonal to its planning contribution: Brier/log score is the evaluation methodology, applicable regardless of which planner architecture is chosen; adopting it for P5 costs nothing (no new σ source, scores whatever the ensemble emits)
- Biased Dreams' attractor-bias finding implies aggregate ECE is structurally insufficient for the OOD/미관측 guarantee — density stratification is a first-class harness requirement, not an optional refinement
- The deadlock-breaker b-criterion ("superseded by D-NNN") applied to #24 (energy-based regularizer) via D-009 (MLP-ensemble chosen); prior cycles that reported "b-criterion fails" were looking at architectural supersession too narrowly

## Recommended next 1–3 priorities

1. **Merge P2 build-path cluster** (#44 → #45 → #23 — user action); every downstream step unblocks on this
2. **Create [research]-prefixed Backlog TODOs in Notion** (HOLO-MPPI, condition-aware residual, MPPI-PID, DUCCT-MPPI proper-scoring-rules, iCrowdNav I²Former) once Notion MCP is reachable — queue now at 6 (PR #62 added), Curator merge of #60+#61 at 23:00 KST expected to drop to 4
3. **P4 kick-off spec** (2026-07-10): spec the dynamic-obstacle risk channel and Gazebo actor setup; iCrowdNav I²Former is the Phase 0 candidate for P4

## Artifacts

- PR: https://github.com/Geonhee-LEE/Representation-Aware-MPPI/pull/62 (autoresearch/p3-p5-harness-scoring-axis)
- Files touched: `docs/p5_risk_calibration_harness.md`, `results/p3-p5-harness-scoring-axis.tsv`
- TSV row appended: yes

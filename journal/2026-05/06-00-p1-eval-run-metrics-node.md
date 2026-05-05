# P1 — `eval/run_metrics.py` ROS2 wrapper for v0 metrics

- **Cycle**: 2026-05-06 00:00 KST
- **Branch**: `autoresearch/p1-eval-run-metrics-node`
- **TODO**: `357c5d39` [north-star] eval/run_metrics.py — ROS2 node wrap of v0 metrics
- **Phase**: P1
- **Status**: in_progress (PR pending; depends on PR #4 for runtime)

## What I tried

- Wrote `eval/run_metrics.py` — pure-Python helpers (`_quat_to_yaw`, `_odom_row_from_pose_twist`, `_path_rows_from_poses`, `write_summary_json`) at module top; rclpy / nav_msgs / std_srvs imports deferred into `_make_ros_node()` so smoke + unit tests don't need ROS2 sourced.
- `RunMetricsNode` subscribes to `/odom` (BEST_EFFORT) and `/plan` (RELIABLE + TRANSIENT_LOCAL); buffers a `(T, 6)` traj; on shutdown or via `~/finalize` Trigger service, calls `path_tracking_metrics.summary()` and writes `runs/<run_id>.json` with metadata.
- Added `eval/tests/test_run_metrics.py` — 9 unit tests covering yaw round-trip, traj-row contract, empty/short-input guards, and an end-to-end synthetic-line JSON-write check.
- Branched off `main` per the rule, even though `eval/path_tracking_metrics.py` only lives on PR #4 — handled by lazy import + `@skipUnless` on the integration test.

## What worked / what failed

- ✅ 8 / 9 tests pass; 1 skipped with explicit reason (`eval.path_tracking_metrics not on main yet (PR #4)`). Helpers verified against known yaw values and traj/path shapes.
- ✅ `python -m py_compile` clean — no rclpy needed at import time.
- ✅ `runs/<run_id>.json` payload schema decided: `{run_id, target_speed, n_traj, n_path, metrics: {…summary keys…}}`.
- ⚠️ Couldn't run the actual ROS node (sim is user-blocked + budget). Live `/odom` flow + QoS choice will only get exercised when PR #4 lands and someone runs the launch.
- ⚠️ Cross-PR dependency: this PR can't merge cleanly until PR #4 does. Once #4 lands, the skipped test auto-re-enables.

## North-star delta

- "정량 metric layer 가 라이브 데이터에 닿을 수 있는 코드" 가 처음 등장. v0 (offline numpy) → v2 (live ROS2 node) 점프 — v1 (rosbag helper) 은 의도적으로 스킵 (sim 이 더 빠른 first-baseline 경로).
- north-star "perfect path tracking in all envs" 의 측정 인프라가 바로 다음 sim 실행에서 첫 baseline JSON 을 토해낼 수 있는 상태. 단, sim 자체는 여전히 미실행.

## Key learnings

- Cross-PR dependency 패턴 (이 PR ↔ PR #4) 은 lazy import + `@skipUnless` 로 깨끗이 처리됨. 전부 한 PR 에 우겨넣지 않고 단계별로 합리적인 PR boundary 유지 가능 — 다음에도 쓰기.
- ROS2 노드 코드를 `_make_ros_node()` factory 안에 넣어 import 사이드이펙트를 막는 패턴이 unit-testability 와 sim-unbox 둘 다 살림. `if HAS_ROS:` 글로벌 분기보다 깔끔.
- `executor` 가 sim 을 못 돌릴 때 sim 직전 단계 (코드 + 단위 테스트) 까지 끌고 가두면 user A1 verification 직후 곧바로 첫 baseline 확보 가능. "user-blocked" 가 progress block 이 아니게 됨.

## Recommended next 1–3 priorities

1. `eval/scenarios/*.yaml` v0 — straight/curved/figure8/obstacle_crossing 4 종 start/goal/world spec. Metric "어디서 측정" 채움. claude 자율 가능.
2. `jackal_cafe.launch.py` 에 run_metrics 노드 옵션 플래그 (`include_run_metrics:=true`) — sim 실행과 동시에 자동 metric 수집. claude 자율 가능 (launch 파일만 편집).
3. (user-blocked, 의존성 그대로) A1 — Jackal cafe sim 1회 시각 검증 + RViz 캡처. PR #4 + 이번 PR 머지 직후 실행하면 첫 baseline JSON 산출.

## Artifacts

- PR: pending merge (`autoresearch/p1-eval-run-metrics-node`)
- Files touched: `eval/run_metrics.py`, `eval/tests/test_run_metrics.py`, `results/p1-eval-run-metrics-node.tsv`, `RESULTS.md`
- TSV row appended: yes (`qual:tests-8pass`, status=in_progress)
- Depends on: PR #4 (path_tracking_metrics v0 module)

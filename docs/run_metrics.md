# run_metrics — sim 실행 → 정량 JSON

`eval/run_metrics.py` 는 ROS2 노드로 `/odom` + `/plan` 을 구독해 한 run 당 **한 JSON 파일** 을 `runs/<run_id>.json` 으로 dump. 우리 자동 평가 파이프라인의 **유일한 정량 출력** (P5 calibration 까지).

수학적 정의: [`path_tracking_metrics.md`](path_tracking_metrics.md). 시나리오 yaml: `eval/scenarios/*.yaml`.

---

## 한 명령 가동

```bash
ros2 launch representation_aware_mppi_bringup jackal_cafe.launch.py \
  include_run_metrics:=true \
  run_id:=cafe-001
```

`include_run_metrics:=true` 면 launch 가 `eval/run_metrics.py` 노드를 함께 spawn. RViz `2D Goal Pose` 로 navigation → 도달 시 `runs/cafe-001.json` 자동 생성. `=false` (default) 면 byte-identical 기존 동작.

---

## launch 인자

| 인자 | 기본 | 설명 |
|---|---|---|
| `include_run_metrics` | `false` | run_metrics 노드 동시 가동 |
| `run_id` | `default` | 출력 파일명 prefix |
| `target_speed` | `0.5` | time_deviation 계산 baseline (m/s) |
| `run_metrics_output_dir` | `runs/` | JSON dump 위치 |
| `run_metrics_pythonpath` | `<repo-root>` | `eval/` import 위해 |

같은 인자가 `jackal_outdoor_sim.launch.py` (city/cafe) 에도 동일 적용.

---

## JSON schema

`runs/<run_id>.json`:
```json
{
  "run_id": "cafe-001",
  "started_at": "2026-06-03T13:30:01+09:00",
  "world": "cafe3_jazzy.sdf.xacro",
  "robot": "jackal",
  "target_speed": 0.5,
  "metrics": {
    "cte_rms": 0.18, "cte_max": 0.41,
    "heading_err_rms": 0.12, "heading_err_max": 0.31,
    "completion_final": 1.0, "time_deviation_final": -0.32,
    "jerk_lat": 2.1, "jerk_lon": 1.4, "accel_var": 0.08,
    "goal_reached": 1
  }
}
```

`metrics` block 은 `eval.path_tracking_metrics.summary()` 의 dict 그대로 — PRD § 1 "완벽" 임계와 직접 비교 가능.

---

## 시나리오 yaml 와 함께 (acceptance 자동 평가)

```bash
ros2 launch ... include_run_metrics:=true run_id:=head-on-001 \
  scenario:=eval/scenarios/cafe_head_on_v0.yaml      # planned (#39)
```

yaml `acceptance:` 블록 (`cte_rms_max`, `goal_reached: 1`, `min_distance_to_obstacle`, ...) 과 측정값 비교 → JSON 에 `pass: true/false` 추가. 시나리오 format: [`scenarios_and_controllers.md`](scenarios_and_controllers.md), generator: issue #39.

---

## 통합 위치

- `eval/run_metrics.py` — ROS2 노드 (rclpy + nav_msgs/Odometry + Path)
- `eval/path_tracking_metrics.py` — 순수 NumPy 메트릭 (lazy import)
- `eval/tests/test_run_metrics.py` — 8 unit test
- `launch/jackal_cafe.launch.py`, `launch/jackal_outdoor_sim.launch.py` — `include_run_metrics` 인자 wiring (PR #7/#8 merged)

---

## 3 사용 시나리오

### baseline 잡기
```bash
ros2 launch ... include_run_metrics:=true run_id:=cafe-baseline
# RViz 2D Goal Pose → 도달
cat runs/cafe-baseline.json
```
→ PRD § 1 임계와 비교: `cte_rms ≤ 0.2 m` (indoor) 통과? 통과 시 첫 정량 baseline.

### BEV channel on/off ablation (P1)
```bash
ros2 launch ... include_run_metrics:=true run_id:=cafe-no-bev    enable_bev:=false
ros2 launch ... include_run_metrics:=true run_id:=cafe-with-bev  enable_bev:=true
python eval/compare_runs.py runs/cafe-no-bev.json runs/cafe-with-bev.json   # planned
```

### 시나리오 × controller 매트릭스 (P5, issue #40)
```bash
for scen in cafe_straight cafe_head_on cafe_freezing cafe_convoy; do
  for ctrl in mppi mpc_cbf dpcbf dra_mppi; do
    ros2 launch ... scenario:=eval/scenarios/${scen}_v0.yaml controller:=${ctrl} \
                    include_run_metrics:=true run_id:=${scen}_${ctrl}_v01
  done
done
```

---

## 한계 (v0)

- piecewise-linear path 만 (곡선 cusp 부정확)
- collision/near-miss metric 미포함 (P5 obstacle metric)
- single path 만 — multi-waypoint sequence 는 v1
- safe_control / Gazebo 두 백엔드 통합은 issue #39 진행 중

---

## 관련

- [`path_tracking_metrics.md`](path_tracking_metrics.md) — 수학 정의
- [`scenarios_and_controllers.md`](scenarios_and_controllers.md) — 시나리오 + acceptance
- [`safe_control_harness.md`](safe_control_harness.md) — 보조 sim 트랙

_2026-06-03 KST_

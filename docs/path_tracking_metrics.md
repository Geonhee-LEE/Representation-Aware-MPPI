# Path-tracking metrics — v0

North-star alignment: 프로젝트 목표는 "**모든 환경에서 물체회피 + 경로추종 완벽**". 이 문서는 **경로추종** 절반을 정량화하는 metric 셋을 정의한다. 물체회피 metric (success rate, near-miss count) 은 별도 (P5).

v0 의 목적은 "최소 metric set 으로 자동 평가의 첫 신호 만들기" — 이후 P5 에서 calibration 하면서 가중치/임계치 조정.

## API

```python
from eval.path_tracking_metrics import summary, Goal

s = summary(traj, path, target_speed=0.5)
# {'cte_rms': 0.12, 'heading_err_rms': 0.08, 'completion_final': 1.0,
#  'time_deviation_final': -0.3, 'jerk_lat': 0.4, 'jerk_lon': 0.6,
#  'accel_var': 0.05, 'goal_reached': 1}
```

순수 NumPy. ROS 의존성 없음. 한 run 당 한 행 (CSV append) 수준의 scalar dict 반환. 시계열도 별도 함수로 노출.

## 입력 contract

| 이름 | shape | columns |
|---|---|---|
| `traj` | `(T, 6)` | `[t, x, y, yaw, v, omega]` |
| `path` | `(M, 3)` | `[x, y, yaw_target]` (yaw_target 은 control directive — segment tangent 와 다를 수 있음) |
| `goal` (선택) | dataclass | `Goal(x, y, yaw)` — 미지정 시 path 마지막 행 |

`path` 는 piecewise-linear polyline. 곡선 보간/스플라인은 v1.

## 메트릭

### 1. Cross-track error (CTE)
가장 가까운 path segment 까지의 부호 있는 수직 거리 (좌측 양수, z-up × tangent = left-normal).
- 단위: m
- 임계 가설: indoor `cte_rms < 0.2`, outdoor `< 0.5`.

### 2. Heading error
robot yaw 와 segment tangent yaw 의 차이를 [-π, π] 로 wrap.
- 단위: rad

### 3. Completion %
가장 가까운 점의 arclength / 전체 path arclength, [0, 1].
- "완벽" 필수: `completion_final ≥ 0.99`.

### 4. Time deviation
실제 경과 시간 - 목표 속도 기준 expected 시간. 양수 = 늦음.
- 단위: s

### 5. Smoothness
- `jerk_lon = sqrt(∫(d²v/dt²)² dt)`
- `jerk_lat = sqrt(∫(d²a_lat/dt²)² dt)`, `a_lat ≈ v · ω`
- `accel_var` = longitudinal + lateral acceleration variance

### 6. Goal reached
`||p_T - p_goal||_xy ≤ τ_xy AND |yaw_diff| ≤ τ_yaw`. 기본 `τ_xy=0.2 m`, `τ_yaw=0.3 rad`. 임의의 timestep 이 만족하면 True.

## "완벽" 의 임계 (v0 가설, P5 에서 calibration)

| metric | indoor | outdoor |
|---|---|---|
| `cte_rms` (m) | ≤ 0.2 | ≤ 0.5 |
| `cte_max` (m) | ≤ 0.5 | ≤ 1.0 |
| `heading_err_rms` (rad) | ≤ 0.15 | ≤ 0.25 |
| `completion_final` | ≥ 0.99 | ≥ 0.99 |
| `|time_deviation_final|/T_target` | < 0.2 | < 0.3 |
| `jerk_lat` (m/s³) | ≤ 5 | ≤ 8 |
| `goal_reached` | 1 | 1 |

전 항목 만족 = 시나리오 "완벽 통과". north-star = `tests/scenarios/*` **전체** 통과.

## 통합 계획

| | v0 (지금) | v1 (P2-P3) | v2 (P5) |
|---|---|---|---|
| 입력 | numpy 오프라인 | rosbag → numpy 헬퍼 | 라이브 ROS2 노드 (`/odom + /plan`) |
| Path 모델 | piecewise-linear | spline | spline + 곡률 인지 |
| 임계치 | 가설 | 1 시나리오 calibration | 다 시나리오 통계 |
| 출력 | dict | CSV 행 | run-id 별 JSON + plot |

## 다음 후속 TODO (executor picking)

- v0 metric → ROS2 노드 wrap (`eval/run_metrics.py`): bag/odom 구독 → run 당 dict
- 시나리오 정의 yaml (`eval/scenarios/*.yaml`): start/goal/world
- 첫 sim 시각 검증 후 그 trajectory 로 v0 calibration

## v0 한계

- piecewise-linear 만 — 곡선 reference cusp 에서 CTE 부정확
- yaw_target (control directive) ↔ segment tangent 차이 미반영
- collision/near-miss 미포함 (P5 obstacle metrics 가 보완)
- 단일 path 만 — multi-waypoint sequence 는 v1
- plotting 은 호출자 몫

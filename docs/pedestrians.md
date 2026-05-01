# Pedestrians (dynamic obstacle world variant)

P0 baseline 위에 dynamic obstacle 평가용 5인 보행자를 추가한 world variant.
정적 baseline (`tb3_mppi_sim.launch.py` + `tb3_sandbox.sdf.xacro`) 은 그대로 두고,
별도 launch (`tb3_mppi_sim_pedestrians.launch.py`) + 별도 world
(`worlds/tb3_sandbox_pedestrians.sdf.xacro`) 로 분리.

## 왜 `<model>` + TrajectoryFollower 인가 (`<actor>` 가 아니라)

| 선택지 | 보행 애니메이션 | LiDAR 가시성 (gpu_lidar 레이) | 결론 |
|---|---|---|---|
| `<actor>` + `walking.dae` | O (skinned mesh) | **X** — actor mesh 는 collision 이 자동으로 안 잡힘. 별도 `<collision>` link 가 없으면 `/scan`/`/points` 에 안 잡힘 | 우리의 핵심 신호(LiDAR cluster) 손실 → 부적합 |
| `<actor>` + manual `<collision>` | O | O | 동작은 가능하나 Harmonic 에서 `<actor>` collision API 가 불안정 + `walking.dae` 가 시스템에 미설치 |
| **`<model>` + capsule visual+collision + TrajectoryFollower (선택)** | X (강체 capsule 슬라이드) | **O** — 일반 collision geometry 라서 ray-cast 에 그대로 잡힘 | research 신호 우선 → 채택 |

`gz-sim-trajectory-follower-system` 플러그인이 force/torque 로 link 를 waypoint 로
끌고 가므로, capsule 이 사람 키 (≈1.7 m, capsule = r 0.25 + length 1.2) 로 보행 속도
대로 미끄러진다. 외형은 단순하지만 LiDAR/카메라 입장에선 "걷는 사람" 과 동일한 클러스터.

> 추후 사회적 힘 (PedSim, HuNav) 기반 reactive pedestrian 은 P4 업그레이드 경로.
> P0 단계에서는 정해진 trajectory loop 만 — 평가 reproducibility 우선.

## 다섯 명의 패턴

| # | 이름 | 색 (RGB) | 패턴 | Waypoints | force(N) | 추정 cruise (m/s) |
|---|---|---|---|---|---|---|
| 1 | `ped_red` | red (0.9, 0.1, 0.1) | 동-서 횡단 (south corridor) | (2.0,-1.7) ↔ (-2.0,-1.7) | 100 | ~1.2 |
| 2 | `ped_blue` | blue (0.1, 0.2, 0.9) | 원점 r=1.7 사각 순찰 | (1.7,0)→(0,1.7)→(-1.7,0)→(0,-1.7) | 60 | ~0.8 |
| 3 | `ped_green` | green (0.1, 0.8, 0.2) | 남-북 진동 (east edge) | (2.2,-2.0) ↔ (2.2,2.0) | 120 | ~1.4 |
| 4 | `ped_yellow` | yellow (0.95, 0.85, 0.1) | 느린 8자형 (NW quadrant) | (-2.2,1.5)→(-1.5,2.2)→(-2.2,2.5)→(-2.5,1.8) | 40 | ~0.6 |
| 5 | `ped_magenta` | magenta (0.9, 0.1, 0.8) | 대각선 cross | (-1.8,-2.2) ↔ (2.2,1.8) | 80 | ~1.0 |

속도는 `<force>` (질량 70 kg 대비) 로 조절. TrajectoryFollower 는 명시적
`speed` 파라미터가 없고 PD-식 actuator 라서 mass + force + ground friction 합으로
정상상태 속도가 결정됨. 위 force 값은 70 kg + μ=0.5 ground 기준 대략적 추정치
(±20% 변동 가능, 실 시뮬에서 한 번 보고 미세조정 권장).

TB3 spawn = (-2.0, -0.5). 모든 시작 위치는 spawn 으로부터 1 m 이상 떨어졌고,
`turtlebot3_world` 의 실린더 링 (대략 |x|,|y| < 1.2 영역) 외곽의 open space 에
배치 — 보행자가 정적 장애물에 끼지 않도록 함.

## 센서 가시성 검증

| Topic | 어떤 보행자가 잡혀야 하나 | 비고 |
|---|---|---|
| `/scan` (2D LiDAR, height ≈ 0.18 m) | TB3 시야에 들어온 capsule 의 **하단부**가 잡힘 (capsule 은 z=0.85 중앙, 반경 0.25, 총 높이 ~1.7) | 2D scan 평면이 capsule 옆구리를 stab — 폭 ~0.5 m 의 cluster |
| `/points` (3D LiDAR, 16ch, ±15° vertical) | 전체 capsule 형태 (높이 1.7 m 까지 커버) | 거리에 따라 voxel 밀도 변함 |
| `/rgb_camera/image` (1280×720) | 색이 명확하므로 segmentation/feature 학습 시 색 라벨로도 활용 가능 | 5색이 모두 다른 hue → 디버깅에 유리 |

**실험 검증 명령** (시뮬 띄운 후 다른 터미널):

```bash
ros2 topic echo --once /scan | grep ranges | head -1   # cluster 보임
ros2 topic hz /points && ros2 topic hz /scan
# RViz: PointCloud2 + LaserScan + Image display 추가, 색깔 capsule 5개 확인
```

`<actor>` 였다면 `/scan`/`/points` 에 잡히지 않음 — 이번 선택의 가장 큰 이유.

## Baseline 과 pedestrian variant 전환

```bash
# 정적 baseline (Step A)
ros2 launch representation_aware_mppi_bringup tb3_mppi_sim.launch.py

# 동적 보행자 variant (Step B)
ros2 launch representation_aware_mppi_bringup tb3_mppi_sim_pedestrians.launch.py
```

두 launch 의 차이는 `world` 인자 default 뿐. 동일한 map (`tb3_sandbox.yaml`),
동일한 robot SDF (`gz_waffle_outdoor.sdf.xacro`), 동일한 Nav2/MPPI params,
동일한 추가 sensor bridge — 비교 평가가 깔끔함.

## 파일 위치

```
src/representation_aware_mppi_bringup/
├── worlds/
│   └── tb3_sandbox_pedestrians.sdf.xacro    # upstream world 복사 + 5 pedestrian model
└── launch/
    └── tb3_mppi_sim_pedestrians.launch.py   # tb3_mppi_sim.launch.py 와 동일 구조, world default 만 변경
```

## 검증

```bash
source /opt/ros/jazzy/setup.bash
colcon build --symlink-install --packages-select representation_aware_mppi_bringup

# xacro 렌더 + SDF 문법 (단, model:// include 는 runtime 해석이라 sed 로 떼고 검사)
xacro src/representation_aware_mppi_bringup/worlds/tb3_sandbox_pedestrians.sdf.xacro \
      headless:=true > /tmp/peds.sdf
sed '/<model name="turtlebot3_world">/,/<\/model>/d' /tmp/peds.sdf > /tmp/peds_noinc.sdf
gz sdf -k /tmp/peds_noinc.sdf   # → "Valid."
```

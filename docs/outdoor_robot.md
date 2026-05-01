# Outdoor robot (Husky-class `scout_outdoor`)

Husky 등급 1 m 폭 base 를 새로 추가. TB3 baseline launch 는 그대로 두고 별도
launch (`outdoor_sim.launch.py`) + 별도 robot SDF (`urdf/scout_outdoor.sdf.xacro`)
+ 별도 bridge yaml (`configs/scout_outdoor_bridge.yaml`) + 별도 Nav2 params
(`config/nav2_outdoor_params.yaml`) 로 분리.

## 왜 갈아탔나

| 문제 | 원인 | 해결 |
|---|---|---|
| TB3 (0.3 m wide) vs walking actor (1.7 m) 비율이 비현실적 | 단순 스케일 미스매치 | 1.0 × 0.7 m chassis 로 교체 |
| Wheels spin, body doesn't translate (ODE lateral slip) | upstream `nav2_minimal_tb3_sim` 의 `gz_waffle.sdf.xacro` 가 `<mu>` 만 설정하고 `<mu2>` 가 빠짐. ground plane 도 friction 미설정 | 새 robot 의 4 wheel collision 모두 `<mu>=<mu2>=1.2`, `slip1=slip2=0`, `kp=1e7`, `kd=1.0`, `min_depth=0.001` 명시 |

upstream 파일은 절대 수정하지 않음 (regression baseline 보존).

## 로봇 사양 (`scout_outdoor`)

| 항목 | 값 |
|---|---|
| Chassis box | 1.00 × 0.65 × 0.30 m, mass 50 kg, centred at z=0.20 |
| Wheel | r=0.165 m, width=0.10 m, mass 3 kg × 4 |
| Wheel separation | y=0.55 m (left/right), x=0.64 m (front/rear) |
| Drive | DiffDrive, left = front_left+rear_left, right = front_right+rear_right |
| Velocity caps | linear ±1.5 m/s, angular ±2.0 rad/s |
| Friction (per wheel) | mu=1.2, mu2=1.2, slip1=slip2=0, kp=1e7, kd=1.0 |
| 2D laser | gpu_lidar 360 samples, 0.12-3.5 m, 5 Hz, z=0.55 m, topic `scan` |
| 3D LiDAR | 16 ch ±15° vertical, 1800 horizontal, 0.4-100 m, 10 Hz, z=1.50 m, topic `lidar` (-> `/lidar/points`) |
| RGB camera | 1280×720, hfov 1.2 rad, 15 Hz, z≈0.60 m at front, topic `rgb_camera/image` |
| IMU | 100 Hz, topic `imu`, at chassis centre |

PosePublisher 가 `/model/scout_outdoor/pose` (link poses) 로 발행하면
ros_gz_bridge 가 `/tf` 로 변환 — RViz 에서 robot 이 map 프레임에 떠 있는 모습을
보려면 이 bridge entry 가 필수. DiffDrive 의 `tf_topic` 은 odom→base_footprint
만 담당.

## Launch

```bash
# Pedestrian variant (default)
ros2 launch representation_aware_mppi_bringup outdoor_sim.launch.py

# Static baseline (upstream tb3_sandbox)
ros2 launch representation_aware_mppi_bringup outdoor_sim.launch.py pedestrians:=false

# Headless (no Gazebo GUI)
ros2 launch representation_aware_mppi_bringup outdoor_sim.launch.py headless:=True

# RViz off
ros2 launch representation_aware_mppi_bringup outdoor_sim.launch.py use_rviz:=False
```

TB3 baseline regression 은 변동 없음:

```bash
ros2 launch representation_aware_mppi_bringup tb3_mppi_sim.launch.py
ros2 launch representation_aware_mppi_bringup tb3_mppi_sim_pedestrians.launch.py
```

## 알려진 한계

- Gazebo `<actor>` (walk.dae 보행자) 는 collision geometry 를 자동으로 잡지
  않으므로 `/scan` 과 `/points` 에 **잡히지 않음**. `/rgb_camera/image` 에서만
  보임 — P1 BEV semantic seg 학습 신호로는 충분.
- Reactive (social-force) 보행자는 P4 로 deferred. 현재는 scripted
  `<trajectory>` waypoint loop 만.

## 파일

```
src/representation_aware_mppi_bringup/
├── urdf/scout_outdoor.sdf.xacro
├── configs/scout_outdoor_bridge.yaml
├── config/nav2_outdoor_params.yaml
└── launch/outdoor_sim.launch.py
```

## 검증

```bash
source /opt/ros/jazzy/setup.bash
colcon build --symlink-install --packages-select representation_aware_mppi_bringup
source install/setup.bash

# 1) launch arg 정상 해석
ros2 launch representation_aware_mppi_bringup outdoor_sim.launch.py --show-args

# 2) robot SDF 문법 검증
xacro src/representation_aware_mppi_bringup/urdf/scout_outdoor.sdf.xacro \
      namespace:='' > /tmp/scout.sdf
gz sdf -k /tmp/scout.sdf   # → "Valid." (gz_frame_id warning OK)
```

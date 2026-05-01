# Sensor Suite

P0 baseline 위에 outdoor 자율주행을 모사할 수 있도록 TB3 waffle 에 3D LiDAR + RGB camera 를 추가. 기존 센서 (IMU, 2D scan, RealSense depth) 는 그대로 보존했기 때문에 Nav2 MPPI baseline 은 영향 없음.

## 추가된 것

| 센서 | 모델 컨셉 | Topic | 메시지 타입 | Rate | Frame |
|---|---|---|---|---|---|
| 3D LiDAR | Velodyne VLP-16 급 | `/points` | `sensor_msgs/msg/PointCloud2` | 10 Hz | `velodyne_link` |
| RGB camera | 1280×720 forward-facing | `/rgb_camera/image` | `sensor_msgs/msg/Image` | 15 Hz | `rgb_camera_link` |
| RGB camera info | (위와 함께) | `/rgb_camera/camera_info` | `sensor_msgs/msg/CameraInfo` | 15 Hz | `rgb_camera_link` |

기존 보존된 토픽: `/scan`, `/imu`, `/odom`, `/cmd_vel`, `/tf`, `/joint_states`, `/clock`.

## 파일 위치

```
src/representation_aware_mppi_bringup/
├── urdf/
│   └── gz_waffle_outdoor.sdf.xacro       # upstream gz_waffle 복사 + 신규 센서 블록
├── configs/
│   └── extra_sensors_bridge.yaml         # 새 센서 토픽만 ros_gz_bridge
└── launch/
    └── tb3_mppi_sim.launch.py            # robot_sdf 인자로 위 xacro 사용 + 추가 bridge 노드
```

upstream 파일은 손대지 않음 — `nav2_minimal_tb3_sim/urdf/gz_waffle.sdf.xacro` 가 system update 로 바뀌어도 베이스 변경분만 반영하면 됨.

## 센서 배치

```
       ┌──── velodyne_link (z ≈ 0.18 m, r=0.04 cylinder)
       │
   ────┼────  base_link
       │
       └──── rgb_camera_link (x ≈ 0.12, z ≈ 0.10, +X forward)
```

3D LiDAR 는 로봇 상단 중앙, RGB camera 는 전방. URDF/xacro 의 `<joint>` 두 개로 `base_link` 에 fixed 결합.

## Gazebo 토픽 명명 함정 (해결됨)

Gazebo Harmonic 의 sensor 출력 토픽은 `<topic>` 태그 값을 그대로 쓰지 않고 변환을 거침:

- **`gpu_lidar`**: `<topic>X</topic>` 이면 gz 측은 `X` (LaserScan) 와 `X/points` (PointCloudPacked) 두 개 발행. `X/points` 만 ROS 로 bridge.
- **`camera`**: `<topic>X</topic>` 이면 마지막 path segment 를 `camera_info` 로 치환해서 `X` (Image) 와 (X 의 부모 경로)/`camera_info` (CameraInfo) 두 개 발행.

이걸 모르면 `<topic>rgb_camera</topic>` 로 설정 시 `/camera_info` 가 root 에 떠서 다른 노드와 충돌 가능. 이를 피하려고 xacro 에서 카메라는 `<topic>rgb_camera/image</topic>` 로 의도적으로 한 단계 깊게 설정 → gz 가 `rgb_camera/image` (Image) + `rgb_camera/camera_info` (CameraInfo) 깔끔하게 발행.

## ros_gz_bridge 분리 전략

upstream `nav2_minimal_tb3_sim` 은 자체 bridge (IMU/scan/odom/cmd_vel/joint_states/tf/clock) 를 launch 시 자동으로 띄움. 우리는 그것을 그대로 사용하고, **추가 센서만** 별도 bridge 노드로 띄움 (`extra_sensors_bridge.yaml`).

장점:
- upstream bridge 설정을 우리 패키지에 복사하지 않아도 됨 → 시스템 업데이트로 upstream bridge 가 바뀌어도 자동 반영.
- 토픽 충돌 없음 — 두 bridge 가 diff 한 토픽 셋 처리.

```
┌──────────── nav2_minimal_tb3_sim (upstream, unchanged) ────────────┐
│   gz topics (clock, imu, scan, odom, ...)                          │
│         │                                                          │
│         ▼  upstream bridge (turtlebot3_waffle_bridge.yaml)         │
│   ROS topics (/clock, /imu, /scan, /odom, ...)                     │
└────────────────────────────────────────────────────────────────────┘

┌────── representation_aware_mppi_bringup (this package) ────────────┐
│   gz topics (lidar/points, rgb_camera/image, rgb_camera/...)       │
│         │                                                          │
│         ▼  extra bridge (extra_sensors_bridge.yaml)                │
│   ROS topics (/points, /rgb_camera/image, /rgb_camera/...)         │
└────────────────────────────────────────────────────────────────────┘
```

## Nav2 baseline 보존

Nav2 의 costmap/AMCL/MPPI 는 모두 `/scan` 만 사용. 새로 추가한 `/points` 와 `/rgb_camera/*` 는 Nav2 가 안 보고 있어서 baseline 거동에 영향 없음. 추후 P1 (Multi-Channel BEV) 에서 새 센서를 활용하는 representation 모듈을 추가할 때, Nav2 의 입력은 우리가 만들 BEV 채널로 swap 하는 형태가 됨.

## 검증 명령

```bash
# 빌드
source /opt/ros/jazzy/setup.bash
cd ~/Representation-Aware-MPPI
colcon build --symlink-install --packages-select representation_aware_mppi_bringup
source install/setup.bash

# 시뮬 띄우기
ros2 launch representation_aware_mppi_bringup tb3_mppi_sim.launch.py

# 별 터미널에서 토픽 확인
ros2 topic list | grep -E '^/(points|rgb_camera)'
ros2 topic hz /points              # 약 10 Hz
ros2 topic hz /rgb_camera/image    # 약 15 Hz

# RViz 에서 PointCloud2 / Image display 추가하면 시각화 가능
```

## 추가/변경 시 체크리스트

새 센서를 더 붙일 때:
1. `urdf/gz_waffle_outdoor.sdf.xacro` 에 `<link>` + `<joint>` + `<sensor>` 블록 추가.
2. `configs/extra_sensors_bridge.yaml` 에 bridge 항목 추가 (gz 측 실제 토픽 이름 확인 필수).
3. `colcon build` 후 `xacro` validation: `xacro <path> namespace:='' > /tmp/check.sdf && gz sdf -k /tmp/check.sdf`.
4. 빈 시뮬에서 토픽이 실제로 ROS 로 흐르는지 확인.

기존 센서를 제거하지 말 것 (Nav2 baseline 의존성). 필요하면 fork 해서 별도 xacro variant 로 관리.

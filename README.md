# Representation-Aware-MPPI

[![CI](https://github.com/Geonhee-LEE/Representation-Aware-MPPI/actions/workflows/ci.yml/badge.svg)](https://github.com/Geonhee-LEE/Representation-Aware-MPPI/actions/workflows/ci.yml)

Phase 0 baseline. See [CLAUDE.md](./CLAUDE.md) for full project context.

This workspace brings up TurtleBot3 in Gazebo Harmonic with the upstream Nav2
stack and the official `nav2_mppi_controller::MPPIController` as a single
`ros2 launch` entry point. It is the unmodified reference that all
representation-aware MPPI experiments will be benchmarked against.

## Quickstart

```bash
source /opt/ros/jazzy/setup.bash
cd ~/Representation-Aware-MPPI
colcon build --symlink-install
source install/setup.bash
ros2 launch representation_aware_mppi_bringup tb3_mppi_sim.launch.py
```

In a second terminal, source the same overlays and use RViz's "2D Goal Pose"
button to send a navigation goal:

```bash
source /opt/ros/jazzy/setup.bash
source ~/Representation-Aware-MPPI/install/setup.bash
```

## Notes

- The launch wraps `nav2_bringup/tb3_simulation_launch.py` and overrides
  `params_file` with `config/nav2_mppi_params.yaml`.
- The Jazzy `nav2_bringup` default `nav2_params.yaml` already ships with
  MPPIController; only velocity/accel limits were narrowed to TB3 burger spec.
- Default robot is TB3 waffle (per `nav2_minimal_tb3_sim`). Velocity limits in
  the params file are set conservatively for burger; raise them for waffle.

## Sensor suite

Step A adds a 16-channel 3D LiDAR (`/points`, `sensor_msgs/PointCloud2`, ~10 Hz)
and a forward-facing RGB camera (`/rgb_camera/image` + `/rgb_camera/camera_info`,
1280x720, ~15 Hz) to the upstream TB3 waffle via
`urdf/gz_waffle_outdoor.sdf.xacro` and `configs/extra_sensors_bridge.yaml`.
The original 2D `/scan` and `/imu` are preserved so the Nav2 baseline keeps
working unchanged. Override the SDF with `robot_sdf:=...` if you need the
stock waffle.
# Representation-Aware-MPPI

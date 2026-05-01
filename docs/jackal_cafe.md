# Jackal + cafe3 (Stage 1 of the RDSim port)

Stage 1 of porting [Geonhee-LEE/RDSim](https://github.com/Geonhee-LEE/RDSim)
(ROS 2 Humble + Gazebo Classic 11) onto our ROS 2 **Jazzy** + Gazebo Sim
**Harmonic** stack. The earlier `scout_outdoor` was built from boxes and
cylinders for a quick stand-in; this stage replaces it with a real Jackal
mesh and parks it in the cafe3 indoor environment.

## Why Jackal + cafe3

* The Clearpath **Jackal** (~62 x 42 cm, ~17 kg) is the canonical
  indoor/outdoor mid-size differential-drive research platform — pairs
  well with realistic 1.7 m walking actors and our existing MPPI tuning.
* The **cafe3** environment (cafe shell + 5 tables + 5 pedestrians) gives
  the MPPI critic something interesting to plan around: tight aisles,
  static furniture, dynamic humans. RDSim's social-scenario evaluation
  worlds.

## Source attribution

All RDSim assets are **BSD-3-Clause** (Service Robotics Lab, U. Pablo de
Olavide). Files copied verbatim into this package:

| Path under `src/representation_aware_mppi_bringup/` | Origin in RDSim |
|---|---|
| `meshes/jackal/jackal-base.stl`                | `rdsim_description/meshes/jackal-base.stl` |
| `meshes/jackal/jackal-wheel.stl`               | `rdsim_description/meshes/jackal-wheel.stl` |
| `meshes/jackal/jackal-fender.stl`              | `rdsim_description/meshes/jackal-fender.stl` |
| `meshes/jackal/jackal-fenders.stl`             | `rdsim_description/meshes/jackal-fenders.stl` |
| `meshes/jackal/accessory_fender.stl`           | `rdsim_description/meshes/accessory_fender.stl` |
| `meshes/jackal/hokuyo_ust10.stl`               | `rdsim_description/meshes/hokuyo_ust10.stl` |
| `meshes/jackal/VLP16_base_{1,2}.dae`           | `rdsim_description/meshes/VLP16_base_{1,2}.dae` |
| `meshes/jackal/VLP16_scan.dae`                 | `rdsim_description/meshes/VLP16_scan.dae` |
| `meshes/actors/walk{,-red,-blue,-green}.dae`   | `gazebo_sfm_plugin/media/models/walk{,-red,-blue,-green}.dae` |
| `models/cafe_table/*`                          | `rdsim_gazebo/models/cafe_table/*` |

The Jackal mesh family was originally published by Clearpath Robotics
under BSD-3-Clause in `jackal_description` and is redistributed via RDSim
under the same terms. Walking actor DAEs are from the
[gazebo_sfm_plugin](https://github.com/robotics-upo/gazebo_sfm_plugin) project.

The world `worlds/cafe3_jazzy.sdf.xacro` is **adapted** (not verbatim)
from `rdsim/gazebo_sfm_plugin/worlds/cafe3.world` — see "Porting notes"
below.

## What's in the package

### Robot — `urdf/jackal_outdoor.sdf.xacro`

| Property | Value |
|---|---|
| Footprint (L x W x H) | 0.420 x 0.310 x 0.184 m |
| Mass (chassis) | 17.0 kg |
| Wheels | 4 x cylinder, r=0.098 m, w=0.040 m, m=0.477 kg |
| Track / wheelbase | 0.376 m / 0.262 m |
| Friction (per wheel) | mu=mu2=1.2, slip1=slip2=0, kp=1e7, kd=1.0 |
| Drive plugin | `gz-sim-diff-drive-system` (front+rear joint averaging) |
| Max linear / angular | 2.0 m/s / 2.5 rad/s |
| Sensors | VLP16 16ch lidar, Hokuyo UST10 2D laser, RGB cam 1280x720, IMU 100 Hz |
| Decorative meshes | jackal-base.stl, jackal-fender.stl x2 (yellow), VLP16 mast, hokuyo |
| Plugins | DiffDrive, JointStatePublisher, PosePublisher (link+sensor pose) |

`<mu>` AND `<mu2>` are both set on every wheel collision (TB3 ships only
`<mu>` and the wheels-spin-but-body-doesn't-translate bug bites you in
Harmonic ODE without `<mu2>`).

### World — `worlds/cafe3_jazzy.sdf.xacro`

| Element | Source / decision |
|---|---|
| 4 plugins (physics, user-cmds, sensors, imu) | Harmonic-native |
| SceneBroadcaster | Gated on `headless==false` |
| Sun + indoor point light | Adapted from upstream |
| Ground plane | Hand-rolled (warm tan diffuse for cafe floor) |
| Cafe shell (4 walls + counter) | **Hand-built** ~9 x 14 m; replaces upstream `model://cafe` (Classic stock Building model not available on Harmonic) |
| 5 cafe_tables | Verbatim positions from upstream cafe3.world (XY + yaw); Z corrected to 0 |
| 5 actors (red, blue, green, white, red-2) | **Replaces** upstream SFM actors with scripted `<actor>`/`<script>`/`<trajectory>` blocks |

### Bridge — `configs/jackal_outdoor_bridge.yaml`

Identical topic set to `scout_outdoor_bridge.yaml` with the model name
swap (`/model/jackal/pose` for the PosePublisher TF feed).

### Nav2 — `config/nav2_jackal_params.yaml`

Derived from `nav2_outdoor_params.yaml`. Key deltas:

* MPPI `vx_max=1.5, vx_min=-0.5, wz_max=2.0`
* Footprint `[[0.31,0.21],[0.31,-0.21],[-0.31,-0.21],[-0.31,0.21]]`
* `inflation_layer.inflation_radius: 0.4` for tighter cafe aisles

### Launch — `launch/jackal_cafe.launch.py`

Built from scratch (no `tb3_*` wrapper). Composes:

1. `gz sim` with cafe3_jazzy world (xacro-rendered to /tmp at launch time)
2. `ros_gz_sim/create` to spawn `jackal` at `(x, y, z, yaw)` (defaults: `0, 0, 0.05, -pi/2`)
3. `ros_gz_bridge/parameter_bridge` with `jackal_outdoor_bridge.yaml`
4. `nav2_bringup/bringup_launch.py` with `nav2_jackal_params.yaml` and `slam:=True` by default
5. `nav2_bringup/rviz_launch.py` (conditional on `use_rviz`)

`GZ_SIM_RESOURCE_PATH` is prepended with `share/.../models` and
`share/.../meshes` so `model://cafe_table` resolves and any future
file:// URIs do too.

## Topic list (post-bridge)

| ROS topic | Direction | Type |
|---|---|---|
| `/clock` | <- gz | `rosgraph_msgs/Clock` |
| `/joint_states` | <- gz | `sensor_msgs/JointState` |
| `/odom` | <- gz | `nav_msgs/Odometry` |
| `/tf` | <- gz (twice: DiffDrive odom->base_footprint and PosePublisher world->link) | `tf2_msgs/TFMessage` |
| `/imu` | <- gz | `sensor_msgs/Imu` |
| `/scan` | <- gz | `sensor_msgs/LaserScan` |
| `/points` | <- gz (`lidar/points`) | `sensor_msgs/PointCloud2` |
| `/rgb_camera/image` | <- gz | `sensor_msgs/Image` |
| `/rgb_camera/camera_info` | <- gz | `sensor_msgs/CameraInfo` |
| `/cmd_vel` | -> gz | `geometry_msgs/Twist` |

## TF tree (expected)

```
map (slam_toolbox)
  -> odom (DiffDrive)
       -> base_footprint
            -> chassis_link (joint base_link_joint)
                 -> base_link (alias)
                 -> imu_link
                 -> hokuyo_link
                 -> velodyne_link
                 -> rgb_camera_link
                 -> wheel_{front,rear}_{left,right}_link
                 -> {front,rear}_fender_link (visual-only)
```

## Run

```bash
source /opt/ros/jazzy/setup.bash
cd ~/Representation-Aware-MPPI
colcon build --symlink-install --packages-select representation_aware_mppi_bringup
source install/setup.bash

ros2 launch representation_aware_mppi_bringup jackal_cafe.launch.py
```

Common knobs:

```bash
# headless (no Gazebo client GUI)
ros2 launch representation_aware_mppi_bringup jackal_cafe.launch.py headless:=True

# alternate spawn pose
ros2 launch representation_aware_mppi_bringup jackal_cafe.launch.py x:=2.0 y:=-2.0 yaw:=0.0

# use AMCL with a pre-built map (when you have one)
ros2 launch representation_aware_mppi_bringup jackal_cafe.launch.py slam:=False map:=/path/to/cafe3.yaml
```

## Known limitations

* **Pedestrian SFM (reactive social-force) is NOT included.** Stage 2.
  The 5 actors here use scripted `<trajectory>` waypoints — they will
  walk through the robot if the robot is in their path. This matches
  the existing tb3 sandbox behaviour.
* `<actor>`s have no physics collision -> invisible to the gpu_lidar
  topics (`/scan`, `/points`). They are visible to `/rgb_camera/image`,
  which is the channel the upcoming representation-learning critic
  will consume.
* The cafe shell is a hand-built 4-wall box, not the original
  `model://cafe` Building model. Geometry is approximate; table
  positions are exact.
* No pre-built occupancy map for cafe3 ships with the package -> we
  default to `slam:=True` (slam_toolbox). Generate a map and switch to
  `slam:=False` if you want AMCL.
* The Jackal `<actor>` skin `walk-yellow.dae` does not exist upstream;
  the 5th actor reuses `walk-red.dae` ("red-2").

## Regression baseline

TB3 launches and the scout_outdoor launch are untouched and continue to
work:

```bash
ros2 launch representation_aware_mppi_bringup tb3_mppi_sim_pedestrians.launch.py --show-args
ros2 launch representation_aware_mppi_bringup outdoor_sim.launch.py --show-args
```

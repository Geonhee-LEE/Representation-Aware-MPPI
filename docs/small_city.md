# Jackal + small_city (Stage 2 of the RDSim port)

Stage 2 follows the Stage-1 cafe (`docs/jackal_cafe.md`) by porting RDSim's
`small_city.world` onto our ROS 2 **Jazzy** + Gazebo Sim **Harmonic**
stack. Same Jackal robot; much larger outdoor environment more aligned
with the project's outdoor-driving theme.

## What the world contains

`worlds/small_city.sdf.xacro` is a hand-port of
`rdsim/rdsim_gazebo/worlds/small_city.world` (BSD-3-Clause, Service
Robotics Lab, U. Pablo de Olavide). The footprint is roughly
170 m x 100 m and contains:

* **Road grid** - 9 `<road>` segments: 5 N-S (`x = -45, -15, 45, 110, 120`)
  and 3 E-W (`y = -45, 0, 45`).
* **Sidewalks** - 40 `<polyline>` models lining every block.
* **185 `<include>` blocks** referencing standard Gazebo Classic stock
  models: `apartment`, `house_{1,2,3}`, `oak_tree`, `pine_tree`,
  `hatchback`, `hatchback_red`, `hatchback_blue`, `pickup`, `suv`,
  `ambulance`, `gas_station`, `fast_food`, `salon`, `post_office`,
  `law_office`, `thrift_shop`, `radio_tower`, `truss_bridge`,
  `lamp_post`, `telephone_pole`, `fire_hydrant`, `stop_sign`,
  `stop_light_post`, `postbox`, `dumpster`, `cardboard_box`, `fountain`,
  `pier`, `ocean`, `city_terrain`, `osrf_first_office`. The 35 unique
  URIs resolve at runtime via `GZ_SIM_RESOURCE_PATH`; missing models are
  silently skipped by `gz sim` (the world still loads).
* **Hand-rolled inline models** - `gas_station_73`, `asphalt_plane_74`
  (kept verbatim since they reference textures from the corresponding
  `model://` trees rather than instancing the model itself).
* **Ground plane** with explicit `<mu>100</mu><mu2>50</mu2>` (no friction
  bug to patch - upstream got this right).
* **5 scripted `<actor>`s** added on top of the upstream geometry; see
  "Pedestrians" below. The upstream SFM-driven `actor1` was removed;
  reactive social-force pedestrians are Stage 3.

### Pedestrians (5 scripted actors)

| Name        | Skin DAE        | Pattern                                                      |
|-------------|-----------------|--------------------------------------------------------------|
| `ped_red`   | walk-red.dae    | Crosswalk: N-S across `road_x_2` (y=0) at x=-30, 12 s loop   |
| `ped_blue`  | walk-blue.dae   | Sidewalk patrol: E-W on +Y sidewalk of `road_x_2`, x=-38..-22 |
| `ped_green` | walk-green.dae  | Plaza wandering: 6x6 m loop near apartment_76 (~83, -27)      |
| `ped_white` | walk.dae        | Long pedestrian street: eastbound +Y sidewalk, x=-15..110     |
| `ped_red2`  | walk-red.dae    | Diagonal crossing between buildings, NW->SE near (-30, -25)   |

All five use the `<actor>`/`<script>`/`<trajectory>` pattern (no SFM
plugin). Skin DAEs are taken from `meshes/actors/`. Speeds tuned to
~1 m/s to match the walk DAE animation rate (no foot skating).

## First-time setup: external models

The 1.3 GB Gazebo-Classic stock model dump is **not committed** to this
repo. Fetch RDSim's tree once:

```bash
./scripts/fetch_rdsim_models.sh
```

The script clones `https://github.com/Geonhee-LEE/RDSim.git` into
`~/.local/share/representation-aware-mppi/rdsim/`. Re-running it just
does `git pull --ff-only`. If a `rdsim` symlink already exists at the
destination (handy for development), the script leaves it untouched.

The Stage-2 launch (`jackal_outdoor_sim.launch.py`) prepends
`~/.local/share/representation-aware-mppi/rdsim/rdsim_gazebo/models` to
`GZ_SIM_RESOURCE_PATH` automatically. When `world:=city` is requested
and the directory is missing, the launch hard-fails with a pointer to
`scripts/fetch_rdsim_models.sh`.

> Note: RDSim itself ships only `city_terrain`, `ocean`, and
> `asphalt_plane`. The other ~32 unique URIs are Gazebo Classic stock
> models that historically lived in `/usr/share/gazebo-11/models` or
> downloaded from Gazebo Fuel on first reference. If you do not have
> them, the city loads with empty space where those models would
> render; the road grid, sidewalks, terrain, ocean, and the 5 actors
> still appear and the simulation is fully usable for navigation
> testing.

### Why models stay outside the repo

* **Repo size** - 1.3 GB of binary mesh/texture data is too large for
  the project's `git` history.
* **Licensing** - the stock models are individually-licensed Gazebo
  community assets; we don't want to redistribute them under our
  package's license boundaries.
* **Reproducibility** - the fetch script is the single source of truth
  for "what models do I need".

## Launch

```bash
source /opt/ros/jazzy/setup.bash
cd ~/Representation-Aware-MPPI
colcon build --symlink-install --packages-select representation_aware_mppi_bringup
source install/setup.bash

# (one-time) fetch models
./scripts/fetch_rdsim_models.sh

# default: small_city, slam_toolbox on, RViz on
ros2 launch representation_aware_mppi_bringup jackal_outdoor_sim.launch.py
```

### Switching world

```bash
# Stage-1 cafe
ros2 launch representation_aware_mppi_bringup jackal_outdoor_sim.launch.py world:=cafe

# Custom xacro (must be absolute path)
ros2 launch representation_aware_mppi_bringup jackal_outdoor_sim.launch.py \
    world:=/home/me/my_world.sdf.xacro
```

### Common knobs

```bash
# headless (no GUI)
ros2 launch ... jackal_outdoor_sim.launch.py world:=city headless:=True

# AMCL with a pre-built map (you'll need to build one with SLAM first)
ros2 launch ... jackal_outdoor_sim.launch.py \
    world:=city slam:=False map:=/path/to/small_city.yaml

# alternate spawn pose
ros2 launch ... jackal_outdoor_sim.launch.py \
    world:=city x:=80 y:=-15 yaw:=1.5708
```

Per-world default spawn:

| world | x      | y     | z     | yaw     |
|-------|--------|-------|-------|---------|
| city  | -30.0  | 0.0   | 0.05  | 0.0     |
| cafe  | 0.0    | 0.0   | 0.05  | -1.5708 |

## Map / SLAM note

No pre-built occupancy map ships for either world. `slam:=True` is the
default; `slam_toolbox` will produce a map online. Build one and switch
to `slam:=False map:=...` if you want AMCL.

## Backwards compatibility

`launch/jackal_cafe.launch.py` is **unchanged** and continues to work
(Stage-1 baseline). The new `jackal_outdoor_sim.launch.py` is the
canonical entry point going forward; `jackal_cafe.launch.py` is
effectively a thin equivalent of `jackal_outdoor_sim.launch.py
world:=cafe`.

The TB3 launches (`tb3_mppi_sim*.launch.py`) and the earlier
`outdoor_sim.launch.py` (scout robot) are likewise untouched.

## Attribution

* World geometry, road grid, sidewalks, include list, ground-plane
  friction values: ported from `rdsim/rdsim_gazebo/worlds/small_city.world`,
  BSD-3-Clause (Service Robotics Lab, U. Pablo de Olavide).
* Gazebo-Harmonic plugin stack and `<xacro:walking_actor>` macro: own
  work, mirrors `cafe3_jazzy.sdf.xacro`.
* Walking actor DAEs (`walk{,-red,-blue,-green}.dae`): from
  `gazebo_sfm_plugin/media/models/`, BSD-3-Clause.

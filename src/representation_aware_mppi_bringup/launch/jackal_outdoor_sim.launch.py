# Copyright 2026 Geonhee Lee
# Licensed under the Apache License, Version 2.0.

"""Stage 2 of the RDSim port: Jackal + selectable outdoor world on
ROS 2 Jazzy / Gazebo Harmonic.

Generalises ``jackal_cafe.launch.py`` to swap between worlds:

    world:=city   (default) -> worlds/small_city.sdf.xacro
    world:=cafe              -> worlds/cafe3_jazzy.sdf.xacro
    world:=/abs/path.xacro   -> arbitrary xacro file

Both stock worlds are hand-ported from RDSim (BSD-3-Clause). The city
world references ~35 Gazebo-Classic-stock model URIs (apartment, oak_tree,
hatchback, pickup, suv, ...) which RDSim itself does not ship. They are
expected to be present on disk under
``~/.local/share/representation-aware-mppi/rdsim/rdsim_gazebo/models/``,
which ``scripts/fetch_rdsim_models.sh`` populates. Run that script once
before launching with ``world:=city``.

Pedestrians: both worlds bake in five scripted ``<actor>``s today; the
``pedestrians`` arg is currently a no-op kept for API parity with the
TB3 launches and for the upcoming SFM-plugin port (Stage 3).
"""

import os

from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    ExecuteProcess,
    IncludeLaunchDescription,
    OpaqueFunction,
    SetEnvironmentVariable,
)
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration

from launch_ros.actions import Node


# Shorthand -> world xacro filename inside share/.../worlds/.
_WORLD_ALIASES = {
    'city': 'small_city.sdf.xacro',
    'cafe': 'cafe3_jazzy.sdf.xacro',
}

# Default spawn pose (x, y, z, yaw) per world alias. Picked to put Jackal
# in the open street area of each world. For `city` we drop in on the
# south-west open road segment near (-30, 0). For `cafe` we use cafe3's
# original origin (matches the Stage-1 launch).
_DEFAULT_SPAWN = {
    'city': ('-30.0', '0.0', '0.05', '0.0'),
    'cafe': ('0.0', '0.0', '0.05', '-1.5708'),
}


def _resolve_world(world_arg, pkg_share):
    """Translate the `world` arg into an absolute xacro path.

    `world_arg` may be: an alias (city|cafe), or an absolute filesystem
    path to a .xacro file. Returns (abs_xacro_path, alias_or_none).
    """
    if not world_arg:
        # Empty -> default to city.
        world_arg = 'city'
    if world_arg in _WORLD_ALIASES:
        path = os.path.join(pkg_share, 'worlds', _WORLD_ALIASES[world_arg])
        return path, world_arg
    # Treat as path; require it exist and end in .xacro.
    if not os.path.isabs(world_arg):
        raise RuntimeError(
            f"world={world_arg!r} is neither an alias (city|cafe) nor "
            "an absolute path to a xacro.")
    if not os.path.exists(world_arg):
        raise RuntimeError(f"world xacro not found: {world_arg}")
    return world_arg, None


def launch_setup(context, *args, **kwargs):
    pkg_share = get_package_share_directory('representation_aware_mppi_bringup')
    nav2_bringup_share = get_package_share_directory('nav2_bringup')
    ros_gz_sim_share = get_package_share_directory('ros_gz_sim')

    headless = LaunchConfiguration('headless').perform(context)
    use_rviz = LaunchConfiguration('use_rviz')

    robot_xacro = os.path.join(pkg_share, 'urdf', 'jackal_outdoor.sdf.xacro')
    bridge_yaml = os.path.join(pkg_share, 'configs', 'jackal_outdoor_bridge.yaml')
    params_file = LaunchConfiguration('params_file').perform(context)

    meshes_path = os.path.join(pkg_share, 'meshes')
    models_path = os.path.join(pkg_share, 'models')

    world_arg = LaunchConfiguration('world').perform(context)
    world_path, alias = _resolve_world(world_arg, pkg_share)

    # Resolve external RDSim models cache.
    rdsim_root = os.path.expanduser(
        '~/.local/share/representation-aware-mppi/rdsim')
    rdsim_models = os.path.join(rdsim_root, 'rdsim_gazebo', 'models')
    rdsim_sfm_models = os.path.join(rdsim_root, 'gazebo_sfm_plugin',
                                    'media', 'models')

    # Hard-fail when world=city is requested but models aren't fetched.
    # cafe doesn't need the external cache (cafe_table is in the package).
    if alias == 'city' and not os.path.isdir(rdsim_models):
        raise RuntimeError(
            "RDSim models not found at {}. Run scripts/fetch_rdsim_models.sh "
            "once before launching with world:=city.".format(rdsim_models))

    # Spawn pose: respect explicit user values; only fall back to per-world
    # defaults when the launch arg is at its sentinel value (the empty
    # string). DeclareLaunchArgument forces strings only.
    def _spawn(name, default):
        v = LaunchConfiguration(name).perform(context)
        return v if v != '' else default

    if alias and alias in _DEFAULT_SPAWN:
        sx, sy, sz, syaw = _DEFAULT_SPAWN[alias]
    else:
        sx, sy, sz, syaw = '0.0', '0.0', '0.05', '0.0'
    spawn_x = _spawn('x', sx)
    spawn_y = _spawn('y', sy)
    spawn_z = _spawn('z', sz)
    spawn_yaw = _spawn('yaw', syaw)

    # Render world xacro to a tmp file (gz expects a real .sdf path).
    rendered_world = os.path.join('/tmp', f'jackal_outdoor_{alias or "custom"}_world.sdf')
    rc = os.system(
        f"xacro {world_path} headless:={headless.lower()} "
        f"meshes_path:={meshes_path} > {rendered_world}")
    if rc != 0:
        raise RuntimeError(f"xacro failed for world: {world_path}")

    # Render robot xacro.
    rendered_robot = os.path.join('/tmp', 'jackal_outdoor.sdf')
    rc_robot = os.system(
        f"xacro {robot_xacro} namespace:='' "
        f"meshes_path:={meshes_path} > {rendered_robot}")
    if rc_robot != 0:
        raise RuntimeError(f"xacro failed for robot: {robot_xacro}")

    gz_args = f"-r {rendered_world}"
    if headless.lower() in ('true', '1', 'yes', 'on'):
        gz_args = f"-s -r {rendered_world}"

    gz_sim = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(ros_gz_sim_share, 'launch', 'gz_sim.launch.py')),
        launch_arguments={
            'gz_args': gz_args,
            'on_exit_shutdown': 'true',
        }.items(),
    )

    spawn_robot = Node(
        package='ros_gz_sim',
        executable='create',
        output='screen',
        arguments=[
            '-name', 'jackal',
            '-file', rendered_robot,
            '-x', spawn_x,
            '-y', spawn_y,
            '-z', spawn_z,
            '-Y', spawn_yaw,
            '-allow_renaming', 'false',
        ],
    )

    bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        name='jackal_outdoor_bridge',
        namespace=LaunchConfiguration('namespace'),
        parameters=[{
            'config_file': bridge_yaml,
            'expand_gz_topic_names': True,
            'use_sim_time': True,
        }],
        output='screen',
    )

    bringup = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(nav2_bringup_share, 'launch', 'bringup_launch.py')),
        launch_arguments={
            'namespace': LaunchConfiguration('namespace'),
            'use_sim_time': 'true',
            'autostart': LaunchConfiguration('autostart'),
            'params_file': params_file,
            'map': LaunchConfiguration('map'),
            'slam': LaunchConfiguration('slam'),
        }.items(),
    )

    rviz = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(nav2_bringup_share, 'launch', 'rviz_launch.py')),
        condition=IfCondition(use_rviz),
        launch_arguments={
            'use_sim_time': 'true',
            'namespace': LaunchConfiguration('namespace'),
        }.items(),
    )

    # GZ_SIM_RESOURCE_PATH: prepend in priority order
    #   1. Package's models/   (cafe_table)
    #   2. RDSim rdsim_gazebo/models/ (city_terrain, ocean, asphalt_plane,
    #      and any Gazebo Classic stock models the user has dropped in
    #      sibling-style)
    #   3. RDSim gazebo_sfm_plugin/media/models/ (legacy actor DAEs;
    #      harmless when missing)
    #   4. Package's meshes/   (file:// fallback for stage-1 paths)
    parts = [models_path, rdsim_models, rdsim_sfm_models, meshes_path]
    parts.append(os.environ.get('GZ_SIM_RESOURCE_PATH', ''))
    set_resource_path = SetEnvironmentVariable(
        name='GZ_SIM_RESOURCE_PATH',
        value=':'.join(p for p in parts if p),
    )

    include_run_metrics = LaunchConfiguration('include_run_metrics')
    run_id = LaunchConfiguration('run_id').perform(context)
    target_speed = LaunchConfiguration('target_speed').perform(context)
    run_metrics_output_dir = LaunchConfiguration(
        'run_metrics_output_dir').perform(context)
    run_metrics_pythonpath = LaunchConfiguration(
        'run_metrics_pythonpath').perform(context)

    existing_pythonpath = os.environ.get('PYTHONPATH', '')
    if run_metrics_pythonpath and existing_pythonpath:
        combined_pythonpath = f"{run_metrics_pythonpath}:{existing_pythonpath}"
    else:
        combined_pythonpath = run_metrics_pythonpath or existing_pythonpath

    run_metrics = ExecuteProcess(
        cmd=[
            'python3', '-m', 'eval.run_metrics',
            '--ros-args',
            '-p', f'run_id:={run_id}',
            '-p', f'target_speed:={target_speed}',
            '-p', f'output_dir:={run_metrics_output_dir}',
        ],
        additional_env=(
            {'PYTHONPATH': combined_pythonpath}
            if combined_pythonpath else {}
        ),
        output='screen',
        condition=IfCondition(include_run_metrics),
    )

    return [set_resource_path, gz_sim, spawn_robot, bridge, bringup, rviz,
            run_metrics]


def generate_launch_description():
    pkg_share = get_package_share_directory('representation_aware_mppi_bringup')
    nav2_bringup_share = get_package_share_directory('nav2_bringup')

    default_params = os.path.join(pkg_share, 'config', 'nav2_jackal_params.yaml')
    default_map = os.path.join(nav2_bringup_share, 'maps', 'tb3_sandbox.yaml')

    return LaunchDescription([
        DeclareLaunchArgument(
            'namespace', default_value='',
            description='Top-level namespace.'),
        DeclareLaunchArgument(
            'headless', default_value='False',
            description='Run gz sim without GUI client.'),
        DeclareLaunchArgument(
            'use_rviz', default_value='True',
            description='Launch RViz with the default Nav2 view.'),
        DeclareLaunchArgument(
            'world', default_value='city',
            description='World selector: "city" (small_city.sdf.xacro), '
                        '"cafe" (cafe3_jazzy.sdf.xacro), or absolute path '
                        'to a custom xacro file.'),
        DeclareLaunchArgument(
            'pedestrians', default_value='True',
            description='Reserved (no-op): both worlds currently bake in '
                        'five scripted actors. Reactive-SFM pedestrians '
                        'are Stage 3.'),
        DeclareLaunchArgument(
            'map', default_value=default_map,
            description='Map yaml. Ignored when slam:=True (the default).'),
        DeclareLaunchArgument(
            'params_file', default_value=default_params,
            description='Nav2 params yaml.'),
        DeclareLaunchArgument(
            'autostart', default_value='true',
            description='Auto-start Nav2 lifecycle nodes.'),
        DeclareLaunchArgument(
            'slam', default_value='True',
            description='Run SLAM (slam_toolbox) instead of AMCL+map_server. '
                        'Default True since neither world ships a pre-built map.'),
        DeclareLaunchArgument(
            'x', default_value='',
            description='Spawn x [m]. Empty -> per-world default.'),
        DeclareLaunchArgument(
            'y', default_value='',
            description='Spawn y [m]. Empty -> per-world default.'),
        DeclareLaunchArgument(
            'z', default_value='',
            description='Spawn z [m]. Empty -> per-world default.'),
        DeclareLaunchArgument(
            'yaw', default_value='',
            description='Spawn yaw [rad]. Empty -> per-world default.'),
        DeclareLaunchArgument(
            'include_run_metrics', default_value='false',
            description='Spawn eval.run_metrics ROS2 node alongside sim '
                        '(records /odom + /plan to runs/<run_id>.json on '
                        'shutdown or /run_metrics/finalize service call). '
                        'Default false → byte-identical to legacy launch.'),
        DeclareLaunchArgument(
            'run_id', default_value='run-default',
            description='Run identifier; output JSON is '
                        '<run_metrics_output_dir>/<run_id>.json.'),
        DeclareLaunchArgument(
            'target_speed', default_value='0.5',
            description='Target speed [m/s] for the time-deviation metric '
                        '(only used when include_run_metrics:=true).'),
        DeclareLaunchArgument(
            'run_metrics_output_dir', default_value='runs',
            description='Output directory for run_metrics JSON. Relative '
                        'paths are resolved against the launch CWD.'),
        DeclareLaunchArgument(
            'run_metrics_pythonpath', default_value='',
            description='Optional PYTHONPATH prefix for spawning '
                        'eval.run_metrics. Empty -> use process PYTHONPATH '
                        '(set e.g. PYTHONPATH=$(pwd) before invoking '
                        'ros2 launch from the repo root).'),
        OpaqueFunction(function=launch_setup),
    ])

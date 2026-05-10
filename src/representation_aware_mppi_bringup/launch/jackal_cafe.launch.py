# Copyright 2026 Geonhee Lee
# Licensed under the Apache License, Version 2.0.

"""Stage 1 of the RDSim port: Jackal (Clearpath) + cafe3 indoor world on
ROS 2 Jazzy / Gazebo Harmonic.

Composes:
  - gz sim with cafe3_jazzy world (xacro-rendered to /tmp at launch time).
    Mesh paths inside the rendered world are absolute file:// URIs pointing
    to share/representation_aware_mppi_bringup/meshes (the rendered SDF is
    portable across processes; no GZ_SIM_RESOURCE_PATH dance needed for the
    actor skin meshes).
  - ros_gz_sim/create to spawn jackal at (0, 0, 0.05) inside the cafe.
  - ros_gz_bridge/parameter_bridge with jackal_outdoor_bridge.yaml.
  - nav2_bringup/bringup_launch.py with nav2_jackal_params.yaml. SLAM is on
    by default (slam:=True) since cafe3 has no pre-built occupancy map.
  - nav2_bringup/rviz_launch.py (conditional on `use_rviz`).

Pedestrian SFM (reactive social force) is OUT of scope here — five
scripted <actor>s with colored walk DAEs stand in. SFM port is Stage 2.

This launch is built from scratch — it does not wrap any tb3_* or
outdoor_sim launch, keeping the regression baseline isolated.
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

    world_path = LaunchConfiguration('world').perform(context)
    if not world_path:
        world_path = os.path.join(pkg_share, 'worlds', 'cafe3_jazzy.sdf.xacro')

    # Render world xacro to a tmp file (gz expects a real .sdf path). Pass
    # absolute meshes_path so actor skin DAEs resolve as file://.
    rendered_world = os.path.join('/tmp', 'jackal_cafe_world.sdf')
    rc = os.system(
        f"xacro {world_path} headless:={headless.lower()} "
        f"meshes_path:={meshes_path} > {rendered_world}")
    if rc != 0:
        raise RuntimeError(f"xacro failed for world: {world_path}")

    # Render robot xacro to a real .sdf path (ros_gz_sim/create needs SDF).
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
            '-x', LaunchConfiguration('x'),
            '-y', LaunchConfiguration('y'),
            '-z', LaunchConfiguration('z'),
            '-Y', LaunchConfiguration('yaw'),
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

    # GZ_SIM_RESOURCE_PATH: include both the package's models/ and meshes/
    # so model:// URIs (cafe_table) and any future file:// includes
    # resolve. Prepend so we beat any system defaults.
    set_resource_path = SetEnvironmentVariable(
        name='GZ_SIM_RESOURCE_PATH',
        value=f"{models_path}:{meshes_path}:{os.environ.get('GZ_SIM_RESOURCE_PATH', '')}",
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
    # Default map: tb3_sandbox map; only used when slam:=False. With the
    # default slam:=True the map_server is not loaded by nav2_bringup, so
    # this path being present-but-irrelevant is fine.
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
            'world', default_value='',
            description='Override world xacro path. Empty -> cafe3_jazzy.'),
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
                        'Default True since cafe3 has no pre-built map.'),
        DeclareLaunchArgument('x', default_value='0.0',
                              description='Spawn x [m].'),
        DeclareLaunchArgument('y', default_value='0.0',
                              description='Spawn y [m].'),
        DeclareLaunchArgument('z', default_value='0.05',
                              description='Spawn z [m].'),
        DeclareLaunchArgument('yaw', default_value='-1.5708',
                              description='Spawn yaw [rad]; -pi/2 faces -Y '
                                          '(into the cafe, toward tables).'),
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

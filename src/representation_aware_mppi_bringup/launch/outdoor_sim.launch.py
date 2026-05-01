# Copyright 2026 Geonhee Lee
# Licensed under the Apache License, Version 2.0.

"""Outdoor (Husky-class) Nav2/MPPI sim — built from scratch (no upstream
tb3_simulation_launch wrapper).

Composes:
  - gz sim with our pedestrian world (xacro-rendered) or upstream tb3 sandbox
  - ros_gz_sim/create to spawn scout_outdoor at (-2.0, -0.5, 0.0)
  - ros_gz_bridge/parameter_bridge with scout_outdoor_bridge.yaml
  - robot_state_publisher consuming the rendered robot xacro
  - nav2_bringup/bringup_launch.py with our outdoor params + tb3_sandbox map
  - nav2_bringup/rviz_launch.py (optional)

TB3 launches are untouched so baseline regressions still run.
"""

import os

from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    IncludeLaunchDescription,
    OpaqueFunction,
)
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import (
    Command,
    FindExecutable,
    LaunchConfiguration,
    PathJoinSubstitution,
    PythonExpression,
)

from launch_ros.actions import Node


def _resolve_world(context):
    """Pick pedestrian vs baseline world based on `pedestrians` arg."""
    pkg_share = get_package_share_directory('representation_aware_mppi_bringup')
    tb3_sim_share = get_package_share_directory('nav2_minimal_tb3_sim')
    pedestrians = LaunchConfiguration('pedestrians').perform(context).lower()
    if pedestrians in ('true', '1', 'yes', 'on'):
        return os.path.join(pkg_share, 'worlds', 'tb3_sandbox_pedestrians.sdf.xacro')
    return os.path.join(tb3_sim_share, 'worlds', 'tb3_sandbox.sdf.xacro')


def launch_setup(context, *args, **kwargs):
    pkg_share = get_package_share_directory('representation_aware_mppi_bringup')
    nav2_bringup_share = get_package_share_directory('nav2_bringup')
    ros_gz_sim_share = get_package_share_directory('ros_gz_sim')

    headless = LaunchConfiguration('headless').perform(context)
    use_rviz = LaunchConfiguration('use_rviz')

    robot_xacro = os.path.join(pkg_share, 'urdf', 'scout_outdoor.sdf.xacro')
    bridge_yaml = os.path.join(pkg_share, 'configs', 'scout_outdoor_bridge.yaml')
    params_file = LaunchConfiguration('params_file').perform(context)
    map_file = LaunchConfiguration('map').perform(context)

    world_path = LaunchConfiguration('world').perform(context)
    if not world_path:
        world_path = _resolve_world(context)

    # Render world xacro to a tmp file (gz expects a real .sdf path).
    rendered_world = os.path.join('/tmp', 'scout_outdoor_world.sdf')
    rc = os.system(
        f"xacro {world_path} headless:={headless.lower()} > {rendered_world}")
    if rc != 0:
        raise RuntimeError(f"xacro failed for world: {world_path}")

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

    # No robot_state_publisher: scout_outdoor is SDF (not URDF), and gz's
    # PosePublisher already emits link+sensor TFs via the `tf` bridge entry.

    # Render robot xacro to a real .sdf path; ros_gz_sim/create needs SDF, not
    # xacro source. Render once at launch time, reuse the path for spawning.
    rendered_robot = os.path.join('/tmp', 'scout_outdoor.sdf')
    rc_robot = os.system(
        f"xacro {robot_xacro} namespace:='' > {rendered_robot}")
    if rc_robot != 0:
        raise RuntimeError(f"xacro failed for robot: {robot_xacro}")

    spawn_robot = Node(
        package='ros_gz_sim',
        executable='create',
        output='screen',
        arguments=[
            '-name', 'scout_outdoor',
            '-file', rendered_robot,
            '-x', '-2.0',
            '-y', '-0.5',
            '-z', '0.05',
            '-Y', '0.0',
            '-allow_renaming', 'false',
        ],
    )

    bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        name='scout_outdoor_bridge',
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
            'map': map_file,
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

    return [gz_sim, spawn_robot, bridge, bringup, rviz]


def generate_launch_description():
    pkg_share = get_package_share_directory('representation_aware_mppi_bringup')
    nav2_bringup_share = get_package_share_directory('nav2_bringup')

    default_params = os.path.join(pkg_share, 'config', 'nav2_outdoor_params.yaml')
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
            'pedestrians', default_value='true',
            description='Use pedestrian world; false -> upstream tb3_sandbox.'),
        DeclareLaunchArgument(
            'world', default_value='',
            description='Override world xacro path. Empty -> chosen by '
                        '`pedestrians` arg.'),
        DeclareLaunchArgument(
            'map', default_value=default_map,
            description='Map yaml. Defaults to tb3_sandbox.'),
        DeclareLaunchArgument(
            'params_file', default_value=default_params,
            description='Nav2 params yaml.'),
        DeclareLaunchArgument(
            'autostart', default_value='true',
            description='Auto-start Nav2 lifecycle nodes.'),
        DeclareLaunchArgument(
            'slam', default_value='False',
            description='Enable SLAM instead of AMCL.'),
        OpaqueFunction(function=launch_setup),
    ])

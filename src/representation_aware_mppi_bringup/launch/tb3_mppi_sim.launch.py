# Copyright 2026 Geonhee Lee
# Licensed under the Apache License, Version 2.0.

"""Phase 0 baseline: TB3 (Gazebo Harmonic) + Nav2 MPPI controller.

Wraps nav2_bringup/tb3_simulation_launch.py and overrides ``params_file``
to point at this package's MPPI-tuned config. Map and world defaults stay
matched (tb3_sandbox) so AMCL converges out of the box.

Step A adds an outdoor sensor suite (3D LiDAR + forward RGB camera) on top
of the upstream waffle. Original IMU, 2D scan, and RealSense are preserved
so the Nav2 baseline keeps using /scan unchanged.
"""

import os

from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration

from launch_ros.actions import Node


def generate_launch_description():
    pkg_share = get_package_share_directory('representation_aware_mppi_bringup')
    nav2_bringup_share = get_package_share_directory('nav2_bringup')
    tb3_sim_share = get_package_share_directory('nav2_minimal_tb3_sim')

    default_params = os.path.join(pkg_share, 'config', 'nav2_mppi_params.yaml')
    default_map = os.path.join(nav2_bringup_share, 'maps', 'tb3_sandbox.yaml')
    default_world = os.path.join(tb3_sim_share, 'worlds', 'tb3_sandbox.sdf.xacro')
    default_robot_sdf = os.path.join(
        pkg_share, 'urdf', 'gz_waffle_outdoor.sdf.xacro')
    extra_bridge_yaml = os.path.join(
        pkg_share, 'configs', 'extra_sensors_bridge.yaml')

    declare_use_sim_time = DeclareLaunchArgument(
        'use_sim_time', default_value='true')
    declare_headless = DeclareLaunchArgument(
        'headless', default_value='False',
        description='Run Gazebo without the GUI client')
    declare_world = DeclareLaunchArgument(
        'world', default_value=default_world)
    declare_map = DeclareLaunchArgument(
        'map', default_value=default_map)
    declare_params_file = DeclareLaunchArgument(
        'params_file', default_value=default_params,
        description='Nav2 parameters file (defaults to MPPI config in this package)')
    declare_autostart = DeclareLaunchArgument(
        'autostart', default_value='true')
    declare_use_rviz = DeclareLaunchArgument(
        'use_rviz', default_value='True')
    declare_slam = DeclareLaunchArgument(
        'slam', default_value='False')
    declare_robot_sdf = DeclareLaunchArgument(
        'robot_sdf', default_value=default_robot_sdf,
        description='Full path to robot SDF/xacro spawned in Gazebo. '
                    'Defaults to outdoor-sensor variant in this package.')
    declare_namespace = DeclareLaunchArgument(
        'namespace', default_value='',
        description='Top-level namespace; passed to upstream and to extra bridge.')

    upstream = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(nav2_bringup_share, 'launch', 'tb3_simulation_launch.py')),
        launch_arguments={
            'namespace': LaunchConfiguration('namespace'),
            'use_sim_time': LaunchConfiguration('use_sim_time'),
            'headless': LaunchConfiguration('headless'),
            'world': LaunchConfiguration('world'),
            'map': LaunchConfiguration('map'),
            'params_file': LaunchConfiguration('params_file'),
            'autostart': LaunchConfiguration('autostart'),
            'use_rviz': LaunchConfiguration('use_rviz'),
            'slam': LaunchConfiguration('slam'),
            'robot_sdf': LaunchConfiguration('robot_sdf'),
        }.items(),
    )

    extra_sensors_bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        name='extra_sensors_bridge',
        namespace=LaunchConfiguration('namespace'),
        parameters=[{
            'config_file': extra_bridge_yaml,
            'expand_gz_topic_names': True,
            'use_sim_time': True,
        }],
        output='screen',
    )

    ld = LaunchDescription()
    ld.add_action(declare_use_sim_time)
    ld.add_action(declare_headless)
    ld.add_action(declare_world)
    ld.add_action(declare_map)
    ld.add_action(declare_params_file)
    ld.add_action(declare_autostart)
    ld.add_action(declare_use_rviz)
    ld.add_action(declare_slam)
    ld.add_action(declare_robot_sdf)
    ld.add_action(declare_namespace)
    ld.add_action(upstream)
    ld.add_action(extra_sensors_bridge)
    return ld

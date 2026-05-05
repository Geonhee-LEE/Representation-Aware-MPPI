"""Evaluation harness for Representation-Aware-MPPI.

v0: path-tracking + smoothness + goal metrics. Pure NumPy, no ROS deps.
Designed to consume nav_msgs/Path + a logged robot trajectory and emit
both per-timestep arrays and scalar summaries.
"""

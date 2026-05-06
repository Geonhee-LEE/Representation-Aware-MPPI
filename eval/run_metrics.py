# SPDX-License-Identifier: BSD-3-Clause
"""ROS2 wrapper around eval.path_tracking_metrics — live `/odom + /plan` → JSON.

v0 integration plan (docs/path_tracking_metrics.md):
    v0 (offline numpy)  →  v1 (rosbag helper)  →  v2 (live ROS2 node).
This file is the v2 entry point but kept minimal: subscribes to /odom and
/plan, buffers into a (T, 6) trajectory + (M, 3) path, and on shutdown (or
on a Trigger service call) computes summary() and writes runs/<run_id>.json.

Pure-Python helpers (`_quat_to_yaw`, `_odom_row_from_pose_twist`,
`_path_msg_rows`, `write_summary_json`) are unit-tested without rclpy so the
shape/yaw/JSON contract is locked even before sim verification.

Run::

    source /opt/ros/jazzy/setup.bash
    PYTHONPATH=$(pwd) python3 -m eval.run_metrics \
        --ros-args -p run_id:=jackal-cafe-001 -p target_speed:=0.5

Then either Ctrl-C (auto-finalize) or call::

    ros2 service call /run_metrics/finalize std_srvs/srv/Trigger {}
"""

from __future__ import annotations

import json
import threading
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Sequence

import numpy as np


# ---------------------------------------------------------------- pure helpers
# (no rclpy / no nav_msgs imports — testable on any Python install)

def _quat_to_yaw(qx: float, qy: float, qz: float, qw: float) -> float:
    """Yaw (z-axis rotation) from a unit quaternion. Right-handed, ENU-like."""
    siny_cosp = 2.0 * (qw * qz + qx * qy)
    cosy_cosp = 1.0 - 2.0 * (qy * qy + qz * qz)
    return float(np.arctan2(siny_cosp, cosy_cosp))


def _odom_row_from_pose_twist(
    stamp_sec: float,
    pos_x: float,
    pos_y: float,
    quat: Sequence[float],
    lin_x: float,
    ang_z: float,
) -> List[float]:
    """Build one (t, x, y, yaw, v, omega) row from pose+twist scalars.

    Kept separate from the ROS callback so tests don't need msg classes.
    `quat` is (qx, qy, qz, qw) — same order as geometry_msgs/Quaternion.
    """
    yaw = _quat_to_yaw(quat[0], quat[1], quat[2], quat[3])
    return [float(stamp_sec), float(pos_x), float(pos_y), yaw,
            float(lin_x), float(ang_z)]


def _path_rows_from_poses(poses: Sequence) -> np.ndarray:
    """Convert a sequence of pose-likes (each with .position, .orientation)
    into an (M, 3) [x, y, yaw] ndarray.

    Each pose must expose position.x / position.y and orientation.x/y/z/w.
    Empty input → shape (0, 3).
    """
    rows: List[List[float]] = []
    for ps in poses:
        p = ps.position
        q = ps.orientation
        rows.append([float(p.x), float(p.y),
                     _quat_to_yaw(q.x, q.y, q.z, q.w)])
    if not rows:
        return np.zeros((0, 3), dtype=float)
    return np.asarray(rows, dtype=float)


@dataclass
class RunMetricsConfig:
    run_id: str = "run-default"
    output_dir: Path = field(default_factory=lambda: Path("runs"))
    target_speed: float = 0.5
    odom_topic: str = "/odom"
    plan_topic: str = "/plan"
    auto_finalize_on_shutdown: bool = True


def write_summary_json(
    traj_rows: Sequence[Sequence[float]],
    path_xy3: np.ndarray,
    cfg: RunMetricsConfig,
) -> Optional[Path]:
    """Compute eval.path_tracking_metrics.summary() and persist JSON.

    Returns the written path, or None if there isn't enough data to compute
    metrics (need ≥ 2 odom samples and ≥ 2 path waypoints — matches the
    polyline contract of path_tracking_metrics).
    """
    if len(traj_rows) < 2 or path_xy3.shape[0] < 2:
        return None

    # Lazy import: eval.path_tracking_metrics may live in the same repo or
    # be sourced from a different commit (PR-staged). Importing at call time
    # also keeps `python -m py_compile eval/run_metrics.py` green even when
    # numpy is the only available dep.
    from eval.path_tracking_metrics import summary  # noqa: WPS433

    traj = np.asarray(traj_rows, dtype=float)
    cfg.output_dir.mkdir(parents=True, exist_ok=True)
    out_path = cfg.output_dir / f"{cfg.run_id}.json"
    metrics = summary(traj, path_xy3, target_speed=cfg.target_speed)
    payload = {
        "run_id": cfg.run_id,
        "target_speed": cfg.target_speed,
        "n_traj": int(len(traj)),
        "n_path": int(path_xy3.shape[0]),
        "metrics": metrics,
    }
    out_path.write_text(json.dumps(payload, indent=2, sort_keys=True))
    return out_path


# ---------------------------------------------------------------- ROS2 node
# Imports are deferred so unit tests on the pure helpers don't pull in rclpy.

def _make_ros_node():
    """Factory returning a RunMetricsNode class bound to the current rclpy.

    Defers all rclpy / nav_msgs / std_srvs imports until the node is built.
    Returns the class — caller does `cls()` after `rclpy.init()`.
    """
    import rclpy
    from rclpy.node import Node
    from rclpy.qos import (QoSDurabilityPolicy, QoSProfile,
                           QoSReliabilityPolicy)
    from nav_msgs.msg import Odometry, Path as NavPath
    from std_srvs.srv import Trigger

    class RunMetricsNode(Node):
        def __init__(self) -> None:
            super().__init__("run_metrics")
            self.declare_parameter("run_id", "run-default")
            self.declare_parameter("output_dir", "runs")
            self.declare_parameter("target_speed", 0.5)
            self.declare_parameter("odom_topic", "/odom")
            self.declare_parameter("plan_topic", "/plan")
            self.declare_parameter("auto_finalize_on_shutdown", True)

            self.cfg = RunMetricsConfig(
                run_id=str(self.get_parameter("run_id").value),
                output_dir=Path(str(self.get_parameter("output_dir").value)),
                target_speed=float(self.get_parameter("target_speed").value),
                odom_topic=str(self.get_parameter("odom_topic").value),
                plan_topic=str(self.get_parameter("plan_topic").value),
                auto_finalize_on_shutdown=bool(
                    self.get_parameter("auto_finalize_on_shutdown").value),
            )

            self._traj: List[List[float]] = []
            self._path: np.ndarray = np.zeros((0, 3), dtype=float)
            self._lock = threading.Lock()

            odom_qos = QoSProfile(
                depth=50,
                reliability=QoSReliabilityPolicy.BEST_EFFORT,
            )
            plan_qos = QoSProfile(
                depth=1,
                reliability=QoSReliabilityPolicy.RELIABLE,
                durability=QoSDurabilityPolicy.TRANSIENT_LOCAL,
            )
            self.create_subscription(
                Odometry, self.cfg.odom_topic, self._odom_cb, odom_qos)
            self.create_subscription(
                NavPath, self.cfg.plan_topic, self._plan_cb, plan_qos)
            self.create_service(Trigger, "~/finalize", self._finalize_srv)

            self.get_logger().info(
                "run_metrics: run_id=%s odom=%s plan=%s output=%s" % (
                    self.cfg.run_id, self.cfg.odom_topic,
                    self.cfg.plan_topic, str(self.cfg.output_dir)))

        def _odom_cb(self, msg) -> None:
            stamp = msg.header.stamp
            t = float(stamp.sec) + float(stamp.nanosec) * 1e-9
            p = msg.pose.pose.position
            q = msg.pose.pose.orientation
            row = _odom_row_from_pose_twist(
                t, p.x, p.y, (q.x, q.y, q.z, q.w),
                msg.twist.twist.linear.x, msg.twist.twist.angular.z)
            with self._lock:
                self._traj.append(row)

        def _plan_cb(self, msg) -> None:
            arr = _path_rows_from_poses([ps.pose for ps in msg.poses])
            if arr.shape[0] >= 2:
                with self._lock:
                    self._path = arr

        def _finalize_srv(self, _request, response):
            written = self._finalize()
            if written is None:
                response.success = False
                response.message = (
                    "insufficient data: need >=2 odom samples and "
                    ">=2 plan waypoints")
            else:
                response.success = True
                response.message = str(written)
            return response

        def _finalize(self) -> Optional[Path]:
            with self._lock:
                traj_rows = list(self._traj)
                path_xy3 = self._path.copy()
            written = write_summary_json(traj_rows, path_xy3, self.cfg)
            if written is None:
                self.get_logger().warn(
                    "run_metrics: not enough data; no JSON written")
            else:
                self.get_logger().info(
                    "run_metrics: wrote %s" % str(written))
            return written

        def shutdown(self) -> None:
            if self.cfg.auto_finalize_on_shutdown:
                self._finalize()

    return RunMetricsNode


def main(args=None):  # pragma: no cover — exercised in sim only
    import rclpy
    rclpy.init(args=args)
    cls = _make_ros_node()
    node = cls()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.shutdown()
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":  # pragma: no cover
    main()

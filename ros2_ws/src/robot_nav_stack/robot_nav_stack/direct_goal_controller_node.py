from __future__ import annotations

import math

import rclpy
from geometry_msgs.msg import PoseStamped, Twist
from rclpy.node import Node

from .core import Pose2D, angle_diff, yaw_from_quaternion


class DirectGoalControllerNode(Node):
    """Drive directly toward a map-frame goal without Nav2 planning."""

    def __init__(self) -> None:
        super().__init__("direct_goal_controller_node")
        self.declare_parameter("robot_pose_topic", "/robot_pose_map")
        self.declare_parameter("goal_pose_topic", "/bbox_goal_pose")
        self.declare_parameter("cmd_vel_topic", "/cmd_vel")
        self.declare_parameter("control_period_sec", 0.05)
        self.declare_parameter("max_linear_mps", 0.08)
        self.declare_parameter("max_angular_radps", 0.7)
        self.declare_parameter("linear_kp", 0.45)
        self.declare_parameter("angular_kp", 1.6)
        self.declare_parameter("xy_goal_tolerance_m", 0.08)
        self.declare_parameter("yaw_align_tolerance_rad", math.radians(18.0))
        self.declare_parameter("goal_timeout_sec", 1.5)
        self.declare_parameter("rotate_in_place_first", True)

        self.robot_pose: Pose2D | None = None
        self.goal_pose: Pose2D | None = None
        self.goal_stamp_sec: float | None = None

        self.cmd_pub = self.create_publisher(
            Twist,
            str(self.get_parameter("cmd_vel_topic").value),
            10,
        )
        self.create_subscription(
            PoseStamped,
            str(self.get_parameter("robot_pose_topic").value),
            self._on_robot_pose,
            10,
        )
        self.create_subscription(
            PoseStamped,
            str(self.get_parameter("goal_pose_topic").value),
            self._on_goal_pose,
            10,
        )
        period = max(0.02, float(self.get_parameter("control_period_sec").value))
        self.timer = self.create_timer(period, self._control_step)

    def _on_robot_pose(self, msg: PoseStamped) -> None:
        self.robot_pose = _pose_from_msg(msg)

    def _on_goal_pose(self, msg: PoseStamped) -> None:
        self.goal_pose = _pose_from_msg(msg)
        stamp_sec = float(msg.header.stamp.sec) + float(msg.header.stamp.nanosec) * 1e-9
        self.goal_stamp_sec = stamp_sec if stamp_sec > 0.0 else self._now_sec()

    def _control_step(self) -> None:
        cmd = Twist()
        if self.robot_pose is None or self.goal_pose is None or self.goal_stamp_sec is None:
            self.cmd_pub.publish(cmd)
            return

        timeout = float(self.get_parameter("goal_timeout_sec").value)
        if timeout > 0.0 and self._now_sec() - self.goal_stamp_sec > timeout:
            self.cmd_pub.publish(cmd)
            return

        dx = self.goal_pose.x - self.robot_pose.x
        dy = self.goal_pose.y - self.robot_pose.y
        distance = math.hypot(dx, dy)
        xy_tol = max(0.0, float(self.get_parameter("xy_goal_tolerance_m").value))
        if distance <= xy_tol:
            self.cmd_pub.publish(cmd)
            return

        heading = math.atan2(dy, dx)
        heading_error = angle_diff(heading, self.robot_pose.theta)
        max_w = max(0.0, float(self.get_parameter("max_angular_radps").value))
        cmd.angular.z = _clamp(
            float(self.get_parameter("angular_kp").value) * heading_error,
            -max_w,
            max_w,
        )

        align_tol = max(0.0, float(self.get_parameter("yaw_align_tolerance_rad").value))
        rotate_first = bool(self.get_parameter("rotate_in_place_first").value)
        if rotate_first and abs(heading_error) > align_tol:
            self.cmd_pub.publish(cmd)
            return

        max_v = max(0.0, float(self.get_parameter("max_linear_mps").value))
        cmd.linear.x = _clamp(
            float(self.get_parameter("linear_kp").value) * distance,
            0.0,
            max_v,
        )
        self.cmd_pub.publish(cmd)

    def _now_sec(self) -> float:
        return self.get_clock().now().nanoseconds * 1e-9


def _pose_from_msg(msg: PoseStamped) -> Pose2D:
    q = msg.pose.orientation
    return Pose2D(
        x=float(msg.pose.position.x),
        y=float(msg.pose.position.y),
        theta=yaw_from_quaternion(q.x, q.y, q.z, q.w),
    )


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def main() -> None:
    rclpy.init()
    node = DirectGoalControllerNode()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()

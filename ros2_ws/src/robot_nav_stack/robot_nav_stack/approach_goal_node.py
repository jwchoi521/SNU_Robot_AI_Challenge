from __future__ import annotations

import math

import rclpy
from geometry_msgs.msg import PoseStamped
from rclpy.node import Node

from .core import Pose2D, quaternion_from_yaw, yaw_from_quaternion


class ApproachGoalNode(Node):
    """Generate a target-facing approach goal.

    Production version should try multiple candidates through Nav2 planning.
    This node publishes the best geometric candidate as a first integration step.
    """

    def __init__(self) -> None:
        super().__init__("approach_goal_node")
        self.declare_parameter("approach_radius_m", 0.9)
        self.declare_parameter("angle_step_deg", 15.0)

        self.robot_pose: Pose2D | None = None
        self.target_pose: Pose2D | None = None
        self.pub = self.create_publisher(PoseStamped, "/approach_goal", 10)
        self.robot_sub = self.create_subscription(PoseStamped, "/robot_pose_map", self.on_robot_pose, 10)
        self.target_sub = self.create_subscription(PoseStamped, "/target_pose_map", self.on_target_pose, 10)
        self.timer = self.create_timer(0.2, self.publish_goal)

    def on_robot_pose(self, msg: PoseStamped) -> None:
        self.robot_pose = self._pose_from_msg(msg)

    def on_target_pose(self, msg: PoseStamped) -> None:
        self.target_pose = self._pose_from_msg(msg)

    def publish_goal(self) -> None:
        if self.robot_pose is None or self.target_pose is None:
            return

        radius = float(self.get_parameter("approach_radius_m").value)
        step = math.radians(float(self.get_parameter("angle_step_deg").value))
        steps = max(1, int(round(2.0 * math.pi / step)))

        best_score = float("inf")
        best_goal: Pose2D | None = None
        for i in range(steps):
            theta_to_target = i * 2.0 * math.pi / steps
            gx = self.target_pose.x - radius * math.cos(theta_to_target)
            gy = self.target_pose.y - radius * math.sin(theta_to_target)
            heading = math.atan2(self.target_pose.y - gy, self.target_pose.x - gx)
            score = math.hypot(gx - self.robot_pose.x, gy - self.robot_pose.y)
            if score < best_score:
                best_score = score
                best_goal = Pose2D(gx, gy, heading)

        if best_goal is None:
            return

        msg = PoseStamped()
        msg.header.frame_id = "map"
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.pose.position.x = best_goal.x
        msg.pose.position.y = best_goal.y
        qx, qy, qz, qw = quaternion_from_yaw(best_goal.theta)
        msg.pose.orientation.x = qx
        msg.pose.orientation.y = qy
        msg.pose.orientation.z = qz
        msg.pose.orientation.w = qw
        self.pub.publish(msg)

    @staticmethod
    def _pose_from_msg(msg: PoseStamped) -> Pose2D:
        q = msg.pose.orientation
        return Pose2D(
            x=msg.pose.position.x,
            y=msg.pose.position.y,
            theta=yaw_from_quaternion(q.x, q.y, q.z, q.w),
        )


def main() -> None:
    rclpy.init()
    node = ApproachGoalNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()


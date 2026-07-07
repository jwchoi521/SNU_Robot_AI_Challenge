from __future__ import annotations

import math

import rclpy
from geometry_msgs.msg import PoseStamped, Twist
from nav_msgs.msg import Path
from rclpy.node import Node

from .core import Pose2D, angle_diff, yaw_from_quaternion


class PurePursuitNode(Node):
    """Fallback path follower.

    In production, Nav2 controller server can replace this node. This is useful
    for early bring-up when you only need path -> cmd_vel.
    """

    def __init__(self) -> None:
        super().__init__("pure_pursuit_node")
        self.declare_parameter("lookahead_m", 0.55)
        self.declare_parameter("max_v", 0.45)
        self.declare_parameter("max_w", 1.4)
        self.declare_parameter("xy_goal_tolerance_m", 0.12)
        self.declare_parameter("yaw_goal_tolerance_rad", math.radians(10.0))

        self.pose: Pose2D | None = None
        self.path: list[Pose2D] = []
        self.cmd_pub = self.create_publisher(Twist, "/cmd_vel", 10)
        self.pose_sub = self.create_subscription(PoseStamped, "/robot_pose_map", self.on_pose, 10)
        self.path_sub = self.create_subscription(Path, "/planned_path", self.on_path, 10)
        self.timer = self.create_timer(0.05, self.control_step)

    def on_pose(self, msg: PoseStamped) -> None:
        q = msg.pose.orientation
        self.pose = Pose2D(
            msg.pose.position.x,
            msg.pose.position.y,
            yaw_from_quaternion(q.x, q.y, q.z, q.w),
        )

    def on_path(self, msg: Path) -> None:
        self.path = []
        for pose_stamped in msg.poses:
            q = pose_stamped.pose.orientation
            self.path.append(
                Pose2D(
                    pose_stamped.pose.position.x,
                    pose_stamped.pose.position.y,
                    yaw_from_quaternion(q.x, q.y, q.z, q.w),
                )
            )

    def control_step(self) -> None:
        cmd = Twist()
        if self.pose is None or not self.path:
            self.cmd_pub.publish(cmd)
            return

        goal = self.path[-1]
        xy_tol = float(self.get_parameter("xy_goal_tolerance_m").value)
        yaw_tol = float(self.get_parameter("yaw_goal_tolerance_rad").value)
        dx_goal = goal.x - self.pose.x
        dy_goal = goal.y - self.pose.y
        if math.hypot(dx_goal, dy_goal) <= xy_tol:
            yaw_error = angle_diff(goal.theta, self.pose.theta)
            if abs(yaw_error) > yaw_tol:
                max_w = float(self.get_parameter("max_w").value)
                cmd.angular.z = max(-max_w, min(max_w, 1.6 * yaw_error))
            self.cmd_pub.publish(cmd)
            return

        target = self._lookahead_point()
        dx = target.x - self.pose.x
        dy = target.y - self.pose.y
        local_x = math.cos(self.pose.theta) * dx + math.sin(self.pose.theta) * dy
        local_y = -math.sin(self.pose.theta) * dx + math.cos(self.pose.theta) * dy
        lookahead = max(math.hypot(local_x, local_y), 1e-6)
        curvature = 2.0 * local_y / (lookahead * lookahead)
        max_v = float(self.get_parameter("max_v").value)
        max_w = float(self.get_parameter("max_w").value)
        cmd.linear.x = max_v
        cmd.angular.z = max(-max_w, min(max_w, max_v * curvature))
        self.cmd_pub.publish(cmd)

    def _lookahead_point(self) -> Pose2D:
        assert self.pose is not None
        lookahead = float(self.get_parameter("lookahead_m").value)
        nearest = min(range(len(self.path)), key=lambda i: math.hypot(self.path[i].x - self.pose.x, self.path[i].y - self.pose.y))
        for point in self.path[nearest:]:
            if math.hypot(point.x - self.pose.x, point.y - self.pose.y) >= lookahead:
                return point
        return self.path[-1]


def main() -> None:
    rclpy.init()
    node = PurePursuitNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()

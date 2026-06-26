from __future__ import annotations

from math import atan2, cos, isfinite, sin

import rclpy
from geometry_msgs.msg import TransformStamped
from nav_msgs.msg import Odometry
from rclpy.node import Node
from sensor_msgs.msg import JointState
from tf2_ros import TransformBroadcaster


class FourWheelOdometry(Node):
    """Estimate base odometry from four independently measured wheel speeds."""

    def __init__(self) -> None:
        super().__init__("four_wheel_odometry")

        self.declare_parameter("joint_states_topic", "/joint_states")
        self.declare_parameter("odom_topic", "/wheel/odom")
        self.declare_parameter("odom_frame", "odom")
        self.declare_parameter("base_frame", "base_link")
        self.declare_parameter("publish_tf", False)
        self.declare_parameter("drive_model", "skid_steer")
        self.declare_parameter("wheel_radius_m", 0.035)
        self.declare_parameter("track_width_m", 0.112)
        self.declare_parameter("wheelbase_m", 0.0986)
        self.declare_parameter("front_left_joint", "front_left_wheel_joint")
        self.declare_parameter("front_right_joint", "front_right_wheel_joint")
        self.declare_parameter("rear_left_joint", "rear_left_wheel_joint")
        self.declare_parameter("rear_right_joint", "rear_right_wheel_joint")

        self._odom_frame = str(self.get_parameter("odom_frame").value)
        self._base_frame = str(self.get_parameter("base_frame").value)
        self._publish_tf = bool(self.get_parameter("publish_tf").value)
        self._drive_model = str(self.get_parameter("drive_model").value)
        self._wheel_radius_m = float(self.get_parameter("wheel_radius_m").value)
        self._track_width_m = float(self.get_parameter("track_width_m").value)
        self._wheelbase_m = float(self.get_parameter("wheelbase_m").value)
        self._joint_names = (
            str(self.get_parameter("front_left_joint").value),
            str(self.get_parameter("front_right_joint").value),
            str(self.get_parameter("rear_left_joint").value),
            str(self.get_parameter("rear_right_joint").value),
        )

        self._x = 0.0
        self._y = 0.0
        self._yaw = 0.0
        self._last_stamp = None
        self._last_positions: dict[str, float] = {}

        self._odom_pub = self.create_publisher(
            Odometry, str(self.get_parameter("odom_topic").value), 10
        )
        self._tf_broadcaster = TransformBroadcaster(self) if self._publish_tf else None
        self._sub = self.create_subscription(
            JointState,
            str(self.get_parameter("joint_states_topic").value),
            self._on_joint_state,
            10,
        )

        self.get_logger().info(
            f"Four-wheel odometry using {self._drive_model}; joints={self._joint_names}"
        )

    def _on_joint_state(self, msg: JointState) -> None:
        stamp = msg.header.stamp
        now_sec = stamp.sec + stamp.nanosec * 1.0e-9
        if self._last_stamp is None:
            self._last_stamp = now_sec
            self._cache_positions(msg)
            return

        dt = now_sec - self._last_stamp
        if dt <= 0.0 or dt > 1.0:
            self._last_stamp = now_sec
            self._cache_positions(msg)
            return

        wheel_speeds = self._wheel_speeds_rad_s(msg, dt)
        if wheel_speeds is None:
            return

        vx, vy, wz = self._body_twist(wheel_speeds)
        self._integrate(vx, vy, wz, dt)
        self._publish_odom(msg, vx, vy, wz)

        self._last_stamp = now_sec
        self._cache_positions(msg)

    def _wheel_speeds_rad_s(
        self, msg: JointState, dt: float
    ) -> tuple[float, float, float, float] | None:
        name_to_index = {name: index for index, name in enumerate(msg.name)}
        speeds: list[float] = []

        for joint_name in self._joint_names:
            index = name_to_index.get(joint_name)
            if index is None:
                return None

            velocity = _read_index(msg.velocity, index)
            if velocity is not None and isfinite(velocity):
                speeds.append(velocity)
                continue

            position = _read_index(msg.position, index)
            last_position = self._last_positions.get(joint_name)
            if position is None or last_position is None:
                return None
            speeds.append((position - last_position) / dt)

        return speeds[0], speeds[1], speeds[2], speeds[3]

    def _body_twist(
        self, wheel_speeds: tuple[float, float, float, float]
    ) -> tuple[float, float, float]:
        fl, fr, rl, rr = wheel_speeds
        r = self._wheel_radius_m

        if self._drive_model == "mecanum":
            lx_plus_ly = 0.5 * (self._wheelbase_m + self._track_width_m)
            vx = r * (fl + fr + rl + rr) / 4.0
            vy = r * (-fl + fr + rl - rr) / 4.0
            wz = r * (-fl + fr - rl + rr) / (4.0 * lx_plus_ly)
            return vx, vy, wz

        left = r * (fl + rl) / 2.0
        right = r * (fr + rr) / 2.0
        vx = (left + right) / 2.0
        wz = (right - left) / self._track_width_m
        return vx, 0.0, wz

    def _integrate(self, vx: float, vy: float, wz: float, dt: float) -> None:
        mid_yaw = self._yaw + 0.5 * wz * dt
        self._x += (vx * cos(mid_yaw) - vy * sin(mid_yaw)) * dt
        self._y += (vx * sin(mid_yaw) + vy * cos(mid_yaw)) * dt
        self._yaw = _normalize_angle(self._yaw + wz * dt)

    def _publish_odom(self, joint_msg: JointState, vx: float, vy: float, wz: float) -> None:
        odom = Odometry()
        odom.header.stamp = joint_msg.header.stamp
        odom.header.frame_id = self._odom_frame
        odom.child_frame_id = self._base_frame
        odom.pose.pose.position.x = self._x
        odom.pose.pose.position.y = self._y
        odom.pose.pose.orientation.z = sin(self._yaw / 2.0)
        odom.pose.pose.orientation.w = cos(self._yaw / 2.0)
        odom.twist.twist.linear.x = vx
        odom.twist.twist.linear.y = vy
        odom.twist.twist.angular.z = wz
        odom.pose.covariance[0] = 0.05
        odom.pose.covariance[7] = 0.05
        odom.pose.covariance[35] = 0.10
        odom.twist.covariance[0] = 0.05
        odom.twist.covariance[7] = 0.05
        odom.twist.covariance[35] = 0.10
        self._odom_pub.publish(odom)

        if self._tf_broadcaster is not None:
            transform = TransformStamped()
            transform.header = odom.header
            transform.child_frame_id = self._base_frame
            transform.transform.translation.x = self._x
            transform.transform.translation.y = self._y
            transform.transform.rotation = odom.pose.pose.orientation
            self._tf_broadcaster.sendTransform(transform)

    def _cache_positions(self, msg: JointState) -> None:
        name_to_index = {name: index for index, name in enumerate(msg.name)}
        for joint_name in self._joint_names:
            index = name_to_index.get(joint_name)
            if index is None:
                continue
            position = _read_index(msg.position, index)
            if position is not None:
                self._last_positions[joint_name] = position


def _read_index(values: list[float] | tuple[float, ...], index: int) -> float | None:
    if index >= len(values):
        return None
    return float(values[index])


def _normalize_angle(angle: float) -> float:
    return atan2(sin(angle), cos(angle))


def main() -> None:
    rclpy.init()
    node = FourWheelOdometry()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()

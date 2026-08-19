from __future__ import annotations

from math import isfinite

import rclpy
from geometry_msgs.msg import Twist
from rclpy.node import Node
from snu_robot_interfaces.msg import FourWheelCommand
from std_msgs.msg import Bool


class CmdVelToFourWheel(Node):
    """Convert body velocity commands into four independent wheel commands."""

    def __init__(self) -> None:
        super().__init__("cmd_vel_to_four_wheel")

        self.declare_parameter("cmd_vel_topic", "/cmd_vel")
        self.declare_parameter("wheel_command_topic", "/wheel_commands")
        self.declare_parameter("drive_model", "skid_steer")
        self.declare_parameter("command_mode", "velocity")
        self.declare_parameter("wheel_radius_m", 0.033)
        self.declare_parameter("track_width_m", 0.30)
        self.declare_parameter("wheelbase_m", 0.235)
        self.declare_parameter("max_wheel_velocity_rad_s", 20.0)
        self.declare_parameter("front_left_sign", 1.0)
        self.declare_parameter("front_right_sign", 1.0)
        self.declare_parameter("rear_left_sign", 1.0)
        self.declare_parameter("rear_right_sign", 1.0)
        self.declare_parameter("startup_escape_active_topic", "/startup_escape/active")
        self.declare_parameter("startup_escape_block_on_start", False)

        self._drive_model = str(self.get_parameter("drive_model").value)
        self._command_mode = str(self.get_parameter("command_mode").value)
        self._wheel_radius_m = float(self.get_parameter("wheel_radius_m").value)
        self._track_width_m = float(self.get_parameter("track_width_m").value)
        self._wheelbase_m = float(self.get_parameter("wheelbase_m").value)
        self._max_wheel_velocity_rad_s = float(
            self.get_parameter("max_wheel_velocity_rad_s").value
        )
        self._wheel_signs = (
            float(self.get_parameter("front_left_sign").value),
            float(self.get_parameter("front_right_sign").value),
            float(self.get_parameter("rear_left_sign").value),
            float(self.get_parameter("rear_right_sign").value),
        )
        self._startup_escape_active = bool(
            self.get_parameter("startup_escape_block_on_start").value
        )
        self._last_startup_block_log_sec = 0.0

        self._publisher = self.create_publisher(
            FourWheelCommand,
            str(self.get_parameter("wheel_command_topic").value),
            10,
        )
        self._subscription = self.create_subscription(
            Twist,
            str(self.get_parameter("cmd_vel_topic").value),
            self._on_cmd_vel,
            10,
        )
        startup_escape_active_topic = str(
            self.get_parameter("startup_escape_active_topic").value
        )
        if startup_escape_active_topic:
            self._startup_escape_subscription = self.create_subscription(
                Bool,
                startup_escape_active_topic,
                self._on_startup_escape_active,
                10,
            )

        self.get_logger().info(
            f"Mapping /cmd_vel to four-wheel commands using {self._drive_model}"
        )

    def _on_cmd_vel(self, msg: Twist) -> None:
        if self._startup_escape_active:
            self._log_startup_block_if_needed()
            return

        vx = _finite_or_zero(msg.linear.x)
        vy = _finite_or_zero(msg.linear.y)
        wz = _finite_or_zero(msg.angular.z)
        wheel_velocities = self._wheel_velocities_rad_s(vx, vy, wz)
        wheel_velocities = tuple(
            sign * _clamp(value, -self._max_wheel_velocity_rad_s, self._max_wheel_velocity_rad_s)
            for value, sign in zip(wheel_velocities, self._wheel_signs)
        )

        command = FourWheelCommand()
        command.header.stamp = self.get_clock().now().to_msg()

        if self._command_mode == "normalized_power":
            command.command_mode = FourWheelCommand.NORMALIZED_POWER
            values = tuple(value / self._max_wheel_velocity_rad_s for value in wheel_velocities)
        else:
            command.command_mode = FourWheelCommand.VELOCITY_RAD_S
            values = wheel_velocities

        (
            command.front_left,
            command.front_right,
            command.rear_left,
            command.rear_right,
        ) = values
        self._publisher.publish(command)

    def _on_startup_escape_active(self, msg: Bool) -> None:
        active = bool(msg.data)
        if active == self._startup_escape_active:
            return
        self._startup_escape_active = active
        state = "blocking" if active else "released"
        self.get_logger().info(f"startup escape cmd_vel gate {state}")

    def _log_startup_block_if_needed(self) -> None:
        now_sec = self.get_clock().now().nanoseconds * 1.0e-9
        if now_sec - self._last_startup_block_log_sec < 1.0:
            return
        self._last_startup_block_log_sec = now_sec
        self.get_logger().info("ignoring /cmd_vel while startup escape is active")

    def _wheel_velocities_rad_s(
        self, vx: float, vy: float, wz: float
    ) -> tuple[float, float, float, float]:
        radius = self._wheel_radius_m

        if self._drive_model == "mecanum":
            lx_plus_ly = 0.5 * (self._wheelbase_m + self._track_width_m)
            return (
                (vx - vy - lx_plus_ly * wz) / radius,
                (vx + vy + lx_plus_ly * wz) / radius,
                (vx + vy - lx_plus_ly * wz) / radius,
                (vx - vy + lx_plus_ly * wz) / radius,
            )

        left = vx - wz * self._track_width_m / 2.0
        right = vx + wz * self._track_width_m / 2.0
        return left / radius, right / radius, left / radius, right / radius


def _finite_or_zero(value: float) -> float:
    return float(value) if isfinite(float(value)) else 0.0


def _clamp(value: float, lower: float, upper: float) -> float:
    return max(lower, min(upper, value))


def main() -> None:
    rclpy.init()
    node = CmdVelToFourWheel()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()

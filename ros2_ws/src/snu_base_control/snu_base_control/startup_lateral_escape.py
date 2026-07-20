from __future__ import annotations

from math import isfinite

import rclpy
from rclpy.node import Node
from snu_robot_interfaces.msg import FourWheelCommand


class StartupLateralEscape(Node):
    """Publish a short lateral wheel command at launch to clear a tight start area."""

    def __init__(self) -> None:
        super().__init__("startup_lateral_escape")

        self.declare_parameter("wheel_command_topic", "/wheel_commands")
        self.declare_parameter("start_delay_sec", 6.0)
        self.declare_parameter("distance_m", 0.50)
        self.declare_parameter("speed_mps", 0.30)
        self.declare_parameter("wheel_radius_m", 0.033)
        self.declare_parameter("direction_sign", 1.0)
        self.declare_parameter("publish_hz", 30.0)
        self.declare_parameter("stop_hold_sec", 0.40)

        self._publisher = self.create_publisher(
            FourWheelCommand,
            str(self.get_parameter("wheel_command_topic").value),
            10,
        )

        self._start_delay_sec = max(
            0.0,
            _finite_or_default(self.get_parameter("start_delay_sec").value, 6.0),
        )
        self._distance_m = max(
            0.0,
            _finite_or_default(self.get_parameter("distance_m").value, 0.50),
        )
        self._speed_mps = max(
            0.0,
            _finite_or_default(self.get_parameter("speed_mps").value, 0.30),
        )
        self._wheel_radius_m = max(
            1.0e-6,
            _finite_or_default(self.get_parameter("wheel_radius_m").value, 0.033),
        )
        self._direction_sign = (
            1.0
            if _finite_or_default(self.get_parameter("direction_sign").value, 1.0) >= 0.0
            else -1.0
        )
        self._stop_hold_sec = max(
            0.0,
            _finite_or_default(self.get_parameter("stop_hold_sec").value, 0.40),
        )

        now_sec = self._now_sec()
        run_sec = self._distance_m / self._speed_mps if self._speed_mps > 0.0 else 0.0
        self._start_sec = now_sec + self._start_delay_sec
        self._end_sec = self._start_sec + run_sec
        self._stop_until_sec = self._end_sec + self._stop_hold_sec
        self.done = self._distance_m <= 0.0 or self._speed_mps <= 0.0
        self._started = False
        self._stopping = False

        publish_hz = max(
            1.0,
            _finite_or_default(self.get_parameter("publish_hz").value, 30.0),
        )
        self._timer = self.create_timer(1.0 / publish_hz, self._on_timer)
        self.get_logger().info(
            "startup lateral escape armed: "
            f"delay={self._start_delay_sec:.2f}s, "
            f"distance={self._distance_m:.2f}m, speed={self._speed_mps:.2f}m/s, "
            f"direction_sign={self._direction_sign:+.0f}"
        )

    def _on_timer(self) -> None:
        if self.done:
            return

        now_sec = self._now_sec()
        if now_sec < self._start_sec:
            return

        if now_sec < self._end_sec:
            if not self._started:
                self._started = True
                self.get_logger().info("starting +Y startup lateral escape")
            self._publish_lateral_command()
            return

        if now_sec < self._stop_until_sec:
            if not self._stopping:
                self._stopping = True
                self.get_logger().info("startup lateral escape complete; stopping wheels")
            self._publish_stop()
            return

        self._publish_stop()
        self.done = True
        self.get_logger().info("startup lateral escape node done")

    def _publish_lateral_command(self) -> None:
        wheel_rad_s = self._direction_sign * self._speed_mps / self._wheel_radius_m
        self._publish_wheels(
            front_left=-wheel_rad_s,
            front_right=wheel_rad_s,
            rear_left=wheel_rad_s,
            rear_right=-wheel_rad_s,
        )

    def _publish_stop(self) -> None:
        self._publish_wheels(
            front_left=0.0,
            front_right=0.0,
            rear_left=0.0,
            rear_right=0.0,
        )

    def _publish_wheels(
        self,
        *,
        front_left: float,
        front_right: float,
        rear_left: float,
        rear_right: float,
    ) -> None:
        msg = FourWheelCommand()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.command_mode = FourWheelCommand.VELOCITY_RAD_S
        msg.front_left = float(front_left)
        msg.front_right = float(front_right)
        msg.rear_left = float(rear_left)
        msg.rear_right = float(rear_right)
        self._publisher.publish(msg)

    def _now_sec(self) -> float:
        return self.get_clock().now().nanoseconds * 1.0e-9


def _finite_or_default(value, default: float) -> float:
    number = float(value)
    return number if isfinite(number) else default


def main() -> None:
    rclpy.init()
    node = StartupLateralEscape()
    try:
        while rclpy.ok() and not node.done:
            rclpy.spin_once(node, timeout_sec=0.1)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()

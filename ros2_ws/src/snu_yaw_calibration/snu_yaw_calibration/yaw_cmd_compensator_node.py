from __future__ import annotations

import math

import rclpy
from geometry_msgs.msg import Twist
from rclpy.node import Node

from .yaw_response_model import YawResponseModel


class YawCommandCompensator(Node):
    """Convert desired body yaw rate into calibrated internal yaw command."""

    def __init__(self) -> None:
        super().__init__("yaw_cmd_compensator")

        self.declare_parameter("model_path", "")
        self.declare_parameter("input_cmd_vel_topic", "/cmd_vel_raw")
        self.declare_parameter("output_cmd_vel_topic", "/cmd_vel")
        self.declare_parameter("enabled", True)
        self.declare_parameter("deadband_rad_s", 0.01)
        self.declare_parameter("max_abs_yaw_cmd_rad_s", 4.0)
        self.declare_parameter("log_period_sec", 1.0)

        model_path = str(self.get_parameter("model_path").value).strip()
        if not model_path:
            raise ValueError("model_path parameter is required")
        self._model = YawResponseModel.from_file(model_path)
        self._enabled = bool(self.get_parameter("enabled").value)
        self._deadband_rad_s = max(0.0, float(self.get_parameter("deadband_rad_s").value))
        self._max_abs_yaw_cmd_rad_s = max(
            0.1, float(self.get_parameter("max_abs_yaw_cmd_rad_s").value)
        )
        self._log_period_sec = max(0.1, float(self.get_parameter("log_period_sec").value))
        self._last_log_sec = 0.0

        self._publisher = self.create_publisher(
            Twist, str(self.get_parameter("output_cmd_vel_topic").value), 10
        )
        self._subscription = self.create_subscription(
            Twist,
            str(self.get_parameter("input_cmd_vel_topic").value),
            self._on_cmd_vel,
            10,
        )
        self.get_logger().info(
            f"Loaded yaw response model from {model_path}; "
            f"{self.get_parameter('input_cmd_vel_topic').value} -> "
            f"{self.get_parameter('output_cmd_vel_topic').value}"
        )

    def _on_cmd_vel(self, msg: Twist) -> None:
        output = Twist()
        output.linear = msg.linear
        output.angular = msg.angular

        target_wz = float(msg.angular.z)
        linear_x = float(msg.linear.x)
        if self._enabled and math.isfinite(target_wz) and math.isfinite(linear_x):
            yaw_cmd, predicted_wz, reachable = self._model.choose_yaw_cmd(
                linear_x,
                target_wz,
                deadband_rad_s=self._deadband_rad_s,
                max_abs_yaw_cmd_rad_s=self._max_abs_yaw_cmd_rad_s,
            )
            output.angular.z = yaw_cmd
            self._log_mapping(linear_x, target_wz, yaw_cmd, predicted_wz, reachable)

        self._publisher.publish(output)

    def _log_mapping(
        self,
        linear_x: float,
        target_wz: float,
        yaw_cmd: float,
        predicted_wz: float,
        reachable: bool,
    ) -> None:
        now_sec = self.get_clock().now().nanoseconds * 1.0e-9
        if now_sec - self._last_log_sec < self._log_period_sec:
            return
        self._last_log_sec = now_sec
        state = "ok" if reachable else "limited"
        self.get_logger().info(
            f"yaw_comp {state}: v={linear_x:+.3f} target_wz={target_wz:+.3f} "
            f"yaw_cmd={yaw_cmd:+.3f} predicted_wz={predicted_wz:+.3f}"
        )


def main() -> None:
    rclpy.init()
    node = YawCommandCompensator()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()


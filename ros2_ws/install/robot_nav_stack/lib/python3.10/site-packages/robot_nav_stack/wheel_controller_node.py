from __future__ import annotations

from dataclasses import dataclass

import rclpy
from geometry_msgs.msg import Twist
from rclpy.node import Node
from std_msgs.msg import Float32MultiArray


@dataclass
class PID:
    kp: float
    ki: float
    kd: float
    out_min: float
    out_max: float
    integral: float = 0.0
    prev_error: float | None = None

    def update(self, target: float, measured: float, dt: float) -> float:
        if dt <= 0.0:
            return 0.0
        error = target - measured
        self.integral += error * dt
        derivative = 0.0 if self.prev_error is None else (error - self.prev_error) / dt
        self.prev_error = error
        output = self.kp * error + self.ki * self.integral + self.kd * derivative
        if output > self.out_max:
            output = self.out_max
            self.integral -= error * dt
        if output < self.out_min:
            output = self.out_min
            self.integral -= error * dt
        return output


class WheelControllerNode(Node):
    """Convert cmd_vel to wheel voltage/PWM commands with encoder feedback."""

    def __init__(self) -> None:
        super().__init__("wheel_controller_node")
        self.declare_parameter("wheel_radius_m", 0.033)
        self.declare_parameter("track_width_m", 0.30)
        self.declare_parameter("voltage_limit", 12.0)
        self.declare_parameter("kp", 2.0)
        self.declare_parameter("ki", 0.2)
        self.declare_parameter("kd", 0.02)

        limit = float(self.get_parameter("voltage_limit").value)
        kp = float(self.get_parameter("kp").value)
        ki = float(self.get_parameter("ki").value)
        kd = float(self.get_parameter("kd").value)
        self.left_pid = PID(kp, ki, kd, -limit, limit)
        self.right_pid = PID(kp, ki, kd, -limit, limit)
        self.target_left = 0.0
        self.target_right = 0.0
        self.measured_left = 0.0
        self.measured_right = 0.0
        self.prev_time = self.get_clock().now()

        self.cmd_sub = self.create_subscription(Twist, "/cmd_vel", self.on_cmd_vel, 10)
        self.enc_sub = self.create_subscription(Float32MultiArray, "/wheel_speed_measured", self.on_wheel_speed, 10)
        self.pub = self.create_publisher(Float32MultiArray, "/motor_voltage_cmd", 10)
        self.timer = self.create_timer(0.01, self.control_step)

    def on_cmd_vel(self, msg: Twist) -> None:
        radius = float(self.get_parameter("wheel_radius_m").value)
        track = float(self.get_parameter("track_width_m").value)
        v_left = msg.linear.x - msg.angular.z * track / 2.0
        v_right = msg.linear.x + msg.angular.z * track / 2.0
        self.target_left = v_left / radius
        self.target_right = v_right / radius

    def on_wheel_speed(self, msg: Float32MultiArray) -> None:
        if len(msg.data) >= 2:
            self.measured_left = float(msg.data[0])
            self.measured_right = float(msg.data[1])

    def control_step(self) -> None:
        now = self.get_clock().now()
        dt = (now - self.prev_time).nanoseconds * 1e-9
        self.prev_time = now
        left_voltage = self.left_pid.update(self.target_left, self.measured_left, dt)
        right_voltage = self.right_pid.update(self.target_right, self.measured_right, dt)
        msg = Float32MultiArray()
        msg.data = [float(left_voltage), float(right_voltage)]
        self.pub.publish(msg)


def main() -> None:
    rclpy.init()
    node = WheelControllerNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()

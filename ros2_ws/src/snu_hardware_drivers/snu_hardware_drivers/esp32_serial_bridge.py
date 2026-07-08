from __future__ import annotations

from dataclasses import dataclass
from math import cos, isfinite, pi, sin
from time import sleep
from typing import Any

import rclpy
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from sensor_msgs.msg import Imu, JointState
from snu_robot_interfaces.msg import FourWheelCommand


@dataclass(frozen=True)
class WheelConfig:
    field: str
    joint_name: str
    motor_sign: float
    encoder_sign: float


class Esp32SerialBridge(Node):
    """Bridge ROS wheel commands and ESP32 motor/encoder firmware over USB serial."""

    def __init__(self) -> None:
        super().__init__("esp32_serial_bridge")

        self.declare_parameter("dry_run", True)
        self.declare_parameter("serial_port", "/dev/ttyUSB0")
        self.declare_parameter("baud_rate", 115200)
        self.declare_parameter("serial_reset_wait_sec", 2.0)
        self.declare_parameter("esp32_protocol", "motor_bridge")
        self.declare_parameter("esp32_command_mode", "velocity")
        self.declare_parameter("command_topic", "/wheel_commands")
        self.declare_parameter("joint_states_topic", "/joint_states")
        self.declare_parameter("command_timeout_sec", 0.5)
        self.declare_parameter("read_rate_hz", 100.0)
        self.declare_parameter("max_power", 0.12)
        self.declare_parameter("u_shape_pwm_max", 120)
        self.declare_parameter("u_shape_stream_encoders", True)
        self.declare_parameter("publish_imu", True)
        self.declare_parameter("imu_topic", "/imu")
        self.declare_parameter("imu_frame", "base_link")
        self.declare_parameter("imu_yaw_offset_deg", 0.0)
        self.declare_parameter("max_wheel_velocity_rad_s", 20.0)
        self.declare_parameter("encoder_counts_per_revolution", 1.0)

        self.declare_parameter("front_left_joint", "front_left_wheel_joint")
        self.declare_parameter("front_right_joint", "front_right_wheel_joint")
        self.declare_parameter("rear_left_joint", "rear_left_wheel_joint")
        self.declare_parameter("rear_right_joint", "rear_right_wheel_joint")

        self.declare_parameter("front_left_motor_sign", 1.0)
        self.declare_parameter("front_right_motor_sign", 1.0)
        self.declare_parameter("rear_left_motor_sign", 1.0)
        self.declare_parameter("rear_right_motor_sign", 1.0)
        self.declare_parameter("front_left_encoder_sign", 1.0)
        self.declare_parameter("front_right_encoder_sign", 1.0)
        self.declare_parameter("rear_left_encoder_sign", 1.0)
        self.declare_parameter("rear_right_encoder_sign", 1.0)

        self._dry_run = bool(self.get_parameter("dry_run").value)
        self._serial_port = str(self.get_parameter("serial_port").value)
        self._baud_rate = int(self.get_parameter("baud_rate").value)
        self._serial_reset_wait_sec = max(
            0.0,
            float(self.get_parameter("serial_reset_wait_sec").value),
        )
        self._esp32_command_mode = str(
            self.get_parameter("esp32_command_mode").value
        ).lower()
        self._esp32_protocol = str(self.get_parameter("esp32_protocol").value).lower()
        self._command_timeout_sec = float(
            self.get_parameter("command_timeout_sec").value
        )
        self._max_power = _clamp(float(self.get_parameter("max_power").value), 0.0, 1.0)
        self._u_shape_pwm_max = int(
            _clamp(float(self.get_parameter("u_shape_pwm_max").value), 0.0, 255.0)
        )
        self._u_shape_stream_encoders = bool(
            self.get_parameter("u_shape_stream_encoders").value
        )
        self._publish_imu = bool(self.get_parameter("publish_imu").value)
        self._imu_frame = str(self.get_parameter("imu_frame").value)
        self._imu_yaw_offset_rad = (
            float(self.get_parameter("imu_yaw_offset_deg").value) * pi / 180.0
        )
        self._max_wheel_velocity_rad_s = max(
            0.01,
            float(self.get_parameter("max_wheel_velocity_rad_s").value),
        )
        self._counts_per_revolution = max(
            1.0,
            float(self.get_parameter("encoder_counts_per_revolution").value),
        )
        self._wheels = [
            WheelConfig(
                "front_left",
                str(self.get_parameter("front_left_joint").value),
                float(self.get_parameter("front_left_motor_sign").value),
                float(self.get_parameter("front_left_encoder_sign").value),
            ),
            WheelConfig(
                "front_right",
                str(self.get_parameter("front_right_joint").value),
                float(self.get_parameter("front_right_motor_sign").value),
                float(self.get_parameter("front_right_encoder_sign").value),
            ),
            WheelConfig(
                "rear_left",
                str(self.get_parameter("rear_left_joint").value),
                float(self.get_parameter("rear_left_motor_sign").value),
                float(self.get_parameter("rear_left_encoder_sign").value),
            ),
            WheelConfig(
                "rear_right",
                str(self.get_parameter("rear_right_joint").value),
                float(self.get_parameter("rear_right_motor_sign").value),
                float(self.get_parameter("rear_right_encoder_sign").value),
            ),
        ]

        self._serial: Any | None = None
        self._last_command_time = self.get_clock().now()
        self._last_counts: list[int] | None = None
        self._last_joint_counts: list[int] | None = None
        self._last_joint_time = self.get_clock().now()
        self._last_imu_yaw: float | None = None
        self._last_imu_time = self.get_clock().now()
        self._last_dry_run_log_sec = 0.0

        if self._dry_run:
            self.get_logger().warn(
                "ESP32 serial bridge is in dry_run mode; serial port will not be opened"
            )
        else:
            self._serial = _open_serial(
                self._serial_port,
                self._baud_rate,
                self._serial_reset_wait_sec,
            )
            self._configure_firmware_after_open()
            self.get_logger().info(
                f"Opened ESP32 serial port {self._serial_port} at {self._baud_rate} "
                f"using protocol {self._esp32_protocol}"
            )

        self._joint_publisher = self.create_publisher(
            JointState,
            str(self.get_parameter("joint_states_topic").value),
            10,
        )
        self._imu_publisher = (
            self.create_publisher(
                Imu,
                str(self.get_parameter("imu_topic").value),
                10,
            )
            if self._publish_imu
            else None
        )
        self._command_subscription = self.create_subscription(
            FourWheelCommand,
            str(self.get_parameter("command_topic").value),
            self._on_command,
            10,
        )
        read_rate_hz = float(self.get_parameter("read_rate_hz").value)
        self._read_timer = self.create_timer(1.0 / max(1.0, read_rate_hz), self._read)
        self._watchdog_timer = self.create_timer(0.05, self._stop_if_timed_out)

    def _on_command(self, msg: FourWheelCommand) -> None:
        self._last_command_time = self.get_clock().now()
        values = []
        for wheel in self._wheels:
            raw_value = float(getattr(msg, wheel.field))
            normalized = (
                self._normalize(raw_value, msg.command_mode)
                * wheel.motor_sign
            )
            values.append(_clamp(normalized, -self._max_power, self._max_power))
        self._send_wheel_command(self._serial_command_prefix(), values)

    def _normalize(self, value: float, command_mode: int) -> float:
        if not isfinite(value):
            return 0.0
        if command_mode == FourWheelCommand.VELOCITY_RAD_S:
            return _clamp(value / self._max_wheel_velocity_rad_s, -1.0, 1.0)
        if command_mode == FourWheelCommand.NORMALIZED_POWER:
            return _clamp(value, -1.0, 1.0)
        self.get_logger().warn(f"Unknown wheel command mode {command_mode}; stopping")
        return 0.0

    def _serial_command_prefix(self) -> str:
        if self._esp32_command_mode in ("velocity", "closed_loop", "closed_loop_velocity"):
            return "V"
        return "M"

    def _send_wheel_command(self, prefix: str, values: list[float]) -> None:
        if self._esp32_protocol in ("u_shape", "u_shape_pwm", "u_shape_robot"):
            line = self._u_shape_set_command(values)
            if self._dry_run:
                self._log_dry_run(line.strip())
                return
            if self._serial is not None:
                self._serial.write(line.encode("ascii"))
            return

        line = prefix + " " + " ".join(f"{value:.3f}" for value in values) + "\n"
        if self._dry_run:
            self._log_dry_run(line.strip())
            return
        if self._serial is not None:
            self._serial.write(line.encode("ascii"))

    def _u_shape_set_command(self, values: list[float]) -> str:
        scale = self._u_shape_pwm_max / max(self._max_power, 1.0e-6)
        pwm = [
            int(round(_clamp(value * scale, -self._u_shape_pwm_max, self._u_shape_pwm_max)))
            for value in values
        ]
        return "SET " + " ".join(str(value) for value in pwm) + "\n"

    def _configure_firmware_after_open(self) -> None:
        if self._serial is None:
            return
        if self._esp32_protocol not in ("u_shape", "u_shape_pwm", "u_shape_robot"):
            return
        if self._u_shape_stream_encoders:
            self._serial.write(b"ENC ON\n")
        if self._publish_imu:
            self._serial.write(b"IMU ON\n")

    def _log_dry_run(self, line: str) -> None:
        now_sec = self.get_clock().now().nanoseconds * 1.0e-9
        if now_sec - self._last_dry_run_log_sec < 0.5:
            return
        self._last_dry_run_log_sec = now_sec
        self.get_logger().info(f"dry_run serial write: {line}")

    def _read(self) -> None:
        if self._dry_run or self._serial is None:
            return

        while self._serial.in_waiting:
            line = self._serial.readline().decode("ascii", errors="replace").strip()
            if not line:
                continue
            self._handle_line(line)

    def _handle_line(self, line: str) -> None:
        parts = line.split()
        if not parts:
            return
        if parts[0] == "E" and len(parts) == 5:
            try:
                counts = [int(part) for part in parts[1:]]
            except ValueError:
                self.get_logger().warn(f"Invalid encoder line from ESP32: {line}")
                return
            self._publish_joint_states(counts)
        elif parts[0] == "ENC":
            counts = _parse_u_shape_encoder_line(parts)
            if counts is not None:
                self._publish_joint_states(counts)
        elif parts[0] == "IMU":
            self._publish_imu_sample(parts, line)
        elif parts[0] not in ("OK", "READY"):
            self.get_logger().info(f"ESP32: {line}")

    def _publish_imu_sample(self, parts: list[str], line: str) -> None:
        if self._imu_publisher is None:
            return
        if len(parts) < 5:
            self.get_logger().warn(f"Invalid IMU line from ESP32: {line}")
            return

        try:
            yaw = float(parts[2]) + self._imu_yaw_offset_rad
            float(parts[3])
            float(parts[4])
        except ValueError:
            self.get_logger().warn(f"Invalid IMU line from ESP32: {line}")
            return

        now = self.get_clock().now()
        msg = Imu()
        msg.header.stamp = now.to_msg()
        msg.header.frame_id = self._imu_frame

        # The U-shape firmware sends yaw zeroed at startup/ZERO_YAW. Publish a
        # yaw-only orientation so EKF two_d_mode can use heading without needing
        # a separate IMU frame transform.
        half_yaw = 0.5 * _wrap_angle(yaw)
        msg.orientation.x = 0.0
        msg.orientation.y = 0.0
        msg.orientation.z = sin(half_yaw)
        msg.orientation.w = cos(half_yaw)
        msg.orientation_covariance = [
            999.0,
            0.0,
            0.0,
            0.0,
            999.0,
            0.0,
            0.0,
            0.0,
            0.03,
        ]

        if self._last_imu_yaw is not None:
            dt = max(1.0e-6, (now - self._last_imu_time).nanoseconds * 1.0e-9)
            msg.angular_velocity.z = _wrap_angle(yaw - self._last_imu_yaw) / dt
        msg.angular_velocity_covariance = [
            999.0,
            0.0,
            0.0,
            0.0,
            999.0,
            0.0,
            0.0,
            0.0,
            0.05,
        ]
        msg.linear_acceleration_covariance[0] = -1.0

        self._imu_publisher.publish(msg)
        self._last_imu_yaw = yaw
        self._last_imu_time = now

    def _publish_joint_states(self, counts: list[int]) -> None:
        now = self.get_clock().now()
        if self._last_joint_counts is None:
            self._last_joint_counts = counts
            self._last_joint_time = now

        dt = max(1.0e-6, (now - self._last_joint_time).nanoseconds * 1.0e-9)
        msg = JointState()
        msg.header.stamp = now.to_msg()

        for index, wheel in enumerate(self._wheels):
            count = counts[index]
            last_count = self._last_joint_counts[index]
            position = wheel.encoder_sign * count * 2.0 * pi / self._counts_per_revolution
            velocity = (
                wheel.encoder_sign
                * (count - last_count)
                * 2.0
                * pi
                / self._counts_per_revolution
                / dt
            )
            msg.name.append(wheel.joint_name)
            msg.position.append(position)
            msg.velocity.append(velocity)

        self._joint_publisher.publish(msg)
        self._last_joint_counts = counts
        self._last_joint_time = now

    def _stop_if_timed_out(self) -> None:
        age = (self.get_clock().now() - self._last_command_time).nanoseconds * 1.0e-9
        if age > self._command_timeout_sec:
            self._send_wheel_command(self._serial_command_prefix(), [0.0, 0.0, 0.0, 0.0])

    def destroy_node(self) -> bool:
        if self._serial is not None:
            self._send_wheel_command(self._serial_command_prefix(), [0.0, 0.0, 0.0, 0.0])
            self._serial.close()
        return super().destroy_node()


def _open_serial(port: str, baud_rate: int, reset_wait_sec: float) -> Any:
    try:
        import serial
    except ImportError as exc:
        raise RuntimeError(
            "pyserial is not installed. Install python3-serial or run with dry_run:=true."
        ) from exc
    serial_port = serial.Serial(
        port=port,
        baudrate=baud_rate,
        timeout=0.01,
        rtscts=False,
        dsrdtr=False,
    )
    serial_port.setDTR(False)
    serial_port.setRTS(False)
    if reset_wait_sec > 0.0:
        sleep(reset_wait_sec)
    serial_port.reset_input_buffer()
    return serial_port


def _parse_u_shape_encoder_line(parts: list[str]) -> list[int] | None:
    values: dict[str, int] = {}
    for part in parts[1:]:
        if "=" not in part:
            continue
        name, value = part.split("=", 1)
        try:
            values[name.upper()] = int(value)
        except ValueError:
            return None

    required = ("FL", "FR", "BL", "BR")
    if not all(name in values for name in required):
        return None
    return [values[name] for name in required]


def _clamp(value: float, low: float, high: float) -> float:
    return min(high, max(low, value))


def _wrap_angle(angle: float) -> float:
    while angle > pi:
        angle -= 2.0 * pi
    while angle < -pi:
        angle += 2.0 * pi
    return angle


def main() -> None:
    rclpy.init()
    node = Esp32SerialBridge()
    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == "__main__":
    main()

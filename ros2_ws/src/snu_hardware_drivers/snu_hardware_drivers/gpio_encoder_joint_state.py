from __future__ import annotations

from dataclasses import dataclass
from math import pi
from typing import Any

import rclpy
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from sensor_msgs.msg import JointState

from snu_hardware_drivers.gpio_four_wheel_driver import RESERVED_BOARD_PINS
from snu_hardware_drivers.gpio_four_wheel_driver import _load_jetson_gpio
from snu_hardware_drivers.gpio_four_wheel_driver import _set_gpio_mode


TRANSITIONS = {
    (0b00, 0b01): 1,
    (0b01, 0b11): 1,
    (0b11, 0b10): 1,
    (0b10, 0b00): 1,
    (0b00, 0b10): -1,
    (0b10, 0b11): -1,
    (0b11, 0b01): -1,
    (0b01, 0b00): -1,
}


@dataclass(frozen=True)
class EncoderPins:
    name: str
    joint_name: str
    pin_a: int
    pin_b: int
    sign: float


class GpioEncoderJointState(Node):
    """Poll quadrature encoders and publish wheel joint states."""

    def __init__(self) -> None:
        super().__init__("gpio_encoder_joint_state")

        self.declare_parameter("dry_run", True)
        self.declare_parameter("pin_numbering", "BCM")
        self.declare_parameter("allow_reserved_board_pins", False)
        self.declare_parameter("joint_states_topic", "/joint_states")
        self.declare_parameter("publish_rate_hz", 20.0)
        self.declare_parameter("poll_rate_hz", 500.0)
        self.declare_parameter("encoder_counts_per_revolution", 1.0)

        self.declare_parameter("front_left_joint", "front_left_wheel_joint")
        self.declare_parameter("front_right_joint", "front_right_wheel_joint")
        self.declare_parameter("rear_left_joint", "rear_left_wheel_joint")
        self.declare_parameter("rear_right_joint", "rear_right_wheel_joint")

        self.declare_parameter("front_left_encoder_a_pin", 18)
        self.declare_parameter("front_left_encoder_b_pin", 19)
        self.declare_parameter("front_right_encoder_a_pin", 16)
        self.declare_parameter("front_right_encoder_b_pin", 17)
        self.declare_parameter("rear_left_encoder_a_pin", 32)
        self.declare_parameter("rear_left_encoder_b_pin", 33)
        self.declare_parameter("rear_right_encoder_a_pin", 26)
        self.declare_parameter("rear_right_encoder_b_pin", 27)

        self.declare_parameter("front_left_sign", 1.0)
        self.declare_parameter("front_right_sign", 1.0)
        self.declare_parameter("rear_left_sign", 1.0)
        self.declare_parameter("rear_right_sign", 1.0)

        self._dry_run = bool(self.get_parameter("dry_run").value)
        self._pin_numbering = str(self.get_parameter("pin_numbering").value).upper()
        self._counts_per_revolution = max(
            1.0,
            float(self.get_parameter("encoder_counts_per_revolution").value),
        )
        self._encoders = [
            EncoderPins(
                "front_left",
                str(self.get_parameter("front_left_joint").value),
                int(self.get_parameter("front_left_encoder_a_pin").value),
                int(self.get_parameter("front_left_encoder_b_pin").value),
                float(self.get_parameter("front_left_sign").value),
            ),
            EncoderPins(
                "front_right",
                str(self.get_parameter("front_right_joint").value),
                int(self.get_parameter("front_right_encoder_a_pin").value),
                int(self.get_parameter("front_right_encoder_b_pin").value),
                float(self.get_parameter("front_right_sign").value),
            ),
            EncoderPins(
                "rear_left",
                str(self.get_parameter("rear_left_joint").value),
                int(self.get_parameter("rear_left_encoder_a_pin").value),
                int(self.get_parameter("rear_left_encoder_b_pin").value),
                float(self.get_parameter("rear_left_sign").value),
            ),
            EncoderPins(
                "rear_right",
                str(self.get_parameter("rear_right_joint").value),
                int(self.get_parameter("rear_right_encoder_a_pin").value),
                int(self.get_parameter("rear_right_encoder_b_pin").value),
                float(self.get_parameter("rear_right_sign").value),
            ),
        ]

        self._validate_pin_settings()
        self._gpio: Any | None = None
        self._counts = {encoder.name: 0 for encoder in self._encoders}
        self._last_states = {encoder.name: 0 for encoder in self._encoders}
        self._last_publish_counts = dict(self._counts)
        self._last_publish_time = self.get_clock().now()

        if self._dry_run:
            self.get_logger().warn(
                "GPIO encoder reader is in dry_run mode; publishing zero joint states"
            )
        else:
            self._setup_gpio()

        self._publisher = self.create_publisher(
            JointState,
            str(self.get_parameter("joint_states_topic").value),
            10,
        )
        poll_rate_hz = float(self.get_parameter("poll_rate_hz").value)
        publish_rate_hz = float(self.get_parameter("publish_rate_hz").value)
        self._poll_timer = self.create_timer(1.0 / max(1.0, poll_rate_hz), self._poll)
        self._publish_timer = self.create_timer(
            1.0 / max(1.0, publish_rate_hz),
            self._publish_joint_states,
        )
        self.get_logger().info(
            f"GPIO encoder joint state publisher ready, numbering={self._pin_numbering}"
        )

    def _validate_pin_settings(self) -> None:
        if self._pin_numbering != "BOARD":
            return
        if bool(self.get_parameter("allow_reserved_board_pins").value):
            return

        pins = {pin for enc in self._encoders for pin in (enc.pin_a, enc.pin_b)}
        reserved = sorted(pins.intersection(RESERVED_BOARD_PINS))
        if reserved:
            raise RuntimeError(
                "Refusing BOARD mode because encoder pins include reserved 40-pin "
                f"header power/ground pins: {reserved}. If your numbers are GPIO/BCM "
                "numbers, set pin_numbering:=BCM."
            )

    def _setup_gpio(self) -> None:
        gpio = _load_jetson_gpio()
        _set_gpio_mode(gpio, self._pin_numbering)
        gpio.setwarnings(False)

        for encoder in self._encoders:
            gpio.setup(encoder.pin_a, gpio.IN)
            gpio.setup(encoder.pin_b, gpio.IN)
            self._last_states[encoder.name] = self._read_state(encoder, gpio)

        self._gpio = gpio

    def _poll(self) -> None:
        if self._dry_run or self._gpio is None:
            return

        for encoder in self._encoders:
            previous = self._last_states[encoder.name]
            current = self._read_state(encoder, self._gpio)
            if current != previous:
                self._counts[encoder.name] += TRANSITIONS.get((previous, current), 0)
                self._last_states[encoder.name] = current

    def _read_state(self, encoder: EncoderPins, gpio: Any) -> int:
        a_state = 1 if gpio.input(encoder.pin_a) else 0
        b_state = 1 if gpio.input(encoder.pin_b) else 0
        return (a_state << 1) | b_state

    def _publish_joint_states(self) -> None:
        now = self.get_clock().now()
        dt = max(1.0e-6, (now - self._last_publish_time).nanoseconds * 1.0e-9)

        msg = JointState()
        msg.header.stamp = now.to_msg()
        for encoder in self._encoders:
            count = self._counts[encoder.name]
            previous_count = self._last_publish_counts[encoder.name]
            position = encoder.sign * count * 2.0 * pi / self._counts_per_revolution
            velocity = (
                encoder.sign
                * (count - previous_count)
                * 2.0
                * pi
                / self._counts_per_revolution
                / dt
            )
            msg.name.append(encoder.joint_name)
            msg.position.append(position)
            msg.velocity.append(velocity)

        self._publisher.publish(msg)
        self._last_publish_counts = dict(self._counts)
        self._last_publish_time = now

    def destroy_node(self) -> bool:
        if not self._dry_run and self._gpio is not None:
            self._gpio.cleanup()
        return super().destroy_node()


def main() -> None:
    rclpy.init()
    node = GpioEncoderJointState()
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

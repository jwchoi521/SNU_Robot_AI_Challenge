from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from typing import Any

import rclpy
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from snu_robot_interfaces.msg import FourWheelCommand


RESERVED_BOARD_PINS = {1, 2, 4, 6, 9, 14, 17, 20, 25, 30, 34, 39}


@dataclass(frozen=True)
class WheelPins:
    name: str
    pin_a: int
    pin_b: int
    sign: float


class GpioFourWheelDriver(Node):
    """Convert FourWheelCommand into two-pin H-bridge PWM outputs on Jetson."""

    def __init__(self) -> None:
        super().__init__("gpio_four_wheel_driver")

        self.declare_parameter("dry_run", True)
        self.declare_parameter("pin_numbering", "BCM")
        self.declare_parameter("allow_reserved_board_pins", False)
        self.declare_parameter("command_topic", "/wheel_commands")
        self.declare_parameter("command_timeout_sec", 0.5)
        self.declare_parameter("pwm_frequency_hz", 1000.0)
        self.declare_parameter("max_duty_cycle", 0.12)
        self.declare_parameter("max_wheel_velocity_rad_s", 20.0)

        self.declare_parameter("front_left_pin_a", 23)
        self.declare_parameter("front_left_pin_b", 25)
        self.declare_parameter("front_right_pin_a", 4)
        self.declare_parameter("front_right_pin_b", 5)
        self.declare_parameter("rear_left_pin_a", 2)
        self.declare_parameter("rear_left_pin_b", 15)
        self.declare_parameter("rear_right_pin_a", 14)
        self.declare_parameter("rear_right_pin_b", 13)

        self.declare_parameter("front_left_sign", 1.0)
        self.declare_parameter("front_right_sign", 1.0)
        self.declare_parameter("rear_left_sign", 1.0)
        self.declare_parameter("rear_right_sign", 1.0)

        self._dry_run = bool(self.get_parameter("dry_run").value)
        self._pin_numbering = str(self.get_parameter("pin_numbering").value).upper()
        self._command_timeout_sec = float(
            self.get_parameter("command_timeout_sec").value
        )
        self._pwm_frequency_hz = float(self.get_parameter("pwm_frequency_hz").value)
        self._max_duty_cycle = _clamp(
            float(self.get_parameter("max_duty_cycle").value),
            0.0,
            1.0,
        )
        self._max_wheel_velocity_rad_s = max(
            0.01,
            float(self.get_parameter("max_wheel_velocity_rad_s").value),
        )
        self._wheels = [
            WheelPins(
                "front_left",
                int(self.get_parameter("front_left_pin_a").value),
                int(self.get_parameter("front_left_pin_b").value),
                float(self.get_parameter("front_left_sign").value),
            ),
            WheelPins(
                "front_right",
                int(self.get_parameter("front_right_pin_a").value),
                int(self.get_parameter("front_right_pin_b").value),
                float(self.get_parameter("front_right_sign").value),
            ),
            WheelPins(
                "rear_left",
                int(self.get_parameter("rear_left_pin_a").value),
                int(self.get_parameter("rear_left_pin_b").value),
                float(self.get_parameter("rear_left_sign").value),
            ),
            WheelPins(
                "rear_right",
                int(self.get_parameter("rear_right_pin_a").value),
                int(self.get_parameter("rear_right_pin_b").value),
                float(self.get_parameter("rear_right_sign").value),
            ),
        ]

        self._validate_pin_settings()
        self._gpio: Any | None = None
        self._pwm: dict[tuple[str, str], Any] = {}
        self._last_command_time = self.get_clock().now()
        self._last_dry_run_log_sec = 0.0

        if self._dry_run:
            self.get_logger().warn(
                "GPIO motor driver is in dry_run mode; no Jetson pins will be driven"
            )
        else:
            self._setup_gpio()

        self._subscription = self.create_subscription(
            FourWheelCommand,
            str(self.get_parameter("command_topic").value),
            self._on_command,
            10,
        )
        self._watchdog = self.create_timer(0.05, self._stop_if_timed_out)
        self.get_logger().info(
            f"GPIO four-wheel driver ready, numbering={self._pin_numbering}, "
            f"max_duty={self._max_duty_cycle:.2f}"
        )

    def _validate_pin_settings(self) -> None:
        if self._pin_numbering != "BOARD":
            return
        if bool(self.get_parameter("allow_reserved_board_pins").value):
            return

        pins = {pin for wheel in self._wheels for pin in (wheel.pin_a, wheel.pin_b)}
        reserved = sorted(pins.intersection(RESERVED_BOARD_PINS))
        if reserved:
            raise RuntimeError(
                "Refusing BOARD mode because motor pins include reserved 40-pin header "
                f"power/ground pins: {reserved}. If your numbers are GPIO/BCM numbers, "
                "set pin_numbering:=BCM."
            )

    def _setup_gpio(self) -> None:
        gpio = _load_jetson_gpio()
        _set_gpio_mode(gpio, self._pin_numbering)
        gpio.setwarnings(False)

        for wheel in self._wheels:
            for side, pin in (("a", wheel.pin_a), ("b", wheel.pin_b)):
                gpio.setup(pin, gpio.OUT, initial=gpio.LOW)
                pwm = gpio.PWM(pin, self._pwm_frequency_hz)
                pwm.start(0.0)
                self._pwm[(wheel.name, side)] = pwm

        self._gpio = gpio

    def _on_command(self, msg: FourWheelCommand) -> None:
        self._last_command_time = self.get_clock().now()
        values = {
            "front_left": float(msg.front_left),
            "front_right": float(msg.front_right),
            "rear_left": float(msg.rear_left),
            "rear_right": float(msg.rear_right),
        }
        normalized = {
            wheel.name: self._normalize(values[wheel.name], msg.command_mode) * wheel.sign
            for wheel in self._wheels
        }
        self._apply_outputs(normalized)

    def _normalize(self, value: float, command_mode: int) -> float:
        if not isfinite(value):
            return 0.0
        if command_mode == FourWheelCommand.VELOCITY_RAD_S:
            return _clamp(value / self._max_wheel_velocity_rad_s, -1.0, 1.0)
        if command_mode == FourWheelCommand.NORMALIZED_POWER:
            return _clamp(value, -1.0, 1.0)

        self.get_logger().warn(f"Unknown wheel command mode {command_mode}; stopping")
        return 0.0

    def _apply_outputs(self, normalized: dict[str, float]) -> None:
        if self._dry_run:
            self._log_dry_run(normalized)
            return

        for wheel in self._wheels:
            value = _clamp(normalized[wheel.name], -1.0, 1.0)
            duty = abs(value) * self._max_duty_cycle * 100.0
            pwm_a = self._pwm[(wheel.name, "a")]
            pwm_b = self._pwm[(wheel.name, "b")]
            if value >= 0.0:
                pwm_a.ChangeDutyCycle(duty)
                pwm_b.ChangeDutyCycle(0.0)
            else:
                pwm_a.ChangeDutyCycle(0.0)
                pwm_b.ChangeDutyCycle(duty)

    def _log_dry_run(self, normalized: dict[str, float]) -> None:
        now_sec = self.get_clock().now().nanoseconds * 1.0e-9
        if now_sec - self._last_dry_run_log_sec < 0.5:
            return
        self._last_dry_run_log_sec = now_sec
        values = ", ".join(
            f"{wheel}={value:+.2f}" for wheel, value in sorted(normalized.items())
        )
        self.get_logger().info(f"dry_run wheel output: {values}")

    def _stop_if_timed_out(self) -> None:
        age = (self.get_clock().now() - self._last_command_time).nanoseconds * 1.0e-9
        if age > self._command_timeout_sec:
            self._apply_outputs({wheel.name: 0.0 for wheel in self._wheels})

    def destroy_node(self) -> bool:
        self._shutdown_gpio()
        return super().destroy_node()

    def _shutdown_gpio(self) -> None:
        if self._dry_run or self._gpio is None:
            return
        for pwm in self._pwm.values():
            pwm.ChangeDutyCycle(0.0)
            pwm.stop()
        self._gpio.cleanup()


def _load_jetson_gpio() -> Any:
    try:
        import Jetson.GPIO as gpio
    except ImportError as exc:
        raise RuntimeError(
            "Jetson.GPIO is not installed. Install it on Jetson or run with dry_run:=true."
        ) from exc
    return gpio


def _set_gpio_mode(gpio: Any, mode: str) -> None:
    if not hasattr(gpio, mode):
        raise RuntimeError(f"Unsupported Jetson.GPIO pin_numbering mode: {mode}")
    gpio.setmode(getattr(gpio, mode))


def _clamp(value: float, low: float, high: float) -> float:
    return min(high, max(low, value))


def main() -> None:
    rclpy.init()
    node = GpioFourWheelDriver()
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

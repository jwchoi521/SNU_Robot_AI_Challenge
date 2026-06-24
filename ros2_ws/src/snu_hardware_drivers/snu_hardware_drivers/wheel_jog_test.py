from __future__ import annotations

from dataclasses import dataclass

import rclpy
from rclpy.node import Node
from snu_robot_interfaces.msg import FourWheelCommand


WHEEL_FIELDS = ("front_left", "front_right", "rear_left", "rear_right")


@dataclass(frozen=True)
class Step:
    wheel: str | None
    power: float
    duration_sec: float
    label: str


class WheelJogTest(Node):
    """Publish a low-power one-wheel-at-a-time test sequence."""

    def __init__(self) -> None:
        super().__init__("wheel_jog_test")

        self.declare_parameter("wheel_command_topic", "/wheel_commands")
        self.declare_parameter("power", 0.10)
        self.declare_parameter("run_sec", 0.40)
        self.declare_parameter("pause_sec", 0.80)
        self.declare_parameter("include_reverse", False)
        self.declare_parameter("repeat", False)
        self.declare_parameter(
            "wheel_order",
            ["front_left", "front_right", "rear_left", "rear_right"],
        )

        self._power = abs(float(self.get_parameter("power").value))
        self._run_sec = float(self.get_parameter("run_sec").value)
        self._pause_sec = float(self.get_parameter("pause_sec").value)
        self._repeat = bool(self.get_parameter("repeat").value)
        self._steps = self._build_steps()
        self._step_index = 0
        self._step_start_time = self.get_clock().now()
        self.done = False

        self._publisher = self.create_publisher(
            FourWheelCommand,
            str(self.get_parameter("wheel_command_topic").value),
            10,
        )
        self._timer = self.create_timer(0.05, self._tick)
        self.get_logger().warn(
            f"Starting wheel jog test with power={self._power:.2f}. Keep robot lifted."
        )

    def _build_steps(self) -> list[Step]:
        steps = [Step(None, 0.0, self._pause_sec, "initial_stop")]
        wheel_order = [
            str(wheel)
            for wheel in self.get_parameter("wheel_order").value
            if str(wheel) in WHEEL_FIELDS
        ]
        include_reverse = bool(self.get_parameter("include_reverse").value)

        for wheel in wheel_order:
            steps.append(Step(wheel, self._power, self._run_sec, f"{wheel}_forward"))
            steps.append(Step(None, 0.0, self._pause_sec, "stop"))
            if include_reverse:
                steps.append(
                    Step(wheel, -self._power, self._run_sec, f"{wheel}_reverse")
                )
                steps.append(Step(None, 0.0, self._pause_sec, "stop"))

        steps.append(Step(None, 0.0, self._pause_sec, "final_stop"))
        return steps

    def _tick(self) -> None:
        if self.done:
            return

        now = self.get_clock().now()
        step = self._steps[self._step_index]
        elapsed = (now - self._step_start_time).nanoseconds * 1.0e-9
        if elapsed >= step.duration_sec:
            self._advance_step(now)
            step = self._steps[self._step_index]

        self._publish_step(step)

    def _advance_step(self, now) -> None:
        self._step_index += 1
        self._step_start_time = now
        if self._step_index >= len(self._steps):
            if self._repeat:
                self._step_index = 0
                self.get_logger().info("Repeating wheel jog test")
            else:
                self._publish_stop()
                self.done = True
                self.get_logger().info("Wheel jog test complete")
                return

        self.get_logger().info(f"Jog step: {self._steps[self._step_index].label}")

    def _publish_step(self, step: Step) -> None:
        msg = _stop_command(self.get_clock().now().to_msg())
        if step.wheel is not None:
            setattr(msg, step.wheel, float(step.power))
        self._publisher.publish(msg)

    def _publish_stop(self) -> None:
        self._publisher.publish(_stop_command(self.get_clock().now().to_msg()))


def _stop_command(stamp) -> FourWheelCommand:
    msg = FourWheelCommand()
    msg.header.stamp = stamp
    msg.command_mode = FourWheelCommand.NORMALIZED_POWER
    msg.front_left = 0.0
    msg.front_right = 0.0
    msg.rear_left = 0.0
    msg.rear_right = 0.0
    return msg


def main() -> None:
    rclpy.init()
    node = WheelJogTest()
    try:
        while rclpy.ok() and not node.done:
            rclpy.spin_once(node, timeout_sec=0.1)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()

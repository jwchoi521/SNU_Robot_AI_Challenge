from __future__ import annotations

import csv
import math
import os
import random
import time
from dataclasses import dataclass
from pathlib import Path

import rclpy
from geometry_msgs.msg import Twist
from rcl_interfaces.msg import Log
from rclpy.node import Node
from sensor_msgs.msg import Imu, JointState
from snu_robot_interfaces.msg import FourWheelCommand


@dataclass(frozen=True)
class Trial:
    trial_id: int
    repeat_index: int
    linear_x: float
    yaw_cmd: float


class YawCalibrationCollector(Node):
    """Drive a command grid and record IMU yaw-rate response to CSV."""

    def __init__(self) -> None:
        super().__init__("yaw_calibration_collector")

        self.declare_parameter("cmd_vel_topic", "/cmd_vel")
        self.declare_parameter("imu_topic", "/imu")
        self.declare_parameter("joint_states_topic", "/joint_states")
        self.declare_parameter("wheel_command_topic", "/wheel_commands")
        self.declare_parameter("rosout_topic", "/rosout")
        self.declare_parameter("output_csv", "")
        self.declare_parameter("enable_motion", False)
        self.declare_parameter("linear_x_values", [0.0, 0.04, 0.08, 0.12, 0.15])
        self.declare_parameter(
            "yaw_cmd_values",
            [
                -4.0,
                -3.5,
                -3.0,
                -2.5,
                -2.0,
                -1.5,
                -1.0,
                -0.6,
                -0.3,
                0.3,
                0.6,
                1.0,
                1.5,
                2.0,
                2.5,
                3.0,
                3.5,
                4.0,
            ],
        )
        self.declare_parameter("repeat_count", 1)
        self.declare_parameter("randomize_trials", False)
        self.declare_parameter("start_delay_sec", 3.0)
        self.declare_parameter("stop_sec", 0.75)
        self.declare_parameter("settle_sec", 0.5)
        self.declare_parameter("sample_sec", 1.5)
        self.declare_parameter("sample_rate_hz", 30.0)
        self.declare_parameter("max_abs_linear_x", 0.20)
        self.declare_parameter("max_abs_yaw_cmd", 4.0)
        self.declare_parameter("pwm_saturation_threshold", 245.0)
        self.declare_parameter("pwm_warning_period_sec", 1.0)

        self._enable_motion = bool(self.get_parameter("enable_motion").value)
        self._start_delay_sec = max(0.0, float(self.get_parameter("start_delay_sec").value))
        self._stop_sec = max(0.0, float(self.get_parameter("stop_sec").value))
        self._settle_sec = max(0.0, float(self.get_parameter("settle_sec").value))
        self._sample_sec = max(0.1, float(self.get_parameter("sample_sec").value))
        self._sample_period_sec = 1.0 / max(1.0, float(self.get_parameter("sample_rate_hz").value))
        self._max_abs_linear_x = max(0.0, float(self.get_parameter("max_abs_linear_x").value))
        self._max_abs_yaw_cmd = max(0.0, float(self.get_parameter("max_abs_yaw_cmd").value))
        self._pwm_saturation_threshold = max(
            0.0, float(self.get_parameter("pwm_saturation_threshold").value)
        )
        self._pwm_warning_period_sec = max(
            0.1, float(self.get_parameter("pwm_warning_period_sec").value)
        )

        linear_values = [
            self._clamp(float(value), -self._max_abs_linear_x, self._max_abs_linear_x)
            for value in self.get_parameter("linear_x_values").value
        ]
        yaw_values = [
            self._clamp(float(value), -self._max_abs_yaw_cmd, self._max_abs_yaw_cmd)
            for value in self.get_parameter("yaw_cmd_values").value
            if abs(float(value)) > 1.0e-6
        ]
        repeat_count = max(1, int(self.get_parameter("repeat_count").value))
        self._trials = self._build_trials(linear_values, yaw_values, repeat_count)
        if bool(self.get_parameter("randomize_trials").value):
            random.shuffle(self._trials)

        self._cmd_pub = self.create_publisher(
            Twist, str(self.get_parameter("cmd_vel_topic").value), 10
        )
        self.create_subscription(
            Imu, str(self.get_parameter("imu_topic").value), self._on_imu, 50
        )
        self.create_subscription(
            JointState,
            str(self.get_parameter("joint_states_topic").value),
            self._on_joint_states,
            50,
        )
        self.create_subscription(
            FourWheelCommand,
            str(self.get_parameter("wheel_command_topic").value),
            self._on_wheel_command,
            50,
        )
        self.create_subscription(
            Log,
            str(self.get_parameter("rosout_topic").value),
            self._on_rosout,
            50,
        )

        self._latest_imu_wz: float | None = None
        self._latest_imu_stamp_sec: float | None = None
        self._joint_velocities: dict[str, float] = {}
        self._latest_joint_stamp_sec: float | None = None
        self._wheel_command: FourWheelCommand | None = None
        self._latest_wheel_command_stamp_sec: float | None = None
        self._esp32_debug: dict[str, float] = {}
        self._latest_esp32_debug_stamp_sec: float | None = None
        self._last_pwm_warning_sec = 0.0

        self._start_time = time.monotonic()
        self._active_trial_index = -1
        self._done = False
        self._last_log_sec = 0.0
        self._csv_file = self._open_output_csv()
        self._writer = csv.DictWriter(self._csv_file, fieldnames=self._fieldnames())
        self._writer.writeheader()
        self._csv_file.flush()

        self.get_logger().info(
            f"Yaw calibration plan: {len(self._trials)} trials, "
            f"settle={self._settle_sec:.2f}s sample={self._sample_sec:.2f}s "
            f"stop={self._stop_sec:.2f}s output={self._csv_file.name}"
        )
        if not self._enable_motion:
            self.get_logger().warn(
                "enable_motion is false; publishing zero cmd_vel only. "
                "Rerun with -p enable_motion:=true to collect moving data."
            )

        self._timer = self.create_timer(self._sample_period_sec, self._tick)

    def _build_trials(
        self, linear_values: list[float], yaw_values: list[float], repeat_count: int
    ) -> list[Trial]:
        trials: list[Trial] = []
        trial_id = 0
        for repeat_index in range(repeat_count):
            for linear_x in linear_values:
                for yaw_cmd in yaw_values:
                    trials.append(
                        Trial(
                            trial_id=trial_id,
                            repeat_index=repeat_index,
                            linear_x=linear_x,
                            yaw_cmd=yaw_cmd,
                        )
                    )
                    trial_id += 1
        return trials

    def _open_output_csv(self):
        configured = str(self.get_parameter("output_csv").value).strip()
        if configured:
            path = Path(os.path.expanduser(configured))
        else:
            stamp = time.strftime("%Y%m%d_%H%M%S")
            path = Path.home() / "yaw_calibration" / f"yaw_calibration_{stamp}.csv"
        path.parent.mkdir(parents=True, exist_ok=True)
        return path.open("w", newline="", encoding="utf-8")

    def _fieldnames(self) -> list[str]:
        return [
            "wall_time_sec",
            "ros_time_sec",
            "trial_id",
            "repeat_index",
            "phase",
            "phase_elapsed_sec",
            "valid_sample",
            "linear_x",
            "yaw_cmd",
            "imu_wz",
            "imu_age_sec",
            "wheel_cmd_fl",
            "wheel_cmd_fr",
            "wheel_cmd_rl",
            "wheel_cmd_rr",
            "wheel_cmd_age_sec",
            "pwm_fl",
            "pwm_fr",
            "pwm_bl",
            "pwm_br",
            "pwm_saturated",
            "esp32_debug_age_sec",
            "esp32_target_wz",
            "esp32_imu_wz",
            "esp32_yaw_err",
            "esp32_yaw_corr",
            "esp32_yaw_corr_cps",
            "joint_fl_rad_s",
            "joint_fr_rad_s",
            "joint_rl_rad_s",
            "joint_rr_rad_s",
            "joint_age_sec",
        ]

    def _on_imu(self, msg: Imu) -> None:
        self._latest_imu_wz = float(msg.angular_velocity.z)
        self._latest_imu_stamp_sec = self._stamp_to_sec(msg.header.stamp)

    def _on_joint_states(self, msg: JointState) -> None:
        self._joint_velocities = {
            str(name): float(velocity)
            for name, velocity in zip(msg.name, msg.velocity)
            if math.isfinite(float(velocity))
        }
        self._latest_joint_stamp_sec = self._stamp_to_sec(msg.header.stamp)

    def _on_wheel_command(self, msg: FourWheelCommand) -> None:
        self._wheel_command = msg
        self._latest_wheel_command_stamp_sec = self._stamp_to_sec(msg.header.stamp)

    def _on_rosout(self, msg: Log) -> None:
        if "SET1_DBG" not in msg.msg:
            return
        parsed = self._parse_set1_debug(msg.msg)
        if not parsed:
            return
        self._esp32_debug = parsed
        self._latest_esp32_debug_stamp_sec = self._stamp_to_sec(msg.stamp)
        if self._is_pwm_saturated(parsed):
            self._warn_pwm_saturation(parsed)

    def _parse_set1_debug(self, text: str) -> dict[str, float]:
        parsed: dict[str, float] = {}
        for token in text.replace("ESP32:", "").split():
            if "=" not in token:
                continue
            key, value = token.split("=", 1)
            try:
                parsed[key] = float(value)
            except ValueError:
                continue
        return parsed

    def _is_pwm_saturated(self, parsed: dict[str, float]) -> bool:
        return any(
            abs(parsed.get(key, 0.0)) >= self._pwm_saturation_threshold
            for key in ("pwmFL", "pwmFR", "pwmBL", "pwmBR")
        )

    def _warn_pwm_saturation(self, parsed: dict[str, float]) -> None:
        now_sec = self.get_clock().now().nanoseconds * 1.0e-9
        if now_sec - self._last_pwm_warning_sec < self._pwm_warning_period_sec:
            return
        self._last_pwm_warning_sec = now_sec
        self.get_logger().warn(
            "PWM saturation near limit: "
            f"FL={parsed.get('pwmFL', 0.0):+.0f} "
            f"FR={parsed.get('pwmFR', 0.0):+.0f} "
            f"BL={parsed.get('pwmBL', 0.0):+.0f} "
            f"BR={parsed.get('pwmBR', 0.0):+.0f}; "
            f"target_wz={parsed.get('target_wz', 0.0):+.3f} "
            f"imu_wz={parsed.get('imu_wz', 0.0):+.3f}"
        )

    def _tick(self) -> None:
        now = time.monotonic()
        elapsed = now - self._start_time
        if elapsed < self._start_delay_sec:
            self._publish_cmd(0.0, 0.0)
            self._log_waiting(now, self._start_delay_sec - elapsed)
            return

        if not self._enable_motion:
            self._publish_cmd(0.0, 0.0)
            return

        trial_duration = self._stop_sec + self._settle_sec + self._sample_sec
        total_elapsed = elapsed - self._start_delay_sec
        trial_index = int(total_elapsed // trial_duration) if trial_duration > 0.0 else 0
        if trial_index >= len(self._trials):
            self._finish()
            return

        phase_elapsed_total = total_elapsed - trial_index * trial_duration
        trial = self._trials[trial_index]
        phase = "stop"
        phase_elapsed = phase_elapsed_total
        valid_sample = False
        linear_x = 0.0
        yaw_cmd = 0.0

        if phase_elapsed_total >= self._stop_sec:
            command_elapsed = phase_elapsed_total - self._stop_sec
            phase = "settle" if command_elapsed < self._settle_sec else "sample"
            phase_elapsed = command_elapsed if phase == "settle" else command_elapsed - self._settle_sec
            linear_x = trial.linear_x
            yaw_cmd = trial.yaw_cmd
            valid_sample = phase == "sample"

        if trial_index != self._active_trial_index:
            self._active_trial_index = trial_index
            self.get_logger().info(
                f"trial {trial_index + 1}/{len(self._trials)}: "
                f"v={trial.linear_x:.3f} yaw_cmd={trial.yaw_cmd:.3f}"
            )

        self._publish_cmd(linear_x, yaw_cmd)
        self._write_row(trial, phase, phase_elapsed, valid_sample, linear_x, yaw_cmd)

    def _publish_cmd(self, linear_x: float, yaw_cmd: float) -> None:
        msg = Twist()
        msg.linear.x = float(linear_x)
        msg.angular.z = float(yaw_cmd)
        self._cmd_pub.publish(msg)

    def _write_row(
        self,
        trial: Trial,
        phase: str,
        phase_elapsed: float,
        valid_sample: bool,
        linear_x: float,
        yaw_cmd: float,
    ) -> None:
        now_msg = self.get_clock().now()
        ros_time_sec = now_msg.nanoseconds * 1.0e-9
        imu_age = self._age_sec(ros_time_sec, self._latest_imu_stamp_sec)
        joint_age = self._age_sec(ros_time_sec, self._latest_joint_stamp_sec)
        wheel_age = self._age_sec(ros_time_sec, self._latest_wheel_command_stamp_sec)
        esp32_debug_age = self._age_sec(ros_time_sec, self._latest_esp32_debug_stamp_sec)
        pwm_saturated = self._is_pwm_saturated(self._esp32_debug)

        wheel = self._wheel_command
        row = {
            "wall_time_sec": f"{time.time():.6f}",
            "ros_time_sec": f"{ros_time_sec:.6f}",
            "trial_id": trial.trial_id,
            "repeat_index": trial.repeat_index,
            "phase": phase,
            "phase_elapsed_sec": f"{phase_elapsed:.4f}",
            "valid_sample": int(valid_sample),
            "linear_x": f"{linear_x:.6f}",
            "yaw_cmd": f"{yaw_cmd:.6f}",
            "imu_wz": self._format_optional(self._latest_imu_wz),
            "imu_age_sec": self._format_optional(imu_age),
            "wheel_cmd_fl": self._format_optional(wheel.front_left if wheel else None),
            "wheel_cmd_fr": self._format_optional(wheel.front_right if wheel else None),
            "wheel_cmd_rl": self._format_optional(wheel.rear_left if wheel else None),
            "wheel_cmd_rr": self._format_optional(wheel.rear_right if wheel else None),
            "wheel_cmd_age_sec": self._format_optional(wheel_age),
            "pwm_fl": self._format_optional(self._esp32_debug.get("pwmFL")),
            "pwm_fr": self._format_optional(self._esp32_debug.get("pwmFR")),
            "pwm_bl": self._format_optional(self._esp32_debug.get("pwmBL")),
            "pwm_br": self._format_optional(self._esp32_debug.get("pwmBR")),
            "pwm_saturated": int(pwm_saturated),
            "esp32_debug_age_sec": self._format_optional(esp32_debug_age),
            "esp32_target_wz": self._format_optional(self._esp32_debug.get("target_wz")),
            "esp32_imu_wz": self._format_optional(self._esp32_debug.get("imu_wz")),
            "esp32_yaw_err": self._format_optional(self._esp32_debug.get("yaw_err")),
            "esp32_yaw_corr": self._format_optional(self._esp32_debug.get("yaw_corr")),
            "esp32_yaw_corr_cps": self._format_optional(self._esp32_debug.get("yaw_corr_cps")),
            "joint_fl_rad_s": self._format_optional(
                self._joint_velocities.get("front_left_wheel_joint")
            ),
            "joint_fr_rad_s": self._format_optional(
                self._joint_velocities.get("front_right_wheel_joint")
            ),
            "joint_rl_rad_s": self._format_optional(
                self._joint_velocities.get("rear_left_wheel_joint")
            ),
            "joint_rr_rad_s": self._format_optional(
                self._joint_velocities.get("rear_right_wheel_joint")
            ),
            "joint_age_sec": self._format_optional(joint_age),
        }
        self._writer.writerow(row)
        self._csv_file.flush()

    def _finish(self) -> None:
        if self._done:
            self._publish_cmd(0.0, 0.0)
            return
        self._done = True
        for _ in range(3):
            self._publish_cmd(0.0, 0.0)
        self._csv_file.flush()
        self.get_logger().info(f"Yaw calibration finished: {self._csv_file.name}")

    def _log_waiting(self, now: float, remaining: float) -> None:
        if now - self._last_log_sec < 1.0:
            return
        self._last_log_sec = now
        self.get_logger().info(f"starting in {remaining:.1f}s")

    @staticmethod
    def _stamp_to_sec(stamp) -> float:
        return float(stamp.sec) + float(stamp.nanosec) * 1.0e-9

    @staticmethod
    def _age_sec(now_sec: float, stamp_sec: float | None) -> float | None:
        if stamp_sec is None:
            return None
        return max(0.0, now_sec - stamp_sec)

    @staticmethod
    def _format_optional(value: float | None) -> str:
        if value is None or not math.isfinite(float(value)):
            return ""
        return f"{float(value):.6f}"

    @staticmethod
    def _clamp(value: float, lower: float, upper: float) -> float:
        return max(lower, min(upper, value))

    def destroy_node(self) -> bool:
        self._publish_cmd(0.0, 0.0)
        try:
            self._csv_file.close()
        except Exception:
            pass
        return super().destroy_node()


def main() -> None:
    rclpy.init()
    node = YawCalibrationCollector()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()

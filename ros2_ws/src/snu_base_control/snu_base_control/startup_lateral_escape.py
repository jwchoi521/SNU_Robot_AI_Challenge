from __future__ import annotations

from math import isfinite
import os
import select

try:
    import termios
    import tty
except ImportError:  # pragma: no cover - the robot runs on Linux.
    termios = None
    tty = None

import rclpy
from geometry_msgs.msg import PoseStamped
from nav_msgs.msg import OccupancyGrid
from rclpy.node import Node
from rclpy.qos import DurabilityPolicy, QoSProfile, ReliabilityPolicy
from sensor_msgs.msg import Image
from snu_robot_interfaces.msg import FourWheelCommand
from std_msgs.msg import Bool, Empty


class StartupLateralEscape(Node):
    """Publish a short startup wheel command after perception/localization is ready."""

    def __init__(self) -> None:
        super().__init__("startup_lateral_escape")

        self.declare_parameter("wheel_command_topic", "/wheel_commands")
        self.declare_parameter("active_topic", "/startup_escape/active")
        self.declare_parameter("mission_start_topic", "/mission/start")
        self.declare_parameter("require_map_ready", True)
        self.declare_parameter("map_topic", "/map")
        self.declare_parameter("require_robot_pose_ready", True)
        self.declare_parameter("robot_pose_topic", "/robot_pose_map")
        self.declare_parameter("require_camera_ready", True)
        self.declare_parameter("camera_topic", "/camera/image_raw")
        self.declare_parameter("ready_timeout_sec", 20.0)
        self.declare_parameter("wait_for_manual_trigger", False)
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
        self._active_publisher = self.create_publisher(
            Bool,
            str(self.get_parameter("active_topic").value),
            QoSProfile(
                depth=1,
                durability=DurabilityPolicy.TRANSIENT_LOCAL,
                reliability=ReliabilityPolicy.RELIABLE,
            ),
        )
        self._mission_start_publisher = self.create_publisher(
            Empty,
            str(self.get_parameter("mission_start_topic").value),
            QoSProfile(
                depth=1,
                durability=DurabilityPolicy.TRANSIENT_LOCAL,
                reliability=ReliabilityPolicy.RELIABLE,
            ),
        )

        self._require_map_ready = bool(self.get_parameter("require_map_ready").value)
        self._require_robot_pose_ready = bool(
            self.get_parameter("require_robot_pose_ready").value
        )
        self._require_camera_ready = bool(
            self.get_parameter("require_camera_ready").value
        )
        self._ready_timeout_sec = max(
            0.0,
            _finite_or_default(self.get_parameter("ready_timeout_sec").value, 20.0),
        )
        self._wait_for_manual_trigger = bool(
            self.get_parameter("wait_for_manual_trigger").value
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
        self._created_sec = now_sec
        self._ready_sec: float | None = None
        run_sec = self._distance_m / self._speed_mps if self._speed_mps > 0.0 else 0.0
        self._start_sec: float | None = None
        self._run_sec = run_sec
        self._end_sec: float | None = None
        self._stop_until_sec: float | None = None
        self._have_map = not self._require_map_ready
        self._have_robot_pose = not self._require_robot_pose_ready
        self._have_camera = not self._require_camera_ready
        self._last_wait_log_sec = 0.0
        self._manual_trigger_stream = None
        self._manual_trigger_terminal_settings = None
        self._manual_trigger_unavailable = False
        self._mission_start_published = False
        self._ready_subscriptions = []
        if self._require_map_ready:
            self._ready_subscriptions.append(
                self.create_subscription(
                    OccupancyGrid,
                    str(self.get_parameter("map_topic").value),
                    self._on_map,
                    1,
                )
            )
        if self._require_robot_pose_ready:
            self._ready_subscriptions.append(
                self.create_subscription(
                    PoseStamped,
                    str(self.get_parameter("robot_pose_topic").value),
                    self._on_robot_pose,
                    10,
                )
            )
        if self._require_camera_ready:
            self._ready_subscriptions.append(
                self.create_subscription(
                    Image,
                    str(self.get_parameter("camera_topic").value),
                    self._on_camera,
                    1,
                )
            )
        self.done = self._distance_m <= 0.0 or self._speed_mps <= 0.0
        self._started = False
        self._stopping = False

        publish_hz = max(
            1.0,
            _finite_or_default(self.get_parameter("publish_hz").value, 30.0),
        )
        self._timer = self.create_timer(1.0 / publish_hz, self._on_timer)
        self._publish_active(True)
        self.get_logger().info(
            "startup forward escape armed: "
            f"require_map={self._require_map_ready}, "
            f"require_robot_pose={self._require_robot_pose_ready}, "
            f"require_camera={self._require_camera_ready}, "
            f"ready_timeout={self._ready_timeout_sec:.2f}s, "
            f"manual_trigger={self._wait_for_manual_trigger}, "
            f"delay={self._start_delay_sec:.2f}s, "
            f"distance={self._distance_m:.2f}m, speed={self._speed_mps:.2f}m/s, "
            f"direction_sign={self._direction_sign:+.0f}"
        )

    def _on_map(self, _msg: OccupancyGrid) -> None:
        self._have_map = True

    def _on_robot_pose(self, _msg: PoseStamped) -> None:
        self._have_robot_pose = True

    def _on_camera(self, _msg: Image) -> None:
        self._have_camera = True

    def _on_timer(self) -> None:
        if self.done:
            return

        self._publish_active(True)
        now_sec = self._now_sec()
        if self._ready_sec is None:
            if not self._ready():
                if (
                    self._ready_timeout_sec <= 0.0
                    or now_sec - self._created_sec < self._ready_timeout_sec
                ):
                    self._log_waiting_if_needed(now_sec)
                    return
                self.get_logger().warn(
                    "startup escape readiness timeout; running with missing inputs: "
                    + ", ".join(self._missing_inputs())
                )
            self._ready_sec = now_sec
            if self._wait_for_manual_trigger:
                self._arm_manual_trigger()
                self.get_logger().info(
                    "startup escape ready; press SPACE or ENTER to start"
                )
            else:
                self._schedule_start(now_sec)

        if self._start_sec is None:
            if not self._manual_trigger_received():
                return
            self.get_logger().info("manual startup trigger received")
            self._schedule_start(now_sec)

        if now_sec < self._start_sec:
            return

        if self._end_sec is not None and now_sec < self._end_sec:
            if not self._started:
                self._started = True
                self.get_logger().info("starting startup forward escape")
            self._publish_forward_command()
            return

        if self._stop_until_sec is not None and now_sec < self._stop_until_sec:
            if not self._stopping:
                self._stopping = True
                self.get_logger().info("startup forward escape complete; stopping wheels")
            self._publish_stop()
            return

        self._publish_stop()
        self.done = True
        self._publish_active(False)
        self.get_logger().info("startup forward escape node done")

    def _schedule_start(self, now_sec: float) -> None:
        self._publish_mission_start()
        self._start_sec = now_sec + self._start_delay_sec
        self._end_sec = self._start_sec + self._run_sec
        self._stop_until_sec = self._end_sec + self._stop_hold_sec
        self.get_logger().info(
            "startup escape released; "
            f"starting in {self._start_delay_sec:.2f}s"
        )

    def _publish_mission_start(self) -> None:
        if self._mission_start_published:
            return
        self._mission_start_publisher.publish(Empty())
        self._mission_start_published = True
        self.get_logger().info("mission timer started")

    def _arm_manual_trigger(self) -> None:
        if self._manual_trigger_stream is not None or self._manual_trigger_unavailable:
            return
        if termios is None or tty is None:
            self._manual_trigger_unavailable = True
            self.get_logger().error(
                "manual startup trigger requires a Linux terminal"
            )
            return

        stream = None
        try:
            stream = open("/dev/tty", "rb", buffering=0)
            fd = stream.fileno()
            terminal_settings = termios.tcgetattr(fd)
            termios.tcflush(fd, termios.TCIFLUSH)
            tty.setcbreak(fd)
        except Exception as exc:
            if stream is not None:
                stream.close()
            self._manual_trigger_unavailable = True
            self.get_logger().error(
                "failed to arm manual startup trigger from /dev/tty: " + str(exc)
            )
            return

        self._manual_trigger_stream = stream
        self._manual_trigger_terminal_settings = terminal_settings

    def _manual_trigger_received(self) -> bool:
        if not self._wait_for_manual_trigger:
            return True
        if self._manual_trigger_stream is None:
            self._arm_manual_trigger()
            return False

        try:
            fd = self._manual_trigger_stream.fileno()
            readable, _, _ = select.select([fd], [], [], 0.0)
            if not readable:
                return False
            key = os.read(fd, 1)
        except Exception as exc:
            self.get_logger().error("manual startup trigger read failed: " + str(exc))
            self._close_manual_trigger_input()
            self._manual_trigger_unavailable = True
            return False

        if key not in (b" ", b"\r", b"\n"):
            return False
        self._close_manual_trigger_input()
        return True

    def _close_manual_trigger_input(self) -> None:
        stream = self._manual_trigger_stream
        terminal_settings = self._manual_trigger_terminal_settings
        self._manual_trigger_stream = None
        self._manual_trigger_terminal_settings = None
        if stream is None:
            return
        try:
            if termios is not None and terminal_settings is not None:
                termios.tcsetattr(
                    stream.fileno(),
                    termios.TCSADRAIN,
                    terminal_settings,
                )
        finally:
            stream.close()

    def destroy_node(self):
        self._close_manual_trigger_input()
        return super().destroy_node()

    def _publish_active(self, active: bool) -> None:
        msg = Bool()
        msg.data = bool(active)
        self._active_publisher.publish(msg)

    def _ready(self) -> bool:
        return self._have_map and self._have_robot_pose and self._have_camera

    def _missing_inputs(self) -> list[str]:
        missing = []
        if not self._have_map:
            missing.append(str(self.get_parameter("map_topic").value))
        if not self._have_robot_pose:
            missing.append(str(self.get_parameter("robot_pose_topic").value))
        if not self._have_camera:
            missing.append(str(self.get_parameter("camera_topic").value))
        return missing

    def _log_waiting_if_needed(self, now_sec: float) -> None:
        if now_sec - self._last_wait_log_sec < 1.0:
            return
        self._last_wait_log_sec = now_sec
        self.get_logger().info(
            "waiting before startup escape for: " + ", ".join(self._missing_inputs())
        )

    def _publish_forward_command(self) -> None:
        wheel_rad_s = self._direction_sign * self._speed_mps / self._wheel_radius_m
        self._publish_wheels(
            front_left=wheel_rad_s,
            front_right=wheel_rad_s,
            rear_left=wheel_rad_s,
            rear_right=wheel_rad_s,
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

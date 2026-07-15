from __future__ import annotations

import json
import math
from dataclasses import dataclass
from typing import Any

import rclpy
from action_msgs.msg import GoalStatus
from geometry_msgs.msg import PoseStamped, Twist
from nav2_msgs.action import NavigateToPose
from rclpy.action import ActionClient
from rclpy.node import Node
from snu_robot_interfaces.msg import GripperCommand
from std_msgs.msg import String

from .core import Pose2D, angle_diff, quaternion_from_yaw, yaw_from_quaternion


@dataclass
class TrackedTarget:
    pose: Pose2D
    stamp_sec: float
    last_seen_sec: float
    seen_count: int = 1


class BboxGoalNavigatorNode(Node):
    """Turn bbox-localized object poses into Nav2 navigation goals.

    The perception stack publishes object poses in the map frame after YOLO,
    homography/residual pose estimation, and LiDAR wall localization. This node
    chooses either the object center or a target-facing approach pose near that
    object and optionally sends it to Nav2's NavigateToPose action server.
    """

    def __init__(self) -> None:
        super().__init__("bbox_goal_navigator_node")

        self.declare_parameter("target_pose_topic", "/object_pose_map")
        self.declare_parameter("obstacle_pose_topic", "/obstacle_object_pose_map")
        self.declare_parameter("robot_pose_topic", "/robot_pose_map")
        self.declare_parameter("computed_goal_topic", "/bbox_goal_pose")
        self.declare_parameter("selected_target_pose_topic", "/bbox_goal_target_pose")
        self.declare_parameter("status_topic", "/bbox_goal_navigator/status")
        self.declare_parameter("mission_event_topic", "/mission/event")
        self.declare_parameter(
            "capture_event_names",
            "object_captured,cargo_entry,pickup_success,target_captured",
        )
        self.declare_parameter("gripper_command_topic", "/gripper/command")
        self.declare_parameter("cmd_vel_topic", "/cmd_vel")
        self.declare_parameter("nav_action_name", "navigate_to_pose")
        self.declare_parameter("map_frame", "map")
        self.declare_parameter("send_nav2_goal", True)
        self.declare_parameter("publish_mission_events", True)
        self.declare_parameter("control_gripper_gate", True)
        self.declare_parameter("gate_open_distance_m", 0.70)
        self.declare_parameter("approach_distance_m", 0.0)
        self.declare_parameter("goal_reached_tolerance_m", 0.12)
        self.declare_parameter("min_goal_separation_m", 0.15)
        self.declare_parameter("min_goal_yaw_delta_deg", 12.0)
        self.declare_parameter("max_target_age_sec", 1.5)
        self.declare_parameter("target_selection_mode", "nearest")
        self.declare_parameter("target_association_radius_m", 0.15)
        self.declare_parameter("reclassification_radius_m", 0.25)
        self.declare_parameter("max_tracked_targets", 20)
        self.declare_parameter("control_period_sec", 0.2)
        self.declare_parameter("capture_stop_hold_sec", 0.8)
        self.declare_parameter("capture_remove_radius_m", 0.40)
        self.declare_parameter("nav_server_wait_sec", 0.05)
        self.declare_parameter("arena_width_m", 0.0)
        self.declare_parameter("arena_height_m", 0.0)
        self.declare_parameter("arena_origin", "center")
        self.declare_parameter("goal_margin_m", 0.20)

        self._map_frame = str(self.get_parameter("map_frame").value)
        self._send_nav2_goal = bool(self.get_parameter("send_nav2_goal").value)
        self._publish_mission_events = bool(
            self.get_parameter("publish_mission_events").value
        )
        self._control_gripper_gate = bool(
            self.get_parameter("control_gripper_gate").value
        )
        self._nav_server_wait_sec = float(
            self.get_parameter("nav_server_wait_sec").value
        )

        self._robot_pose: Pose2D | None = None
        self._target_pose: Pose2D | None = None
        self._target_stamp_sec: float | None = None
        self._tracked_targets: list[TrackedTarget] = []
        self._selected_target_distance_m: float | None = None
        self._last_sent_goal: Pose2D | None = None
        self._goal_sequence = 0
        self._active_goal_sequence: int | None = None
        self._active_goal_handle = None
        self._cancel_pending_goal = False
        self._nav_state = "idle"
        self._gate_state = "closed"
        self._gate_open_latched = False
        self._stop_until_sec = 0.0
        self._last_status: dict[str, Any] = {}
        self._warned_nav_server_unavailable = False

        self._nav_client = ActionClient(
            self,
            NavigateToPose,
            str(self.get_parameter("nav_action_name").value),
        )
        self._goal_pub = self.create_publisher(
            PoseStamped,
            str(self.get_parameter("computed_goal_topic").value),
            10,
        )
        self._selected_target_pub = self.create_publisher(
            PoseStamped,
            str(self.get_parameter("selected_target_pose_topic").value),
            10,
        )
        self._status_pub = self.create_publisher(
            String,
            str(self.get_parameter("status_topic").value),
            10,
        )
        self._mission_event_pub = self.create_publisher(
            String,
            str(self.get_parameter("mission_event_topic").value),
            10,
        )
        self._cmd_vel_pub = self.create_publisher(
            Twist,
            str(self.get_parameter("cmd_vel_topic").value),
            10,
        )
        self._gripper_pub = self.create_publisher(
            GripperCommand,
            str(self.get_parameter("gripper_command_topic").value),
            10,
        )
        self.create_subscription(
            String,
            str(self.get_parameter("mission_event_topic").value),
            self._on_mission_event,
            10,
        )
        self.create_subscription(
            PoseStamped,
            str(self.get_parameter("target_pose_topic").value),
            self._on_target_pose,
            10,
        )
        self.create_subscription(
            PoseStamped,
            str(self.get_parameter("obstacle_pose_topic").value),
            self._on_obstacle_pose,
            10,
        )
        self.create_subscription(
            PoseStamped,
            str(self.get_parameter("robot_pose_topic").value),
            self._on_robot_pose,
            10,
        )

        period = max(0.05, float(self.get_parameter("control_period_sec").value))
        self._timer = self.create_timer(period, self._control_step)
        self.get_logger().info(
            "bbox goal navigator listening for "
            f"{self.get_parameter('target_pose_topic').value}; "
            f"send_nav2_goal={self._send_nav2_goal}; "
            f"target_selection_mode={self._target_selection_mode()}"
        )

    def _on_robot_pose(self, msg: PoseStamped) -> None:
        self._robot_pose = _pose_from_msg(msg)

    def _on_target_pose(self, msg: PoseStamped) -> None:
        if msg.header.frame_id and msg.header.frame_id != self._map_frame:
            self.get_logger().warn(
                "ignoring target pose in frame "
                f"{msg.header.frame_id!r}; expected {self._map_frame!r}"
            )
            return
        pose = _pose_from_msg(msg)
        stamp_sec = self._stamp_to_sec(msg.header.stamp)
        if stamp_sec <= 0.0:
            stamp_sec = self._now_sec()

        self._upsert_tracked_target(pose, stamp_sec)
        if self._target_selection_mode() == "latest":
            self._target_pose = pose
            self._target_stamp_sec = stamp_sec

    def _on_obstacle_pose(self, msg: PoseStamped) -> None:
        if msg.header.frame_id and msg.header.frame_id != self._map_frame:
            self.get_logger().warn(
                "ignoring obstacle pose in frame "
                f"{msg.header.frame_id!r}; expected {self._map_frame!r}"
            )
            return

        obstacle = _pose_from_msg(msg)
        radius = max(
            0.0,
            float(self.get_parameter("reclassification_radius_m").value),
        )
        before = len(self._tracked_targets)
        self._tracked_targets = [
            tracked
            for tracked in self._tracked_targets
            if math.hypot(tracked.pose.x - obstacle.x, tracked.pose.y - obstacle.y)
            > radius
        ]
        removed = before - len(self._tracked_targets)
        selected_reclassified = (
            self._target_pose is not None
            and math.hypot(
                self._target_pose.x - obstacle.x,
                self._target_pose.y - obstacle.y,
            )
            <= radius
        )
        if not selected_reclassified and removed == 0:
            return

        if selected_reclassified:
            self._nav_state = "target_reclassified_obstacle"
            self._cancel_active_goal("target_reclassified_obstacle")
            self._publish_stop_cmd()
            self._send_gripper(GripperCommand.CLOSE, "target_reclassified_obstacle")
            self._target_pose = None
            self._target_stamp_sec = None
            self._selected_target_distance_m = None
            self._last_sent_goal = None

        self._publish_status(
            "target_reclassified_obstacle",
            removed_tracked_targets=removed,
            obstacle=_pose_to_dict(obstacle),
        )

    def _on_mission_event(self, msg: String) -> None:
        event = msg.data.strip()
        if not event:
            return
        event_name = event.split()[0].strip().lower()
        capture_event_names = {
            name.strip().lower()
            for name in str(self.get_parameter("capture_event_names").value).split(",")
            if name.strip()
        }
        if event_name not in capture_event_names:
            return
        self._handle_capture_event(event_name)

    def _handle_capture_event(self, event_name: str) -> None:
        self._nav_state = "capture_complete"
        self._cancel_active_goal(event_name)
        self._publish_stop_cmd()
        hold_sec = max(0.0, float(self.get_parameter("capture_stop_hold_sec").value))
        self._stop_until_sec = max(self._stop_until_sec, self._now_sec() + hold_sec)
        self._send_gripper(GripperCommand.CLOSE, f"capture_event:{event_name}")
        self._gate_open_latched = False
        removed = self._remove_selected_target()
        self._last_sent_goal = None
        self._target_pose = None
        self._target_stamp_sec = None
        self._selected_target_distance_m = None
        self._publish_status(
            "capture_complete",
            capture_event=event_name,
            removed_tracked_targets=removed,
        )

    def _control_step(self) -> None:
        if self._now_sec() <= self._stop_until_sec:
            self._publish_stop_cmd()
            self._publish_status("capture_stop_hold")
            return
        if self._robot_pose is None:
            self._publish_status("waiting_for_robot_pose")
            return
        selected_target = self._select_target(self._robot_pose)
        if selected_target is not None:
            self._target_pose = selected_target.pose
            self._target_stamp_sec = selected_target.stamp_sec

        if self._target_pose is None or self._target_stamp_sec is None:
            self._close_gate_and_reset_latch("waiting_for_target_pose")
            self._publish_status("waiting_for_target_pose")
            return

        target_age = self._now_sec() - self._target_stamp_sec
        max_age = float(self.get_parameter("max_target_age_sec").value)
        if max_age > 0.0 and target_age > max_age:
            self._close_gate_and_reset_latch("target_stale")
            self._publish_status("target_stale", target_age_sec=target_age)
            return

        self._publish_selected_target_pose(self._target_pose)
        self._update_gate_for_target_distance()
        goal = self._compute_approach_goal(self._robot_pose, self._target_pose)
        if goal is None:
            self._publish_status("target_goal_reached")
            return

        self._publish_goal_pose(goal)
        if not self._send_nav2_goal:
            self._publish_status("published_goal_only", goal=goal, target_age_sec=target_age)
            return

        if not self._should_send_goal(goal):
            self._publish_status(
                self._nav_state,
                goal=goal,
                target_age_sec=target_age,
            )
            return

        self._send_goal(goal)

    def _upsert_tracked_target(self, pose: Pose2D, stamp_sec: float) -> None:
        now_sec = self._now_sec()
        self._prune_tracked_targets(now_sec)

        association_radius = max(
            0.0,
            float(self.get_parameter("target_association_radius_m").value),
        )
        best_index: int | None = None
        best_distance = association_radius
        for index, target in enumerate(self._tracked_targets):
            distance = math.hypot(pose.x - target.pose.x, pose.y - target.pose.y)
            if distance <= best_distance:
                best_distance = distance
                best_index = index

        if best_index is None:
            self._tracked_targets.append(
                TrackedTarget(pose=pose, stamp_sec=stamp_sec, last_seen_sec=now_sec)
            )
        else:
            target = self._tracked_targets[best_index]
            target.pose = pose
            target.stamp_sec = stamp_sec
            target.last_seen_sec = now_sec
            target.seen_count += 1

        max_targets = max(1, int(self.get_parameter("max_tracked_targets").value))
        if len(self._tracked_targets) > max_targets:
            self._tracked_targets.sort(key=lambda target: target.last_seen_sec, reverse=True)
            del self._tracked_targets[max_targets:]

    def _select_target(self, robot: Pose2D) -> TrackedTarget | None:
        self._prune_tracked_targets(self._now_sec())
        if not self._tracked_targets:
            self._selected_target_distance_m = None
            return None

        mode = self._target_selection_mode()
        if mode == "latest":
            selected = max(
                self._tracked_targets,
                key=lambda target: (target.stamp_sec, target.last_seen_sec),
            )
        else:
            selected = min(
                self._tracked_targets,
                key=lambda target: math.hypot(
                    target.pose.x - robot.x,
                    target.pose.y - robot.y,
                ),
            )

        self._selected_target_distance_m = math.hypot(
            selected.pose.x - robot.x,
            selected.pose.y - robot.y,
        )
        return selected

    def _prune_tracked_targets(self, now_sec: float) -> None:
        max_age = float(self.get_parameter("max_target_age_sec").value)
        if max_age <= 0.0:
            return
        self._tracked_targets = [
            target
            for target in self._tracked_targets
            if now_sec - target.stamp_sec <= max_age
        ]

    def _target_selection_mode(self) -> str:
        mode = str(self.get_parameter("target_selection_mode").value).strip().lower()
        if mode in ("latest", "last"):
            return "latest"
        return "nearest"

    def _compute_approach_goal(
        self,
        robot: Pose2D,
        target: Pose2D,
    ) -> Pose2D | None:
        dx = target.x - robot.x
        dy = target.y - robot.y
        target_distance = math.hypot(dx, dy)
        approach_distance = max(
            0.0,
            float(self.get_parameter("approach_distance_m").value),
        )
        reached_tolerance = max(
            0.0,
            float(self.get_parameter("goal_reached_tolerance_m").value),
        )
        if target_distance <= approach_distance + reached_tolerance:
            return None

        if target_distance > 1e-6 and approach_distance > 0.0:
            gx = target.x - approach_distance * dx / target_distance
            gy = target.y - approach_distance * dy / target_distance
        else:
            gx = target.x
            gy = target.y

        gx, gy = self._clamp_goal_to_arena(gx, gy)
        heading = math.atan2(target.y - gy, target.x - gx)
        return Pose2D(x=gx, y=gy, theta=heading)

    def _clamp_goal_to_arena(self, x: float, y: float) -> tuple[float, float]:
        width = float(self.get_parameter("arena_width_m").value)
        height = float(self.get_parameter("arena_height_m").value)
        margin = max(0.0, float(self.get_parameter("goal_margin_m").value))
        if width > 0.0:
            min_x, max_x = self._axis_bounds(width)
            x = min(max(min_x + margin, x), max(min_x + margin, max_x - margin))
        if height > 0.0:
            min_y, max_y = self._axis_bounds(height)
            y = min(max(min_y + margin, y), max(min_y + margin, max_y - margin))
        return x, y

    def _axis_bounds(self, length: float) -> tuple[float, float]:
        origin = str(self.get_parameter("arena_origin").value).lower()
        if origin in ("center", "centre", "middle"):
            half = 0.5 * length
            return -half, half
        if origin in ("corner", "bottom_left", "lower_left"):
            return 0.0, length
        raise ValueError(f"arena_origin must be 'center' or 'corner', got {origin!r}")

    def _should_send_goal(self, goal: Pose2D) -> bool:
        if self._last_sent_goal is None:
            return True

        distance = math.hypot(
            goal.x - self._last_sent_goal.x,
            goal.y - self._last_sent_goal.y,
        )
        min_separation = max(
            0.0,
            float(self.get_parameter("min_goal_separation_m").value),
        )
        if distance >= min_separation:
            return True

        yaw_delta = abs(angle_diff(goal.theta, self._last_sent_goal.theta))
        min_yaw_delta = math.radians(
            max(0.0, float(self.get_parameter("min_goal_yaw_delta_deg").value))
        )
        return yaw_delta >= min_yaw_delta

    def _send_goal(self, goal: Pose2D) -> None:
        if not self._nav_client.wait_for_server(timeout_sec=self._nav_server_wait_sec):
            if not self._warned_nav_server_unavailable:
                self.get_logger().warn("Nav2 NavigateToPose action server is unavailable")
                self._warned_nav_server_unavailable = True
            self._publish_status("nav2_server_unavailable", goal=goal)
            return

        self._warned_nav_server_unavailable = False
        goal_msg = NavigateToPose.Goal()
        goal_msg.pose = self._make_pose_stamped(goal)

        self._goal_sequence += 1
        sequence = self._goal_sequence
        self._active_goal_sequence = sequence
        self._active_goal_handle = None
        self._cancel_pending_goal = False
        self._last_sent_goal = goal
        self._nav_state = "sending_goal"
        self._publish_status("sending_goal", goal=goal)

        future = self._nav_client.send_goal_async(goal_msg)
        future.add_done_callback(
            lambda done_future: self._on_goal_response(done_future, sequence, goal)
        )

    def _on_goal_response(self, future, sequence: int, goal: Pose2D) -> None:
        if sequence != self._active_goal_sequence:
            return
        try:
            goal_handle = future.result()
        except Exception as exc:  # noqa: BLE001 - report action-client failures.
            self._nav_state = "goal_send_failed"
            self._last_sent_goal = None
            self._send_gripper(GripperCommand.CLOSE, "goal_send_failed")
            self._publish_status("goal_send_failed", error=str(exc), goal=goal)
            return

        if not goal_handle.accepted:
            self._nav_state = "goal_rejected"
            self._active_goal_handle = None
            self._cancel_pending_goal = False
            self._last_sent_goal = None
            self._send_gripper(GripperCommand.CLOSE, "goal_rejected")
            self._publish_status("goal_rejected", goal=goal)
            return

        self._active_goal_handle = goal_handle
        if self._cancel_pending_goal:
            self._cancel_pending_goal = False
            self._cancel_active_goal("pending_capture_event")
            return
        self._nav_state = "goal_active"
        self._publish_status("goal_active", goal=goal)
        result_future = goal_handle.get_result_async()
        result_future.add_done_callback(
            lambda done_future: self._on_goal_result(done_future, sequence, goal)
        )

    def _on_goal_result(self, future, sequence: int, goal: Pose2D) -> None:
        if sequence != self._active_goal_sequence:
            return
        self._active_goal_sequence = None
        self._active_goal_handle = None
        self._cancel_pending_goal = False
        try:
            result = future.result()
        except Exception as exc:  # noqa: BLE001 - report action-client failures.
            self._nav_state = "goal_result_failed"
            self._send_gripper(GripperCommand.CLOSE, "goal_result_failed")
            self._publish_status("goal_result_failed", error=str(exc), goal=goal)
            return

        status_name = _goal_status_name(int(result.status))
        self._nav_state = status_name
        self._publish_status(status_name, goal=goal)
        if result.status == GoalStatus.STATUS_SUCCEEDED:
            self._publish_mission_event("target_reached")
            self._send_gripper(GripperCommand.CLOSE, "target_reached")
        elif result.status in (
            GoalStatus.STATUS_ABORTED,
            GoalStatus.STATUS_CANCELED,
        ):
            self._send_gripper(GripperCommand.CLOSE, status_name)

    def _cancel_active_goal(self, reason: str) -> None:
        goal_handle = self._active_goal_handle
        if goal_handle is None:
            if self._active_goal_sequence is not None:
                self._cancel_pending_goal = True
            return
        self._active_goal_handle = None
        self._active_goal_sequence = None
        self._cancel_pending_goal = False
        try:
            future = goal_handle.cancel_goal_async()
            future.add_done_callback(
                lambda done_future: self._on_cancel_result(done_future, reason)
            )
        except Exception as exc:  # noqa: BLE001 - best-effort emergency cancel.
            self.get_logger().warn(f"failed to cancel Nav2 goal after {reason}: {exc}")

    def _on_cancel_result(self, future, reason: str) -> None:
        try:
            future.result()
        except Exception as exc:  # noqa: BLE001 - report action-client failures.
            self.get_logger().warn(f"Nav2 goal cancel failed after {reason}: {exc}")

    def _publish_stop_cmd(self) -> None:
        self._cmd_vel_pub.publish(Twist())

    def _update_gate_for_target_distance(self) -> None:
        if self._selected_target_distance_m is None:
            self._close_gate_and_reset_latch("target_distance_unknown")
            return
        open_distance = max(
            0.0,
            float(self.get_parameter("gate_open_distance_m").value),
        )
        if self._gate_open_latched:
            self._send_gripper(GripperCommand.OPEN, "gate_open_latched")
            return
        if self._selected_target_distance_m <= open_distance:
            self._gate_open_latched = True
            self._send_gripper(GripperCommand.OPEN, "target_within_gate_open_distance")
        else:
            self._send_gripper(GripperCommand.CLOSE, "target_outside_gate_open_distance")

    def _close_gate_and_reset_latch(self, reason: str) -> None:
        self._gate_open_latched = False
        self._send_gripper(GripperCommand.CLOSE, reason)

    def _remove_selected_target(self) -> int:
        target = self._target_pose
        if target is None:
            return 0
        remove_radius = max(
            0.0,
            float(self.get_parameter("capture_remove_radius_m").value),
        )
        before = len(self._tracked_targets)
        self._tracked_targets = [
            tracked
            for tracked in self._tracked_targets
            if math.hypot(tracked.pose.x - target.x, tracked.pose.y - target.y)
            > remove_radius
        ]
        return before - len(self._tracked_targets)

    def _publish_goal_pose(self, goal: Pose2D) -> None:
        self._goal_pub.publish(self._make_pose_stamped(goal))

    def _publish_selected_target_pose(self, target: Pose2D) -> None:
        self._selected_target_pub.publish(self._make_pose_stamped(target))

    def _make_pose_stamped(self, pose: Pose2D) -> PoseStamped:
        msg = PoseStamped()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = self._map_frame
        msg.pose.position.x = pose.x
        msg.pose.position.y = pose.y
        msg.pose.position.z = 0.0
        qx, qy, qz, qw = quaternion_from_yaw(pose.theta)
        msg.pose.orientation.x = qx
        msg.pose.orientation.y = qy
        msg.pose.orientation.z = qz
        msg.pose.orientation.w = qw
        return msg

    def _publish_mission_event(self, event: str) -> None:
        if not self._publish_mission_events:
            return
        msg = String()
        msg.data = event
        self._mission_event_pub.publish(msg)

    def _send_gripper(self, command: int, reason: str) -> None:
        if not self._control_gripper_gate:
            return
        desired_state = "open" if command == GripperCommand.OPEN else "closed"
        if self._gate_state == desired_state:
            return
        msg = GripperCommand()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.command = command
        msg.effort = 0.5
        self._gripper_pub.publish(msg)
        self._gate_state = desired_state
        self.get_logger().info(f"gripper gate {desired_state}: {reason}")

    def _publish_status(self, state: str, **extra: Any) -> None:
        payload: dict[str, Any] = {
            "state": state,
            "nav_state": self._nav_state,
            "send_nav2_goal": self._send_nav2_goal,
            "target_selection_mode": self._target_selection_mode(),
            "tracked_target_count": len(self._tracked_targets),
            "gate_state": self._gate_state,
            "gate_open_latched": self._gate_open_latched,
        }
        if self._selected_target_distance_m is not None:
            payload["selected_target_distance_m"] = round(
                float(self._selected_target_distance_m),
                4,
            )
        if self._robot_pose is not None:
            payload["robot"] = _pose_to_dict(self._robot_pose)
        if self._target_pose is not None:
            payload["target"] = _pose_to_dict(self._target_pose)
        for key, value in extra.items():
            if isinstance(value, Pose2D):
                payload[key] = _pose_to_dict(value)
            else:
                payload[key] = value

        if payload == self._last_status:
            return
        self._last_status = payload
        msg = String()
        msg.data = json.dumps(payload, separators=(",", ":"), sort_keys=True)
        self._status_pub.publish(msg)

    @staticmethod
    def _stamp_to_sec(stamp) -> float:
        return float(stamp.sec) + float(stamp.nanosec) * 1e-9

    def _now_sec(self) -> float:
        return self.get_clock().now().nanoseconds * 1e-9


def _pose_from_msg(msg: PoseStamped) -> Pose2D:
    q = msg.pose.orientation
    return Pose2D(
        x=float(msg.pose.position.x),
        y=float(msg.pose.position.y),
        theta=yaw_from_quaternion(q.x, q.y, q.z, q.w),
    )


def _pose_to_dict(pose: Pose2D) -> dict[str, float]:
    return {
        "x": round(float(pose.x), 4),
        "y": round(float(pose.y), 4),
        "theta": round(float(pose.theta), 4),
    }


def _goal_status_name(status: int) -> str:
    names = {
        GoalStatus.STATUS_UNKNOWN: "goal_unknown",
        GoalStatus.STATUS_ACCEPTED: "goal_accepted",
        GoalStatus.STATUS_EXECUTING: "goal_executing",
        GoalStatus.STATUS_CANCELING: "goal_canceling",
        GoalStatus.STATUS_SUCCEEDED: "goal_succeeded",
        GoalStatus.STATUS_CANCELED: "goal_canceled",
        GoalStatus.STATUS_ABORTED: "goal_aborted",
    }
    return names.get(status, f"goal_status_{status}")


def main() -> None:
    rclpy.init()
    node = BboxGoalNavigatorNode()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()

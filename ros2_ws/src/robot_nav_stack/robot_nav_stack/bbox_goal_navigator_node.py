from __future__ import annotations

import json
import math
from dataclasses import dataclass
from enum import Enum
from typing import Any

import rclpy
from action_msgs.msg import GoalStatus
from geometry_msgs.msg import PoseStamped, Twist
from nav2_msgs.action import BackUp, NavigateToPose
from rclpy.action import ActionClient
from rclpy.node import Node
from rclpy.qos import DurabilityPolicy, QoSProfile, ReliabilityPolicy
from snu_robot_interfaces.msg import GripperCommand
from std_msgs.msg import Bool, String

from .core import Pose2D, angle_diff, quaternion_from_yaw, wrap_angle, yaw_from_quaternion
from .storage_dropoff import (
    StorageBounds,
    StoragePlan,
    choose_storage_plan,
    footprint_fully_contained,
    heading_matches_entry,
)
from .target_lock import TargetLock


@dataclass
class TrackedTarget:
    pose: Pose2D
    stamp_sec: float
    last_seen_sec: float
    seen_count: int = 1


class StoragePhase(str, Enum):
    INACTIVE = "inactive"
    APPROACHING = "approaching"
    ENTERING = "entering"
    VERIFYING_INSIDE = "verifying_inside"
    OPENING_GATE = "opening_gate"
    BACKING_UP = "backing_up"
    COMPLETE = "complete"
    FAILED = "failed"


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
        self.declare_parameter("capture_arm_topic", "/capture/arm")
        self.declare_parameter("cmd_vel_topic", "/cmd_vel")
        self.declare_parameter("nav_action_name", "navigate_to_pose")
        self.declare_parameter("map_frame", "map")
        self.declare_parameter("send_nav2_goal", True)
        self.declare_parameter("publish_mission_events", True)
        self.declare_parameter("control_gripper_gate", True)
        self.declare_parameter("control_capture_arm", True)
        self.declare_parameter("gate_open_distance_m", 0.70)
        self.declare_parameter("approach_distance_m", 0.0)
        self.declare_parameter("goal_reached_tolerance_m", 0.12)
        self.declare_parameter("min_goal_separation_m", 0.15)
        self.declare_parameter("min_goal_yaw_delta_deg", 12.0)
        self.declare_parameter("goal_heading_offset_deg", 0.0)
        self.declare_parameter("max_target_age_sec", 1.5)
        self.declare_parameter("target_selection_mode", "nearest")
        self.declare_parameter("target_association_radius_m", 0.15)
        self.declare_parameter("target_lock_distance_m", 0.30)
        self.declare_parameter("reclassification_radius_m", 0.25)
        self.declare_parameter("max_tracked_targets", 20)
        self.declare_parameter("target_search_enabled", True)
        self.declare_parameter("target_search_missing_timeout_sec", 2.0)
        self.declare_parameter("target_search_radius_m", 1.70)
        self.declare_parameter("target_search_goal_timeout_sec", 12.0)
        self.declare_parameter("target_search_initial_spin_enabled", True)
        self.declare_parameter("target_search_initial_spin_step_deg", 60.0)
        self.declare_parameter("target_search_dwell_sec", 1.0)
        self.declare_parameter("target_search_center_x_m", 0.0)
        self.declare_parameter("target_search_center_y_m", 0.0)
        self.declare_parameter("control_period_sec", 0.2)
        self.declare_parameter("capture_stop_hold_sec", 0.8)
        self.declare_parameter("capture_remove_radius_m", 0.40)
        self.declare_parameter("nav_server_wait_sec", 0.05)
        self.declare_parameter("arena_width_m", 0.0)
        self.declare_parameter("arena_height_m", 0.0)
        self.declare_parameter("arena_origin", "center")
        self.declare_parameter("goal_margin_m", 0.20)
        self.declare_parameter("storage_dropoff_enabled", True)
        self.declare_parameter("storage_trigger_count", 3)
        self.declare_parameter("storage_min_x", -2.0)
        self.declare_parameter("storage_max_x", -1.6)
        self.declare_parameter("storage_min_y", -2.0)
        self.declare_parameter("storage_max_y", -1.6)
        self.declare_parameter("storage_entry_mode", "auto")
        self.declare_parameter("storage_approach_clearance_m", 0.05)
        self.declare_parameter("robot_half_length_m", 0.16)
        self.declare_parameter("robot_half_width_m", 0.165)
        self.declare_parameter("storage_containment_margin_m", 0.0)
        self.declare_parameter("storage_heading_tolerance_deg", 10.0)
        self.declare_parameter("storage_verify_timeout_sec", 3.0)
        self.declare_parameter("storage_nav_max_retries", 2)
        self.declare_parameter("storage_open_gate_before_backup", True)
        self.declare_parameter("storage_gate_open_wait_sec", 1.0)
        self.declare_parameter("storage_backup_action_name", "backup")
        self.declare_parameter("storage_backup_distance_m", 0.50)
        self.declare_parameter("storage_backup_speed_mps", 0.20)
        self.declare_parameter("storage_backup_time_allowance_sec", 4.0)

        self._map_frame = str(self.get_parameter("map_frame").value)
        self._send_nav2_goal = bool(self.get_parameter("send_nav2_goal").value)
        self._publish_mission_events = bool(
            self.get_parameter("publish_mission_events").value
        )
        self._control_gripper_gate = bool(
            self.get_parameter("control_gripper_gate").value
        )
        self._control_capture_arm = bool(
            self.get_parameter("control_capture_arm").value
        )
        self._nav_server_wait_sec = float(
            self.get_parameter("nav_server_wait_sec").value
        )
        self._storage_dropoff_enabled = bool(
            self.get_parameter("storage_dropoff_enabled").value
        )
        self._storage_bounds = StorageBounds(
            min_x=float(self.get_parameter("storage_min_x").value),
            max_x=float(self.get_parameter("storage_max_x").value),
            min_y=float(self.get_parameter("storage_min_y").value),
            max_y=float(self.get_parameter("storage_max_y").value),
        )
        self._storage_bounds.validate()
        self._robot_half_length_m = float(
            self.get_parameter("robot_half_length_m").value
        )
        self._robot_half_width_m = float(
            self.get_parameter("robot_half_width_m").value
        )

        self._robot_pose: Pose2D | None = None
        self._target_pose: Pose2D | None = None
        self._target_stamp_sec: float | None = None
        self._tracked_targets: list[TrackedTarget] = []
        self._target_lock = TargetLock()
        self._selected_target_distance_m: float | None = None
        self._no_target_since_sec: float | None = None
        self._has_seen_target_since_start = False
        self._target_search_phase = "idle"
        self._target_search_index: int | None = None
        self._target_search_spin_start_yaw: float | None = None
        self._target_search_spin_index = 0
        self._target_search_goal_started_sec = 0.0
        self._target_search_dwell_until_sec = 0.0
        self._target_search_dwell_phase: str | None = None
        self._target_search_dwell_goal: Pose2D | None = None
        self._target_search_lap_count = 0
        self._last_sent_goal: Pose2D | None = None
        self._goal_sequence = 0
        self._active_goal_sequence: int | None = None
        self._active_goal_handle = None
        self._active_goal_purpose: str | None = None
        self._cancel_pending_goal = False
        self._nav_state = "idle"
        self._gate_state = "closed"
        self._gate_open_latched = False
        self._capture_arm_armed = False
        self._stop_until_sec = 0.0
        self._last_status: dict[str, Any] = {}
        self._warned_nav_server_unavailable = False
        self._captured_object_count = 0
        self._storage_phase = StoragePhase.INACTIVE
        self._storage_plan: StoragePlan | None = None
        self._storage_stage_goal_sent = False
        self._storage_nav_retry_count = 0
        self._storage_verify_deadline_sec = 0.0
        self._storage_gate_opened_at_sec = 0.0
        self._storage_cycle_id = 0
        self._backup_goal_pending = False
        self._backup_goal_handle = None
        self._warned_backup_server_unavailable = False

        self._nav_client = ActionClient(
            self,
            NavigateToPose,
            str(self.get_parameter("nav_action_name").value),
        )
        self._backup_client = ActionClient(
            self,
            BackUp,
            str(self.get_parameter("storage_backup_action_name").value),
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
        capture_arm_qos = QoSProfile(
            depth=1,
            durability=DurabilityPolicy.TRANSIENT_LOCAL,
            reliability=ReliabilityPolicy.RELIABLE,
        )
        self._capture_arm_pub = self.create_publisher(
            Bool,
            str(self.get_parameter("capture_arm_topic").value),
            capture_arm_qos,
        )
        self._send_capture_arm(False, "startup", force=True)
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
        self._no_target_since_sec = None
        if self._active_goal_purpose == "search":
            self._nav_state = "search_canceling_target_found"
            self._last_sent_goal = None
            self._cancel_active_goal("target_found_during_search")
        if self._target_selection_mode() == "latest" and not self._target_lock.active:
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
        locked_reclassification = self._target_lock.protects(obstacle, radius)
        before = len(self._tracked_targets)
        self._tracked_targets = [
            tracked
            for tracked in self._tracked_targets
            if self._target_lock.protects(tracked.pose, radius)
            or math.hypot(tracked.pose.x - obstacle.x, tracked.pose.y - obstacle.y)
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
        if locked_reclassification:
            self._publish_status(
                "target_reclassification_ignored_locked",
                removed_tracked_targets=removed,
                obstacle=_pose_to_dict(obstacle),
            )
            return
        if not selected_reclassified and removed == 0:
            return

        if selected_reclassified:
            self._nav_state = "target_reclassified_obstacle"
            self._cancel_active_goal("target_reclassified_obstacle")
            self._publish_stop_cmd()
            self._target_pose = None
            self._target_stamp_sec = None
            self._selected_target_distance_m = None
            self._last_sent_goal = None
            self._target_lock.clear()

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
        if event_name == "reset":
            self._reset_storage_mission()
            return
        capture_event_names = {
            name.strip().lower()
            for name in str(self.get_parameter("capture_event_names").value).split(",")
            if name.strip()
        }
        if event_name not in capture_event_names:
            return
        self._handle_capture_event(event_name)

    def _handle_capture_event(self, event_name: str) -> None:
        if self._storage_phase != StoragePhase.INACTIVE:
            self._publish_status(
                "capture_ignored_during_storage_dropoff",
                capture_event=event_name,
            )
            return

        self._captured_object_count += 1
        self._nav_state = "capture_complete"
        self._cancel_active_goal(event_name)
        self._publish_stop_cmd()
        hold_sec = max(0.0, float(self.get_parameter("capture_stop_hold_sec").value))
        self._stop_until_sec = max(self._stop_until_sec, self._now_sec() + hold_sec)
        self._send_capture_arm(False, f"capture_event:{event_name}")
        self._send_gripper(GripperCommand.CLOSE, f"capture_event:{event_name}")
        self._gate_open_latched = False
        removed = self._remove_selected_target()
        self._target_lock.clear()
        self._reset_target_search_runtime()
        self._last_sent_goal = None
        self._target_pose = None
        self._target_stamp_sec = None
        self._selected_target_distance_m = None
        self._publish_status(
            "capture_complete",
            captured_object_count=self._captured_object_count,
            capture_event=event_name,
            removed_tracked_targets=removed,
        )
        trigger_count = max(
            1,
            int(self.get_parameter("storage_trigger_count").value),
        )
        if self._storage_dropoff_enabled and self._captured_object_count >= trigger_count:
            self._begin_storage_dropoff()

    def _begin_storage_dropoff(self) -> None:
        self._storage_cycle_id += 1
        self._storage_plan = None
        self._storage_nav_retry_count = 0
        self._storage_verify_deadline_sec = 0.0
        self._storage_gate_opened_at_sec = 0.0
        self._storage_stage_goal_sent = False
        self._nav_state = "storage_dropoff_start"
        self._send_capture_arm(False, "storage_dropoff_start")
        self._send_gripper(GripperCommand.CLOSE, "storage_dropoff_start")
        self._gate_open_latched = False
        self._reset_target_search_runtime()
        self._set_storage_phase(StoragePhase.APPROACHING)
        self._publish_stop_cmd()
        self._publish_status("storage_dropoff_start")

    def _reset_storage_mission(self) -> None:
        self._storage_cycle_id += 1
        self._cancel_active_goal("mission_reset")
        self._cancel_backup_goal("mission_reset")
        self._send_capture_arm(False, "mission_reset", force=True)
        self._send_gripper(GripperCommand.CLOSE, "mission_reset")
        self._captured_object_count = 0
        self._storage_plan = None
        self._storage_stage_goal_sent = False
        self._storage_nav_retry_count = 0
        self._storage_verify_deadline_sec = 0.0
        self._storage_gate_opened_at_sec = 0.0
        self._storage_phase = StoragePhase.INACTIVE
        self._nav_state = "idle"
        self._target_lock.clear()
        self._reset_target_search_runtime()
        self._last_sent_goal = None
        self._target_pose = None
        self._target_stamp_sec = None
        self._selected_target_distance_m = None
        self._gate_open_latched = False
        self._publish_stop_cmd()
        self._publish_status("mission_reset")

    def _cancel_backup_goal(self, reason: str) -> None:
        goal_handle = self._backup_goal_handle
        self._backup_goal_handle = None
        self._backup_goal_pending = False
        if goal_handle is None:
            return
        try:
            future = goal_handle.cancel_goal_async()
            future.add_done_callback(
                lambda done_future: self._on_cancel_result(done_future, reason)
            )
        except Exception as exc:  # noqa: BLE001 - best-effort emergency cancel.
            self.get_logger().warn(
                f"failed to cancel Nav2 BackUp after {reason}: {exc}"
            )

    def _set_storage_phase(self, phase: StoragePhase) -> None:
        if phase == self._storage_phase:
            return
        previous = self._storage_phase
        self._storage_phase = phase
        self._nav_state = f"storage_{phase.value}"
        if phase in (StoragePhase.APPROACHING, StoragePhase.ENTERING):
            self._storage_stage_goal_sent = False
            self._last_sent_goal = None
        self.get_logger().info(
            f"storage dropoff phase: {previous.value} -> {phase.value}"
        )

    def _control_storage_step(self) -> None:
        robot_pose = self._robot_pose
        if robot_pose is None:
            self._publish_status("storage_waiting_for_robot_pose")
            return
        if self._storage_phase in (StoragePhase.COMPLETE, StoragePhase.FAILED):
            self._publish_stop_cmd()
            self._publish_status(f"storage_{self._storage_phase.value}")
            return

        if self._storage_plan is None:
            try:
                self._storage_plan = choose_storage_plan(
                    robot_pose=robot_pose,
                    bounds=self._storage_bounds,
                    robot_half_length_m=self._robot_half_length_m,
                    robot_half_width_m=self._robot_half_width_m,
                    approach_clearance_m=float(
                        self.get_parameter("storage_approach_clearance_m").value
                    ),
                    entry_mode=str(
                        self.get_parameter("storage_entry_mode").value
                    ),
                )
            except ValueError as exc:
                self._fail_storage_dropoff(f"invalid_storage_plan:{exc}")
                return
            self.get_logger().info(
                "storage entry selected: "
                f"{self._storage_plan.entry_direction.value}; "
                f"exit={self._storage_plan.exit_direction}"
            )

        plan = self._storage_plan
        if self._storage_phase == StoragePhase.APPROACHING:
            self._publish_goal_pose(plan.approach_pose)
            if not self._send_nav2_goal:
                self._publish_status(
                    "storage_approach_goal_published_only",
                    goal=plan.approach_pose,
                )
                return
            if not self._storage_stage_goal_sent:
                self._storage_stage_goal_sent = self._send_goal(
                    plan.approach_pose,
                    purpose="storage_approach",
                )
            self._publish_status(
                "storage_approaching",
                goal=plan.approach_pose,
            )
            return

        if self._storage_phase == StoragePhase.ENTERING:
            self._publish_goal_pose(plan.inside_pose)
            if not self._send_nav2_goal:
                self._publish_status(
                    "storage_inside_goal_published_only",
                    goal=plan.inside_pose,
                )
                return
            if not self._storage_stage_goal_sent:
                self._storage_stage_goal_sent = self._send_goal(
                    plan.inside_pose,
                    purpose="storage_enter",
                )
            self._publish_status("storage_entering", goal=plan.inside_pose)
            return

        if self._storage_phase == StoragePhase.VERIFYING_INSIDE:
            self._publish_stop_cmd()
            footprint_inside, heading_aligned = self._storage_ready_to_unload()
            self._publish_status(
                "storage_verifying_inside",
                footprint_fully_inside=footprint_inside,
                heading_aligned=heading_aligned,
            )
            if footprint_inside and heading_aligned:
                if not bool(
                    self.get_parameter("storage_open_gate_before_backup").value
                ):
                    self._publish_status("storage_gate_open_skipped")
                    self._send_backup_goal()
                    return
                self._send_gripper(
                    GripperCommand.OPEN,
                    "robot_fully_inside_storage",
                )
                self._storage_gate_opened_at_sec = self._now_sec()
                self._set_storage_phase(StoragePhase.OPENING_GATE)
                return
            if self._now_sec() >= self._storage_verify_deadline_sec:
                self._retry_storage_navigation(
                    "storage_enter",
                    "footprint_or_heading_not_inside",
                )
            return

        if self._storage_phase == StoragePhase.OPENING_GATE:
            self._publish_stop_cmd()
            wait_sec = max(
                0.0,
                float(self.get_parameter("storage_gate_open_wait_sec").value),
            )
            elapsed = self._now_sec() - self._storage_gate_opened_at_sec
            if elapsed >= wait_sec:
                self._send_backup_goal()
            else:
                self._publish_status(
                    "storage_waiting_for_gate_open",
                    gate_wait_remaining_sec=max(0.0, wait_sec - elapsed),
                )
            return

        if self._storage_phase == StoragePhase.BACKING_UP:
            self._publish_status(
                "storage_backing_up",
                backup_distance_m=float(
                    self.get_parameter("storage_backup_distance_m").value
                ),
                exit_direction=plan.exit_direction,
            )

    def _storage_ready_to_unload(self) -> tuple[bool, bool]:
        assert self._robot_pose is not None
        assert self._storage_plan is not None
        footprint_inside = footprint_fully_contained(
            robot_pose=self._robot_pose,
            bounds=self._storage_bounds,
            robot_half_length_m=self._robot_half_length_m,
            robot_half_width_m=self._robot_half_width_m,
            containment_margin_m=float(
                self.get_parameter("storage_containment_margin_m").value
            ),
        )
        heading_aligned = heading_matches_entry(
            robot_pose=self._robot_pose,
            plan=self._storage_plan,
            tolerance_rad=math.radians(
                max(
                    0.0,
                    float(
                        self.get_parameter(
                            "storage_heading_tolerance_deg"
                        ).value
                    ),
                )
            ),
        )
        return footprint_inside, heading_aligned

    def _retry_storage_navigation(self, purpose: str, reason: str) -> None:
        self._storage_nav_retry_count += 1
        max_retries = max(
            0,
            int(self.get_parameter("storage_nav_max_retries").value),
        )
        if self._storage_nav_retry_count > max_retries:
            self._fail_storage_dropoff(
                f"{purpose}_failed_after_{max_retries}_retries:{reason}"
            )
            return

        retry_phase = (
            StoragePhase.APPROACHING
            if purpose == "storage_approach"
            else StoragePhase.ENTERING
        )
        self._set_storage_phase(retry_phase)
        self._storage_stage_goal_sent = False
        self._last_sent_goal = None
        self._publish_status(
            "storage_navigation_retry",
            retry_count=self._storage_nav_retry_count,
            retry_reason=reason,
            retry_stage=purpose,
        )

    def _fail_storage_dropoff(self, reason: str) -> None:
        self._send_capture_arm(False, f"storage_failure:{reason}")
        self._send_gripper(GripperCommand.CLOSE, f"storage_failure:{reason}")
        self._publish_stop_cmd()
        self._set_storage_phase(StoragePhase.FAILED)
        self.get_logger().error(f"storage dropoff failed: {reason}")
        self._publish_status("storage_failed", failure_reason=reason)

    def _send_backup_goal(self) -> bool:
        if self._backup_goal_pending or self._backup_goal_handle is not None:
            return True
        if not self._backup_client.wait_for_server(
            timeout_sec=self._nav_server_wait_sec
        ):
            if not self._warned_backup_server_unavailable:
                self.get_logger().warn("Nav2 BackUp action server is unavailable")
                self._warned_backup_server_unavailable = True
            self._publish_status("storage_backup_server_unavailable")
            return False

        self._warned_backup_server_unavailable = False
        goal_msg = BackUp.Goal()
        goal_msg.target.x = -abs(
            float(self.get_parameter("storage_backup_distance_m").value)
        )
        goal_msg.target.y = 0.0
        goal_msg.target.z = 0.0
        goal_msg.speed = abs(
            float(self.get_parameter("storage_backup_speed_mps").value)
        )
        allowance = max(
            0.0,
            float(
                self.get_parameter(
                    "storage_backup_time_allowance_sec"
                ).value
            ),
        )
        goal_msg.time_allowance.sec = int(allowance)
        goal_msg.time_allowance.nanosec = int(
            (allowance - int(allowance)) * 1_000_000_000
        )
        if hasattr(goal_msg, "disable_collision_checks"):
            goal_msg.disable_collision_checks = False

        cycle_id = self._storage_cycle_id
        try:
            future = self._backup_client.send_goal_async(goal_msg)
        except Exception as exc:  # noqa: BLE001 - report action-client failures.
            self.get_logger().warn(f"failed to send Nav2 BackUp goal: {exc}")
            self._publish_status("storage_backup_send_failed", error=str(exc))
            return False
        self._backup_goal_pending = True
        self._set_storage_phase(StoragePhase.BACKING_UP)
        future.add_done_callback(
            lambda done_future: self._on_backup_goal_response(
                done_future,
                cycle_id,
            )
        )
        return True

    def _on_backup_goal_response(self, future, cycle_id: int) -> None:
        self._backup_goal_pending = False
        try:
            goal_handle = future.result()
        except Exception as exc:  # noqa: BLE001 - report action-client failures.
            if cycle_id == self._storage_cycle_id:
                self._fail_storage_dropoff(f"backup_send_failed:{exc}")
            return

        if cycle_id != self._storage_cycle_id:
            if goal_handle.accepted:
                goal_handle.cancel_goal_async()
            return
        if not goal_handle.accepted:
            self._fail_storage_dropoff("backup_goal_rejected")
            return

        self._backup_goal_handle = goal_handle
        result_future = goal_handle.get_result_async()
        result_future.add_done_callback(
            lambda done_future: self._on_backup_goal_result(
                done_future,
                cycle_id,
            )
        )

    def _on_backup_goal_result(self, future, cycle_id: int) -> None:
        if cycle_id != self._storage_cycle_id:
            return
        self._backup_goal_handle = None
        try:
            result = future.result()
        except Exception as exc:  # noqa: BLE001 - report action-client failures.
            self._fail_storage_dropoff(f"backup_result_failed:{exc}")
            return

        status_name = _goal_status_name(int(result.status))
        if result.status != GoalStatus.STATUS_SUCCEEDED:
            self._fail_storage_dropoff(f"backup_{status_name}")
            return

        self._publish_stop_cmd()
        self._send_capture_arm(False, "storage_backup_complete")
        self._send_gripper(GripperCommand.CLOSE, "storage_backup_complete")
        self._set_storage_phase(StoragePhase.COMPLETE)
        self._publish_mission_event("storage_dropoff_complete")
        self._publish_status(
            "storage_complete",
            backup_distance_m=float(
                self.get_parameter("storage_backup_distance_m").value
            ),
        )

    def _control_step(self) -> None:
        if self._now_sec() <= self._stop_until_sec:
            self._publish_stop_cmd()
            self._publish_status("capture_stop_hold")
            return
        if self._robot_pose is None:
            self._publish_status("waiting_for_robot_pose")
            return
        if self._storage_phase != StoragePhase.INACTIVE:
            self._control_storage_step()
            return
        selected_target = self._select_target(self._robot_pose)
        if selected_target is not None:
            self._target_pose = selected_target.pose
            self._target_stamp_sec = selected_target.stamp_sec
            self._no_target_since_sec = None
            self._has_seen_target_since_start = True
            self._reset_target_search_runtime()
            if self._active_goal_purpose == "search":
                self._nav_state = "search_canceling_target_found"
                self._last_sent_goal = None
                self._cancel_active_goal("target_found_during_search")
                self._publish_status(
                    "search_canceling_target_found",
                    target=_pose_to_dict(selected_target.pose),
                )
                return

        if self._target_pose is None or self._target_stamp_sec is None:
            self._control_target_search("waiting_for_target_pose")
            return

        target_age = self._now_sec() - self._target_stamp_sec
        max_age = float(self.get_parameter("max_target_age_sec").value)
        if not self._target_lock.active and max_age > 0.0 and target_age > max_age:
            self._target_pose = None
            self._target_stamp_sec = None
            self._selected_target_distance_m = None
            self._control_target_search("target_stale", target_age_sec=target_age)
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

    def _control_target_search(
        self,
        reason: str,
        target_age_sec: float | None = None,
    ) -> None:
        now_sec = self._now_sec()
        self._selected_target_distance_m = None
        self._gate_open_latched = False
        if self._no_target_since_sec is None:
            self._no_target_since_sec = now_sec
        missing_for_sec = max(0.0, now_sec - self._no_target_since_sec)

        if not bool(self.get_parameter("target_search_enabled").value):
            self._publish_status(
                reason,
                target_missing_for_sec=round(missing_for_sec, 3),
                target_age_sec=target_age_sec,
            )
            return

        missing_timeout = max(
            0.0,
            float(self.get_parameter("target_search_missing_timeout_sec").value),
        )
        if missing_for_sec < missing_timeout:
            self._publish_status(
                "waiting_before_target_search",
                target_missing_reason=reason,
                target_missing_for_sec=round(missing_for_sec, 3),
                target_search_missing_timeout_sec=missing_timeout,
                target_age_sec=target_age_sec,
            )
            return

        self._ensure_target_search_started(self._robot_pose)
        if self._target_search_dwell_until_sec > 0.0:
            if now_sec < self._target_search_dwell_until_sec:
                self._publish_stop_cmd()
                self._publish_status(
                    "target_search_dwell",
                    goal=self._target_search_dwell_goal,
                    target_missing_reason=reason,
                    target_missing_for_sec=round(missing_for_sec, 3),
                    target_search_dwell_remaining_sec=round(
                        max(0.0, self._target_search_dwell_until_sec - now_sec),
                        3,
                    ),
                    target_search_phase=self._target_search_phase,
                    target_search_spin_index=self._target_search_spin_index,
                    target_search_index=self._target_search_index,
                    target_search_lap_count=self._target_search_lap_count,
                )
                return
            self._finish_target_search_dwell()

        if self._active_goal_sequence is not None:
            if self._active_goal_purpose == "search":
                timeout_sec = max(
                    0.0,
                    float(self.get_parameter("target_search_goal_timeout_sec").value),
                )
                elapsed_sec = max(0.0, now_sec - self._target_search_goal_started_sec)
                if timeout_sec > 0.0 and elapsed_sec > timeout_sec:
                    self._advance_target_search_after_goal()
                    self._last_sent_goal = None
                    self._nav_state = "search_goal_timeout"
                    self._cancel_active_goal("target_search_goal_timeout")
                    self._publish_status(
                        "search_goal_timeout",
                        target_missing_reason=reason,
                        target_missing_for_sec=round(missing_for_sec, 3),
                        target_search_elapsed_sec=round(elapsed_sec, 3),
                        target_search_phase=self._target_search_phase,
                        target_search_spin_index=self._target_search_spin_index,
                        target_search_index=self._target_search_index,
                        target_search_lap_count=self._target_search_lap_count,
                    )
                    return
                self._publish_status(
                    "search_goal_active",
                    target_missing_reason=reason,
                    target_missing_for_sec=round(missing_for_sec, 3),
                    target_search_elapsed_sec=round(elapsed_sec, 3),
                    target_search_phase=self._target_search_phase,
                    target_search_spin_index=self._target_search_spin_index,
                    target_search_index=self._target_search_index,
                    target_search_lap_count=self._target_search_lap_count,
                )
                return

            self._publish_status(
                "waiting_for_active_goal_before_search",
                active_goal_purpose=self._active_goal_purpose,
                target_missing_reason=reason,
                target_missing_for_sec=round(missing_for_sec, 3),
            )
            return

        goal = self._target_search_goal(self._robot_pose)
        if goal is None:
            self._publish_status(
                "target_search_unavailable",
                target_missing_reason=reason,
                target_missing_for_sec=round(missing_for_sec, 3),
                target_search_phase=self._target_search_phase,
            )
            return

        self._publish_goal_pose(goal)
        if not self._send_nav2_goal:
            self._publish_status(
                "published_search_goal_only",
                goal=goal,
                target_missing_reason=reason,
                target_missing_for_sec=round(missing_for_sec, 3),
                target_search_phase=self._target_search_phase,
                target_search_spin_index=self._target_search_spin_index,
                target_search_index=self._target_search_index,
                target_search_lap_count=self._target_search_lap_count,
            )
            return

        if self._send_goal(goal, purpose="search"):
            self._target_search_goal_started_sec = now_sec
            self._publish_status(
                "sending_search_goal",
                goal=goal,
                target_missing_reason=reason,
                target_missing_for_sec=round(missing_for_sec, 3),
                target_search_phase=self._target_search_phase,
                target_search_spin_index=self._target_search_spin_index,
                target_search_index=self._target_search_index,
                target_search_lap_count=self._target_search_lap_count,
            )

    def _reset_target_search_runtime(self) -> None:
        self._target_search_phase = "idle"
        self._target_search_spin_start_yaw = None
        self._target_search_spin_index = 0
        self._target_search_dwell_until_sec = 0.0
        self._target_search_dwell_phase = None
        self._target_search_dwell_goal = None

    def _ensure_target_search_started(self, robot: Pose2D) -> None:
        if self._target_search_phase != "idle":
            return
        if (
            self._has_seen_target_since_start
            and bool(self.get_parameter("target_search_initial_spin_enabled").value)
        ):
            self._target_search_phase = "initial_spin"
            self._target_search_spin_start_yaw = robot.theta
            self._target_search_spin_index = 0
            return
        self._target_search_phase = "patrol"

    def _target_search_goal(self, robot: Pose2D) -> Pose2D | None:
        if self._target_search_phase == "initial_spin":
            spin_count = self._target_search_spin_count()
            if self._target_search_spin_index >= spin_count:
                self._target_search_phase = "patrol"
            else:
                if self._target_search_spin_start_yaw is None:
                    self._target_search_spin_start_yaw = robot.theta
                step = math.radians(
                    max(
                        1.0,
                        float(
                            self.get_parameter(
                                "target_search_initial_spin_step_deg"
                            ).value
                        ),
                    )
                )
                heading = self._target_search_spin_start_yaw + step * (
                    self._target_search_spin_index + 1
                )
                heading = self._apply_goal_heading_offset(wrap_angle(heading))
                return Pose2D(x=robot.x, y=robot.y, theta=heading)

        points = self._target_search_points()
        if not points:
            return None
        if self._target_search_index is None:
            self._target_search_index = min(
                range(len(points)),
                key=lambda index: math.hypot(
                    points[index][0] - robot.x,
                    points[index][1] - robot.y,
                ),
            )

        index = self._target_search_index % len(points)
        x, y = points[index]
        x, y = self._clamp_goal_to_arena(x, y)
        center_x = float(self.get_parameter("target_search_center_x_m").value)
        center_y = float(self.get_parameter("target_search_center_y_m").value)
        heading = math.atan2(center_y - y, center_x - x)
        heading = self._apply_goal_heading_offset(heading)
        return Pose2D(x=x, y=y, theta=heading)

    def _target_search_spin_count(self) -> int:
        step_deg = max(
            1.0,
            float(self.get_parameter("target_search_initial_spin_step_deg").value),
        )
        return max(1, int(math.ceil(360.0 / step_deg)))

    def _begin_target_search_dwell(self, goal: Pose2D) -> None:
        dwell_sec = max(0.0, float(self.get_parameter("target_search_dwell_sec").value))
        self._target_search_dwell_goal = goal
        self._target_search_dwell_phase = self._target_search_phase
        self._target_search_dwell_until_sec = self._now_sec() + dwell_sec
        self._publish_stop_cmd()

    def _finish_target_search_dwell(self) -> None:
        phase = self._target_search_dwell_phase
        self._target_search_dwell_until_sec = 0.0
        self._target_search_dwell_phase = None
        self._target_search_dwell_goal = None
        if phase == "initial_spin":
            self._target_search_spin_index += 1
            if self._target_search_spin_index >= self._target_search_spin_count():
                self._target_search_phase = "patrol"
        elif phase == "patrol":
            self._advance_target_search_index()

    def _advance_target_search_after_goal(self) -> None:
        if self._target_search_phase == "initial_spin":
            self._target_search_spin_index += 1
            if self._target_search_spin_index >= self._target_search_spin_count():
                self._target_search_phase = "patrol"
            return
        self._advance_target_search_index()


    def _target_search_points(self) -> list[tuple[float, float]]:
        radius = max(0.0, float(self.get_parameter("target_search_radius_m").value))
        if radius <= 0.0:
            return []
        center_x = float(self.get_parameter("target_search_center_x_m").value)
        center_y = float(self.get_parameter("target_search_center_y_m").value)
        diagonal = radius / math.sqrt(2.0)
        offsets = [
            (radius, 0.0),
            (diagonal, diagonal),
            (0.0, radius),
            (-diagonal, diagonal),
            (-radius, 0.0),
            (-diagonal, -diagonal),
            (0.0, -radius),
            (diagonal, -diagonal),
        ]
        return [(center_x + dx, center_y + dy) for dx, dy in offsets]

    def _advance_target_search_index(self) -> None:
        points = self._target_search_points()
        if not points:
            self._target_search_index = None
            return
        if self._target_search_index is None:
            self._target_search_index = 0
            return
        self._target_search_index = (self._target_search_index + 1) % len(points)
        if self._target_search_index == 0:
            self._target_search_lap_count += 1

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
        now_sec = self._now_sec()
        self._prune_tracked_targets(now_sec)
        lock_distance = max(
            0.0,
            float(self.get_parameter("target_lock_distance_m").value),
        )
        locked_selection = self._target_lock.select(
            candidate_pose=None,
            candidate_stamp_sec=None,
            robot_pose=robot,
            lock_distance_m=lock_distance,
        )
        if locked_selection is not None:
            self._selected_target_distance_m = locked_selection.distance_m
            return TrackedTarget(
                pose=locked_selection.pose,
                stamp_sec=locked_selection.stamp_sec,
                last_seen_sec=now_sec,
            )

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

        selection = self._target_lock.select(
            candidate_pose=selected.pose,
            candidate_stamp_sec=selected.stamp_sec,
            robot_pose=robot,
            lock_distance_m=lock_distance,
        )
        assert selection is not None
        self._selected_target_distance_m = selection.distance_m
        if selection.locked:
            self.get_logger().info(
                "target locked at "
                f"{selection.distance_m:.3f}m "
                f"(threshold={lock_distance:.3f}m)"
            )
        return TrackedTarget(
            pose=selection.pose,
            stamp_sec=selection.stamp_sec,
            last_seen_sec=now_sec,
            seen_count=selected.seen_count,
        )

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
            gx, gy = self._clamp_goal_to_arena(gx, gy)
            heading = math.atan2(target.y - gy, target.x - gx)
        else:
            gx = target.x
            gy = target.y
            gx, gy = self._clamp_goal_to_arena(gx, gy)
            heading = math.atan2(dy, dx) if target_distance > 1e-6 else robot.theta

        heading = self._apply_goal_heading_offset(heading)
        return Pose2D(x=gx, y=gy, theta=heading)

    def _apply_goal_heading_offset(self, heading: float) -> float:
        offset_deg = float(self.get_parameter("goal_heading_offset_deg").value)
        if abs(offset_deg) <= 1e-9:
            return heading
        return wrap_angle(heading + math.radians(offset_deg))

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

    def _send_goal(
        self,
        goal: Pose2D,
        purpose: str = "target",
    ) -> bool:
        if self._active_goal_sequence is not None:
            self._publish_status(
                "waiting_for_active_goal",
                active_goal_purpose=self._active_goal_purpose,
                queued_goal_purpose=purpose,
            )
            return False
        if not self._nav_client.wait_for_server(timeout_sec=self._nav_server_wait_sec):
            if not self._warned_nav_server_unavailable:
                self.get_logger().warn("Nav2 NavigateToPose action server is unavailable")
                self._warned_nav_server_unavailable = True
            self._publish_status("nav2_server_unavailable", goal=goal)
            return False

        self._warned_nav_server_unavailable = False
        goal_msg = NavigateToPose.Goal()
        goal_msg.pose = self._make_pose_stamped(goal)

        self._goal_sequence += 1
        sequence = self._goal_sequence
        self._active_goal_sequence = sequence
        self._active_goal_handle = None
        self._active_goal_purpose = purpose
        self._cancel_pending_goal = False
        self._last_sent_goal = goal
        self._nav_state = "sending_goal"
        self._publish_status("sending_goal", goal=goal, goal_purpose=purpose)

        future = self._nav_client.send_goal_async(goal_msg)
        future.add_done_callback(
            lambda done_future: self._on_goal_response(
                done_future, sequence, goal, purpose
            )
        )
        return True

    def _on_goal_response(
        self, future, sequence: int, goal: Pose2D, purpose: str
    ) -> None:
        if sequence != self._active_goal_sequence:
            return
        try:
            goal_handle = future.result()
        except Exception as exc:  # noqa: BLE001 - report action-client failures.
            self._active_goal_sequence = None
            self._active_goal_purpose = None
            self._nav_state = "goal_send_failed"
            self._last_sent_goal = None
            self._publish_status(
                "goal_send_failed",
                error=str(exc),
                goal=goal,
                goal_purpose=purpose,
            )
            self._handle_navigation_failure(purpose, f"goal_send_failed:{exc}")
            return

        if not goal_handle.accepted:
            self._nav_state = "goal_rejected"
            self._active_goal_sequence = None
            self._active_goal_handle = None
            self._active_goal_purpose = None
            self._cancel_pending_goal = False
            self._last_sent_goal = None
            self._publish_status(
                "goal_rejected", goal=goal, goal_purpose=purpose
            )
            self._handle_navigation_failure(purpose, "goal_rejected")
            return

        self._active_goal_handle = goal_handle
        if self._cancel_pending_goal:
            self._cancel_pending_goal = False
            self._cancel_active_goal("pending_capture_event")
            return
        self._nav_state = "goal_active"
        self._publish_status("goal_active", goal=goal, goal_purpose=purpose)
        result_future = goal_handle.get_result_async()
        result_future.add_done_callback(
            lambda done_future: self._on_goal_result(
                done_future, sequence, goal, purpose
            )
        )

    def _on_goal_result(
        self, future, sequence: int, goal: Pose2D, purpose: str
    ) -> None:
        if sequence != self._active_goal_sequence:
            return
        self._active_goal_sequence = None
        self._active_goal_handle = None
        self._active_goal_purpose = None
        self._cancel_pending_goal = False
        try:
            result = future.result()
        except Exception as exc:  # noqa: BLE001 - report action-client failures.
            self._nav_state = "goal_result_failed"
            self._last_sent_goal = None
            self._publish_status(
                "goal_result_failed",
                error=str(exc),
                goal=goal,
                goal_purpose=purpose,
            )
            self._handle_navigation_failure(
                purpose,
                f"goal_result_failed:{exc}",
            )
            return

        status_name = _goal_status_name(int(result.status))
        self._nav_state = status_name
        self._publish_status(
            status_name,
            goal=goal,
            goal_purpose=purpose,
        )
        if result.status != GoalStatus.STATUS_SUCCEEDED:
            self._last_sent_goal = None
            self._handle_navigation_failure(purpose, status_name)
            return

        if purpose == "target":
            self._publish_mission_event("target_reached")
        elif purpose == "search":
            self._begin_target_search_dwell(goal)
            self._last_sent_goal = None
        elif (
            purpose == "storage_approach"
            and self._storage_phase == StoragePhase.APPROACHING
        ):
            self._storage_nav_retry_count = 0
            self._set_storage_phase(StoragePhase.ENTERING)
        elif (
            purpose == "storage_enter"
            and self._storage_phase == StoragePhase.ENTERING
        ):
            verify_timeout = max(
                0.0,
                float(
                    self.get_parameter("storage_verify_timeout_sec").value
                ),
            )
            self._storage_verify_deadline_sec = self._now_sec() + verify_timeout
            self._set_storage_phase(StoragePhase.VERIFYING_INSIDE)

    def _handle_navigation_failure(self, purpose: str, reason: str) -> None:
        if (
            purpose in ("storage_approach", "storage_enter")
            and self._storage_phase
            not in (StoragePhase.COMPLETE, StoragePhase.FAILED)
        ):
            self._retry_storage_navigation(purpose, reason)
            return
        if purpose == "search":
            self._advance_target_search_after_goal()
            self._nav_state = f"search_retry_after_{reason}"
            self._last_sent_goal = None
            return
        if purpose == "target":
            self._send_capture_arm(False, f"target_navigation_failure:{reason}")
            self._send_gripper(GripperCommand.CLOSE, "target_navigation_failure")
            self._gate_open_latched = False
        self._last_sent_goal = None

    def _cancel_active_goal(self, reason: str) -> None:
        goal_handle = self._active_goal_handle
        if goal_handle is None:
            if self._active_goal_sequence is not None:
                self._cancel_pending_goal = True
            return
        self._active_goal_handle = None
        self._active_goal_sequence = None
        self._active_goal_purpose = None
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
        if self._active_goal_purpose == "search":
            return
        if self._selected_target_distance_m is None:
            return
        open_distance = max(
            0.0,
            float(self.get_parameter("gate_open_distance_m").value),
        )
        if self._gate_open_latched:
            self._send_gripper(GripperCommand.OPEN, "gate_open_latched")
            self._send_capture_arm(True, "gate_open_latched")
            return
        if self._selected_target_distance_m <= open_distance:
            self._gate_open_latched = True
            self._send_gripper(GripperCommand.OPEN, "target_within_gate_open_distance")
            self._send_capture_arm(True, "target_within_gate_open_distance")

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

    def _send_capture_arm(
        self, armed: bool, reason: str, *, force: bool = False
    ) -> None:
        if not self._control_capture_arm:
            return
        if self._capture_arm_armed == armed and not force:
            return
        msg = Bool()
        msg.data = armed
        self._capture_arm_pub.publish(msg)
        self._capture_arm_armed = armed
        state = "ON" if armed else "OFF"
        self.get_logger().info(f"capture arm {state}: {reason}")

    def _publish_status(self, state: str, **extra: Any) -> None:
        payload: dict[str, Any] = {
            "state": state,
            "nav_state": self._nav_state,
            "active_goal_purpose": self._active_goal_purpose,
            "send_nav2_goal": self._send_nav2_goal,
            "captured_object_count": self._captured_object_count,
            "storage_trigger_count": max(
                1, int(self.get_parameter("storage_trigger_count").value)
            ),
            "storage_phase": self._storage_phase.value,
            "target_selection_mode": self._target_selection_mode(),
            "target_locked": self._target_lock.active,
            "target_lock_distance_m": max(
                0.0,
                float(self.get_parameter("target_lock_distance_m").value),
            ),
            "target_search_enabled": bool(
                self.get_parameter("target_search_enabled").value
            ),
            "target_seen_since_start": self._has_seen_target_since_start,
            "target_search_phase": self._target_search_phase,
            "target_search_spin_index": self._target_search_spin_index,
            "target_search_dwell_active": self._target_search_dwell_until_sec
            > self._now_sec(),
            "target_search_index": self._target_search_index,
            "target_search_lap_count": self._target_search_lap_count,
            "tracked_target_count": len(self._tracked_targets),
            "gate_state": self._gate_state,
            "gate_open_latched": self._gate_open_latched,
            "capture_arm_armed": self._capture_arm_armed,
        }
        if self._storage_plan is not None:
            payload["storage_entry_direction"] = (
                self._storage_plan.entry_direction.value
            )
            payload["storage_exit_direction"] = self._storage_plan.exit_direction
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

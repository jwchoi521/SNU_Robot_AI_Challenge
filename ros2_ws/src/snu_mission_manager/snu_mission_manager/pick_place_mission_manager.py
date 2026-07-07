from __future__ import annotations

from enum import Enum
from math import cos, sin

import rclpy
from geometry_msgs.msg import PoseStamped
from rclpy.node import Node
from snu_robot_interfaces.msg import GripperCommand, GripperState
from std_msgs.msg import String


class MissionState(str, Enum):
    IDLE = "IDLE"
    SEARCH_TARGET = "SEARCH_TARGET"
    NAV_TO_TARGET = "NAV_TO_TARGET"
    FINAL_ALIGN = "FINAL_ALIGN"
    CAPTURE_TARGET = "CAPTURE_TARGET"
    VERIFY_CAPTURE = "VERIFY_CAPTURE"
    NAV_TO_DROP_ZONE = "NAV_TO_DROP_ZONE"
    RELEASE_TARGET = "RELEASE_TARGET"
    BACK_OFF = "BACK_OFF"
    DONE = "DONE"


class PickPlaceMissionManager(Node):
    """Skeleton state machine for target pickup and fixed drop-off."""

    def __init__(self) -> None:
        super().__init__("pick_place_mission_manager")

        self.declare_parameter("auto_start", False)
        self.declare_parameter("target_pose_topic", "/target_pose_map")
        self.declare_parameter("nav_goal_topic", "/mission/nav_goal")
        self.declare_parameter("mission_event_topic", "/mission/event")
        self.declare_parameter("state_topic", "/mission/state")
        self.declare_parameter("gripper_command_topic", "/gripper/command")
        self.declare_parameter("gripper_state_topic", "/gripper/state")
        self.declare_parameter("drop_frame", "map")
        self.declare_parameter("drop_x", 0.0)
        self.declare_parameter("drop_y", 0.0)
        self.declare_parameter("drop_yaw", 0.0)
        self.declare_parameter("drop_pose_configured", False)

        self._state = (
            MissionState.SEARCH_TARGET
            if bool(self.get_parameter("auto_start").value)
            else MissionState.IDLE
        )
        self._latest_target: PoseStamped | None = None
        self._drop_pose_configured = bool(
            self.get_parameter("drop_pose_configured").value
        )

        self._nav_goal_pub = self.create_publisher(
            PoseStamped,
            str(self.get_parameter("nav_goal_topic").value),
            10,
        )
        self._state_pub = self.create_publisher(
            String,
            str(self.get_parameter("state_topic").value),
            10,
        )
        self._gripper_pub = self.create_publisher(
            GripperCommand,
            str(self.get_parameter("gripper_command_topic").value),
            10,
        )
        self._target_sub = self.create_subscription(
            PoseStamped,
            str(self.get_parameter("target_pose_topic").value),
            self._on_target_pose,
            10,
        )
        self._event_sub = self.create_subscription(
            String,
            str(self.get_parameter("mission_event_topic").value),
            self._on_event,
            10,
        )
        self._gripper_state_sub = self.create_subscription(
            GripperState,
            str(self.get_parameter("gripper_state_topic").value),
            self._on_gripper_state,
            10,
        )
        self._timer = self.create_timer(1.0, self._publish_state)
        self.get_logger().info(f"Mission manager started in {self._state.value}")

    def _on_target_pose(self, msg: PoseStamped) -> None:
        self._latest_target = msg
        if self._state in (MissionState.IDLE, MissionState.SEARCH_TARGET):
            self._transition(MissionState.NAV_TO_TARGET)
            self._publish_nav_goal(msg)

    def _on_event(self, msg: String) -> None:
        event = msg.data.strip().lower()
        if event == "start":
            self._transition(MissionState.SEARCH_TARGET)
        elif event == "target_reached" and self._state == MissionState.NAV_TO_TARGET:
            self._transition(MissionState.FINAL_ALIGN)
            self._send_gripper(GripperCommand.OPEN)
        elif event == "target_inside" and self._state == MissionState.FINAL_ALIGN:
            self._transition(MissionState.CAPTURE_TARGET)
            self._send_gripper(GripperCommand.CLOSE)
            self._transition(MissionState.VERIFY_CAPTURE)
        elif event == "drop_reached" and self._state == MissionState.NAV_TO_DROP_ZONE:
            self._transition(MissionState.RELEASE_TARGET)
            self._send_gripper(GripperCommand.OPEN)
            self._transition(MissionState.BACK_OFF)
        elif event == "backoff_done" and self._state == MissionState.BACK_OFF:
            self._transition(MissionState.DONE)
        elif event == "reset":
            self._latest_target = None
            self._transition(MissionState.IDLE)

    def _on_gripper_state(self, msg: GripperState) -> None:
        if self._state != MissionState.VERIFY_CAPTURE:
            return
        if not msg.has_object:
            return
        if not self._drop_pose_configured:
            self.get_logger().warn("Captured target, but drop pose is not configured")
            return
        self._transition(MissionState.NAV_TO_DROP_ZONE)
        self._publish_nav_goal(self._drop_pose())

    def _send_gripper(self, command: int) -> None:
        msg = GripperCommand()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.command = command
        msg.effort = 0.5
        self._gripper_pub.publish(msg)

    def _publish_nav_goal(self, pose: PoseStamped) -> None:
        self._nav_goal_pub.publish(pose)

    def _drop_pose(self) -> PoseStamped:
        yaw = float(self.get_parameter("drop_yaw").value)
        pose = PoseStamped()
        pose.header.stamp = self.get_clock().now().to_msg()
        pose.header.frame_id = str(self.get_parameter("drop_frame").value)
        pose.pose.position.x = float(self.get_parameter("drop_x").value)
        pose.pose.position.y = float(self.get_parameter("drop_y").value)
        pose.pose.orientation.z = sin(yaw / 2.0)
        pose.pose.orientation.w = cos(yaw / 2.0)
        return pose

    def _transition(self, state: MissionState) -> None:
        if state == self._state:
            return
        self.get_logger().info(f"Mission state: {self._state.value} -> {state.value}")
        self._state = state
        self._publish_state()

    def _publish_state(self) -> None:
        msg = String()
        msg.data = self._state.value
        self._state_pub.publish(msg)


def main() -> None:
    rclpy.init()
    node = PickPlaceMissionManager()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()

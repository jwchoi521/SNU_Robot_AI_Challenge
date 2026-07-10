from __future__ import annotations

import json
import math
from dataclasses import dataclass
from typing import Any

import rclpy
from geometry_msgs.msg import PoseStamped
from rclpy.node import Node
from sensor_msgs.msg import PointCloud2
from std_msgs.msg import String

from .core import yaw_from_quaternion


@dataclass
class TimedValue:
    data: Any
    arrival_sec: float


class MappingDebugMonitorNode(Node):
    """Print and publish a compact live view of mapping/localization state."""

    def __init__(self) -> None:
        super().__init__("mapping_debug_monitor_node")
        self.declare_parameter("robot_pose_topic", "/robot_pose_map")
        self.declare_parameter("object_pose_topic", "/object_pose_map")
        self.declare_parameter("approach_goal_topic", "/approach_goal")
        self.declare_parameter("semantic_cloud_topic", "/semantic_obstacles")
        self.declare_parameter("localizer_status_topic", "/four_wall_localizer/status")
        self.declare_parameter("detections_topic", "/detections_json")
        self.declare_parameter("debug_topic", "/robot_nav_stack/debug_state")
        self.declare_parameter("log_period_sec", 1.0)
        self.declare_parameter("stale_after_sec", 2.0)
        self.declare_parameter("print_to_console", True)
        self.declare_parameter("publish_debug_json", True)

        self.stale_after_sec = float(self.get_parameter("stale_after_sec").value)
        self.print_to_console = bool(self.get_parameter("print_to_console").value)
        self.publish_debug_json = bool(self.get_parameter("publish_debug_json").value)

        self.robot_pose: TimedValue | None = None
        self.object_pose: TimedValue | None = None
        self.approach_goal: TimedValue | None = None
        self.semantic_cloud: TimedValue | None = None
        self.localizer_status: TimedValue | None = None
        self.detection: TimedValue | None = None
        self.detections_since_last_log = 0
        self.objects_since_last_log = 0

        robot_pose_topic = str(self.get_parameter("robot_pose_topic").value)
        object_pose_topic = str(self.get_parameter("object_pose_topic").value)
        approach_goal_topic = str(self.get_parameter("approach_goal_topic").value)
        semantic_cloud_topic = str(self.get_parameter("semantic_cloud_topic").value)
        localizer_status_topic = str(self.get_parameter("localizer_status_topic").value)
        detections_topic = str(self.get_parameter("detections_topic").value)
        debug_topic = str(self.get_parameter("debug_topic").value)

        self.create_subscription(PoseStamped, robot_pose_topic, self._on_robot_pose, 20)
        self.create_subscription(PoseStamped, object_pose_topic, self._on_object_pose, 20)
        self.create_subscription(PoseStamped, approach_goal_topic, self._on_approach_goal, 10)
        self.create_subscription(PointCloud2, semantic_cloud_topic, self._on_semantic_cloud, 10)
        self.create_subscription(String, localizer_status_topic, self._on_localizer_status, 10)
        self.create_subscription(String, detections_topic, self._on_detection, 20)
        self.debug_pub = self.create_publisher(String, debug_topic, 10)

        self.create_timer(float(self.get_parameter("log_period_sec").value), self._publish_summary)
        self.get_logger().info(
            "debug monitor enabled: "
            f"robot={robot_pose_topic}, object={object_pose_topic}, cloud={semantic_cloud_topic}, "
            f"debug={debug_topic}"
        )

    def _on_robot_pose(self, msg: PoseStamped) -> None:
        self.robot_pose = TimedValue(self._pose_to_dict(msg), self._now_sec())

    def _on_object_pose(self, msg: PoseStamped) -> None:
        self.object_pose = TimedValue(self._pose_to_dict(msg), self._now_sec())
        self.objects_since_last_log += 1

    def _on_approach_goal(self, msg: PoseStamped) -> None:
        self.approach_goal = TimedValue(self._pose_to_dict(msg), self._now_sec())

    def _on_semantic_cloud(self, msg: PointCloud2) -> None:
        point_count = int(msg.width) * max(1, int(msg.height))
        payload = {
            "frame_id": msg.header.frame_id,
            "stamp": self._stamp_to_sec(msg.header.stamp),
            "points": point_count,
        }
        self.semantic_cloud = TimedValue(payload, self._now_sec())

    def _on_localizer_status(self, msg: String) -> None:
        try:
            payload = json.loads(msg.data)
        except json.JSONDecodeError:
            payload = {"raw": msg.data}
        self.localizer_status = TimedValue(payload, self._now_sec())

    def _on_detection(self, msg: String) -> None:
        try:
            payload = json.loads(msg.data)
        except json.JSONDecodeError:
            payload = {"raw": msg.data}
        self.detection = TimedValue(payload, self._now_sec())
        self.detections_since_last_log += 1

    def _publish_summary(self) -> None:
        state = self._state_dict()
        if self.publish_debug_json:
            out = String()
            out.data = json.dumps(state, separators=(",", ":"), sort_keys=True)
            self.debug_pub.publish(out)

        if self.print_to_console:
            self.get_logger().info(self._format_state(state))

        self.detections_since_last_log = 0
        self.objects_since_last_log = 0

    def _state_dict(self) -> dict[str, Any]:
        return {
            "stamp": self._now_sec(),
            "robot_pose": self._value_state(self.robot_pose),
            "object_pose": self._value_state(self.object_pose),
            "approach_goal": self._value_state(self.approach_goal),
            "semantic_obstacles": self._value_state(self.semantic_cloud),
            "localizer": self._value_state(self.localizer_status),
            "latest_detection": self._value_state(self.detection),
            "counts_since_last_log": {
                "detections": self.detections_since_last_log,
                "localized_objects": self.objects_since_last_log,
            },
        }

    def _value_state(self, timed: TimedValue | None) -> dict[str, Any]:
        if timed is None:
            return {"available": False}
        age = max(0.0, self._now_sec() - timed.arrival_sec)
        return {
            "available": True,
            "age_sec": age,
            "stale": age > self.stale_after_sec,
            "data": timed.data,
        }

    def _format_state(self, state: dict[str, Any]) -> str:
        robot = self._format_pose_state("robot", state["robot_pose"])
        obj = self._format_pose_state("object", state["object_pose"])
        goal = self._format_pose_state("goal", state["approach_goal"])
        obstacles = self._format_cloud_state(state["semantic_obstacles"])
        localizer = self._format_localizer_state(state["localizer"])
        detection = self._format_detection_state(state["latest_detection"])
        counts = state["counts_since_last_log"]
        return (
            f"{robot} | {obj} | {goal} | {obstacles} | {localizer} | {detection} | "
            f"new: det={counts['detections']}, obj={counts['localized_objects']}"
        )

    def _format_pose_state(self, name: str, state: dict[str, Any]) -> str:
        if not state["available"]:
            return f"{name}=missing"
        pose = state["data"]
        stale = " stale" if state["stale"] else ""
        return (
            f"{name}=({pose['x']:.2f},{pose['y']:.2f},{pose['yaw_deg']:.1f}deg"
            f" {state['age_sec']:.1f}s{stale})"
        )

    @staticmethod
    def _format_cloud_state(state: dict[str, Any]) -> str:
        if not state["available"]:
            return "obstacles=missing"
        data = state["data"]
        stale = " stale" if state["stale"] else ""
        return f"obstacles={int(data['points'])}pts {state['age_sec']:.1f}s{stale}"

    @staticmethod
    def _format_localizer_state(state: dict[str, Any]) -> str:
        if not state["available"]:
            return "localizer=missing"
        data = state["data"]
        if "ok" not in data:
            return f"localizer=raw {state['age_sec']:.1f}s"
        if not data["ok"]:
            return f"localizer=bad:{data.get('reason', 'unknown')} {state['age_sec']:.1f}s"
        score = float(data.get("total_score", math.nan))
        walls = int(data.get("visible_walls", 0))
        ambiguous = bool(data.get("ambiguous_without_prior", False))
        amb = ",amb" if ambiguous else ""
        return f"localizer=ok score={score:.3f},walls={walls}{amb} {state['age_sec']:.1f}s"

    @staticmethod
    def _format_detection_state(state: dict[str, Any]) -> str:
        if not state["available"]:
            return "detection=missing"
        data = state["data"]
        if "bbox" not in data:
            return f"detection=raw {state['age_sec']:.1f}s"
        bbox = data["bbox"]
        return (
            f"detection={data.get('object_type', '?')} conf={float(data.get('confidence', 0.0)):.2f} "
            f"bbox=({float(bbox['cx']):.0f},{float(bbox['cy']):.0f},"
            f"{float(bbox['w']):.0f},{float(bbox['h']):.0f}) {state['age_sec']:.1f}s"
        )

    def _pose_to_dict(self, msg: PoseStamped) -> dict[str, float | str]:
        q = msg.pose.orientation
        return {
            "frame_id": msg.header.frame_id,
            "stamp": self._stamp_to_sec(msg.header.stamp),
            "x": float(msg.pose.position.x),
            "y": float(msg.pose.position.y),
            "yaw_rad": yaw_from_quaternion(q.x, q.y, q.z, q.w),
            "yaw_deg": math.degrees(yaw_from_quaternion(q.x, q.y, q.z, q.w)),
        }

    def _now_sec(self) -> float:
        return self.get_clock().now().nanoseconds * 1e-9

    @staticmethod
    def _stamp_to_sec(stamp) -> float:
        return float(stamp.sec) + float(stamp.nanosec) * 1e-9


def main() -> None:
    rclpy.init()
    node = MappingDebugMonitorNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()

from __future__ import annotations

from math import cos, isfinite, radians, sin

import rclpy
from geometry_msgs.msg import PoseStamped
from rclpy.node import Node
from snu_robot_interfaces.msg import DetectedTarget, DetectedTargetArray


class TargetPoseProjector(Node):
    """Project confirmed target detections into a base-frame target pose."""

    def __init__(self) -> None:
        super().__init__("target_pose_projector")

        self.declare_parameter("input_topic", "/perception/targets")
        self.declare_parameter("output_topic", "/target_pose_base")
        self.declare_parameter("base_frame", "base_link")
        self.declare_parameter("bearing_positive_is_left", False)
        self.declare_parameter("min_distance_m", 0.10)
        self.declare_parameter("max_distance_m", 2.50)
        self.declare_parameter("prefer_closest", True)

        input_topic = self.get_parameter("input_topic").value
        output_topic = self.get_parameter("output_topic").value

        self._base_frame = str(self.get_parameter("base_frame").value)
        self._bearing_positive_is_left = bool(
            self.get_parameter("bearing_positive_is_left").value
        )
        self._min_distance_m = float(self.get_parameter("min_distance_m").value)
        self._max_distance_m = float(self.get_parameter("max_distance_m").value)
        self._prefer_closest = bool(self.get_parameter("prefer_closest").value)

        self._publisher = self.create_publisher(PoseStamped, str(output_topic), 10)
        self._subscription = self.create_subscription(
            DetectedTargetArray,
            str(input_topic),
            self._on_targets,
            10,
        )

        self.get_logger().info(
            f"Projecting targets from {input_topic} to {output_topic}"
        )

    def _on_targets(self, msg: DetectedTargetArray) -> None:
        target = self._select_target(msg.targets)
        if target is None:
            return

        pose = self._target_to_pose(target)
        pose.header.stamp = msg.header.stamp
        pose.header.frame_id = self._base_frame
        self._publisher.publish(pose)

    def _select_target(
        self, targets: list[DetectedTarget] | tuple[DetectedTarget, ...]
    ) -> DetectedTarget | None:
        candidates = [
            target
            for target in targets
            if target.pick_allowed
            and target.target_confirmed
            and target.has_distance
            and isfinite(float(target.distance_m))
            and self._min_distance_m <= float(target.distance_m) <= self._max_distance_m
        ]
        if not candidates:
            return None

        if self._prefer_closest:
            return min(candidates, key=lambda target: float(target.distance_m))
        return max(candidates, key=lambda target: float(target.confidence))

    def _target_to_pose(self, target: DetectedTarget) -> PoseStamped:
        bearing_rad = radians(float(target.bearing_deg))
        distance_m = float(target.distance_m)

        lateral_sign = 1.0 if self._bearing_positive_is_left else -1.0
        pose = PoseStamped()
        pose.pose.position.x = distance_m * cos(bearing_rad)
        pose.pose.position.y = lateral_sign * distance_m * sin(bearing_rad)
        pose.pose.position.z = 0.0
        pose.pose.orientation.w = 1.0
        return pose


def main() -> None:
    rclpy.init()
    node = TargetPoseProjector()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()

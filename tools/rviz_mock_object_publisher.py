#!/usr/bin/env python3
"""
RViz 클릭으로 가짜 object pose를 발행하는 테스트 도구.

실제 카메라/YOLO 없이 Publish Point로 찍은 위치를 object pose 토픽에
반복 발행해 object localization 이후 경로/장애물 처리를 확인할 때 쓴다.
"""

import rclpy
from geometry_msgs.msg import PointStamped, PoseStamped
from rclpy.node import Node


class RvizMockObjectPublisher(Node):
    def __init__(self) -> None:
        super().__init__("rviz_mock_object_publisher")
        self.declare_parameter("clicked_point_topic", "/clicked_point")
        self.declare_parameter("object_pose_topic", "/object_pose_map")
        self.declare_parameter("publish_hz", 2.0)

        self._last_point: PointStamped | None = None
        self.create_subscription(
            PointStamped,
            str(self.get_parameter("clicked_point_topic").value),
            self._on_point,
            10,
        )
        self._publisher = self.create_publisher(
            PoseStamped,
            str(self.get_parameter("object_pose_topic").value),
            10,
        )
        publish_hz = max(0.1, float(self.get_parameter("publish_hz").value))
        self.create_timer(1.0 / publish_hz, self._publish)
        self.get_logger().info(
            "select RViz Publish Point and click the map to create a mock object"
        )

    def _on_point(self, msg: PointStamped) -> None:
        self._last_point = msg
        self.get_logger().info(
            f"mock object set to x={msg.point.x:.3f}, y={msg.point.y:.3f}"
        )

    def _publish(self) -> None:
        if self._last_point is None:
            return

        pose = PoseStamped()
        pose.header.stamp = self.get_clock().now().to_msg()
        pose.header.frame_id = "map"
        pose.pose.position.x = float(self._last_point.point.x)
        pose.pose.position.y = float(self._last_point.point.y)
        pose.pose.position.z = 0.0
        pose.pose.orientation.w = 1.0
        self._publisher.publish(pose)


def main() -> None:
    rclpy.init()
    node = RvizMockObjectPublisher()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()

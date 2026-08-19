#!/usr/bin/env python3
"""
RViz/Nav2 경로 테스트용 가짜 localization 노드.

실제 로봇, LiDAR, EKF 없이 RViz의 2D Pose Estimate 값을 받아
map -> odom -> base_link TF를 계속 발행해 Nav2가 현재 로봇 위치를
알고 있는 것처럼 만들어준다.
"""

import rclpy
from geometry_msgs.msg import PoseWithCovarianceStamped, TransformStamped
from rclpy.node import Node
from tf2_ros import TransformBroadcaster


class RVizFakeLocalization(Node):
    def __init__(self) -> None:
        super().__init__("rviz_fake_localization")
        self.tf_broadcaster = TransformBroadcaster(self)
        self.create_subscription(
            PoseWithCovarianceStamped,
            "/initialpose",
            self.pose_callback,
            10,
        )

        # 기본 시작 위치. RViz에서 2D Pose Estimate를 찍으면 이 값이 갱신된다.
        self.x = 0.0
        self.y = 0.0
        self.qx = 0.0
        self.qy = 0.0
        self.qz = 0.0
        self.qw = 1.0

        # Nav2가 오래된 TF라고 판단하지 않도록 20Hz로 계속 발행한다.
        self.create_timer(0.05, self.publish_tf)
        self.get_logger().info(
            "fake localization started. Use RViz '2D Pose Estimate' to move the robot."
        )

    def pose_callback(self, msg: PoseWithCovarianceStamped) -> None:
        self.x = float(msg.pose.pose.position.x)
        self.y = float(msg.pose.pose.position.y)
        self.qx = float(msg.pose.pose.orientation.x)
        self.qy = float(msg.pose.pose.orientation.y)
        self.qz = float(msg.pose.pose.orientation.z)
        self.qw = float(msg.pose.pose.orientation.w)
        self.get_logger().info(f"fake robot pose: x={self.x:.2f}, y={self.y:.2f}")

    def publish_tf(self) -> None:
        now = self.get_clock().now().to_msg()

        # RViz에서 지정한 위치를 map -> odom 변환으로 반영한다.
        map_to_odom = TransformStamped()
        map_to_odom.header.stamp = now
        map_to_odom.header.frame_id = "map"
        map_to_odom.child_frame_id = "odom"
        map_to_odom.transform.translation.x = self.x
        map_to_odom.transform.translation.y = self.y
        map_to_odom.transform.translation.z = 0.0
        map_to_odom.transform.rotation.x = self.qx
        map_to_odom.transform.rotation.y = self.qy
        map_to_odom.transform.rotation.z = self.qz
        map_to_odom.transform.rotation.w = self.qw
        self.tf_broadcaster.sendTransform(map_to_odom)

        # 테스트에서는 실제 odometry가 없으므로 base_link를 odom 원점에 고정한다.
        odom_to_base = TransformStamped()
        odom_to_base.header.stamp = now
        odom_to_base.header.frame_id = "odom"
        odom_to_base.child_frame_id = "base_link"
        odom_to_base.transform.translation.x = 0.0
        odom_to_base.transform.translation.y = 0.0
        odom_to_base.transform.translation.z = 0.0
        odom_to_base.transform.rotation.w = 1.0
        self.tf_broadcaster.sendTransform(odom_to_base)


def main() -> None:
    rclpy.init()
    node = RVizFakeLocalization()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()

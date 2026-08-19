#!/usr/bin/env python3
"""
Nav2 경로 생성/장애물 회피를 RViz에서 순차 확인하는 테스트 도구.

실제 로봇 센서 없이 42개 후보 지점 중 선택한 target을 /goal_pose로 보내고,
선택 target을 제외한 나머지 지점은 /semantic_obstacle_cloud 장애물로 발행한다.
따라서 새 map, footprint, inflation_radius, semantic obstacle 설정이
RViz에서 의도대로 보이는지 빠르게 검증할 수 있다.
"""

import struct
import threading
import time

import rclpy
from geometry_msgs.msg import PoseStamped, PoseWithCovarianceStamped
from nav2_msgs.srv import ClearEntireCostmap
from rclpy.node import Node
from sensor_msgs.msg import PointCloud2, PointField


def _expanded_points(x: float, y: float, radius: float) -> list[tuple[float, float, float]]:
    if radius <= 0.0:
        return [(x + 0.001, y + 0.001, 0.0)]

    points = []
    spacing = 0.015
    steps = int(radius / spacing)
    for i in range(-steps, steps + 1):
        for j in range(-steps, steps + 1):
            dx = i * spacing
            dy = j * spacing
            if dx * dx + dy * dy <= radius * radius:
                # Nav2가 센서 원점과 정확히 겹친 점을 필터링하지 않도록 1mm 보정한다.
                points.append((x + dx + 0.001, y + dy + 0.001, 0.0))

    if not points:
        points.append((x + 0.001, y + 0.001, 0.0))
    return points


def _make_cloud(stamp, frame_id: str, points: list[tuple[float, float, float]]) -> PointCloud2:
    cloud = PointCloud2()
    cloud.header.stamp = stamp
    cloud.header.frame_id = frame_id
    cloud.height = 1
    cloud.width = len(points)
    cloud.fields = [
        PointField(name="x", offset=0, datatype=PointField.FLOAT32, count=1),
        PointField(name="y", offset=4, datatype=PointField.FLOAT32, count=1),
        PointField(name="z", offset=8, datatype=PointField.FLOAT32, count=1),
    ]
    cloud.is_bigendian = False
    cloud.point_step = 12
    cloud.row_step = cloud.point_step * cloud.width
    cloud.is_dense = True
    cloud.data = b"".join(struct.pack("<fff", *point) for point in points)
    return cloud


class SequentialTester(Node):
    def __init__(self) -> None:
        super().__init__("sequential_tester")

        self.initial_pose_pub = self.create_publisher(
            PoseWithCovarianceStamped, "/initialpose", 10
        )
        self.goal_pub = self.create_publisher(PoseStamped, "/goal_pose", 10)
        self.obstacle_pub = self.create_publisher(
            PointCloud2, "/semantic_obstacle_cloud", 10
        )
        self.clear_costmap_cli = self.create_client(
            ClearEntireCostmap, "/local_costmap/clear_entirely_local_costmap"
        )

        # 4m 경기장 내부에서 반복 테스트할 후보 target 위치 42개.
        self.points = []
        for x in [-1.5, -1.0, -0.5, 0.0, 0.5, 1.0, 1.5]:
            for y in [-1.0, -0.5, 0.0, 0.5, 1.0, 1.5]:
                self.points.append((x, y))

        self.sequence_queue = []
        self.state = "IDLE"
        self.wait_start_time = 0.0
        self.current_x = 1.8
        self.current_y = -1.8
        self.initial_pose_set = False

        self.create_timer(0.1, self._timer_callback)
        self.get_logger().info("sequential Nav2 path tester initialized")

    def set_initial_pose(self, x: float, y: float) -> None:
        msg = PoseWithCovarianceStamped()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = "map"
        msg.pose.pose.position.x = float(x)
        msg.pose.pose.position.y = float(y)
        msg.pose.pose.orientation.w = 1.0
        self.initial_pose_pub.publish(msg)
        self.get_logger().info(f"teleported fake robot to ({x}, {y})")

        # 이전 위치의 local costmap 흔적이 다음 경로에 섞이지 않도록 지운다.
        if self.clear_costmap_cli.wait_for_service(timeout_sec=0.5):
            self.clear_costmap_cli.call_async(ClearEntireCostmap.Request())
            self.get_logger().info("requested local costmap clearing")

    def _timer_callback(self) -> None:
        if not self.initial_pose_set:
            self.initial_pose_set = True
            self.set_initial_pose(self.current_x, self.current_y)
            return

        if self.state == "IDLE" and self.sequence_queue:
            target = self.sequence_queue.pop(0)
            if target == "d":
                target_x, target_y = -1.7, -1.7
                exclude_idx = -1
            else:
                exclude_idx = target - 1
                target_x, target_y = self.points[exclude_idx]

            self.set_initial_pose(self.current_x, self.current_y)
            self.publish_obstacles(exclude_idx)
            self.get_logger().info(
                f"generate path: ({self.current_x}, {self.current_y})"
                f" -> ({target_x}, {target_y})"
            )
            self.publish_goal(target_x, target_y)
            self.current_x = target_x
            self.current_y = target_y
            self.wait_start_time = time.time()
            self.state = "WAITING"
            return

        if self.state == "WAITING" and time.time() - self.wait_start_time >= 3.0:
            self.get_logger().info("ready for next path")
            self.state = "IDLE"

    def publish_obstacles(self, exclude_idx: int) -> None:
        obstacle_points = []
        for i, point in enumerate(self.points):
            if i != exclude_idx:
                obstacle_points.extend(_expanded_points(point[0], point[1], 0.05))

        cloud_msg = _make_cloud(self.get_clock().now().to_msg(), "map", obstacle_points)
        self.obstacle_pub.publish(cloud_msg)

    def publish_goal(self, x: float, y: float) -> None:
        msg = PoseStamped()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = "map"
        msg.pose.position.x = float(x)
        msg.pose.position.y = float(y)
        msg.pose.orientation.w = 1.0
        self.goal_pub.publish(msg)


def user_input_thread(node: SequentialTester) -> None:
    print("=========================================")
    print("    Static Path Sequence Tester          ")
    print("=========================================")
    print("Commands:")
    print("  Input sequence (e.g. 3->9->12->d or 3,9,12,d)")
    print("  Numbers 1-42: Go to target ID")
    print("  d           : Go to drop zone (-1.7, -1.7)")
    print("  q           : Quit")
    print("=========================================")

    while rclpy.ok():
        try:
            command = input("\nEnter sequence: ").strip().lower()
        except EOFError:
            break

        if command in ["q", "quit"]:
            print("Shutting down...")
            rclpy.shutdown()
            break

        command = command.replace("->", ",")
        targets = []
        for part in command.split(","):
            part = part.strip()
            if not part:
                continue
            if part == "d":
                targets.append("d")
            elif part.isdigit() and 1 <= int(part) <= 42:
                targets.append(int(part))
            else:
                print(f"Invalid input: {part}")

        if targets:
            node.sequence_queue.extend(targets)
            print(f"Added to queue: {targets}")
            print(f"Current queue length: {len(node.sequence_queue)}")


def main() -> None:
    rclpy.init()
    node = SequentialTester()
    thread = threading.Thread(target=user_input_thread, args=(node,), daemon=True)
    thread.start()

    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == "__main__":
    main()

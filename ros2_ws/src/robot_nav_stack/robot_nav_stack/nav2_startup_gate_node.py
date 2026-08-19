from __future__ import annotations

from typing import Any

import rclpy
from nav2_msgs.srv import ManageLifecycleNodes
from nav_msgs.msg import OccupancyGrid
from rclpy.duration import Duration
from rclpy.node import Node
from rclpy.qos import DurabilityPolicy, QoSProfile, ReliabilityPolicy
from rclpy.time import Time
from tf2_ros import Buffer, TransformListener


class Nav2StartupGate(Node):
    """Activate Nav2 only after the map and map->base TF are available."""

    def __init__(self) -> None:
        super().__init__("nav2_startup_gate_node")

        self.declare_parameter("enabled", True)
        self.declare_parameter("autostart_requested", True)
        self.declare_parameter(
            "lifecycle_service", "/lifecycle_manager_navigation/manage_nodes"
        )
        self.declare_parameter("map_topic", "/map")
        self.declare_parameter("map_frame", "map")
        self.declare_parameter("base_frame", "base_link")
        self.declare_parameter("check_period_sec", 0.1)
        self.declare_parameter("ready_timeout_sec", 30.0)

        self.done = False
        self._enabled = self._param_bool("enabled")
        self._autostart_requested = self._param_bool("autostart_requested")
        if not self._enabled:
            self.get_logger().info("Nav2 startup gate disabled")
            self.done = True
            return
        if not self._autostart_requested:
            self.get_logger().info("Nav2 autostart was not requested; gate is idle")
            self.done = True
            return

        self._map_topic = str(self.get_parameter("map_topic").value)
        self._map_frame = str(self.get_parameter("map_frame").value)
        self._base_frame = str(self.get_parameter("base_frame").value)
        self._ready_timeout_sec = float(
            self.get_parameter("ready_timeout_sec").value
        )
        check_period_sec = max(
            0.05, float(self.get_parameter("check_period_sec").value)
        )
        lifecycle_service = str(self.get_parameter("lifecycle_service").value)

        self._map_ready = False
        self._startup_requested = False
        self._start_time_sec = self.get_clock().now().nanoseconds / 1e9
        self._last_wait_log_sec = 0.0

        map_qos = QoSProfile(
            depth=1,
            durability=DurabilityPolicy.TRANSIENT_LOCAL,
            reliability=ReliabilityPolicy.RELIABLE,
        )
        self.create_subscription(
            OccupancyGrid, self._map_topic, self._on_map, map_qos
        )

        self._tf_buffer = Buffer()
        self._tf_listener = TransformListener(self._tf_buffer, self)
        self._lifecycle_client = self.create_client(
            ManageLifecycleNodes, lifecycle_service
        )
        self._timer = self.create_timer(check_period_sec, self._on_timer)
        self.get_logger().info(
            "waiting to activate Nav2 until map and "
            f"{self._map_frame}->{self._base_frame} TF are ready"
        )

    def _param_bool(self, name: str) -> bool:
        value: Any = self.get_parameter(name).value
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.strip().lower() in ("1", "true", "yes", "on")
        return bool(value)

    def _on_map(self, _msg: OccupancyGrid) -> None:
        if not self._map_ready:
            self.get_logger().info(f"map ready on {self._map_topic}")
        self._map_ready = True

    def _on_timer(self) -> None:
        if self.done or self._startup_requested:
            return

        now_sec = self.get_clock().now().nanoseconds / 1e9
        elapsed_sec = now_sec - self._start_time_sec
        if self._ready_timeout_sec > 0.0 and elapsed_sec > self._ready_timeout_sec:
            self.get_logger().error(
                "Nav2 startup gate timed out before map/TF became ready; "
                "Nav2 remains inactive"
            )
            self.done = True
            return

        service_ready = self._lifecycle_client.service_is_ready()
        if not service_ready:
            self._lifecycle_client.wait_for_service(timeout_sec=0.0)
            service_ready = self._lifecycle_client.service_is_ready()

        tf_ready = self._tf_buffer.can_transform(
            self._map_frame,
            self._base_frame,
            Time(),
            timeout=Duration(seconds=0.0),
        )
        if not (self._map_ready and tf_ready and service_ready):
            if now_sec - self._last_wait_log_sec >= 2.0:
                self._last_wait_log_sec = now_sec
                self.get_logger().info(
                    "waiting for Nav2 prerequisites: "
                    f"map={self._map_ready}, tf={tf_ready}, "
                    f"lifecycle_service={service_ready}"
                )
            return

        request = ManageLifecycleNodes.Request()
        request.command = ManageLifecycleNodes.Request.STARTUP
        self._startup_requested = True
        future = self._lifecycle_client.call_async(request)
        future.add_done_callback(self._on_startup_done)
        self.get_logger().info("map/TF ready; requesting Nav2 lifecycle startup")

    def _on_startup_done(self, future) -> None:
        try:
            response = future.result()
        except Exception as exc:  # pragma: no cover - defensive ROS callback guard
            self.get_logger().error(f"Nav2 lifecycle startup request failed: {exc}")
        else:
            if response.success:
                self.get_logger().info("Nav2 lifecycle startup completed")
            else:
                self.get_logger().error("Nav2 lifecycle startup was rejected")
        self.done = True


def main(args=None) -> None:
    rclpy.init(args=args)
    node = Nav2StartupGate()
    try:
        while rclpy.ok() and not node.done:
            rclpy.spin_once(node, timeout_sec=0.1)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == "__main__":
    main()

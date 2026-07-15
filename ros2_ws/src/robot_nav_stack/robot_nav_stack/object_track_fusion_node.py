from __future__ import annotations

import json
import math
from dataclasses import dataclass, field

import rclpy
from geometry_msgs.msg import PoseStamped
from rclpy.node import Node
from rclpy.time import Time
from std_msgs.msg import String

from .core import Pose2D, quaternion_from_yaw, wrap_angle, yaw_from_quaternion
from .track_evidence import TrackEvidence


@dataclass
class ObjectTrack:
    track_id: int
    object_type: str
    role: str
    pose: Pose2D
    first_seen_sec: float
    last_seen_sec: float
    first_observation_stamp_sec: float
    last_observation_stamp_sec: float
    evidence: TrackEvidence = field(default_factory=TrackEvidence)
    published_once: bool = False

    @property
    def hits(self) -> int:
        return self.evidence.frame_count


@dataclass
class RobotPoseSample:
    pose: Pose2D
    stamp_sec: float


class ObjectTrackFusionNode(Node):
    """Fuse noisy map-frame object observations into stable object tracks.

    This node sits between `object_localizer_node` and consumers such as
    `bbox_goal_navigator_node` / `semantic_obstacle_cloud_node`.

    Raw detections are sparse and can jitter while the robot moves. Instead of
    publishing every raw point as a separate map object, this node associates
    nearby observations with an existing track and publishes confirmed tracks.
    """

    def __init__(self) -> None:
        super().__init__("object_track_fusion_node")

        self.declare_parameter("input_topic", "/object_pose_map_raw")
        self.declare_parameter("input_json_topic", "")
        self.declare_parameter("output_topic", "/object_pose_map")
        self.declare_parameter("target_output_topic", "/target_object_pose_map")
        self.declare_parameter("obstacle_output_topic", "/obstacle_object_pose_map")
        self.declare_parameter("status_topic", "/object_track_fusion/status")
        self.declare_parameter("selected_target_pose_topic", "/bbox_goal_target_pose")
        self.declare_parameter("remove_pose_topic", "/object_track_fusion/remove_pose")
        self.declare_parameter("mission_event_topic", "/mission/event")
        self.declare_parameter("robot_pose_topic", "/robot_pose_map")
        self.declare_parameter("frame_id", "map")
        self.declare_parameter("class_aware_association", False)
        self.declare_parameter("association_radius_m", 0.35)
        self.declare_parameter("use_dynamic_association_radius", False)
        self.declare_parameter("association_base_radius_m", 0.35)
        self.declare_parameter("association_max_radius_m", 0.35)
        self.declare_parameter("association_speed_gain", 1.0)
        self.declare_parameter("association_yaw_gain_m_per_rad", 0.12)
        self.declare_parameter("association_dt_cap_sec", 1.0)
        self.declare_parameter("smoothing_alpha", 0.40)
        self.declare_parameter("confirm_observations", 3)
        self.declare_parameter("candidate_max_age_sec", 1.5)
        self.declare_parameter("confirmed_max_age_sec", 1.5)
        self.declare_parameter("keep_confirmed_tracks", False)
        self.declare_parameter("max_publish_age_sec", 1.5)
        self.declare_parameter("out_of_order_tolerance_sec", 0.02)
        self.declare_parameter("publish_hz", 10.0)
        self.declare_parameter("max_tracks", 30)
        self.declare_parameter("remove_radius_m", 0.40)
        self.declare_parameter("ignored_zones", "")
        self.declare_parameter(
            "remove_event_names",
            "object_captured,pickup_success,target_captured",
        )

        self.frame_id = str(self.get_parameter("frame_id").value)
        self.tracks: list[ObjectTrack] = []
        self.selected_target: Pose2D | None = None
        self.next_track_id = 1
        self.raw_observations_since_status = 0
        self.confirmed_published_since_status = 0
        self.removed_since_status = 0
        self.stale_publish_suppressed_since_status = 0
        self.stale_observation_dropped_since_status = 0
        self.out_of_order_dropped_since_status = 0
        self.robot_pose_prev: RobotPoseSample | None = None
        self.robot_pose_latest: RobotPoseSample | None = None
        self.robot_linear_speed_mps = 0.0
        self.robot_yaw_rate_radps = 0.0
        self.last_association_radius_m = 0.0
        self._warned_input_frame = False
        self._warned_remove_frame = False
        self._warned_selected_frame = False
        self._warned_robot_frame = False

        input_topic = str(self.get_parameter("input_topic").value)
        input_json_topic = str(self.get_parameter("input_json_topic").value).strip()
        output_topic = str(self.get_parameter("output_topic").value)
        target_output_topic = str(self.get_parameter("target_output_topic").value).strip()
        obstacle_output_topic = str(self.get_parameter("obstacle_output_topic").value).strip()
        status_topic = str(self.get_parameter("status_topic").value)
        selected_topic = str(self.get_parameter("selected_target_pose_topic").value).strip()
        remove_pose_topic = str(self.get_parameter("remove_pose_topic").value).strip()
        mission_event_topic = str(self.get_parameter("mission_event_topic").value).strip()
        robot_pose_topic = str(self.get_parameter("robot_pose_topic").value).strip()
        publish_hz = float(self.get_parameter("publish_hz").value)

        if input_json_topic:
            self.create_subscription(String, input_json_topic, self._on_raw_json, 20)
        else:
            self.create_subscription(PoseStamped, input_topic, self._on_raw_pose, 20)
        if robot_pose_topic:
            self.create_subscription(PoseStamped, robot_pose_topic, self._on_robot_pose, 20)
        if selected_topic:
            self.create_subscription(PoseStamped, selected_topic, self._on_selected_target, 10)
        if remove_pose_topic:
            self.create_subscription(PoseStamped, remove_pose_topic, self._on_remove_pose, 10)
        if mission_event_topic:
            self.create_subscription(String, mission_event_topic, self._on_mission_event, 10)

        self.pose_pub = self.create_publisher(PoseStamped, output_topic, 20)
        self.target_pose_pub = (
            self.create_publisher(PoseStamped, target_output_topic, 20)
            if target_output_topic
            else None
        )
        self.obstacle_pose_pub = (
            self.create_publisher(PoseStamped, obstacle_output_topic, 20)
            if obstacle_output_topic
            else None
        )
        self.status_pub = self.create_publisher(String, status_topic, 10)
        self.create_timer(1.0 / max(publish_hz, 0.1), self._publish_tracks)
        self.create_timer(1.0, self._publish_status)

        self.get_logger().info(
            "object track fusion enabled: "
            f"input={input_json_topic or input_topic}, output={output_topic}, "
            f"target_output={target_output_topic}, obstacle_output={obstacle_output_topic}, "
            f"association_radius={self.get_parameter('association_radius_m').value}, "
            "dynamic_association="
            f"{self.get_parameter('use_dynamic_association_radius').value}"
        )

    def _on_raw_pose(self, msg: PoseStamped) -> None:
        if not self._accept_frame(msg.header.frame_id, "input"):
            return
        observation_stamp_sec = self._stamp_to_sec(msg.header.stamp)
        if observation_stamp_sec <= 0.0:
            observation_stamp_sec = self._now_sec()
        self._on_observation(
            self._pose_from_msg(msg),
            object_type="",
            role="unfiltered",
            confidence=1.0,
            observation_stamp_sec=observation_stamp_sec,
        )

    def _on_raw_json(self, msg: String) -> None:
        try:
            payload = json.loads(msg.data)
            frame_id = str(payload.get("frame_id", self.frame_id))
            if not self._accept_frame(frame_id, "input"):
                return
            pose = Pose2D(
                x=float(payload["x"]),
                y=float(payload["y"]),
                theta=float(payload.get("theta", 0.0)),
            )
            object_type = str(payload.get("object_type", "")).strip()
            role = str(payload.get("role", "unfiltered")).strip() or "unfiltered"
            confidence = float(payload.get("confidence", 1.0))
            observation_stamp_sec = float(payload.get("stamp", 0.0))
        except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
            self.get_logger().warn(f"failed to parse raw object JSON: {exc}")
            return

        if not math.isfinite(observation_stamp_sec) or observation_stamp_sec <= 0.0:
            observation_stamp_sec = self._now_sec()
        self._on_observation(
            pose,
            object_type=object_type,
            role=role,
            confidence=confidence,
            observation_stamp_sec=observation_stamp_sec,
        )

    def _on_observation(
        self,
        pose: Pose2D,
        object_type: str,
        role: str,
        confidence: float,
        observation_stamp_sec: float,
    ) -> None:
        self.raw_observations_since_status += 1
        now_sec = self._now_sec()
        self._prune(now_sec)
        max_publish_age = float(self.get_parameter("max_publish_age_sec").value)
        if (
            max_publish_age >= 0.0
            and now_sec - observation_stamp_sec > max_publish_age
        ):
            self.stale_observation_dropped_since_status += 1
            return

        if self._in_ignored_zone(pose):
            return

        match = self._nearest_track(pose, object_type, now_sec)
        if match is None:
            self._add_track(
                pose,
                object_type,
                role,
                confidence,
                observation_stamp_sec,
                now_sec,
            )
        else:
            self._update_track(
                match,
                pose,
                object_type,
                role,
                confidence,
                observation_stamp_sec,
                now_sec,
            )

        self._limit_tracks()

    def _on_robot_pose(self, msg: PoseStamped) -> None:
        if not self._accept_frame(msg.header.frame_id, "robot"):
            return

        stamp_sec = self._stamp_to_sec(msg.header.stamp)
        if stamp_sec <= 0.0:
            stamp_sec = self._now_sec()
        sample = RobotPoseSample(pose=self._pose_from_msg(msg), stamp_sec=stamp_sec)
        if self.robot_pose_latest is not None:
            dt = sample.stamp_sec - self.robot_pose_latest.stamp_sec
            if dt > 1e-3:
                distance = math.hypot(
                    sample.pose.x - self.robot_pose_latest.pose.x,
                    sample.pose.y - self.robot_pose_latest.pose.y,
                )
                yaw_delta = wrap_angle(sample.pose.theta - self.robot_pose_latest.pose.theta)
                self.robot_linear_speed_mps = distance / dt
                self.robot_yaw_rate_radps = yaw_delta / dt
                self.robot_pose_prev = self.robot_pose_latest
        self.robot_pose_latest = sample

    def _on_selected_target(self, msg: PoseStamped) -> None:
        if not self._accept_frame(msg.header.frame_id, "selected"):
            return
        self.selected_target = self._pose_from_msg(msg)

    def _on_remove_pose(self, msg: PoseStamped) -> None:
        if not self._accept_frame(msg.header.frame_id, "remove"):
            return
        self._remove_near(self._pose_from_msg(msg))

    def _on_mission_event(self, msg: String) -> None:
        event = msg.data.strip()
        if not event:
            return
        names = {
            name.strip()
            for name in str(self.get_parameter("remove_event_names").value).split(",")
            if name.strip()
        }
        if event in names and self.selected_target is not None:
            self._remove_near(self.selected_target)

    def _add_track(
        self,
        pose: Pose2D,
        object_type: str,
        role: str,
        confidence: float,
        observation_stamp_sec: float,
        now_sec: float,
    ) -> None:
        track = ObjectTrack(
            track_id=self.next_track_id,
            object_type=object_type,
            role=role,
            pose=pose,
            first_seen_sec=now_sec,
            last_seen_sec=now_sec,
            first_observation_stamp_sec=observation_stamp_sec,
            last_observation_stamp_sec=observation_stamp_sec,
        )
        track.evidence.observe(observation_stamp_sec, object_type, role, confidence)
        track.object_type = track.evidence.representative_class
        track.role = track.evidence.representative_role
        self.tracks.append(track)
        self.next_track_id += 1

    def _update_track(
        self,
        track: ObjectTrack,
        pose: Pose2D,
        object_type: str,
        role: str,
        confidence: float,
        observation_stamp_sec: float,
        now_sec: float,
    ) -> None:
        tolerance = max(
            0.0,
            float(self.get_parameter("out_of_order_tolerance_sec").value),
        )
        if observation_stamp_sec < track.last_observation_stamp_sec - tolerance:
            self.out_of_order_dropped_since_status += 1
            return

        accepted = track.evidence.observe(
            observation_stamp_sec,
            object_type,
            role,
            confidence,
        )
        if accepted:
            alpha = self._clamp(
                float(self.get_parameter("smoothing_alpha").value),
                0.0,
                1.0,
            )
            track.pose = Pose2D(
                x=(1.0 - alpha) * track.pose.x + alpha * pose.x,
                y=(1.0 - alpha) * track.pose.y + alpha * pose.y,
                theta=self._blend_angle(track.pose.theta, pose.theta, alpha),
            )
            track.object_type = track.evidence.representative_class
            track.role = track.evidence.representative_role
        track.last_seen_sec = now_sec
        track.last_observation_stamp_sec = max(
            track.last_observation_stamp_sec, observation_stamp_sec
        )

    def _nearest_track(
        self,
        pose: Pose2D,
        object_type: str,
        now_sec: float,
    ) -> ObjectTrack | None:
        best: ObjectTrack | None = None
        best_dist = math.inf
        for track in self.tracks:
            if not self._same_class(track.object_type, object_type):
                continue
            radius = self._association_radius(track, now_sec)
            dist = math.hypot(pose.x - track.pose.x, pose.y - track.pose.y)
            if dist <= radius and dist <= best_dist:
                best = track
                best_dist = dist
        return best

    def _association_radius(self, track: ObjectTrack, now_sec: float) -> float:
        fixed_radius = max(0.0, float(self.get_parameter("association_radius_m").value))
        if not bool(self.get_parameter("use_dynamic_association_radius").value):
            self.last_association_radius_m = fixed_radius
            return fixed_radius

        base_radius = max(
            0.0,
            float(self.get_parameter("association_base_radius_m").value),
        )
        max_radius = max(
            base_radius,
            float(self.get_parameter("association_max_radius_m").value),
        )
        if self.robot_pose_latest is None:
            radius = self._clamp(fixed_radius, base_radius, max_radius)
            self.last_association_radius_m = radius
            return radius

        dt_cap = max(0.0, float(self.get_parameter("association_dt_cap_sec").value))
        observation_dt = max(0.0, now_sec - track.last_seen_sec)
        if dt_cap > 0.0:
            observation_dt = min(observation_dt, dt_cap)

        speed_gain = max(0.0, float(self.get_parameter("association_speed_gain").value))
        yaw_gain = max(
            0.0,
            float(self.get_parameter("association_yaw_gain_m_per_rad").value),
        )
        radius = (
            base_radius
            + speed_gain * abs(self.robot_linear_speed_mps) * observation_dt
            + yaw_gain * abs(self.robot_yaw_rate_radps) * observation_dt
        )
        radius = self._clamp(radius, base_radius, max_radius)
        self.last_association_radius_m = radius
        return radius

    def _publish_tracks(self) -> None:
        now_sec = self._now_sec()
        self._prune(now_sec)
        max_publish_age = float(self.get_parameter("max_publish_age_sec").value)
        for track in self.tracks:
            if not self._is_confirmed(track):
                continue
            if self._in_ignored_zone(track.pose):
                continue
            measurement_age = now_sec - track.last_observation_stamp_sec
            if max_publish_age >= 0.0 and measurement_age > max_publish_age:
                self.stale_publish_suppressed_since_status += 1
                continue
            msg = self._make_pose_msg(track.pose, track.last_observation_stamp_sec)
            self.pose_pub.publish(msg)
            if track.role in ("unfiltered", "target") and self.target_pose_pub is not None:
                self.target_pose_pub.publish(msg)
            if track.role in ("unfiltered", "obstacle") and self.obstacle_pose_pub is not None:
                self.obstacle_pose_pub.publish(msg)
            track.published_once = True
            self.confirmed_published_since_status += 1

    def _publish_status(self) -> None:
        now_sec = self._now_sec()
        confirmed = [track for track in self.tracks if self._is_confirmed(track)]
        payload = {
            "stamp": now_sec,
            "track_count": len(self.tracks),
            "confirmed_track_count": len(confirmed),
            "candidate_track_count": len(self.tracks) - len(confirmed),
            "raw_observations": self.raw_observations_since_status,
            "confirmed_published": self.confirmed_published_since_status,
            "removed": self.removed_since_status,
            "stale_publish_suppressed": self.stale_publish_suppressed_since_status,
            "stale_observation_dropped": self.stale_observation_dropped_since_status,
            "out_of_order_dropped": self.out_of_order_dropped_since_status,
            "dynamic_association": bool(
                self.get_parameter("use_dynamic_association_radius").value
            ),
            "association_radius_m": round(self.last_association_radius_m, 4),
            "robot_linear_speed_mps": round(self.robot_linear_speed_mps, 4),
            "robot_yaw_rate_radps": round(self.robot_yaw_rate_radps, 4),
            "tracks": [
                {
                    "id": track.track_id,
                    "object_type": track.object_type,
                    "role": track.role,
                    "x": round(track.pose.x, 4),
                    "y": round(track.pose.y, 4),
                    "theta": round(track.pose.theta, 4),
                    "hits": track.hits,
                    "class_score": round(
                        track.evidence.representative_class_score,
                        4,
                    ),
                    "class_scores": {
                        name: round(score, 4)
                        for name, score in sorted(track.evidence.class_scores.items())
                    },
                    "age_sec": round(now_sec - track.first_seen_sec, 3),
                    "last_seen_age_sec": round(now_sec - track.last_seen_sec, 3),
                    "first_observation_stamp": round(track.first_observation_stamp_sec, 6),
                    "last_observation_stamp": round(track.last_observation_stamp_sec, 6),
                    "measurement_age_sec": round(
                        now_sec - track.last_observation_stamp_sec, 3
                    ),
                    "confirmed": self._is_confirmed(track),
                }
                for track in self.tracks
            ],
        }
        out = String()
        out.data = json.dumps(payload, separators=(",", ":"), sort_keys=True)
        self.status_pub.publish(out)
        self.raw_observations_since_status = 0
        self.confirmed_published_since_status = 0
        self.removed_since_status = 0
        self.stale_publish_suppressed_since_status = 0
        self.stale_observation_dropped_since_status = 0
        self.out_of_order_dropped_since_status = 0

    def _remove_near(self, pose: Pose2D) -> None:
        radius = max(0.0, float(self.get_parameter("remove_radius_m").value))
        best_index: int | None = None
        best_dist = radius
        for index, track in enumerate(self.tracks):
            dist = math.hypot(pose.x - track.pose.x, pose.y - track.pose.y)
            if dist <= best_dist:
                best_dist = dist
                best_index = index

        if best_index is None:
            return
        removed = self.tracks.pop(best_index)
        self.removed_since_status += 1
        self.get_logger().info(
            "removed object track "
            f"id={removed.track_id} near ({pose.x:.2f}, {pose.y:.2f})"
        )

    def _prune(self, now_sec: float) -> None:
        keep_confirmed = bool(self.get_parameter("keep_confirmed_tracks").value)
        candidate_max_age = float(self.get_parameter("candidate_max_age_sec").value)
        confirmed_max_age = float(self.get_parameter("confirmed_max_age_sec").value)
        kept: list[ObjectTrack] = []
        for track in self.tracks:
            if self._in_ignored_zone(track.pose):
                continue
            age = now_sec - track.last_seen_sec
            if self._is_confirmed(track):
                if keep_confirmed or confirmed_max_age < 0.0 or age <= confirmed_max_age:
                    kept.append(track)
            elif candidate_max_age < 0.0 or age <= candidate_max_age:
                kept.append(track)
        self.tracks = kept

    def _limit_tracks(self) -> None:
        max_tracks = max(1, int(self.get_parameter("max_tracks").value))
        if len(self.tracks) <= max_tracks:
            return
        self.tracks.sort(
            key=lambda track: (
                self._is_confirmed(track),
                track.last_seen_sec,
                track.hits,
            ),
            reverse=True,
        )
        del self.tracks[max_tracks:]

    def _is_confirmed(self, track: ObjectTrack) -> bool:
        confirm_observations = max(1, int(self.get_parameter("confirm_observations").value))
        return track.hits >= confirm_observations

    def _same_class(self, track_type: str, observation_type: str) -> bool:
        if not bool(self.get_parameter("class_aware_association").value):
            return True
        return track_type == observation_type

    def _in_ignored_zone(self, pose: Pose2D) -> bool:
        for zone_x, zone_y, radius in self._ignored_zones():
            if radius > 0.0 and math.hypot(pose.x - zone_x, pose.y - zone_y) <= radius:
                return True
        return False

    def _ignored_zones(self) -> list[tuple[float, float, float]]:
        raw = str(self.get_parameter("ignored_zones").value).strip()
        if not raw:
            return []
        zones: list[tuple[float, float, float]] = []
        for chunk in raw.split(";"):
            parts = [part.strip() for part in chunk.split(",")]
            if len(parts) != 3:
                continue
            try:
                zones.append((float(parts[0]), float(parts[1]), float(parts[2])))
            except ValueError:
                continue
        return zones

    def _accept_frame(self, frame_id: str, source: str) -> bool:
        if not frame_id or frame_id == self.frame_id:
            return True
        if source == "input" and not self._warned_input_frame:
            self.get_logger().warn(
                f"ignoring raw object pose in frame {frame_id!r}; expected {self.frame_id!r}"
            )
            self._warned_input_frame = True
        elif source == "remove" and not self._warned_remove_frame:
            self.get_logger().warn(
                f"ignoring remove pose in frame {frame_id!r}; expected {self.frame_id!r}"
            )
            self._warned_remove_frame = True
        elif source == "selected" and not self._warned_selected_frame:
            self.get_logger().warn(
                f"ignoring selected target pose in frame {frame_id!r}; expected {self.frame_id!r}"
            )
            self._warned_selected_frame = True
        elif source == "robot" and not self._warned_robot_frame:
            self.get_logger().warn(
                f"ignoring robot pose in frame {frame_id!r}; expected {self.frame_id!r}"
            )
            self._warned_robot_frame = True
        return False

    def _make_pose_msg(self, pose: Pose2D, observation_stamp_sec: float) -> PoseStamped:
        msg = PoseStamped()
        msg.header.stamp = Time(nanoseconds=int(round(observation_stamp_sec * 1e9))).to_msg()
        msg.header.frame_id = self.frame_id
        msg.pose.position.x = pose.x
        msg.pose.position.y = pose.y
        msg.pose.position.z = 0.0
        qx, qy, qz, qw = quaternion_from_yaw(pose.theta)
        msg.pose.orientation.x = qx
        msg.pose.orientation.y = qy
        msg.pose.orientation.z = qz
        msg.pose.orientation.w = qw
        return msg

    @staticmethod
    def _pose_from_msg(msg: PoseStamped) -> Pose2D:
        q = msg.pose.orientation
        return Pose2D(
            x=float(msg.pose.position.x),
            y=float(msg.pose.position.y),
            theta=yaw_from_quaternion(q.x, q.y, q.z, q.w),
        )

    @staticmethod
    def _stamp_to_sec(stamp) -> float:
        return float(stamp.sec) + float(stamp.nanosec) * 1e-9

    @staticmethod
    def _blend_angle(old: float, new: float, alpha: float) -> float:
        return wrap_angle(old + alpha * wrap_angle(new - old))

    @staticmethod
    def _clamp(value: float, low: float, high: float) -> float:
        return max(low, min(high, value))

    def _now_sec(self) -> float:
        return self.get_clock().now().nanoseconds * 1e-9


def main() -> None:
    rclpy.init()
    node = ObjectTrackFusionNode()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()

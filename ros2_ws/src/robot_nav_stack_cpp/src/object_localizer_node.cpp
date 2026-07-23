#include <algorithm>
#include <cctype>
#include <chrono>
#include <cmath>
#include <cstdint>
#include <deque>
#include <functional>
#include <iomanip>
#include <memory>
#include <optional>
#include <sstream>
#include <stdexcept>
#include <string>
#include <utility>
#include <vector>

#include "builtin_interfaces/msg/time.hpp"
#include "geometry_msgs/msg/pose_stamped.hpp"
#include "geometry_msgs/msg/quaternion.hpp"
#include "geometry_msgs/msg/transform_stamped.hpp"
#include "rclcpp/rclcpp.hpp"
#include "std_msgs/msg/string.hpp"
#include "tf2/exceptions.h"
#include "tf2/time.h"
#include "tf2_ros/buffer.h"
#include "tf2_ros/transform_listener.h"

#include "robot_nav_stack_cpp/minijson.hpp"
#include "robot_nav_stack_cpp/portable_bbox_model.hpp"

namespace robot_nav_stack_cpp
{
namespace
{

constexpr double kPi = 3.141592653589793238462643383279502884;

struct Pose2D
{
  double x{0.0};
  double y{0.0};
  double theta{0.0};
};

struct BBox
{
  double cx{0.0};
  double cy{0.0};
  double width{0.0};
  double height{0.0};
};

struct Detection
{
  double stamp{0.0};
  BBox bbox;
  std::string object_type;
  double confidence{1.0};
  int class_id{-1};
  std::string fruit_kind;
  double fruit_confidence{0.0};
};

struct PendingLocalization
{
  Detection detection;
  Pose2D object_source;
  double enqueued_sec{0.0};
};

struct TrackedMapObject
{
  std::string object_type;
  Pose2D pose;
  double first_seen_sec{0.0};
  double last_seen_sec{0.0};
  int seen_count{1};
};

struct StorageBounds
{
  double min_x{-2.0};
  double max_x{-1.4};
  double min_y{-2.0};
  double max_y{-1.4};

  void validate() const
  {
    if (min_x >= max_x || min_y >= max_y) {
      throw std::runtime_error("invalid storage bounds");
    }
  }

  bool contains(double x, double y) const
  {
    return min_x <= x && x <= max_x && min_y <= y && y <= max_y;
  }
};

class TransformFailure : public std::runtime_error
{
public:
  explicit TransformFailure(const std::string & message) : std::runtime_error(message) {}
};

double wrap_angle(double theta)
{
  double wrapped = std::fmod(theta + kPi, 2.0 * kPi);
  if (wrapped < 0.0) {wrapped += 2.0 * kPi;}
  return wrapped - kPi;
}

double yaw_from_quaternion(double x, double y, double z, double w)
{
  const double siny_cosp = 2.0 * (w * z + x * y);
  const double cosy_cosp = 1.0 - 2.0 * (y * y + z * z);
  return std::atan2(siny_cosp, cosy_cosp);
}

geometry_msgs::msg::Quaternion quaternion_from_yaw(double yaw)
{
  geometry_msgs::msg::Quaternion quaternion;
  quaternion.z = std::sin(0.5 * yaw);
  quaternion.w = std::cos(0.5 * yaw);
  return quaternion;
}

std::string clean_name(std::string value)
{
  const auto not_space = [](unsigned char ch) {return !std::isspace(ch);};
  value.erase(value.begin(), std::find_if(value.begin(), value.end(), not_space));
  value.erase(std::find_if(value.rbegin(), value.rend(), not_space).base(), value.end());
  std::transform(value.begin(), value.end(), value.begin(), [](unsigned char ch) {
    return static_cast<char>(std::tolower(ch));
  });
  return value;
}

std::string lowercase(std::string value)
{
  std::transform(value.begin(), value.end(), value.begin(), [](unsigned char ch) {
    return static_cast<char>(std::tolower(ch));
  });
  return value;
}

std::string json_escape(const std::string & value)
{
  std::ostringstream output;
  output << '"';
  for (const unsigned char ch : value) {
    switch (ch) {
      case '"': output << "\\\""; break;
      case '\\': output << "\\\\"; break;
      case '\b': output << "\\b"; break;
      case '\f': output << "\\f"; break;
      case '\n': output << "\\n"; break;
      case '\r': output << "\\r"; break;
      case '\t': output << "\\t"; break;
      default:
        if (ch < 0x20U) {
          output << "\\u" << std::hex << std::setw(4) << std::setfill('0')
                 << static_cast<int>(ch) << std::dec;
        } else {
          output << static_cast<char>(ch);
        }
    }
  }
  output << '"';
  return output.str();
}

std::string json_number(double value)
{
  if (std::isnan(value)) {return "NaN";}
  if (std::isinf(value)) {return value > 0.0 ? "Infinity" : "-Infinity";}
  std::ostringstream output;
  output << std::setprecision(17) << value;
  return output.str();
}

double stamp_to_seconds(const builtin_interfaces::msg::Time & stamp)
{
  return static_cast<double>(stamp.sec) + static_cast<double>(stamp.nanosec) * 1.0e-9;
}

builtin_interfaces::msg::Time seconds_to_stamp(double seconds)
{
  constexpr std::int64_t nanoseconds_per_second = 1000000000LL;
  const std::int64_t total_nanoseconds =
    static_cast<std::int64_t>(std::llround(seconds * 1.0e9));
  std::int64_t whole_seconds = total_nanoseconds / nanoseconds_per_second;
  std::int64_t remaining_nanoseconds = total_nanoseconds % nanoseconds_per_second;
  if (remaining_nanoseconds < 0) {
    --whole_seconds;
    remaining_nanoseconds += nanoseconds_per_second;
  }

  builtin_interfaces::msg::Time stamp;
  stamp.sec = static_cast<std::int32_t>(whole_seconds);
  stamp.nanosec = static_cast<std::uint32_t>(remaining_nanoseconds);
  return stamp;
}

}  // namespace

class ObjectLocalizerNode : public rclcpp::Node
{
public:
  ObjectLocalizerNode() : Node("object_localizer_node")
  {
    declare_parameters();
    const std::string model_path = string_parameter("model_path");
    if (model_path.empty()) {throw std::runtime_error("model_path parameter is required");}

    target_frame_ = string_parameter("target_frame");
    source_frame_ = clean_name_preserving_case(string_parameter("source_frame"));
    if (source_frame_.empty()) {source_frame_ = string_parameter("lidar_frame");}
    tf_lookup_timeout_sec_ = double_parameter("tf_lookup_timeout_sec");
    fallback_to_latest_tf_ = bool_parameter("fallback_to_latest_tf");
    latest_tf_max_extrapolation_sec_ = double_parameter("latest_tf_max_extrapolation_sec");
    pending_detection_timeout_sec_ = double_parameter("pending_detection_timeout_sec");
    max_pending_detections_ = std::max(1, int_parameter("max_pending_detections"));
    estimator_ = std::make_unique<PortableBboxModel>(model_path);
    ignore_storage_objects_ = bool_parameter("ignore_storage_objects");
    storage_bounds_ = StorageBounds{
      double_parameter("storage_min_x"), double_parameter("storage_max_x"),
      double_parameter("storage_min_y"), double_parameter("storage_max_y")};
    if (ignore_storage_objects_) {storage_bounds_.validate();}

    tf_buffer_ = std::make_unique<tf2_ros::Buffer>(get_clock());
    tf_listener_ = std::make_shared<tf2_ros::TransformListener>(*tf_buffer_);

    const std::string detections_topic = string_parameter("detections_topic");
    const std::string object_pose_topic = string_parameter("object_pose_topic");
    const std::string object_pose_json_topic = clean_name_preserving_case(
      string_parameter("object_pose_json_topic"));
    const std::string target_object_pose_topic = string_parameter("target_object_pose_topic");
    const std::string obstacle_object_pose_topic = string_parameter("obstacle_object_pose_topic");
    const std::string target_lock_status_topic = clean_name_preserving_case(
      string_parameter("target_lock_status_topic"));
    target_shape_ = clean_name(string_parameter("target_shape"));
    target_fruit_ = clean_name(string_parameter("target_fruit"));
    no_fruit_class_ = clean_name(string_parameter("no_fruit_class"));
    target_min_confidence_ = std::max(0.0, double_parameter("target_min_confidence"));

    detection_sub_ = create_subscription<std_msgs::msg::String>(
      detections_topic, 10,
      std::bind(&ObjectLocalizerNode::on_detection_json, this, std::placeholders::_1));
    pose_pub_ = create_publisher<geometry_msgs::msg::PoseStamped>(object_pose_topic, 10);
    if (!object_pose_json_topic.empty()) {
      json_pub_ = create_publisher<std_msgs::msg::String>(object_pose_json_topic, 10);
    }
    target_pub_ = create_publisher<geometry_msgs::msg::PoseStamped>(
      target_object_pose_topic, 10);
    obstacle_pub_ = create_publisher<geometry_msgs::msg::PoseStamped>(
      obstacle_object_pose_topic, 10);
    if (!target_lock_status_topic.empty()) {
      target_lock_status_sub_ = create_subscription<std_msgs::msg::String>(
        target_lock_status_topic, 10,
        std::bind(&ObjectLocalizerNode::on_target_lock_status, this, std::placeholders::_1));
    }
    const double retry_period = std::max(
      0.01, double_parameter("pending_tf_retry_period_sec"));
    retry_timer_ = create_wall_timer(
      std::chrono::duration<double>(retry_period),
      std::bind(&ObjectLocalizerNode::retry_pending_detections, this));
    RCLCPP_INFO(
      get_logger(),
      "object pose split: all=%s, target=%s, obstacle=%s, target_shape='%s', target_fruit='%s'",
      object_pose_topic.c_str(), target_object_pose_topic.c_str(),
      obstacle_object_pose_topic.c_str(), target_shape_.c_str(), target_fruit_.c_str());
  }

private:
  void declare_parameters()
  {
    declare_parameter<std::string>("model_path", "");
    declare_parameter<std::string>("detections_topic", "/detections_json");
    declare_parameter<std::string>("object_pose_topic", "/object_pose_map");
    declare_parameter<std::string>("object_pose_json_topic", "");
    declare_parameter<std::string>("target_object_pose_topic", "/target_object_pose_map");
    declare_parameter<std::string>("obstacle_object_pose_topic", "/obstacle_object_pose_map");
    declare_parameter<std::string>("target_shape", "");
    declare_parameter<std::string>("target_fruit", "");
    declare_parameter<std::string>("no_fruit_class", "none");
    declare_parameter<double>("target_min_confidence", 0.0);
    declare_parameter<std::string>("target_frame", "map");
    declare_parameter<std::string>("source_frame", "");
    declare_parameter<std::string>("lidar_frame", "lidar");
    declare_parameter<double>("tf_lookup_timeout_sec", 0.0);
    declare_parameter<bool>("fallback_to_latest_tf", false);
    declare_parameter<double>("latest_tf_max_extrapolation_sec", 3.0);
    declare_parameter<double>("pending_detection_timeout_sec", 0.5);
    declare_parameter<double>("pending_tf_retry_period_sec", 0.05);
    declare_parameter<std::int64_t>("max_pending_detections", 10);
    declare_parameter<bool>("stabilize_objects", true);
    declare_parameter<double>("object_association_radius_m", 0.35);
    declare_parameter<double>("object_update_alpha", 0.4);
    declare_parameter<std::int64_t>("max_tracked_objects", 20);
    declare_parameter<std::string>("target_lock_status_topic", "/bbox_goal_navigator/status");
    declare_parameter<double>("locked_target_radius_m", 0.25);
    declare_parameter<bool>("ignore_storage_objects", true);
    declare_parameter<double>("storage_min_x", -2.0);
    declare_parameter<double>("storage_max_x", -1.4);
    declare_parameter<double>("storage_min_y", -2.0);
    declare_parameter<double>("storage_max_y", -1.4);
  }

  double double_parameter(const std::string & name) const
  {
    return get_parameter(name).as_double();
  }

  int int_parameter(const std::string & name) const
  {
    return static_cast<int>(get_parameter(name).as_int());
  }

  bool bool_parameter(const std::string & name) const
  {
    return get_parameter(name).as_bool();
  }

  std::string string_parameter(const std::string & name) const
  {
    return get_parameter(name).as_string();
  }

  static std::string clean_name_preserving_case(std::string value)
  {
    const auto not_space = [](unsigned char ch) {return !std::isspace(ch);};
    value.erase(value.begin(), std::find_if(value.begin(), value.end(), not_space));
    value.erase(std::find_if(value.rbegin(), value.rend(), not_space).base(), value.end());
    return value;
  }

  void on_detection_json(const std_msgs::msg::String::SharedPtr msg)
  {
    try {
      const Detection detection = parse_detection(msg->data);
      const auto prediction = estimator_->predict(BboxModelInput{
        detection.bbox.cx, detection.bbox.cy, detection.bbox.width,
        detection.bbox.height, detection.object_type});
      localize_or_queue(detection, Pose2D{prediction.x, prediction.y, 0.0});
    } catch (const std::exception & exc) {
      RCLCPP_WARN(get_logger(), "failed to localize object: %s", exc.what());
    }
  }

  void localize_or_queue(const Detection & detection, const Pose2D & object_source)
  {
    try {
      publish_object_pose(
        detection, transform_source_to_map(object_source, detection.stamp));
    } catch (const TransformFailure & exc) {
      if (should_wait_for_transform(exc.what())) {
        enqueue_pending_detection(detection, object_source, exc.what());
      } else {
        RCLCPP_WARN(get_logger(), "failed to localize object: %s", exc.what());
      }
    }
  }

  void publish_object_pose(const Detection & detection, Pose2D object_map)
  {
    if (object_map.x < -2.0 || object_map.x > 2.0 ||
      object_map.y < -2.0 || object_map.y > 2.0)
    {
      return;
    }
    if (object_map.x <= -1.4 && object_map.y <= -1.4) {return;}
    std::string role = detection_role(detection);
    Pose2D raw_object_map = object_map;
    if (in_storage_zone(object_map)) {return;}

    const double lock_radius = std::max(0.0, double_parameter("locked_target_radius_m"));
    if (locked_target_pose_ &&
      std::hypot(object_map.x - locked_target_pose_->x,
      object_map.y - locked_target_pose_->y) <= lock_radius)
    {
      object_map = *locked_target_pose_;
      raw_object_map = object_map;
      role = "target";
      if (!logged_locked_target_override_) {
        RCLCPP_INFO(
          get_logger(),
          "holding locked target classification and map pose against close-range reclassification");
        logged_locked_target_override_ = true;
      }
    }

    object_map = role == "obstacle" ? raw_object_map :
      stabilize_object_pose(detection, object_map);
    const auto output = make_pose_msg(object_map, detection.stamp);
    pose_pub_->publish(output);
    if (role == "target") {
      target_pub_->publish(output);
    } else if (role == "obstacle") {
      obstacle_pub_->publish(make_pose_msg(raw_object_map, detection.stamp));
    }
    if (json_pub_) {
      std_msgs::msg::String message;
      std::ostringstream payload;
      payload << "{\"confidence\":" << json_number(detection.confidence)
              << ",\"frame_id\":" << json_escape(target_frame_)
              << ",\"fruit_confidence\":" << json_number(detection.fruit_confidence)
              << ",\"fruit_kind\":" << json_escape(detection.fruit_kind)
              << ",\"object_type\":" << json_escape(detection.object_type)
              << ",\"role\":" << json_escape(role)
              << ",\"stamp\":" << json_number(detection.stamp)
              << ",\"theta\":" << json_number(object_map.theta)
              << ",\"x\":" << json_number(object_map.x)
              << ",\"y\":" << json_number(object_map.y) << '}';
      message.data = payload.str();
      json_pub_->publish(message);
    }
  }

  void on_target_lock_status(const std_msgs::msg::String::SharedPtr msg)
  {
    try {
      update_locked_target(msg->data);
    } catch (const std::exception & exc) {
      if (!warned_target_lock_status_) {
        RCLCPP_WARN(get_logger(), "ignoring invalid target-lock status: %s", exc.what());
        warned_target_lock_status_ = true;
      }
      return;
    }
    warned_target_lock_status_ = false;
    if (!locked_target_pose_) {logged_locked_target_override_ = false;}
  }

  void update_locked_target(const std::string & data)
  {
    const auto payload = minijson::parse(data);
    if (!payload.is_object()) {
      throw std::runtime_error("target-lock status must be a JSON object");
    }
    const auto * locked = payload.find("target_locked");
    if (locked == nullptr || !locked->is_bool() || !locked->as_bool()) {
      locked_target_pose_.reset();
      return;
    }
    const auto * target = payload.find("target");
    if (target == nullptr || !target->is_object()) {
      throw std::runtime_error("locked target status is missing target coordinates");
    }
    try {
      const double x = target->at("x").as_double();
      const double y = target->at("y").as_double();
      const auto * theta_value = target->find("theta");
      const double theta = theta_value == nullptr ? 0.0 : theta_value->as_double();
      if (!std::isfinite(x) || !std::isfinite(y) || !std::isfinite(theta)) {
        throw std::runtime_error("locked target coordinates must be finite");
      }
      locked_target_pose_ = Pose2D{x, y, theta};
    } catch (const std::runtime_error & exc) {
      const std::string message(exc.what());
      if (message == "locked target coordinates must be finite") {throw;}
      throw std::runtime_error("locked target coordinates are invalid");
    }
  }

  bool in_storage_zone(const Pose2D & pose) const
  {
    return ignore_storage_objects_ && storage_bounds_.contains(pose.x, pose.y);
  }

  geometry_msgs::msg::PoseStamped make_pose_msg(
    const Pose2D & pose, double stamp_sec) const
  {
    geometry_msgs::msg::PoseStamped output;
    output.header.frame_id = target_frame_;
    output.header.stamp = seconds_to_stamp(stamp_sec);
    output.pose.position.x = pose.x;
    output.pose.position.y = pose.y;
    output.pose.position.z = 0.0;
    output.pose.orientation = quaternion_from_yaw(pose.theta);
    return output;
  }

  Pose2D stabilize_object_pose(const Detection & detection, const Pose2D & object_map)
  {
    if (!bool_parameter("stabilize_objects")) {return object_map;}
    const double now = now_sec();
    const double association_radius = std::max(
      0.0, double_parameter("object_association_radius_m"));
    const std::string object_key = tracking_key(detection);
    TrackedMapObject * best_track = nullptr;
    double best_distance = association_radius;
    for (auto & track : tracked_objects_) {
      if (track.object_type != object_key) {continue;}
      const double distance = std::hypot(
        track.pose.x - object_map.x, track.pose.y - object_map.y);
      if (distance <= best_distance) {
        best_distance = distance;
        best_track = &track;
      }
    }
    if (best_track == nullptr) {
      tracked_objects_.push_back(TrackedMapObject{
        object_key, object_map, now, now, 1});
      trim_tracked_objects();
      return object_map;
    }
    const double alpha = std::clamp(
      double_parameter("object_update_alpha"), 0.0, 1.0);
    if (alpha > 0.0) {
      best_track->pose = Pose2D{
        (1.0 - alpha) * best_track->pose.x + alpha * object_map.x,
        (1.0 - alpha) * best_track->pose.y + alpha * object_map.y,
        wrap_angle(best_track->pose.theta +
        alpha * wrap_angle(object_map.theta - best_track->pose.theta))};
    }
    best_track->last_seen_sec = now;
    ++best_track->seen_count;
    return best_track->pose;
  }

  std::string tracking_key(const Detection & detection) const
  {
    const std::string fruit_kind = clean_name(detection.fruit_kind);
    const std::string object_type = clean_name(detection.object_type);
    return fruit_kind.empty() ? object_type : object_type + ":" + fruit_kind;
  }

  void trim_tracked_objects()
  {
    const int max_tracked = std::max(1, int_parameter("max_tracked_objects"));
    if (tracked_objects_.size() <= static_cast<std::size_t>(max_tracked)) {return;}
    std::stable_sort(
      tracked_objects_.begin(), tracked_objects_.end(),
      [](const auto & left, const auto & right) {
        return left.last_seen_sec > right.last_seen_sec;
      });
    tracked_objects_.resize(static_cast<std::size_t>(max_tracked));
  }

  void retry_pending_detections()
  {
    if (pending_detections_.empty()) {return;}
    auto pending = std::move(pending_detections_);
    pending_detections_.clear();
    const double now = now_sec();
    for (const auto & item : pending) {
      const double age_sec = now - item.enqueued_sec;
      try {
        publish_object_pose(
          item.detection,
          transform_source_to_map(item.object_source, item.detection.stamp));
      } catch (const TransformFailure & exc) {
        if (age_sec <= pending_detection_timeout_sec_ &&
          should_wait_for_transform(exc.what()))
        {
          pending_detections_.push_back(item);
          continue;
        }
        RCLCPP_WARN(
          get_logger(),
          "dropping pending object localization after %.3fs without exact TF at stamp %.6f: %s",
          age_sec, item.detection.stamp, exc.what());
      }
    }
  }

  void enqueue_pending_detection(
    const Detection & detection, const Pose2D & object_source,
    const std::string & error)
  {
    if (pending_detection_timeout_sec_ <= 0.0) {
      RCLCPP_WARN(get_logger(), "failed to localize object: %s", error.c_str());
      return;
    }
    if (pending_detections_.size() >= static_cast<std::size_t>(max_pending_detections_)) {
      const Detection dropped = pending_detections_.front().detection;
      pending_detections_.pop_front();
      RCLCPP_WARN(
        get_logger(),
        "dropping oldest pending object localization because queue is full "
        "(stamp=%.6f, max_pending_detections=%d)",
        dropped.stamp, max_pending_detections_);
    }
    pending_detections_.push_back(PendingLocalization{
      detection, object_source, now_sec()});
    if (!warned_pending_tf_wait_) {
      RCLCPP_WARN(
        get_logger(),
        "TF at detection stamp is not available yet; waiting for exact TF "
        "for up to %.3fs before dropping. First error: %s",
        pending_detection_timeout_sec_, error.c_str());
      warned_pending_tf_wait_ = true;
    }
  }

  Detection parse_detection(const std::string & data) const
  {
    const auto payload = minijson::parse(data);
    const auto & bbox = payload.at("bbox");
    Detection detection;
    detection.stamp = payload.at("stamp").as_double();
    detection.bbox = BBox{
      bbox.at("cx").as_double(), bbox.at("cy").as_double(),
      bbox.at("w").as_double(), bbox.at("h").as_double()};
    detection.object_type = payload.at("object_type").as_string();
    if (const auto * value = payload.find("confidence")) {
      detection.confidence = value->as_double();
    }
    if (const auto * value = payload.find("class_id")) {
      detection.class_id = value->as_int();
    }
    if (const auto * value = payload.find("fruit_kind")) {
      detection.fruit_kind = clean_name(value->as_string());
    }
    if (const auto * value = payload.find("fruit_confidence")) {
      detection.fruit_confidence = value->as_double();
    }
    return detection;
  }

  std::string detection_role(const Detection & detection) const
  {
    const std::string object_type = clean_name(detection.object_type);
    const std::string fruit_kind = clean_name(detection.fruit_kind);
    const bool is_cube = object_type == "cube_any";
    const bool has_no_fruit = fruit_kind.empty() || fruit_kind == no_fruit_class_;
    bool shape_matches = false;
    if (target_shape_ == "cube_any") {
      shape_matches = is_cube && has_no_fruit;
    } else {
      shape_matches = !target_shape_.empty() && object_type == target_shape_;
    }
    bool fruit_matches = false;
    if (target_fruit_ == no_fruit_class_) {
      fruit_matches = is_cube && has_no_fruit;
    } else {
      fruit_matches = !target_fruit_.empty() && is_cube && !has_no_fruit &&
        fruit_kind == target_fruit_;
    }
    if (target_shape_.empty() && target_fruit_.empty()) {return "unfiltered";}
    if ((shape_matches || fruit_matches) && detection.confidence >= target_min_confidence_) {
      return "target";
    }
    return "obstacle";
  }

  Pose2D transform_source_to_map(const Pose2D & object_source, double stamp)
  {
    const auto transform = lookup_map_source_transform(stamp);
    const auto & translation = transform.transform.translation;
    const auto & rotation = transform.transform.rotation;
    const Pose2D source_map{
      translation.x, translation.y,
      yaw_from_quaternion(rotation.x, rotation.y, rotation.z, rotation.w)};
    const double c = std::cos(source_map.theta);
    const double s = std::sin(source_map.theta);
    const double x = source_map.x + c * object_source.x - s * object_source.y;
    const double y = source_map.y + s * object_source.x + c * object_source.y;
    const double theta = std::hypot(object_source.x, object_source.y) > 1.0e-6 ?
      wrap_angle(source_map.theta + std::atan2(object_source.y, object_source.x)) :
      source_map.theta;
    return Pose2D{x, y, theta};
  }

  geometry_msgs::msg::TransformStamped lookup_map_source_transform(double stamp)
  {
    const auto timeout = tf2::durationFromSec(std::max(0.0, tf_lookup_timeout_sec_));
    const auto exact_time = tf2::timeFromSec(stamp);
    std::string original_error;
    try {
      return tf_buffer_->lookupTransform(target_frame_, source_frame_, exact_time, timeout);
    } catch (const tf2::TransformException & exc) {
      original_error = exc.what();
      if (!fallback_to_latest_tf_) {throw TransformFailure(original_error);}
    }
    geometry_msgs::msg::TransformStamped transform;
    try {
      transform = tf_buffer_->lookupTransform(
        target_frame_, source_frame_, tf2::TimePointZero, timeout);
    } catch (const tf2::TransformException & exc) {
      throw TransformFailure(exc.what());
    }
    const double latest_stamp = stamp_to_seconds(transform.header.stamp);
    const double extrapolation_sec = stamp - latest_stamp;
    if (extrapolation_sec < 0.0) {
      std::ostringstream message;
      message << "latest TF fallback only handles future extrapolation: detection stamp "
              << std::fixed << std::setprecision(6) << stamp
              << ", latest TF stamp " << latest_stamp
              << ". Original error: " << original_error;
      throw TransformFailure(message.str());
    }
    if (latest_tf_max_extrapolation_sec_ >= 0.0 &&
      extrapolation_sec > latest_tf_max_extrapolation_sec_)
    {
      std::ostringstream message;
      message << "latest TF fallback is too stale: detection stamp "
              << std::fixed << std::setprecision(6) << stamp
              << ", latest TF stamp " << latest_stamp
              << ", extrapolation " << std::setprecision(3) << extrapolation_sec
              << "s > limit " << latest_tf_max_extrapolation_sec_
              << "s. Original error: " << original_error;
      throw TransformFailure(message.str());
    }
    if (!warned_latest_tf_fallback_) {
      RCLCPP_WARN(
        get_logger(),
        "TF at detection stamp was unavailable; using latest %s->%s TF as fallback "
        "(%.3fs newer than latest TF). Original error: %s",
        target_frame_.c_str(), source_frame_.c_str(),
        std::max(0.0, extrapolation_sec), original_error.c_str());
      warned_latest_tf_fallback_ = true;
    }
    return transform;
  }

  static bool should_wait_for_transform(const std::string & error)
  {
    return lowercase(error).find("future") != std::string::npos;
  }

  double now_sec()
  {
    return static_cast<double>(get_clock()->now().nanoseconds()) * 1.0e-9;
  }

  std::string target_frame_;
  std::string source_frame_;
  std::string target_shape_;
  std::string target_fruit_;
  std::string no_fruit_class_;
  double target_min_confidence_{0.0};
  double tf_lookup_timeout_sec_{0.0};
  bool fallback_to_latest_tf_{false};
  double latest_tf_max_extrapolation_sec_{3.0};
  bool warned_latest_tf_fallback_{false};
  double pending_detection_timeout_sec_{0.5};
  int max_pending_detections_{10};
  std::deque<PendingLocalization> pending_detections_;
  bool warned_pending_tf_wait_{false};
  std::vector<TrackedMapObject> tracked_objects_;
  std::optional<Pose2D> locked_target_pose_;
  bool warned_target_lock_status_{false};
  bool logged_locked_target_override_{false};
  bool ignore_storage_objects_{true};
  StorageBounds storage_bounds_;

  std::unique_ptr<PortableBboxModel> estimator_;
  std::unique_ptr<tf2_ros::Buffer> tf_buffer_;
  std::shared_ptr<tf2_ros::TransformListener> tf_listener_;
  rclcpp::Subscription<std_msgs::msg::String>::SharedPtr detection_sub_;
  rclcpp::Subscription<std_msgs::msg::String>::SharedPtr target_lock_status_sub_;
  rclcpp::Publisher<geometry_msgs::msg::PoseStamped>::SharedPtr pose_pub_;
  rclcpp::Publisher<std_msgs::msg::String>::SharedPtr json_pub_;
  rclcpp::Publisher<geometry_msgs::msg::PoseStamped>::SharedPtr target_pub_;
  rclcpp::Publisher<geometry_msgs::msg::PoseStamped>::SharedPtr obstacle_pub_;
  rclcpp::TimerBase::SharedPtr retry_timer_;
};

}  // namespace robot_nav_stack_cpp

int main(int argc, char ** argv)
{
  rclcpp::init(argc, argv);
  try {
    rclcpp::spin(std::make_shared<robot_nav_stack_cpp::ObjectLocalizerNode>());
  } catch (const std::exception & exc) {
    RCLCPP_FATAL(rclcpp::get_logger("object_localizer_node"), "%s", exc.what());
    rclcpp::shutdown();
    return 1;
  }
  rclcpp::shutdown();
  return 0;
}

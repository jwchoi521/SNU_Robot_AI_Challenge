#include <algorithm>
#include <array>
#include <cctype>
#include <cmath>
#include <cstdint>
#include <deque>
#include <functional>
#include <iomanip>
#include <limits>
#include <memory>
#include <numeric>
#include <optional>
#include <sstream>
#include <stdexcept>
#include <string>
#include <tuple>
#include <utility>
#include <vector>

#include "builtin_interfaces/msg/time.hpp"
#include "geometry_msgs/msg/pose_stamped.hpp"
#include "geometry_msgs/msg/quaternion.hpp"
#include "geometry_msgs/msg/transform_stamped.hpp"
#include "nav_msgs/msg/odometry.hpp"
#include "rclcpp/rclcpp.hpp"
#include "sensor_msgs/msg/imu.hpp"
#include "sensor_msgs/msg/laser_scan.hpp"
#include "std_msgs/msg/string.hpp"
#include "tf2/exceptions.h"
#include "tf2/time.h"
#include "tf2_ros/buffer.h"
#include "tf2_ros/transform_broadcaster.h"
#include "tf2_ros/transform_listener.h"

namespace robot_nav_stack_cpp
{

constexpr double kPi = 3.141592653589793238462643383279502884;

struct Pose2D
{
  double x{0.0};
  double y{0.0};
  double theta{0.0};
};

struct TimedPose2D
{
  double stamp_sec{0.0};
  Pose2D pose;
};

struct ScanRay
{
  double origin_x{0.0};
  double origin_y{0.0};
  double dir_x{0.0};
  double dir_y{0.0};
  double observed_range{0.0};
};

enum class Wall : std::size_t { Left = 0, Right = 1, Bottom = 2, Top = 3 };

struct RangeScore
{
  double score{std::numeric_limits<double>::infinity()};
  int used_rays{0};
  std::array<int, 4> wall_counts{{0, 0, 0, 0}};
  int visible_walls{0};
};

struct LocalizerResult
{
  Pose2D pose;
  RangeScore range_score;
  double prior_score{0.0};
  double total_score{std::numeric_limits<double>::infinity()};
  std::size_t source_index{0};
};

double wrap_angle(double theta)
{
  double wrapped = std::fmod(theta + kPi, 2.0 * kPi);
  if (wrapped < 0.0) {
    wrapped += 2.0 * kPi;
  }
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
  geometry_msgs::msg::Quaternion q;
  const double half = 0.5 * yaw;
  q.x = 0.0;
  q.y = 0.0;
  q.z = std::sin(half);
  q.w = std::cos(half);
  return q;
}

Pose2D interpolate_pair(
  const TimedPose2D & before, const TimedPose2D & after, double stamp_sec)
{
  const double dt = after.stamp_sec - before.stamp_sec;
  if (dt <= 0.0) {
    return after.pose;
  }
  const double alpha = (stamp_sec - before.stamp_sec) / dt;
  const double theta_delta = wrap_angle(after.pose.theta - before.pose.theta);
  return Pose2D{
    before.pose.x + alpha * (after.pose.x - before.pose.x),
    before.pose.y + alpha * (after.pose.y - before.pose.y),
    wrap_angle(before.pose.theta + alpha * theta_delta)};
}

std::optional<Pose2D> interpolate_pose(
  const std::deque<TimedPose2D> & samples, double stamp_sec, double max_extrapolation_sec)
{
  if (samples.empty()) {
    return std::nullopt;
  }
  const double limit = std::max(0.0, max_extrapolation_sec);
  constexpr double epsilon = 1.0e-9;
  const auto & first = samples.front();
  const auto & last = samples.back();
  if (samples.size() == 1U) {
    return std::abs(stamp_sec - first.stamp_sec) <= limit + epsilon ?
           std::optional<Pose2D>(first.pose) : std::nullopt;
  }
  if (stamp_sec <= first.stamp_sec) {
    if (first.stamp_sec - stamp_sec > limit + epsilon) {
      return std::nullopt;
    }
    return interpolate_pair(first, samples[1], stamp_sec);
  }
  if (stamp_sec >= last.stamp_sec) {
    if (stamp_sec - last.stamp_sec > limit + epsilon) {
      return std::nullopt;
    }
    return interpolate_pair(samples[samples.size() - 2U], last, stamp_sec);
  }
  for (std::size_t index = 1; index < samples.size(); ++index) {
    const auto & before = samples[index - 1U];
    const auto & after = samples[index];
    if (before.stamp_sec <= stamp_sec && stamp_sec <= after.stamp_sec) {
      return interpolate_pair(before, after, stamp_sec);
    }
  }
  return std::nullopt;
}

double scan_duration_sec(std::size_t range_count, double time_increment, double scan_time)
{
  if (range_count > 1U && std::isfinite(time_increment) && time_increment > 0.0) {
    return static_cast<double>(range_count - 1U) * time_increment;
  }
  if (std::isfinite(scan_time) && scan_time > 0.0) {
    return scan_time;
  }
  return 0.0;
}

ScanRay transform_ray_to_reference(
  const ScanRay & ray, const Pose2D & odom_pose_at_ray,
  const Pose2D & odom_pose_at_reference)
{
  const double c_ray = std::cos(odom_pose_at_ray.theta);
  const double s_ray = std::sin(odom_pose_at_ray.theta);
  const double origin_odom_x =
    odom_pose_at_ray.x + c_ray * ray.origin_x - s_ray * ray.origin_y;
  const double origin_odom_y =
    odom_pose_at_ray.y + s_ray * ray.origin_x + c_ray * ray.origin_y;

  const double dx = origin_odom_x - odom_pose_at_reference.x;
  const double dy = origin_odom_y - odom_pose_at_reference.y;
  const double c_ref = std::cos(odom_pose_at_reference.theta);
  const double s_ref = std::sin(odom_pose_at_reference.theta);
  const double yaw_delta = wrap_angle(
    odom_pose_at_ray.theta - odom_pose_at_reference.theta);
  const double c_delta = std::cos(yaw_delta);
  const double s_delta = std::sin(yaw_delta);
  return ScanRay{
    c_ref * dx + s_ref * dy,
    -s_ref * dx + c_ref * dy,
    c_delta * ray.dir_x - s_delta * ray.dir_y,
    s_delta * ray.dir_x + c_delta * ray.dir_y,
    ray.observed_range};
}

std::string json_string(const std::string & value)
{
  std::ostringstream out;
  out << '"';
  for (const char ch : value) {
    switch (ch) {
      case '"': out << "\\\""; break;
      case '\\': out << "\\\\"; break;
      case '\n': out << "\\n"; break;
      case '\r': out << "\\r"; break;
      case '\t': out << "\\t"; break;
      default: out << ch; break;
    }
  }
  out << '"';
  return out.str();
}

std::string json_number(double value)
{
  if (std::isnan(value)) {
    return "NaN";
  }
  if (std::isinf(value)) {
    return value > 0.0 ? "Infinity" : "-Infinity";
  }
  std::ostringstream out;
  out << std::setprecision(17) << value;
  return out.str();
}

const char * json_bool(bool value) {return value ? "true" : "false";}

class FourWallLocalizerNode : public rclcpp::Node
{
public:
  FourWallLocalizerNode()
  : Node("four_wall_localizer_node")
  {
    declare_parameters();
    map_frame_ = string_parameter("map_frame");
    odom_frame_ = string_parameter("odom_frame");
    base_frame_ = string_parameter("base_frame");
    arena_w_ = double_parameter("arena_width_m");
    arena_h_ = double_parameter("arena_height_m");
    arena_origin_ = lowercase(string_parameter("arena_origin"));
    compute_arena_bounds();

    scan_sub_ = create_subscription<sensor_msgs::msg::LaserScan>(
      string_parameter("scan_topic"), 1,
      std::bind(&FourWallLocalizerNode::on_scan, this, std::placeholders::_1));
    odom_sub_ = create_subscription<nav_msgs::msg::Odometry>(
      string_parameter("odom_topic"), 30,
      std::bind(&FourWallLocalizerNode::on_odom, this, std::placeholders::_1));
    imu_sub_ = create_subscription<sensor_msgs::msg::Imu>(
      string_parameter("imu_topic"), 30,
      std::bind(&FourWallLocalizerNode::on_imu, this, std::placeholders::_1));
    pose_pub_ = create_publisher<geometry_msgs::msg::PoseStamped>(
      string_parameter("pose_topic"), 10);
    status_pub_ = create_publisher<std_msgs::msg::String>(
      string_parameter("status_topic"), 10);
    tf_broadcaster_ = std::make_unique<tf2_ros::TransformBroadcaster>(*this);
    tf_buffer_ = std::make_unique<tf2_ros::Buffer>(get_clock());
    tf_listener_ = std::make_shared<tf2_ros::TransformListener>(*tf_buffer_);
  }

private:
  struct ValidRay
  {
    std::size_t index;
    double angle;
    double observed_range;
  };

  void declare_parameters()
  {
    declare_parameter<std::string>("scan_topic", "/scan");
    declare_parameter<std::string>("odom_topic", "/odom");
    declare_parameter<std::string>("imu_topic", "/imu");
    declare_parameter<std::string>("pose_topic", "/robot_pose_map");
    declare_parameter<std::string>("status_topic", "/four_wall_localizer/status");
    declare_parameter<std::string>("map_frame", "map");
    declare_parameter<std::string>("odom_frame", "odom");
    declare_parameter<std::string>("base_frame", "base_link");
    declare_parameter<std::string>("lidar_frame", "lidar");
    declare_parameter<double>("arena_width_m", 4.0);
    declare_parameter<double>("arena_height_m", 4.0);
    declare_parameter<std::string>("arena_origin", "center");
    declare_parameter<double>("initial_x_m", 1.8);
    declare_parameter<double>("initial_y_m", -1.8);
    declare_parameter<double>("initial_yaw_deg", 90.0);
    declare_parameter<double>("lidar_x_m", 0.0);
    declare_parameter<double>("lidar_y_m", 0.0);
    declare_parameter<double>("lidar_yaw_deg", 0.0);
    declare_parameter<bool>("use_lidar_tf_extrinsics", false);
    declare_parameter<double>("lidar_tf_timeout_sec", 0.05);
    declare_parameter<bool>("enable_lidar_deskew", true);
    declare_parameter<double>("motion_history_sec", 3.0);
    declare_parameter<double>("motion_max_extrapolation_sec", 0.05);
    declare_parameter<bool>("use_odom_prior", true);
    declare_parameter<bool>("use_imu_yaw_prior", true);
    declare_parameter<double>("max_imu_age_sec", 0.5);
    declare_parameter<bool>("publish_tf", false);
    declare_parameter<std::string>("tf_mode", "map_to_base");
    declare_parameter<double>("transform_tolerance_sec", 0.2);
    declare_parameter<bool>("publish_lidar_tf", true);
    declare_parameter<int64_t>("max_rays", 60);
    declare_parameter<int64_t>("min_rays", 40);
    declare_parameter<double>("trim_fraction", 0.70);
    declare_parameter<double>("range_residual_clamp_m", 0.25);
    declare_parameter<int64_t>("min_visible_walls", 2);
    declare_parameter<int64_t>("min_rays_per_wall", 10);
    declare_parameter<double>("missing_wall_penalty", 0.05);
    declare_parameter<int64_t>("opt_iterations", 1);
    declare_parameter<double>("initial_step_xy_m", 0.10);
    declare_parameter<double>("initial_step_yaw_deg", 5.0);
    declare_parameter<bool>("use_global_seed_search_on_first_scan", false);
    declare_parameter<bool>("use_symmetry_seeds", false);
    declare_parameter<double>("global_seed_step_m", 0.75);
    declare_parameter<double>("global_seed_yaw_step_deg", 90.0);
    declare_parameter<double>("prior_xy_weight", 0.0003);
    declare_parameter<double>("prior_yaw_weight", 0.0003);
    declare_parameter<double>("symmetry_range_score_ratio", 1.20);
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

  static std::string lowercase(std::string value)
  {
    std::transform(value.begin(), value.end(), value.begin(), [](unsigned char ch) {
      return static_cast<char>(std::tolower(ch));
    });
    return value;
  }

  static double stamp_to_seconds(const builtin_interfaces::msg::Time & stamp)
  {
    return static_cast<double>(stamp.sec) +
           static_cast<double>(stamp.nanosec) * 1.0e-9;
  }

  static builtin_interfaces::msg::Time seconds_to_stamp(double seconds)
  {
    return rclcpp::Time(
      static_cast<int64_t>(std::llround(seconds * 1.0e9)), RCL_ROS_TIME).to_msg();
  }

  void on_odom(const nav_msgs::msg::Odometry::SharedPtr msg)
  {
    const auto & q = msg->pose.pose.orientation;
    const Pose2D pose{
      msg->pose.pose.position.x, msg->pose.pose.position.y,
      yaw_from_quaternion(q.x, q.y, q.z, q.w)};
    current_odom_pose_ = pose;
    const double stamp_sec = message_stamp_sec(msg->header.stamp, "odometry");
    if (stamp_sec > 0.0) {
      append_motion_sample(odom_history_, TimedPose2D{stamp_sec, pose});
    }
  }

  void on_imu(const sensor_msgs::msg::Imu::SharedPtr msg)
  {
    const auto & q = msg->orientation;
    const double yaw = yaw_from_quaternion(q.x, q.y, q.z, q.w);
    current_imu_yaw_ = yaw;
    const double stamp_sec = message_stamp_sec(msg->header.stamp, "IMU");
    if (stamp_sec > 0.0) {
      current_imu_time_sec_ = stamp_sec;
      append_motion_sample(imu_history_, TimedPose2D{stamp_sec, Pose2D{0.0, 0.0, yaw}});
    }
  }

  double message_stamp_sec(
    const builtin_interfaces::msg::Time & stamp, const std::string & source)
  {
    const double stamp_sec = stamp_to_seconds(stamp);
    if (stamp_sec > 0.0) {
      return stamp_sec;
    }
    bool & warned = source == "odometry" ? warned_bad_odom_stamp_ : warned_bad_imu_stamp_;
    if (!warned) {
      RCLCPP_WARN(get_logger(), "ignoring %s sample with a zero timestamp", source.c_str());
      warned = true;
    }
    return 0.0;
  }

  void append_motion_sample(std::deque<TimedPose2D> & history, const TimedPose2D & sample)
  {
    if (!history.empty() && sample.stamp_sec < history.back().stamp_sec - 1.0e-6) {
      return;
    }
    if (!history.empty() && std::abs(sample.stamp_sec - history.back().stamp_sec) <= 1.0e-9) {
      history.back() = sample;
    } else {
      history.push_back(sample);
    }
    const double history_sec = std::max(0.5, double_parameter("motion_history_sec"));
    const double cutoff = sample.stamp_sec - history_sec;
    while (history.size() > 1U && history[1].stamp_sec < cutoff) {
      history.pop_front();
    }
  }

  void on_scan(const sensor_msgs::msg::LaserScan::SharedPtr msg)
  {
    const double scan_start_sec = stamp_to_seconds(msg->header.stamp);
    if (scan_start_sec <= 0.0) {
      publish_status("{\"ok\":false,\"reason\":\"zero_scan_timestamp\"}");
      return;
    }
    const double scan_span_sec = scan_duration_sec(
      msg->ranges.size(), msg->time_increment, msg->scan_time);
    const double reference_sec = scan_start_sec + 0.5 * scan_span_sec;
    const auto reference_stamp = seconds_to_stamp(reference_sec);
    const double max_extrapolation = std::max(
      0.0, double_parameter("motion_max_extrapolation_sec"));
    const auto odom_pose_at_reference = interpolate_pose(
      odom_history_, reference_sec, max_extrapolation);
    const std::string tf_mode = lowercase(string_parameter("tf_mode"));
    const bool deskew_requested = bool_parameter("enable_lidar_deskew");
    const bool map_to_odom = tf_mode == "map_to_odom" || tf_mode == "map_odom";
    if ((map_to_odom || deskew_requested) && !odom_pose_at_reference) {
      std::ostringstream status;
      status << "{\"ok\":false,\"reason\":\"missing_odom_at_scan_reference\",";
      status << "\"scan_reference_stamp\":" << json_number(reference_sec) << ',';
      status << "\"odom_samples\":" << odom_history_.size() << ",\"required_by\":[";
      bool first = true;
      if (map_to_odom) {
        status << json_string("map_to_odom");
        first = false;
      }
      if (deskew_requested) {
        if (!first) {status << ',';}
        status << json_string("lidar_deskew");
      }
      status << "]}";
      publish_status(status.str());
      return;
    }

    const auto lidar_extrinsics = resolve_lidar_extrinsics(*msg);
    if (!lidar_extrinsics) {
      std::ostringstream status;
      status << "{\"ok\":false,\"reason\":\"missing_lidar_extrinsics_tf\",";
      status << "\"base_frame\":" << json_string(base_frame_) << ',';
      status << "\"lidar_frame\":" << json_string(msg->header.frame_id) << '}';
      publish_status(status.str());
      return;
    }

    int deskewed_rays = 0;
    int motion_dropped_rays = 0;
    const auto rays = scan_to_base_rays(
      *msg, scan_start_sec, reference_sec, odom_pose_at_reference,
      *lidar_extrinsics, deskewed_rays, motion_dropped_rays);
    if (static_cast<int>(rays.size()) < int_parameter("min_rays")) {
      std::ostringstream status;
      status << "{\"ok\":false,\"reason\":\"not_enough_lidar_rays\",";
      status << "\"rays\":" << rays.size() << ',';
      status << "\"motion_dropped_rays\":" << motion_dropped_rays << '}';
      publish_status(status.str());
      return;
    }

    imu_prior_used_ = false;
    const auto imu_yaw_at_reference = imu_yaw_at(reference_sec);
    const bool has_pose_prior = last_pose_.has_value();
    const Pose2D prior = predict_prior_pose(odom_pose_at_reference, imu_yaw_at_reference);
    const auto seeds = symmetry_seeds(prior);
    std::vector<LocalizerResult> results;
    results.reserve(seeds.size());
    for (std::size_t index = 0; index < seeds.size(); ++index) {
      auto result = optimize_seed(seeds[index], prior, rays, has_pose_prior);
      result.source_index = index;
      results.push_back(result);
    }
    if (results.empty()) {
      publish_status("{\"ok\":false,\"reason\":\"no_localization_candidates\"}");
      return;
    }
    const auto best_it = std::min_element(
      results.begin(), results.end(), [](const auto & a, const auto & b) {
        return a.total_score < b.total_score;
      });
    const auto range_best_it = std::min_element(
      results.begin(), results.end(), [](const auto & a, const auto & b) {
        return a.range_score.score < b.range_score.score;
      });
    std::vector<double> range_scores;
    range_scores.reserve(results.size());
    for (const auto & result : results) {
      range_scores.push_back(result.range_score.score);
    }
    std::sort(range_scores.begin(), range_scores.end());
    const double score_ratio = range_scores.size() > 1U ?
      range_scores[1] / std::max(range_scores[0], 1.0e-9) : 999.0;
    const bool symmetry_resolved_by_prior =
      score_ratio <= double_parameter("symmetry_range_score_ratio");
    const bool ambiguous = symmetry_resolved_by_prior &&
      best_it->source_index != range_best_it->source_index;
    const LocalizerResult best = *best_it;

    last_pose_ = best.pose;
    last_odom_pose_ = odom_pose_at_reference;
    if (imu_yaw_at_reference) {
      last_imu_yaw_ = *imu_yaw_at_reference;
    }
    publish_pose(best.pose, reference_stamp);
    if (bool_parameter("publish_tf")) {
      publish_tf(best.pose, reference_stamp, odom_pose_at_reference);
    }
    publish_success_status(
      best, results.size(), rays.size(), scan_start_sec, reference_sec,
      scan_span_sec, odom_pose_at_reference.has_value(), deskew_requested,
      deskewed_rays, motion_dropped_rays, imu_yaw_at_reference,
      has_pose_prior, score_ratio, symmetry_resolved_by_prior, ambiguous);
  }

  std::optional<Pose2D> resolve_lidar_extrinsics(
    const sensor_msgs::msg::LaserScan & msg)
  {
    if (!bool_parameter("use_lidar_tf_extrinsics")) {
      return Pose2D{
        double_parameter("lidar_x_m"), double_parameter("lidar_y_m"),
        double_parameter("lidar_yaw_deg") * kPi / 180.0};
    }
    const std::string lidar_frame = msg.header.frame_id.empty() ?
      string_parameter("lidar_frame") : msg.header.frame_id;
    if (lidar_frame == base_frame_) {
      return Pose2D{};
    }
    const double timeout = std::max(0.0, double_parameter("lidar_tf_timeout_sec"));
    try {
      const auto transform = tf_buffer_->lookupTransform(
        base_frame_, lidar_frame, tf2::TimePointZero, tf2::durationFromSec(timeout));
      warned_missing_lidar_tf_ = false;
      const auto & translation = transform.transform.translation;
      const auto & rotation = transform.transform.rotation;
      return Pose2D{
        translation.x, translation.y,
        yaw_from_quaternion(rotation.x, rotation.y, rotation.z, rotation.w)};
    } catch (const tf2::TransformException & exc) {
      if (!warned_missing_lidar_tf_) {
        RCLCPP_WARN(
          get_logger(), "waiting for static %s->%s TF: %s",
          base_frame_.c_str(), lidar_frame.c_str(), exc.what());
        warned_missing_lidar_tf_ = true;
      }
      return std::nullopt;
    }
  }

  std::vector<ScanRay> scan_to_base_rays(
    const sensor_msgs::msg::LaserScan & msg, double scan_start_sec,
    double reference_sec, const std::optional<Pose2D> & odom_pose_at_reference,
    const Pose2D & lidar_extrinsics, int & deskewed_rays,
    int & motion_dropped_rays)
  {
    std::vector<ValidRay> valid;
    valid.reserve(msg.ranges.size());
    double angle = msg.angle_min;
    for (std::size_t index = 0; index < msg.ranges.size(); ++index) {
      const double observed = msg.ranges[index];
      if (std::isfinite(observed) && observed >= msg.range_min && observed <= 4.0) {
        valid.push_back(ValidRay{index, angle, observed});
      }
      angle += msg.angle_increment;
    }
    const int max_rays = std::max(1, int_parameter("max_rays"));
    std::size_t stride = 1U;
    if (valid.size() > static_cast<std::size_t>(max_rays)) {
      stride = std::max<std::size_t>(
        1U, static_cast<std::size_t>(std::ceil(
          static_cast<double>(valid.size()) / static_cast<double>(max_rays))));
    }
    const double max_extrapolation = std::max(
      0.0, double_parameter("motion_max_extrapolation_sec"));
    const bool deskew = bool_parameter("enable_lidar_deskew") &&
      odom_pose_at_reference.has_value() && msg.ranges.size() > 1U &&
      reference_sec > scan_start_sec;
    double ray_dt = msg.time_increment;
    if (!std::isfinite(ray_dt) || ray_dt <= 0.0) {
      const std::size_t interval_count =
        msg.ranges.size() > 1U ? msg.ranges.size() - 1U : 1U;
      ray_dt = 2.0 * (reference_sec - scan_start_sec) /
        static_cast<double>(interval_count);
    }

    std::vector<ScanRay> rays;
    rays.reserve((valid.size() + stride - 1U) / stride);
    for (std::size_t valid_index = 0; valid_index < valid.size(); valid_index += stride) {
      const auto & item = valid[valid_index];
      const double ray_yaw = lidar_extrinsics.theta + item.angle;
      ScanRay ray{
        lidar_extrinsics.x, lidar_extrinsics.y,
        std::cos(ray_yaw), std::sin(ray_yaw), item.observed_range};
      if (deskew) {
        const auto odom_pose_at_ray = interpolate_pose(
          odom_history_, scan_start_sec + static_cast<double>(item.index) * ray_dt,
          max_extrapolation);
        if (!odom_pose_at_ray) {
          ++motion_dropped_rays;
          continue;
        }
        ray = transform_ray_to_reference(
          ray, *odom_pose_at_ray, *odom_pose_at_reference);
        ++deskewed_rays;
      }
      rays.push_back(ray);
    }
    return rays;
  }

  Pose2D predict_prior_pose(
    const std::optional<Pose2D> & odom_pose_at_reference,
    const std::optional<double> & imu_yaw_at_reference)
  {
    const auto imu_delta = imu_yaw_delta_since_last_scan(imu_yaw_at_reference);
    if (bool_parameter("use_odom_prior") && last_pose_ && last_odom_pose_ &&
      odom_pose_at_reference)
    {
      const double dx_odom = odom_pose_at_reference->x - last_odom_pose_->x;
      const double dy_odom = odom_pose_at_reference->y - last_odom_pose_->y;
      const double c_o = std::cos(-last_odom_pose_->theta);
      const double s_o = std::sin(-last_odom_pose_->theta);
      const double dx_local = c_o * dx_odom - s_o * dy_odom;
      const double dy_local = s_o * dx_odom + c_o * dy_odom;
      double dtheta = wrap_angle(
        odom_pose_at_reference->theta - last_odom_pose_->theta);
      if (imu_delta) {
        dtheta = *imu_delta;
      }
      const double c_m = std::cos(last_pose_->theta);
      const double s_m = std::sin(last_pose_->theta);
      return Pose2D{
        last_pose_->x + c_m * dx_local - s_m * dy_local,
        last_pose_->y + s_m * dx_local + c_m * dy_local,
        wrap_angle(last_pose_->theta + dtheta)};
    }
    if (last_pose_) {
      if (imu_delta) {
        return Pose2D{last_pose_->x, last_pose_->y,
          wrap_angle(last_pose_->theta + *imu_delta)};
      }
      return *last_pose_;
    }
    return Pose2D{
      double_parameter("initial_x_m"), double_parameter("initial_y_m"),
      double_parameter("initial_yaw_deg") * kPi / 180.0};
  }

  std::optional<double> imu_yaw_delta_since_last_scan(
    const std::optional<double> & imu_yaw_at_reference)
  {
    if (!imu_yaw_at_reference || !last_imu_yaw_) {
      return std::nullopt;
    }
    imu_prior_used_ = true;
    return wrap_angle(*imu_yaw_at_reference - *last_imu_yaw_);
  }

  std::optional<double> imu_yaw_at(double stamp_sec) const
  {
    if (!bool_parameter("use_imu_yaw_prior")) {
      return std::nullopt;
    }
    const double max_age = std::max(0.0, double_parameter("max_imu_age_sec"));
    const auto sample = interpolate_pose(imu_history_, stamp_sec, max_age);
    return sample ? std::optional<double>(sample->theta) : std::nullopt;
  }

  std::vector<Pose2D> symmetry_seeds(const Pose2D & pose)
  {
    if (!last_pose_) {
      if (bool_parameter("use_global_seed_search_on_first_scan")) {
        const auto seeds = global_first_scan_seeds({}, pose);
        if (!seeds.empty()) {
          return seeds;
        }
      }
      return {clip_pose_to_arena(pose)};
    }
    if (!bool_parameter("use_symmetry_seeds")) {
      return {clip_pose_to_arena(pose)};
    }
    const double center_x = 0.5 * (min_x_ + max_x_);
    const double center_y = 0.5 * (min_y_ + max_y_);
    const double span_x = max_x_ - min_x_;
    const double span_y = max_y_ - min_y_;
    std::vector<Pose2D> candidates{
      pose,
      {min_x_ + max_x_ - pose.x, min_y_ + max_y_ - pose.y, wrap_angle(pose.theta + kPi)},
      {min_x_ + max_x_ - pose.x, pose.y, wrap_angle(kPi - pose.theta)},
      {pose.x, min_y_ + max_y_ - pose.y, wrap_angle(-pose.theta)}};
    if (std::abs(span_x - span_y) <= 0.05) {
      const double rel_x = pose.x - center_x;
      const double rel_y = pose.y - center_y;
      candidates.push_back({center_x - rel_y, center_y + rel_x, wrap_angle(pose.theta + 0.5 * kPi)});
      candidates.push_back({center_x + rel_y, center_y - rel_x, wrap_angle(pose.theta - 0.5 * kPi)});
      candidates.push_back({center_x + rel_y, center_y + rel_x, wrap_angle(0.5 * kPi - pose.theta)});
      candidates.push_back({center_x - rel_y, center_y - rel_x, wrap_angle(-0.5 * kPi - pose.theta)});
    }
    std::vector<Pose2D> unique;
    for (const auto & candidate : candidates) {
      const Pose2D clipped{
        std::clamp(candidate.x, min_x_ + 0.02, max_x_ - 0.02),
        std::clamp(candidate.y, min_y_ + 0.02, max_y_ - 0.02),
        wrap_angle(candidate.theta)};
      if (!seed_exists(clipped, unique)) {
        unique.push_back(clipped);
      }
    }
    const auto global = global_first_scan_seeds(unique, pose);
    unique.insert(unique.end(), global.begin(), global.end());
    return unique;
  }

  Pose2D clip_pose_to_arena(const Pose2D & pose) const
  {
    return Pose2D{
      std::clamp(pose.x, min_x_ + 0.02, max_x_ - 0.02),
      std::clamp(pose.y, min_y_ + 0.02, max_y_ - 0.02), wrap_angle(pose.theta)};
  }

  std::vector<Pose2D> global_first_scan_seeds(
    const std::vector<Pose2D> & existing, const Pose2D & prior) const
  {
    if (last_pose_ || !bool_parameter("use_global_seed_search_on_first_scan")) {
      return {};
    }
    const double step = std::max(0.10, double_parameter("global_seed_step_m"));
    const double yaw_step = std::max(5.0, double_parameter("global_seed_yaw_step_deg")) *
      kPi / 180.0;
    const int yaw_count = std::max(1, static_cast<int>(std::ceil(2.0 * kPi / yaw_step)));
    constexpr double margin = 0.02;
    const auto x_values = seed_axis_values(min_x_ + margin, max_x_ - margin, step);
    const auto y_values = seed_axis_values(min_y_ + margin, max_y_ - margin, step);
    std::vector<Pose2D> seeds;
    for (const double x : x_values) {
      for (const double y : y_values) {
        for (int yaw_index = 0; yaw_index < yaw_count; ++yaw_index) {
          const Pose2D seed{x, y, wrap_angle(prior.theta + yaw_index * yaw_step)};
          if (!seed_exists(seed, existing) && !seed_exists(seed, seeds)) {
            seeds.push_back(seed);
          }
        }
      }
    }
    return seeds;
  }

  static std::vector<double> seed_axis_values(double low, double high, double step)
  {
    if (high <= low) {
      return {0.5 * (low + high)};
    }
    std::vector<double> values{low};
    double current = low;
    while (current + step < high) {
      current += step;
      values.push_back(current);
    }
    if (std::abs(values.back() - high) > 1.0e-6) {
      values.push_back(high);
    }
    const double center = 0.5 * (low + high);
    const bool has_center = std::any_of(values.begin(), values.end(), [center](double value) {
      return std::abs(value - center) <= 1.0e-6;
    });
    if (!has_center) {
      values.push_back(center);
      std::sort(values.begin(), values.end());
    }
    return values;
  }

  static bool seed_exists(const Pose2D & seed, const std::vector<Pose2D> & seeds)
  {
    return std::any_of(seeds.begin(), seeds.end(), [&seed](const Pose2D & old) {
      return std::hypot(seed.x - old.x, seed.y - old.y) < 1.0e-4 &&
             std::abs(wrap_angle(seed.theta - old.theta)) < 1.0e-4;
    });
  }

  LocalizerResult optimize_seed(
    const Pose2D & seed, const Pose2D & prior, const std::vector<ScanRay> & rays,
    bool use_prior) const
  {
    Pose2D pose = seed;
    RangeScore range_score = range_score_for_pose(pose, rays);
    double score = range_score.score;
    double step_xy = double_parameter("initial_step_xy_m");
    double step_yaw = double_parameter("initial_step_yaw_deg") * kPi / 180.0;
    const int iterations = int_parameter("opt_iterations");
    for (int iteration = 0; iteration < iterations; ++iteration) {
      bool improved = true;
      while (improved) {
        improved = false;
        const std::array<Pose2D, 6> candidates{{
          {pose.x + step_xy, pose.y, pose.theta},
          {pose.x - step_xy, pose.y, pose.theta},
          {pose.x, pose.y + step_xy, pose.theta},
          {pose.x, pose.y - step_xy, pose.theta},
          {pose.x, pose.y, wrap_angle(pose.theta + step_yaw)},
          {pose.x, pose.y, wrap_angle(pose.theta - step_yaw)}}};
        for (const auto & candidate : candidates) {
          if (candidate.x < min_x_ || candidate.x > max_x_ ||
            candidate.y < min_y_ || candidate.y > max_y_)
          {
            continue;
          }
          const auto candidate_score = range_score_for_pose(candidate, rays);
          if (candidate_score.score + 1.0e-12 < score) {
            pose = candidate;
            range_score = candidate_score;
            score = candidate_score.score;
            improved = true;
          }
        }
      }
      step_xy *= 0.5;
      step_yaw *= 0.5;
    }
    const double prior_value = use_prior ? prior_score(pose, prior) : 0.0;
    return LocalizerResult{pose, range_score, prior_value, range_score.score + prior_value, 0U};
  }

  RangeScore range_score_for_pose(
    const Pose2D & pose, const std::vector<ScanRay> & rays) const
  {
    const double c = std::cos(pose.theta);
    const double s = std::sin(pose.theta);
    const double clamp = std::max(0.05, double_parameter("range_residual_clamp_m"));
    std::vector<double> residuals;
    residuals.reserve(rays.size());
    std::array<int, 4> wall_counts{{0, 0, 0, 0}};
    for (const auto & ray : rays) {
      const double origin_x = pose.x + c * ray.origin_x - s * ray.origin_y;
      const double origin_y = pose.y + s * ray.origin_x + c * ray.origin_y;
      const double dir_x = c * ray.dir_x - s * ray.dir_y;
      const double dir_y = s * ray.dir_x + c * ray.dir_y;
      const auto hit = first_wall_hit(origin_x, origin_y, dir_x, dir_y);
      if (!hit) {
        continue;
      }
      const double residual = std::min(clamp, std::abs(ray.observed_range - hit->first));
      residuals.push_back(residual * residual);
      ++wall_counts[static_cast<std::size_t>(hit->second)];
    }
    if (residuals.empty()) {
      return RangeScore{std::numeric_limits<double>::infinity(), 0, wall_counts, 0};
    }
    std::sort(residuals.begin(), residuals.end());
    const int keep = std::max(
      1, static_cast<int>(static_cast<double>(residuals.size()) *
      double_parameter("trim_fraction")));
    const double base_score = std::accumulate(
      residuals.begin(), residuals.begin() + keep, 0.0) / static_cast<double>(keep);
    const int min_rays_per_wall = int_parameter("min_rays_per_wall");
    const int visible_walls = static_cast<int>(std::count_if(
      wall_counts.begin(), wall_counts.end(), [min_rays_per_wall](int count) {
        return count >= min_rays_per_wall;
      }));
    const int missing = std::max(
      0, int_parameter("min_visible_walls") - visible_walls);
    return RangeScore{
      base_score + missing * double_parameter("missing_wall_penalty"),
      static_cast<int>(residuals.size()), wall_counts, visible_walls};
  }

  std::optional<std::pair<double, Wall>> first_wall_hit(
    double origin_x, double origin_y, double dir_x, double dir_y) const
  {
    constexpr double eps = 1.0e-9;
    constexpr double tolerance = 1.0e-6;
    std::optional<std::pair<double, Wall>> best;
    const auto consider = [&best](double distance, Wall wall) {
      if (distance > 0.0 && (!best || distance < best->first)) {
        best = std::make_pair(distance, wall);
      }
    };
    if (std::abs(dir_x) > eps) {
      const double t_left = (min_x_ - origin_x) / dir_x;
      const double y_left = origin_y + t_left * dir_y;
      if (min_y_ - tolerance <= y_left && y_left <= max_y_ + tolerance) {
        consider(t_left, Wall::Left);
      }
      const double t_right = (max_x_ - origin_x) / dir_x;
      const double y_right = origin_y + t_right * dir_y;
      if (min_y_ - tolerance <= y_right && y_right <= max_y_ + tolerance) {
        consider(t_right, Wall::Right);
      }
    }
    if (std::abs(dir_y) > eps) {
      const double t_bottom = (min_y_ - origin_y) / dir_y;
      const double x_bottom = origin_x + t_bottom * dir_x;
      if (min_x_ - tolerance <= x_bottom && x_bottom <= max_x_ + tolerance) {
        consider(t_bottom, Wall::Bottom);
      }
      const double t_top = (max_y_ - origin_y) / dir_y;
      const double x_top = origin_x + t_top * dir_x;
      if (min_x_ - tolerance <= x_top && x_top <= max_x_ + tolerance) {
        consider(t_top, Wall::Top);
      }
    }
    return best;
  }

  void compute_arena_bounds()
  {
    if (arena_origin_ == "center" || arena_origin_ == "centre" || arena_origin_ == "middle") {
      min_x_ = -0.5 * arena_w_;
      max_x_ = 0.5 * arena_w_;
      min_y_ = -0.5 * arena_h_;
      max_y_ = 0.5 * arena_h_;
      return;
    }
    if (arena_origin_ == "corner" || arena_origin_ == "bottom_left" ||
      arena_origin_ == "lower_left")
    {
      min_x_ = 0.0;
      max_x_ = arena_w_;
      min_y_ = 0.0;
      max_y_ = arena_h_;
      return;
    }
    throw std::invalid_argument(
            "arena_origin must be 'center' or 'corner', got " + arena_origin_);
  }

  double prior_score(const Pose2D & pose, const Pose2D & prior) const
  {
    const double dx = pose.x - prior.x;
    const double dy = pose.y - prior.y;
    const double dtheta = wrap_angle(pose.theta - prior.theta);
    return double_parameter("prior_xy_weight") * (dx * dx + dy * dy) +
           double_parameter("prior_yaw_weight") * dtheta * dtheta;
  }

  void publish_pose(const Pose2D & pose, const builtin_interfaces::msg::Time & stamp)
  {
    geometry_msgs::msg::PoseStamped msg;
    msg.header.stamp = stamp;
    msg.header.frame_id = map_frame_;
    msg.pose.position.x = pose.x;
    msg.pose.position.y = pose.y;
    msg.pose.position.z = 0.0;
    msg.pose.orientation = quaternion_from_yaw(pose.theta);
    pose_pub_->publish(msg);
  }

  void publish_tf(
    const Pose2D & pose, const builtin_interfaces::msg::Time & stamp,
    const std::optional<Pose2D> & odom_pose_at_stamp)
  {
    const auto tf_stamp = tf_publish_stamp(stamp);
    const std::string tf_mode = lowercase(string_parameter("tf_mode"));
    if (tf_mode == "map_to_odom" || tf_mode == "map_odom") {
      publish_map_to_odom_tf(pose, tf_stamp, odom_pose_at_stamp);
      return;
    }
    if (tf_mode != "map_to_base" && tf_mode != "map_base" && tf_mode != "direct") {
      RCLCPP_WARN(
        get_logger(), "unknown tf_mode '%s'; falling back to map_to_base",
        tf_mode.c_str());
    }
    geometry_msgs::msg::TransformStamped transform;
    transform.header.stamp = tf_stamp;
    transform.header.frame_id = map_frame_;
    transform.child_frame_id = base_frame_;
    transform.transform.translation.x = pose.x;
    transform.transform.translation.y = pose.y;
    transform.transform.translation.z = 0.0;
    transform.transform.rotation = quaternion_from_yaw(pose.theta);
    tf_broadcaster_->sendTransform(transform);
    if (!bool_parameter("publish_lidar_tf")) {
      return;
    }
    const std::string lidar_frame = string_parameter("lidar_frame");
    if (lidar_frame == base_frame_) {
      return;
    }
    const double lidar_x = double_parameter("lidar_x_m");
    const double lidar_y = double_parameter("lidar_y_m");
    const double lidar_yaw = double_parameter("lidar_yaw_deg") * kPi / 180.0;
    const double c = std::cos(pose.theta);
    const double s = std::sin(pose.theta);
    const Pose2D lidar_pose{
      pose.x + c * lidar_x - s * lidar_y,
      pose.y + s * lidar_x + c * lidar_y,
      wrap_angle(pose.theta + lidar_yaw)};
    geometry_msgs::msg::TransformStamped lidar_transform;
    lidar_transform.header.stamp = tf_stamp;
    lidar_transform.header.frame_id = map_frame_;
    lidar_transform.child_frame_id = lidar_frame;
    lidar_transform.transform.translation.x = lidar_pose.x;
    lidar_transform.transform.translation.y = lidar_pose.y;
    lidar_transform.transform.translation.z = 0.0;
    lidar_transform.transform.rotation = quaternion_from_yaw(lidar_pose.theta);
    tf_broadcaster_->sendTransform(lidar_transform);
  }

  void publish_map_to_odom_tf(
    const Pose2D & map_pose_base, const builtin_interfaces::msg::Time & stamp,
    const std::optional<Pose2D> & odom_pose_at_stamp)
  {
    if (!odom_pose_at_stamp) {
      if (!warned_missing_odom_for_tf_) {
        RCLCPP_WARN(
          get_logger(),
          "tf_mode=map_to_odom needs odometry interpolated at the TF stamp; skipping map -> odom");
        warned_missing_odom_for_tf_ = true;
      }
      return;
    }
    warned_missing_odom_for_tf_ = false;
    const double theta = wrap_angle(map_pose_base.theta - odom_pose_at_stamp->theta);
    const double c = std::cos(theta);
    const double s = std::sin(theta);
    geometry_msgs::msg::TransformStamped transform;
    transform.header.stamp = stamp;
    transform.header.frame_id = map_frame_;
    transform.child_frame_id = odom_frame_;
    transform.transform.translation.x = map_pose_base.x -
      (c * odom_pose_at_stamp->x - s * odom_pose_at_stamp->y);
    transform.transform.translation.y = map_pose_base.y -
      (s * odom_pose_at_stamp->x + c * odom_pose_at_stamp->y);
    transform.transform.translation.z = 0.0;
    transform.transform.rotation = quaternion_from_yaw(theta);
    tf_broadcaster_->sendTransform(transform);
  }

  builtin_interfaces::msg::Time tf_publish_stamp(
    const builtin_interfaces::msg::Time & stamp) const
  {
    const double tolerance = std::max(
      0.0, double_parameter("transform_tolerance_sec"));
    return tolerance <= 0.0 ? stamp : seconds_to_stamp(stamp_to_seconds(stamp) + tolerance);
  }

  void publish_success_status(
    const LocalizerResult & best, std::size_t candidate_count, std::size_t ray_count,
    double scan_start_sec, double reference_sec, double scan_span_sec,
    bool odom_aligned, bool deskew_requested, int deskewed_rays,
    int motion_dropped_rays, const std::optional<double> & imu_yaw,
    bool has_pose_prior, double score_ratio, bool symmetry_resolved_by_prior,
    bool ambiguous)
  {
    std::ostringstream out;
    out << "{\"ok\":true";
    out << ",\"rays\":" << ray_count;
    out << ",\"used_rays\":" << best.range_score.used_rays;
    out << ",\"x\":" << json_number(best.pose.x);
    out << ",\"y\":" << json_number(best.pose.y);
    out << ",\"yaw_deg\":" << json_number(best.pose.theta * 180.0 / kPi);
    out << ",\"imu_yaw_deg\":" << (imu_yaw ? json_number(*imu_yaw * 180.0 / kPi) : "null");
    out << ",\"imu_yaw_prior_used\":" << json_bool(imu_prior_used_);
    out << ",\"scan_start_stamp\":" << json_number(scan_start_sec);
    out << ",\"scan_reference_stamp\":" << json_number(reference_sec);
    out << ",\"scan_duration_sec\":" << json_number(scan_span_sec);
    out << ",\"odom_aligned_to_scan\":" << json_bool(odom_aligned);
    out << ",\"lidar_deskew_enabled\":" << json_bool(deskew_requested);
    out << ",\"lidar_deskew_applied\":" << json_bool(deskewed_rays > 0);
    out << ",\"deskewed_rays\":" << deskewed_rays;
    out << ",\"motion_dropped_rays\":" << motion_dropped_rays;
    out << ",\"lidar_extrinsics_source\":" << json_string(
      bool_parameter("use_lidar_tf_extrinsics") ? "tf" : "parameters");
    out << ",\"arena_origin\":" << json_string(arena_origin_);
    out << ",\"tf_mode\":" << json_string(string_parameter("tf_mode"));
    out << ",\"transform_tolerance_sec\":" << json_number(
      double_parameter("transform_tolerance_sec"));
    out << ",\"arena_bounds\":{\"min_x\":" << json_number(min_x_)
        << ",\"max_x\":" << json_number(max_x_)
        << ",\"min_y\":" << json_number(min_y_)
        << ",\"max_y\":" << json_number(max_y_) << '}';
    out << ",\"global_seed_search_on_first_scan\":" << json_bool(
      bool_parameter("use_global_seed_search_on_first_scan"));
    out << ",\"symmetry_seeds_enabled\":" << json_bool(
      bool_parameter("use_symmetry_seeds"));
    out << ",\"pose_prior_active\":" << json_bool(has_pose_prior);
    out << ",\"range_score\":" << json_number(best.range_score.score);
    out << ",\"prior_score\":" << json_number(best.prior_score);
    out << ",\"total_score\":" << json_number(best.total_score);
    out << ",\"wall_counts\":{\"left\":" << best.range_score.wall_counts[0]
        << ",\"right\":" << best.range_score.wall_counts[1]
        << ",\"bottom\":" << best.range_score.wall_counts[2]
        << ",\"top\":" << best.range_score.wall_counts[3] << '}';
    out << ",\"visible_walls\":" << best.range_score.visible_walls;
    out << ",\"range_score_ratio_best_two\":" << json_number(score_ratio);
    out << ",\"symmetry_resolved_by_prior\":" << json_bool(symmetry_resolved_by_prior);
    out << ",\"ambiguous_without_prior\":" << json_bool(ambiguous);
    out << ",\"candidate_count\":" << candidate_count << '}';
    publish_status(out.str());
  }

  void publish_status(const std::string & payload)
  {
    std_msgs::msg::String msg;
    msg.data = payload;
    status_pub_->publish(msg);
  }

  std::string map_frame_;
  std::string odom_frame_;
  std::string base_frame_;
  std::string arena_origin_;
  double arena_w_{4.0};
  double arena_h_{4.0};
  double min_x_{-2.0};
  double max_x_{2.0};
  double min_y_{-2.0};
  double max_y_{2.0};

  std::optional<Pose2D> last_pose_;
  std::optional<Pose2D> last_odom_pose_;
  std::optional<Pose2D> current_odom_pose_;
  std::deque<TimedPose2D> odom_history_;
  std::optional<double> last_imu_yaw_;
  std::optional<double> current_imu_yaw_;
  std::optional<double> current_imu_time_sec_;
  std::deque<TimedPose2D> imu_history_;
  bool imu_prior_used_{false};
  bool warned_missing_odom_for_tf_{false};
  bool warned_bad_odom_stamp_{false};
  bool warned_bad_imu_stamp_{false};
  bool warned_missing_lidar_tf_{false};

  rclcpp::Subscription<sensor_msgs::msg::LaserScan>::SharedPtr scan_sub_;
  rclcpp::Subscription<nav_msgs::msg::Odometry>::SharedPtr odom_sub_;
  rclcpp::Subscription<sensor_msgs::msg::Imu>::SharedPtr imu_sub_;
  rclcpp::Publisher<geometry_msgs::msg::PoseStamped>::SharedPtr pose_pub_;
  rclcpp::Publisher<std_msgs::msg::String>::SharedPtr status_pub_;
  std::unique_ptr<tf2_ros::TransformBroadcaster> tf_broadcaster_;
  std::unique_ptr<tf2_ros::Buffer> tf_buffer_;
  std::shared_ptr<tf2_ros::TransformListener> tf_listener_;
};

}  // namespace robot_nav_stack_cpp

int main(int argc, char ** argv)
{
  rclcpp::init(argc, argv);
  rclcpp::spin(std::make_shared<robot_nav_stack_cpp::FourWallLocalizerNode>());
  rclcpp::shutdown();
  return 0;
}

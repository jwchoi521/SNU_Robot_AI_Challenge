#include <cv_bridge/cv_bridge.h>
#include <rclcpp/rclcpp.hpp>
#include <sensor_msgs/msg/image.hpp>
#include <std_msgs/msg/header.hpp>

#include <opencv2/videoio.hpp>

#include <algorithm>
#include <chrono>
#include <cstdint>
#include <functional>
#include <memory>
#include <stdexcept>
#include <string>

using namespace std::chrono_literals;

namespace robot_object_detector_ros
{

class OpenCvCameraNode final : public rclcpp::Node
{
public:
  OpenCvCameraNode()
  : Node("opencv_camera_node")
  {
    topic_ = declare_parameter<std::string>("image_topic", "/camera/image_raw");
    camera_index_ = declare_parameter<int>("camera_index", 0);
    camera_pipeline_ = declare_parameter<std::string>("camera_pipeline", "");
    frame_id_ = declare_parameter<std::string>("frame_id", "camera");
    width_ = declare_parameter<int>("frame_width", 1280);
    height_ = declare_parameter<int>("frame_height", 720);
    fps_ = declare_parameter<double>("fps", 30.0);
    buffer_size_ = static_cast<int>(std::max<int64_t>(
      1, declare_parameter<int64_t>("buffer_size", 1)));
    timestamp_mode_ = declare_parameter<std::string>("timestamp_mode", "midpoint");
    timestamp_offset_sec_ = declare_parameter<double>("timestamp_offset_sec", 0.0);
    if (timestamp_mode_ != "start" && timestamp_mode_ != "midpoint" && timestamp_mode_ != "end") {
      throw std::invalid_argument(
              "timestamp_mode must be one of: start, midpoint, end");
    }

    if (!camera_pipeline_.empty()) {
      cap_.open(camera_pipeline_, cv::CAP_GSTREAMER);
    } else {
      cap_.open(camera_index_);
      cap_.set(cv::CAP_PROP_FRAME_WIDTH, width_);
      cap_.set(cv::CAP_PROP_FRAME_HEIGHT, height_);
      cap_.set(cv::CAP_PROP_FPS, fps_);
      cap_.set(cv::CAP_PROP_BUFFERSIZE, buffer_size_);
    }
    if (!cap_.isOpened()) {
      throw std::runtime_error("OpenCV camera could not be opened");
    }

    publisher_ = create_publisher<sensor_msgs::msg::Image>(topic_, 10);
    const auto period_ms = static_cast<int>(1000.0 / std::max(1.0, fps_));
    timer_ = create_wall_timer(
      std::chrono::milliseconds(period_ms),
      std::bind(&OpenCvCameraNode::onTimer, this));
    if (!camera_pipeline_.empty() &&
      (camera_pipeline_.find("drop=true") == std::string::npos ||
      camera_pipeline_.find("max-buffers=1") == std::string::npos))
    {
      RCLCPP_WARN(
        get_logger(),
        "GStreamer pipeline should end with appsink drop=true max-buffers=1 sync=false "
        "to prevent stale frames");
    }
    RCLCPP_INFO(
      get_logger(),
      "publishing camera images on %s; buffer_size=%d timestamp_mode=%s offset=%.6fs",
      topic_.c_str(), buffer_size_, timestamp_mode_.c_str(), timestamp_offset_sec_);
  }

private:
  void onTimer()
  {
    cv::Mat frame;
    const auto read_start = now();
    if (!cap_.read(frame) || frame.empty()) {
      RCLCPP_WARN_THROTTLE(get_logger(), *get_clock(), 2000, "camera frame read failed");
      return;
    }
    const auto read_end = now();

    auto acquisition_stamp = read_end;
    if (timestamp_mode_ == "start") {
      acquisition_stamp = read_start;
    } else if (timestamp_mode_ == "midpoint") {
      acquisition_stamp = read_start + rclcpp::Duration::from_seconds(
        0.5 * (read_end - read_start).seconds());
    }
    if (timestamp_offset_sec_ != 0.0) {
      acquisition_stamp = acquisition_stamp -
        rclcpp::Duration::from_seconds(timestamp_offset_sec_);
    }

    std_msgs::msg::Header header;
    header.stamp = acquisition_stamp;
    header.frame_id = frame_id_;
    auto message = cv_bridge::CvImage(header, "bgr8", frame).toImageMsg();
    publisher_->publish(*message);
  }

  std::string topic_;
  int camera_index_ = 0;
  std::string camera_pipeline_;
  std::string frame_id_;
  int width_ = 1280;
  int height_ = 720;
  double fps_ = 30.0;
  int buffer_size_ = 1;
  std::string timestamp_mode_ = "midpoint";
  double timestamp_offset_sec_ = 0.0;
  cv::VideoCapture cap_;
  rclcpp::Publisher<sensor_msgs::msg::Image>::SharedPtr publisher_;
  rclcpp::TimerBase::SharedPtr timer_;
};

}  // namespace robot_object_detector_ros

int main(int argc, char ** argv)
{
  rclcpp::init(argc, argv);
  rclcpp::spin(std::make_shared<robot_object_detector_ros::OpenCvCameraNode>());
  rclcpp::shutdown();
  return 0;
}

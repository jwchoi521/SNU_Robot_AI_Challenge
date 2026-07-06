#include <cv_bridge/cv_bridge.h>
#include <rclcpp/rclcpp.hpp>
#include <sensor_msgs/msg/image.hpp>
#include <std_msgs/msg/header.hpp>

#include <opencv2/videoio.hpp>

#include <algorithm>
#include <chrono>
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

    if (!camera_pipeline_.empty()) {
      cap_.open(camera_pipeline_, cv::CAP_GSTREAMER);
    } else {
      cap_.open(camera_index_);
      cap_.set(cv::CAP_PROP_FRAME_WIDTH, width_);
      cap_.set(cv::CAP_PROP_FRAME_HEIGHT, height_);
      cap_.set(cv::CAP_PROP_FPS, fps_);
    }
    if (!cap_.isOpened()) {
      throw std::runtime_error("OpenCV camera could not be opened");
    }

    publisher_ = create_publisher<sensor_msgs::msg::Image>(topic_, 10);
    const auto period_ms = static_cast<int>(1000.0 / std::max(1.0, fps_));
    timer_ = create_wall_timer(
      std::chrono::milliseconds(period_ms),
      std::bind(&OpenCvCameraNode::onTimer, this));
    RCLCPP_INFO(get_logger(), "publishing camera images on %s", topic_.c_str());
  }

private:
  void onTimer()
  {
    cv::Mat frame;
    if (!cap_.read(frame) || frame.empty()) {
      RCLCPP_WARN_THROTTLE(get_logger(), *get_clock(), 2000, "camera frame read failed");
      return;
    }

    std_msgs::msg::Header header;
    header.stamp = now();
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

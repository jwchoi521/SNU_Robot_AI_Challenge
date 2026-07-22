#include "robot_object_detector_ros/msg/detection2_d.hpp"
#include "robot_object_detector_ros/msg/detection2_d_array.hpp"
#include "robot_object_detector_ros/trt_engine.hpp"
#include "robot_object_detector_ros/vision_utils.hpp"

#include <cv_bridge/cv_bridge.h>
#include <rclcpp/rclcpp.hpp>
#include <sensor_msgs/msg/image.hpp>

#include <opencv2/imgproc.hpp>

#include <algorithm>
#include <cmath>
#include <exception>
#include <functional>
#include <memory>
#include <string>
#include <vector>

namespace robot_object_detector_ros
{

class ShapeYoloNode final : public rclcpp::Node
{
public:
  ShapeYoloNode()
  : Node("shape_yolo_node")
  {
    const auto engine_path = declare_parameter<std::string>("engine_path", "models/shape_yolo_best.engine");
    image_topic_ = declare_parameter<std::string>("image_topic", "/camera/image_raw");
    detections_topic_ = declare_parameter<std::string>("detections_topic", "/shape_yolo/detections");
    annotated_topic_ = declare_parameter<std::string>("annotated_topic", "/shape_yolo/annotated_image");
    input_width_ = declare_parameter<int>("input_width", 640);
    input_height_ = declare_parameter<int>("input_height", 640);
    num_classes_ = declare_parameter<int>("num_classes", 4);
    class_names_ = declare_parameter<std::vector<std::string>>(
      "class_names",
      {"cube_any", "octahedron", "dodecahedron", "icosahedron"});
    conf_threshold_ = declare_parameter<double>("conf_threshold", 0.5);
    nms_iou_threshold_ = declare_parameter<double>("nms_iou_threshold", 0.7);
    class_agnostic_nms_ = declare_parameter<bool>("class_agnostic_nms", true);
    inference_fps_ = declare_parameter<double>("inference_fps", 0.0);
    min_inference_period_sec_ =
      std::isfinite(inference_fps_) && inference_fps_ > 0.0 ? 1.0 / inference_fps_ : 0.0;

    engine_ = std::make_unique<TensorRtEngine>(engine_path);
    engine_->setInputShape(0, {1, 3, input_height_, input_width_});

    detections_pub_ = create_publisher<msg::Detection2DArray>(detections_topic_, 10);
    annotated_pub_ = create_publisher<sensor_msgs::msg::Image>(annotated_topic_, 10);
    image_sub_ = create_subscription<sensor_msgs::msg::Image>(
      image_topic_,
      rclcpp::SensorDataQoS(),
      std::bind(&ShapeYoloNode::onImage, this, std::placeholders::_1));

    RCLCPP_INFO(
      get_logger(),
      "loaded YOLO TensorRT engine %s; subscribing %s; inference_fps=%.2f",
      engine_path.c_str(),
      image_topic_.c_str(),
      inference_fps_);
  }

private:
  void onImage(const sensor_msgs::msg::Image::ConstSharedPtr image_msg)
  {
    if (!shouldRunInference()) {
      return;
    }

    cv_bridge::CvImageConstPtr cv_ptr;
    try {
      cv_ptr = cv_bridge::toCvShare(image_msg, "bgr8");
    } catch (const cv_bridge::Exception & error) {
      RCLCPP_WARN(get_logger(), "cv_bridge failed: %s", error.what());
      return;
    }

    try {
      LetterboxInfo letterbox;
      const auto input = makeYoloInput(cv_ptr->image, input_width_, input_height_, letterbox);
      engine_->copyInputFromFloat(0, input);
      engine_->infer();
      const auto output = engine_->outputAsFloat(0);
      const auto detections = parseYoloDetections(
        output,
        engine_->output(0).shape,
        letterbox,
        cv_ptr->image.size(),
        num_classes_,
        class_names_,
        static_cast<float>(conf_threshold_),
        static_cast<float>(nms_iou_threshold_),
        class_agnostic_nms_);

      publishDetections(*image_msg, detections);
      if (annotated_pub_->get_subscription_count() > 0U) {
        publishAnnotated(*image_msg, cv_ptr->image, detections);
      }
    } catch (const std::exception & error) {
      RCLCPP_ERROR_THROTTLE(get_logger(), *get_clock(), 2000, "YOLO inference failed: %s", error.what());
    }
  }

  bool shouldRunInference()
  {
    if (min_inference_period_sec_ <= 0.0) {
      return true;
    }

    const auto now = get_clock()->now();
    if (!has_last_inference_time_) {
      last_inference_time_ = now;
      has_last_inference_time_ = true;
      return true;
    }

    const auto elapsed_sec = (now - last_inference_time_).seconds();
    if (elapsed_sec < min_inference_period_sec_) {
      return false;
    }

    last_inference_time_ = now;
    return true;
  }

  void publishDetections(
    const sensor_msgs::msg::Image & image_msg,
    const std::vector<Detection> & detections)
  {
    msg::Detection2DArray output_msg;
    output_msg.header = image_msg.header;
    output_msg.detections.reserve(detections.size());
    for (const auto & detection : detections) {
      msg::Detection2D item;
      item.class_id = detection.class_id;
      item.class_name = detection.class_name;
      item.confidence = detection.confidence;
      item.x1 = detection.box.x;
      item.y1 = detection.box.y;
      item.x2 = detection.box.x + detection.box.width;
      item.y2 = detection.box.y + detection.box.height;
      output_msg.detections.push_back(item);
    }
    detections_pub_->publish(output_msg);
  }

  void publishAnnotated(
    const sensor_msgs::msg::Image & image_msg,
    const cv::Mat & image,
    const std::vector<Detection> & detections)
  {
    cv::Mat annotated = image.clone();
    for (const auto & detection : detections) {
      const cv::Rect rect = clampRect(detection.box, annotated.size());
      if (rect.empty()) {
        continue;
      }
      const cv::Scalar color =
        detection.class_id == 0 ? cv::Scalar(0, 220, 0) : cv::Scalar(0, 180, 255);
      cv::rectangle(annotated, rect, color, 2);
      const std::string label =
        detection.class_name + " " + cv::format("%.2f", detection.confidence);
      cv::putText(
        annotated,
        label,
        cv::Point(rect.x, std::max(18, rect.y - 6)),
        cv::FONT_HERSHEY_SIMPLEX,
        0.5,
        color,
        1,
        cv::LINE_AA);
    }
    auto annotated_msg = cv_bridge::CvImage(image_msg.header, "bgr8", annotated).toImageMsg();
    annotated_pub_->publish(*annotated_msg);
  }

  std::string image_topic_;
  std::string detections_topic_;
  std::string annotated_topic_;
  int input_width_ = 640;
  int input_height_ = 640;
  int num_classes_ = 4;
  std::vector<std::string> class_names_;
  double conf_threshold_ = 0.25;
  double nms_iou_threshold_ = 0.8;
  bool class_agnostic_nms_ = true;
  double inference_fps_ = 0.0;
  double min_inference_period_sec_ = 0.0;
  bool has_last_inference_time_ = false;
  rclcpp::Time last_inference_time_;

  std::unique_ptr<TensorRtEngine> engine_;
  rclcpp::Subscription<sensor_msgs::msg::Image>::SharedPtr image_sub_;
  rclcpp::Publisher<msg::Detection2DArray>::SharedPtr detections_pub_;
  rclcpp::Publisher<sensor_msgs::msg::Image>::SharedPtr annotated_pub_;
};

}  // namespace robot_object_detector_ros

int main(int argc, char ** argv)
{
  rclcpp::init(argc, argv);
  rclcpp::spin(std::make_shared<robot_object_detector_ros::ShapeYoloNode>());
  rclcpp::shutdown();
  return 0;
}

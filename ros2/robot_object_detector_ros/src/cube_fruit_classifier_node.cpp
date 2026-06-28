#include "robot_object_detector_ros/msg/detection2_d_array.hpp"
#include "robot_object_detector_ros/msg/fruit_classification.hpp"
#include "robot_object_detector_ros/msg/fruit_classification_array.hpp"
#include "robot_object_detector_ros/trt_engine.hpp"
#include "robot_object_detector_ros/vision_utils.hpp"

#include <cv_bridge/cv_bridge.h>
#include <message_filters/subscriber.h>
#include <message_filters/sync_policies/approximate_time.h>
#include <message_filters/synchronizer.h>
#include <rclcpp/rclcpp.hpp>
#include <rmw/qos_profiles.h>
#include <sensor_msgs/msg/image.hpp>

#include <opencv2/imgproc.hpp>

#include <algorithm>
#include <exception>
#include <functional>
#include <memory>
#include <stdexcept>
#include <string>
#include <vector>

namespace robot_object_detector_ros
{

class CubeFruitClassifierNode final : public rclcpp::Node
{
public:
  using SyncPolicy = message_filters::sync_policies::ApproximateTime<
    sensor_msgs::msg::Image,
    msg::Detection2DArray>;

  CubeFruitClassifierNode()
  : Node("cube_fruit_classifier_node")
  {
    const auto engine_path =
      declare_parameter<std::string>("engine_path", "models/cube_fruit_classifier.engine");
    image_topic_ = declare_parameter<std::string>("image_topic", "/camera/image_raw");
    detections_topic_ = declare_parameter<std::string>("detections_topic", "/shape_yolo/detections");
    classifications_topic_ =
      declare_parameter<std::string>("classifications_topic", "/cube_fruit/classifications");
    annotated_topic_ = declare_parameter<std::string>("annotated_topic", "/cube_fruit/annotated_image");
    input_width_ = declare_parameter<int>("input_width", 100);
    input_height_ = declare_parameter<int>("input_height", 100);
    cube_class_id_ = declare_parameter<int>("cube_class_id", 0);
    min_cube_confidence_ = declare_parameter<double>("min_cube_confidence", 0.0);
    threshold_ = declare_parameter<double>("threshold", 0.7);
    no_fruit_class_ = declare_parameter<std::string>("no_fruit_class", "none");
    class_names_ = declare_parameter<std::vector<std::string>>(
      "class_names",
      {"apple", "orange", "banana", "pineapple", "none"});

    engine_ = std::make_unique<TensorRtEngine>(engine_path);
    engine_->setInputShape(0, {1, 3, input_height_, input_width_});

    classifications_pub_ = create_publisher<msg::FruitClassificationArray>(classifications_topic_, 10);
    annotated_pub_ = create_publisher<sensor_msgs::msg::Image>(annotated_topic_, 10);

    image_sub_.subscribe(this, image_topic_, rmw_qos_profile_sensor_data);
    detections_sub_.subscribe(this, detections_topic_);
    sync_ = std::make_shared<message_filters::Synchronizer<SyncPolicy>>(
      SyncPolicy(10),
      image_sub_,
      detections_sub_);
    sync_->registerCallback(
      std::bind(
        &CubeFruitClassifierNode::onSynchronized,
        this,
        std::placeholders::_1,
        std::placeholders::_2));

    RCLCPP_INFO(
      get_logger(),
      "loaded classifier TensorRT engine %s; subscribing %s + %s",
      engine_path.c_str(),
      image_topic_.c_str(),
      detections_topic_.c_str());
  }

private:
  struct Prediction
  {
    std::string fruit_kind;
    float confidence = 0.0F;
    std::vector<float> probabilities;
  };

  void onSynchronized(
    const sensor_msgs::msg::Image::ConstSharedPtr image_msg,
    const msg::Detection2DArray::ConstSharedPtr detections_msg)
  {
    cv_bridge::CvImageConstPtr cv_ptr;
    try {
      cv_ptr = cv_bridge::toCvShare(image_msg, "bgr8");
    } catch (const cv_bridge::Exception & error) {
      RCLCPP_WARN(get_logger(), "cv_bridge failed: %s", error.what());
      return;
    }

    msg::FruitClassificationArray output_msg;
    output_msg.header = detections_msg->header;
    cv::Mat annotated = cv_ptr->image.clone();

    for (const auto & detection_msg : detections_msg->detections) {
      if (
        detection_msg.class_id != cube_class_id_ ||
        detection_msg.confidence < static_cast<float>(min_cube_confidence_))
      {
        drawShapeDetection(annotated, detection_msg);
        continue;
      }

      const cv::Rect2f box(
        cv::Point2f(detection_msg.x1, detection_msg.y1),
        cv::Point2f(detection_msg.x2, detection_msg.y2));
      const cv::Rect crop_rect = clampRect(box, cv_ptr->image.size());
      if (crop_rect.empty()) {
        continue;
      }

      try {
        const auto prediction = classifyCrop(cv_ptr->image(crop_rect));
        msg::FruitClassification item;
        item.cube = detection_msg;
        item.fruit_kind = prediction.fruit_kind;
        item.confidence = prediction.confidence;
        item.pick_allowed = prediction.fruit_kind != no_fruit_class_;
        item.class_names = class_names_;
        item.probabilities = prediction.probabilities;
        output_msg.classifications.push_back(item);
        drawClassification(annotated, detection_msg, prediction);
      } catch (const std::exception & error) {
        RCLCPP_ERROR_THROTTLE(
          get_logger(),
          *get_clock(),
          2000,
          "classifier inference failed: %s",
          error.what());
      }
    }

    classifications_pub_->publish(output_msg);
    auto annotated_msg = cv_bridge::CvImage(image_msg->header, "bgr8", annotated).toImageMsg();
    annotated_pub_->publish(*annotated_msg);
  }

  Prediction classifyCrop(const cv::Mat & crop)
  {
    const auto input = makeClassifierInput(crop, input_width_, input_height_);
    engine_->copyInputFromFloat(0, input);
    engine_->infer();
    auto logits = engine_->outputAsFloat(0);
    if (logits.size() < class_names_.size()) {
      throw std::runtime_error("classifier output has fewer values than class_names");
    }
    if (logits.size() > class_names_.size()) {
      logits.resize(class_names_.size());
    }
    const auto probabilities = softmax(logits);
    const auto best_iter = std::max_element(probabilities.begin(), probabilities.end());
    const std::size_t best_index = static_cast<std::size_t>(
      std::distance(probabilities.begin(), best_iter));
    const float best_probability = *best_iter;
    const std::string best_class = class_names_[best_index];

    Prediction prediction;
    prediction.probabilities = probabilities;
    prediction.confidence = best_probability;
    prediction.fruit_kind =
      best_class != no_fruit_class_ && best_probability >= static_cast<float>(threshold_) ?
      best_class :
      no_fruit_class_;
    return prediction;
  }

  void drawShapeDetection(cv::Mat & image, const msg::Detection2D & detection)
  {
    const cv::Rect2f box(
      cv::Point2f(detection.x1, detection.y1),
      cv::Point2f(detection.x2, detection.y2));
    const cv::Rect rect = clampRect(box, image.size());
    if (rect.empty()) {
      return;
    }
    const cv::Scalar color(0, 180, 255);
    cv::rectangle(image, rect, color, 2);
    cv::putText(
      image,
      detection.class_name + " " + cv::format("%.2f", detection.confidence),
      cv::Point(rect.x, std::max(18, rect.y - 6)),
      cv::FONT_HERSHEY_SIMPLEX,
      0.5,
      color,
      1,
      cv::LINE_AA);
  }

  void drawClassification(
    cv::Mat & image,
    const msg::Detection2D & detection,
    const Prediction & prediction)
  {
    const cv::Rect2f box(
      cv::Point2f(detection.x1, detection.y1),
      cv::Point2f(detection.x2, detection.y2));
    const cv::Rect rect = clampRect(box, image.size());
    if (rect.empty()) {
      return;
    }

    const bool has_fruit = prediction.fruit_kind != no_fruit_class_;
    const cv::Scalar color = has_fruit ? cv::Scalar(0, 220, 0) : cv::Scalar(160, 160, 160);
    const std::string label =
      (has_fruit ? prediction.fruit_kind : "unknown_cube") + " " +
      cv::format("%.2f", prediction.confidence);

    cv::rectangle(image, rect, color, 2);
    cv::putText(
      image,
      label,
      cv::Point(rect.x, std::max(18, rect.y - 6)),
      cv::FONT_HERSHEY_SIMPLEX,
      0.5,
      color,
      1,
      cv::LINE_AA);
  }

  std::string image_topic_;
  std::string detections_topic_;
  std::string classifications_topic_;
  std::string annotated_topic_;
  int input_width_ = 100;
  int input_height_ = 100;
  int cube_class_id_ = 0;
  double min_cube_confidence_ = 0.0;
  double threshold_ = 0.7;
  std::string no_fruit_class_ = "none";
  std::vector<std::string> class_names_;

  std::unique_ptr<TensorRtEngine> engine_;
  message_filters::Subscriber<sensor_msgs::msg::Image> image_sub_;
  message_filters::Subscriber<msg::Detection2DArray> detections_sub_;
  std::shared_ptr<message_filters::Synchronizer<SyncPolicy>> sync_;
  rclcpp::Publisher<msg::FruitClassificationArray>::SharedPtr classifications_pub_;
  rclcpp::Publisher<sensor_msgs::msg::Image>::SharedPtr annotated_pub_;
};

}  // namespace robot_object_detector_ros

int main(int argc, char ** argv)
{
  rclcpp::init(argc, argv);
  rclcpp::spin(std::make_shared<robot_object_detector_ros::CubeFruitClassifierNode>());
  rclcpp::shutdown();
  return 0;
}

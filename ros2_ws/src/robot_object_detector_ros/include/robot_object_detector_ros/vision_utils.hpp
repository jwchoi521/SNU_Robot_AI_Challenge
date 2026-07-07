#pragma once

#include <opencv2/core.hpp>

#include <string>
#include <vector>

namespace robot_object_detector_ros
{

struct LetterboxInfo
{
  float scale = 1.0F;
  float pad_x = 0.0F;
  float pad_y = 0.0F;
  int input_width = 0;
  int input_height = 0;
};

struct Detection
{
  int class_id = -1;
  std::string class_name;
  float confidence = 0.0F;
  cv::Rect2f box;
};

std::vector<float> makeYoloInput(
  const cv::Mat & bgr,
  int input_width,
  int input_height,
  LetterboxInfo & info);

std::vector<Detection> parseYoloDetections(
  const std::vector<float> & output,
  const std::vector<int64_t> & output_shape,
  const LetterboxInfo & info,
  const cv::Size & original_size,
  int num_classes,
  const std::vector<std::string> & class_names,
  float conf_threshold,
  float nms_iou_threshold,
  bool class_agnostic_nms);

std::vector<float> makeClassifierInput(
  const cv::Mat & bgr_crop,
  int input_width,
  int input_height);

std::vector<float> softmax(const std::vector<float> & logits);

cv::Rect clampRect(const cv::Rect2f & rect, const cv::Size & image_size);
float intersectionOverUnion(const cv::Rect2f & a, const cv::Rect2f & b);

}  // namespace robot_object_detector_ros

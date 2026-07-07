#include "robot_object_detector_ros/vision_utils.hpp"

#include <opencv2/imgproc.hpp>

#include <algorithm>
#include <cmath>
#include <numeric>
#include <stdexcept>

namespace robot_object_detector_ros
{
namespace
{

float clampFloat(float value, float low, float high)
{
  return std::max(low, std::min(high, value));
}

std::vector<int> sortedIndicesByConfidence(const std::vector<Detection> & detections)
{
  std::vector<int> indices(detections.size());
  std::iota(indices.begin(), indices.end(), 0);
  std::sort(indices.begin(), indices.end(), [&detections](int lhs, int rhs) {
    return detections[static_cast<std::size_t>(lhs)].confidence >
           detections[static_cast<std::size_t>(rhs)].confidence;
  });
  return indices;
}

std::vector<Detection> nms(
  const std::vector<Detection> & detections,
  float iou_threshold,
  bool class_agnostic)
{
  const auto sorted = sortedIndicesByConfidence(detections);
  std::vector<Detection> kept;
  std::vector<bool> suppressed(detections.size(), false);

  for (int sorted_index : sorted) {
    const auto index = static_cast<std::size_t>(sorted_index);
    if (suppressed[index]) {
      continue;
    }
    const auto & candidate = detections[index];
    kept.push_back(candidate);

    for (int other_sorted_index : sorted) {
      const auto other_index = static_cast<std::size_t>(other_sorted_index);
      if (other_index == index || suppressed[other_index]) {
        continue;
      }
      const auto & other = detections[other_index];
      if (!class_agnostic && other.class_id != candidate.class_id) {
        continue;
      }
      if (intersectionOverUnion(candidate.box, other.box) > iou_threshold) {
        suppressed[other_index] = true;
      }
    }
  }
  return kept;
}

}  // namespace

std::vector<float> makeYoloInput(
  const cv::Mat & bgr,
  int input_width,
  int input_height,
  LetterboxInfo & info)
{
  if (bgr.empty()) {
    throw std::runtime_error("empty image passed to makeYoloInput");
  }

  const float scale = std::min(
    static_cast<float>(input_width) / static_cast<float>(bgr.cols),
    static_cast<float>(input_height) / static_cast<float>(bgr.rows));
  const int resized_width = static_cast<int>(std::round(bgr.cols * scale));
  const int resized_height = static_cast<int>(std::round(bgr.rows * scale));
  const int pad_x = (input_width - resized_width) / 2;
  const int pad_y = (input_height - resized_height) / 2;

  cv::Mat resized;
  cv::resize(bgr, resized, cv::Size(resized_width, resized_height));

  cv::Mat canvas(input_height, input_width, CV_8UC3, cv::Scalar(114, 114, 114));
  resized.copyTo(canvas(cv::Rect(pad_x, pad_y, resized_width, resized_height)));

  cv::Mat rgb;
  cv::cvtColor(canvas, rgb, cv::COLOR_BGR2RGB);
  rgb.convertTo(rgb, CV_32FC3, 1.0 / 255.0);

  std::vector<float> input(static_cast<std::size_t>(3 * input_width * input_height));
  const int plane = input_width * input_height;
  for (int y = 0; y < input_height; ++y) {
    for (int x = 0; x < input_width; ++x) {
      const auto pixel = rgb.at<cv::Vec3f>(y, x);
      const int offset = y * input_width + x;
      input[static_cast<std::size_t>(offset)] = pixel[0];
      input[static_cast<std::size_t>(plane + offset)] = pixel[1];
      input[static_cast<std::size_t>(2 * plane + offset)] = pixel[2];
    }
  }

  info.scale = scale;
  info.pad_x = static_cast<float>(pad_x);
  info.pad_y = static_cast<float>(pad_y);
  info.input_width = input_width;
  info.input_height = input_height;
  return input;
}

std::vector<Detection> parseYoloDetections(
  const std::vector<float> & output,
  const std::vector<int64_t> & output_shape,
  const LetterboxInfo & info,
  const cv::Size & original_size,
  int num_classes,
  const std::vector<std::string> & class_names,
  float conf_threshold,
  float nms_iou_threshold,
  bool class_agnostic_nms)
{
  if (num_classes <= 0) {
    throw std::runtime_error("num_classes must be positive");
  }
  if (output_shape.size() < 2 || output_shape.size() > 3) {
    throw std::runtime_error("unsupported YOLO output rank");
  }

  const int64_t dim_a = output_shape.size() == 3 ? output_shape[1] : output_shape[0];
  const int64_t dim_b = output_shape.size() == 3 ? output_shape[2] : output_shape[1];
  const int64_t expected_attrs = static_cast<int64_t>(4 + num_classes);

  bool channels_first = false;
  int64_t attrs = 0;
  int64_t box_count = 0;
  if (dim_a == expected_attrs) {
    channels_first = true;
    attrs = dim_a;
    box_count = dim_b;
  } else if (dim_b == expected_attrs) {
    channels_first = false;
    attrs = dim_b;
    box_count = dim_a;
  } else if (dim_b == 6) {
    // TensorRT engine exported with NMS: [boxes, x1 y1 x2 y2 conf class].
    channels_first = false;
    attrs = 6;
    box_count = dim_a;
  } else if (dim_a == 6) {
    channels_first = true;
    attrs = 6;
    box_count = dim_b;
  } else {
    throw std::runtime_error("YOLO output shape does not match class count");
  }

  auto value_at = [&](int64_t box_index, int64_t attr_index) -> float {
    if (channels_first) {
      return output[static_cast<std::size_t>(attr_index * box_count + box_index)];
    }
    return output[static_cast<std::size_t>(box_index * attrs + attr_index)];
  };

  std::vector<Detection> detections;
  detections.reserve(static_cast<std::size_t>(box_count));

  for (int64_t i = 0; i < box_count; ++i) {
    int class_id = -1;
    float confidence = 0.0F;
    float x1 = 0.0F;
    float y1 = 0.0F;
    float x2 = 0.0F;
    float y2 = 0.0F;

    if (attrs == 6) {
      x1 = value_at(i, 0);
      y1 = value_at(i, 1);
      x2 = value_at(i, 2);
      y2 = value_at(i, 3);
      confidence = value_at(i, 4);
      class_id = static_cast<int>(std::round(value_at(i, 5)));
    } else {
      const float cx_raw = value_at(i, 0);
      const float cy_raw = value_at(i, 1);
      const float width_raw = value_at(i, 2);
      const float height_raw = value_at(i, 3);
      for (int class_index = 0; class_index < num_classes; ++class_index) {
        const float score = value_at(i, 4 + class_index);
        if (score > confidence) {
          confidence = score;
          class_id = class_index;
        }
      }

      const bool normalized =
        std::max({std::abs(cx_raw), std::abs(cy_raw), std::abs(width_raw), std::abs(height_raw)}) <=
        2.0F;
      const float cx = normalized ? cx_raw * info.input_width : cx_raw;
      const float cy = normalized ? cy_raw * info.input_height : cy_raw;
      const float width = normalized ? width_raw * info.input_width : width_raw;
      const float height = normalized ? height_raw * info.input_height : height_raw;
      x1 = cx - width * 0.5F;
      y1 = cy - height * 0.5F;
      x2 = cx + width * 0.5F;
      y2 = cy + height * 0.5F;
    }

    if (confidence < conf_threshold || class_id < 0 || class_id >= num_classes) {
      continue;
    }

    x1 = (x1 - info.pad_x) / info.scale;
    y1 = (y1 - info.pad_y) / info.scale;
    x2 = (x2 - info.pad_x) / info.scale;
    y2 = (y2 - info.pad_y) / info.scale;
    x1 = clampFloat(x1, 0.0F, static_cast<float>(original_size.width - 1));
    y1 = clampFloat(y1, 0.0F, static_cast<float>(original_size.height - 1));
    x2 = clampFloat(x2, 0.0F, static_cast<float>(original_size.width - 1));
    y2 = clampFloat(y2, 0.0F, static_cast<float>(original_size.height - 1));
    if (x2 <= x1 || y2 <= y1) {
      continue;
    }

    Detection detection;
    detection.class_id = class_id;
    detection.class_name =
      class_id < static_cast<int>(class_names.size()) ? class_names[static_cast<std::size_t>(class_id)] :
                                                        std::to_string(class_id);
    detection.confidence = confidence;
    detection.box = cv::Rect2f(cv::Point2f(x1, y1), cv::Point2f(x2, y2));
    detections.push_back(detection);
  }

  return nms(detections, nms_iou_threshold, class_agnostic_nms);
}

std::vector<float> makeClassifierInput(
  const cv::Mat & bgr_crop,
  int input_width,
  int input_height)
{
  if (bgr_crop.empty()) {
    throw std::runtime_error("empty crop passed to makeClassifierInput");
  }
  cv::Mat resized;
  cv::resize(bgr_crop, resized, cv::Size(input_width, input_height), 0.0, 0.0, cv::INTER_AREA);
  cv::Mat rgb;
  cv::cvtColor(resized, rgb, cv::COLOR_BGR2RGB);
  rgb.convertTo(rgb, CV_32FC3, 1.0 / 255.0);

  std::vector<float> input(static_cast<std::size_t>(3 * input_width * input_height));
  const int plane = input_width * input_height;
  for (int y = 0; y < input_height; ++y) {
    for (int x = 0; x < input_width; ++x) {
      const auto pixel = rgb.at<cv::Vec3f>(y, x);
      const int offset = y * input_width + x;
      input[static_cast<std::size_t>(offset)] = (pixel[0] - 0.5F) / 0.5F;
      input[static_cast<std::size_t>(plane + offset)] = (pixel[1] - 0.5F) / 0.5F;
      input[static_cast<std::size_t>(2 * plane + offset)] = (pixel[2] - 0.5F) / 0.5F;
    }
  }
  return input;
}

std::vector<float> softmax(const std::vector<float> & logits)
{
  if (logits.empty()) {
    return {};
  }
  const float max_logit = *std::max_element(logits.begin(), logits.end());
  std::vector<float> probabilities(logits.size());
  float total = 0.0F;
  for (std::size_t i = 0; i < logits.size(); ++i) {
    probabilities[i] = std::exp(logits[i] - max_logit);
    total += probabilities[i];
  }
  if (total <= 0.0F) {
    return probabilities;
  }
  for (auto & probability : probabilities) {
    probability /= total;
  }
  return probabilities;
}

cv::Rect clampRect(const cv::Rect2f & rect, const cv::Size & image_size)
{
  const int x1 = static_cast<int>(std::floor(clampFloat(rect.x, 0.0F, static_cast<float>(image_size.width))));
  const int y1 = static_cast<int>(std::floor(clampFloat(rect.y, 0.0F, static_cast<float>(image_size.height))));
  const int x2 = static_cast<int>(
    std::ceil(clampFloat(rect.x + rect.width, 0.0F, static_cast<float>(image_size.width))));
  const int y2 = static_cast<int>(
    std::ceil(clampFloat(rect.y + rect.height, 0.0F, static_cast<float>(image_size.height))));
  if (x2 <= x1 || y2 <= y1) {
    return {};
  }
  return cv::Rect(x1, y1, x2 - x1, y2 - y1);
}

float intersectionOverUnion(const cv::Rect2f & a, const cv::Rect2f & b)
{
  const float x1 = std::max(a.x, b.x);
  const float y1 = std::max(a.y, b.y);
  const float x2 = std::min(a.x + a.width, b.x + b.width);
  const float y2 = std::min(a.y + a.height, b.y + b.height);
  const float intersection_width = std::max(0.0F, x2 - x1);
  const float intersection_height = std::max(0.0F, y2 - y1);
  const float intersection_area = intersection_width * intersection_height;
  const float union_area = a.area() + b.area() - intersection_area;
  if (union_area <= 0.0F) {
    return 0.0F;
  }
  return intersection_area / union_area;
}

}  // namespace robot_object_detector_ros

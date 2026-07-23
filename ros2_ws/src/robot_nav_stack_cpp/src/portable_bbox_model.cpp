#include "robot_nav_stack_cpp/portable_bbox_model.hpp"

#include <algorithm>
#include <cmath>
#include <cstring>
#include <fstream>
#include <limits>
#include <stdexcept>
#include <string>
#include <vector>

namespace robot_nav_stack_cpp
{
namespace
{

template<typename T>
T read_value(std::istream & stream)
{
  T value{};
  stream.read(reinterpret_cast<char *>(&value), sizeof(T));
  if (!stream) {throw std::runtime_error("truncated portable bbox model");}
  return value;
}

std::string read_string(std::istream & stream)
{
  const auto size = read_value<std::uint32_t>(stream);
  if (size > 1024U * 1024U) {throw std::runtime_error("invalid model string size");}
  std::string value(size, '\0');
  if (size > 0U) {
    stream.read(&value[0], static_cast<std::streamsize>(size));
  }
  if (!stream) {throw std::runtime_error("truncated portable bbox model string");}
  return value;
}

}  // namespace

PortableBboxModel::PortableBboxModel(const std::string & configured_model_path)
: portable_path_(resolve_portable_path(configured_model_path))
{
  load(portable_path_);
}

std::string PortableBboxModel::resolve_portable_path(
  const std::string & configured_model_path)
{
  if (configured_model_path.empty()) {
    throw std::runtime_error("model_path parameter is required");
  }
  std::string path = configured_model_path;
  const auto slash = path.find_last_of("/\\");
  const auto dot = path.find_last_of('.');
  if (dot == std::string::npos || (slash != std::string::npos && dot < slash)) {
    path += ".cppbin";
  } else if (path.substr(dot) != ".cppbin") {
    path.replace(dot, std::string::npos, ".cppbin");
  }
  return path;
}

void PortableBboxModel::load(const std::string & path)
{
  std::ifstream stream(path, std::ios::binary);
  if (!stream) {
    throw std::runtime_error(
            "portable bbox residual model not found: " + path +
            " (export the configured joblib model with export_bbox_model_cpp.py)");
  }
  std::array<char, 8> magic{};
  stream.read(magic.data(), static_cast<std::streamsize>(magic.size()));
  const std::array<char, 8> expected{{'B', 'N', 'R', 'F', 'V', '1', '\0', '\0'}};
  if (!stream || magic != expected) {throw std::runtime_error("invalid portable bbox model magic");}
  const auto version = read_value<std::uint32_t>(stream);
  if (version != 1U) {throw std::runtime_error("unsupported portable bbox model version");}
  anchor_alpha_ = read_value<double>(stream);
  for (double & value : homography_) {value = read_value<double>(stream);}

  const auto numeric_count = read_value<std::uint32_t>(stream);
  if (numeric_count == 0U || numeric_count > 1024U) {
    throw std::runtime_error("invalid portable model numeric feature count");
  }
  numeric_features_.reserve(numeric_count);
  for (std::uint32_t index = 0; index < numeric_count; ++index) {
    NumericFeature feature;
    feature.name = read_string(stream);
    feature.mean = read_value<double>(stream);
    feature.scale = read_value<double>(stream);
    if (!std::isfinite(feature.scale) || feature.scale == 0.0) {
      throw std::runtime_error("invalid StandardScaler scale in portable model");
    }
    numeric_features_.push_back(std::move(feature));
  }

  const auto category_count = read_value<std::uint32_t>(stream);
  if (category_count > 1024U) {throw std::runtime_error("invalid model category count");}
  categories_.reserve(category_count);
  for (std::uint32_t index = 0; index < category_count; ++index) {
    categories_.push_back(read_string(stream));
  }
  transformed_feature_count_ = read_value<std::uint32_t>(stream);
  const auto output_count = read_value<std::uint32_t>(stream);
  const auto tree_count = read_value<std::uint32_t>(stream);
  if (transformed_feature_count_ != numeric_count + category_count || output_count != 2U ||
    tree_count == 0U || tree_count > 100000U)
  {
    throw std::runtime_error("invalid portable forest dimensions");
  }
  trees_.reserve(tree_count);
  for (std::uint32_t tree_index = 0; tree_index < tree_count; ++tree_index) {
    const auto node_count = read_value<std::uint32_t>(stream);
    if (node_count == 0U || node_count > 10000000U) {
      throw std::runtime_error("invalid portable tree node count");
    }
    Tree tree;
    tree.reserve(node_count);
    for (std::uint32_t node_index = 0; node_index < node_count; ++node_index) {
      TreeNode node;
      node.left = read_value<std::int32_t>(stream);
      node.right = read_value<std::int32_t>(stream);
      node.feature = read_value<std::int32_t>(stream);
      node.threshold = read_value<double>(stream);
      node.value_x = read_value<double>(stream);
      node.value_y = read_value<double>(stream);
      if (node.feature >= static_cast<std::int32_t>(transformed_feature_count_)) {
        throw std::runtime_error("portable tree feature index is out of bounds");
      }
      tree.push_back(node);
    }
    trees_.push_back(std::move(tree));
  }
}

double PortableBboxModel::raw_feature(
  const std::string & name, const BboxModelInput & input,
  double anchor_x, double anchor_y, double base_x, double base_y) const
{
  constexpr double eps = 1.0e-6;
  const double width = std::max(input.width, eps);
  const double height = std::max(input.height, eps);
  const double area = std::max(width * height, eps);
  if (name == "bbox_cx") {return input.cx;}
  if (name == "bbox_cy") {return input.cy;}
  if (name == "bbox_w") {return input.width;}
  if (name == "bbox_h") {return input.height;}
  if (name == "anchor_x") {return anchor_x;}
  if (name == "anchor_y") {return anchor_y;}
  if (name == "bbox_bottom_y") {return input.cy + 0.5 * input.height;}
  if (name == "bbox_top_y") {return input.cy - 0.5 * input.height;}
  if (name == "bbox_area") {return input.width * input.height;}
  if (name == "aspect_ratio") {return width / height;}
  if (name == "inv_w") {return 1.0 / width;}
  if (name == "inv_h") {return 1.0 / height;}
  if (name == "inv_sqrt_area") {return 1.0 / std::sqrt(area);}
  if (name == "base_x") {return base_x;}
  if (name == "base_y") {return base_y;}
  if (name == "base_distance") {return std::hypot(base_x, base_y);}
  if (name == "base_angle") {return std::atan2(base_y, base_x) * 180.0 / std::acos(-1.0);}
  throw std::runtime_error("unsupported portable bbox feature: " + name);
}

std::pair<double, double> PortableBboxModel::predict_residual(
  const std::vector<double> & features) const
{
  double sum_x = 0.0;
  double sum_y = 0.0;
  for (const auto & tree : trees_) {
    std::int32_t node_index = 0;
    for (;;) {
      if (node_index < 0 || static_cast<std::size_t>(node_index) >= tree.size()) {
        throw std::runtime_error("portable tree child index is out of bounds");
      }
      const auto & node = tree[static_cast<std::size_t>(node_index)];
      if (node.feature < 0) {
        sum_x += node.value_x;
        sum_y += node.value_y;
        break;
      }
      const auto feature_index = static_cast<std::size_t>(node.feature);
      node_index = features[feature_index] <= node.threshold ? node.left : node.right;
    }
  }
  const double divisor = static_cast<double>(trees_.size());
  return {sum_x / divisor, sum_y / divisor};
}

BboxModelPrediction PortableBboxModel::predict(const BboxModelInput & input) const
{
  const double anchor_x = input.cx;
  const double anchor_y = input.cy + anchor_alpha_ * input.height;
  const double mapped_x = homography_[0] * anchor_x + homography_[1] * anchor_y + homography_[2];
  const double mapped_y = homography_[3] * anchor_x + homography_[4] * anchor_y + homography_[5];
  const double mapped_w = homography_[6] * anchor_x + homography_[7] * anchor_y + homography_[8];
  if (std::abs(mapped_w) < 1.0e-12) {
    throw std::runtime_error("Homography mapped point near infinity.");
  }
  const double base_x = mapped_x / mapped_w;
  const double base_y = mapped_y / mapped_w;
  std::vector<double> features;
  features.reserve(transformed_feature_count_);
  for (const auto & feature : numeric_features_) {
    const double raw = raw_feature(
      feature.name, input, anchor_x, anchor_y, base_x, base_y);
    features.push_back((raw - feature.mean) / feature.scale);
  }
  for (const auto & category : categories_) {
    features.push_back(input.object_type == category ? 1.0 : 0.0);
  }
  if (features.size() != transformed_feature_count_) {
    throw std::runtime_error("portable bbox feature count mismatch");
  }
  const auto residual = predict_residual(features);
  return BboxModelPrediction{base_x + residual.first, base_y + residual.second};
}

}  // namespace robot_nav_stack_cpp

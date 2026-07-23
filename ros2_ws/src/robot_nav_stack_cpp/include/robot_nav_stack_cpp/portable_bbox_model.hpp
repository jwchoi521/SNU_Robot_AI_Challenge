#pragma once

#include <array>
#include <cstdint>
#include <string>
#include <utility>
#include <vector>

namespace robot_nav_stack_cpp
{

struct BboxModelInput
{
  double cx{0.0};
  double cy{0.0};
  double width{0.0};
  double height{0.0};
  std::string object_type;
};

struct BboxModelPrediction
{
  double x{0.0};
  double y{0.0};
};

class PortableBboxModel
{
public:
  explicit PortableBboxModel(const std::string & configured_model_path);
  BboxModelPrediction predict(const BboxModelInput & input) const;
  const std::string & portable_path() const {return portable_path_;}

private:
  struct NumericFeature
  {
    std::string name;
    double mean{0.0};
    double scale{1.0};
  };

  struct TreeNode
  {
    std::int32_t left{-1};
    std::int32_t right{-1};
    std::int32_t feature{-2};
    double threshold{0.0};
    double value_x{0.0};
    double value_y{0.0};
  };

  using Tree = std::vector<TreeNode>;

  static std::string resolve_portable_path(const std::string & configured_model_path);
  void load(const std::string & path);
  double raw_feature(
    const std::string & name, const BboxModelInput & input,
    double anchor_x, double anchor_y, double base_x, double base_y) const;
  std::pair<double, double> predict_residual(const std::vector<double> & features) const;

  std::string portable_path_;
  double anchor_alpha_{0.0};
  std::array<double, 9> homography_{};
  std::vector<NumericFeature> numeric_features_;
  std::vector<std::string> categories_;
  std::uint32_t transformed_feature_count_{0U};
  std::vector<Tree> trees_;
};

}  // namespace robot_nav_stack_cpp

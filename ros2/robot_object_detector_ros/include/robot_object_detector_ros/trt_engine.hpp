#pragma once

#include <NvInfer.h>
#include <NvInferVersion.h>
#include <cuda_runtime_api.h>

#include <cstddef>
#include <cstdint>
#include <string>
#include <vector>

namespace robot_object_detector_ros
{

struct TensorBinding
{
  std::string name;
  bool is_input = false;
  nvinfer1::DataType dtype = nvinfer1::DataType::kFLOAT;
  std::vector<int64_t> shape;
  std::size_t element_count = 0;
  std::size_t byte_size = 0;
  void * device_ptr = nullptr;
};

class TrtLogger final : public nvinfer1::ILogger
{
public:
  void log(Severity severity, const char * msg) noexcept override;
};

class TensorRtEngine
{
public:
  explicit TensorRtEngine(const std::string & engine_path);
  ~TensorRtEngine();

  TensorRtEngine(const TensorRtEngine &) = delete;
  TensorRtEngine & operator=(const TensorRtEngine &) = delete;

  std::size_t numInputs() const;
  std::size_t numOutputs() const;

  const TensorBinding & input(std::size_t index = 0) const;
  const TensorBinding & output(std::size_t index = 0) const;

  void setInputShape(std::size_t index, const std::vector<int64_t> & shape);
  void copyInputFromFloat(std::size_t index, const std::vector<float> & values);
  void infer();
  std::vector<float> outputAsFloat(std::size_t index = 0);

private:
  void load(const std::string & engine_path);
  void discoverBindings();
  void refreshBindingShapes();
  void allocateBinding(TensorBinding & binding);
  TensorBinding & mutableInput(std::size_t index);
  TensorBinding & mutableOutput(std::size_t index);

  TrtLogger logger_;
  nvinfer1::IRuntime * runtime_ = nullptr;
  nvinfer1::ICudaEngine * engine_ = nullptr;
  nvinfer1::IExecutionContext * context_ = nullptr;
  cudaStream_t stream_ = nullptr;
  std::vector<TensorBinding> inputs_;
  std::vector<TensorBinding> outputs_;
#if NV_TENSORRT_MAJOR < 10
  std::vector<void *> bindings_;
  std::vector<int> input_binding_indices_;
  std::vector<int> output_binding_indices_;
#endif
};

std::size_t elementSize(nvinfer1::DataType dtype);
std::size_t volume(const std::vector<int64_t> & shape);

}  // namespace robot_object_detector_ros

#include "robot_object_detector_ros/trt_engine.hpp"

#include <NvInferPlugin.h>
#include <NvInferVersion.h>
#include <cuda_fp16.h>

#include <algorithm>
#include <fstream>
#include <iostream>
#include <iterator>
#include <numeric>
#include <stdexcept>

namespace robot_object_detector_ros
{
namespace
{

void checkCuda(cudaError_t status, const char * action)
{
  if (status != cudaSuccess) {
    throw std::runtime_error(
      std::string(action) + " failed: " + cudaGetErrorString(status));
  }
}

template <typename T>
void destroyTrt(T * object)
{
  if (object == nullptr) {
    return;
  }
#if NV_TENSORRT_MAJOR >= 10
  delete object;
#else
  object->destroy();
#endif
}

nvinfer1::Dims toDims(const std::vector<int64_t> & shape)
{
  if (shape.size() > static_cast<std::size_t>(nvinfer1::Dims::MAX_DIMS)) {
    throw std::runtime_error("TensorRT shape has too many dimensions");
  }
  nvinfer1::Dims dims{};
  dims.nbDims = static_cast<int32_t>(shape.size());
  for (int32_t i = 0; i < dims.nbDims; ++i) {
    dims.d[i] = static_cast<int32_t>(shape[static_cast<std::size_t>(i)]);
  }
  return dims;
}

std::vector<int64_t> fromDims(const nvinfer1::Dims & dims)
{
  std::vector<int64_t> shape;
  shape.reserve(static_cast<std::size_t>(dims.nbDims));
  for (int32_t i = 0; i < dims.nbDims; ++i) {
    shape.push_back(static_cast<int64_t>(dims.d[i]));
  }
  return shape;
}

bool hasDynamicDim(const std::vector<int64_t> & shape)
{
  return std::any_of(shape.begin(), shape.end(), [](int64_t value) {
    return value <= 0;
  });
}

}  // namespace

void TrtLogger::log(Severity severity, const char * msg) noexcept
{
  if (severity <= Severity::kWARNING) {
    std::cerr << "[TensorRT] " << msg << '\n';
  }
}

TensorRtEngine::TensorRtEngine(const std::string & engine_path)
{
  checkCuda(cudaStreamCreate(&stream_), "cudaStreamCreate");
  load(engine_path);
  discoverBindings();
  refreshBindingShapes();
}

TensorRtEngine::~TensorRtEngine()
{
  for (auto & binding : inputs_) {
    if (binding.device_ptr != nullptr) {
      cudaFree(binding.device_ptr);
    }
  }
  for (auto & binding : outputs_) {
    if (binding.device_ptr != nullptr) {
      cudaFree(binding.device_ptr);
    }
  }
  if (stream_ != nullptr) {
    cudaStreamDestroy(stream_);
  }
  destroyTrt(context_);
  destroyTrt(engine_);
  destroyTrt(runtime_);
}

void TensorRtEngine::load(const std::string & engine_path)
{
  std::ifstream file(engine_path, std::ios::binary);
  if (!file) {
    throw std::runtime_error("TensorRT engine not found: " + engine_path);
  }
  std::vector<char> data(
    (std::istreambuf_iterator<char>(file)),
    std::istreambuf_iterator<char>());
  if (data.empty()) {
    throw std::runtime_error("TensorRT engine is empty: " + engine_path);
  }

  runtime_ = nvinfer1::createInferRuntime(logger_);
  if (runtime_ == nullptr) {
    throw std::runtime_error("createInferRuntime failed");
  }
  initLibNvInferPlugins(&logger_, "");
#if NV_TENSORRT_MAJOR >= 10
  engine_ = runtime_->deserializeCudaEngine(data.data(), data.size());
#else
  engine_ = runtime_->deserializeCudaEngine(data.data(), data.size(), nullptr);
#endif
  if (engine_ == nullptr) {
    throw std::runtime_error("deserializeCudaEngine failed: " + engine_path);
  }
  context_ = engine_->createExecutionContext();
  if (context_ == nullptr) {
    throw std::runtime_error("createExecutionContext failed");
  }
}

void TensorRtEngine::discoverBindings()
{
#if NV_TENSORRT_MAJOR >= 10
  const int32_t count = engine_->getNbIOTensors();
  for (int32_t i = 0; i < count; ++i) {
    const char * name = engine_->getIOTensorName(i);
    TensorBinding binding;
    binding.name = name;
    binding.is_input =
      engine_->getTensorIOMode(name) == nvinfer1::TensorIOMode::kINPUT;
    binding.dtype = engine_->getTensorDataType(name);
    binding.shape = fromDims(engine_->getTensorShape(name));
    if (binding.is_input) {
      inputs_.push_back(binding);
    } else {
      outputs_.push_back(binding);
    }
  }
#else
  const int32_t count = engine_->getNbBindings();
  bindings_.assign(static_cast<std::size_t>(count), nullptr);
  for (int32_t i = 0; i < count; ++i) {
    TensorBinding binding;
    binding.name = engine_->getBindingName(i);
    binding.is_input = engine_->bindingIsInput(i);
    binding.dtype = engine_->getBindingDataType(i);
    binding.shape = fromDims(engine_->getBindingDimensions(i));
    if (binding.is_input) {
      input_binding_indices_.push_back(i);
      inputs_.push_back(binding);
    } else {
      output_binding_indices_.push_back(i);
      outputs_.push_back(binding);
    }
  }
#endif
  if (inputs_.empty() || outputs_.empty()) {
    throw std::runtime_error("TensorRT engine must have at least one input and one output");
  }
}

void TensorRtEngine::refreshBindingShapes()
{
#if NV_TENSORRT_MAJOR >= 10
  for (auto & binding : inputs_) {
    binding.shape = fromDims(context_->getTensorShape(binding.name.c_str()));
    if (!hasDynamicDim(binding.shape)) {
      allocateBinding(binding);
      context_->setTensorAddress(binding.name.c_str(), binding.device_ptr);
    }
  }
  for (auto & binding : outputs_) {
    binding.shape = fromDims(context_->getTensorShape(binding.name.c_str()));
    if (!hasDynamicDim(binding.shape)) {
      allocateBinding(binding);
      context_->setTensorAddress(binding.name.c_str(), binding.device_ptr);
    }
  }
#else
  for (std::size_t i = 0; i < inputs_.size(); ++i) {
    const int binding_index = input_binding_indices_[i];
    inputs_[i].shape = fromDims(context_->getBindingDimensions(binding_index));
    if (!hasDynamicDim(inputs_[i].shape)) {
      allocateBinding(inputs_[i]);
      bindings_[static_cast<std::size_t>(binding_index)] = inputs_[i].device_ptr;
    }
  }
  for (std::size_t i = 0; i < outputs_.size(); ++i) {
    const int binding_index = output_binding_indices_[i];
    outputs_[i].shape = fromDims(context_->getBindingDimensions(binding_index));
    if (!hasDynamicDim(outputs_[i].shape)) {
      allocateBinding(outputs_[i]);
      bindings_[static_cast<std::size_t>(binding_index)] = outputs_[i].device_ptr;
    }
  }
#endif
}

void TensorRtEngine::allocateBinding(TensorBinding & binding)
{
  binding.element_count = volume(binding.shape);
  binding.byte_size = binding.element_count * elementSize(binding.dtype);
  if (binding.byte_size == 0) {
    throw std::runtime_error("TensorRT binding has zero size: " + binding.name);
  }
  if (binding.device_ptr != nullptr) {
    cudaFree(binding.device_ptr);
    binding.device_ptr = nullptr;
  }
  checkCuda(cudaMalloc(&binding.device_ptr, binding.byte_size), "cudaMalloc");
}

std::size_t TensorRtEngine::numInputs() const
{
  return inputs_.size();
}

std::size_t TensorRtEngine::numOutputs() const
{
  return outputs_.size();
}

const TensorBinding & TensorRtEngine::input(std::size_t index) const
{
  if (index >= inputs_.size()) {
    throw std::out_of_range("input index out of range");
  }
  return inputs_[index];
}

const TensorBinding & TensorRtEngine::output(std::size_t index) const
{
  if (index >= outputs_.size()) {
    throw std::out_of_range("output index out of range");
  }
  return outputs_[index];
}

TensorBinding & TensorRtEngine::mutableInput(std::size_t index)
{
  if (index >= inputs_.size()) {
    throw std::out_of_range("input index out of range");
  }
  return inputs_[index];
}

TensorBinding & TensorRtEngine::mutableOutput(std::size_t index)
{
  if (index >= outputs_.size()) {
    throw std::out_of_range("output index out of range");
  }
  return outputs_[index];
}

void TensorRtEngine::setInputShape(
  std::size_t index,
  const std::vector<int64_t> & shape)
{
  auto & binding = mutableInput(index);
  if (!hasDynamicDim(binding.shape)) {
    if (binding.shape != shape) {
      throw std::runtime_error(
        "static TensorRT input shape mismatch for " + binding.name);
    }
    refreshBindingShapes();
    return;
  }

  const auto dims = toDims(shape);
#if NV_TENSORRT_MAJOR >= 10
  if (!context_->setInputShape(binding.name.c_str(), dims)) {
    throw std::runtime_error("setInputShape failed for " + binding.name);
  }
#else
  const int binding_index = input_binding_indices_[index];
  if (!context_->setBindingDimensions(binding_index, dims)) {
    throw std::runtime_error("setBindingDimensions failed for " + binding.name);
  }
#endif
  refreshBindingShapes();
}

void TensorRtEngine::copyInputFromFloat(
  std::size_t index,
  const std::vector<float> & values)
{
  auto & binding = mutableInput(index);
  if (values.size() != binding.element_count) {
    throw std::runtime_error(
      "input size mismatch for " + binding.name + ": expected " +
      std::to_string(binding.element_count) + ", got " +
      std::to_string(values.size()));
  }

  if (binding.dtype == nvinfer1::DataType::kFLOAT) {
    checkCuda(
      cudaMemcpyAsync(
        binding.device_ptr,
        values.data(),
        binding.byte_size,
        cudaMemcpyHostToDevice,
        stream_),
      "cudaMemcpyAsync input");
    return;
  }

  if (binding.dtype == nvinfer1::DataType::kHALF) {
    std::vector<__half> half_values(values.size());
    std::transform(values.begin(), values.end(), half_values.begin(), [](float value) {
      return __float2half(value);
    });
    checkCuda(
      cudaMemcpyAsync(
        binding.device_ptr,
        half_values.data(),
        binding.byte_size,
        cudaMemcpyHostToDevice,
        stream_),
      "cudaMemcpyAsync input fp16");
    return;
  }

  throw std::runtime_error("unsupported input TensorRT dtype for " + binding.name);
}

void TensorRtEngine::infer()
{
#if NV_TENSORRT_MAJOR >= 10
  for (auto & binding : inputs_) {
    context_->setTensorAddress(binding.name.c_str(), binding.device_ptr);
  }
  for (auto & binding : outputs_) {
    context_->setTensorAddress(binding.name.c_str(), binding.device_ptr);
  }
  if (!context_->enqueueV3(stream_)) {
    throw std::runtime_error("TensorRT enqueueV3 failed");
  }
#else
  if (!context_->enqueueV2(bindings_.data(), stream_, nullptr)) {
    throw std::runtime_error("TensorRT enqueueV2 failed");
  }
#endif
}

std::vector<float> TensorRtEngine::outputAsFloat(std::size_t index)
{
  auto & binding = mutableOutput(index);
  std::vector<std::uint8_t> host(binding.byte_size);
  checkCuda(
    cudaMemcpyAsync(
      host.data(),
      binding.device_ptr,
      binding.byte_size,
      cudaMemcpyDeviceToHost,
      stream_),
    "cudaMemcpyAsync output");
  checkCuda(cudaStreamSynchronize(stream_), "cudaStreamSynchronize");

  std::vector<float> values(binding.element_count);
  if (binding.dtype == nvinfer1::DataType::kFLOAT) {
    const auto * ptr = reinterpret_cast<const float *>(host.data());
    std::copy(ptr, ptr + binding.element_count, values.begin());
    return values;
  }
  if (binding.dtype == nvinfer1::DataType::kHALF) {
    const auto * ptr = reinterpret_cast<const __half *>(host.data());
    std::transform(ptr, ptr + binding.element_count, values.begin(), [](const __half value) {
      return __half2float(value);
    });
    return values;
  }
  throw std::runtime_error("unsupported output TensorRT dtype for " + binding.name);
}

std::size_t elementSize(nvinfer1::DataType dtype)
{
  switch (dtype) {
    case nvinfer1::DataType::kFLOAT:
      return sizeof(float);
    case nvinfer1::DataType::kHALF:
      return sizeof(std::uint16_t);
    case nvinfer1::DataType::kINT8:
      return sizeof(std::int8_t);
    case nvinfer1::DataType::kINT32:
      return sizeof(std::int32_t);
    case nvinfer1::DataType::kBOOL:
      return sizeof(bool);
    default:
      throw std::runtime_error("unsupported TensorRT dtype");
  }
}

std::size_t volume(const std::vector<int64_t> & shape)
{
  if (shape.empty() || hasDynamicDim(shape)) {
    return 0;
  }
  return std::accumulate(
    shape.begin(),
    shape.end(),
    static_cast<std::size_t>(1),
    [](std::size_t total, int64_t value) {
      return total * static_cast<std::size_t>(value);
    });
}

}  // namespace robot_object_detector_ros

cmake_minimum_required(VERSION 3.16)
project(robot_object_detector_ros)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_POSITION_INDEPENDENT_CODE ON)

find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(sensor_msgs REQUIRED)
find_package(std_msgs REQUIRED)
find_package(cv_bridge REQUIRED)
find_package(message_filters REQUIRED)
find_package(rosidl_default_generators REQUIRED)
find_package(OpenCV REQUIRED)
find_package(CUDAToolkit QUIET)

if(CUDAToolkit_FOUND)
  set(CUDA_RUNTIME_LIB CUDA::cudart)
else()
  find_library(CUDA_RUNTIME_LIB
    cudart
    PATHS /usr/local/cuda/lib64 /usr/lib/aarch64-linux-gnu /usr/lib/x86_64-linux-gnu
  )
  if(NOT CUDA_RUNTIME_LIB)
    message(FATAL_ERROR "CUDA runtime library cudart was not found.")
  endif()
endif()

find_path(TENSORRT_INCLUDE_DIR
  NvInfer.h
  PATHS /usr/include/aarch64-linux-gnu /usr/include/x86_64-linux-gnu /usr/include
)
find_library(TENSORRT_LIBRARY
  nvinfer
  PATHS /usr/lib/aarch64-linux-gnu /usr/lib/x86_64-linux-gnu /usr/lib
)
find_library(TENSORRT_PLUGIN_LIBRARY
  nvinfer_plugin
  PATHS /usr/lib/aarch64-linux-gnu /usr/lib/x86_64-linux-gnu /usr/lib
)

if(NOT TENSORRT_INCLUDE_DIR OR NOT TENSORRT_LIBRARY OR NOT TENSORRT_PLUGIN_LIBRARY)
  message(FATAL_ERROR "TensorRT headers/library were not found. Install JetPack TensorRT development packages.")
endif()

rosidl_generate_interfaces(${PROJECT_NAME}
  "msg/Detection2D.msg"
  "msg/Detection2DArray.msg"
  "msg/FruitClassification.msg"
  "msg/FruitClassificationArray.msg"
  DEPENDENCIES std_msgs
)

include_directories(
  include
  ${OpenCV_INCLUDE_DIRS}
  ${TENSORRT_INCLUDE_DIR}
)

set(COMMON_SOURCES
  src/trt_engine.cpp
  src/vision_utils.cpp
)

function(add_detector_node target source)
  add_executable(${target} ${source} ${COMMON_SOURCES})
  ament_target_dependencies(${target}
    rclcpp
    sensor_msgs
    std_msgs
    cv_bridge
    message_filters
  )
  target_link_libraries(${target}
    ${OpenCV_LIBS}
    ${TENSORRT_LIBRARY}
    ${TENSORRT_PLUGIN_LIBRARY}
    ${CUDA_RUNTIME_LIB}
  )
  if(COMMAND rosidl_get_typesupport_target)
    rosidl_get_typesupport_target(cpp_typesupport_target ${PROJECT_NAME} "rosidl_typesupport_cpp")
    target_link_libraries(${target} "${cpp_typesupport_target}")
  else()
    rosidl_target_interfaces(${target} ${PROJECT_NAME} "rosidl_typesupport_cpp")
  endif()
  if(TARGET ${PROJECT_NAME}__rosidl_generator_cpp)
    add_dependencies(${target} ${PROJECT_NAME}__rosidl_generator_cpp)
  endif()
  target_compile_options(${target} PRIVATE -Wall -Wextra -Wpedantic)
endfunction()

add_detector_node(opencv_camera_node src/opencv_camera_node.cpp)
add_detector_node(shape_yolo_node src/shape_yolo_node.cpp)
add_detector_node(cube_fruit_classifier_node src/cube_fruit_classifier_node.cpp)

install(TARGETS
  opencv_camera_node
  shape_yolo_node
  cube_fruit_classifier_node
  DESTINATION lib/${PROJECT_NAME}
)

install(DIRECTORY
  launch
  config
  DESTINATION share/${PROJECT_NAME}
)

install(DIRECTORY include/
  DESTINATION include
)

ament_export_dependencies(rosidl_default_runtime)
ament_package()

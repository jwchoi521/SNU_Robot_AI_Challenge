cmake_minimum_required(VERSION 3.8)
project(robot_nav_stack_cpp)

if(NOT CMAKE_CXX_STANDARD)
  set(CMAKE_CXX_STANDARD 17)
endif()

find_package(ament_cmake REQUIRED)
find_package(builtin_interfaces REQUIRED)
find_package(geometry_msgs REQUIRED)
find_package(nav_msgs REQUIRED)
find_package(rclcpp REQUIRED)
find_package(sensor_msgs REQUIRED)
find_package(std_msgs REQUIRED)
find_package(tf2 REQUIRED)
find_package(tf2_ros REQUIRED)

add_executable(four_wall_localizer_node src/four_wall_localizer_node.cpp)
ament_target_dependencies(
  four_wall_localizer_node
  builtin_interfaces
  geometry_msgs
  nav_msgs
  rclcpp
  sensor_msgs
  std_msgs
  tf2
  tf2_ros
)

if(CMAKE_CXX_COMPILER_ID MATCHES "GNU|Clang")
  target_compile_options(four_wall_localizer_node PRIVATE -O3 -Wall -Wextra -Wpedantic)
endif()

add_library(portable_bbox_model STATIC src/portable_bbox_model.cpp)
target_include_directories(portable_bbox_model PUBLIC include)
if(CMAKE_CXX_COMPILER_ID MATCHES "GNU|Clang")
  target_compile_options(portable_bbox_model PRIVATE -O3 -Wall -Wextra -Wpedantic)
endif()

add_executable(object_localizer_node src/object_localizer_node.cpp)
target_include_directories(object_localizer_node PRIVATE include)
target_link_libraries(object_localizer_node portable_bbox_model)
ament_target_dependencies(
  object_localizer_node
  builtin_interfaces
  geometry_msgs
  rclcpp
  std_msgs
  tf2
  tf2_ros
)
if(CMAKE_CXX_COMPILER_ID MATCHES "GNU|Clang")
  target_compile_options(object_localizer_node PRIVATE -O3 -Wall -Wextra -Wpedantic)
endif()

install(TARGETS four_wall_localizer_node object_localizer_node DESTINATION lib/${PROJECT_NAME})

ament_package()

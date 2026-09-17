cmake_minimum_required(VERSION 3.8)
project(moveit_collision_management)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(sensor_msgs REQUIRED)
find_package(ament_index_cpp REQUIRED)
find_package(urdf REQUIRED)
find_package(srdfdom REQUIRED)
find_package(moveit_core REQUIRED)
find_package(collision_management REQUIRED)

add_executable(moveit_collision_guard_node src/moveit_collision_guard_node.cpp)
target_link_libraries(moveit_collision_guard_node
  moveit_core::moveit_robot_model
  moveit_core::moveit_robot_state
  moveit_core::moveit_collision_detection
  moveit_core::moveit_collision_detection_fcl
  urdf::urdf
  srdfdom::srdfdom
)
ament_target_dependencies(moveit_collision_guard_node
  rclcpp
  sensor_msgs
  ament_index_cpp
  collision_management
)

install(TARGETS moveit_collision_guard_node
  DESTINATION lib/${PROJECT_NAME}
)

install(DIRECTORY
  launch
  scripts
  DESTINATION share/${PROJECT_NAME}
)

ament_package()

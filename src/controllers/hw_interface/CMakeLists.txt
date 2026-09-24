cmake_minimum_required(VERSION 3.8)
project(hw_interface)
if(CMAKE_COMPILER_IS_GNUCXX OR
   CMAKE_CXX_COMPILER_ID MATCHES "Clang")

  add_compile_options(-Wall -Wextra -Wpedantic)

endif()

# --------------------------------------------------
# Dependencies
# --------------------------------------------------
find_package(ament_cmake REQUIRED)

find_package(rclcpp REQUIRED)
find_package(rclcpp_lifecycle REQUIRED)

find_package(hardware_interface REQUIRED)

find_package(pluginlib REQUIRED)

find_package(std_srvs REQUIRED)

find_package(std_msgs REQUIRED)

find_package(rosidl_default_generators REQUIRED)

find_package(PkgConfig REQUIRED)
pkg_check_modules(LIBUSB REQUIRED IMPORTED_TARGET libusb-1.0)

find_package(Threads REQUIRED)

# --------------------------------------------------
# Messages
# --------------------------------------------------
rosidl_generate_interfaces(${PROJECT_NAME}
  "msg/MotorStatus.msg"
  "msg/MotorStatusArray.msg"
  "srv/SetMotorGains.srv"
)

# --------------------------------------------------
# Hardware plugin library
# --------------------------------------------------
add_library(hw_interface_plugin SHARED
  src/arm_interface.cpp
)

target_include_directories(hw_interface_plugin PUBLIC
  $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
  $<INSTALL_INTERFACE:include>
)

ament_target_dependencies(
  hw_interface_plugin
  rclcpp
  rclcpp_lifecycle
  hardware_interface
  pluginlib
  std_srvs
  std_msgs
)

# --------------------------------------------------
# Link generated message typesupport
# --------------------------------------------------
rosidl_get_typesupport_target(hw_interface_typesupport ${PROJECT_NAME} "rosidl_typesupport_cpp")
target_link_libraries(hw_interface_plugin ${hw_interface_typesupport})

# --------------------------------------------------
# vcan_bridge_node: CANalyst-II <-> vcan0/vcan1 bridge
# --------------------------------------------------
add_executable(vcan_bridge_node
  src/vcan_bridge_node.cpp
)

ament_target_dependencies(vcan_bridge_node
  rclcpp
)

target_link_libraries(vcan_bridge_node
  PkgConfig::LIBUSB
  Threads::Threads
)

install(
  TARGETS vcan_bridge_node
  DESTINATION lib/${PROJECT_NAME}
)

# --------------------------------------------------
# Export plugin
# --------------------------------------------------
pluginlib_export_plugin_description_file(
  hardware_interface
  my_robot_hardware_interface.xml
)

# --------------------------------------------------
# Install plugin xml
# --------------------------------------------------
install(
  FILES my_robot_hardware_interface.xml
  DESTINATION share/${PROJECT_NAME}
)

# --------------------------------------------------
# Install library
# --------------------------------------------------
install(
  TARGETS hw_interface_plugin
  DESTINATION lib
)

# --------------------------------------------------
# Install headers
# --------------------------------------------------
install(
  DIRECTORY include/
  DESTINATION include
)

# --------------------------------------------------
# Export dependencies
# --------------------------------------------------
ament_export_dependencies(
  rosidl_default_runtime
)

ament_package()
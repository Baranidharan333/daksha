cmake_minimum_required(VERSION 3.8)
project(gesture_management)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

find_package(ament_cmake REQUIRED)
find_package(rclpy REQUIRED)
find_package(sensor_msgs REQUIRED)
find_package(std_srvs REQUIRED)
find_package(rosidl_default_generators REQUIRED)

rosidl_generate_interfaces(${PROJECT_NAME}
  "srv/StartRecording.srv"
  "srv/ReplayRecording.srv"
  "srv/PlayRecording.srv"
  "srv/PlaySequence.srv"
  "srv/SaveSequence.srv"
  "srv/DeleteSequence.srv"
  "srv/ListSequences.srv"
  "srv/GetReplayStatus.srv"
)

install(PROGRAMS
  gesture_management/recorder_server.py
  gesture_management/replay_server.py
  gesture_management/gesture_management_app.py
  DESTINATION lib/${PROJECT_NAME}
)

install(DIRECTORY
  launch
  config
  DESTINATION share/${PROJECT_NAME}
)


if(EXISTS "${CMAKE_CURRENT_SOURCE_DIR}/recordings")
  install(
    DIRECTORY recordings
    DESTINATION share/${PROJECT_NAME}
  )
endif()


# Flask looks for templates/ and static/ next to gesture_management_app.py,
# so they must be installed alongside it in lib/${PROJECT_NAME}, not share/.
install(DIRECTORY
  gesture_management/templates
  gesture_management/static
  DESTINATION lib/${PROJECT_NAME}
)

ament_package()
cmake_minimum_required(VERSION 3.8)
project(automation)

find_package(ament_cmake REQUIRED)

install(PROGRAMS
  automation/launch_control_app.py
  DESTINATION lib/${PROJECT_NAME}
)

# Flask looks for templates/ and static/ next to launch_control_app.py, so
# they must be installed alongside it in lib/${PROJECT_NAME}, not share/.
# config/ (ROS 2 param-style yaml, e.g. viewer_joint_overrides.yaml) is
# resolved by launch_control_app.py the same way, so it goes here too.
install(DIRECTORY
  automation/templates
  automation/static
  automation/config
  DESTINATION lib/${PROJECT_NAME}
)

ament_package()

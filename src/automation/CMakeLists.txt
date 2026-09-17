cmake_minimum_required(VERSION 3.8)
project(automation)

find_package(ament_cmake REQUIRED)

install(PROGRAMS
  automation/launch_control_app.py
  DESTINATION lib/${PROJECT_NAME}
)

# Flask looks for templates/ and static/ next to launch_control_app.py, so
# they must be installed alongside it in lib/${PROJECT_NAME}, not share/.
install(DIRECTORY
  automation/templates
  automation/static
  DESTINATION lib/${PROJECT_NAME}
)

ament_package()

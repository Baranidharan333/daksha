cmake_minimum_required(VERSION 3.8)
project(web_nav_site)

find_package(ament_cmake REQUIRED)

# ros2 launch's Node action only looks for an executable directly in
# lib/${PROJECT_NAME} (no recursive search), so server.py must install flat
# there, same convention as this workspace's other single-script UI packages
# (daksha_ui, automation, gesture_management).
install(PROGRAMS
  web_nav_site/server.py
  DESTINATION lib/${PROJECT_NAME}
)

# server.py resolves static/ and config/ relative to its own installed
# location (Path(__file__).resolve().parent), so they install alongside it
# in lib/, not in share/.
install(DIRECTORY
  web_nav_site/static
  web_nav_site/config
  DESTINATION lib/${PROJECT_NAME}
)

install(DIRECTORY
  launch
  DESTINATION share/${PROJECT_NAME}
)

ament_package()

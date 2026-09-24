cmake_minimum_required(VERSION 3.8)
project(daksha_ui)

find_package(ament_cmake REQUIRED)

# All three executables install flat into lib/${PROJECT_NAME} — ros2 launch's
# Node action only looks for an executable directly in that directory (no
# recursive search, and a name containing "/" bypasses its search path
# entirely rather than being treated as a subpath), so nothing here can live
# in a subdirectory.
install(PROGRAMS
  daksha_ui/dashboard_app.py
  daksha_ui/viveka_camera_ui.py
  DESTINATION lib/${PROJECT_NAME}
)

# dashboard_app.py's templates/static must sit alongside it in
# lib/${PROJECT_NAME} (Flask(__name__) resolves them relative to the running
# script's own location). viveka_camera_ui.py serves no templates/static of
# its own. The instruction console's resources moved out with it, to the
# vla_inference package.
install(DIRECTORY
  daksha_ui/templates
  daksha_ui/static
  daksha_ui/logs
  DESTINATION lib/${PROJECT_NAME}
)

install(DIRECTORY
  launch
  config
  DESTINATION share/${PROJECT_NAME}
)

# config/ (installed just above) carries this package's ROS parameter file,
# config/daksha_ui.yaml, alongside camera_layout.json. Installing it is what
# makes it reachable from a built workspace at all - client_ui.launch.py
# resolves it with get_package_share_directory(), and nothing on the robot
# knows where the source tree is.

ament_package()

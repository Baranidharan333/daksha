cmake_minimum_required(VERSION 3.8)
project(daksha_ui)

find_package(ament_cmake REQUIRED)

# Both executables install flat into lib/${PROJECT_NAME} — ros2 launch's
# Node action only looks for an executable directly in that directory (no
# recursive search, and a name containing "/" bypasses its search path
# entirely rather than being treated as a subpath), so nothing here can live
# in a subdirectory.
install(PROGRAMS
  daksha_ui/dashboard_app.py
  daksha_ui/viveka_camera_ui.py
  DESTINATION lib/${PROJECT_NAME}
)

# Each Flask app's templates/static must sit alongside it in lib/${PROJECT_NAME}
# (Flask(__name__) resolves them relative to the running script's own
# location). viveka_camera_ui.py serves no templates/static of its own.
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

ament_package()

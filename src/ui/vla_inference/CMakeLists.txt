cmake_minimum_required(VERSION 3.8)
project(vla_inference)

find_package(ament_cmake REQUIRED)

# ros2 launch's Node action looks for an executable directly in
# lib/${PROJECT_NAME} - no recursive search - so the app installs flat there.
install(PROGRAMS
  vla_inference/vla_inference_app.py
  DESTINATION lib/${PROJECT_NAME}
)

# Flask(__name__) resolves templates/ and static/ relative to the running
# script, so they have to sit beside it in lib/${PROJECT_NAME}. This package
# owns that directory alone, which is why the folders can use the plain Flask
# names - inside daksha_ui they had to be subui_templates/subui_static to
# avoid colliding with dashboard_app.py's own templates/ and static/.
install(DIRECTORY
  vla_inference/templates
  vla_inference/static
  DESTINATION lib/${PROJECT_NAME}
)

# config/vla_inference.yaml is this package's own ROS parameter file, and is
# self-contained - the console launches without any other package being built.
install(DIRECTORY
  launch
  config
  DESTINATION share/${PROJECT_NAME}
)

ament_package()

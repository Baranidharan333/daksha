# generated from rosidl_cmake/cmake/rosidl_cmake_aggregate_target-extras.cmake.in

# Create a convenience aggregate target gesture_management::gesture_management
# that links all generated interface targets, so downstream packages can use
# a single modern CMake target name instead of ${gesture_management_TARGETS}.
if(gesture_management_TARGETS AND NOT TARGET gesture_management::gesture_management)
  add_library(gesture_management::gesture_management INTERFACE IMPORTED)
  set_target_properties(gesture_management::gesture_management PROPERTIES
    INTERFACE_LINK_LIBRARIES "${gesture_management_TARGETS}")
endif()

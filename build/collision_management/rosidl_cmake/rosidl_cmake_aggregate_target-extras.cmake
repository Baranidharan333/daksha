# generated from rosidl_cmake/cmake/rosidl_cmake_aggregate_target-extras.cmake.in

# Create a convenience aggregate target collision_management::collision_management
# that links all generated interface targets, so downstream packages can use
# a single modern CMake target name instead of ${collision_management_TARGETS}.
if(collision_management_TARGETS AND NOT TARGET collision_management::collision_management)
  add_library(collision_management::collision_management INTERFACE IMPORTED)
  set_target_properties(collision_management::collision_management PROPERTIES
    INTERFACE_LINK_LIBRARIES "${collision_management_TARGETS}")
endif()

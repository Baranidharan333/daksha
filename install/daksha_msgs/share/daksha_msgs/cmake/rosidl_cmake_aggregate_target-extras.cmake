# generated from rosidl_cmake/cmake/rosidl_cmake_aggregate_target-extras.cmake.in

# Create a convenience aggregate target daksha_msgs::daksha_msgs
# that links all generated interface targets, so downstream packages can use
# a single modern CMake target name instead of ${daksha_msgs_TARGETS}.
if(daksha_msgs_TARGETS AND NOT TARGET daksha_msgs::daksha_msgs)
  add_library(daksha_msgs::daksha_msgs INTERFACE IMPORTED)
  set_target_properties(daksha_msgs::daksha_msgs PROPERTIES
    INTERFACE_LINK_LIBRARIES "${daksha_msgs_TARGETS}")
endif()

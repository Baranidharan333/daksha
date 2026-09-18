# generated from ament/cmake/core/templates/nameConfig.cmake.in

# prevent multiple inclusion
if(_automation_CONFIG_INCLUDED)
  # ensure to keep the found flag the same
  if(NOT DEFINED automation_FOUND)
    # explicitly set it to FALSE, otherwise CMake will set it to TRUE
    set(automation_FOUND FALSE)
  elseif(NOT automation_FOUND)
    # use separate condition to avoid uninitialized variable warning
    set(automation_FOUND FALSE)
  endif()
  return()
endif()
set(_automation_CONFIG_INCLUDED TRUE)

# output package information
if(NOT automation_FIND_QUIETLY)
  message(STATUS "Found automation: 0.0.1 (${automation_DIR})")
endif()

# warn when using a deprecated package
if(NOT "" STREQUAL "")
  set(_msg "Package 'automation' is deprecated")
  # append custom deprecation text if available
  if(NOT "" STREQUAL "TRUE")
    set(_msg "${_msg} ()")
  endif()
  # optionally quiet the deprecation message
  if(NOT ${automation_DEPRECATED_QUIET})
    message(DEPRECATION "${_msg}")
  endif()
endif()

# flag package as ament-based to distinguish it after being find_package()-ed
set(automation_FOUND_AMENT_PACKAGE TRUE)

# include all config extra files
set(_extras "")
foreach(_extra ${_extras})
  include("${automation_DIR}/${_extra}")
endforeach()

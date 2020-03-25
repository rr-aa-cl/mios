#----------------------------------------------------------------
# Generated CMake target import file for configuration "Release".
#----------------------------------------------------------------

# Commands may need to know the format version.
set(CMAKE_IMPORT_FILE_VERSION 1)

# Import target "motion_error_cart::motion_error_cart" for configuration "Release"
set_property(TARGET motion_error_cart::motion_error_cart APPEND PROPERTY IMPORTED_CONFIGURATIONS RELEASE)
set_target_properties(motion_error_cart::motion_error_cart PROPERTIES
  IMPORTED_LOCATION_RELEASE "/home/lars/repos/franka/simulink_pipeline/install/motion_error_cart/libmotion_error_cart.so"
  IMPORTED_SONAME_RELEASE "libmotion_error_cart.so"
  )

list(APPEND _IMPORT_CHECK_TARGETS motion_error_cart::motion_error_cart )
list(APPEND _IMPORT_CHECK_FILES_FOR_motion_error_cart::motion_error_cart "/home/lars/repos/franka/simulink_pipeline/install/motion_error_cart/libmotion_error_cart.so" )

# Commands beyond this point should not need to know the version.
set(CMAKE_IMPORT_FILE_VERSION)

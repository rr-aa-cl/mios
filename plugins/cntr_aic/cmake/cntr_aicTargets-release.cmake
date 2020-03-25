#----------------------------------------------------------------
# Generated CMake target import file for configuration "Release".
#----------------------------------------------------------------

# Commands may need to know the format version.
set(CMAKE_IMPORT_FILE_VERSION 1)

# Import target "cntr_aic::cntr_aic" for configuration "Release"
set_property(TARGET cntr_aic::cntr_aic APPEND PROPERTY IMPORTED_CONFIGURATIONS RELEASE)
set_target_properties(cntr_aic::cntr_aic PROPERTIES
  IMPORTED_LOCATION_RELEASE "/home/lars/repos/franka/simulink_pipeline/install/cntr_aic/libcntr_aic.so"
  IMPORTED_SONAME_RELEASE "libcntr_aic.so"
  )

list(APPEND _IMPORT_CHECK_TARGETS cntr_aic::cntr_aic )
list(APPEND _IMPORT_CHECK_FILES_FOR_cntr_aic::cntr_aic "/home/lars/repos/franka/simulink_pipeline/install/cntr_aic/libcntr_aic.so" )

# Commands beyond this point should not need to know the version.
set(CMAKE_IMPORT_FILE_VERSION)

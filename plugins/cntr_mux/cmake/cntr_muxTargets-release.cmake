#----------------------------------------------------------------
# Generated CMake target import file for configuration "Release".
#----------------------------------------------------------------

# Commands may need to know the format version.
set(CMAKE_IMPORT_FILE_VERSION 1)

# Import target "cntr_mux::cntr_mux" for configuration "Release"
set_property(TARGET cntr_mux::cntr_mux APPEND PROPERTY IMPORTED_CONFIGURATIONS RELEASE)
set_target_properties(cntr_mux::cntr_mux PROPERTIES
  IMPORTED_LOCATION_RELEASE "/home/lars/repos/franka/simulink_pipeline/install/cntr_mux/libcntr_mux.so"
  IMPORTED_SONAME_RELEASE "libcntr_mux.so"
  )

list(APPEND _IMPORT_CHECK_TARGETS cntr_mux::cntr_mux )
list(APPEND _IMPORT_CHECK_FILES_FOR_cntr_mux::cntr_mux "/home/lars/repos/franka/simulink_pipeline/install/cntr_mux/libcntr_mux.so" )

# Commands beyond this point should not need to know the version.
set(CMAKE_IMPORT_FILE_VERSION)

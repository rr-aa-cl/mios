#----------------------------------------------------------------
# Generated CMake target import file for configuration "Release".
#----------------------------------------------------------------

# Commands may need to know the format version.
set(CMAKE_IMPORT_FILE_VERSION 1)

# Import target "cntr_nullsp_proj::cntr_nullsp_proj" for configuration "Release"
set_property(TARGET cntr_nullsp_proj::cntr_nullsp_proj APPEND PROPERTY IMPORTED_CONFIGURATIONS RELEASE)
set_target_properties(cntr_nullsp_proj::cntr_nullsp_proj PROPERTIES
  IMPORTED_LOCATION_RELEASE "/home/lars/repos/franka/simulink_pipeline/install/cntr_nullsp_proj/libcntr_nullsp_proj.so"
  IMPORTED_SONAME_RELEASE "libcntr_nullsp_proj.so"
  )

list(APPEND _IMPORT_CHECK_TARGETS cntr_nullsp_proj::cntr_nullsp_proj )
list(APPEND _IMPORT_CHECK_FILES_FOR_cntr_nullsp_proj::cntr_nullsp_proj "/home/lars/repos/franka/simulink_pipeline/install/cntr_nullsp_proj/libcntr_nullsp_proj.so" )

# Commands beyond this point should not need to know the version.
set(CMAKE_IMPORT_FILE_VERSION)

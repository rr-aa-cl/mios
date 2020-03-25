#----------------------------------------------------------------
# Generated CMake target import file for configuration "Release".
#----------------------------------------------------------------

# Commands may need to know the format version.
set(CMAKE_IMPORT_FILE_VERSION 1)

# Import target "mogen_p2p::mogen_p2p" for configuration "Release"
set_property(TARGET mogen_p2p::mogen_p2p APPEND PROPERTY IMPORTED_CONFIGURATIONS RELEASE)
set_target_properties(mogen_p2p::mogen_p2p PROPERTIES
  IMPORTED_LOCATION_RELEASE "/home/lars/repos/franka/simulink_pipeline/install/mogen_p2p/libmogen_p2p.so"
  IMPORTED_SONAME_RELEASE "libmogen_p2p.so"
  )

list(APPEND _IMPORT_CHECK_TARGETS mogen_p2p::mogen_p2p )
list(APPEND _IMPORT_CHECK_FILES_FOR_mogen_p2p::mogen_p2p "/home/lars/repos/franka/simulink_pipeline/install/mogen_p2p/libmogen_p2p.so" )

# Commands beyond this point should not need to know the version.
set(CMAKE_IMPORT_FILE_VERSION)

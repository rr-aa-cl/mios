#----------------------------------------------------------------
# Generated CMake target import file for configuration "Release".
#----------------------------------------------------------------

# Commands may need to know the format version.
set(CMAKE_IMPORT_FILE_VERSION 1)

# Import target "virtual_walls_joint::virtual_walls_joint" for configuration "Release"
set_property(TARGET virtual_walls_joint::virtual_walls_joint APPEND PROPERTY IMPORTED_CONFIGURATIONS RELEASE)
set_target_properties(virtual_walls_joint::virtual_walls_joint PROPERTIES
  IMPORTED_LOCATION_RELEASE "/home/lars/repos/franka/simulink_pipeline/install/virtual_walls_joint/libvirtual_walls_joint.so"
  IMPORTED_SONAME_RELEASE "libvirtual_walls_joint.so"
  )

list(APPEND _IMPORT_CHECK_TARGETS virtual_walls_joint::virtual_walls_joint )
list(APPEND _IMPORT_CHECK_FILES_FOR_virtual_walls_joint::virtual_walls_joint "/home/lars/repos/franka/simulink_pipeline/install/virtual_walls_joint/libvirtual_walls_joint.so" )

# Commands beyond this point should not need to know the version.
set(CMAKE_IMPORT_FILE_VERSION)

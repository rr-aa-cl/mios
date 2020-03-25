#----------------------------------------------------------------
# Generated CMake target import file for configuration "Release".
#----------------------------------------------------------------

# Commands may need to know the format version.
set(CMAKE_IMPORT_FILE_VERSION 1)

# Import target "virtual_cube::virtual_cube" for configuration "Release"
set_property(TARGET virtual_cube::virtual_cube APPEND PROPERTY IMPORTED_CONFIGURATIONS RELEASE)
set_target_properties(virtual_cube::virtual_cube PROPERTIES
  IMPORTED_LOCATION_RELEASE "/home/lars/repos/franka/simulink_pipeline/install/virtual_cube/libvirtual_cube.so"
  IMPORTED_SONAME_RELEASE "libvirtual_cube.so"
  )

list(APPEND _IMPORT_CHECK_TARGETS virtual_cube::virtual_cube )
list(APPEND _IMPORT_CHECK_FILES_FOR_virtual_cube::virtual_cube "/home/lars/repos/franka/simulink_pipeline/install/virtual_cube/libvirtual_cube.so" )

# Commands beyond this point should not need to know the version.
set(CMAKE_IMPORT_FILE_VERSION)

if(NOT EXISTS "${PROJECT_BINARY_DIR}/conan.cmake")
    message(STATUS "Downloading conan.cmake from https://github.com/conan-io/cmake-conan")
    file(DOWNLOAD  "https://raw.githubusercontent.com/conan-io/cmake-conan/master/conan.cmake"
        "${PROJECT_BINARY_DIR}/conan.cmake")
endif()
include(${PROJECT_BINARY_DIR}/conan.cmake)

conan_check(REQUIRED)
conan_cmake_run(
    CONANFILE
    conanfile.txt
    BASIC_SETUP
#    CONAN_COMMAND
#    ${CONAN_CMD}
    CMAKE_TARGETS
#    BUILD
#    missing
    )

#include(${PROJECT_BINARY_DIR}/conanbuildinfo.cmake)
#conan_basic_setup()

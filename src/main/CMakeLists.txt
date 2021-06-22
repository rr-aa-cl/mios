add_executable(mios src/mios.cpp)

find_package(PythonLibsNew REQUIRED)

target_include_directories(mios
    PRIVATE
    src
    ${PYTHON_INCLUDE_DIRS}
    PUBLIC
    $<BUILD_INTERFACE:${CMAKE_SOURCE_DIR}/include>
    )

target_link_libraries(mios
    PRIVATE
    ${PROJECT_NAME}::${PROJECT_NAME}_project_options
    ${PROJECT_NAME}::${PROJECT_NAME}_project_warnings
    ${PROJECT_NAME}::${PROJECT_NAME}_project_deps
    PUBLIC
    ${PROJECT_NAME}::core
    CONAN_PKG::pybind11
    CONAN_PKG::cxxopts
    stdc++fs
    )

install(TARGETS mios DESTINATION ${CMAKE_INSTALL_BINDIR})

add_executable(mios src/mios.cpp)

target_include_directories(mios
    PRIVATE
    src
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
    )

install(TARGETS mios DESTINATION ${CMAKE_SOURCE_DIR}/bin)

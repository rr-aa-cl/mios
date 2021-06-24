set(MODULE_NAME learning_module)

set(${MODULE_NAME}_SRC
    src/learning_module.cpp
    )

set(${MODULE_NAME}_HEADER_FILES
    include/${PROJECT_NAME}/${MODULE_NAME}/learning_module.hpp
    )

add_library(${MODULE_NAME}
    ${${MODULE_NAME}_SRC}
    ${${MODULE_NAME}_HEADER_FILES}
    )

find_package (Python3 COMPONENTS Interpreter Development)
find_package(PythonLibsNew REQUIRED)


add_library(${PROJECT_NAME}::${MODULE_NAME} ALIAS ${MODULE_NAME})


target_include_directories(${MODULE_NAME}
    PRIVATE
    src
    PUBLIC
    $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
    ${PYTHON_INCLUDE_DIRS}
    )

target_link_libraries(${MODULE_NAME}
    PRIVATE
    ${PROJECT_NAME}::${PROJECT_NAME}_project_options
    ${PROJECT_NAME}::${PROJECT_NAME}_project_warnings
    ${PROJECT_NAME}::${PROJECT_NAME}_project_deps
    ${PYTHON_LIBRARIES}
    PUBLIC
    CONAN_PKG::pybind11
    CONAN_PKG::nlohmann_json
    Python3::Python
    )

apply_module_options(${MODULE_NAME})


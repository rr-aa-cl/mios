set(MODULE_NAME core)

set(${MODULE_NAME}_SRC
    src/core.cpp
    )

set(${MODULE_NAME}_HEADER_FILES
    include/${PROJECT_NAME}/${MODULE_NAME}/core.hpp
    )

add_library(${MODULE_NAME}
    ${${MODULE_NAME}_SRC}
    ${${MODULE_NAME}_HEADER_FILES}
    )


add_library(${PROJECT_NAME}::${MODULE_NAME} ALIAS ${MODULE_NAME})

target_include_directories(${MODULE_NAME}
    PRIVATE
    src
    PUBLIC
    $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
    )

target_link_libraries(${MODULE_NAME}
    PRIVATE
    ${PROJECT_NAME}::${PROJECT_NAME}_project_options
    ${PROJECT_NAME}::${PROJECT_NAME}_project_warnings
    ${PROJECT_NAME}::${PROJECT_NAME}_project_deps
    msrm_cpp_utils::math
    msrm_cpp_utils::conversion
    msrm_cpp_utils::json
    msrm_cpp_utils::system
    PUBLIC
    ${PROJECT_NAME}::controller_pipeline
    ${PROJECT_NAME}::interface
    ${PROJECT_NAME}::learning_module
    ${PROJECT_NAME}::memory
    ${PROJECT_NAME}::panda
    ${PROJECT_NAME}::portal
    ${PROJECT_NAME}::safety
    ${PROJECT_NAME}::skill
    ${PROJECT_NAME}::task
    ${PROJECT_NAME}::telemetry
    ${PROJECT_NAME}::utils
    )

apply_module_options(${MODULE_NAME})


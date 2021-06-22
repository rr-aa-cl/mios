set(MODULE_NAME task)

set(${MODULE_NAME}_SRC
    src/task.cpp
    src/task_engine.cpp
    src/taskfactory.cpp
    src/taskobserver.cpp
    )

set(${MODULE_NAME}_HEADER_FILES
    include/${PROJECT_NAME}/${MODULE_NAME}/task.hpp
    include/${PROJECT_NAME}/${MODULE_NAME}/task_engine.hpp
    include/${PROJECT_NAME}/${MODULE_NAME}/taskfactory.hpp
    include/${PROJECT_NAME}/${MODULE_NAME}/taskobserver.hpp
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
    ${PROJECT_NAME}::core
    ${PROJECT_NAME}::memory
    msrm_cpp_utils::system
    msrm_cpp_utils::files
    PUBLIC
    ${PROJECT_NAME}::portal
    ${PROJECT_NAME}::skill
    ${PROJECT_NAME}::utils
    ${PROJECT_NAME}::tasks
    msrm_cpp_utils::json
    CONAN_PKG::nlohmann_json
    CONAN_PKG::eigen
    )

apply_module_options(${MODULE_NAME})


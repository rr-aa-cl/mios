set(MODULE_NAME utils)

set(${MODULE_NAME}_SRC
    src/actuator.cpp
    src/event.cpp
    src/exceptions.cpp
    src/object.cpp
    src/parameters.cpp
    src/percept.cpp
    src/results.cpp
    )

set(${MODULE_NAME}_HEADER_FILES
    include/${PROJECT_NAME}/data_structures/actuator.hpp
    include/${PROJECT_NAME}/data_structures/event.hpp
    include/${PROJECT_NAME}/data_structures/object.hpp
    include/${PROJECT_NAME}/data_structures/parameters.hpp
    include/${PROJECT_NAME}/data_structures/percept.hpp
    include/${PROJECT_NAME}/data_structures/results.hpp
    include/${PROJECT_NAME}/data_structures/task_data.hpp
    include/${PROJECT_NAME}/utils/exceptions.hpp
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
    ${PROJECT_NAME}::skills
    msrm_cpp_utils::math
    msrm_cpp_utils::json
    CONAN_PKG::spdlog
    PUBLIC
    CONAN_PKG::eigen
    CONAN_PKG::nlohmann_json
    Franka::Franka
    )

apply_module_options(${MODULE_NAME})


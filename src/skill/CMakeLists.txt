set(MODULE_NAME skill)

set(${MODULE_NAME}_SRC
    src/skill.cpp
    src/skill_engine.cpp
    src/skill_library.cpp
    )

set(${MODULE_NAME}_HEADER_FILES
    include/${PROJECT_NAME}/${MODULE_NAME}/skill.hpp
    include/${PROJECT_NAME}/${MODULE_NAME}/skill_engine.hpp
    include/${PROJECT_NAME}/${MODULE_NAME}/skill_library.hpp
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
    ${PROJECT_NAME}::core
    Franka::Franka
    msrm_cpp_utils::benchmarking
    msrm_cpp_utils::conversion
    msrm_cpp_utils::files
    msrm_cpp_utils::math
    PUBLIC
    ${PROJECT_NAME}::manipulation_primitive
    ${PROJECT_NAME}::memory
    ${PROJECT_NAME}::portal
    ${PROJECT_NAME}::utils
    msrm_cpp_utils::json
    CONAN_PKG::spdlog
    CONAN_PKG::nlohmann_json
    )

apply_module_options(${MODULE_NAME})


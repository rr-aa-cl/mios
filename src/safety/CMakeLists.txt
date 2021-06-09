set(MODULE_NAME safety)

set(${MODULE_NAME}_SRC
    src/cartesian_velocity_damping.cpp
    src/velocity_walls.cpp
    src/virtual_cube.cpp
    src/virtual_joint_walls.cpp
    )

set(${MODULE_NAME}_HEADER_FILES
    include/${PROJECT_NAME}/safety_stage_1/velocity_walls.hpp
    include/${PROJECT_NAME}/safety_stage_1/safety_module_stage_1.hpp
    include/${PROJECT_NAME}/safety_stage_2/cartesian_velocity_damping.hpp
    include/${PROJECT_NAME}/safety_stage_2/virtual_cube.hpp
    include/${PROJECT_NAME}/safety_stage_2/virtual_joint_walls.hpp
    include/${PROJECT_NAME}/safety_stage_2/safety_module_stage_2.hpp
    )

if(BUILD_SHARED_LIBS)
    add_library(${MODULE_NAME}
        SHARED
        ${${MODULE_NAME}_SRC}
        ${${MODULE_NAME}_HEADER_FILES}
        )
else()
    add_library(${MODULE_NAME}
        STATIC
        ${${MODULE_NAME}_SRC}
        ${${MODULE_NAME}_HEADER_FILES}
        )
endif()


add_library(${PROJECT_NAME}::${MODULE_NAME} ALIAS ${MODULE_NAME})

target_include_directories(${MODULE_NAME}
    PRIVATE
    src
    PUBLIC
    $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
    $<BUILD_INTERFACE:${CMAKE_SOURCE_DIR}/include>
    )

target_link_libraries(${MODULE_NAME}
    PRIVATE
    ${PROJECT_NAME}::${PROJECT_NAME}_project_options
    ${PROJECT_NAME}::${PROJECT_NAME}_project_warnings
    ${PROJECT_NAME}::${PROJECT_NAME}_project_deps
    msrm_cpp_utils::math
    PUBLIC
    ${PROJECT_NAME}::memory
    ${PROJECT_NAME}::utils
    CONAN_PKG::eigen
    )

apply_module_options(${MODULE_NAME})


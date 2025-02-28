# Strategies
set(MODULE_NAME strategies)

file(GLOB ${MODULE_NAME}_SRC "${CMAKE_CURRENT_SOURCE_DIR}/src/strategies/*.cpp")
file(GLOB ${MODULE_NAME}_HEADER_FILES "${CMAKE_CURRENT_SOURCE_DIR}/include/mios/strategies/*.hpp")

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
    $<BUILD_INTERFACE:${CMAKE_SOURCE_DIR}/include>
    )

find_package(mogen_p2p REQUIRED)
find_package(mogen_p2p_joint REQUIRED)
find_package(Eigen3 REQUIRED)

target_link_libraries(${MODULE_NAME}
    PRIVATE
    ${PROJECT_NAME}::${PROJECT_NAME}_project_options
    ${PROJECT_NAME}::${PROJECT_NAME}_project_warnings
    ${PROJECT_NAME}::manipulation_primitive
    ${PROJECT_NAME}::portal
    mirmi_cpp_utils::math
    mirmi_cpp_utils::files
    mirmi_cpp_utils::conversion
    PUBLIC
    mogen_p2p::mogen_p2p
    mogen_p2p_joint::mogen_p2p_joint
    Eigen3::Eigen
    ${PROJECT_NAME}::${PROJECT_NAME}_project_deps
    )

apply_module_options(${MODULE_NAME})


# Skills
set(MODULE_NAME skills)

file(GLOB ${MODULE_NAME}_SRC "${CMAKE_CURRENT_SOURCE_DIR}/src/skills/*.cpp")
file(GLOB ${MODULE_NAME}_HEADER_FILES "${CMAKE_CURRENT_SOURCE_DIR}/include/mios/skills/*.hpp")

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
    mirmi_cpp_utils::files
    mirmi_cpp_utils::conversion
    mirmi_cpp_utils::math
    ${PROJECT_NAME}::strategies
    PUBLIC
    ${PROJECT_NAME}::skill
    ${PROJECT_NAME}::${PROJECT_NAME}_project_deps
    )

apply_module_options(${MODULE_NAME})

# Tasks
set(MODULE_NAME tasks)

file(GLOB ${MODULE_NAME}_SRC "${CMAKE_CURRENT_SOURCE_DIR}/src/tasks/*.cpp")
file(GLOB ${MODULE_NAME}_HEADER_FILES "${CMAKE_CURRENT_SOURCE_DIR}/include/mios/tasks/*.hpp")

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
    mirmi_cpp_utils::json
    mirmi_cpp_utils::math
    mirmi_cpp_utils::files
    PUBLIC
    ${PROJECT_NAME}::task
    )

apply_module_options(${MODULE_NAME})

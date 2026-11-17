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

if(ENABLE_TESTING)
    # Compile the production strategy and its value-type dependencies directly.
    # The full utils/skills libraries also pull in the unrelated Core runtime.
    add_executable(test_ff_strategy
        test/test_ff_strategy.cpp
        src/strategies/ff_strategy.cpp
        ../manipulation_primitive/src/primitive_strategy.cpp
        ../utils/src/actuator.cpp
        ../utils/src/percept.cpp
        ../utils/src/parameters.cpp)
    target_compile_features(test_ff_strategy PRIVATE cxx_std_17)
    target_include_directories(test_ff_strategy PRIVATE
        ${CMAKE_SOURCE_DIR}/include
        ${CMAKE_CURRENT_SOURCE_DIR}/include
        ${CMAKE_SOURCE_DIR}/src/manipulation_primitive/include
        ${CMAKE_SOURCE_DIR}/src/utils/include
        ${CMAKE_SOURCE_DIR}/src/skill/include
        ${CMAKE_SOURCE_DIR}/src/memory/include
        ${CMAKE_SOURCE_DIR}/src/portal/include)
    # parameters.cpp contains both the tested ControlParameters and unused
    # skill constructors. Discard unused functions instead of linking Core.
    if(CMAKE_CXX_COMPILER_ID MATCHES "GNU|Clang")
        target_compile_options(test_ff_strategy PRIVATE -ffunction-sections -fdata-sections)
        target_link_options(test_ff_strategy PRIVATE -Wl,--gc-sections)
    endif()
    target_link_libraries(test_ff_strategy PRIVATE
        ${PROJECT_NAME}::${PROJECT_NAME}_project_deps
        mirmi_cpp_utils::math
        mirmi_cpp_utils::json
        mirmi_cpp_utils::network
        CONAN_PKG::mongo-cxx-driver
        CONAN_PKG::nlohmann_json
        Eigen3::Eigen)
    add_test(NAME test_ff_strategy COMMAND test_ff_strategy)
endif()


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

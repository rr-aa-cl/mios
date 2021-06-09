set(MODULE_NAME controller_pipeline)

set(${MODULE_NAME}_SRC
    src/cart_torque_pipeline.cpp
    src/cart_velocity_pipeline.cpp
    src/joint_torque_pipeline.cpp
    src/joint_velocity_pipeline.cpp
    src/null_pipeline.cpp
    )

set(${MODULE_NAME}_HEADER_FILES
    include/${PROJECT_NAME}/${MODULE_NAME}/controller_pipeline.hpp
    include/${PROJECT_NAME}/${MODULE_NAME}/cart_torque_pipeline.hpp
    include/${PROJECT_NAME}/${MODULE_NAME}/cart_velocity_pipeline.hpp
    include/${PROJECT_NAME}/${MODULE_NAME}/joint_torque_pipeline.hpp
    include/${PROJECT_NAME}/${MODULE_NAME}/joint_velocity_pipeline.hpp
    include/${PROJECT_NAME}/${MODULE_NAME}/null_pipeline.hpp
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

target_link_directories(${MODULE_NAME}
    PUBLIC
    $<BUILD_INTERFACE:${CMAKE_SOURCE_DIR}/lib/plugins>
    )

target_include_directories(${MODULE_NAME}
    PRIVATE
    src
    PUBLIC
    $<BUILD_INTERFACE:${CMAKE_SOURCE_DIR}/include>
    $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
    )

target_link_libraries(${MODULE_NAME}
    PRIVATE
    ${PROJECT_NAME}_project_options
    ${PROJECT_NAME}_project_warnings
    ${PROJECT_NAME}_project_deps
    msrm_cpp_utils::math
    conv_vel2pose
    cntr_aic
    cntr_force
    cntr_joint_var_imp
    cntr_nullsp_proj
    cntr_mux
    PUBLIC
    ${PROJECT_NAME}::memory
    ${PROJECT_NAME}::utils
    Franka::Franka
    )

set_target_properties(${MODULE_NAME} PROPERTIES PUBLIC_HEADER "${${MODULE_NAME}_HEADER_FILES}")

apply_module_options(${MODULE_NAME})


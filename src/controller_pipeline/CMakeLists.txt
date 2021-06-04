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

target_include_directories(${MODULE_NAME}
    PRIVATE
    $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
    src
    )

target_link_libraries(${MODULE_NAME}
    PRIVATE
    project_options
    project_warnings
    )

apply_module_options(${MODULE_NAME})


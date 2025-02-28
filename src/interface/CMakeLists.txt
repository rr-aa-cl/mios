set(MODULE_NAME interface)

set(${MODULE_NAME}_SRC
    src/interface.cpp
    #src/ros_node.cpp
    )

set(${MODULE_NAME}_HEADER_FILES
    include/${PROJECT_NAME}/${MODULE_NAME}/interface.hpp
    #include/${PROJECT_NAME}/${MODULE_NAME}/ros_node.hpp
    )

add_library(${MODULE_NAME}
    ${${MODULE_NAME}_SRC}
    ${${MODULE_NAME}_HEADER_FILES}
    )


add_library(${PROJECT_NAME}::${MODULE_NAME} ALIAS ${MODULE_NAME})

#find_package(roscpp REQUIRED  #ros1 stuff
#    std_srvs REQUIRED
#    message_generation REQUIRED)

target_include_directories(${MODULE_NAME}
    PRIVATE
    src
    PUBLIC
    $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
    #${roscpp_INCLUDE_DIRS}
    #${CMAKE_SOURCE_DIR}/src/ros_workspace/devel/include
    )

find_package(nlohmann_json REQUIRED)

target_link_libraries(${MODULE_NAME}
    PRIVATE
    ${PROJECT_NAME}::${PROJECT_NAME}_project_options
    ${PROJECT_NAME}::${PROJECT_NAME}_project_warnings
    ${PROJECT_NAME}::${PROJECT_NAME}_project_deps
    ${PROJECT_NAME}::core
    ${PROJECT_NAME}::memory
    ${PROJECT_NAME}::portal
    ${PROJECT_NAME}::task
    mirmi_cpp_utils::conversion
    #${roscpp_LIBRARIES}
    PUBLIC
    nlohmann_json::nlohmann_json
    )

apply_module_options(${MODULE_NAME})


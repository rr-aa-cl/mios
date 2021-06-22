set(MODULE_NAME manipulation_primitive)

set(${MODULE_NAME}_SRC
    src/manipulation_primitive.cpp
    src/primitive_strategy.cpp
    )

set(${MODULE_NAME}_HEADER_FILES
    include/${PROJECT_NAME}/${MODULE_NAME}/manipulation_primitive.hpp
    include/${PROJECT_NAME}/strategy/primitive_strategy.hpp
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
    ${PROJECT_NAME}::memory
    ${PROJECT_NAME}::strategies
    PUBLIC
    ${PROJECT_NAME}::utils
    CONAN_PKG::eigen
    )

apply_module_options(${MODULE_NAME})


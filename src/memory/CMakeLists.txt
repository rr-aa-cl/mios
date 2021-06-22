set(MODULE_NAME memory)

set(${MODULE_NAME}_SRC
    src/memory.cpp
    src/lt_memory.cpp
    src/st_memory.cpp
    src/mongodb_client.cpp
    )

set(${MODULE_NAME}_HEADER_FILES
    include/${PROJECT_NAME}/${MODULE_NAME}/memory.hpp
    include/${PROJECT_NAME}/${MODULE_NAME}/lt_memory.hpp
    include/${PROJECT_NAME}/${MODULE_NAME}/st_memory.hpp
    include/${PROJECT_NAME}/mongodb_client/mongodb_client.hpp
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
    ${PROJECT_NAME}::task
    ${PROJECT_NAME}::skill
    msrm_cpp_utils::json
    msrm_cpp_utils::math
    PUBLIC
    ${PROJECT_NAME}::utils
    CONAN_PKG::nlohmann_json
    CONAN_PKG::mongo-cxx-driver
    )

apply_module_options(${MODULE_NAME})

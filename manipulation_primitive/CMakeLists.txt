cmake_minimum_required(VERSION 2.8.3)
project(mios-manipulation_primitive)

add_library(manipulation_primitive SHARED src/manipulation_primitive.cpp)
install(TARGETS manipulation_primitive DESTINATION ${CMAKE_SOURCE_DIR}/lib)

foreach(mp ${ACTIVE_MP})
    set(SOURCES src/primitives/${mp}.cpp)
    add_library(${mp} SHARED
        ${SOURCES})
    target_link_libraries(${mp} mogen_p2p mogen_p2p_joint motion_error_cart)

    install(TARGETS ${mp} DESTINATION ${CMAKE_SOURCE_DIR}/lib/primitives)

endforeach(mp)



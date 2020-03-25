cmake_minimum_required(VERSION 2.8.3)
project(mios-skill)

add_library(skill SHARED src/skill.cpp)
target_link_libraries(skill manipulation_primitive)

install(TARGETS skill DESTINATION ${CMAKE_SOURCE_DIR}/lib)

foreach(skill ${ACTIVE_SKILLS})
    set(SOURCES src/skills/${skill}.cpp)
    add_library(${skill} SHARED
        ${SOURCES})

    target_link_libraries(${skill} ${ACTIVE_MP} skill)
    install(TARGETS ${skill} DESTINATION ${CMAKE_SOURCE_DIR}/lib/skills)

endforeach(skill)

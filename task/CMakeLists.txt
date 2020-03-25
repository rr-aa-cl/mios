cmake_minimum_required(VERSION 2.8.3)
project(mios-task)

add_library(task_list SHARED src/task_list.cpp)
target_link_libraries(task_list ${ACTIVE_TASKS})
install(TARGETS task_list DESTINATION ${CMAKE_SOURCE_DIR}/lib)

add_library(task_handler SHARED src/task_handler.cpp)
target_link_libraries(task_handler task_list)
install(TARGETS task_handler DESTINATION ${CMAKE_SOURCE_DIR}/lib)

add_library(task SHARED src/task.cpp)
install(TARGETS task DESTINATION ${CMAKE_SOURCE_DIR}/lib)


foreach(task ${ACTIVE_TASKS})
    set(SOURCES src/tasks/${task}.cpp)
    add_library(${task} SHARED
        ${SOURCES})
    target_link_libraries(${task} task ${ACTIVE_SKILLS} ${ACTIVE_LED_PATTERNS})

    install(TARGETS ${task} DESTINATION ${CMAKE_SOURCE_DIR}/lib/tasks)

endforeach(task)



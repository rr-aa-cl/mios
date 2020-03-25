cmake_minimum_required(VERSION 2.8.3)
project(mios-led_patterns)

add_library(led_pattern SHARED src/led_pattern.cpp)
install(TARGETS led_pattern DESTINATION ${CMAKE_SOURCE_DIR}/lib)

foreach(pattern ${ACTIVE_LED_PATTERNS})
        set(SOURCES src/patterns/${pattern}.cpp)
	add_library(${pattern} SHARED
	    ${SOURCES})

	target_link_libraries(${pattern} led_pattern)
	install(TARGETS ${pattern} DESTINATION ${CMAKE_SOURCE_DIR}/lib/led_patterns)

endforeach(pattern)
